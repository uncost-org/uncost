#!/usr/bin/env python3
"""Horizontal-overflow sweep: every built route, at eighteen widths.

WHY EIGHTEEN AND NOT THREE
--------------------------
This repository shipped a real horizontal-overflow defect while a render gate
was already sampling 1440 / 1290 / 390. A `.sgrid` grid had its column count
pinned by media-query bands, so the right-hand column was pushed off the page
for every width in 1041-1304 (5 columns), 681-784 (3 columns) and 461-523
(2 columns) -- and correct at all three sampled widths. Sampling the widths a
designer happens to own is not an audit; it is a coincidence.

So the width list below is dense across 360..1600 and deliberately places
samples INSIDE each of those three known-bad bands:

    461-523   -> 480, 500
    681-784   -> 700, 768
    1041-1304 -> 1100, 1200, 1290

WHAT COUNTS AS OVERFLOW
-----------------------
For each (route, width) pair the page fails if either arm trips:

  1. document.scrollingElement.scrollWidth exceeds the viewport width.
     Unambiguous, cheap, and it fires even when no single element box is the
     culprit (a nowrap text run, for instance, overflows its own block box
     without that block's rect ever leaving the viewport).

  2. Some rendered element's right edge exceeds the viewport width and that
     element is NOT contained by an opted-in scroll/clip ancestor. This arm
     exists for diagnosis: it names the offender.

A 1px rounding tolerance is allowed on both arms.

Two deliberate judgements, stated so they can be argued with:

  * Content inside an ancestor whose computed overflow-x is hidden / clip /
    auto / scroll, where that ancestor itself sits inside the viewport, is NOT
    reported. The site does this on purpose (the sector anchor bars are
    overflow-x:auto rails). Reporting those would bury the real findings.
  * <html> and <body> are excluded from that clipping check. A global
    `body { overflow-x: hidden }` is a band-aid over a layout bug, not a fix,
    and must not be able to hide a defect from this audit.

FAILING ON "I DON'T KNOW"
-------------------------
A route that will not load, a width whose measurement throws, a zero-route
enumeration, a browser that dies, a viewport whose layout width does not equal
the width we asked for -- each of those is an ERROR that fails the run. The
audit is not allowed to pass by not looking.

USAGE
-----
    python3 tools/overflow_sweep.py                       # the built site
    python3 tools/overflow_sweep.py --built website/dist
    python3 tools/overflow_sweep.py --routes / /faq/
    python3 tools/overflow_sweep.py --selftest            # fixtures only

Prints JSON. Exit 0 when ok, exit 1 on any overflow or error.

The selftest runs ONLY against tools/fixtures/overflow/ -- never against
website/dist or any tracked source -- and asserts that four adversarial
fixtures are caught, three good fixtures are not, a missing page is reported
as an error, and that the mid-band grid fixture is invisible to a sparse
390/1440 width list. That last case is the point of the whole file.
"""

import argparse
import http.server
import json
import pathlib
import socketserver
import subprocess
import sys
import tempfile
import threading

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
DIST = ROOT / "website" / "dist"
FIXTURES = HERE / "fixtures" / "overflow"
WEBSITE = ROOT / "website"

PORT = 8850
TOLERANCE_PX = 1.0

# Dense across 360..1600, with samples inside all three historically broken
# bands. Eighteen widths; see the module docstring for why each cluster exists.
WIDTHS = [
    360, 390, 414,        # small phones
    480, 500,             # inside the 461-523 two-column band
    600,
    700, 768,             # inside the 681-784 three-column band
    800, 900, 1024,
    1100, 1200, 1290,     # inside the 1041-1304 five-column band
    1366, 1440, 1536, 1600,
]

# How many named offenders to report per (route, width). The count of unclipped
# offenders is always reported in full; only the detail list is capped.
MAX_REPORT = 5
# Ceiling on re-load confirmations. Any detection already fails the run, so a
# cap can never turn a failure into a pass -- it only bounds the runtime of a
# catastrophically broken build.
CONFIRM_CAP = 250

NODE_HELPER = r"""
"use strict";
// Inlined at runtime into a temp dir by tools/overflow_sweep.py. Not a
// committed file -- the sweep is one tool, not two.
const fs = require("node:fs");
const puppeteer = require(require.resolve("puppeteer", {
  paths: JSON.parse(process.env.OVERFLOW_PUP_PATHS),
}));

const job = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));

// ---------------------------------------------------------------- in-page --
// Serialised into the page by puppeteer. Must not close over anything.
function measureInPage(vw, tol, maxReport) {
  const out = {
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: 0,
    scanned: 0,
    unclipped: 0,
    offenders: [],
  };
  const se = document.scrollingElement || document.documentElement;
  out.scrollWidth = Math.max(
    se ? se.scrollWidth : 0,
    document.documentElement.scrollWidth,
    document.body ? document.body.scrollWidth : 0
  );
  const esc = (s) => (window.CSS && CSS.escape ? CSS.escape(s) : s);

  function part(e) {
    let s = e.tagName.toLowerCase();
    if (e.id) return s + "#" + esc(e.id);
    const cls = (e.getAttribute("class") || "").trim().split(/\s+/).filter(Boolean).slice(0, 3);
    if (cls.length) s += "." + cls.map(esc).join(".");
    const p = e.parentElement;
    if (p) {
      const sibs = Array.prototype.filter.call(p.children, (x) => x.tagName === e.tagName);
      if (sibs.length > 1) s += ":nth-of-type(" + (sibs.indexOf(e) + 1) + ")";
    }
    return s;
  }
  function selector(el) {
    const chain = [];
    let e = el;
    for (let i = 0; i < 3 && e && e.nodeType === 1 && e !== document.documentElement; i++) {
      chain.unshift(part(e));
      if (e.id) break;
      e = e.parentElement;
    }
    return chain.join(" > ") || "html";
  }
  // html/body are excluded on purpose: see the module docstring.
  function clippedBy(el) {
    let p = el.parentElement;
    while (p && p !== document.body && p !== document.documentElement) {
      const ox = getComputedStyle(p).overflowX;
      if (ox === "hidden" || ox === "clip" || ox === "auto" || ox === "scroll") {
        if (p.getBoundingClientRect().right <= vw + tol) return part(p) + " [overflow-x:" + ox + "]";
      }
      p = p.parentElement;
    }
    return null;
  }

  const body = document.body;
  if (!body) throw new Error("document.body is missing");
  const all = [body].concat(Array.prototype.slice.call(body.querySelectorAll("*")));
  out.scanned = all.length;

  const raw = [];
  for (const el of all) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) continue;   // not rendered
    const over = r.right - vw;
    if (over <= tol) continue;
    raw.push({ el: el, right: r.right, over: over });
  }
  raw.sort((a, b) => b.over - a.over);
  for (const c of raw) {
    if (clippedBy(c.el)) continue;
    out.unclipped++;
    if (out.offenders.length < maxReport) {
      out.offenders.push({
        selector: selector(c.el),
        kind: "box",
        right: Math.round(c.right * 100) / 100,
        overflow_px: Math.round(c.over * 100) / 100,
      });
    }
  }

  // The document scrolls but no element box left the viewport -- that is the
  // signature of inline content (an unbreakable token) overflowing its own
  // block. Measure the text runs so the report can still name a culprit.
  if (out.unclipped === 0 && out.scrollWidth > vw + tol) {
    const walker = document.createTreeWalker(body, NodeFilter.SHOW_TEXT);
    const range = document.createRange();
    const seen = [];
    let n;
    while ((n = walker.nextNode())) {
      if (!n.nodeValue || !n.nodeValue.trim()) continue;
      const host = n.parentElement;
      if (!host) continue;
      range.selectNodeContents(n);
      const r = range.getBoundingClientRect();
      if (r.width === 0 && r.height === 0) continue;
      const over = r.right - vw;
      if (over <= tol) continue;
      if (clippedBy(host)) continue;
      const hcs = getComputedStyle(host);
      if (hcs.overflowX !== "visible" && host.getBoundingClientRect().right <= vw + tol) continue;
      seen.push({ host: host, right: r.right, over: over });
    }
    seen.sort((a, b) => b.over - a.over);
    for (const c of seen) {
      out.unclipped++;
      if (out.offenders.length < maxReport) {
        out.offenders.push({
          selector: selector(c.host) + " (text run)",
          kind: "text",
          right: Math.round(c.right * 100) / 100,
          overflow_px: Math.round(c.over * 100) / 100,
        });
      }
    }
  }
  return out;
}

// ------------------------------------------------------------------ driver --
async function settle(page) {
  // Images that never load measure as zero-sized boxes, which would hide an
  // overflow rather than reveal one. Force them in and wait.
  await page.evaluate(async () => {
    if (document.fonts && document.fonts.ready) await document.fonts.ready;
    for (const img of document.querySelectorAll('img[loading="lazy"]')) {
      img.loading = "eager";
      if (img.dataset && img.dataset.src) img.src = img.dataset.src;
    }
    await Promise.all(
      Array.prototype.slice
        .call(document.images)
        .filter((i) => !i.complete)
        .map((i) => new Promise((res) => {
          i.onload = i.onerror = res;
          setTimeout(res, 4000);
        }))
    );
    await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
  });
}

(async () => {
  const browser = await puppeteer.launch({
    args: ["--no-sandbox", "--force-device-scale-factor=1", "--hide-scrollbars"],
  });
  const page = await browser.newPage();
  // http.server honours If-Modified-Since, so revisiting a route answers 304 --
  // which res.ok() rejects, and a conditional hit could also serve a stale body.
  // Disabling the cache makes every navigation a real, fresh fetch.
  await page.setCacheEnabled(false);
  await page.emulateMediaFeatures([{ name: "prefers-reduced-motion", value: "reduce" }]);
  page.setDefaultTimeout(45000);

  const results = {};
  let confirmBudget = job.confirmCap;

  for (const spec of job.jobs) {
    const res = { overflows: [], errors: [], checks: 0, routes: spec.routes.length, widths: spec.widths.length };
    results[spec.id] = res;

    for (const route of spec.routes) {
      const url = job.base + route;
      let loaded = true;
      try {
        await page.setViewport({ width: spec.widths[0], height: 900, deviceScaleFactor: 1 });
        const r = await page.goto(url, { waitUntil: "load", timeout: 45000 });
        if (!r) throw new Error("no response");
        // 304 means "your copy is current", which is a successful load.
        if (!r.ok() && r.status() !== 304) throw new Error("HTTP " + r.status());
        await settle(page);
      } catch (e) {
        loaded = false;
        res.errors.push({
          type: "load", route: route, width: null,
          message: "route failed to load: " + url + " -- " + (e && e.message ? e.message : String(e)),
        });
      }
      if (!loaded) continue;

      const hits = [];
      for (const w of spec.widths) {
        let m;
        try {
          await page.setViewport({ width: w, height: 900, deviceScaleFactor: 1 });
          await page.evaluate(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))));
          m = await page.evaluate(measureInPage, w, job.tol, job.maxReport);
        } catch (e) {
          res.errors.push({
            type: "measure", route: route, width: w,
            message: "measurement failed: " + (e && e.message ? e.message : String(e)),
          });
          continue;
        }
        res.checks++;
        if (m.clientWidth > w + job.tol || m.clientWidth < w - job.tol) {
          res.errors.push({
            type: "viewport", route: route, width: w,
            message: "layout viewport is " + m.clientWidth + "px but " + w +
                     "px was requested; measurements at this width cannot be trusted",
          });
        }
        if (m.scanned <= 1) {
          res.errors.push({
            type: "empty", route: route, width: w,
            message: "page rendered " + m.scanned + " element(s); nothing to measure",
          });
        }
        const docOver = m.scrollWidth - w;
        if (docOver > job.tol || m.unclipped > 0) hits.push({ w: w, m: m, docOver: docOver });
      }

      // Widths are swept by resizing one loaded page, which is fast and, for
      // pure-CSS layout, identical to a fresh load. Every hit is nonetheless
      // re-checked on a clean load at that width so a stale layout can never be
      // reported as a defect -- and a hit that does not reproduce is itself
      // raised as an error rather than dropped.
      for (const hit of hits) {
        let confirmed = null;
        if (confirmBudget > 0) {
          confirmBudget--;
          try {
            await page.setViewport({ width: hit.w, height: 900, deviceScaleFactor: 1 });
            const r = await page.goto(url, { waitUntil: "load", timeout: 45000 });
            if (!r || (!r.ok() && r.status() !== 304)) {
              throw new Error("reload failed: HTTP " + (r ? r.status() : "no response"));
            }
            await settle(page);
            confirmed = await page.evaluate(measureInPage, hit.w, job.tol, job.maxReport);
          } catch (e) {
            res.errors.push({
              type: "confirm", route: route, width: hit.w,
              message: "could not re-check a detected overflow on a clean load: " +
                       (e && e.message ? e.message : String(e)),
            });
          }
        }
        let m = hit.m, note = confirmBudget > 0 || confirmed ? null : "not re-checked (confirmation budget exhausted)";
        if (confirmed) {
          const stillOver = confirmed.scrollWidth - hit.w > job.tol || confirmed.unclipped > 0;
          if (!stillOver) {
            res.errors.push({
              type: "unstable", route: route, width: hit.w,
              message: "overflow seen after resize but not on a clean load at this width; " +
                       "the page's layout depends on resize history and cannot be judged",
            });
            continue;
          }
          m = confirmed;
        }
        const docOver = m.scrollWidth - hit.w;
        res.overflows.push({
          type: "overflow",
          route: route,
          width: hit.w,
          viewport_px: hit.w,
          document_scroll_width: m.scrollWidth,
          document_overflow_px: Math.round(docOver * 100) / 100,
          offender_count: m.unclipped,
          offenders: m.offenders,
          note: note,
        });
      }
    }
  }

  await browser.close();
  process.stdout.write(JSON.stringify({ results: results }));
})().catch((e) => {
  process.stdout.write(JSON.stringify({ fatal: String((e && e.stack) || e) }));
  process.exit(3);
});
"""


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):  # keep stdout pure JSON
        pass


def serve(directory: pathlib.Path, port: int):
    """Same pattern as tools/render_gate.py serve(), silenced."""
    handler = lambda *a, **kw: _Quiet(*a, directory=str(directory), **kw)
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def enumerate_routes(built: pathlib.Path):
    """Every .html file under the built tree, as the URL path that serves it."""
    routes = []
    for p in sorted(built.rglob("*.html")):
        rel = p.relative_to(built).as_posix()
        routes.append("/" + (rel[: -len("index.html")] if rel.endswith("index.html") else rel))
    return sorted(set(routes))


def run_jobs(base: str, jobs: list) -> dict:
    """Inline the node driver into a temp dir and run it. Never a second file."""
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="uncost-overflow-"))
    helper = tmp / "sweep.cjs"
    helper.write_text(NODE_HELPER, encoding="utf-8")
    spec = tmp / "job.json"
    spec.write_text(json.dumps({
        "base": base, "jobs": jobs, "tol": TOLERANCE_PX,
        "maxReport": MAX_REPORT, "confirmCap": CONFIRM_CAP,
    }), encoding="utf-8")
    env = dict(**__import__("os").environ)
    env["OVERFLOW_PUP_PATHS"] = json.dumps([str(WEBSITE)])
    proc = subprocess.run([ "node", str(helper), str(spec) ],
                          capture_output=True, text=True, env=env)
    if not proc.stdout.strip():
        raise RuntimeError(f"browser driver produced no output (exit {proc.returncode}): "
                           f"{proc.stderr.strip()[-800:]}")
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"browser driver output was not JSON: {e}: {proc.stdout[:400]}")
    if "fatal" in payload:
        raise RuntimeError(f"browser driver crashed: {payload['fatal'][:800]}")
    return payload["results"]


def _message(entry: dict) -> str:
    if entry.get("type") != "overflow":
        return entry.get("message", "")
    head = (f"horizontal overflow on {entry['route']} at {entry['width']}px: "
            f"document scrollWidth {entry['document_scroll_width']} vs viewport "
            f"{entry['viewport_px']} (+{entry['document_overflow_px']}px), "
            f"{entry['offender_count']} unclipped offending element(s)")
    for o in entry["offenders"]:
        head += (f"; {o['selector']} right={o['right']} vs {entry['viewport_px']} "
                 f"(+{o['overflow_px']}px)")
    if entry.get("note"):
        head += f"; {entry['note']}"
    return head


def decorate(result: dict) -> dict:
    """Merge overflows and errors into one ordered, human-readable error list."""
    entries = list(result["overflows"]) + list(result["errors"])
    entries.sort(key=lambda e: (e.get("route") or "", e.get("width") or 0, e.get("type")))
    for e in entries:
        e["message"] = _message(e)
    return {
        "entries": entries,
        "overflow_cells": len(result["overflows"]),
        "hard_errors": len(result["errors"]),
        "checks": result["checks"],
        "routes": result["routes"],
        "widths": result["widths"],
    }


def sweep(built: pathlib.Path, routes=None, widths=None) -> dict:
    widths = widths or WIDTHS
    if not built.is_dir():
        return {"ok": False,
                "errors": [{"type": "setup", "message":
                            f"built site not found at {built}; run `cd website && npm run build`"}],
                "counts": {"routes": 0, "widths": len(widths), "checks": 0, "overflows": 0}}
    routes = routes if routes else enumerate_routes(built)
    if not routes:
        return {"ok": False,
                "errors": [{"type": "setup", "message": f"no .html routes found under {built}"}],
                "counts": {"routes": 0, "widths": len(widths), "checks": 0, "overflows": 0}}
    httpd = serve(built, PORT)
    try:
        results = run_jobs(f"http://127.0.0.1:{PORT}",
                           [{"id": "main", "routes": routes, "widths": widths}])
    except Exception as e:  # a sweep that cannot see its subject must fail loudly
        return {"ok": False,
                "errors": [{"type": "setup", "message": str(e)}],
                "counts": {"routes": len(routes), "widths": len(widths),
                           "checks": 0, "overflows": 0}}
    finally:
        httpd.shutdown()
        httpd.server_close()
    d = decorate(results["main"])
    expected = len(routes) * len(widths)
    if d["checks"] != expected:
        d["entries"].append({"type": "coverage", "route": None, "width": None,
                             "message": f"only {d['checks']} of {expected} "
                                        f"route x width checks completed"})
        d["hard_errors"] += 1
    return {
        "ok": d["overflow_cells"] == 0 and d["hard_errors"] == 0,
        "errors": d["entries"],
        "counts": {"routes": len(routes), "widths": len(widths),
                   "checks": d["checks"], "overflows": d["overflow_cells"]},
    }


# --------------------------------------------------------------- selftest --

BAD = ["bad-fixed-width.html", "bad-mid-band-grid.html",
       "bad-long-string.html", "bad-offset-right.html"]
GOOD = ["good-simple.html", "good-tall.html", "good-scroll-container.html"]
MISSING = "does-not-exist.html"


def selftest() -> dict:
    """Fixtures only. Never website/dist, never a tracked source file."""
    failures = []
    cases = 0
    if not FIXTURES.is_dir():
        return {"ok": False, "selftest_cases": 0,
                "failures": [f"fixture directory missing: {FIXTURES}"]}
    for name in BAD + GOOD:
        if not (FIXTURES / name).is_file():
            failures.append(f"fixture missing: {name}")
    if (FIXTURES / MISSING).exists():
        failures.append(f"{MISSING} must NOT exist -- it is the failed-load case")
    if failures:
        return {"ok": False, "selftest_cases": 0, "failures": failures}

    routes = ["/" + n for n in BAD + GOOD] + ["/" + MISSING]
    httpd = serve(FIXTURES, PORT)
    try:
        results = run_jobs(f"http://127.0.0.1:{PORT}", [
            {"id": "dense", "routes": routes, "widths": WIDTHS},
            # The control: the exact width list that let the shipped defect
            # through. The mid-band grid fixture must be INVISIBLE here.
            {"id": "sparse", "routes": ["/bad-mid-band-grid.html"], "widths": [390, 1440]},
        ])
    except Exception as e:
        return {"ok": False, "selftest_cases": 0,
                "failures": [f"selftest could not run the browser: {e}"]}
    finally:
        httpd.shutdown()
        httpd.server_close()

    dense = decorate(results["dense"])
    sparse = decorate(results["sparse"])

    def widths_hit(entries, route, kind="overflow"):
        return sorted(e["width"] for e in entries
                      if e.get("route") == route and e.get("type") == kind)

    # 1-4: every adversarial fixture must be caught by the dense list.
    for name in BAD:
        cases += 1
        hit = widths_hit(dense["entries"], "/" + name)
        if not hit:
            failures.append(f"{name}: deliberately broken but the sweep reported no overflow")

    # 5: a page that will not load is an error, not a quiet pass.
    cases += 1
    load_errs = [e for e in dense["entries"]
                 if e.get("route") == "/" + MISSING and e.get("type") == "load"]
    if not load_errs:
        failures.append(f"{MISSING}: a route that cannot load must be reported as an error")

    # 6-8: the good fixtures must be clean, with no errors of any kind.
    for name in GOOD:
        cases += 1
        noise = [e for e in dense["entries"] if e.get("route") == "/" + name]
        if noise:
            failures.append(f"{name}: expected clean, got {len(noise)} finding(s): "
                            + "; ".join(n["message"] for n in noise[:3]))

    # 9: THE case. The mid-band grid must pass a 390/1440 sweep. If it does not,
    # the fixture is not actually band-limited and case 2 proves nothing.
    cases += 1
    if sparse["overflow_cells"] or sparse["hard_errors"]:
        failures.append("bad-mid-band-grid.html was flagged at 390/1440; the fixture is not "
                        "band-limited, so catching it with the dense list proves nothing "
                        f"({'; '.join(e['message'] for e in sparse['entries'][:2])})")
    else:
        band = [w for w in widths_hit(dense["entries"], "/bad-mid-band-grid.html")
                if 461 <= w <= 523]
        if not band:
            failures.append("bad-mid-band-grid.html was not caught at any width inside "
                            "461-523; the dense list is not covering the known-bad band")

    # 10: the run as a whole must fail.
    cases += 1
    if dense["overflow_cells"] == 0 and dense["hard_errors"] == 0:
        failures.append("the fixture sweep reported ok; it contains four broken pages "
                        "and one unloadable route")

    # 11: coverage -- every loadable route x width must actually have been measured.
    cases += 1
    expected = (len(BAD) + len(GOOD)) * len(WIDTHS)
    if dense["checks"] != expected:
        failures.append(f"dense run measured {dense['checks']} cells, expected {expected}")

    return {"ok": not failures, "selftest_cases": cases, "failures": failures}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--built", default=str(DIST), help="built site directory")
    ap.add_argument("--routes", nargs="*", default=None, help="URL paths to check")
    ap.add_argument("--selftest", action="store_true", help="run fixture selftest only")
    args = ap.parse_args()

    if args.selftest:
        out = selftest()
        print(json.dumps(out, indent=2))
        return 0 if out["ok"] else 1

    out = sweep(pathlib.Path(args.built).resolve(), args.routes)
    print(json.dumps(out, indent=2))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

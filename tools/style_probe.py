#!/usr/bin/env python3
"""Style probe — read computed styles, boxes and line counts off the built site.

A brief that says "the headline goes from 4 lines to 2", "the robot stays
440px" or "the two intro lines compute to the same style" is making claims
about rendered pages. Standing rule 4 (docs/DESIGN_IMPORT_RUNBOOK.md) allows a
result to be reported only when the script that produced it is committed, so
the measurements behind those claims come from here, driven by a spec file
committed beside it (tools/probes/*.json).

A spec:

    {"widths": [390, 1440],
     "probes": [
       {"name": "hero-h1", "routes": ["/"], "selector": ".hero-grid h1",
        "props": ["font-size", "max-width"], "lines": true, "box": true},
       {"name": "aim", "routes": ["/"], "selector": ".hero-aim",
        "props": ["font-family", "font-size", "font-weight", "color"],
        "same_as": "subhead"},
       {"name": "no-details", "routes": ["/news/"], "selector": "details.ldrawer",
        "expect_count": 0},
       {"name": "hero", "routes": ["/"], "selector": "main > section:first-child",
        "shot": true}
     ]}

For each route x width x probe it records how many elements match and, for the
first match (every match with "all": true), the requested computed properties,
the border box (x, y, width, height) and, with "lines", the number of rendered
line boxes of its text. Every row also carries the page's scrollWidth, so a
horizontal scroll shows as scrollWidth > width.

Checks — each an ERROR, never a skipped line (standing rule 1):
  - a selector that matches nothing, unless the probe says "expect_count": 0;
  - "expect_count": N and a different number of matches;
  - "same_as": a probe whose first match differs in any listed property;
  - a route that will not load.

    python3 tools/style_probe.py tools/probes/site-sweep-2026-10-10.json
    python3 tools/style_probe.py SPEC --built DIR --shots OUTDIR   # element PNGs
    python3 tools/style_probe.py --selftest

Exit 0 when ok, 1 on any error.
"""
from __future__ import annotations

import argparse
import http.server
import json
import pathlib
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading

ROOT = pathlib.Path(__file__).resolve().parents[1]
WEBSITE = ROOT / "website"
DIST = WEBSITE / "dist"

PROBE_JS = r"""
const puppeteer = require(require.resolve("puppeteer", { paths: [process.argv[2]] }));
const fs = require("node:fs");
const path = require("node:path");
const base = process.argv[3];
const spec = JSON.parse(fs.readFileSync(process.argv[4], "utf8"));
const shots = process.argv[5] || "";

const IN_PAGE = (probe) => {
  const els = [...document.querySelectorAll(probe.selector)];
  const read = (el) => {
    const cs = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    const out = { props: {}, box: null, lines: null,
                  text: (el.textContent || "").replace(/\s+/g, " ").trim().slice(0, 90) };
    for (const p of probe.props || []) out.props[p] = cs.getPropertyValue(p);
    if (probe.box) out.box = [r.x, r.y + window.scrollY, r.width, r.height].map((v) => Math.round(v * 100) / 100);
    if (probe.lines) {
      const range = document.createRange();
      range.selectNodeContents(el);
      const tops = new Set();
      for (const rc of range.getClientRects()) if (rc.width > 0 && rc.height > 0) tops.add(Math.round(rc.top));
      out.lines = tops.size;
    }
    return out;
  };
  return { count: els.length, items: (probe.all ? els : els.slice(0, 1)).map(read),
           scrollWidth: document.documentElement.scrollWidth };
};

(async () => {
  const browser = await puppeteer.launch({ args: ["--no-sandbox", "--force-device-scale-factor=1"] });
  const page = await browser.newPage();
  await page.emulateMediaFeatures([{ name: "prefers-reduced-motion", value: "reduce" }]);
  const results = [];
  const routes = [...new Set(spec.probes.flatMap((p) => p.routes))];
  for (const route of routes) {
    for (const w of spec.widths) {
      await page.setViewport({ width: w, height: 1000, deviceScaleFactor: 1 });
      let res;
      try { res = await page.goto(base + route, { waitUntil: "networkidle0", timeout: 60000 }); }
      catch (e) { results.push({ route, width: w, error: "load: " + e.message }); continue; }
      if (!res || !res.ok()) { results.push({ route, width: w, error: "status " + (res && res.status()) }); continue; }
      await page.evaluate(() => document.fonts && document.fonts.ready);
      await page.evaluate(async () => {
        for (const img of document.querySelectorAll('img[loading="lazy"]')) img.loading = "eager";
        await Promise.all([...document.images].filter((i) => !i.complete)
          .map((i) => new Promise((r) => { i.onload = i.onerror = r; })));
      });
      await new Promise((r) => setTimeout(r, 150));
      for (const probe of spec.probes.filter((p) => p.routes.includes(route))) {
        const got = await page.evaluate(IN_PAGE, probe);
        const row = { route, width: w, probe: probe.name, ...got };
        if (shots && probe.shot && got.count) {
          const handle = await page.$(probe.selector);
          const name = (route.replace(/^\//, "").replace(/\/$/, "").replace(/[\/.]/g, "_") || "index");
          const file = path.join(shots, `${name}__${probe.name}@${w}.png`);
          fs.mkdirSync(shots, { recursive: true });
          await handle.screenshot({ path: file });
          row.shot = file;
        }
        results.push(row);
      }
    }
  }
  await browser.close();
  process.stdout.write(JSON.stringify(results));
})().catch((e) => { console.error(e.stack || String(e)); process.exit(2); });
"""


def serve(directory: pathlib.Path, port: int):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    class Server(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True

        def handle_error(self, request, client_address):
            pass  # the browser dropping a connection mid-transfer is not a finding

    handler = lambda *a, **kw: Quiet(*a, directory=str(directory), **kw)
    httpd = Server(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def run(spec_path: pathlib.Path, built: pathlib.Path, port: int, shots: str = ""):
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="uncost-probe-"))
    try:
        js = tmp / "probe.cjs"
        js.write_text(PROBE_JS, encoding="utf-8")
        httpd = serve(built, port)
        try:
            proc = subprocess.run(["node", str(js), str(WEBSITE), f"http://127.0.0.1:{port}",
                                   str(spec_path), shots], capture_output=True, text=True, timeout=1800)
        finally:
            httpd.shutdown()
            httpd.server_close()
        if proc.returncode != 0:
            raise RuntimeError(f"probe failed: {proc.stderr[-2000:]}")
        return json.loads(proc.stdout)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def judge(spec, rows):
    errors = []
    by = {(r.get("route"), r.get("width"), r.get("probe")): r for r in rows}
    for r in rows:
        if "error" in r:
            errors.append({"kind": "route", "route": r["route"], "width": r["width"], "detail": r["error"]})
    for p in spec["probes"]:
        for route in p["routes"]:
            for w in spec["widths"]:
                r = by.get((route, w, p["name"]))
                if r is None:
                    continue  # the route itself failed; reported above
                want = p.get("expect_count")
                if want is None and r["count"] == 0:
                    errors.append({"kind": "no-match", "probe": p["name"], "route": route, "width": w})
                elif want is not None and r["count"] != want:
                    errors.append({"kind": "count", "probe": p["name"], "route": route, "width": w,
                                   "expected": want, "got": r["count"]})
                other = p.get("same_as")
                if other and r["count"]:
                    o = by.get((route, w, other))
                    if not o or not o["count"]:
                        errors.append({"kind": "same_as-missing", "probe": p["name"], "other": other,
                                       "route": route, "width": w})
                        continue
                    a, b = r["items"][0]["props"], o["items"][0]["props"]
                    diff = {k: [a[k], b.get(k)] for k in a if a[k] != b.get(k)}
                    if diff:
                        errors.append({"kind": "same_as", "probe": p["name"], "other": other,
                                       "route": route, "width": w, "differs": diff})
    return errors


def selftest(port: int) -> int:
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="uncost-probe-st-"))
    try:
        (tmp / "index.html").write_text(
            "<!doctype html><html><head><style>body{margin:0;font:16px/20px sans-serif}"
            ".a,.b{font-size:20px}.c{font-size:21px}.w{width:100px}</style></head><body>"
            "<p class='a'>alpha</p><p class='b'>beta</p><p class='c'>gamma</p>"
            "<p class='w'>one two three four five six seven eight</p></body></html>", encoding="utf-8")
        spec = {"widths": [400], "probes": [
            {"name": "a", "routes": ["/"], "selector": ".a", "props": ["font-size"]},
            {"name": "b", "routes": ["/"], "selector": ".b", "props": ["font-size"], "same_as": "a"},
            {"name": "c", "routes": ["/"], "selector": ".c", "props": ["font-size"], "same_as": "a"},
            {"name": "gone", "routes": ["/"], "selector": ".nothing"},
            {"name": "absent-ok", "routes": ["/"], "selector": ".nothing", "expect_count": 0},
            {"name": "two", "routes": ["/"], "selector": "p", "expect_count": 2},
            {"name": "wrap", "routes": ["/"], "selector": ".w", "lines": True, "box": True},
        ]}
        sp = tmp / "spec.json"
        sp.write_text(json.dumps(spec), encoding="utf-8")
        rows = run(sp, tmp, port)
        errs = judge(spec, rows)
        kinds = sorted((e["kind"], e["probe"]) for e in errs)
        wrap = next(r for r in rows if r["probe"] == "wrap")["items"][0]
        cases = [
            ("same style passes, different style fails", ("same_as", "c") in kinds and ("same_as", "b") not in kinds),
            ("a selector matching nothing is an error", ("no-match", "gone") in kinds),
            ("expect_count 0 accepts no match", not any(p == "absent-ok" for _, p in kinds)),
            ("a wrong count is an error", ("count", "two") in kinds),
            ("lines counts rendered line boxes", wrap["lines"] and wrap["lines"] >= 3 and wrap["box"][2] == 100),
        ]
        failures = [n for n, ok in cases if not ok]
        print(json.dumps({"ok": not failures, "selftest_cases": len(cases), "failures": failures}, indent=2))
        return 0 if not failures else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("spec", nargs="?")
    ap.add_argument("--built", default=str(DIST))
    ap.add_argument("--port", type=int, default=8931)
    ap.add_argument("--shots", default="", help="directory for element screenshots of probes with \"shot\": true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest(a.port)
    if not a.spec:
        ap.error("a spec file is required")
    spec = json.loads(pathlib.Path(a.spec).read_text(encoding="utf-8"))
    rows = run(pathlib.Path(a.spec).resolve(), pathlib.Path(a.built), a.port, str(pathlib.Path(a.shots).resolve()) if a.shots else "")
    errors = judge(spec, rows)
    print(json.dumps({"ok": not errors, "errors": errors, "rows": rows}, indent=1))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())

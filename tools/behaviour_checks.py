#!/usr/bin/env python3
"""Progressive-enhancement behaviour, asserted on RENDERED state.

Why this exists
---------------
Every check here asserts what a reader can actually see, via `offsetParent`,
never via the DOM property or attribute that is supposed to cause it. That
distinction is not pedantry — this repository shipped both halves of it:

  - `[hidden] { display: none }` is (0,1,0). `.cards .card { display: flex }`
    is (0,2,0) and beat it, so cards carrying the `hidden` attribute stayed on
    screen. A test reading `el.hidden` would have said "hidden: true" while the
    card was visible. (CANVAS-SYNC 66.)
  - The same filter's test asserted on the counter's TEXT. The counter read
    "1 of 26" while three cards were still rendered, and the test passed.

So: `offsetParent !== null` means rendered. `el.hidden === true` means nothing
about what the reader sees, and this tool never asks.

Usage
-----
    python3 tools/behaviour_checks.py                # built site
    python3 tools/behaviour_checks.py --built DIR
    python3 tools/behaviour_checks.py --selftest     # adversarial fixtures
"""
from __future__ import annotations

import argparse
import http.server
import json
import pathlib
import re
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_BUILT = ROOT / "website" / "dist"
WEBSITE = ROOT / "website"
FIXTURES = ROOT / "tools" / "fixtures" / "behaviour"

# Expected register size. Asserted rather than derived, so that a register that
# silently loses rows fails here instead of quietly redefining "all of them".
REGISTER_CARDS = 26
SHOW_MORE_STEP = 12

PROBE_JS = r"""
const puppeteer = require(require.resolve("puppeteer", { paths: [process.argv[2]] }));
const base = process.argv[3];
const jobs = JSON.parse(process.argv[4]);   // [{route, js, queries:{name:selector}}]

(async () => {
  const browser = await puppeteer.launch({ args: ["--no-sandbox", "--force-device-scale-factor=1"] });
  const out = [];
  for (const job of jobs) {
    const page = await browser.newPage();
    await page.setCacheEnabled(false);
    await page.setJavaScriptEnabled(job.js);
    await page.setViewport({ width: job.width || 1440, height: 1000, deviceScaleFactor: 1 });
    let res;
    try {
      res = await page.goto(base + job.route, { waitUntil: job.js ? "networkidle0" : "load", timeout: 60000 });
    } catch (e) {
      out.push({ ...job, loadError: String(e).slice(0, 200) });
      await page.close();
      continue;
    }
    if (!res || !(res.ok() || res.status() === 304)) {
      out.push({ ...job, loadError: "HTTP " + (res && res.status()) });
      await page.close();
      continue;
    }
    if (job.js) {
      // Web fonts change line breaks; measure only once they have landed.
      await page.evaluate(() => document.fonts && document.fonts.ready);
      await new Promise(r => setTimeout(r, 150));
    }
    if (job.js && job.type) {
      try { await page.type(job.type[0], job.type[1]); await new Promise(r => setTimeout(r, 250)); } catch (e) {}
    }
    if (job.js && job.clickFirst) {
      try { await page.click(job.clickFirst); await new Promise(r => setTimeout(r, 250)); } catch (e) {}
    }
    const measured = await page.evaluate((queries) => {
      // RENDERED, not declared. offsetParent is null for display:none and for
      // any ancestor that is display:none, which is exactly "the reader cannot
      // see it". position:fixed elements report null offsetParent while being
      // perfectly visible, so they are handled explicitly.
      const rendered = (el) => {
        const cs = getComputedStyle(el);
        if (cs.display === "none" || cs.visibility === "hidden") return false;
        if (cs.position === "fixed") {
          const r = el.getBoundingClientRect();
          return r.width > 0 && r.height > 0;
        }
        return el.offsetParent !== null;
      };
      const res = {};
      for (const [name, sel] of Object.entries(queries)) {
        const els = [...document.querySelectorAll(sel)];
        res[name] = {
          total: els.length,
          rendered: els.filter(rendered).length,
          // Recorded only to expose the gap between the attribute and reality.
          // Never asserted on.
          attrHidden: els.filter((e) => e.hasAttribute("hidden")).length,
          // TRUNCATED as drawn: the box is shorter than its own content.
          // Measured on the rendered element, never inferred from a class.
          clipped: els.filter((e) => rendered(e) && e.scrollHeight > e.clientHeight + 1).length,
          // Tallest rendered box, in its own lines.
          maxLines: Math.max(0, ...els.filter(rendered).map((e) =>
            Math.round(e.clientHeight / (parseFloat(getComputedStyle(e).lineHeight) || 1)))),
          // A rendered control whose aria-controls target is NOT truncated
          // (a control that does nothing), and a truncated element with no
          // rendered control pointing at it (text the reader cannot reach).
          orphanControls: els.filter((e) => {
            if (!rendered(e) || !e.hasAttribute("aria-controls")) return false;
            const t = document.getElementById(e.getAttribute("aria-controls"));
            return !t || !(t.scrollHeight > t.clientHeight + 1);
          }).length,
          unreachable: els.filter((e) => rendered(e) && e.scrollHeight > e.clientHeight + 1 &&
            ![...document.querySelectorAll('[aria-controls="' + e.id + '"]')].some(rendered)).length,
        };
      }
      return res;
    }, job.queries);
    out.push({ ...job, measured });
    await page.close();
  }
  await browser.close();
  process.stdout.write(JSON.stringify(out));
})().catch((e) => { console.error(e); process.exit(1); });
"""


def serve(directory: pathlib.Path, port: int):
    handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(
        *a, directory=str(directory), **kw
    )
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def run_jobs(directory: pathlib.Path, jobs, port: int):
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="uncost-behaviour-"))
    try:
        js = tmp / "probe.cjs"
        js.write_text(PROBE_JS, encoding="utf-8")
        httpd = serve(directory, port)
        try:
            proc = subprocess.run(
                ["node", str(js), str(WEBSITE), f"http://127.0.0.1:{port}", json.dumps(jobs)],
                capture_output=True, text=True, timeout=900,
            )
        finally:
            httpd.shutdown()
            httpd.server_close()
        if proc.returncode != 0:
            raise RuntimeError(f"probe failed: {proc.stderr[-2000:]}")
        return json.loads(proc.stdout)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------------
# the real-site checks
# --------------------------------------------------------------------------
SITE_JOBS = [
    {"name": "receipts-js-off", "route": "/receipts/", "js": False,
     "queries": {"cards": "#register-cards > .card",
                 "showmore": "[data-show-more]"}},
    {"name": "receipts-js-on", "route": "/receipts/", "js": True,
     "queries": {"cards": "#register-cards > .card",
                 "showmore": "[data-show-more]"}},
    {"name": "search-js-off", "route": "/", "js": False,
     "queries": {"links": ".search-ov .so-links a",
                 "searchbox": ".search-ov [data-search-box]"}},
    {"name": "search-js-on", "route": "/", "js": True,
     "queries": {"links": ".search-ov .so-links a",
                 "searchbox": ".search-ov [data-search-box]"}},
] + [
    # V16 — three-line clamp with "Read more" (/js/read-more.js). /news/ is
    # measured at 1440, where two of its three updates run past three lines;
    # Cost Watch at 320, the one width where a claim does (a 1440 Cost Watch
    # card is one line and would assert nothing). `-open` presses the first
    # control; `-filter` narrows Cost Watch to the BLS rows, hiding the only
    # card with a control, whose control then must not render either.
    {"name": f"{key}-{mode}", "route": route, "width": width, "js": mode != "js-off",
     "queries": {"bodies": f"#{grid} [data-news-item] p", "controls": "[data-read-more]"},
     **extra}
    for key, route, width, grid in (("news", "/news/", 1440, "news-uncost"),
                                    ("costwatch", "/news/cost-watch/", 320, "news-costwatch"))
    for mode, extra in (("js-off", {}), ("js-on", {}),
                        ("js-on-open", {"clickFirst": "[data-read-more]"}),
                        ("js-on-filter", {"type": ["#cfilter-q", "bls"]}))
    if not (key == "news" and mode == "js-on-filter")
]


def check_read_more(key, off, on, opened, filtered, errors, results):
    """V16. With JS off nothing is truncated and no control exists; with JS on
    every truncated body has a rendered control, no control is dead, and no
    body shows more than three lines while truncated."""
    tag = key.upper()
    if off:
        b, c = off["bodies"], off["controls"]
        results[f"{key}_js_off_truncated"] = b["clipped"]
        if b["total"] == 0:
            errors.append(f"{tag}-JS-OFF: no item bodies in the markup — nothing to assert on")
        elif b["rendered"] != b["total"] or b["clipped"]:
            errors.append(f"{tag}-JS-OFF: {b['clipped']} of {b['total']} item bodies are "
                          f"truncated with JS off; the full text must render without script")
        if c["rendered"] or c["total"]:
            errors.append(f"{tag}-JS-OFF: {c['total']} Read more control(s) in the page with "
                          f"JS off ({c['rendered']} rendered) — a control with no behaviour")

    def js_on(label, m):
        b, c = m["bodies"], m["controls"]
        if b["unreachable"]:
            errors.append(f"{tag}-{label}: {b['unreachable']} truncated body(ies) with no "
                          f"rendered Read more — text the reader cannot reach")
        if c["orphanControls"]:
            errors.append(f"{tag}-{label}: {c['orphanControls']} Read more control(s) on a "
                          f"body that is not truncated — a control that does nothing")
        if c["rendered"] != b["clipped"]:
            errors.append(f"{tag}-{label}: {c['rendered']} controls for {b['clipped']} "
                          f"truncated bodies")

    if on:
        b = on["bodies"]
        results[f"{key}_js_on_truncated"] = b["clipped"]
        results[f"{key}_js_on_controls"] = on["controls"]["rendered"]
        if b["clipped"] == 0:
            errors.append(f"{tag}-JS-ON: no body is truncated at the measured width — the "
                          f"check cannot see its subject (a longer item or a narrower width "
                          f"is needed)")
        if b["clipped"] and b["maxLines"] > 3:
            errors.append(f"{tag}-JS-ON: a truncated body shows {b['maxLines']} lines, "
                          f"expected at most 3")
        js_on("JS-ON", on)
    if opened and on:
        b = opened["bodies"]
        results[f"{key}_js_on_open_truncated"] = b["clipped"]
        if b["clipped"] != on["bodies"]["clipped"] - 1:
            errors.append(f"{tag}-OPEN: pressing Read more left {b['clipped']} bodies "
                          f"truncated, expected {on['bodies']['clipped'] - 1}")
        js_on("OPEN", opened)
    if filtered:
        results[f"{key}_js_on_filter_controls"] = filtered["controls"]["rendered"]
        js_on("FILTER", filtered)


def check_site(payload, built: pathlib.Path):
    errors, results = [], {}

    by_name = {}
    for p in payload:
        if p.get("loadError"):
            errors.append(f"LOAD {p['name']} {p['route']}: {p['loadError']} "
                          f"(a check that cannot see its subject fails)")
            continue
        by_name[p["name"]] = p["measured"]

    def need(name):
        if name not in by_name:
            errors.append(f"MISSING measurement for {name}")
            return None
        return by_name[name]

    # 1. /receipts/ with JS off: every register row is rendered, and the
    #    show-more control is not — it must never appear as a dead button.
    m = need("receipts-js-off")
    if m:
        c = m["cards"]
        results["receipts_js_off_cards_rendered"] = c["rendered"]
        if c["rendered"] != REGISTER_CARDS:
            errors.append(f"RECEIPTS-JS-OFF: {c['rendered']} of {c['total']} register "
                          f"cards rendered, expected all {REGISTER_CARDS}")
        s = m["showmore"]
        results["receipts_js_off_showmore_rendered"] = s["rendered"]
        if s["total"] == 0:
            errors.append("RECEIPTS-JS-OFF: no [data-show-more] control in the markup "
                          "at all — the check has nothing to assert on")
        elif s["rendered"] != 0:
            errors.append(f"RECEIPTS-JS-OFF: show-more control is RENDERED "
                          f"({s['rendered']} visible) with JS off — a dead control. "
                          f"{s['attrHidden']} carry the hidden attribute, which is "
                          f"exactly the gap this check exists to catch")

    # 2. /receipts/ with JS on: the control appears and the list is paged.
    m = need("receipts-js-on")
    if m:
        s = m["showmore"]
        results["receipts_js_on_showmore_rendered"] = s["rendered"]
        if s["rendered"] < 1:
            errors.append("RECEIPTS-JS-ON: show-more control is not rendered with JS on")
        c = m["cards"]
        results["receipts_js_on_cards_rendered"] = c["rendered"]
        if c["rendered"] > SHOW_MORE_STEP:
            errors.append(f"RECEIPTS-JS-ON: {c['rendered']} cards rendered before any "
                          f"interaction; the control pages at {SHOW_MORE_STEP}")

    # 3. Search overlay with JS off: link blocks render, the input does not.
    m = need("search-js-off")
    if m:
        l = m["links"]
        results["search_js_off_links_rendered"] = l["rendered"]
        if l["total"] == 0:
            errors.append("SEARCH-JS-OFF: no .so-links anchors in the markup")
        elif l["rendered"] != l["total"]:
            errors.append(f"SEARCH-JS-OFF: only {l['rendered']} of {l['total']} link "
                          f"blocks rendered; with JS off they are the whole feature")
        b = m["searchbox"]
        results["search_js_off_box_rendered"] = b["rendered"]
        if b["rendered"] != 0:
            errors.append("SEARCH-JS-OFF: the search input is RENDERED with JS off — "
                          "a control that cannot do anything")

    # 4. V16 — Read more on both news routes.
    for key in ("news", "costwatch"):
        check_read_more(key, need(f"{key}-js-off"), need(f"{key}-js-on"),
                        need(f"{key}-js-on-open"),
                        need(f"{key}-js-on-filter") if key == "costwatch" else None,
                        errors, results)

    # 5. /news/uncost/ is a 301, not a page. Cloudflare applies _redirects, so
    #    this is asserted against the built artefacts: the rule is present and
    #    no real file shadows it (a static file would win over the redirect).
    red = built / "_redirects"
    if not red.is_file():
        errors.append("REDIRECT: no _redirects in the built output")
    else:
        text = red.read_text(encoding="utf-8")
        rule = re.search(r"^/news/uncost/\s+(\S+)\s+(\d{3})\s*$", text, re.M)
        if not rule:
            errors.append("REDIRECT: no /news/uncost/ rule in _redirects")
        else:
            target, code = rule.group(1), rule.group(2)
            results["news_uncost_redirect"] = f"{target} {code}"
            if code != "301":
                errors.append(f"REDIRECT: /news/uncost/ is {code}, expected 301")
            if target != "/news/":
                errors.append(f"REDIRECT: /news/uncost/ points at {target}, expected /news/")
        if (built / "news" / "uncost").exists():
            errors.append("REDIRECT: a built /news/uncost/ exists and would shadow "
                          "the redirect — a static file wins over _redirects")
        stale = [str(p.relative_to(built)) for p in built.rglob("*.html")
                 if "/news/uncost/" in p.read_text(encoding="utf-8", errors="replace")]
        results["links_to_news_uncost"] = len(stale)
        if stale:
            errors.append(f"REDIRECT: {len(stale)} built page(s) still link to "
                          f"/news/uncost/: {stale[:5]}")
    return errors, results


# --------------------------------------------------------------------------
# selftest — adversarial fixtures only, never a tracked source
# --------------------------------------------------------------------------
# The load-bearing case. The control carries the `hidden` ATTRIBUTE, and a
# higher-specificity display rule beats [hidden]{display:none}, so it renders
# anyway. A check reading el.hidden reports "hidden". This must FAIL.
BAD_HIDDEN_BEATEN = """<!doctype html><meta charset=utf-8><title>hidden beaten</title>
<style>[hidden]{display:none}
#register-cards > .card{display:flex}
[data-show-more]{display:block}
.card{padding:4px}</style>
<body><div id=register-cards>
""" + "".join(f'<div class="card">row {i}</div>' for i in range(26)) + """
</div><p data-show-more hidden>Show more</p></body>"""

# All 26 render and the control is genuinely not rendered. Must PASS.
GOOD_JS_OFF = """<!doctype html><meta charset=utf-8><title>good js-off</title>
<style>[hidden]{display:none}.card{padding:4px}</style>
<body><div id=register-cards>
""" + "".join(f'<div class="card">row {i}</div>' for i in range(26)) + """
</div><p data-show-more hidden>Show more</p>
<div class="search-ov"><div class="so-search" data-search-box hidden>
<input id=site-search></div>
<div class="so-links"><a href="/a/">A</a><a href="/b/">B</a></div></div></body>"""

# Rows missing with JS off — the list depends on script to exist. Must FAIL.
BAD_CARDS_HIDDEN = """<!doctype html><meta charset=utf-8><title>cards hidden</title>
<style>[hidden]{display:none}.card{padding:4px}
#register-cards > .card:nth-child(n+13){display:none}</style>
<body><div id=register-cards>
""" + "".join(f'<div class="card">row {i}</div>' for i in range(26)) + """
</div><p data-show-more hidden>Show more</p></body>"""

# The search input renders with JS off — a dead control. Must FAIL.
BAD_DEAD_SEARCHBOX = """<!doctype html><meta charset=utf-8><title>dead box</title>
<style>.so-search{display:block}</style>
<body><div class="search-ov"><div class="so-search" data-search-box>
<input id=site-search></div>
<div class="so-links"><a href="/a/">A</a></div></div></body>"""

# Link blocks present in markup but not rendered — nothing to fall back to.
BAD_NO_LINKS_RENDERED = """<!doctype html><meta charset=utf-8><title>no links</title>
<style>.so-links{display:none}</style>
<body><div class="search-ov"><div class="so-search" data-search-box hidden></div>
<div class="so-links"><a href="/a/">A</a><a href="/b/">B</a></div></div></body>"""


# V16 fixtures. One long body and one short body; `CLAMP_JS` is a minimal
# read-more (clamp every body, add a control only where it cuts). Run with JS
# off the good fixture shows full text and no control; run with JS on it
# truncates the long body and gives exactly that body a control.
_LONG = "Lorem ipsum dolor sit amet consectetur. " * 40
_READMORE_HTML = """<!doctype html><meta charset=utf-8><title>{t}</title>
<style>body{{width:600px;font:16px/1.5 sans-serif}}
p.cl{{display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:{n};overflow:hidden}}
{css}</style>
<body><div id=g><article data-news-item><p id=b1>""" + _LONG + """</p></article>
<article data-news-item><p id=b2>Short.</p></article></div>
<script>{js}</script></body>"""
CLAMP_JS = """document.querySelectorAll('[data-news-item] p').forEach(function(p){
  p.classList.add('cl');
  if (%s) { var b=document.createElement('button'); b.setAttribute('data-read-more','');
    b.setAttribute('aria-controls',p.id); b.textContent='Read more'; p.after(b); }
});"""
GOOD_READMORE = _READMORE_HTML.format(t="good read-more", n=3, css="",
                                     js=CLAMP_JS % "p.scrollHeight > p.clientHeight + 1")
# The clamp is CSS-only, so it cuts text with JS off and there is no control.
BAD_CLAMP_NO_JS = _READMORE_HTML.format(t="clamp without js", n=3,
                                       css="#g p{display:-webkit-box;-webkit-box-orient:vertical;"
                                           "-webkit-line-clamp:3;overflow:hidden}", js="")
# JS clamps but never adds a control: the rest of the text is unreachable.
BAD_UNREACHABLE = _READMORE_HTML.format(t="unreachable", n=3, css="", js=CLAMP_JS % "false")
# A control on every body, including the short one it cannot expand.
BAD_DEAD_CONTROL = _READMORE_HTML.format(t="dead control", n=3, css="", js=CLAMP_JS % "true")
# Clamped at five lines, not three.
BAD_FIVE_LINES = _READMORE_HTML.format(t="five lines", n=5, css="",
                                      js=CLAMP_JS % "p.scrollHeight > p.clientHeight + 1")


def write_fixtures():
    FIXTURES.mkdir(parents=True, exist_ok=True)
    for name, body in (
        ("good-js-off.html", GOOD_JS_OFF),
        ("bad-hidden-attr-beaten-by-specificity.html", BAD_HIDDEN_BEATEN),
        ("bad-cards-not-rendered.html", BAD_CARDS_HIDDEN),
        ("bad-dead-searchbox.html", BAD_DEAD_SEARCHBOX),
        ("bad-links-not-rendered.html", BAD_NO_LINKS_RENDERED),
        ("good-read-more.html", GOOD_READMORE),
        ("bad-read-more-clamp-without-js.html", BAD_CLAMP_NO_JS),
        ("bad-read-more-unreachable.html", BAD_UNREACHABLE),
        ("bad-read-more-dead-control.html", BAD_DEAD_CONTROL),
        ("bad-read-more-five-lines.html", BAD_FIVE_LINES),
    ):
        (FIXTURES / name).write_text(body, encoding="utf-8")
    (FIXTURES / "README.md").write_text(
        "# behaviour_checks fixtures\n\n"
        "Inputs for `python3 tools/behaviour_checks.py --selftest`. Fixtures\n"
        "only — the selftest never runs against website/dist or any tracked\n"
        "source.\n\n"
        "`bad-hidden-attr-beaten-by-specificity.html` is the one that matters.\n"
        "The control carries the `hidden` ATTRIBUTE and still renders, because\n"
        "`[hidden]{display:none}` is (0,1,0) and a class rule beats it. A check\n"
        "that reads `el.hidden` calls this page clean; this repository shipped\n"
        "exactly that bug (CANVAS-SYNC 66). The tool must assert on\n"
        "`offsetParent` and FAIL here.\n",
        encoding="utf-8",
    )


SELF_CASES = [   # (fixture, expected to pass, JS enabled)
    ("good-js-off.html", True, False),
    ("bad-hidden-attr-beaten-by-specificity.html", False, False),
    ("bad-cards-not-rendered.html", False, False),
    ("bad-dead-searchbox.html", False, False),
    ("bad-links-not-rendered.html", False, False),
    ("good-read-more.html", True, False),
    ("good-read-more.html", True, True),
    ("bad-read-more-clamp-without-js.html", False, False),
    ("bad-read-more-unreachable.html", False, True),
    ("bad-read-more-dead-control.html", False, True),
    ("bad-read-more-five-lines.html", False, True),
]


def selftest(port: int) -> int:
    write_fixtures()
    failures = []
    for name, should_pass, js in SELF_CASES:
        jobs = [{"name": "fixture", "route": "/" + name, "js": js,
                 "queries": {"cards": "#register-cards > .card",
                             "showmore": "[data-show-more]",
                             "links": ".search-ov .so-links a",
                             "searchbox": ".search-ov [data-search-box]",
                             "bodies": "[data-news-item] p",
                             "controls": "[data-read-more]"}}]
        payload = run_jobs(FIXTURES, jobs, port)
        errors = []
        for p in payload:
            if p.get("loadError"):
                errors.append(p["loadError"])
                continue
            m = p["measured"]
            # Same assertions as the site, applied only where the fixture
            # actually carries the thing being asserted on.
            if m["cards"]["total"]:
                if m["cards"]["rendered"] != REGISTER_CARDS:
                    errors.append(f"cards rendered {m['cards']['rendered']}")
                if m["showmore"]["total"] and m["showmore"]["rendered"] != 0:
                    errors.append(f"showmore rendered {m['showmore']['rendered']}")
            if m["links"]["total"]:
                if m["links"]["rendered"] != m["links"]["total"]:
                    errors.append(f"links rendered {m['links']['rendered']}"
                                  f"/{m['links']['total']}")
                if m["searchbox"]["total"] and m["searchbox"]["rendered"] != 0:
                    errors.append(f"searchbox rendered {m['searchbox']['rendered']}")
            if m["bodies"]["total"]:
                sub = []
                if js:
                    check_read_more("fixture", None, m, None, None, sub, {})
                else:
                    check_read_more("fixture", m, None, None, None, sub, {})
                errors.extend(sub)
        passed = not errors
        if passed != should_pass:
            failures.append({"fixture": name, "js": js,
                             "expected": "PASS" if should_pass else "FAIL",
                             "got": "PASS" if passed else "FAIL",
                             "sample": errors[:3]})
    print(json.dumps({"ok": not failures, "selftest_cases": len(SELF_CASES),
                      "failures": failures}, indent=2))
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--built", default=str(DEFAULT_BUILT))
    ap.add_argument("--port", type=int, default=8910)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest(args.port)

    built = pathlib.Path(args.built).resolve()
    if not built.is_dir():
        print(json.dumps({"ok": False, "errors": [f"no built directory at {built}"]}))
        return 1
    payload = run_jobs(built, SITE_JOBS, args.port)
    errors, results = check_site(payload, built)
    print(json.dumps({"ok": not errors, "errors": errors,
                      "counts": {"jobs": len(SITE_JOBS), "problems": len(errors)},
                      "measured": results}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Pages rendered from ONE template: do they render ONE structure?

Why this exists
---------------
The seven project pages have been one template since V20 (projects/project.njk),
yet the founder saw five of them "render differently" (Batch X, X14). A
template cannot differ from itself, so every difference is DATA — a field that
is empty on one page and filled on another, a list of a different length. This
tool renders each page and reports, section by section, exactly which elements
a page has that the reference page does not (and vice versa), so a difference
can be traced to the field that causes it instead of being eyeballed.

What it compares, per page, in the rendered DOM of <main>:
  - the section sequence (each direct child's data-screen-label, else tag.class)
  - within each section, the element signature: every element's tag and class
    list, in document order, collapsed to counts — so "one more sector link"
    shows as a count, and "no opener headline" shows as a missing h2.sec
Text is not compared: the pages are meant to say different things.

Usage
-----
    python3 tools/template_structure.py --reference /projects/human-essentials-dashboard/ \\
        --routes /projects/basic-needs-cost-model/ ... [--shots DIR] [--width 1440]
    python3 tools/template_structure.py --selftest
"""
from __future__ import annotations

import argparse
import collections
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
DEFAULT_BUILT = ROOT / "website" / "dist"
WEBSITE = ROOT / "website"

PROBE_JS = r"""
const puppeteer = require(require.resolve("puppeteer", { paths: [process.argv[2]] }));
const base = process.argv[3];
const job = JSON.parse(process.argv[4]);
(async () => {
  const browser = await puppeteer.launch({ args: ["--no-sandbox", "--force-device-scale-factor=1"] });
  const out = [];
  for (const route of job.routes) {
    const page = await browser.newPage();
    await page.setCacheEnabled(false);
    await page.setViewport({ width: job.width, height: 1000, deviceScaleFactor: 1 });
    let res;
    try { res = await page.goto(base + route, { waitUntil: "networkidle0", timeout: 60000 }); }
    catch (e) { out.push({ route, loadError: String(e).slice(0, 200) }); await page.close(); continue; }
    if (!res || !(res.ok() || res.status() === 304)) { out.push({ route, loadError: "HTTP " + (res && res.status()) }); await page.close(); continue; }
    await page.evaluate(() => document.fonts && document.fonts.ready);
    const sections = await page.evaluate(() => {
      const main = document.querySelector("main");
      if (!main) return null;
      const sig = (el) => el.tagName.toLowerCase() + (el.classList.length ? "." + [...el.classList].sort().join(".") : "");
      // The STYLE of each element signature's first instance, so a page whose
      // markup matches but whose stylesheet rules never reach it (rules scoped
      // to other pages' data-page) is caught too. Text-independent properties
      // only: colours, fonts, box edges, display.
      const PROPS = ["display", "background-color", "color", "font-family", "font-size", "font-weight",
                     "padding-top", "padding-left", "border-top-width", "border-left-width", "border-top-color"];
      const style = (e) => { const cs = getComputedStyle(e); return PROPS.map((p) => cs.getPropertyValue(p)).join("|"); };
      return [...main.children].filter((c) => !["SCRIPT", "TEMPLATE"].includes(c.tagName)).map((c) => {
        const counts = {}, styles = { ":self": style(c) };
        for (const e of c.querySelectorAll("*")) {
          const k = sig(e); counts[k] = (counts[k] || 0) + 1;
          if (!(k in styles)) styles[k] = style(e);
        }
        return { label: c.getAttribute("data-screen-label") || sig(c), self: sig(c), counts, styles,
                 height: Math.round(c.getBoundingClientRect().height) };
      });
    });
    if (job.shots) {
      await page.evaluate(() => document.querySelectorAll("*").forEach((e) => {
        const p = getComputedStyle(e).position; if (p === "fixed" || p === "sticky") e.style.visibility = "hidden"; }));
      const name = route.replace(/^\/|\/$/g, "").replace(/\//g, "__") || "index";
      await page.screenshot({ path: job.shots + "/" + name + "@" + job.width + ".png", fullPage: true });
    }
    out.push({ route, sections });
    await page.close();
  }
  await browser.close();
  process.stdout.write(JSON.stringify(out));
})().catch((e) => { console.error(e); process.exit(1); });
"""


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):   # the report is the output, not the access log
        pass


def serve(directory: pathlib.Path, port: int):
    handler = lambda *a, **kw: _Quiet(*a, directory=str(directory), **kw)
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def probe(directory: pathlib.Path, routes, width: int, port: int, shots: str | None):
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="uncost-structure-"))
    try:
        js = tmp / "probe.cjs"
        js.write_text(PROBE_JS, encoding="utf-8")
        httpd = serve(directory, port)
        try:
            proc = subprocess.run(["node", str(js), str(WEBSITE), f"http://127.0.0.1:{port}",
                                   json.dumps({"routes": routes, "width": width, "shots": shots})],
                                  capture_output=True, text=True, timeout=900)
        finally:
            httpd.shutdown()
            httpd.server_close()
        if proc.returncode != 0:
            raise RuntimeError(f"probe failed: {proc.stderr[-2000:]}")
        return json.loads(proc.stdout)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def compare(ref, page):
    """-> list of differences of `page` against `ref` (both probe records)."""
    diffs = []
    rs, ps = ref["sections"] or [], page["sections"] or []
    rl, pl = [s["label"] for s in rs], [s["label"] for s in ps]
    if rl != pl:
        diffs.append({"kind": "section-sequence", "reference": rl, "page": pl})
    rmap = {s["label"]: s for s in rs}
    for s in ps:
        r = rmap.get(s["label"])
        if not r:
            continue
        if r["self"] != s["self"]:
            diffs.append({"kind": "section-element", "section": s["label"], "reference": r["self"], "page": s["self"]})
        keys = sorted(set(r["counts"]) | set(s["counts"]))
        delta = {k: [r["counts"].get(k, 0), s["counts"].get(k, 0)] for k in keys
                 if r["counts"].get(k, 0) != s["counts"].get(k, 0)}
        if delta:
            diffs.append({"kind": "elements", "section": s["label"], "reference_vs_page": delta})
        rst, pst = r.get("styles", {}), s.get("styles", {})
        styled = sorted(k for k in set(rst) & set(pst) if rst[k] != pst[k])
        if styled:
            diffs.append({"kind": "styles", "section": s["label"], "elements": styled,
                          "example": {styled[0]: {"reference": rst[styled[0]], "page": pst[styled[0]]}}})
    return diffs


SELF = [
    # (name, reference sections, page sections, expected number of differences)
    ("identical", [{"label": "A", "self": "section", "counts": {"h2": 1, "p": 2}}],
                  [{"label": "A", "self": "section", "counts": {"h2": 1, "p": 2}}], 0),
    ("missing heading", [{"label": "A", "self": "section", "counts": {"h2": 1, "p": 2}}],
                        [{"label": "A", "self": "section", "counts": {"p": 2}}], 1),
    ("extra section", [{"label": "A", "self": "section", "counts": {}}],
                      [{"label": "A", "self": "section", "counts": {}}, {"label": "B", "self": "div", "counts": {}}], 1),
    ("different wrapper", [{"label": "A", "self": "section.blk", "counts": {}}],
                          [{"label": "A", "self": "section.blk.blk--cream", "counts": {}}], 1),
    # Same markup, but the page's elements are unstyled: the case X14 found.
    ("same markup, styles do not reach it",
     [{"label": "A", "self": "header", "counts": {"h1": 1}, "styles": {":self": "block|rgb(10, 10, 10)", "h1": "a"}}],
     [{"label": "A", "self": "header", "counts": {"h1": 1}, "styles": {":self": "block|rgba(0, 0, 0, 0)", "h1": "a"}}], 1),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--built", default=str(DEFAULT_BUILT))
    ap.add_argument("--reference")
    ap.add_argument("--routes", nargs="*", default=[])
    ap.add_argument("--width", type=int, default=1440)
    ap.add_argument("--port", type=int, default=8915)
    ap.add_argument("--shots", help="directory to save a full-page PNG of every route")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        failures = []
        for name, r, p, want in SELF:
            got = len(compare({"sections": r}, {"sections": p}))
            if got != want:
                failures.append({"case": name, "expected": want, "got": got})
        print(json.dumps({"ok": not failures, "selftest_cases": len(SELF), "failures": failures}, indent=2))
        return 1 if failures else 0

    if not args.reference:
        ap.error("--reference is required")
    built = pathlib.Path(args.built).resolve()
    shots = str(pathlib.Path(args.shots).resolve()) if args.shots else None
    if shots:
        pathlib.Path(shots).mkdir(parents=True, exist_ok=True)
    routes = [args.reference] + [r for r in args.routes if r != args.reference]
    data = probe(built, routes, args.width, args.port, shots)
    errors = [f"LOAD {d['route']}: {d['loadError']}" for d in data if d.get("loadError")]
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2))
        return 1
    ref = data[0]
    report = {d["route"]: compare(ref, d) for d in data[1:]}
    print(json.dumps({"ok": True, "reference": args.reference, "width": args.width,
                      "pages_identical_in_structure": [r for r, d in report.items() if not d],
                      "differences": {r: d for r, d in report.items() if d},
                      "sections": {d["route"]: [(s["label"], s["height"]) for s in d["sections"]] for d in data}},
                     indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

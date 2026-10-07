#!/usr/bin/env python3
"""Decision renders that prove their override applied (standing rule 6).

A render offered for a founder decision is evidence only if the page rendered
WITH the option differs, in pixels, from the page rendered without it — and
differs in the element the option changes. Batch U offered four PNGs of a
variant whose injected rules had lost the cascade; they showed the unchanged
page, and the founder chose between variants that did not exist. This tool
makes the check part of producing the render, not a step someone remembers.

For each route × width it renders the BASELINE (the shipped page) and every
VARIANT (the same page with the variant's CSS injected and, optionally, a
state change such as a <details> opened), clipped to the element under
decision. Each variant is then diffed against the baseline taken in the same
state:

  applies   the variant must change pixels inside the element's box
            (changed pixels > 0), and must not change anything on the page
            outside that box — an override that leaks is not the option shown
  n/a       at a width the option does not apply to (e.g. "open by default on
            desktop" at 390), the render must be pixel-identical

CSP is bypassed for the injected rules only (the site's style-src 'self'
would otherwise drop an injected <style> silently — exactly the failure this
tool exists to catch, but for the wrong reason).

Usage
-----
    python3 tools/decision_render.py tools/decisions/x12-drawer.json --out DIR
    python3 tools/decision_render.py --selftest
Writes one PNG per route × width × variant (and the baseline) into --out, and
an index.md summarising every check. Exit 1 if any variant fails its check.
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

from PIL import Image, ImageChops

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_BUILT = ROOT / "website" / "dist"
WEBSITE = ROOT / "website"
FIXTURES = ROOT / "tools" / "fixtures" / "decision"

PROBE_JS = r"""
const puppeteer = require(require.resolve("puppeteer", { paths: [process.argv[2]] }));
const base = process.argv[3];
const job = JSON.parse(process.argv[4]);
(async () => {
  const browser = await puppeteer.launch({ args: ["--no-sandbox", "--force-device-scale-factor=1"] });
  const out = [];
  for (const shot of job.shots) {
    const page = await browser.newPage();
    await page.setBypassCSP(true);
    await page.setCacheEnabled(false);
    // One fixed, tall viewport for EVERY shot. A full-page capture resizes the
    // viewport to the document's height and captures in tiles, so two renders
    // of different heights (an option that grows a drawer) rasterise the SAME
    // untouched content differently — measured on /sectors/ at 390 as 95,073
    // "changed" pixels in card images the override never reached. With the
    // same viewport and a plain viewport capture, baseline and variant differ
    // only where the page does.
    await page.setViewport({ width: shot.width, height: job.captureHeight, deviceScaleFactor: 1 });
    await page.goto(base + shot.route, { waitUntil: "networkidle0", timeout: 60000 });
    await page.evaluate(() => document.fonts && document.fonts.ready);
    // Lazy images load when a full-page capture scrolls them into view, at a
    // moment that differs between two renders of the same page — which reads
    // as "change" in rows the override never touched. Load every image first.
    await page.evaluate(async () => {
      for (const img of document.querySelectorAll('img[loading="lazy"]')) img.loading = "eager";
      await Promise.all([...document.images].filter((i) => !i.complete)
        .map((i) => new Promise((r) => { i.onload = i.onerror = r; })));
    });
    if (shot.css) await page.addStyleTag({ content: shot.css });
    await page.evaluate((s) => {
      document.querySelectorAll("*").forEach((e) => {
        const p = getComputedStyle(e).position;
        if (p === "fixed" || p === "sticky") e.style.visibility = "hidden";
      });
      if (s.open) document.querySelectorAll(s.open).forEach((d) => { d.open = true; });
      if (s.openAtLeast && innerWidth >= s.openAtLeast.minWidth)
        document.querySelectorAll(s.openAtLeast.selector).forEach((d) => { d.open = true; });
    }, shot);
    await new Promise((r) => setTimeout(r, 300));
    const box = await page.evaluate((sel) => {
      const e = document.querySelector(sel);
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return { x: 0, y: Math.round(r.top + scrollY), w: innerWidth, h: Math.round(r.height) };
    }, shot.selector);
    const docH = await page.evaluate(() => document.documentElement.scrollHeight);
    if (docH > job.captureHeight) throw new Error(`${shot.route}@${shot.width}: page is ${docH}px, taller than the ${job.captureHeight}px capture`);
    await page.screenshot({ path: shot.full });
    if (box) {
      const pad = 40;
      await page.screenshot({ path: shot.clip, clip: { x: 0, y: Math.max(0, box.y - pad), width: box.w, height: box.h + 2 * pad }, captureBeyondViewport: true });
    }
    out.push({ ...shot, box });
    await page.close();
  }
  await browser.close();
  process.stdout.write(JSON.stringify(out));
})().catch((e) => { console.error(e); process.exit(1); });
"""


# A pixel counts as changed only if its luminance moves by more than this. Two
# renders of the same image can differ by one or two levels (decoder and
# resampling noise: measured 242 -> 241 in a /sectors/ card image the override
# never touched); an override changes colours by far more.
NOISE = 8
CAPTURE_HEIGHT = 16000   # px; every shot uses this viewport (see the probe); under Chrome's 16384 texture limit


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve(directory: pathlib.Path, port: int):
    handler = lambda *a, **kw: _Quiet(*a, directory=str(directory), **kw)
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def run_probe(directory: pathlib.Path, shots, port: int):
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="uncost-decision-"))
    try:
        js = tmp / "probe.cjs"
        js.write_text(PROBE_JS, encoding="utf-8")
        httpd = serve(directory, port)
        try:
            proc = subprocess.run(["node", str(js), str(WEBSITE), f"http://127.0.0.1:{port}",
                                   json.dumps({"shots": shots, "captureHeight": CAPTURE_HEIGHT})], capture_output=True, text=True, timeout=900)
        finally:
            httpd.shutdown()
            httpd.server_close()
        if proc.returncode != 0:
            raise RuntimeError(f"probe failed: {proc.stderr[-2000:]}")
        return json.loads(proc.stdout)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def changed(a_path, b_path, box=None, inside=True):
    """Changed-pixel count between two full-page PNGs, inside or outside a box.
    Pages of different heights are compared over their common height, and the
    height difference itself counts as change (every row that exists in one
    only)."""
    a, b = Image.open(a_path).convert("RGB"), Image.open(b_path).convert("RGB")
    h, w = min(a.height, b.height), min(a.width, b.width)
    extra_rows = abs(a.height - b.height) * w
    diff = ImageChops.difference(a.crop((0, 0, w, h)), b.crop((0, 0, w, h))).convert("L").point(lambda v: 255 if v > NOISE else 0)
    if box is None:
        return sum(1 for v in diff.getdata() if v) + extra_rows
    y0, y1 = max(0, box["y"]), min(h, box["y"] + box["h"])
    inside_n = sum(1 for v in diff.crop((0, y0, w, y1)).getdata() if v) if y1 > y0 else 0
    if inside:
        return inside_n
    total = sum(1 for v in diff.getdata() if v)
    # Outside the element: rows above its box. Rows below it SHIFT when the
    # element changes height, so they are not "leaks"; only change above the
    # element counts as the override reaching something else.
    above = sum(1 for v in diff.crop((0, 0, w, max(0, box["y"]))).getdata() if v)
    return above


def run_spec(spec, built: pathlib.Path, out: pathlib.Path, port: int):
    out.mkdir(parents=True, exist_ok=True)
    shots = []
    for route in spec["routes"]:
        for width in spec["widths"]:
            slug = route.strip("/").replace("/", "__") or "index"
            for state in {v.get("state", "closed") for v in spec["variants"]}:
                shots.append({"id": f"{slug}@{width}:baseline:{state}", "route": route, "width": width,
                              "selector": spec["selector"], "css": "",
                              "open": spec["selector"] if state == "open" else None,
                              "full": str(out / f"_full-{slug}-baseline-{state}@{width}.png"),
                              "clip": str(out / f"{slug}-v1-baseline-{state}@{width}.png")})
            for v in spec["variants"]:
                shots.append({"id": f"{slug}@{width}:{v['name']}", "route": route, "width": width,
                              "selector": spec["selector"], "css": v.get("css", ""),
                              "open": spec["selector"] if v.get("state") == "open" else None,
                              "openAtLeast": v.get("openAtLeast"),
                              "full": str(out / f"_full-{slug}-{v['name']}@{width}.png"),
                              "clip": str(out / f"{slug}-{v['name']}@{width}.png")})
    rendered = {r["id"]: r for r in run_probe(built, shots, port)}
    results, failures = [], []
    for route in spec["routes"]:
        for width in spec["widths"]:
            slug = route.strip("/").replace("/", "__") or "index"
            for v in spec["variants"]:
                state = v.get("state", "closed")
                base = rendered[f"{slug}@{width}:baseline:{state}"]
                var = rendered[f"{slug}@{width}:{v['name']}"]
                # The element's region is the union of its box before and after:
                # an option that opens a drawer grows the box, and the growth is
                # the option.
                vb = var["box"]
                box = base["box"] if not (base["box"] and vb) else {
                    "y": min(base["box"]["y"], vb["y"]),
                    "h": max(base["box"]["y"] + base["box"]["h"], vb["y"] + vb["h"]) - min(base["box"]["y"], vb["y"])}
                applies = width in v.get("applies_at", spec["widths"])
                inside = changed(base["full"], var["full"], box, inside=True) if box else 0
                above = changed(base["full"], var["full"], box, inside=False) if box else 0
                total = changed(base["full"], var["full"])
                if applies:
                    ok = box is not None and inside > 0 and above == 0
                    why = ("no element to render" if box is None else
                           "the override changed NOTHING in the element — it did not apply" if inside == 0 else
                           f"the override also changed {above} px above the element" if above else "applied")
                else:
                    ok = total == 0
                    why = "identical, as it should be where the option does not apply" if ok else f"changed {total} px where the option should not apply"
                row = {"route": route, "width": width, "variant": v["name"], "label": v.get("label", ""),
                       "baseline_state": state, "applies": applies, "changed_in_element": inside,
                       "changed_above_element": above, "changed_total": total, "ok": ok, "check": why,
                       "png": pathlib.Path(var["clip"]).name, "baseline_png": pathlib.Path(base["clip"]).name}
                results.append(row)
                if not ok:
                    failures.append(row)
    for p in out.glob("_full-*.png"):
        p.unlink()
    return results, failures


def write_index(spec, results, out: pathlib.Path):
    lines = [f"# {spec.get('title', 'Decision renders')}", "",
             spec.get("intro", ""), "",
             "Every render below was diffed against its baseline by `tools/decision_render.py` "
             "(standing rule 6): a variant counts only if it changes pixels **inside the element under "
             "decision** and nothing above it; where an option does not apply, the render must be identical.",
             "", "| Page | Width | Variant | Baseline state | Changed px in element | Changed px above | Check |",
             "|---|---|---|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r['route']} | {r['width']} | {r['variant']} — {r['label']} | {r['baseline_state']} "
                     f"| {r['changed_in_element']} | {r['changed_above_element']} | {'✅' if r['ok'] else '❌'} {r['check']} |")
    lines += ["", "## Files", ""]
    for r in results:
        lines.append(f"- `{r['png']}` (baseline `{r['baseline_png']}`)")
    lines += ["", "## Variants", ""]
    for v in spec["variants"]:
        lines += [f"### {v['name']} — {v.get('label','')}", "", v.get("note", ""), "",
                  "```css", v.get("css", "").strip() or "/* no CSS — state change only */", "```", ""]
    (out / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


SELF_SPEC = {
    "routes": ["/page.html"], "widths": [800, 400], "selector": "#el",
    "variants": [
        {"name": "good-applies", "css": "#el{background:#123456}"},
        {"name": "bad-loses-cascade", "css": "#nope{background:#123456}"},
        {"name": "bad-leaks-above", "css": "#el{background:#123456} #top{background:#654321}"},
        {"name": "good-desktop-only", "css": "@media (min-width:600px){#el{background:#123456}}", "applies_at": [800]},
        {"name": "bad-not-desktop-only", "css": "#el{background:#123456}", "applies_at": [800]},
        # A one-level colour shift is noise, not an override: it must neither
        # pass as "applied" nor fail an n/a width.
        {"name": "noise-only", "css": "#el{background:#f9f9f9}", "applies_at": [800]},
    ],
}
SELF_EXPECT = {("good-applies", 800): True, ("good-applies", 400): True,
               ("bad-loses-cascade", 800): False, ("bad-loses-cascade", 400): False,
               ("bad-leaks-above", 800): False, ("bad-leaks-above", 400): False,
               ("good-desktop-only", 800): True, ("good-desktop-only", 400): True,
               ("bad-not-desktop-only", 800): True, ("bad-not-desktop-only", 400): False,
               ("noise-only", 800): False, ("noise-only", 400): True}
SELF_PAGE = """<!doctype html><meta charset=utf-8><title>decision fixture</title>
<style>body{margin:0;font:16px sans-serif}#top{height:120px;background:#eee}#el{height:200px;background:#fafafa}#bot{height:300px}</style>
<body><div id=top>top</div><div id=el>element under decision</div><div id=bot>below</div></body>"""


def selftest(port: int) -> int:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    (FIXTURES / "page.html").write_text(SELF_PAGE, encoding="utf-8")
    out = pathlib.Path(tempfile.mkdtemp(prefix="uncost-decision-selftest-"))
    try:
        results, _ = run_spec(SELF_SPEC, FIXTURES, out, port)
    finally:
        shutil.rmtree(out, ignore_errors=True)
    failures = [{"case": f"{r['variant']}@{r['width']}", "expected_ok": SELF_EXPECT[(r['variant'], r['width'])],
                 "got_ok": r["ok"], "check": r["check"]}
                for r in results if SELF_EXPECT[(r["variant"], r["width"])] != r["ok"]]
    print(json.dumps({"ok": not failures, "selftest_cases": len(results), "failures": failures}, indent=2))
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("spec", nargs="?")
    ap.add_argument("--built", default=str(DEFAULT_BUILT))
    ap.add_argument("--out")
    ap.add_argument("--port", type=int, default=8916)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest(args.port)
    if not args.spec or not args.out:
        ap.error("a spec and --out are required")
    spec = json.loads(pathlib.Path(args.spec).read_text(encoding="utf-8"))
    out = pathlib.Path(args.out)
    results, failures = run_spec(spec, pathlib.Path(args.built).resolve(), out, args.port)
    write_index(spec, results, out)
    print(json.dumps({"ok": not failures, "renders": len(results), "failures": failures,
                      "results": [{k: r[k] for k in ("route", "width", "variant", "changed_in_element",
                                                      "changed_above_element", "ok", "check")} for r in results]},
                     indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

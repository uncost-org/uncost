#!/usr/bin/env python3
"""Where did the site's icons come from? Compare them with open icon sets.

Takes every symbol in website/design-system/icons/icons.svg and every inline
<svg> drawing in website/src templates (the social marks excepted: they are
Simple Icons, NOTICE.md), and compares each with every icon of the sets given
on the command line (unpacked npm packages: lucide-static, feather-icons,
heroicons, @tabler/icons). The comparison is geometric, so markup differences
(a <line> against an equivalent <path>, attribute order) don't hide a match,
and stroke style doesn't create one: every icon is drawn in Chromium with the
same stroke (2 units, round caps and joins, no fill unless the shape sets
one) at 64px, and two icons are compared by the overlap of their inked
pixels (intersection over union).

  IoU >= 0.95   the same drawing (MATCH)
  0.80 - 0.95   close; a person should look (NEAR)
  below 0.80    different

Each icon reports its best candidate in each set. A trivial shape (three
lines, a plus, a check) can coincide with a set by geometry alone, so the
verdict rests on the non-trivial icons: provenance is claimed only when they
match too.

    python3 tools/icon_provenance.py --playwright-core DIR \\
        --set lucide=PKG/icons --set feather=PKG/dist/icons \\
        --set heroicons=PKG/24/outline --set tabler=PKG/icons/outline

Report only; exit 0. Standing rule 4: these are the results to report.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from axe_check import default_chromium  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPRITE = ROOT / "website" / "design-system" / "icons" / "icons.svg"
TEMPLATES = ROOT / "website" / "src"
SKIP = {"social-icons.njk"}

RUNNER = r"""
const { chromium } = require(process.env.PW_CORE);
const fs = require("fs");
const input = JSON.parse(fs.readFileSync(process.env.INPUT, "utf8"));
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM });
  const page = await browser.newPage();
  await page.setContent("<canvas id=c width=64 height=64></canvas>");
  const out = await page.evaluate(async ({ ours, sets }) => {
    const S = 64;
    const ctx = document.getElementById("c").getContext("2d", { willReadFrequently: true });
    const wrap = (inner, vb) => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${vb}" width="${S}" height="${S}" fill="none" stroke="#000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${inner}</svg>`;
    const mask = async (inner, vb) => {
      const img = new Image();
      img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(wrap(inner, vb));
      try { await img.decode(); } catch { return null; }
      ctx.clearRect(0, 0, S, S); ctx.drawImage(img, 0, 0, S, S);
      const d = ctx.getImageData(0, 0, S, S).data, m = new Uint8Array(S * S);
      let n = 0;
      for (let i = 0; i < S * S; i++) if (d[i * 4 + 3] > 96) { m[i] = 1; n++; }
      return n ? m : null;
    };
    const iou = (a, b) => { let i = 0, u = 0; for (let k = 0; k < a.length; k++) { if (a[k] & b[k]) i++; if (a[k] | b[k]) u++; } return u ? i / u : 0; };
    const lib = {};
    for (const [set, icons] of Object.entries(sets)) {
      lib[set] = [];
      for (const ic of icons) { const m = await mask(ic.inner, ic.vb); if (m) lib[set].push({ name: ic.name, m }); }
    }
    const res = [];
    for (const o of ours) {
      const m = await mask(o.inner, o.vb);
      const row = { id: o.id, where: o.where, best: {} };
      if (!m) { row.error = "did not render"; res.push(row); continue; }
      for (const [set, icons] of Object.entries(lib)) {
        let best = { name: null, iou: 0 };
        for (const ic of icons) { const v = iou(m, ic.m); if (v > best.iou) best = { name: ic.name, iou: v }; }
        row.best[set] = { name: best.name, iou: Math.round(best.iou * 1000) / 1000 };
      }
      res.push(row);
    }
    return { res, sizes: Object.fromEntries(Object.entries(lib).map(([k, v]) => [k, v.length])) };
  }, input);
  await browser.close();
  process.stdout.write(JSON.stringify(out));
})().catch((e) => { process.stderr.write(String(e && e.stack || e)); process.exit(2); });
"""


def inner_and_viewbox(svg: str) -> tuple[str, str]:
    m = re.search(r"<svg\b[^>]*>(.*)</svg>", svg, re.S)
    vb = re.search(r'viewBox="([^"]+)"', svg)
    return (m.group(1) if m else svg), (vb.group(1) if vb else "0 0 24 24")


def ours() -> list:
    out = []
    sprite = SPRITE.read_text(encoding="utf-8")
    for m in re.finditer(r'<symbol\b[^>]*id="([^"]+)"[^>]*viewBox="([^"]+)"[^>]*>(.*?)</symbol>', sprite, re.S):
        out.append({"id": "sprite#" + m.group(1), "where": "icons.svg", "vb": m.group(2), "inner": m.group(3)})
    for f in sorted(TEMPLATES.rglob("*.njk")):
        if f.name in SKIP:
            continue
        for n, m in enumerate(re.finditer(r"<svg\b[^>]*>.*?</svg>", f.read_text(encoding="utf-8"), re.S)):
            svg = m.group(0)
            if "<use " in svg:          # a reference into icons.svg, compared above
                continue
            inner, vb = inner_and_viewbox(svg)
            out.append({"id": f"{f.relative_to(TEMPLATES)}#{n + 1}", "where": str(f.relative_to(ROOT)), "vb": vb, "inner": inner})
    return out


def load_set(path: pathlib.Path) -> list:
    icons = []
    for f in sorted(path.glob("*.svg")):
        inner, vb = inner_and_viewbox(f.read_text(encoding="utf-8"))
        icons.append({"name": f.stem, "inner": inner, "vb": vb})
    return icons


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--playwright-core", required=True)
    ap.add_argument("--chromium")
    ap.add_argument("--set", action="append", required=True, help="name=DIR of .svg files")
    a = ap.parse_args()
    sets = {s.split("=", 1)[0]: load_set(pathlib.Path(s.split("=", 1)[1])) for s in a.set}
    chromium = pathlib.Path(a.chromium) if a.chromium else default_chromium()
    with tempfile.TemporaryDirectory() as tmp:
        inp = pathlib.Path(tmp) / "input.json"
        inp.write_text(json.dumps({"ours": ours(), "sets": sets}), encoding="utf-8")
        runner = pathlib.Path(tmp) / "icons-runner.cjs"
        runner.write_text(RUNNER, encoding="utf-8")
        env = {**os.environ, "PW_CORE": str(pathlib.Path(a.playwright_core).resolve()), "CHROMIUM": str(chromium), "INPUT": str(inp)}
        proc = subprocess.run(["node", str(runner)], env=env, capture_output=True, text=True, timeout=1800)
    if proc.returncode != 0:
        print(json.dumps({"ok": False, "errors": [proc.stderr[-2000:]]}, indent=1))
        return 2
    out = json.loads(proc.stdout)
    for row in out["res"]:
        best = max(row.get("best", {}).items(), key=lambda kv: kv[1]["iou"], default=(None, {"iou": 0}))
        v = best[1]["iou"]
        row["verdict"] = ("MATCH " if v >= 0.95 else "NEAR " if v >= 0.80 else "none ") + (f"{best[0]}:{best[1]['name']} ({v})" if best[0] else "")
    print(json.dumps({"set_sizes": out["sizes"], "icons": out["res"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

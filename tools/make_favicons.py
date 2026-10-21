#!/usr/bin/env python3
"""Favicon and app icons (founder choice C3, 2026-10-20; vector redraw, 2026-10-21).

Two sources, by size:

  SMALL — website/assets/favicon/favicon-robot.svg, a simplified vector redraw
  of the robot's head with bolder lines and bigger eyes, approved by the
  founder for tab sizes. It is served as /favicon.svg, and /favicon.ico is
  rendered from it at 16, 32 and 48 px by Chromium (through Playwright): each
  size is drawn from the vector at that size, never downscaled from a bitmap.

  LARGE — the whole head of website/assets/brand/robots/robot_01_front_transparent.png
  (ears and antenna included; everything above the neck), centred on a --coral
  #D64A1E rounded square with about 5% padding on each side, resampled from
  one large master. The detailed art reads well at these sizes.

    python3 tools/make_favicons.py --playwright-core DIR [--chromium PATH]

Writes to website/assets/favicon/:
  favicon.ico           16, 32 and 48 px, from the SVG
  icon-192.png          rounded square (web app manifest), from the art
  icon-512.png          rounded square (web app manifest), from the art
  apple-touch-icon.png  180 px, full square with no transparency; iOS rounds it
  preview-16.png, preview-32.png, preview-16@2x.png, preview-32@2x.png
                        the SVG at tab sizes, at 1x and 2x (not served)
  preview-sheet.png     those four on light and dark tab colours, at actual
                        size and magnified (not served; for review)

Both sources are licensed to Uncost by Dafuq Industries LLC
(LICENSES/LicenseRef-Dafuq-Industries-Uncost-Art.txt; NOTICE.md).
"""
from __future__ import annotations

import argparse
import io
import json
import os
import pathlib
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from axe_check import default_chromium  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "website" / "assets" / "brand" / "robots" / "robot_01_front_transparent.png"
OUT = ROOT / "website" / "assets" / "favicon"
SVG = OUT / "favicon-robot.svg"
TAB_LIGHT, TAB_DARK = (241, 243, 244, 255), (32, 33, 36, 255)   # browser tab strips

RUNNER = r"""
const { chromium } = require(process.env.PW_CORE);
const fs = require("fs");
const svg = fs.readFileSync(process.env.SVG);
const out = {};
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM });
  for (const scale of [1, 2]) {
    const page = await browser.newPage({ deviceScaleFactor: scale });
    for (const size of JSON.parse(process.env.SIZES)) {
      await page.setContent(`<html><body style="margin:0;background:transparent"><img id=i width=${size} height=${size} src="data:image/svg+xml;base64,${svg.toString("base64")}"></body></html>`);
      await page.waitForFunction(() => document.getElementById("i").complete && document.getElementById("i").naturalWidth > 0);
      out[`${size}@${scale}`] = (await (await page.$("#i")).screenshot({ omitBackground: true })).toString("base64");
    }
    await page.close();
  }
  await browser.close();
  process.stdout.write(JSON.stringify(out));
})().catch((e) => { process.stderr.write(String(e && e.stack || e)); process.exit(2); });
"""
CORAL = (0xD6, 0x4A, 0x1E, 255)
OUTLINE = (0x1A, 0x1A, 0x1A, 255)
MASTER = 1024
PADDING = 0.05      # of the icon's width, on each side
RADIUS = 0.20       # corner radius, as a share of the icon's width


def head(src: Image.Image) -> Image.Image:
    """Everything above the neck: the first row under the head that is narrow."""
    alpha = src.getchannel("A")
    w, h = src.size
    px = alpha.load()
    top = alpha.getbbox()[1]
    neck = next(y for y in range(top + h // 8, h)
                if sum(1 for x in range(w) if px[x, y] > 16) < w // 8)
    region = src.crop((0, 0, w, neck))
    return region.crop(region.getchannel("A").getbbox())


def master(rounded: bool) -> tuple[Image.Image, tuple[float, float]]:
    """The MASTER-px icon, plus where the antenna ball's centre lands (0..1)."""
    h = head(Image.open(SOURCE).convert("RGBA"))
    inner = MASTER * (1 - 2 * PADDING)
    scale = min(inner / h.width, inner / h.height)
    face = h.resize((round(h.width * scale), round(h.height * scale)), Image.LANCZOS)
    icon = Image.new("RGBA", (MASTER, MASTER), (0, 0, 0, 0))
    bg = Image.new("RGBA", (MASTER, MASTER), CORAL)
    if rounded:
        mask = Image.new("L", (MASTER, MASTER), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, MASTER - 1, MASTER - 1), radius=MASTER * RADIUS, fill=255)
        icon.paste(bg, (0, 0), mask)
    else:
        icon = bg
    x, y = (MASTER - face.width) // 2, (MASTER - face.height) // 2
    icon.alpha_composite(face, (x, y))
    # The antenna ball: the widest opaque run in the top tenth of the head.
    fa = face.getchannel("A").load()
    rows = [(sum(1 for i in range(face.width) if fa[i, j] > 128), j) for j in range(face.height // 10)]
    _, ball_y = max(rows)
    cols = [i for i in range(face.width) if fa[i, ball_y] > 128]
    ball = ((x + (min(cols) + max(cols)) / 2) / MASTER, (y + ball_y) / MASTER)
    return icon, ball


def sized(icon: Image.Image, ball: tuple[float, float], size: int) -> Image.Image:
    out = icon.resize((size, size), Image.LANCZOS)
    if size <= 16:
        out.putpixel((min(size - 1, int(ball[0] * size)), min(size - 1, int(ball[1] * size))), OUTLINE)
    return out


def render_svg(pw: pathlib.Path, chromium: pathlib.Path, sizes: list) -> dict:
    """{"16@1": Image, ...}: the SVG drawn by Chromium at each size, 1x and 2x."""
    with tempfile.TemporaryDirectory() as tmp:
        runner = pathlib.Path(tmp) / "favicon-runner.cjs"
        runner.write_text(RUNNER, encoding="utf-8")
        env = {**os.environ, "PW_CORE": str(pw), "CHROMIUM": str(chromium), "SVG": str(SVG), "SIZES": json.dumps(sizes)}
        proc = subprocess.run(["node", str(runner)], env=env, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0:
        raise SystemExit(proc.stderr[-2000:])
    import base64
    return {k: Image.open(io.BytesIO(base64.b64decode(v))).convert("RGBA") for k, v in json.loads(proc.stdout).items()}


def preview_sheet(r: dict) -> Image.Image:
    """16 and 32 px, 1x and 2x, on light and dark tab colours: x6 or so, then actual size."""
    cells = [(s, k) for s in (16, 32) for k in (1, 2)]
    sheet = Image.new("RGBA", (2 * len(cells) * 210 + 10, 300), (255, 255, 255, 255))
    d = ImageDraw.Draw(sheet)
    x = 10
    for bg, name in ((TAB_LIGHT, "light"), (TAB_DARK, "dark")):
        for s, k in cells:
            im = r[f"{s}@{k}"]
            tile = Image.new("RGBA", im.size, bg)
            tile.alpha_composite(im)
            mag = 192 // im.width
            sheet.paste(Image.new("RGBA", (200, 200), bg), (x, 4))
            sheet.paste(tile.resize((im.width * mag, im.height * mag), Image.NEAREST), (x + 4, 8))
            d.text((x, 208), f"{s}px {k}x on {name}", fill=(0, 0, 0, 255))
            sheet.paste(Image.new("RGBA", (76, 76), bg), (x, 222))
            sheet.paste(tile, (x + 38 - im.width // 2, 260 - im.height // 2))
            x += 210
    return sheet


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--playwright-core", required=True, help="the playwright-core package directory")
    ap.add_argument("--chromium", help="a Chromium executable (default: Playwright's newest installed)")
    a = ap.parse_args()
    chromium = pathlib.Path(a.chromium) if a.chromium else default_chromium()
    OUT.mkdir(parents=True, exist_ok=True)

    # Small: the vector, drawn by Chromium at each size.
    r = render_svg(pathlib.Path(a.playwright_core).resolve(), chromium, [16, 32, 48])
    ico = [r["16@1"], r["32@1"], r["48@1"]]
    ico[2].save(OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)], append_images=ico[:2])
    back = Image.open(OUT / "favicon.ico")
    for im in ico:      # the ICO must hold the renders themselves, not resamples
        back.size = im.size
        if back.convert("RGBA").tobytes() != im.tobytes():
            raise SystemExit(f"favicon.ico {im.size} is not the Chromium render")
    for s in (16, 32):
        r[f"{s}@1"].save(OUT / f"preview-{s}.png", optimize=True)
        r[f"{s}@2"].save(OUT / f"preview-{s}@2x.png", optimize=True)
    preview_sheet(r).convert("RGB").save(OUT / "preview-sheet.png", optimize=True)

    # Large: the detailed art.
    rounded, ball = master(rounded=True)
    square, _ = master(rounded=False)
    for s in (192, 512):
        sized(rounded, ball, s).save(OUT / f"icon-{s}.png", optimize=True)
    sized(square, ball, 180).convert("RGB").save(OUT / "apple-touch-icon.png", optimize=True)
    for f in sorted(OUT.iterdir()):
        print(f"{f.relative_to(ROOT)}  {f.stat().st_size} bytes")


if __name__ == "__main__":
    main()

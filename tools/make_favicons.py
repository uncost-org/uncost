#!/usr/bin/env python3
"""Favicon and app icons from the robot's head (founder choice C3, 2026-10-20).

The whole head of website/assets/brand/robots/robot_01_front_transparent.png
(ears and antenna included; everything above the neck) is centred on a
--coral #D64A1E rounded square with about 5% padding on each side. Each size
is resampled from one large master so the drawings match.

    python3 tools/make_favicons.py          # writes website/assets/favicon/

Writes:
  favicon.ico           16, 32 and 48 px, rounded square, transparent corners
  icon-192.png          rounded square (web app manifest)
  icon-512.png          rounded square (web app manifest)
  apple-touch-icon.png  180 px, full square with no transparency; iOS rounds it
  preview-16.png, preview-32.png  the 16 and 32 px icons, for review only
                        (not served)

The antenna stays at every size. From 32 px up it resamples as a ball on a
stalk. At 16 px it would fade into the coral, so after resampling the pixel
where the ball lands is set to the outline colour: a dot above the head.

The robot artwork is a reserved brand asset (website/assets/brand/RIGHTS.md);
these icons are derived from it and are reserved likewise (NOTICE.md).
"""
from __future__ import annotations

import pathlib

from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "website" / "assets" / "brand" / "robots" / "robot_01_front_transparent.png"
OUT = ROOT / "website" / "assets" / "favicon"
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


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rounded, ball = master(rounded=True)
    square, _ = master(rounded=False)
    icons = {s: sized(rounded, ball, s) for s in (16, 32, 48)}
    icons[48].save(OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)],
                   append_images=[icons[16], icons[32]])
    for s in (192, 512):
        sized(rounded, ball, s).save(OUT / f"icon-{s}.png", optimize=True)
    sized(square, ball, 180).convert("RGB").save(OUT / "apple-touch-icon.png", optimize=True)
    for s in (16, 32):
        icons[s].save(OUT / f"preview-{s}.png", optimize=True)
    for f in sorted(OUT.iterdir()):
        print(f"{f.relative_to(ROOT)}  {f.stat().st_size} bytes")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Pixel-compare built pages against the design export's own pages.

The node diff cannot see layout: it ignores text, whitespace and wrapper
elements, so a page can be node-identical and still render wrong. This renders
both with the same CSS in headless Chromium and compares pixels.
"""
import sys, pathlib
from PIL import Image, ImageChops

def load(p): return Image.open(p).convert("RGB")

def compare(a_path, b_path):
    a, b = load(a_path), load(b_path)
    if a.size != b.size:
        # Different page height is itself a layout difference worth reporting.
        h = min(a.height, b.height)
        a2, b2 = a.crop((0, 0, a.width, h)), b.crop((0, 0, min(a.width, b.width), h))
        if a2.size != b2.size:
            return {"size": (a.size, b.size), "pct": 100.0, "first_diff_y": 0}
        diff = ImageChops.difference(a2, b2)
        bbox = diff.getbbox()
        pct = _pct(diff)
        return {"size": (a.size, b.size), "pct": pct, "first_diff_y": bbox[1] if bbox else None}
    diff = ImageChops.difference(a, b)
    bbox = diff.getbbox()
    return {"size": (a.size, b.size), "pct": _pct(diff), "first_diff_y": bbox[1] if bbox else None}

def _pct(diff):
    hist = diff.convert("L").histogram()
    total = sum(hist)
    # Count pixels differing by more than a small antialiasing threshold.
    changed = sum(hist[8:])
    return round(100.0 * changed / total, 3) if total else 0.0

if __name__ == "__main__":
    ex, bu = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    print(f"{'shot':34} {'export hxw':>14} {'built hxw':>14} {'diff%':>7} {'firstY':>7}")
    for f in sorted(ex.glob("*.png")):
        cand = bu / f.name.replace("_html", "")
        if not cand.exists():
            alt = list(bu.glob(f.name.replace("_html", "").replace("@", "*@")))
            cand = alt[0] if alt else None
        if not cand or not cand.exists():
            print(f"{f.name:34} {'—':>14} {'MISSING':>14}")
            continue
        r = compare(f, cand)
        (aw, ah), (bw, bh) = r["size"]
        print(f"{f.name:34} {f'{ah}x{aw}':>14} {f'{bh}x{bw}':>14} {r['pct']:>7} {str(r['first_diff_y']):>7}")

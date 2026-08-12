#!/usr/bin/env python3
"""Rendered-pixel fidelity gate: built dist/ vs the design export's own pages.

The node diff cannot see layout — it ignores text, whitespace and wrappers, so a
page can be node-identical and still render wrong (the hero robot was). This
serves both trees, screenshots each page in headless Chromium at desktop and
mobile widths, and compares pixels.

    python3 tools/render_gate.py                 # every page
    python3 tools/render_gate.py index sectors   # only matching pages

Needs UNCOST_DESIGN_SOURCE to point at the unpacked export.
"""
import os, re, sys, json, shutil, subprocess, pathlib, tempfile, time, http.server, socketserver, threading
from PIL import Image, ImageChops

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPORT = pathlib.Path(os.environ.get("UNCOST_DESIGN_SOURCE", "../uncost-private/design-source"))
DIST = ROOT / "website" / "dist"
WIDTHS = [1440, 390]
# Pixels may differ slightly wherever a responsive derivative is shown instead of
# the export's full-size original — same box, softer pixels. Layout differences
# are far larger than this.
TOLERANCE_PCT = float(os.environ.get("RENDER_TOLERANCE", "3.0"))

sys.path.insert(0, str(ROOT / "tools"))
from design_diff import route_for  # same export-page -> built-route map

def serve(directory, port):
    handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(*a, directory=str(directory), **kw)
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd

def export_root():
    """The export's pages are root-relative (/css, /assets); stage a serve root."""
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="uncost-export-"))
    shutil.copytree(EXPORT / "pages", tmp, dirs_exist_ok=True)
    for d in ("css", "assets", "js"):
        (tmp / d).symlink_to(EXPORT / d)
    return tmp

def shot_name(route: str) -> str:
    """Mirror tools/shoot.cjs exactly, so filenames line up."""
    n = route.lstrip("/").rstrip("/")
    n = n.replace("/", "_").replace(".", "_")
    return n or "index"


def pct_diff(a_path, b_path):
    a, b = Image.open(a_path).convert("RGB"), Image.open(b_path).convert("RGB")
    if a.size != b.size:
        h = min(a.height, b.height)
        a, b = a.crop((0, 0, a.width, h)), b.crop((0, 0, a.width, h))
        penalty = True
    else:
        penalty = False
    d = ImageChops.difference(a, b).convert("L").histogram()
    total = sum(d) or 1
    return round(100.0 * sum(d[8:]) / total, 3), penalty

def main():
    only = sys.argv[1:]
    pages = []
    for p in sorted((EXPORT / "pages").rglob("*.html")):
        rel = str(p.relative_to(EXPORT / "pages"))
        route = route_for(rel)
        if route is None or not (DIST / route).exists():
            continue
        if only and not any(o in rel for o in only):
            continue
        pages.append((rel, route))

    root = export_root()
    s1, s2 = serve(root, 8801), serve(DIST, 8802)
    time.sleep(0.5)
    shots = pathlib.Path(tempfile.mkdtemp(prefix="uncost-shots-"))
    try:
        exp_routes = ["/" + rel for rel, _ in pages]
        built_routes = ["/" + r.replace("index.html", "") if r.endswith("/index.html") else "/" + r
                        for _, r in pages]
        subprocess.run(["node", str(ROOT / "tools" / "shoot.cjs"), "http://127.0.0.1:8801",
                        str(shots / "export"), ",".join(map(str, WIDTHS)), *exp_routes],
                       check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["node", str(ROOT / "tools" / "shoot.cjs"), "http://127.0.0.1:8802",
                        str(shots / "built"), ",".join(map(str, WIDTHS)), *built_routes],
                       check=True, stdout=subprocess.DEVNULL)
        rows, failed = [], 0
        for (rel, route), broute in zip(pages, built_routes):
            ename = shot_name("/" + rel)
            bname = shot_name(broute)
            worst = 0.0
            for w in WIDTHS:
                ep, bp = shots / "export" / f"{ename}@{w}.png", shots / "built" / f"{bname}@{w}.png"
                if not (ep.exists() and bp.exists()):
                    worst = 100.0; break
                pct, _ = pct_diff(ep, bp)
                worst = max(worst, pct)
            ok = worst <= TOLERANCE_PCT
            failed += 0 if ok else 1
            rows.append((rel, worst, ok))
        rows.sort(key=lambda r: r[1])
        print(f"{'page':44} {'worst diff %':>12}  verdict")
        for rel, worst, ok in rows:
            print(f"{rel:44} {worst:>12}  {'PASS' if ok else 'FAIL'}")
        print(f"\n{len(rows)-failed}/{len(rows)} pages render within {TOLERANCE_PCT}% at {WIDTHS}")
        print(f"screenshots: {shots}")
        return 1 if failed else 0
    finally:
        s1.shutdown(); s2.shutdown()

if __name__ == "__main__":
    raise SystemExit(main())

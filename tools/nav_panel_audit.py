#!/usr/bin/env python3
"""C8 nav-panel audit — each dropdown illustration is centred and ~70% tall.

The rule (integration.css item 91, Batch U C8): in every desktop nav dropdown
(`.hd-mega`), the illustration in the right-hand column (`.mg-pic`) is centred
on BOTH axes and drawn at ~70% of the panel's height.

What is measured is the DRAWN artwork, not the <img> box. The image is
`object-fit: contain`, so its box can be larger than what is painted; centring
the box proves nothing about where the picture is. The drawn rectangle is
derived from the box and the image's natural aspect ratio, the way the browser
letterboxes it. "Centred" is judged against the column's PADDING box — the
wheat area inside its 2px left border — because that is the area a reader sees
the picture sitting in.

Every panel is opened the way the site opens it (the `open` class), every
illustration is forced to load and decode first (they are lazy and hidden
until opened), and the audit fails on "I don't know": a panel that will not
open, an image that will not decode, or a panel with no illustration is an
error, never a skipped line.

    python3 tools/nav_panel_audit.py [--built DIR]
    python3 tools/nav_panel_audit.py --selftest

Prints JSON, including every panel's measurements. Exit 0 when ok.
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
DEFAULT_BUILT = ROOT / "website" / "dist"
WEBSITE = ROOT / "website"
FIXTURES = ROOT / "tools" / "fixtures" / "navpanel"
PORT = 8911
# Desktop widths only: below the nav breakpoint the panels are replaced by the
# drawer and never render.
WIDTHS = (1440, 1290, 1100)
ROUTES = ("/", "/about/")          # the header is one partial; two routes prove it
TARGET_PCT = 70.0
PCT_TOL = 3.0                      # "~70%": 67-73
CENTRE_TOL = 1.0                   # px, either axis

PROBE_JS = r"""
const puppeteer = require(require.resolve("puppeteer", { paths: [process.argv[2]] }));
const base = process.argv[3];
const routes = JSON.parse(process.argv[4]);
const widths = JSON.parse(process.argv[5]);
(async () => {
  const browser = await puppeteer.launch({ args: ["--no-sandbox", "--force-device-scale-factor=1"] });
  const page = await browser.newPage();
  await page.setCacheEnabled(false);
  const out = [];
  for (const route of routes) for (const w of widths) {
    await page.setViewport({ width: w, height: 1000, deviceScaleFactor: 1 });
    let res;
    try { res = await page.goto(base + route, { waitUntil: "load", timeout: 60000 }); }
    catch (e) { out.push({ route, width: w, error: String(e).slice(0, 200) }); continue; }
    if (!res || !(res.ok() || res.status() === 304)) {
      out.push({ route, width: w, error: "HTTP " + (res && res.status()) }); continue;
    }
    const panels = await page.evaluate(async () => {
      const r1 = (v) => Math.round(v * 10) / 10;
      const all = [...document.querySelectorAll(".hd-mega")];
      for (const i of document.querySelectorAll(".hd-mega img")) i.loading = "eager";
      const rows = [];
      for (const m of all) {
        all.forEach((x) => x.classList.remove("open"));
        m.classList.add("open");
        const label = m.getAttribute("aria-label") || "(unlabelled)";
        const mg = m.querySelector(".mg"), pic = m.querySelector(".mg-pic");
        const img = pic && pic.querySelector("img");
        if (!mg || !pic || !img) { rows.push({ label, error: "no .mg / .mg-pic / img in this panel" }); continue; }
        try { await img.decode(); } catch (e) {}
        if (!img.naturalWidth || !img.naturalHeight) { rows.push({ label, error: "illustration did not load" }); continue; }
        const P = mg.getBoundingClientRect();
        if (P.height === 0) { rows.push({ label, error: "panel did not open (zero height)" }); continue; }
        const cs = getComputedStyle(pic), C = pic.getBoundingClientRect(), I = img.getBoundingClientRect();
        const bl = parseFloat(cs.borderLeftWidth), br = parseFloat(cs.borderRightWidth);
        const bt = parseFloat(cs.borderTopWidth), bb = parseFloat(cs.borderBottomWidth);
        const pad = { x: C.left + bl, y: C.top + bt, w: C.width - bl - br, h: C.height - bt - bb };
        const fit = getComputedStyle(img).objectFit;
        let dw = I.width, dh = I.height;
        if (fit === "contain" || fit === "scale-down") {
          const nr = img.naturalWidth / img.naturalHeight, bxr = I.width / I.height;
          if (nr > bxr) { dw = I.width; dh = I.width / nr; } else { dh = I.height; dw = I.height * nr; }
        } else if (fit !== "fill") {
          rows.push({ label, error: "object-fit " + fit + " — drawn box cannot be derived" }); continue;
        }
        // object-position decides WHERE in the box the letterboxed artwork
        // sits; assuming the centre is exactly the box-not-art mistake.
        const op = getComputedStyle(img).objectPosition.trim().split(/\s+/);
        const place = (tok, free) => {
          if (/^-?[\d.]+%$/.test(tok)) return free * parseFloat(tok) / 100;
          if (/^-?[\d.]+px$/.test(tok)) return parseFloat(tok);
          return null;
        };
        const ox = op.length === 2 ? place(op[0], I.width - dw) : null;
        const oy = op.length === 2 ? place(op[1], I.height - dh) : null;
        if (ox === null || oy === null) {
          rows.push({ label, error: "object-position " + op.join(" ") + " — drawn box cannot be placed" }); continue;
        }
        const dx = I.left + ox, dy = I.top + oy;
        rows.push({ label, panelH: r1(P.height), drawnW: r1(dw), drawnH: r1(dh),
                    pct: r1(100 * dh / P.height),
                    offX: r1(dx + dw / 2 - (pad.x + pad.w / 2)),
                    offY: r1(dy + dh / 2 - (pad.y + pad.h / 2)) });
      }
      return rows;
    });
    out.push({ route, width: w, panels });
  }
  await browser.close();
  process.stdout.write(JSON.stringify(out));
})().catch((e) => { console.error(e); process.exit(1); });
"""


def serve(directory: pathlib.Path, port: int):
    handler_cls = type("Quiet", (http.server.SimpleHTTPRequestHandler,), {"log_message": lambda *a: None})
    handler = lambda *a, **kw: handler_cls(*a, directory=str(directory), **kw)
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def probe(directory: pathlib.Path, routes, widths, port: int):
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="uncost-navpanel-"))
    try:
        js = tmp / "probe.cjs"
        js.write_text(PROBE_JS, encoding="utf-8")
        httpd = serve(directory, port)
        try:
            proc = subprocess.run(["node", str(js), str(WEBSITE), f"http://127.0.0.1:{port}",
                                   json.dumps(list(routes)), json.dumps(list(widths))],
                                  capture_output=True, text=True, timeout=900)
        finally:
            httpd.shutdown()
            httpd.server_close()
        if proc.returncode != 0:
            raise RuntimeError("probe failed: " + proc.stderr[-2000:])
        return json.loads(proc.stdout)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def evaluate(payload):
    errors, rows = [], []
    for page in payload:
        where = f"{page['route']}@{page['width']}"
        if page.get("error"):
            errors.append(f"LOAD {where}: {page['error']}")
            continue
        if not page.get("panels"):
            errors.append(f"NO PANELS {where}: no .hd-mega found — nothing was audited")
            continue
        for p in page["panels"]:
            if p.get("error"):
                errors.append(f"UNRESOLVED {where} [{p['label']}]: {p['error']}")
                continue
            rows.append({"where": where, **p})
            if abs(p["pct"] - TARGET_PCT) > PCT_TOL:
                errors.append(f"SIZE {where} [{p['label']}]: drawn {p['drawnH']}px is {p['pct']}% of the "
                              f"{p['panelH']}px panel, target {TARGET_PCT}% +/-{PCT_TOL}")
            if abs(p["offX"]) > CENTRE_TOL or abs(p["offY"]) > CENTRE_TOL:
                errors.append(f"CENTRE {where} [{p['label']}]: drawn artwork is off-centre by "
                              f"x={p['offX']}px y={p['offY']}px (tolerance {CENTRE_TOL}px)")
    return errors, rows


# --------------------------------------------------------------------------
# selftest — fixtures only
# --------------------------------------------------------------------------
# A 3x4 PNG (portrait, like the site's artwork), inline so the fixtures need no
# binary file. The bad cases are the real defect classes: the export's floored
# 52% illustration, an image box that is centred while the drawn artwork inside
# it is not, and an illustration that never loads.
PNG = ("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAMAAAAECAIAAADETxJQAAAAF0lEQVR4nGPk4uJiYGBgYGBgYoABbCwABTwAJqfZ9QAAAAAASUVORK5CYII=")


def _page(title, css, img=PNG):
    return ("<!doctype html><meta charset=utf-8><title>%s</title><style>"
            "body{margin:0}.hd-mega{display:none}.hd-mega.open{display:block}"
            ".mg{display:grid;grid-template-columns:1fr 250px;min-height:268px}"
            ".mg-pic{border-left:2px solid #0A0A0A;background:#E8B84A;display:flex}%s</style>"
            "<div class=hd-mega aria-label=Fixture><div class=mg><div>text</div>"
            "<div class=mg-pic><img src='%s' alt=''></div></div></div>" % (title, css, img))


GOOD = _page("good", ".mg-pic{align-items:center;justify-content:center;padding:0 10px;contain:size}"
                     ".mg-pic img{height:70%;width:auto;max-width:100%;object-fit:contain}")
BAD_FLOORED = _page("floored", ".mg-pic{align-items:flex-end;justify-content:center;padding:10px}"
                               ".mg-pic img{max-height:140px;height:140px;width:auto;object-fit:contain}")
# The <img> BOX is centred and 70% tall, but it is far wider than the artwork's
# aspect and object-position pins the drawing to the left: the box passes, the
# picture does not. An audit that measured the box would call this clean.
BAD_BOX_ONLY = _page("box only", ".mg-pic{align-items:center;justify-content:center;padding:0 10px;contain:size}"
                                 ".mg-pic img{height:70%;width:100%;object-fit:contain;object-position:left center}")
BAD_UNLOADED = _page("unloaded", ".mg-pic{align-items:center;justify-content:center;contain:size}"
                                 ".mg-pic img{height:70%}", img="missing.png")

SELF_CASES = [
    ("good-centred-70.html", GOOD, True),
    ("bad-floored-52.html", BAD_FLOORED, False),
    ("bad-box-centred-art-not.html", BAD_BOX_ONLY, False),
    ("bad-unloaded.html", BAD_UNLOADED, False),
]


def selftest(port: int) -> int:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    for name, body, _ in SELF_CASES:
        (FIXTURES / name).write_text(body, encoding="utf-8")
    failures = []
    for name, _, should_pass in SELF_CASES:
        errors, _rows = evaluate(probe(FIXTURES, ["/" + name], (1440,), port))
        if (not errors) != should_pass:
            failures.append({"fixture": name, "expected": "PASS" if should_pass else "FAIL",
                             "got": "PASS" if not errors else "FAIL", "sample": errors[:2]})
    print(json.dumps({"ok": not failures, "selftest_cases": len(SELF_CASES), "failures": failures}, indent=2))
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--built", default=str(DEFAULT_BUILT))
    ap.add_argument("--port", type=int, default=PORT)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest(args.port)
    built = pathlib.Path(args.built).resolve()
    if not built.is_dir():
        print(json.dumps({"ok": False, "errors": [f"no built directory at {built}"]}))
        return 1
    errors, rows = evaluate(probe(built, ROUTES, WIDTHS, args.port))
    print(json.dumps({"ok": not errors, "errors": errors,
                      "counts": {"panels_measured": len(rows), "problems": len(errors)},
                      "panels": rows}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

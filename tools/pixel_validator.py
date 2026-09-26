#!/usr/bin/env python3
"""Validate band-boundary rules against RENDERED PIXELS, not the DOM's account.

Why this exists
---------------
DESIGN_IMPORT_RUNBOOK, standing rule 2 (2026-09-19): an audit's model of the
page is a hypothesis; screenshot the result, read the pixels, and where the two
disagree the pixels are right. This tool is the reference implementation named
there.

The R1 band audit modelled boundaries from selectors and collapsed two rules to
one wherever a framed component touched a boundary, without checking. What
actually shipped: `/join/` and `/policies/` rendered an ink frame edge stacked
on a coral band rule, and `/treasury/` rendered ONE coral rule 8px thick where
4px was declared. Every one of those is invisible to a DOM-only check and
obvious in the pixels.

Method
------
For each boundary between adjacent bands (direct children of <main>):

  1. Ask the browser where the boundary is and what the LOWER band declares on
     its top edge — plus, when a framed component sits flush against that edge
     (within FLUSH_PX), what that frame declares, since R2 says a flush frame
     edge IS the boundary.
  2. Read a vertical strip of real pixels through the boundary and run-length
     encode it by colour.
  3. Compare the rendered rule stack against the declared one.

A boundary is a defect when the pixels show more than one rule run, a run
thicker than declared, or a run in a colour nothing declared — whatever the DOM
says.

The clean set
-------------
`tools/data/pixel-baseline.json` records the boundaries that validate cleanly.
It is a SELF-DECLARED BASELINE: it was rebuilt from this tree, so it certifies
drift from that commit onward, not the correctness of the tree it was built
from. A boundary that was clean and stops being clean is a regression; a
boundary that was already wrong when the baseline was taken is recorded as
wrong, not as right.

Usage
-----
    python3 tools/pixel_validator.py                  # validate against baseline
    python3 tools/pixel_validator.py --rebuild-baseline
    python3 tools/pixel_validator.py --selftest
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

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    print(json.dumps({"ok": False, "errors": ["Pillow is required"]}))
    sys.exit(1)

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_BUILT = ROOT / "website" / "dist"
WEBSITE = ROOT / "website"
FIXTURES = ROOT / "tools" / "fixtures" / "pixel"
BASELINE = ROOT / "tools" / "data" / "pixel-baseline.json"

WIDTHS = (1440, 390)
FLUSH_PX = 4          # a frame edge within this of the band top IS the boundary
PROBE_PX = 14         # pixels read above and below the boundary
TOLERANCE_PX = 1      # sub-pixel rounding in rule thickness


PROBE_JS = r"""
const puppeteer = require(require.resolve("puppeteer", { paths: [process.argv[2]] }));
const base = process.argv[3];
const routes = JSON.parse(process.argv[4]);
const widths = JSON.parse(process.argv[5]);
const outDir = process.argv[6];
const FLUSH = JSON.parse(process.argv[7]);   // FLUSH_PX, injected from Python
const fs = require("node:fs");
const path = require("node:path");

(async () => {
  const browser = await puppeteer.launch({ args: ["--no-sandbox", "--force-device-scale-factor=1"] });
  const page = await browser.newPage();
  await page.setCacheEnabled(false);
  await page.emulateMediaFeatures([{ name: "prefers-reduced-motion", value: "reduce" }]);
  const out = [];
  for (const route of routes) {
    for (const w of widths) {
      await page.setViewport({ width: w, height: 1000, deviceScaleFactor: 1 });
      let res;
      try { res = await page.goto(base + route, { waitUntil: "load", timeout: 60000 }); }
      catch (e) { out.push({ route, width: w, loadError: String(e).slice(0, 200) }); continue; }
      if (!res || !(res.ok() || res.status() === 304)) {
        out.push({ route, width: w, loadError: "HTTP " + (res && res.status()) }); continue;
      }
      try { await page.evaluate(() => document.fonts && document.fonts.ready); } catch (e) {}
      await page.evaluate(async () => {
        for (const img of document.querySelectorAll('img[loading="lazy"]')) img.loading = "eager";
        await Promise.all([...document.images].filter(i => !i.complete)
          .map(i => new Promise(r => { i.onload = i.onerror = r; })));
      });
      await new Promise(r => setTimeout(r, 120));

      const data = await page.evaluate((FLUSH) => {
        const px = (v) => Math.round(parseFloat(v) || 0);
        const top = (el) => { const r = el.getBoundingClientRect();
                              return Math.round(r.top + window.scrollY); };
        const main = document.querySelector("main");
        if (!main) return { bands: [], boundaries: [] };
        const bands = [...main.children].filter((el) => {
          const r = el.getBoundingClientRect();
          return r.height > 0 && r.width > 0;
        });
        // V5 (2026-09-26): the stack does not end at </main>. The footer is the
        // band after it, and the seam between the two is a boundary like any
        // other — /contact/ shipped a frame edge stacked on the footer's rule
        // where no audit looked.
        const foot = main.nextElementSibling;
        if (foot && foot.tagName === "FOOTER") {
          const fr = foot.getBoundingClientRect();
          if (fr.height > 0 && fr.width > 0) bands.push(foot);
        }
        const label = (el) => el.getAttribute("data-screen-label") || el.id
          || (el.tagName.toLowerCase() + "." + (el.className || "").toString().trim().split(/\s+/).join("."));
        const bounds = [];
        for (let i = 1; i < bands.length; i++) {
          const lower = bands[i], upper = bands[i - 1];
          const cs = getComputedStyle(lower);
          const us = getComputedStyle(upper);
          const declared = [];
          if (px(cs.borderTopWidth) > 0)
            declared.push({ src: "band-top", w: px(cs.borderTopWidth), c: cs.borderTopColor });
          // R1 says nothing draws a bottom rule; if one does, that is itself
          // worth seeing, so it is declared and the stack check will catch the
          // doubling.
          if (px(us.borderBottomWidth) > 0)
            declared.push({ src: "upper-bottom", w: px(us.borderBottomWidth), c: us.borderBottomColor });
          // R2: a framed component flush against the boundary IS the boundary
          // — when it spans the band. An INSET component (narrower than the
          // band) touching the boundary draws its own frame edge across its
          // own width only; that edge is the component's, judged by
          // tools/frame_audit.py, not a band rule. Its columns are set aside
          // and the band boundary is read across the rest.
          const r = lower.getBoundingClientRect();
          const inset = [];
          const spans = (el) => { const q = el.getBoundingClientRect();
            return q.left - r.left <= FLUSH && r.right - q.right <= FLUSH; };
          for (const child of lower.children) {
            const ccs = getComputedStyle(child);
            if (px(ccs.borderTopWidth) <= 0) continue;
            if (Math.abs(top(child) - top(lower)) > FLUSH) continue;
            if (spans(child))
              declared.push({ src: "flush-frame", w: px(ccs.borderTopWidth), c: ccs.borderTopColor });
            else { const q = child.getBoundingClientRect();
              inset.push([Math.round(q.left), Math.round(q.right)]); }
          }
          const ub = upper.getBoundingClientRect();
          for (const child of upper.children) {
            const ccs = getComputedStyle(child);
            if (px(ccs.borderBottomWidth) <= 0) continue;
            const q = child.getBoundingClientRect();
            if (Math.abs(q.bottom - ub.bottom) > FLUSH || spans(child)) continue;
            inset.push([Math.round(q.left), Math.round(q.right)]);
          }
          bounds.push({
            index: i,
            label: label(lower),
            upperLabel: label(upper),
            y: top(lower),
            x: Math.round(r.left),
            width: Math.round(r.width),
            declared,
            inset,
            upperBg: us.backgroundColor,
            lowerBg: cs.backgroundColor,
          });
        }
        return { boundaries: bounds };
      }, FLUSH);

      // A full-page capture composites fixed and sticky overlays at their
      // VIEWPORT position, so at 390 the coral mobile pledge bar lands across
      // whatever boundary sits ~950px down the page and reads as the line —
      // /case/ "The mechanism" was reported "no rule renders" for exactly
      // that. Overlays float over the band stack and are not part of it, so
      // they come out for the capture, as tools/band_audit.py already does.
      // Bands themselves are never hidden.
      await page.evaluate(() => {
        const main = document.querySelector("main");
        const bands = new Set(main ? [...main.children] : []);
        for (const el of document.querySelectorAll("body *")) {
          if (bands.has(el)) continue;
          const pos = getComputedStyle(el).position;
          if (pos === "fixed" || pos === "sticky") el.style.visibility = "hidden";
        }
      });
      const name = (route.replace(/^\//, "").replace(/\/$/, "").replace(/[\/.]/g, "_") || "index") + "@" + w;
      const file = path.join(outDir, name + ".png");
      await page.screenshot({ path: file, fullPage: true });
      out.push({ route, width: w, shot: file, ...data });
    }
  }
  await browser.close();
  process.stdout.write(JSON.stringify(out));
})().catch((e) => { console.error(e); process.exit(1); });
"""


def serve(directory: pathlib.Path, port: int):
    handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(
        *a, directory=str(directory), **kw)
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def capture(directory: pathlib.Path, routes, widths, port: int, shots: pathlib.Path):
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="uncost-pixel-"))
    try:
        js = tmp / "probe.cjs"
        js.write_text(PROBE_JS, encoding="utf-8")
        shots.mkdir(parents=True, exist_ok=True)
        httpd = serve(directory, port)
        try:
            proc = subprocess.run(
                ["node", str(js), str(WEBSITE), f"http://127.0.0.1:{port}",
                 json.dumps(list(routes)), json.dumps(list(widths)), str(shots),
                 json.dumps(FLUSH_PX)],
                capture_output=True, text=True, timeout=2400)
        finally:
            httpd.shutdown()
            httpd.server_close()
        if proc.returncode != 0:
            raise RuntimeError(f"probe failed: {proc.stderr[-2000:]}")
        return json.loads(proc.stdout)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def css_rgb(s: str):
    s = (s or "").strip()
    if s.startswith("#") and len(s) == 7:
        return (int(s[1:3], 16), int(s[3:5], 16), int(s[5:7], 16))
    if s.startswith("rgb"):
        nums = [n for n in s[s.find("(") + 1:s.find(")")].replace("/", ",").split(",") if n.strip()]
        try:
            v = [float(n) for n in nums]
        except ValueError:
            return None
        if len(v) >= 3:
            return (int(round(v[0])), int(round(v[1])), int(round(v[2])))
    return None


def close(a, b, tol=10):
    return a is not None and b is not None and all(abs(a[i] - b[i]) <= tol for i in range(3))


def rle_column(img: Image.Image, x: int, y0: int, y1: int):
    """Run-length encode one pixel column by colour."""
    runs = []
    for y in range(max(0, y0), min(img.height, y1)):
        c = img.getpixel((x, y))[:3]
        if runs and close(runs[-1][0], c, tol=6):
            runs[-1][1] += 1
        else:
            runs.append([c, 1])
    return [(tuple(c), n) for c, n in runs]


COLUMN_STEP = 16          # sample every Nth pixel column across the boundary
MODAL_SHARE = 0.5         # the modal verdict must hold this share of columns


def validate_boundary(img, b, width):
    """Return (key, problems) for one boundary: the MODAL verdict across columns.

    One column at the band's centre was the whole reading until 2026-09-25.
    A single column cannot tell a rule from a vertical divider it happens to
    stand on (a four-column grid puts a gap exactly at 50%), or from a glyph
    crossing the probe window, so both read as defects that nobody can see.
    Every COLUMN_STEP-th column is now read and the most common verdict
    stands, the way tools/band_audit.py already reads a boundary. When no
    verdict holds MODAL_SHARE of the columns the boundary is an error, never
    a pass: the pixels disagree with themselves and nothing can be concluded.
    """
    key = f"{b['upperLabel']} -> {b['label']}"
    x0, x1 = b["x"] + 2, min(img.width, b["x"] + b["width"]) - 2
    # Columns under an inset component's flush edge belong to that component.
    inset = b.get("inset") or []
    xs = [x for x in range(x0, x1, COLUMN_STEP)
          if not any(lo - 2 <= x <= hi + 2 for lo, hi in inset)]
    if not xs:
        return key, [f"{key}: boundary is too narrow to read ({b['width']}px)"]
    votes = collections.Counter(tuple(_validate_column(img, b, x, key)) for x in xs)
    verdict, n = votes.most_common(1)[0]
    if n / len(xs) < MODAL_SHARE:
        return key, [f"{key}: no pixel verdict — the most common reading holds "
                     f"{n}/{len(xs)} columns, under {MODAL_SHARE:.0%}"]
    return key, list(verdict)


def _validate_column(img, b, x, key):
    """Problems for one pixel column through the boundary (empty = clean)."""
    y = b["y"]
    problems = []
    if not (0 <= x < img.width):
        return [f"{key}: boundary x={x} is outside the {img.width}px shot"]
    runs = rle_column(img, x, y - PROBE_PX, y + PROBE_PX)
    # The two band fills are read from the PIXELS at the ends of the probe
    # window, not from computed style. A band whose own background is
    # transparent (most of them — the page, or a full-width child, paints
    # the fill) computes to rgba(0,0,0,0), and css_rgb() drops the alpha and
    # returns black. Once C1 moved --ink to #0A0A0A, every ink rule was
    # within tolerance of that phantom black, was counted as band fill, and
    # was reported as "no rule renders" — the tool contradicting a line that
    # is plainly on screen. Before C1 the ink was #0E0E0C, 14 points from
    # black, which is the only reason this went unnoticed.
    if len(runs) >= 2:
        upper, lower = runs[0][0], runs[-1][0]
    else:
        upper = css_rgb(b.get("upperBg"))
        lower = css_rgb(b.get("lowerBg"))
    declared = b.get("declared", [])
    decl_set = [(d["w"], css_rgb(d["c"]), d["src"]) for d in declared]

    # A "rule run" is a run that is neither the upper band's fill nor the
    # lower band's fill. Runs touching the ends of the probe window are the
    # bands themselves.
    rule_runs = []
    for i, (c, n) in enumerate(runs):
        if i == 0 or i == len(runs) - 1:
            continue
        if close(c, upper) or close(c, lower):
            continue
        rule_runs.append((c, n))

    if not decl_set and not rule_runs:
        return []                      # same-colour bands, no rule: fine
    if not decl_set and rule_runs:
        problems.append(
            f"{key}: pixels show {len(rule_runs)} rule run(s) "
            f"{[(f'#%02X%02X%02X' % c, n) for c, n in rule_runs]} but nothing "
            f"declares a rule on this boundary")
        return problems
    if decl_set and not rule_runs:
        problems.append(
            f"{key}: declares {[(w, src) for w, _c, src in decl_set]} but no rule "
            f"renders at the boundary")
        return problems
    if len(rule_runs) > 1:
        problems.append(
            f"{key}: {len(rule_runs)} rule runs render where a boundary may carry "
            f"exactly one — {[(f'#%02X%02X%02X' % c, n) for c, n in rule_runs]} "
            f"(declared {[(w, src) for w, _c, src in decl_set]})")
        return problems

    c, n = rule_runs[0]
    match = None
    for w, dc, src in decl_set:
        if close(c, dc) and abs(n - w) <= TOLERANCE_PX:
            match = (w, src)
            break
    if match is None:
        thick = [w for w, dc, _s in decl_set if close(c, dc)]
        if thick:
            problems.append(
                f"{key}: rule renders {n}px in #%02X%02X%02X against {thick[0]}px "
                f"declared" % c)
        else:
            problems.append(
                f"{key}: rule renders #%02X%02X%02X at {n}px; declared colours are "
                f"{[('#%02X%02X%02X' % dc) if dc else None for _w, dc, _s in decl_set]}" % c)
    return problems


def run(directory: pathlib.Path, routes, port: int):
    shots = pathlib.Path(tempfile.mkdtemp(prefix="uncost-pixel-shots-"))
    try:
        payload = capture(directory, routes, WIDTHS, port, shots)
        errors, clean, checked = [], [], 0
        for page in payload:
            route, width = page.get("route"), page.get("width")
            if page.get("loadError"):
                errors.append(f"LOAD {route}@{width}: {page['loadError']} "
                              f"(an audit that cannot see its subject fails)")
                continue
            img = Image.open(page["shot"]).convert("RGB")
            for b in page.get("boundaries", []):
                checked += 1
                key, problems = validate_boundary(img, b, width)
                full = f"{route}@{width} {key}"
                if problems:
                    errors.extend(f"{route}@{width} {p}" for p in problems)
                else:
                    clean.append(full)
        return errors, clean, checked
    finally:
        shutil.rmtree(shots, ignore_errors=True)


def routes_in(directory: pathlib.Path):
    out = []
    for p in sorted(directory.rglob("*.html")):
        rel = p.relative_to(directory)
        out.append("/" + str(rel.parent).replace("\\", "/").strip(".").strip("/") + "/"
                   if rel.name == "index.html" else "/" + str(rel).replace("\\", "/"))
    return ["/" if r == "//" else r for r in out]


# --------------------------------------------------------------------------
# fixtures + selftest
# --------------------------------------------------------------------------
def _page(title, css, bands):
    return (f"<!doctype html><meta charset=utf-8><title>{title}</title>"
            f"<style>body{{margin:0}}main{{display:block}}{css}</style>"
            f"<body><main>{bands}</main></body>")


BANDS = ('<section class="a" data-screen-label="A">A</section>'
         '<section class="b" data-screen-label="B">B</section>')
BASE = (".a{background:#FAF7F0;height:80px}"
        ".b{background:#E8B84A;height:80px}")

GOOD_ONE_RULE = _page("one rule", BASE + ".b{border-top:4px solid #D64A1E}", BANDS)
GOOD_NO_RULE = _page("same colour", ".a{background:#FAF7F0;height:80px}"
                     ".b{background:#FAF7F0;height:80px}", BANDS)
# Both edges draw: the exact doubling R1 exists to stop.
BAD_DOUBLE = _page("double", BASE + ".a{border-bottom:4px solid #0E0E0C}"
                   ".b{border-top:4px solid #D64A1E}", BANDS)
# The /treasury/ defect. Two 4px rules in the SAME colour stack and merge into
# one 8px run, so the pixels show a single rule of twice the declared weight.
# The distinct-colour version (BAD_DOUBLE) shows up as two runs; this one shows
# up as one run that is wrong, which is the harder case and the one that
# shipped.
BAD_THICK = _page("thick", BASE + ".a{border-bottom:4px solid #D64A1E}"
                  ".b{border-top:4px solid #D64A1E}", BANDS)
# A frame edge stacked on a band rule — the /join/ and /policies/ defect.
BAD_FRAME_STACK = _page(
    "frame stack",
    BASE + ".b{border-top:4px solid #D64A1E}.f{border:2px solid #0E0E0C;margin:0}",
    '<section class="a" data-screen-label="A">A</section>'
    '<section class="b" data-screen-label="B"><div class="f">framed</div></section>')
# A rule renders that nothing declares (drawn by a child's background).
BAD_UNDECLARED = _page(
    "undeclared",
    ".a{background:#FAF7F0;height:80px}.b{background:#E8B84A;height:80px}"
    ".r{height:6px;background:#0E0E0C}",
    '<section class="a" data-screen-label="A">A</section>'
    '<section class="b" data-screen-label="B"><div class="r"></div>B</section>')

# A correct boundary whose CENTRE column stands on a vertical ink divider: the
# lower band is a two-column grid with a 2px ink gap at exactly 50%. A reader
# sees one coral rule. A single centre column saw only ink and called it a
# defect — the /treasury/ and /404 false findings. Must PASS.
GOOD_DIVIDER_AT_CENTRE = _page(
    "divider at centre",
    ".a{background:#FAF7F0;height:80px}"
    ".b{border-top:4px solid #D64A1E;display:grid;grid-template-columns:1fr 1fr;"
    "gap:2px;background:#0A0A0A;height:80px}.b>div{background:#FAF7F0}",
    '<section class="a" data-screen-label="A">A</section>'
    '<section class="b" data-screen-label="B"><div>one</div><div>two</div></section>')
# The same grid with the boundary rule drawn twice. Every column but the
# divider shows the doubling, so the modal reading must still FAIL it —
# reading more columns must not dilute a real defect.
BAD_DOUBLE_WITH_DIVIDER = _page(
    "double with divider",
    ".a{background:#FAF7F0;height:80px;border-bottom:4px solid #0A0A0A}"
    ".b{border-top:4px solid #D64A1E;display:grid;grid-template-columns:1fr 1fr;"
    "gap:2px;background:#0A0A0A;height:80px}.b>div{background:#FAF7F0}",
    '<section class="a" data-screen-label="A">A</section>'
    '<section class="b" data-screen-label="B"><div>one</div><div>two</div></section>')

# An INSET framed box whose top edge touches a same-colour boundary. The band
# boundary itself carries no rule, correctly; the box's edge is the box's.
# Columns inside and outside the box disagree, so without setting the box's
# columns aside there is no majority reading. Must PASS.
GOOD_INSET_BOX = _page(
    "inset box",
    ".a{background:#FAF7F0;height:80px}.b{background:#FAF7F0;height:80px}"
    ".box{border:2px solid #0A0A0A;margin:0 auto;max-width:40%;height:40px}",
    '<section class="a" data-screen-label="A">A</section>'
    '<section class="b" data-screen-label="B"><div class="box"></div></section>')

# A correct boundary with a position:fixed coral bar parked over it in the
# viewport — the /case/ 390 false finding. A full-page capture paints the bar
# at its viewport position, across the boundary. Must PASS.
GOOD_FIXED_OVERLAY = _page(
    "fixed overlay",
    ".a{background:#FAF7F0;height:950px}.b{background:#F2EDE1;height:400px;"
    "border-top:4px solid #D64A1E}"
    ".bar{position:fixed;left:0;right:0;bottom:0;height:70px;background:#D64A1E}",
    '<section class="a" data-screen-label="A">A</section>'
    '<section class="b" data-screen-label="B">B</section>'
    '</main><div class="bar">Sign the Pledge</div><main>')

# V5: the seam past </main>. A cream last band over a footer that draws the
# boundary: one rule, PASS. The same seam with the last band ALSO drawing a
# bottom rule: two rules stacked where one belongs — an audit that stops at
# </main> never reads it. Must FAIL.
FOOTER_TAIL = ("<footer style='border-top:4px solid #D64A1E'>"
               "<div style='background:#E8B84A;height:80px'>footer</div></footer>")
GOOD_FOOTER_SEAM = _page("footer seam", ".a{background:#FAF7F0;height:80px}",
                         '<section class="a" data-screen-label="A">A</section>'
                         ) .replace("</main></body>", "</main>" + FOOTER_TAIL + "</body>")
BAD_FOOTER_DOUBLE = _page("footer double", ".a{background:#FAF7F0;height:80px;"
                          "border-bottom:4px solid #0A0A0A}",
                          '<section class="a" data-screen-label="A">A</section>'
                          ).replace("</main></body>", "</main>" + FOOTER_TAIL + "</body>")

SELF_CASES = [
    ("good-one-rule.html", GOOD_ONE_RULE, True),
    ("good-footer-seam.html", GOOD_FOOTER_SEAM, True),
    ("bad-footer-double-rule.html", BAD_FOOTER_DOUBLE, False),
    ("good-fixed-overlay-over-boundary.html", GOOD_FIXED_OVERLAY, True),
    ("good-inset-box-at-boundary.html", GOOD_INSET_BOX, True),
    ("good-divider-at-centre.html", GOOD_DIVIDER_AT_CENTRE, True),
    ("bad-double-with-divider.html", BAD_DOUBLE_WITH_DIVIDER, False),
    ("good-no-rule-same-colour.html", GOOD_NO_RULE, True),
    ("bad-double-rule.html", BAD_DOUBLE, False),
    ("bad-rule-thicker-than-declared.html", BAD_THICK, False),
    ("bad-frame-stacked-on-band-rule.html", BAD_FRAME_STACK, False),
    ("bad-undeclared-rule.html", BAD_UNDECLARED, False),
]


def write_fixtures():
    FIXTURES.mkdir(parents=True, exist_ok=True)
    for name, body, _ in SELF_CASES:
        (FIXTURES / name).write_text(body, encoding="utf-8")
    (FIXTURES / "README.md").write_text(
        "# pixel_validator fixtures\n\n"
        "Inputs for `python3 tools/pixel_validator.py --selftest`. Fixtures\n"
        "only — the selftest never runs against website/dist or any tracked\n"
        "source.\n\n"
        "Each `bad-*` file reproduces a defect this repository actually\n"
        "shipped past a DOM-only check:\n\n"
        "- `bad-double-rule` — both the upper band's bottom edge and the lower\n"
        "  band's top edge draw, so the boundary carries two rules.\n"
        "- `bad-rule-thicker-than-declared` — 8px renders where 4px is\n"
        "  declared (`/treasury/`).\n"
        "- `bad-frame-stacked-on-band-rule` — a component's frame edge sits on\n"
        "  top of the band rule (`/join/`, `/policies/`).\n"
        "- `bad-undeclared-rule` — a child's background draws a rule no border\n"
        "  declares, so the DOM reports the boundary as bare.\n",
        encoding="utf-8")


def selftest(port: int) -> int:
    write_fixtures()
    failures = []
    for name, _body, should_pass in SELF_CASES:
        errors, _clean, checked = run(FIXTURES, ["/" + name], port)
        passed = not errors
        if checked == 0:
            failures.append({"fixture": name, "expected": "PASS" if should_pass else "FAIL",
                             "got": "NO BOUNDARY MEASURED",
                             "sample": ["the validator found nothing to check, so this "
                                        "case proves nothing"]})
            continue
        if passed != should_pass:
            failures.append({"fixture": name,
                             "expected": "PASS" if should_pass else "FAIL",
                             "got": "PASS" if passed else "FAIL",
                             "sample": errors[:2]})
    print(json.dumps({"ok": not failures, "selftest_cases": len(SELF_CASES),
                      "failures": failures}, indent=2))
    return 1 if failures else 0


BASELINE_LABEL = ("self-declared baseline at ddc77f0 — certifies drift from here, "
                  "not the correctness of this tree")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--built", default=str(DEFAULT_BUILT))
    ap.add_argument("--routes", nargs="*")
    ap.add_argument("--port", type=int, default=8870)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--rebuild-baseline", action="store_true")
    ap.add_argument("--max-errors", type=int, default=40)
    args = ap.parse_args()

    if args.selftest:
        return selftest(args.port)

    built = pathlib.Path(args.built).resolve()
    if not built.is_dir():
        print(json.dumps({"ok": False, "errors": [f"no built directory at {built}"]}))
        return 1
    routes = args.routes or routes_in(built)
    errors, clean, checked = run(built, routes, args.port)

    if args.rebuild_baseline:
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(json.dumps({
            "label": BASELINE_LABEL,
            "commit": "ddc77f0",
            "widths": list(WIDTHS),
            "boundaries_checked": checked,
            "clean": sorted(clean),
            "not_clean": sorted(errors),
        }, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"ok": True, "wrote": str(BASELINE.relative_to(ROOT)),
                          "label": BASELINE_LABEL,
                          "counts": {"boundaries": checked, "clean": len(clean),
                                     "not_clean": len(errors)}}, indent=2))
        return 0

    if not BASELINE.is_file():
        print(json.dumps({"ok": False, "errors": [
            f"no baseline at {BASELINE.relative_to(ROOT)}; run --rebuild-baseline"]}))
        return 1
    base = json.loads(BASELINE.read_text(encoding="utf-8"))
    was_clean = set(base.get("clean", []))
    now_clean = set(clean)
    regressions = sorted(was_clean - now_clean)
    # Newly clean boundaries are reported, never failed on.
    recovered = sorted(now_clean - was_clean)
    print(json.dumps({
        "ok": not regressions,
        "baseline": {"label": base.get("label"), "commit": base.get("commit")},
        "regressions": regressions[: args.max_errors],
        "regression_count": len(regressions),
        "newly_clean": recovered[: args.max_errors],
        "counts": {"boundaries": checked, "clean": len(clean),
                   "not_clean": len(errors),
                   "baseline_clean": len(was_clean)},
        "current_problems": errors[: args.max_errors],
    }, indent=2))
    return 1 if regressions else 0


if __name__ == "__main__":
    sys.exit(main())

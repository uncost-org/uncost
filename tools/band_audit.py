#!/usr/bin/env python3
"""R1 divider audit — every band boundary carries exactly one rule.

The rule being audited (website/src/css/integration.css items 40 and 51):

  R1  Every boundary between adjacent content bands carries EXACTLY ONE rule.
      The rule is normally drawn by the LOWER band's top edge; nothing draws a
      bottom rule, so nothing can double up.
      Colour: the first of [coral, ink, wheat] that differs from BOTH adjacent
      band backgrounds. cream<->wheat is coral; anything<->coral is ink;
      ink<->coral is WHEAT.
  R2  (item 54) Where a framed component's edge is flush against a band
      boundary, that frame edge IS the boundary and R1's rule is suppressed
      there (.ways, .sgrid).

Bands are the direct children of <main> in the BUILT html. Backgrounds are
resolved from COMPUTED STYLE in a real browser, never from class names.

Two independent verdicts are produced for every boundary and both must hold:

  DOM verdict     borders + computed backgrounds + geometry.
  PIXEL verdict   what is actually painted, read out of a screenshot strip
                  taken across the boundary.

Both are needed. integration.css item 76 records three real double-rule defects
that a DOM-only audit of this same rule missed: a frame boundary where two
rules both rendered, an inset component the audit filtered away, and two
stacked rules of the SAME colour that render as one 8px line where 4px is
declared. Counting borders cannot see the third at all; pixels can.

STANDING RULE: this audit fails on "I don't know". A boundary whose background
cannot be resolved, whose rule cannot be classified, or whose two verdicts
disagree is an ERROR, never a skipped line.

    python3 tools/band_audit.py [--built DIR]
    python3 tools/band_audit.py --selftest

Exit 0 when ok, 1 on any error. JSON on stdout; a human breakdown on stderr.
"""

import argparse
import collections
import http.server
import json
import os
import pathlib
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading

try:
    from PIL import Image
except ImportError:  # pragma: no cover - environment problem, not a finding
    sys.stderr.write("band_audit: Pillow is required (import PIL failed)\n")
    raise

ROOT = pathlib.Path(__file__).resolve().parents[1]
WEBSITE = ROOT / "website"
DIST = WEBSITE / "dist"
FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures" / "band"
PORT = 8199
WIDTHS = (1440, 1290, 390)

# --- the rule system's own constants -----------------------------------------
CORAL = (0xD6, 0x4A, 0x1E)
INK = (0x0E, 0x0E, 0x0C)
WHEAT = (0xE8, 0xB8, 0x4A)
RULE_ORDER = (("coral", CORAL), ("ink", INK), ("wheat", WHEAT))
R1_RULE_PX = 4.0          # item 40: `border-top: 4px solid ...`
# Two colours closer than this are not distinguishable as a line against each
# other. #0E0E0C (ink) vs #1A1A17 (ink-2) is 12, and an ink rule on an ink-2
# band is exactly the invisibility R1 exists to prevent, so 12 must not pass.
VISIBLE_DELTA = 12
WIDTH_TOL = 0.75          # sub-pixel layout slack on a declared border width

# --- pixel sampling ----------------------------------------------------------
STRIP_PAD = 24            # px sampled either side of an edge
UNIFORM_WIN = 8           # px that must be one flat colour to call a column clean
MIN_PAD = 6               # below this there is not enough band to read
MIN_CLEAN_COLUMNS = 3     # fewer than this and there is no pixel verdict
MODAL_SHARE = 0.5         # the modal signature must hold this share of columns
SAME_PIXEL = 3            # max channel delta for two sampled rows to be one colour
COLUMN_STEP = 8           # sample every Nth pixel column

GAP_EPS = 0.75            # |gap| at or below this counts as flush


# ============================================================================
# The browser probe. Inlined into a temp dir at runtime so this tool stays one
# committed file. It collects FACTS ONLY — geometry, computed style, and
# screenshot strips. Every judgement is made in Python below.
# ============================================================================
NODE_PROBE = r"""
const fs = require("node:fs");
const path = require("node:path");
const job = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const puppeteer = require(require.resolve("puppeteer", { paths: [job.website] }));

const GAP_EPS = job.gapEps, PAD = job.pad, MIN_PAD = job.minPad;

(async () => {
  const browser = await puppeteer.launch({
    args: ["--no-sandbox", "--force-device-scale-factor=1"],
  });
  const page = await browser.newPage();
  await page.emulateMediaFeatures([{ name: "prefers-reduced-motion", value: "reduce" }]);
  const out = [];
  for (const width of job.widths) {
    await page.setViewport({ width, height: 1000, deviceScaleFactor: 1 });
    for (const route of job.routes) {
      const res = await page.goto(job.base + route, { waitUntil: "networkidle0", timeout: 60000 });
      if (!res || !res.ok()) {
        out.push({ route, width, fetchError: `HTTP ${res ? res.status() : "no response"}` });
        continue;
      }
      await page.evaluate(() => document.fonts && document.fonts.ready);
      // Lazy images below the fold never load in a clipped capture; force them
      // so a band's own content cannot read as blank background.
      await page.evaluate(async () => {
        for (const img of document.querySelectorAll('img[loading="lazy"]')) {
          img.loading = "eager";
          if (img.dataset.src) img.src = img.dataset.src;
        }
        await Promise.all([...document.images].filter((i) => !i.complete)
          .map((i) => new Promise((r) => { i.onload = i.onerror = r; })));
      });
      await new Promise((r) => setTimeout(r, 120));

      const facts = await page.evaluate((GAP_EPS, PAD, MIN_PAD) => {
        const NON_RENDERING = new Set(["script", "template", "style", "noscript", "link", "meta"]);
        // Resolve a background the only way that is trustworthy: computed style,
        // walking up until something opaque paints. Anything that cannot be
        // pinned to one opaque colour is reported unresolved, never guessed.
        const resolveBg = (el) => {
          const chain = [];
          let e = el;
          while (e) {
            const cs = getComputedStyle(e);
            const tag = e.tagName.toLowerCase() +
              (e.className ? "." + e.className.toString().trim().split(/\s+/).join(".") : "");
            chain.push(tag + " " + cs.backgroundColor);
            if (cs.backgroundImage && cs.backgroundImage !== "none") {
              return { bg: null, unresolved: "background-image on " + tag + ": " +
                cs.backgroundImage.slice(0, 80), chain };
            }
            const m = cs.backgroundColor.match(/^rgba?\(([^)]+)\)$/);
            if (!m) return { bg: null, unresolved: "unparsable background-color '" +
              cs.backgroundColor + "' on " + tag, chain };
            const p = m[1].split(",").map((v) => parseFloat(v));
            const a = p.length > 3 ? p[3] : 1;
            if (a >= 0.999) return { bg: [p[0], p[1], p[2]], unresolved: null, chain };
            if (a > 0.001) return { bg: null, unresolved: "semi-transparent background " +
              cs.backgroundColor + " on " + tag, chain };
            e = e.parentElement;
          }
          return { bg: null, unresolved: "no opaque background anywhere up the tree", chain };
        };
        const side = (cs, s) => ({
          w: parseFloat(cs["border" + s + "Width"]) || 0,
          style: cs["border" + s + "Style"],
          color: cs["border" + s + "Color"],
        });

        const main = document.querySelector("main");
        if (!main) return { noMain: true };
        const canvas = resolveBg(main);
        const bands = [];
        [...main.children].forEach((el, domIndex) => {
          const tag = el.tagName.toLowerCase();
          const cs = getComputedStyle(el);
          const cls = (el.className || "").toString().trim();
          const label = tag + (cls ? "." + cls.split(/\s+/).join(".") : (el.id ? "#" + el.id : ""));
          const r = el.getBoundingClientRect();
          if (NON_RENDERING.has(tag) || cs.display === "none" ||
              (r.height === 0 && r.width === 0)) {
            bands.push({ domIndex, label, rendered: false,
              why: NON_RENDERING.has(tag) ? "non-rendering element" :
                   cs.display === "none" ? "display:none" : "zero box" });
            return;
          }
          const bg = resolveBg(el);
          bands.push({
            domIndex, label, rendered: true,
            bg: bg.bg, bgUnresolved: bg.unresolved, bgChain: bg.chain,
            rect: { top: r.top + window.scrollY, bottom: r.bottom + window.scrollY,
                    left: r.left, width: r.width, height: r.height },
            b: { top: side(cs, "Top"), right: side(cs, "Right"),
                 bottom: side(cs, "Bottom"), left: side(cs, "Left") },
            boxShadow: cs.boxShadow,
            outline: cs.outlineStyle === "none" ? "none" :
                     cs.outlineWidth + " " + cs.outlineStyle + " " + cs.outlineColor,
          });
        });

        // Geometry only: where are the horizontal edges, and how much clean band
        // is available either side of each for a pixel read.
        const live = bands.filter((b) => b.rendered);
        const edges = [];
        for (let i = 0; i + 1 < live.length; i++) {
          const U = live[i], L = live[i + 1];
          const gap = L.rect.top - U.rect.bottom;
          const upIn = (y) => y - (U.rect.top + U.b.top.w);
          const downIn = (y) => (L.rect.bottom - L.b.bottom.w) - y;
          // Sample only where the two bands overlap horizontally. An inset
          // component (a callout with its own side margins) has page canvas
          // beside it, and those columns carry no boundary at all — reading
          // them would drown the real line. integration.css item 76b is the
          // defect a full-width test hid.
          const x0 = Math.ceil(Math.max(U.rect.left, L.rect.left));
          const x1 = Math.floor(Math.min(U.rect.left + U.rect.width,
                                         L.rect.left + L.rect.width));
          const mk = (kind, y, availUp, availDown) => ({
            kind, upper: U.domIndex, lower: L.domIndex, y, gap, x0, x1,
            padUp: Math.min(PAD, Math.floor(availUp)),
            padDown: Math.min(PAD, Math.floor(availDown)),
          });
          if (gap > GAP_EPS) {
            edges.push(mk("upper-edge", U.rect.bottom, upIn(U.rect.bottom), gap));
            edges.push(mk("lower-edge", L.rect.top, gap, downIn(L.rect.top)));
          } else {
            edges.push(mk("single", L.rect.top, upIn(L.rect.top), downIn(L.rect.top)));
          }
        }
        return { bands, edges, canvasBg: canvas.bg, canvasUnresolved: canvas.unresolved,
                 docWidth: document.documentElement.scrollWidth };
      }, GAP_EPS, PAD, MIN_PAD);

      if (facts.noMain) { out.push({ route, width, noMain: true }); continue; }

      // A clipped capture taken beyond the viewport composites fixed and stuck
      // overlays at their VIEWPORT position, so the mobile pledge bar (coral,
      // position:fixed) lands in the middle of the document and reads as a
      // painted line. Overlays float over the band stack, they are not part of
      // it, so they come out for the measurement. Bands themselves are never
      // hidden.
      facts.overlaysHidden = await page.evaluate(() => {
        const main = document.querySelector("main");
        const bands = new Set(main ? [...main.children] : []);
        let n = 0;
        for (const el of document.querySelectorAll("body *")) {
          if (bands.has(el)) continue;
          const pos = getComputedStyle(el).position;
          if (pos === "fixed" || pos === "sticky") { el.style.visibility = "hidden"; n++; }
        }
        return n;
      });

      // One narrow full-width strip per edge. Small, and far cheaper than a
      // full-page capture of a 5000px document.
      const shots = [];
      for (let k = 0; k < facts.edges.length; k++) {
        const e = facts.edges[k];
        if (e.padUp < MIN_PAD || e.padDown < MIN_PAD) { shots.push(null); continue; }
        const y0 = Math.round(e.y) - e.padUp;
        const h = e.padUp + e.padDown;
        const x0 = Math.max(0, e.x0);
        const w = Math.min(width, e.x1) - x0;
        if (y0 < 0 || h < 2 || w < 16) {
          shots.push(w < 16 ? { error: "bands overlap horizontally by only " + w + "px" } : null);
          continue;
        }
        const file = path.join(job.shotDir, `s${out.length}_${k}.png`);
        try {
          await page.screenshot({ path: file, captureBeyondViewport: true,
            clip: { x: x0, y: y0, width: w, height: h } });
          shots.push({ file, y0, boundaryRow: Math.round(e.y) - y0 });
        } catch (err) {
          shots.push({ error: String(err).slice(0, 160) });
        }
      }
      facts.edges.forEach((e, k) => { e.shot = shots[k]; });
      out.push({ route, width, ...facts });
    }
  }
  await browser.close();
  fs.writeFileSync(job.outFile, JSON.stringify(out));
})().catch((e) => { console.error(e); process.exit(1); });
"""


# ============================================================================
# colour helpers
# ============================================================================
def parse_css_rgb(value):
    """'rgb(1, 2, 3)' / 'rgba(1,2,3,.5)' -> ((r,g,b), alpha) or (None, None)."""
    if not value:
        return None, None
    v = value.strip()
    if not (v.startswith("rgb(") or v.startswith("rgba(")):
        return None, None
    inner = v[v.index("(") + 1: v.rindex(")")]
    parts = [p.strip() for p in inner.replace("/", ",").split(",") if p.strip()]
    try:
        nums = [float(p) for p in parts]
    except ValueError:
        return None, None
    if len(nums) < 3:
        return None, None
    alpha = nums[3] if len(nums) > 3 else 1.0
    return (int(round(nums[0])), int(round(nums[1])), int(round(nums[2]))), alpha


def delta(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]), abs(a[2] - b[2]))


def visibly_differs(a, b):
    return delta(a, b) > VISIBLE_DELTA


def hexa(c):
    return "#%02X%02X%02X" % tuple(c)


def name_colour(c):
    for name, ref in RULE_ORDER:
        if delta(c, ref) <= 2:
            return name
    return hexa(c)


def expected_rule_colour(bg_above, bg_below):
    """R1: the first of [coral, ink, wheat] visible against BOTH sides."""
    for name, ref in RULE_ORDER:
        if visibly_differs(ref, bg_above) and visibly_differs(ref, bg_below):
            return name, ref
    return None, None


# ============================================================================
# DOM-side band facts
# ============================================================================
def border_rule(side):
    """Is this border side a drawn rule? Returns (present, width, colour)."""
    w = float(side.get("w") or 0.0)
    style = side.get("style")
    colour, alpha = parse_css_rgb(side.get("color"))
    if w <= 0.25 or style in (None, "none", "hidden"):
        return False, w, colour
    if colour is None or (alpha is not None and alpha <= 0.01):
        return False, w, colour
    return True, w, colour


def is_frame(band):
    """R2 component frame: a complete box, all four sides the same drawn line."""
    sides = [band["b"][s] for s in ("top", "right", "bottom", "left")]
    parsed = [border_rule(s) for s in sides]
    if not all(p[0] for p in parsed):
        return False, 0.0
    widths = {round(p[1], 2) for p in parsed}
    colours = {p[2] for p in parsed}
    if len(widths) != 1 or len(colours) != 1:
        return False, 0.0
    return True, parsed[0][1]


# ============================================================================
# PIXEL-side reading
# ============================================================================
def same_px(a, b):
    return delta(a, b) <= SAME_PIXEL


def read_column(px, x, height):
    return [px[x, j] for j in range(height)]


def column_signature(col, palette):
    """What is painted between the two flat backgrounds in this column?

    Returns None if the column is not clean (content in the way), otherwise a
    tuple of (colour_name, thickness) for every line found between them.
    """
    h = len(col)
    win = min(UNIFORM_WIN, h // 3)
    if win < 2:
        return None
    above = col[0]
    below = col[-1]
    if any(not same_px(c, above) for c in col[:win]):
        return None
    if any(not same_px(c, below) for c in col[h - win:]):
        return None
    t = 0
    while t < h and same_px(col[t], above):
        t += 1
    b = h
    while b > t and same_px(col[b - 1], below):
        b -= 1
    runs = []
    i = t
    while i < b:
        j = i + 1
        while j < b and same_px(col[j], col[i]):
            j += 1
        runs.append((col[i], j - i))
        i = j
    lines = []
    for colour, thick in runs:
        near_palette = any(delta(colour, ref) <= VISIBLE_DELTA for ref in palette)
        if thick <= 1 and not near_palette:
            continue  # a single anti-aliased seam row, not a rule
        lines.append((name_colour(colour), thick))
    return tuple(lines)


def pixel_verdict(shot):
    """Modal painted signature across clean columns, or (None, reason)."""
    if shot is None:
        return None, "no strip (band too short to sample either side of the edge)"
    if "error" in shot:
        return None, "screenshot failed: " + shot["error"]
    path = pathlib.Path(shot["file"])
    if not path.exists():
        return None, "strip missing on disk"
    with Image.open(path) as im:
        im = im.convert("RGB")
        w, h = im.size
        px = im.load()
        palette = [CORAL, INK, WHEAT]
        sigs = []
        for x in range(2, max(3, w - 2), COLUMN_STEP):
            sig = column_signature(read_column(px, x, h), palette)
            if sig is not None:
                sigs.append(sig)
    if len(sigs) < MIN_CLEAN_COLUMNS:
        return None, "only %d clean pixel columns (need %d)" % (len(sigs), MIN_CLEAN_COLUMNS)
    counts = collections.Counter(sigs)
    sig, n = counts.most_common(1)[0]
    if n / len(sigs) < MODAL_SHARE:
        return None, "no modal signature (%d columns, best %d: %s)" % (
            len(sigs), n, counts.most_common(3))
    return {"lines": sig, "columns": len(sigs), "share": n / len(sigs)}, None


# ============================================================================
# Judgement
# ============================================================================
def audit_page(page, errors, counts, notes):
    route, width = page["route"], page["width"]
    where = "%dpx %s" % (width, route)

    if page.get("fetchError"):
        errors.append("%s: page did not load (%s)" % (where, page["fetchError"]))
        return
    if page.get("noMain"):
        errors.append("%s: no <main> — bands cannot be enumerated" % where)
        return

    bands = {b["domIndex"]: b for b in page["bands"]}
    canvas_bg = page.get("canvasBg")
    canvas_bg = tuple(canvas_bg) if canvas_bg else None

    for b in page["bands"]:
        if b.get("rendered") and b.get("bgUnresolved"):
            errors.append("%s band %s: background not resolvable — %s [chain: %s]" % (
                where, b["label"], b["bgUnresolved"], " <- ".join(b["bgChain"])))
        if b.get("rendered"):
            if b.get("boxShadow") not in (None, "none"):
                errors.append("%s band %s: box-shadow '%s' can paint a line this audit "
                              "does not model" % (where, b["label"], b["boxShadow"]))
            if b.get("outline") not in (None, "none"):
                errors.append("%s band %s: outline '%s' can paint a line this audit "
                              "does not model" % (where, b["label"], b["outline"]))

    for edge in page["edges"]:
        U, L = bands[edge["upper"]], bands[edge["lower"]]
        tag = "%s boundary %s | %s" % (where, U["label"], L["label"])
        if edge["kind"] != "single":
            tag += " (%s of a %.0fpx gap)" % (edge["kind"], edge["gap"])

        bg_u = tuple(U["bg"]) if U.get("bg") else None
        bg_l = tuple(L["bg"]) if L.get("bg") else None
        if edge["kind"] == "upper-edge":
            above, below = bg_u, canvas_bg
            sides = [("upper band border-bottom", U, "bottom")]
            frame_owner = U
        elif edge["kind"] == "lower-edge":
            above, below = canvas_bg, bg_l
            sides = [("lower band border-top", L, "top")]
            frame_owner = L
        else:
            above, below = bg_u, bg_l
            sides = [("upper band border-bottom", U, "bottom"),
                     ("lower band border-top", L, "top")]
            frame_owner = None

        drawn = []
        for label, band, which in sides:
            present, w, colour = border_rule(band["b"][which])
            if present:
                drawn.append({"label": label, "w": w, "colour": colour, "band": band})

        if above is None or below is None:
            # The unresolved background is already an error against the band.
            # Say so again here so the boundary is never silently uncounted.
            errors.append("%s: not classifiable — an adjacent background is "
                          "unresolved (see band error above)" % tag)
            counts["boundaries"] += 1
            continue

        if not visibly_differs(above, below) and not drawn:
            # Same background, nothing drawn: these siblings are one band split
            # for markup, not two bands. Recorded, not silently dropped.
            notes["same_background_no_rule"].append(tag)
            continue

        counts["boundaries"] += 1
        problems_before = len(errors)

        # --- R2: is a component frame the boundary here? --------------------
        frame_w = None
        if edge["kind"] == "single":
            for cand in (U, L):
                ok, w = is_frame(cand)
                if ok:
                    frame_w, frame_owner = w, cand
                    break
        else:
            ok, w = is_frame(frame_owner)
            frame_w = w if ok else None
            if not ok:
                frame_owner = None
        suppressed = frame_w is not None
        if suppressed:
            counts["suppressed_by_frame"] += 1

        same_bg = not visibly_differs(above, below)
        kind = " [same-background boundary that still draws a rule — the item 52 " \
               "category]" if same_bg else ""
        want_w = frame_w if suppressed else R1_RULE_PX
        want_why = ("the component frame's own weight" if suppressed
                    else "R1's declared %gpx" % R1_RULE_PX)
        exp_name, exp_rgb = expected_rule_colour(above, below)

        # Two band edges both drawing is a defect on its own terms, whatever the
        # pixels end up showing: two rules of one colour merge into a single
        # thick line and would otherwise read as one.
        if len(drawn) > 1:
            errors.append("%s%s: %d band edges draw where R1 allows one — %s" % (
                tag, kind, len(drawn),
                "; ".join("%s %gpx %s" % (d["label"], d["w"], hexa(d["colour"]))
                          for d in drawn)))
        rule = drawn[0] if len(drawn) == 1 else None

        # --- what is actually painted ----------------------------------------
        pv, why = pixel_verdict(edge.get("shot"))
        if pv is None:
            counts["_unverified"] += 1
            notes["pixel_unverified"].append("%s: %s" % (tag, why))
            painted = None
        else:
            painted = pv["lines"]

        if painted is not None:
            # Pixels are the authority on how many lines a reader sees, on how
            # thick they are, and on what colour they are. A band edge is not
            # the only thing that can draw one: on /treasury/ the boundary is
            # carried by the top edges of a gapless card grid inside the band
            # (integration.css item 76c), which is one rule and correct.
            if len(painted) == 0:
                if rule is None:
                    errors.append("%s%s: no rule at all — nothing is declared by either "
                                  "band edge and nothing is painted, where R1 requires "
                                  "exactly one" % (tag, kind))
                elif not visibly_differs(rule["colour"], above) or \
                        not visibly_differs(rule["colour"], below):
                    errors.append("%s%s: the declared %gpx %s rule paints nothing — it is "
                                  "invisible against an adjacent band (above %s, below "
                                  "%s)" % (tag, kind, rule["w"], hexa(rule["colour"]),
                                           hexa(above), hexa(below)))
                else:
                    errors.append("%s%s: the declared %gpx %s rule paints nothing at this "
                                  "boundary — occluded by something drawn over it" % (
                                      tag, kind, rule["w"], hexa(rule["colour"])))
            elif len(painted) != 1:
                errors.append("%s%s: pixels show %d painted lines %s where R1 "
                              "requires exactly one (band edges declare %s)" % (
                                  tag, kind, len(painted), list(painted),
                                  "%gpx %s" % (rule["w"], hexa(rule["colour"]))
                                  if rule else "none"))
            else:
                pname, pthick = painted[0]
                if not drawn:
                    notes["child_drawn"].append("%s: %gpx %s, drawn inside a band "
                                                "rather than by a band edge" % (
                                                    tag, pthick, pname))
                elif rule is not None and (abs(pthick - rule["w"]) > 1.0
                                           or pname != name_colour(rule["colour"])):
                    errors.append("%s%s: pixels paint a %gpx %s line where the band "
                                  "edge declares %gpx %s — stacked, occluded or "
                                  "overdrawn rules" % (
                                      tag, kind, pthick, pname, rule["w"],
                                      hexa(rule["colour"])))
                if abs(pthick - want_w) > 1.0:
                    errors.append("%s%s: the boundary renders %gpx against %gpx "
                                  "declared (%s)" % (tag, kind, pthick, want_w, want_why))
                if not suppressed:
                    if exp_rgb is None:
                        errors.append("%s%s: no rule colour in [coral, ink, wheat] is "
                                      "visible against both %s and %s" % (
                                          tag, kind, hexa(above), hexa(below)))
                    elif pname != exp_name:
                        errors.append("%s%s: the boundary line is %s, R1 requires %s %s "
                                      "(above %s, below %s)" % (
                                          tag, kind, pname, exp_name, hexa(exp_rgb),
                                          hexa(above), hexa(below)))
        else:
            # No pixel reading: the computed-style verdict has to stand alone,
            # and it must still be a complete verdict, never a shrug.
            if len(drawn) == 0:
                errors.append("%s%s: no rule at all — neither band edge declares one, "
                              "where R1 requires exactly one" % (tag, kind))
            elif rule is not None:
                if abs(rule["w"] - want_w) > 1.0:
                    errors.append("%s%s: rule renders %gpx against %gpx declared (%s)" % (
                        tag, kind, rule["w"], want_w, want_why))
                if not suppressed:
                    if exp_rgb is None:
                        errors.append("%s%s: no rule colour in [coral, ink, wheat] is "
                                      "visible against both %s and %s" % (
                                          tag, kind, hexa(above), hexa(below)))
                    elif not visibly_differs(rule["colour"], above) or \
                            not visibly_differs(rule["colour"], below):
                        errors.append("%s%s: rule %s is invisible against an adjacent "
                                      "band (above %s, below %s)" % (
                                          tag, kind, hexa(rule["colour"]),
                                          hexa(above), hexa(below)))
                    elif delta(rule["colour"], exp_rgb) > 2:
                        errors.append("%s%s: rule is %s, R1 requires %s %s (above %s, "
                                      "below %s)" % (
                                          tag, kind, hexa(rule["colour"]), exp_name,
                                          hexa(exp_rgb), hexa(above), hexa(below)))

        if len(errors) > problems_before:
            counts["flagged_boundaries"] += 1


# ============================================================================
# plumbing
# ============================================================================
class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):  # keep stdout/stderr to the audit's own output
        pass


def serve(directory, port):
    handler = lambda *a, **kw: _QuietHandler(*a, directory=str(directory), **kw)
    socketserver.TCPServer.allow_reuse_address = True
    try:
        httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
    except OSError as exc:
        raise RuntimeError(
            "cannot serve %s on 127.0.0.1:%d (%s). Free the port or pass --port."
            % (directory, port, exc)) from None
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def discover_routes(root):
    routes = []
    for p in sorted(root.rglob("*.html")):
        rel = p.relative_to(root).as_posix()
        routes.append("/" + rel[: -len("index.html")] if rel.endswith("index.html")
                      else "/" + rel)
    return routes


def probe(root, routes, widths, port):
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="band-audit-"))
    try:
        (tmp / "probe.cjs").write_text(NODE_PROBE)
        shots = tmp / "shots"
        shots.mkdir()
        job = {
            "website": str(WEBSITE), "base": "http://127.0.0.1:%d" % port,
            "routes": routes, "widths": list(widths), "shotDir": str(shots),
            "outFile": str(tmp / "out.json"), "gapEps": GAP_EPS,
            "pad": STRIP_PAD, "minPad": MIN_PAD,
        }
        (tmp / "job.json").write_text(json.dumps(job))
        httpd = serve(root, port)
        try:
            r = subprocess.run(["node", str(tmp / "probe.cjs"), str(tmp / "job.json")],
                               capture_output=True, text=True)
        finally:
            httpd.shutdown()
            httpd.server_close()
        if r.returncode != 0:
            raise RuntimeError("browser probe failed:\n" + (r.stderr or "")[-4000:])
        pages = json.loads((tmp / "out.json").read_text())
        # Judge while the strips still exist on disk.
        return pages, tmp
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        raise


def run_audit(root, widths=WIDTHS, port=PORT):
    routes = discover_routes(root)
    if not routes:
        raise RuntimeError("no .html found under %s" % root)
    pages, tmp = probe(root, routes, widths, port)
    try:
        errors, per_route = [], collections.defaultdict(list)
        counts = collections.Counter()
        notes = {"same_background_no_rule": [], "pixel_unverified": [],
             "child_drawn": []}
        for page in pages:
            before = len(errors)
            audit_page(page, errors, counts, notes)
            per_route[page["route"]].extend(errors[before:])
        return {
            "errors": errors, "per_route": dict(per_route), "counts": counts,
            "notes": notes, "routes": routes, "pages": len(pages),
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def report(result):
    counts = result["counts"]
    return {
        "ok": not result["errors"],
        "errors": result["errors"],
        "counts": {
            "boundaries": counts["boundaries"],
            "problems": len(result["errors"]),
            "suppressed_by_frame": counts["suppressed_by_frame"],
        },
    }


def stderr_breakdown(result):
    c = result["counts"]
    n = result["notes"]
    w = sys.stderr.write
    w("\n--- band_audit breakdown -------------------------------------------\n")
    w("pages audited                 %d\n" % result["pages"])
    w("boundaries audited            %d\n" % c["boundaries"])
    w("  of those, R2 frame edges    %d\n" % c["suppressed_by_frame"])
    w("  flagged boundaries          %d\n" % c["flagged_boundaries"])
    w("same-background adjacencies   %d  (siblings sharing one background and\n"
      "                                  drawing nothing: one band split for\n"
      "                                  markup, not a boundary)\n"
      % len(n["same_background_no_rule"]))
    w("boundaries drawn from inside  %d  (exactly one rule, but painted by a\n"
      "                                  band's own content rather than by a\n"
      "                                  band edge - integration.css item 76c)\n"
      % len(n["child_drawn"]))
    for line in n["child_drawn"][:10]:
        w("    %s\n" % line)
    if len(n["child_drawn"]) > 10:
        w("    ... %d more\n" % (len(n["child_drawn"]) - 10))
    w("pixel cross-check unavailable %d  (computed-style verdict stands alone;\n"
      "                                  each one is named below)\n"
      % c["_unverified"])
    for line in n["pixel_unverified"][:20]:
        w("    %s\n" % line)
    if len(n["pixel_unverified"]) > 20:
        w("    ... %d more\n" % (len(n["pixel_unverified"]) - 20))
    if result["errors"]:
        w("\nproblems by route:\n")
        for route, errs in sorted(result["per_route"].items()):
            if errs:
                w("  %-42s %d\n" % (route, len(errs)))
    w("--------------------------------------------------------------------\n")


# ============================================================================
# selftest
# ============================================================================
# Each case is a fixture page under tools/fixtures/band/ and what the audit must
# say about it. `expect` is a list of substrings that must ALL appear somewhere
# in that page's errors; an empty list means the page must produce none.
SELFTEST_CASES = [
    ("/good-basic.html", [], "four correct boundaries: cream->wheat coral, "
     "wheat->ink coral, ink->coral wheat, coral->cream2 ink"),
    ("/good-frame.html", [], "R2: a framed component flush on both sides, its "
     "own 2px ink frame carrying each boundary"),
    ("/bad-double.html", ["2 band edges draw where R1 allows one",
                          "renders 8px against 4px declared"],
     "case 1: both the upper band's bottom edge and the lower band's top edge draw. "
     "Two 4px coral rules also merge into one 8px line, so the weight check has to "
     "catch it independently of the border count"),
    ("/bad-missing.html", ["no rule at all"],
     "case 2: a cream->wheat boundary with no rule at all"),
    ("/bad-invisible.html", ["is invisible against an adjacent band",
                             "4px #D64A1E rule paints nothing",
                             "4px #0E0E0C rule paints nothing"],
     "case 3: a coral rule on a coral band, and an ink rule between two ink bands"),
    ("/bad-thick.html", ["renders 9px against 4px declared"],
     "case 4: a rule rendering 9px where the system declares 4px"),
    ("/bad-unresolved.html", ["background not resolvable"],
     "case 5: a band whose background is a gradient — reported, never skipped"),
]


def selftest(port=PORT):
    if not FIXTURES.is_dir():
        return {"ok": False, "selftest_cases": 0,
                "failures": ["fixture directory missing: %s" % FIXTURES]}
    # Hard guard: the selftest must never be pointed at the real site.
    resolved = FIXTURES.resolve()
    if DIST.resolve() == resolved or DIST.resolve() in resolved.parents:
        return {"ok": False, "selftest_cases": 0,
                "failures": ["refusing to run the selftest against the built site"]}
    result = run_audit(FIXTURES, widths=(1440,), port=port)
    failures = []
    for route, expect, why in SELFTEST_CASES:
        errs = result["per_route"].get(route)
        if errs is None:
            failures.append("%s: fixture never audited (missing file?)" % route)
            continue
        blob = "\n".join(errs)
        if not expect:
            if errs:
                failures.append("%s (%s): expected a clean pass, got %d error(s): %s"
                                % (route, why, len(errs), errs[:3]))
            continue
        if not errs:
            failures.append("%s (%s): expected the audit to FAIL and it passed" % (route, why))
            continue
        for needle in expect:
            if needle not in blob:
                failures.append("%s (%s): expected an error containing %r; got: %s"
                                % (route, why, needle, errs))
    audited = set(result["per_route"]) | set(result["routes"])
    for route in sorted(audited):
        if route not in {c[0] for c in SELFTEST_CASES}:
            failures.append("%s: fixture has no declared expectation" % route)
    return {"ok": not failures, "selftest_cases": len(SELFTEST_CASES), "failures": failures}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--built", default=str(DIST),
                    help="built site directory (default website/dist)")
    ap.add_argument("--selftest", action="store_true",
                    help="run the fixture suite under tools/fixtures/band/")
    ap.add_argument("--port", type=int, default=PORT)
    args = ap.parse_args()

    if args.selftest:
        out = selftest(port=args.port)
        print(json.dumps(out, indent=2))
        return 0 if out["ok"] else 1

    root = pathlib.Path(args.built).resolve()
    if not root.is_dir():
        print(json.dumps({"ok": False, "errors": [
            "built site not found at %s — run `cd website && npm run build`" % root],
            "counts": {"boundaries": 0, "problems": 1, "suppressed_by_frame": 0}}, indent=2))
        return 1
    result = run_audit(root, port=args.port)
    out = report(result)
    print(json.dumps(out, indent=2))
    stderr_breakdown(result)
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

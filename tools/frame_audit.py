#!/usr/bin/env python3
"""R2 component-frame audit — integration.css item 54.

    "Any grid or panel that draws ink divider lines between its cells carries a
     COMPLETE frame: top and bottom at the same weight and colour as those
     internal dividers."

Every component that draws internal dividers between its cells must close its
own frame on all four edges, at the divider's weight and colour. Five components
historically drew dividers and left the frame open, so the outermost cells bled
into the band.

HOW IT DECIDES
--------------
Components are DISCOVERED, never listed: the audit walks every element in a real
Chrome page and asks, from COMPUTED STYLE plus measured geometry, whether a line
is drawn in the seam between two neighbouring cells. Two mechanisms are in use
in this codebase and both are handled:

  border          two cells touch (gap <= 1px) and one of them draws a border on
                  the facing edge — directly, or, when its own children tile it,
                  through the border they all draw there (a table row's cells).
  bg-through-gap  the cells are separated by a small grid gap (<= 4px) and the
                  CONTAINER's opaque background paints that gap. No cell carries
                  a border at all; reading the CSS text would report a false pass.

A component is in scope when its cells TILE it — the cell union reaches the
container's padding box (so the dividers run edge to edge and meet the frame), or
reaches its content box behind a small opaque padding, which is itself a frame.
Text rules inset inside a padded card (a tier card's hairline action rows, a
receipt card's footer rule) do not reach the frame and are not R2 subjects.

The frame of each edge is then resolved, again from computed style: the
component's own border, its opaque background showing through a small padding,
or — since a frame edge flush against a band boundary IS that boundary — a line
drawn flush against that edge by an ancestor or by the adjacent band, found by
walking up only while the ancestor stays flush.

STANDING RULE: the audit fails on "I don't know". A component whose dividers or
frame cannot be resolved (non-uniform dividers, two different frame lines on one
edge, a box-shadow or border-image that could be drawing a line, an ambiguous
5-11px gap over a contrasting container background) is an ERROR, never a skipped
line. An audit that prints an unclassified case and keeps counting reports a
subset while appearing to report the whole.

USAGE
    python3 tools/frame_audit.py [--built DIR]   audit the built site
    python3 tools/frame_audit.py --selftest      run the fixture cases

Prints JSON. Exit 0 when ok, 1 on any error.
"""

import argparse
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

ROOT = pathlib.Path(__file__).resolve().parents[1]
DIST = ROOT / "website" / "dist"
WEBSITE = ROOT / "website"
FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures" / "frame"
PORT = 8796
WIDTHS = [1440, 1290, 390]

# --- fixture expectations -------------------------------------------------
# Kept here rather than in a manifest file so the fixtures stay plain .html/.css.
#   verdict  "fail" -> the audit MUST report at least one error for that page
#            "pass" -> the audit MUST report none
#   match    substring every expected error kind must appear in (fail cases)
#   min_components  the page must actually have been audited; a "pass" that
#            comes from seeing nothing is worthless, so good fixtures demand >= 1
SELFTEST_CASES = [
    ("bad-01-no-frame.html", "fail", "frame edge is open", 1),
    ("bad-02-open-bottom.html", "fail", "bottom: frame edge is open", 1),
    ("bad-03-weight-mismatch.html", "fail", "weight", 1),
    ("bad-04-colour-mismatch.html", "fail", "colour", 1),
    ("bad-05-gap-no-frame.html", "fail", "frame edge is open", 1),
    ("bad-06-table-no-frame.html", "fail", "frame edge is open", 1),
    # The two "I don't know" cases: the audit must error, not skip the line.
    ("bad-07-ambiguous-gap.html", "fail", "neither a drawn divider", 1),
    ("bad-08-mixed-dividers.html", "fail", "not uniform", 1),
    ("good-01-border-frame.html", "pass", "", 1),
    ("good-02-gap-frame.html", "pass", "", 1),
    ("good-03-table-frame.html", "pass", "", 1),
    ("good-04-padding-frame.html", "pass", "", 1),
    # 12px gap is spacing, not a drawn divider: nothing to audit at all.
    ("neutral-01-spacing-gap.html", "pass", "", 0),
    # Named exemptions (D3). The fixtures carry their own table below.
    ("good-05-exempt-band-body.html", "pass", "", 1),
    ("bad-09-exempt-lookalike.html", "fail", "frame edge is open", 1),
    ("bad-10-exempt-still-unresolved.html", "fail", "not uniform", 1),
    ("bad-11-exempt-stale.html", "fail", "STALE EXEMPTION", 1),
    # R2 as amended 2026-09-26 (V1, V2).
    ("good-12-r1-under-ink.html", "pass", "", 1),
    ("bad-13-r1-where-visible.html", "fail", "weight and colour differ", 1),
    ("good-14-fullbleed-nosides.html", "pass", "", 1),
    ("bad-15-fullbleed-sides.html", "fail", "runs along the viewport edge", 1),
]

# --- named exemptions -------------------------------------------------------
# A founder decision that a component stays unframed. An exemption matches on
# the exact route AND the exact component path the analyser reports, and it
# covers only frame-EDGE findings (an open edge, or an edge whose weight or
# colour differs from the dividers). An "unresolved" finding is never exempt:
# a decision about how a thing should look is not a licence for the audit to
# stop knowing what it is looking at. An exemption whose route was rendered but
# which matched no component is an error, so a decision cannot outlive its
# subject unnoticed.
#   (route, component path as reported, reason)
EXEMPT_KINDS = {"open", "weight", "colour", "weight+colour", "viewport-edge"}
NAMED_EXEMPTIONS = [
    ("/about/", "html > body > main > div",
     "D3 (founder decision 2026-09-25): the Mechanism step list is a full-bleed "
     "band body, not a component panel, and stays unframed. CANVAS-SYNC 84."),
    ("/roadmap/", "html > body > main > section",
     "D3 (founder decision 2026-09-25): the Year one phase list is a full-bleed "
     "band body and stays unframed. CANVAS-SYNC 84."),
    ("/pledge/", "html > body > main > div.pwrap > div",
     "D3 (founder decision 2026-09-25): the pledge body beside the form is a "
     "full-bleed band body and stays unframed. C14 listed `.pwrap > div` for a "
     "frame, but deferred band bodies to D3, and the D3 renders are exactly this "
     "element. CANVAS-SYNC 84."),
]
SELFTEST_EXEMPTIONS = [
    ("/good-05-exempt-band-body.html", "html > body > div.band > div.g3", "fixture"),
    # Same route, a DIFFERENT path: a route-only key would wrongly exempt it.
    ("/bad-09-exempt-lookalike.html", "html > body > div.band > div.g4", "fixture"),
    ("/bad-10-exempt-still-unresolved.html", "html > body > div.band > div.mix3.fr-full", "fixture"),
    ("/bad-11-exempt-stale.html", "html > body > div.band > div.nothing-here", "fixture"),
]


def apply_exemptions(data, table):
    """-> (data with exempt frame-edge problems removed, extra errors, exercised)."""
    rendered = {r["route"] for r in data["pages"] if not r.get("error")}
    matched, exercised = set(), {}
    for rec in data["pages"]:
        for c in rec.get("components", []) or []:
            for route, path, why in table:
                if rec["route"] != route or c.get("path") != path:
                    continue
                matched.add((route, path))
                kept = [q for q in c["problems"] if q["kind"] not in EXEMPT_KINDS]
                dropped = len(c["problems"]) - len(kept)
                if dropped:
                    e = exercised.setdefault((route, path), {"route": route, "path": path,
                                                             "findings_exempted": 0, "reason": why})
                    e["findings_exempted"] += dropped
                c["problems"] = kept
    extra = []
    for route, path, why in table:
        if route in rendered and (route, path) not in matched:
            extra.append((route, "STALE EXEMPTION %s %s: the route rendered and no component "
                                 "has this path, so the decision no longer describes the page"
                          % (route, path)))
    return data, extra, list(exercised.values())

# ---------------------------------------------------------------------------
# The page-side analyser. Runs in Chrome; reads computed style and geometry.
# ---------------------------------------------------------------------------
ANALYZE_JS = r"""
window.__frameAudit = function (OPT) {
  const TOL = 4;        // px slack for "flush" / "tiles"
  const MAXSEAM = 4;    // a gap this small may be a drawn divider
  const SPACING = 12;   // a gap this large is spacing; between the two: unresolved
  const WTOL = 0.51;    // px slack when comparing line weights
  // Structural landmarks are the page, not components: the rules between their
  // bands are R1 band boundaries, governed elsewhere.
  const SKIP = new Set(["HTML", "BODY", "MAIN", "HEADER", "FOOTER", "NAV"]);
  const VW = document.documentElement.clientWidth;
  const R1W = 4;        // R1's declared rule weight (integration.css item 40)
  const VIS = 12;       // channel delta under which two colours read as one line
  // R2 as amended 2026-09-26:
  //   V1  a frame edge is the boundary only where it is VISIBLE against its
  //       neighbour; where the frame line would vanish into the neighbouring
  //       band, R1's rule replaces it on that edge.
  //   V2  a full-bleed component omits its left/right frame edges where they
  //       meet the viewport — and must not draw a line along the screen edge.
  const cap = (s) => s[0].toUpperCase() + s.slice(1);
  const num = (v) => { const n = parseFloat(v); return isNaN(n) ? 0 : n; };
  const CS = new Map();
  const cs = (el) => { let v = CS.get(el); if (!v) { v = getComputedStyle(el); CS.set(el, v); } return v; };
  const EDGE = { top: "t", bottom: "b", left: "l", right: "r" };
  const OPP = { top: "bottom", bottom: "top", left: "right", right: "left" };

  function parseColor(c) {
    const m = String(c).match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(/[,\s/]+/).filter(Boolean).map(Number);
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
  }
  const key = (c) => { const p = parseColor(c); return p ? `rgba(${p.r},${p.g},${p.b},${+(p.a).toFixed(3)})` : String(c); };
  const opaque = (c) => { const p = parseColor(c); return !!p && p.a > 0.05; };
  const resolveOpaque = (el) => {
    for (let e = el; e; e = e.parentElement) {
      const p = parseColor(getComputedStyle(e).backgroundColor);
      if (p && p.a > 0.999) return p;
    }
    return null;
  };
  const sameInk = (a, b) => !!a && !!b &&
    Math.max(Math.abs(a.r - b.r), Math.abs(a.g - b.g), Math.abs(a.b - b.b)) <= VIS;

  function rendered(el) {
    if (el.nodeType !== 1 || el.namespaceURI !== "http://www.w3.org/1999/xhtml") return false;
    const s = cs(el);
    if (s.display === "none" || s.visibility === "hidden" || num(s.opacity) === 0) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0.5 && r.height > 0.5;
  }
  const inflow = (el) => !["absolute", "fixed"].includes(cs(el).position);
  function box(el) {
    const r = el.getBoundingClientRect();
    return { l: r.left + scrollX, t: r.top + scrollY, r: r.right + scrollX, b: r.bottom + scrollY };
  }
  function shrink(el, b, withPadding) {
    const s = cs(el);
    const bw = (n) => num(s["border" + cap(n) + "Width"]);
    const pw = (n) => (withPadding ? num(s["padding" + cap(n)]) : 0);
    return { l: b.l + bw("left") + pw("left"), t: b.t + bw("top") + pw("top"),
             r: b.r - bw("right") - pw("right"), b: b.b - bw("bottom") - pw("bottom") };
  }
  const padBox = (el) => shrink(el, box(el), false);
  const contentBox = (el) => shrink(el, box(el), true);
  const near = (a, b) => Math.abs(a - b) <= TOL;

  function borderSide(el, side) {
    const s = cs(el);
    const w = num(s["border" + cap(side) + "Width"]);
    const st = s["border" + cap(side) + "Style"];
    const c = s["border" + cap(side) + "Color"];
    if (w <= 0 || st === "none" || st === "hidden" || !opaque(c)) return null;
    return { w: +w.toFixed(2), color: key(c) };
  }
  // A cell carrying a complete border on all four sides is drawing its own box
  // (a button, a chip); that outline is not a shared divider.
  function fullBorder(el) {
    const sides = ["top", "right", "bottom", "left"].map((s) => borderSide(el, s));
    return sides.every((s) => s) && sides.every((s) => s.color === sides[0].color && Math.abs(s.w - sides[0].w) <= WTOL);
  }
  const kidsOf = (el) => [...el.children].filter((k) => rendered(k) && inflow(k));
  const unionBox = (bs) => ({ l: Math.min(...bs.map((b) => b.l)), t: Math.min(...bs.map((b) => b.t)),
                              r: Math.max(...bs.map((b) => b.r)), b: Math.max(...bs.map((b) => b.b)) });
  function tilesPad(el, kids) {
    if (!kids.length) return false;
    const u = unionBox(kids.map(box)), p = padBox(el);
    return near(u.l, p.l) && near(u.t, p.t) && near(u.r, p.r) && near(u.b, p.b);
  }

  // The line drawn at el's `side` edge: its own border, or — when its children
  // tile it — the border every child touching that edge draws (a row's cells).
  const LINE_CACHE = new Map();
  function edgeLine(el, side, depth) {
    const ck = side + "@" + depth;
    let m = LINE_CACHE.get(el);
    if (!m) { m = new Map(); LINE_CACHE.set(el, m); }
    if (m.has(ck)) return m.get(ck);
    let out = borderSide(el, side);
    if (!out && depth < 3) {
      const kids = kidsOf(el);
      if (kids.length && tilesPad(el, kids)) {
        const e = EDGE[side], p = padBox(el);
        const touch = kids.filter((k) => near(box(k)[e], p[e]));
        if (touch.length) {
          const specs = touch.map((k) => edgeLine(k, side, depth + 1));
          if (specs.every((s) => s) &&
              specs.every((s) => Math.abs(s.w - specs[0].w) <= WTOL && s.color === specs[0].color))
            out = { w: specs[0].w, color: specs[0].color };
        }
      }
    }
    m.set(ck, out || null);
    return out || null;
  }

  function selOf(el) {
    const c = (el.getAttribute("class") || "").trim().split(/\s+/).filter(Boolean).slice(0, 4);
    return el.tagName.toLowerCase() + (c.length ? "." + c.join(".") : "");
  }
  function pathOf(el) {
    const parts = [];
    let n = el;
    while (n && n.tagName && parts.length < 5) { parts.unshift(selOf(n)); n = n.parentElement; }
    return parts.join(" > ");
  }
  const fmt = (l) => l.w + "px " + l.color;

  // --- geometry of the component's frame ----------------------------------
  // "pad": cells reach the padding box, so any frame is the container's border.
  // "padding-frame": cells reach the content box behind a small opaque padding,
  // which is itself the frame (background showing through).
  function frameGeom(el, kids) {
    const u = unionBox(kids.map(box)), p = padBox(el), c = contentBox(el), s = cs(el);
    const pads = { top: num(s.paddingTop), right: num(s.paddingRight),
                   bottom: num(s.paddingBottom), left: num(s.paddingLeft) };
    const maxPad = Math.max(pads.top, pads.right, pads.bottom, pads.left);
    // Tested before the plain padding-box fit, because a 2px padding drawing the
    // frame is smaller than the flush tolerance and would otherwise be read as
    // "cells reach the padding box" and the frame reported open.
    if (maxPad > 0 && maxPad <= MAXSEAM && opaque(s.backgroundColor) &&
        near(u.l, c.l) && near(u.t, c.t) && near(u.r, c.r) && near(u.b, c.b))
      return { mode: "padding-frame", pads: pads, bg: key(s.backgroundColor) };
    if (near(u.l, p.l) && near(u.t, p.t) && near(u.r, p.r) && near(u.b, p.b)) return { mode: "pad", pads: null };
    return null;
  }

  // The band a component meets on its `side`: the nearest rendered in-flow
  // sibling, walking up only while the ancestor stays flush on that side — and
  // across </main> to the page header or footer, which are bands too (V5).
  function neighbourBg(el, side) {
    const e = EDGE[side], target = box(el)[e];
    let node = el;
    for (let up = 0; up < 8 && node && node.tagName !== "BODY"; up++) {
      let sib = side === "top" ? node.previousElementSibling : node.nextElementSibling;
      while (sib && !(rendered(sib) && inflow(sib)))
        sib = side === "top" ? sib.previousElementSibling : sib.nextElementSibling;
      if (sib) return resolveOpaque(sib);
      const par = node.parentElement;
      if (!par || !near(box(par)[e], target)) return null;
      node = par;
    }
    return null;
  }
  // Does the component's side edge — or a line drawn just outside it by an
  // ancestor or neighbour (`reach`, the line's width) — meet the viewport?
  // /treasury/'s KPI frame is drawn by the wrapping band, 2px outside the
  // grid, so the grid itself starts at x=2 and a test on its own box misses
  // the line that runs down the screen edge.
  const atViewport = (el, side, reach) => side === "left" ? box(el).l - (reach || 0) - scrollX <= 0.5
    : side === "right" ? box(el).r + (reach || 0) - scrollX >= VW - 0.5 : false;

  // A line drawn flush against the component's outer edge by something else:
  // an ancestor's border, or the adjacent band's facing edge. Walk up only
  // while the ancestor's inner edge stays flush with the component's edge.
  function externalLine(el, side) {
    const e = EDGE[side], target = box(el)[e], found = [];
    let node = el;
    for (let up = 0; up < 5 && node; up++) {
      if (up > 0) {
        const b = borderSide(node, side);
        if (b && near(padBox(node)[e], target)) found.push({ ...b, how: "ancestor-border " + selOf(node) });
      }
      const sib = side === "top" || side === "left" ? node.previousElementSibling : node.nextElementSibling;
      if (sib && rendered(sib) && inflow(sib)) {
        const sl = edgeLine(sib, OPP[side], 0);
        if (sl && near(box(sib)[EDGE[OPP[side]]], target)) found.push({ ...sl, how: "adjacent " + selOf(sib) });
      }
      if (found.length) break;
      const par = node.parentElement;
      if (!par || SKIP.has(par.tagName) || !near(padBox(par)[e], target)) break;
      node = par;
    }
    return found;
  }

  // --- scan ---------------------------------------------------------------
  const raw = [];
  for (const el of document.querySelectorAll("*")) {
    if (SKIP.has(el.tagName) || !rendered(el)) continue;
    const kids = kidsOf(el);
    if (kids.length < 2) continue;
    const geom = frameGeom(el, kids);
    if (!geom) continue;

    const boxes = new Map(kids.map((k) => [k, box(k)]));
    const collapse = cs(el).borderCollapse === "collapse";
    const cbg = cs(el).backgroundColor;
    const seams = [];
    const unresolved = [];
    for (let i = 0; i < kids.length; i++) {
      for (let j = 0; j < kids.length; j++) {
        if (i === j) continue;
        const A = kids[i], B = kids[j], a = boxes.get(A), b = boxes.get(B);
        const vOv = Math.min(a.b, b.b) - Math.max(a.t, b.t);
        const hOv = Math.min(a.r, b.r) - Math.max(a.l, b.l);
        let dir = null, gap = 0;
        if (a.r <= b.l + 1 && vOv > 0.5 * Math.min(a.b - a.t, b.b - b.t)) { dir = "h"; gap = b.l - a.r; }
        else if (a.b <= b.t + 1 && hOv > 0.5 * Math.min(a.r - a.l, b.r - b.l)) { dir = "v"; gap = b.t - a.b; }
        if (dir === null || gap >= SPACING) continue;
        const sideA = dir === "h" ? "right" : "bottom";
        const lines = [];
        if (gap <= 1) {   // touching cells: a border on either facing edge is a shared divider
          if (!fullBorder(A)) { const l = edgeLine(A, sideA, 0); if (l) lines.push(l); }
          if (!fullBorder(B)) { const l = edgeLine(B, OPP[sideA], 0); if (l) lines.push(l); }
        }
        if (gap > 0.5) {
          const abg = cs(A).backgroundColor, bbg = cs(B).backgroundColor;
          const showsThrough = opaque(cbg) &&
            ((opaque(abg) && key(abg) !== key(cbg)) || (opaque(bbg) && key(bbg) !== key(cbg)));
          if (showsThrough && gap <= MAXSEAM) lines.push({ w: +gap.toFixed(2), color: key(cbg) });
          else if (showsThrough) unresolved.push(
            "a " + gap.toFixed(2) + "px gap over a contrasting container background is neither a "
            + "drawn divider (<=" + MAXSEAM + "px) nor spacing (>=" + SPACING + "px)");
        }
        if (!lines.length) continue;
        let spec;
        if (lines.length === 1) spec = lines[0];
        else if (lines.every((l) => l.color === lines[0].color))
          spec = { w: +(collapse ? Math.max(...lines.map((l) => l.w))
                                 : lines.reduce((s, l) => s + l.w, 0)).toFixed(2), color: lines[0].color };
        else { unresolved.push("a seam draws two lines of different colour: " + lines.map(fmt).join(" + ")); continue; }
        seams.push(spec);
      }
    }
    if (!seams.length && !unresolved.length) continue;

    // Table sections divide rows, but the frame belongs to the table.
    let comp = el;
    const disp = cs(el).display;
    if (["table-row-group", "table-header-group", "table-footer-group", "table-row"].includes(disp)) {
      let n = el.parentElement;
      while (n && !["table", "inline-table"].includes(cs(n).display)) n = n.parentElement;
      if (n) comp = n;
    }
    raw.push({ el: comp, from: el, geom: comp === el ? geom : frameGeom(comp, kidsOf(comp)) || { mode: "pad", pads: null },
               seams, unresolved, nkids: kids.length });
  }

  // Merge everything that resolved to the same component box.
  const merged = new Map();
  for (const r of raw) {
    let m = merged.get(r.el);
    if (!m) { m = { el: r.el, geom: r.geom, seams: [], unresolved: [], froms: [], nkids: 0 }; merged.set(r.el, m); }
    m.seams.push(...r.seams);
    m.unresolved.push(...r.unresolved);
    m.froms.push(selOf(r.from));
    m.nkids = Math.max(m.nkids, r.nkids);
  }

  const out = [];
  for (const m of merged.values()) {
    const el = m.el, s = cs(el);
    const problems = [], notes = [];
    for (const u of [...new Set(m.unresolved)]) problems.push({ kind: "unresolved", text: u });

    const specs = [];
    for (const sp of m.seams)
      if (!specs.some((p) => Math.abs(p.w - sp.w) <= WTOL && p.color === sp.color)) specs.push(sp);
    let divider = null;
    if (specs.length === 1) divider = specs[0];
    else if (specs.length > 1)
      problems.push({ kind: "unresolved", text: "internal dividers are not uniform (" +
        specs.map(fmt).join(", ") + "), so no single frame can match them" });

    if (s.boxShadow && s.boxShadow !== "none")
      problems.push({ kind: "unresolved", text: "component carries a box-shadow (" + s.boxShadow +
        "), which may draw an edge the audit cannot resolve from borders" });
    if (s.borderImageSource && s.borderImageSource !== "none")
      problems.push({ kind: "unresolved", text: "component carries a border-image, which the audit cannot resolve" });

    const frame = {};
    if (divider) {
      for (const side of ["top", "right", "bottom", "left"]) {
        const lines = [];
        if (m.geom.mode === "padding-frame" && m.geom.pads[side] > 0)
          lines.push({ w: +m.geom.pads[side].toFixed(2), color: m.geom.bg, how: "bg-through-padding" });
        const own = borderSide(el, side);
        if (own) lines.push({ ...own, how: "own-border" });
        let src = lines.length ? lines.map((l) => l.how).join("+") : null;
        let line = null;
        if (!lines.length) {
          const ext = externalLine(el, side);
          const uniq = [];
          for (const e of ext) if (!uniq.some((u) => Math.abs(u.w - e.w) <= WTOL && u.color === e.color)) uniq.push(e);
          if (uniq.length === 1) { line = uniq[0]; src = uniq[0].how; }
          else if (uniq.length > 1) {
            problems.push({ kind: "unresolved", side: side, text: side +
              ": two different lines are drawn flush against this edge (" + uniq.map(fmt).join(", ") + ")" });
            frame[side] = { state: "unresolved" };
            continue;
          }
        } else if (lines.length === 1) line = lines[0];
        else if (lines.every((l) => l.color === lines[0].color))
          line = { w: +lines.reduce((t, l) => t + l.w, 0).toFixed(2), color: lines[0].color };
        else {
          problems.push({ kind: "unresolved", side: side, text: side +
            ": frame edge draws two lines of different colour (" + lines.map(fmt).join(" + ") + ")" });
          frame[side] = { state: "unresolved" };
          continue;
        }
        if (!line) {
          if ((side === "left" || side === "right") && atViewport(el, side)) {
            frame[side] = { state: "viewport" };          // V2: omitted by rule
            continue;
          }
          problems.push({ kind: "open", side: side, text: side + ": frame edge is open (no line drawn); "
            + "internal dividers are " + fmt(divider) });
          frame[side] = { state: "open" };
          continue;
        }
        const outside = src && src.indexOf("own-border") === -1 && src.indexOf("bg-through-padding") === -1;
        if ((side === "left" || side === "right") && atViewport(el, side, outside ? line.w : 0)) {
          problems.push({ kind: "viewport-edge", side: side, text: side + ": a frame edge (" + fmt(line)
            + ", " + src + ") runs along the viewport edge; a full-bleed component omits it (R2, V2)" });
          frame[side] = { state: "viewport-line", w: line.w, color: line.color, src: src };
          continue;
        }
        frame[side] = { state: "line", w: line.w, color: line.color, src: src };
        const dw = Math.abs(line.w - divider.w) > WTOL, dc = line.color !== divider.color;
        if ((dw || dc) && (side === "top" || side === "bottom") && Math.abs(line.w - R1W) <= WTOL) {
          // V1: R1's rule stands in for a frame edge that could not be seen.
          const nb = neighbourBg(el, side);
          if (nb && sameInk(nb, parseColor(divider.color))) {
            frame[side] = { state: "r1", w: line.w, color: line.color, src: src };
            notes.push(side + ": R1's " + fmt(line) + " replaces a " + fmt(divider)
              + " frame edge that would be invisible against its neighbour (R2, V1)");
            continue;
          }
        }
        if (dw || dc)
          problems.push({ kind: dw && dc ? "weight+colour" : dw ? "weight" : "colour", side: side,
            text: side + ": frame edge is " + fmt(line) + " (" + src + ") but the internal dividers are "
              + fmt(divider) + " — " + (dw && dc ? "weight and colour differ" : dw ? "weight differs" : "colour differs") });
        else if (src && src.indexOf("own-border") === -1 && src.indexOf("bg-through-padding") === -1)
          notes.push(side + ": matching line comes from " + src + ", not the component's own frame");
      }
    }
    out.push({ sel: selOf(el), path: pathOf(el), cells: m.nkids, seams: m.seams.length,
               divider: divider ? fmt(divider) : null, mech: [...new Set(m.froms)].join(","),
               frame: frame, problems: problems, notes: notes });
  }
  return out;
};
"""

RUN_CJS = r"""
const path = require("node:path"), fs = require("node:fs");
const WEB = process.env.FRAME_AUDIT_WEBSITE;
const puppeteer = require(require.resolve("puppeteer", { paths: [WEB] }));
const SRC = fs.readFileSync(path.join(__dirname, "analyze.js"), "utf8");
(async () => {
  const [base, widthsCsv, listFile, outFile] = process.argv.slice(2);
  const widths = widthsCsv.split(",").map(Number);
  const routes = JSON.parse(fs.readFileSync(listFile, "utf8"));
  const browser = await puppeteer.launch({ args: ["--no-sandbox", "--force-device-scale-factor=1"] });
  const page = await browser.newPage();
  await page.emulateMediaFeatures([{ name: "prefers-reduced-motion", value: "reduce" }]);
  // The same route is loaded once per width. When the build is seconds old,
  // Chrome revalidates it, http.server answers 304, and 304 is not res.ok():
  // the page was reported "could not be rendered". Whether it happened
  // depended on how long ago the site was built. Same fix as the other tools.
  await page.setCacheEnabled(false);
  const pageErrors = [];
  page.on("pageerror", (e) => pageErrors.push(String(e)));
  const all = [];
  for (const route of routes) {
    for (const w of widths) {
      const rec = { route, width: w };
      try {
        await page.setViewport({ width: w, height: 1000, deviceScaleFactor: 1 });
        const res = await page.goto(base + route, { waitUntil: "networkidle0", timeout: 60000 });
        if (!res || !(res.ok() || res.status() === 304)) { rec.error = "HTTP " + (res ? res.status() : "no response"); all.push(rec); continue; }
        await page.evaluate(() => document.fonts && document.fonts.ready);
        await page.evaluate(SRC);
        rec.components = await page.evaluate(() => window.__frameAudit({}));
      } catch (e) { rec.error = String(e && e.message || e); }
      all.push(rec);
    }
  }
  await browser.close();
  fs.writeFileSync(outFile, JSON.stringify({ pages: all, pageErrors }));
})().catch((e) => { console.error(e); process.exit(1); });
"""


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):          # keep the tool's output to its JSON
        pass


def serve(directory, port):
    """Same pattern as tools/render_gate.py: a threaded static server on 127.0.0.1."""
    handler = lambda *a, **kw: _Quiet(*a, directory=str(directory), **kw)
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def routes_for(built: pathlib.Path):
    out = []
    for p in sorted(built.rglob("*.html")):
        rel = p.relative_to(built).as_posix()
        out.append("/" + (rel[: -len("index.html")] if rel.endswith("index.html") else rel))
    return out


def drive(built: pathlib.Path, routes, widths):
    """Render every route at every width in Chrome and collect the analyser's verdict."""
    if not routes:
        raise RuntimeError("no .html pages found under %s" % built)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="frame-audit-"))
    try:
        (tmp / "analyze.js").write_text(ANALYZE_JS)
        (tmp / "run.cjs").write_text(RUN_CJS)
        (tmp / "routes.json").write_text(json.dumps(routes))
        httpd = serve(built, PORT)
        try:
            env = dict(os.environ, FRAME_AUDIT_WEBSITE=str(WEBSITE))
            proc = subprocess.run(
                ["node", str(tmp / "run.cjs"), "http://127.0.0.1:%d" % PORT,
                 ",".join(str(w) for w in widths), str(tmp / "routes.json"), str(tmp / "out.json")],
                capture_output=True, text=True, env=env)
        finally:
            httpd.shutdown()
            httpd.server_close()
        if proc.returncode != 0:
            raise RuntimeError("browser run failed: %s" % (proc.stderr.strip() or proc.stdout.strip())[:2000])
        return json.loads((tmp / "out.json").read_text())
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def collect(data):
    """-> (errors, components_seen, incomplete_seen, per_page_counts).

    Errors are deduplicated by component identity + problem, because the same
    component appears on many pages and at every width; each entry carries the
    number of instances and up to three example locations.
    """
    errors, order = {}, []
    seen = incomplete = 0
    per_page = {}

    def add(sig, text, where):
        if sig not in errors:
            errors[sig] = {"text": text, "where": [], "instances": 0}
            order.append(sig)
        e = errors[sig]
        e["instances"] += 1
        if len(e["where"]) < 3 and where not in e["where"]:
            e["where"].append(where)

    for rec in data["pages"]:
        where = "%s @%d" % (rec["route"], rec["width"])
        bucket = per_page.setdefault(rec["route"], {"components": 0, "errors": 0})
        if rec.get("error"):
            bucket["errors"] += 1
            add("page:" + rec["route"] + ":" + rec["error"], "%s could not be rendered: %s" % (where, rec["error"]), where)
            continue
        for c in rec.get("components", []):
            seen += 1
            bucket["components"] += 1
            if c["problems"]:
                incomplete += 1
                bucket["errors"] += len(c["problems"])
            for p in c["problems"]:
                add("|".join([c["sel"], p["kind"], p.get("side", ""), p["text"][:80]]),
                    "%s  %s — %s" % (where, c["path"], p["text"]), where)
    for e in data.get("pageErrors", []):
        add("js:" + e[:80], "page JavaScript error during audit: " + e, "-")
    return [dict(errors[s]) for s in order], seen, incomplete, per_page


def run_audit(built: pathlib.Path, widths):
    data = drive(built, routes_for(built), widths)
    errors, seen, incomplete, _ = collect(data)
    return errors, seen, incomplete


def selftest():
    if not FIXTURES.is_dir():
        print(json.dumps({"ok": False, "selftest_cases": 0,
                          "failures": ["fixtures missing at %s" % FIXTURES]}, indent=2))
        return 1
    # Fixtures only. Never the built site: a selftest that can pass by reading
    # production is not testing the audit.
    names = [c[0] for c in SELFTEST_CASES]
    missing = [n for n in names if not (FIXTURES / n).is_file()]
    present = sorted(p.name for p in FIXTURES.glob("*.html"))
    failures = ["fixture file missing: %s" % n for n in missing]
    failures += ["fixture %s exists but is not a selftest case" % n for n in present if n not in names]
    data = drive(FIXTURES, ["/" + n for n in names if (FIXTURES / n).is_file()], [1440])
    data, stale, _ = apply_exemptions(data, SELFTEST_EXEMPTIONS)
    _, _, _, per_page = collect(data)
    detail = {}
    for route, text in stale:
        detail.setdefault(route, {"components": 0, "problems": []})["problems"].append(text)
    for rec in data["pages"]:
        d = detail.setdefault(rec["route"], {"components": 0, "problems": []})
        if rec.get("error"):
            d["problems"].append("render failed: " + rec["error"])
            continue
        for c in rec.get("components", []):
            d["components"] += 1
            d["problems"].extend(p["text"] for p in c["problems"])

    for name, verdict, match, min_components in SELFTEST_CASES:
        if name in missing:
            continue
        d = detail.get("/" + name, {"components": 0, "problems": []})
        got = d["problems"]
        if d["components"] < min_components:
            failures.append("%s: expected at least %d audited component(s), the audit found %d — "
                            "it did not look at the case" % (name, min_components, d["components"]))
        if verdict == "fail":
            if not got:
                failures.append("%s: expected the audit to FAIL this fixture, it reported nothing" % name)
            elif match and not any(match in g for g in got):
                failures.append("%s: expected an error containing %r, got %s" % (name, match, got))
        else:
            if got:
                failures.append("%s: expected the audit to PASS this fixture, it reported %s" % (name, got))
    out = {"ok": not failures, "selftest_cases": len(SELFTEST_CASES), "failures": failures}
    print(json.dumps(out, indent=2))
    return 0 if not failures else 1


def main():
    ap = argparse.ArgumentParser(description="R2 component-frame audit (integration.css item 54)")
    ap.add_argument("--built", default=str(DIST), help="built site directory (default website/dist)")
    ap.add_argument("--selftest", action="store_true", help="run the fixture cases under tools/fixtures/frame/")
    ap.add_argument("--widths", default=",".join(str(w) for w in WIDTHS))
    ap.add_argument("--only", default="", help="comma-separated route fragments, for debugging")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    built = pathlib.Path(args.built).resolve()
    widths = [int(w) for w in args.widths.split(",") if w.strip()]
    if not built.is_dir():
        print(json.dumps({"ok": False, "errors": ["built site not found at %s — run `cd website && npm run build`" % built],
                          "counts": {"components": 0, "incomplete": 0}}, indent=2))
        return 1
    routes = routes_for(built)
    if args.only:
        frags = [f for f in args.only.split(",") if f]
        routes = [r for r in routes if any(f in r for f in frags)]
    try:
        data = drive(built, routes, widths)
    except Exception as exc:                                   # noqa: BLE001 - reported, never swallowed
        print(json.dumps({"ok": False, "errors": [str(exc)], "counts": {"components": 0, "incomplete": 0}}, indent=2))
        return 1
    data, stale, exempted = apply_exemptions(data, NAMED_EXEMPTIONS)
    errors, seen, incomplete, _ = collect(data)
    errs = ["%s  [%d instance(s); e.g. %s]" % (e["text"], e["instances"], "; ".join(e["where"]))
            for e in errors] + [text for _, text in stale]
    out = {"ok": not errs,
           "errors": errs,
           "counts": {"components": seen, "incomplete": incomplete},
           "exempted": exempted}
    print(json.dumps(out, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())

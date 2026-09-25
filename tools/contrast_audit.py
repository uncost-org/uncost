#!/usr/bin/env python3
"""WCAG 2.2 AA contrast over the RENDERED site — every stylesheet, both states.

Why this exists
---------------
`scripts/audit_design_handoff.py` already validates a contrast matrix, but it
reads `tokens.css + components.css + site.css` only. It deliberately skips
`sections.css`, and it never opens `website/src/css/integration.css` — which is
where R4, C1, C2, G1/G2/G3 and every adoption-era colour decision actually
live. A green result there says nothing about the integration layer.

This audit takes the other approach. It does not parse CSS and model the
cascade; it renders the built site in a real browser and asks the browser what
colour each text run actually is and what it actually sits on. Selector-based
reasoning is what let these defects ship before:

  - a band painting a hardcoded hex near a token but not equal to one was
    classified as "unknown" and skipped (/about/ 3.06:1, /faq/ 3.19:1);
  - a card that repaints on hover was measured at rest only, so the hover
    state shipped at 3.25:1 and 3.91:1;
  - a `.cards` container sets `background: var(--ink)` purely so a 2px grid gap
    draws a divider, while each child repaints its own cream surface. Matching
    a child's colour against that container background reports failures for
    text that never renders on ink.

The last one is why the effective background is resolved by compositing every
ancestor layer the way a browser does, rather than by taking the nearest
ancestor that happens to declare one.

Standing rule (DESIGN_IMPORT_RUNBOOK, 2026-09-19): an audit fails on "I don't
know". Anything this cannot resolve — a gradient, an image, a colour it cannot
composite to an opaque value — is an ERROR, not a skipped line.

Usage
-----
    python3 tools/contrast_audit.py                 # built site, all routes
    python3 tools/contrast_audit.py --built DIR
    python3 tools/contrast_audit.py --routes /faq/ /news/
    python3 tools/contrast_audit.py --selftest      # adversarial fixtures
"""
from __future__ import annotations

import argparse
import http.server
import json
import os
import pathlib
import re
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_BUILT = ROOT / "website" / "dist"
WEBSITE = ROOT / "website"
FIXTURES = ROOT / "tools" / "fixtures" / "contrast"

# WCAG 2.2 AA. Large text is >=24px, or >=18.66px when bold (>=700).
MIN_NORMAL = 4.5
MIN_LARGE = 3.0
LARGE_PX = 24.0
LARGE_BOLD_PX = 18.66
BOLD = 700

# Widths to measure. Type here is fluid (clamp(...) on nearly every headline),
# so a run that is "large" at 1440 can be normal-size at 390 and fall under the
# stricter bar. Measuring one width would miss that entirely.
WIDTHS = (1440, 390)


# --------------------------------------------------------------------------
# contrast maths (WCAG 2.x relative luminance)
# --------------------------------------------------------------------------
def _srgb(c: float) -> float:
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(rgb) -> float:
    r, g, b = rgb
    return 0.2126 * _srgb(r) + 0.7152 * _srgb(g) + 0.0722 * _srgb(b)


def ratio(fg, bg) -> float:
    a, b = luminance(fg), luminance(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def required(px: float, weight: int) -> float:
    if px >= LARGE_PX or (px >= LARGE_BOLD_PX and weight >= BOLD):
        return MIN_LARGE
    return MIN_NORMAL


# --------------------------------------------------------------------------
# named exemptions — founder decisions, never a way to quiet a finding
# --------------------------------------------------------------------------
# A run is exempt only when ALL of route, selector, foreground and background
# match exactly. Keying on the colour pair is the point: if either colour
# changes, the run is no longer the thing the founder accepted and it fails
# again until someone decides again. Every exercised exemption is printed with
# its measured ratio, and an exemption whose route was audited but which
# matched nothing is an error (STALE), so the list cannot rot unnoticed.
#   (route, selector as the probe prints it, fg hex, bg hex, reason)
EXEMPTIONS = [
    ("/treasury/", "span.redact", "#0A0A0A", "#0A0A0A",
     "D2 (founder decision 2026-09-25): a deliberate redaction device — a bar "
     "drawn with ten U+2588 FULL BLOCK glyphs in ink on ink, 1.00:1 because it "
     "is meant to be unreadable. It carries no words, so no aria-label is "
     "needed to stop a screen reader speaking hidden text. CANVAS-SYNC 81."),
    ("/", "span.u-51", "#E8B84A", "#FAF7F0",
     "D5 (founder decision 2026-09-25): the homepage hero word \"Uncost\" keeps "
     "--wheat #E8B84A on cream — a founder-accepted AA exception at 1.72:1 "
     "against the 3.0 large-text bar (77.8px/700 at 1440, 38px/700 at 390). "
     "CANVAS-SYNC 82."),
]


def exemption_for(route, sel, fg_hex, bg_hex, table):
    for e in table:
        if e[0] == route and e[1] == sel and e[2] == fg_hex and e[3] == bg_hex:
            return e
    return None


# --------------------------------------------------------------------------
# the browser side
# --------------------------------------------------------------------------
# Returned per text run: colour, the composited background stack, font size and
# weight, a selector, and the state (rest|hover). Compositing happens in the
# page because only the page knows the full ancestor chain and its alphas.
PROBE_JS = r"""
const puppeteer = require(require.resolve("puppeteer", { paths: [process.argv[2]] }));
const base = process.argv[3];
const routes = JSON.parse(process.argv[4]);
const widths = JSON.parse(process.argv[5]);

// `root` scopes the probe to one subtree. Used for hover, so hovering a card
// reports that card's runs rather than re-reporting the whole page.
const IN_PAGE = (rootSel) => {
  const out = [];
  const scope = rootSel
    ? (() => { const h = document.querySelector(rootSel);
               return h ? [h, ...h.querySelectorAll("*")] : []; })()
    : document.querySelectorAll("body *");
  const parse = (s) => {
    if (!s) return null;
    s = s.trim();
    if (s === "transparent") return [0, 0, 0, 0];
    const m = s.match(/^rgba?\(([^)]+)\)$/);
    if (!m) return undefined;              // undefined = cannot resolve
    const p = m[1].split(/[,\s/]+/).filter(Boolean).map(Number);
    if (p.length < 3 || p.some((n) => Number.isNaN(n))) return undefined;
    return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1];
  };
  // Composite src over dst, both premultiplied-free rgba.
  const over = (src, dst) => {
    const a = src[3] + dst[3] * (1 - src[3]);
    if (a === 0) return [0, 0, 0, 0];
    return [
      (src[0] * src[3] + dst[0] * dst[3] * (1 - src[3])) / a,
      (src[1] * src[3] + dst[1] * dst[3] * (1 - src[3])) / a,
      (src[2] * src[3] + dst[2] * dst[3] * (1 - src[3])) / a,
      a,
    ];
  };
  const sel = (el) => {
    const id = el.id ? "#" + el.id : "";
    const cls = (el.className && el.className.toString().trim())
      ? "." + el.className.toString().trim().split(/\s+/).slice(0, 3).join(".")
      : "";
    return el.tagName.toLowerCase() + id + cls;
  };
  const hasText = (el) => {
    for (const n of el.childNodes) {
      if (n.nodeType === 3 && n.textContent.trim().length) return true;
    }
    return false;
  };
  const visible = (el) => {
    if (el.offsetParent === null && getComputedStyle(el).position !== "fixed") return false;
    const cs = getComputedStyle(el);
    if (cs.visibility === "hidden" || cs.display === "none") return false;
    if (parseFloat(cs.opacity) === 0) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };

  for (const el of scope) {
    if (!hasText(el) || !visible(el)) continue;
    const cs = getComputedStyle(el);
    const fg = parse(cs.color);
    // Walk the ancestor chain compositing backgrounds until opaque. A layer we
    // cannot parse (gradient, image) is reported as unresolved rather than
    // guessed at.
    let acc = [0, 0, 0, 0];
    let unresolved = null;
    let node = el;
    while (node && node !== document.documentElement.parentNode) {
      const ns = getComputedStyle(node);
      if (ns.backgroundImage && ns.backgroundImage !== "none") {
        unresolved = "background-image:" + ns.backgroundImage.slice(0, 60);
        break;
      }
      const bg = parse(ns.backgroundColor);
      if (bg === undefined) { unresolved = "background-color:" + ns.backgroundColor; break; }
      if (bg) acc = over(acc, bg);
      if (acc[3] >= 0.999) break;
      node = node.parentElement;
    }
    if (!unresolved && acc[3] < 0.999) {
      const hb = parse(getComputedStyle(document.documentElement).backgroundColor);
      if (hb && hb[3] > 0) acc = over(acc, hb);
    }
    out.push({
      sel: sel(el),
      text: (el.textContent || "").trim().slice(0, 40),
      fg: fg === undefined ? null : fg,
      fgRaw: cs.color,
      bg: unresolved ? null : acc,
      unresolved,
      px: parseFloat(cs.fontSize),
      weight: parseInt(cs.fontWeight, 10) || 400,
    });
  }
  return out;
};

(async () => {
  const browser = await puppeteer.launch({ args: ["--no-sandbox", "--force-device-scale-factor=1"] });
  const page = await browser.newPage();
  await page.emulateMediaFeatures([{ name: "prefers-reduced-motion", value: "reduce" }]);
  // Without this the second viewport width re-requests the same URL and the
  // dev server answers 304, which is not res.ok() — the audit then reported a
  // load failure for a page that was served perfectly well.
  await page.setCacheEnabled(false);
  const all = [];
  for (const route of routes) {
    for (const w of widths) {
      await page.setViewport({ width: w, height: 1000, deviceScaleFactor: 1 });
      let res;
      try {
        res = await page.goto(base + route, { waitUntil: "load", timeout: 60000 });
      } catch (e) {
        all.push({ route, width: w, loadError: String(e).slice(0, 200) });
        continue;
      }
      if (!res || !(res.ok() || res.status() === 304)) {
        all.push({ route, width: w, loadError: "HTTP " + (res && res.status()) });
        continue;
      }
      try { await page.evaluate(() => document.fonts && document.fonts.ready); } catch (e) {}
      const rest = await page.evaluate(IN_PAGE, null);
      all.push({ route, width: w, state: "rest", runs: rest });

      // Hover. Only elements that a :hover rule can actually match are worth
      // probing, so collect those selectors from the live stylesheets rather
      // than hovering all few-thousand elements.
      const hoverSels = await page.evaluate(() => {
        const out = new Set();
        for (const sheet of document.styleSheets) {
          let rules;
          try { rules = sheet.cssRules; } catch (e) { continue; }
          if (!rules) continue;
          // Check the rule FIRST, then descend. Chrome gives every CSSStyleRule
          // a `cssRules` property now that CSS Nesting exists, and an empty
          // CSSRuleList is a truthy object — so an `if (r.cssRules) continue`
          // here skipped every style rule on the page and collected nothing.
          // The audit then measured zero hover states and reported clean.
          const walk = (list) => {
            for (const r of list) {
              if (r.selectorText && r.selectorText.includes(":hover")) {
                for (const part of r.selectorText.split(",")) {
                  const base = part.trim().replace(/:hover/g, "").replace(/::[a-z-]+/g, "").trim();
                  if (base && !base.includes(":")) out.add(base);
                }
              }
              if (r.cssRules && r.cssRules.length) walk(r.cssRules);
            }
          };
          walk(rules);
        }
        return [...out];
      });
      const hoverRuns = [];
      for (const hs of hoverSels) {
        let count = 0;
        try { count = await page.$$eval(hs, (els) => els.length); } catch (e) { continue; }
        for (let i = 0; i < Math.min(count, 3); i++) {
          try {
            // Mark the instance, so the probe scopes to exactly this subtree
            // rather than matching reconstructed selector strings — that
            // matching silently dropped every hover run and reported clean.
            const ok = await page.evaluate((s, n) => {
              document.querySelectorAll("[data-uncost-hover]")
                .forEach((e) => e.removeAttribute("data-uncost-hover"));
              const el = document.querySelectorAll(s)[n];
              if (!el) return false;
              el.setAttribute("data-uncost-hover", "1");
              return true;
            }, hs, i);
            if (!ok) continue;
            const handle = await page.$("[data-uncost-hover]");
            if (!handle) continue;
            await handle.hover();
            const probed = await page.evaluate(IN_PAGE, "[data-uncost-hover]");
            for (const r of probed) hoverRuns.push({ ...r, hoverSel: hs });
          } catch (e) { /* detached, off-screen, or not hoverable */ }
        }
      }
      try {
        await page.evaluate(() => document.querySelectorAll("[data-uncost-hover]")
          .forEach((e) => e.removeAttribute("data-uncost-hover")));
      } catch (e) {}
      if (hoverRuns.length) all.push({ route, width: w, state: "hover", runs: hoverRuns });
      // Reset hover so the next width starts clean.
      try { await page.mouse.move(0, 0); } catch (e) {}
    }
  }
  await browser.close();
  process.stdout.write(JSON.stringify(all));
})().catch((e) => { console.error(e); process.exit(1); });
"""


def serve(directory: pathlib.Path, port: int):
    handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(
        *a, directory=str(directory), **kw
    )
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def probe(directory: pathlib.Path, routes, widths, port: int):
    """Render `routes` from `directory` and return every measured text run."""
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="uncost-contrast-"))
    try:
        js = tmp / "probe.cjs"
        js.write_text(PROBE_JS, encoding="utf-8")
        httpd = serve(directory, port)
        try:
            proc = subprocess.run(
                ["node", str(js), str(WEBSITE), f"http://127.0.0.1:{port}",
                 json.dumps(list(routes)), json.dumps(list(widths))],
                capture_output=True, text=True, timeout=1800,
            )
        finally:
            httpd.shutdown()
            httpd.server_close()
        if proc.returncode != 0:
            raise RuntimeError(f"probe failed: {proc.stderr[-2000:]}")
        return json.loads(proc.stdout)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def routes_in(directory: pathlib.Path):
    out = []
    for p in sorted(directory.rglob("*.html")):
        rel = p.relative_to(directory)
        out.append("/" + str(rel.parent).replace("\\", "/").strip(".").strip("/") + "/"
                   if rel.name == "index.html" else "/" + str(rel).replace("\\", "/"))
    return ["/" if r == "//" else r for r in out]


def evaluate(payload, exemptions=None):
    """Turn measured runs into errors. Fails closed on anything unresolved."""
    table = EXEMPTIONS if exemptions is None else exemptions
    errors = []
    checked = 0
    pairs = set()
    unresolved = 0
    exempted = {}
    audited_routes = {p.get("route") for p in payload}
    for page in payload:
        route, width = page.get("route"), page.get("width")
        if page.get("loadError"):
            errors.append(f"LOAD {route}@{width}: {page['loadError']} "
                          f"(an audit that cannot see its subject fails)")
            continue
        state = page.get("state", "rest")
        for r in page.get("runs", []):
            where = f"{route}@{width} [{state}] {r['sel']}"
            if r.get("unresolved"):
                unresolved += 1
                errors.append(f"UNRESOLVED {where}: {r['unresolved']} — cannot be "
                              f"judged, so it is a failure, not a skip")
                continue
            if not r.get("fg"):
                unresolved += 1
                errors.append(f"UNRESOLVED {where}: colour {r.get('fgRaw')!r}")
                continue
            bg = r.get("bg")
            if not bg or bg[3] < 0.999:
                unresolved += 1
                errors.append(f"UNRESOLVED {where}: background never reached an "
                              f"opaque value (alpha={bg[3] if bg else 'n/a'})")
                continue
            fg_rgb = r["fg"][:3]
            # Text alpha < 1 composites over its own background.
            if r["fg"][3] < 0.999:
                a = r["fg"][3]
                fg_rgb = [fg_rgb[i] * a + bg[i] * (1 - a) for i in range(3)]
            got = ratio(fg_rgb, bg[:3])
            need = required(r["px"], r["weight"])
            checked += 1
            pairs.add((
                "#%02X%02X%02X" % tuple(int(round(c)) for c in fg_rgb),
                "#%02X%02X%02X" % tuple(int(round(c)) for c in bg[:3]),
                need,
            ))
            fg_hex = "#%02X%02X%02X" % tuple(int(round(c)) for c in fg_rgb)
            bg_hex = "#%02X%02X%02X" % tuple(int(round(c)) for c in bg[:3])
            if got + 1e-9 < need and exemption_for(route, r["sel"], fg_hex, bg_hex, table):
                ex = exemption_for(route, r["sel"], fg_hex, bg_hex, table)
                k = (route, r["sel"], fg_hex, bg_hex)
                rec = exempted.setdefault(k, {"route": route, "selector": r["sel"],
                                              "fg": fg_hex, "bg": bg_hex,
                                              "ratio": round(got, 2), "required": need,
                                              "text": r["text"], "runs": 0,
                                              "reason": ex[4]})
                rec["runs"] += 1
                continue
            if got + 1e-9 < need:
                errors.append(
                    f"CONTRAST {where}: {got:.2f} < {need} "
                    f"({r['px']:.1f}px/{r['weight']}) "
                    f"fg=#%02X%02X%02X bg=#%02X%02X%02X text={r['text']!r}"
                    % (*[int(round(c)) for c in fg_rgb], *[int(round(c)) for c in bg[:3]])
                )
    # 870 individual lines is not a finding, it is a haystack. The same handful
    # of colour pairs repeat across every route, so group by the pair and the
    # bar it missed and carry one worked example each.
    groups = {}
    for e in errors:
        m = re.match(r"CONTRAST (\S+) \[(\w+)\] (\S+): ([\d.]+) < ([\d.]+) "
                     r"\(([\d.]+)px/(\d+)\) fg=(#\w{6}) bg=(#\w{6})", e)
        if not m:
            key = ("OTHER", e.split(":")[0], "", "", "")
            g = groups.setdefault(key, {"count": 0, "example": e})
            g["count"] += 1
            continue
        where, state, sel, got, need, px, wt, fg, bg = m.groups()
        key = (fg, bg, need, state, "large" if float(need) == MIN_LARGE else "normal")
        g = groups.setdefault(key, {"count": 0, "worst": 99.0, "example": ""})
        g["count"] += 1
        if float(got) < g["worst"]:
            g["worst"] = float(got)
            g["example"] = f"{where} {sel} {px}px/{wt} {got}<{need}"
    summary = sorted(
        ({"fg": k[0], "bg": k[1], "required": k[2], "state": k[3], "size": k[4],
          "occurrences": v["count"], "worst": v.get("worst"), "example": v["example"]}
         for k, v in groups.items()),
        key=lambda d: -d["occurrences"],
    )
    used = {(k[0], k[1], k[2], k[3]) for k in exempted}
    for e in table:
        if e[0] in audited_routes and tuple(e[:4]) not in used:
            errors.append(f"STALE EXEMPTION {e[0]} {e[1]} fg={e[2]} bg={e[3]}: its route was "
                          f"audited and nothing matched it — the element or its colours "
                          f"changed, so the founder decision it records no longer "
                          f"describes the page")
    return errors, {"runs_checked": checked, "distinct_pairs": len(pairs),
                    "unresolved": unresolved, "failing_pairs": summary,
                    "exempted": sorted(exempted.values(), key=lambda d: (d["route"], d["selector"]))}


# --------------------------------------------------------------------------
# selftest — adversarial fixtures only, never a tracked source
# --------------------------------------------------------------------------
GOOD_1 = """<!doctype html><meta charset=utf-8><title>good cream</title>
<style>body{background:#FAF7F0;color:#0E0E0C;font:16px sans-serif}
.deep{color:#B23A14}</style>
<body><p>Ink on cream, 18.9:1.</p><p class=deep>Coral-deep on cream, 5.59:1.</p></body>"""

GOOD_2 = """<!doctype html><meta charset=utf-8><title>good ink</title>
<style>body{background:#0E0E0C;color:#FAF7F0;font:16px sans-serif}
.oi{color:#E8734A}
h1{font-size:48px;font-weight:700;color:#E8734A}</style>
<body><p>Cream on ink.</p><p class=oi>Coral-on-ink, 6.42:1.</p>
<h1>Large heading on ink</h1></body>"""

# Each BAD_* must be caught. Named for the real defect class it stands in for.
BAD_SMALL_ON_WHEAT = """<!doctype html><meta charset=utf-8><title>bad wheat</title>
<style>body{background:#E8B84A;color:#B23A14;font:13px sans-serif}</style>
<body><p>Coral-deep on wheat is 3.25:1 at 13px — below the 4.5 bar.</p></body>"""

BAD_ONINK_ON_CREAM = """<!doctype html><meta charset=utf-8><title>bad travel</title>
<style>body{background:#FAF7F0;font:40px sans-serif}
p{color:#E8734A}</style>
<body><p>coral-on-ink on cream is 2.81:1, under even the large bar</p></body>"""

# The nested-container case: the grid container is ink purely to draw a 2px gap
# divider; each cell repaints cream. Text is cream-grounded, NOT ink-grounded.
# A correct audit PASSES this. It is here to prove the audit composites the
# real stack instead of grabbing the nearest ancestor with a background.
GOOD_NESTED_GAP = """<!doctype html><meta charset=utf-8><title>gap divider</title>
<style>body{background:#FAF7F0;font:16px sans-serif}
.cards{display:grid;grid-template-columns:1fr 1fr;gap:2px;background:#0E0E0C}
.card{background:#FAF7F0;padding:12px}
.echo{color:#B23A14}</style>
<body><div class=cards><div class=card><span class=echo>echo span 5.59:1</span></div>
<div class=card><span class=echo>echo span 5.59:1</span></div></div></body>"""

# Hover repaints the card wheat; the small print then fails. Resting state is
# fine, so an audit that measures rest only reports this page clean.
BAD_HOVER = """<!doctype html><meta charset=utf-8><title>bad hover</title>
<style>body{background:#FAF7F0;font:16px sans-serif}
.cw{background:#FAF7F0;padding:20px;width:300px}
.cw:hover{background:#E8B84A}
.cw .meta{font-size:11px;color:#B23A14}</style>
<body><div class=cw><span class=meta>publisher and period, 3.25:1 on hover</span></div></body>"""

# An unresolvable ground. Must be an ERROR, not a silent pass.
BAD_UNRESOLVED = """<!doctype html><meta charset=utf-8><title>gradient</title>
<style>body{background:linear-gradient(#FAF7F0,#E8B84A);color:#B23A14;font:13px sans-serif}</style>
<body><p>ground is a gradient — cannot be judged</p></body>"""

# Alpha text over a light ground: 50% ink on cream is ~4.0:1, under the bar.
BAD_ALPHA = """<!doctype html><meta charset=utf-8><title>alpha</title>
<style>body{background:#FAF7F0;font:14px sans-serif}
p{color:rgba(14,14,12,0.42)}</style>
<body><p>semi-transparent ink on cream</p></body>"""

# Exemptions. The selftest carries its own table (EXEMPT_FIXTURES) so it never
# depends on the site's. The first fixture's failing run matches an entry and
# must pass; the second has the SAME route pattern and selector but a different
# ink, so it must NOT be exempted — an exemption keyed on a selector alone
# would pass it, and that is the loophole this case exists to close.
GOOD_EXEMPT = """<!doctype html><meta charset=utf-8><title>exempt</title>
<style>body{background:#FAF7F0;color:#0A0A0A;font:16px sans-serif}
.redact{background:#0A0A0A;color:#0A0A0A}</style>
<body><p>Ink on cream, then a bar: <span class=redact>&#9608;&#9608;&#9608;</span></p></body>"""

BAD_EXEMPT_LOOKALIKE = """<!doctype html><meta charset=utf-8><title>lookalike</title>
<style>body{background:#FAF7F0;color:#0A0A0A;font:16px sans-serif}
.redact{background:#0A0A0A;color:#2A2A26}</style>
<body><p>Same selector, different ink: <span class=redact>hidden words</span></p></body>"""

# A listed exemption whose route is audited and which matches nothing must be
# reported, or a decision about an element that no longer exists lingers.
GOOD_NO_REDACT = """<!doctype html><meta charset=utf-8><title>stale</title>
<style>body{background:#FAF7F0;color:#0A0A0A;font:16px sans-serif}</style>
<body><p>No redaction bar here at all.</p></body>"""

EXEMPT_FIXTURES = [
    ("/good-exempt.html", "span.redact", "#0A0A0A", "#0A0A0A", "fixture"),
    ("/bad-exempt-lookalike.html", "span.redact", "#0A0A0A", "#0A0A0A", "fixture"),
    ("/bad-exempt-stale.html", "span.redact", "#0A0A0A", "#0A0A0A", "fixture"),
]

CASES = [
    ("good-cream.html", GOOD_1, True),
    ("good-ink.html", GOOD_2, True),
    ("good-nested-gap.html", GOOD_NESTED_GAP, True),
    ("bad-small-on-wheat.html", BAD_SMALL_ON_WHEAT, False),
    ("bad-onink-on-cream.html", BAD_ONINK_ON_CREAM, False),
    ("bad-hover.html", BAD_HOVER, False),
    ("bad-unresolved-ground.html", BAD_UNRESOLVED, False),
    ("bad-alpha-text.html", BAD_ALPHA, False),
    ("good-exempt.html", GOOD_EXEMPT, True),
    ("bad-exempt-lookalike.html", BAD_EXEMPT_LOOKALIKE, False),
    ("bad-exempt-stale.html", GOOD_NO_REDACT, False),
]


def write_fixtures():
    FIXTURES.mkdir(parents=True, exist_ok=True)
    for name, body, _ in CASES:
        (FIXTURES / name).write_text(body, encoding="utf-8")
    (FIXTURES / "README.md").write_text(
        "# contrast_audit fixtures\n\n"
        "Inputs for `python3 tools/contrast_audit.py --selftest`. Each `bad-*`\n"
        "file carries one real defect class this repository has actually\n"
        "shipped or nearly shipped; the audit must FAIL on every one of them\n"
        "and PASS every `good-*` file.\n\n"
        "`good-nested-gap.html` is the important pass: a grid container paints\n"
        "ink only so a 2px gap draws a divider, while each cell repaints cream.\n"
        "An audit that takes the nearest ancestor with a background reports\n"
        "these echo spans as ink-grounded failures. They are cream-grounded and\n"
        "fine.\n\n"
        "These files are fixtures, never site sources. The selftest never runs\n"
        "against website/dist or any tracked source.\n",
        encoding="utf-8",
    )


def selftest(port: int) -> int:
    write_fixtures()
    failures = []
    for name, _, should_pass in CASES:
        errors, _counts = evaluate(probe(FIXTURES, ["/" + name], WIDTHS, port),
                                   exemptions=EXEMPT_FIXTURES)
        passed = not errors
        if passed != should_pass:
            failures.append({
                "fixture": name,
                "expected": "PASS" if should_pass else "FAIL",
                "got": "PASS" if passed else "FAIL",
                "sample": errors[:2],
            })
    print(json.dumps({"ok": not failures, "selftest_cases": len(CASES),
                      "failures": failures}, indent=2))
    return 1 if failures else 0


def show(payload, needles):
    """Every measured run matching a needle, as measured. Reporting aid only."""
    needles = [n.lower() for n in needles]
    rows = []
    for page in payload:
        for r in page.get("runs", []) or []:
            hay = (r.get("text") or "").lower() + " " + (r.get("sel") or "").lower()
            if not any(n in hay for n in needles):
                continue
            row = {"route": page["route"], "width": page["width"],
                   "state": page.get("state", "rest"), "sel": r["sel"],
                   "text": r["text"], "px": r["px"], "weight": r["weight"]}
            if r.get("fg") and r.get("bg") and r["bg"][3] >= 0.999:
                fg = r["fg"][:3]
                if r["fg"][3] < 0.999:
                    a = r["fg"][3]
                    fg = [fg[i] * a + r["bg"][i] * (1 - a) for i in range(3)]
                row["fg"] = "#%02X%02X%02X" % tuple(int(round(c)) for c in fg)
                row["bg"] = "#%02X%02X%02X" % tuple(int(round(c)) for c in r["bg"][:3])
                row["ratio"] = round(ratio(fg, r["bg"][:3]), 2)
                row["required"] = required(r["px"], r["weight"])
            else:
                row["unresolved"] = r.get("unresolved") or "no opaque ground"
            rows.append(row)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--built", default=str(DEFAULT_BUILT))
    ap.add_argument("--routes", nargs="*")
    ap.add_argument("--port", type=int, default=8870)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--max-errors", type=int, default=40)
    ap.add_argument("--show", nargs="*", default=None, metavar="TEXT",
                    help="also print every measured run whose text or selector "
                         "contains TEXT (case-insensitive), with its colours and "
                         "ratio — so a colour quoted in a report comes from here")
    args = ap.parse_args()

    if args.selftest:
        return selftest(args.port)

    built = pathlib.Path(args.built).resolve()
    if not built.is_dir():
        print(json.dumps({"ok": False, "errors": [f"no built directory at {built}"]}))
        return 1
    routes = args.routes or routes_in(built)
    payload = probe(built, routes, WIDTHS, args.port)
    errors, counts = evaluate(payload)
    counts["routes"] = len(routes)
    counts["widths"] = len(WIDTHS)
    out = {
        "ok": not errors,
        "errors": errors[: args.max_errors],
        "error_count": len(errors),
        "counts": counts,
    }
    if args.show:
        out["shown"] = show(payload, args.show)
    print(json.dumps(out, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

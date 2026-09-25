#!/usr/bin/env python3
"""C19 type audit — one section-headline size, one wrap point per prose band.

Why this exists
---------------
Two invariants were claimed for C19 from scratchpad scripts that no longer
exist, so nothing in the repository can re-check them:

  C19.1  ONE SECTION-HEADLINE SIZE. Every section headline outside a page hero
         renders the SAME computed font-size. A section headline is the
         headline of a content band; a content band is a direct child of
         <main>. The page hero — the first band on the page, or a .titleband /
         .hero — is allowed its own larger size and is excluded.

  C19.2  ONE WRAP POINT PER PROSE BAND. Within a prose band, the headline and
         the body wrap at the SAME width.

Nothing here is hardcoded to today's numbers. The measure is moving from 728px
to min(66vw, 960px) and the headline scale may move with it, so an audit that
asserted "56px" or "728px" would be wrong the week it landed. This one asserts
CONSISTENCY and derives the expected value from the page itself: the expected
headline size is the MODAL size of the section headlines actually rendered at
that width, and the expected measure of a band's body is whatever its own
headline wraps at. Both survive any scale change; neither survives an
inconsistency.

Everything is resolved from COMPUTED STYLE in a real browser. No CSS text is
parsed. `h2.sec` renders at 56px, 60px or 72px on this site depending on
whether a :has() exclusion matched three stylesheets up — the selector tells
you nothing, the browser tells you everything.

What counts as what
-------------------
band          a direct element child of <main> that renders (not <script>,
              not display:none, not empty).
page hero     the first band, or a band classed .titleband / .hero. A
              `.blk--first` is a hero only when it is genuinely first;
              integration.css item 349 records that a `.blk--first` sitting
              after a title band is NOT the first band on the page.
headline      the first <h1>/<h2> in a band that is a BAND-level heading:
              within 3 levels of the band, not inside a non-content landmark
              (nav/aside/header/footer/form/dialog), and not inside a repeated
              item — an element with a sibling carrying the same tag and class.
              That last filter is what separates "Working harder, still
              falling behind." from the three card headings underneath it;
              both are <h2>, only one is the section headline.
prose band    a non-hero band with a headline AND a body: the first rendering
              <p> after the headline that passes the same band-level filter.
              A band whose headline sits above a card grid has no body and is
              not a prose band — the measure rule is about running text.
wrap point    min(computed max-width, the containing block's content width).
              The raw max-width alone is the wrong comparand: at 390 a 728px
              cap and no cap at all wrap at exactly the same place, and
              reporting that as a defect is noise. Where the cap actually
              binds, the wrap point IS the cap.

STANDING RULE (docs/DESIGN_IMPORT_RUNBOOK.md, 2026-09-19): this audit fails on
"I don't know". A route that will not load, a page with no <main>, a headline
whose size will not resolve, a max-width in a unit that cannot be reduced to
px — each is an ERROR, never a skipped line.

Usage
-----
    python3 tools/type_audit.py                    # built site, all routes
    python3 tools/type_audit.py --built DIR
    python3 tools/type_audit.py --routes / /faq/
    python3 tools/type_audit.py --selftest         # adversarial fixtures only

Exit 0 when ok, 1 on any error.
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

ROOT = pathlib.Path(__file__).resolve().parents[1]
WEBSITE = ROOT / "website"
DEFAULT_BUILT = WEBSITE / "dist"
FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures" / "type"
DEFAULT_PORT = 8852

# Type on this site is fluid — clamp() on every headline and, after the
# in-flight change, a vw term in the measure. One width proves nothing about
# the other, so both ends of the range are measured and each gets its own
# modal size.
WIDTHS = (1440, 390)

# A clamp() evaluated at the same viewport width is identical across routes, so
# this only has to absorb sub-pixel rounding, not a design step.
SIZE_TOL = 0.5
# Layout slack on a wrap point: padding and border rounding, not a measure.
MEASURE_TOL = 1.0
# How far below a band a heading may sit and still be that band's headline.
# 3 reaches `.blk > .u-63 > div > h2` (a real home-page headline) and stops
# short of `.sys > .card > .bd > .actions > h2`.
MAX_DEPTH = 3


# --------------------------------------------------------------------------
# the browser side
# --------------------------------------------------------------------------
PROBE_JS = r"""
const puppeteer = require(require.resolve("puppeteer", { paths: [process.argv[2]] }));
const base = process.argv[3];
const routes = JSON.parse(process.argv[4]);
const widths = JSON.parse(process.argv[5]);
const MAX_DEPTH = parseInt(process.argv[6], 10);

const IN_PAGE = (maxDepth) => {
  const NON_CONTENT = new Set(["NAV", "ASIDE", "HEADER", "FOOTER", "FORM", "DIALOG"]);
  const NON_RENDER = new Set(["SCRIPT", "STYLE", "TEMPLATE", "LINK", "META", "NOSCRIPT"]);

  const main = document.querySelector("main");
  if (!main) return { noMain: true };

  const sel = (el) => {
    const id = el.id ? "#" + el.id : "";
    const raw = (el.getAttribute("class") || "").trim();
    const cls = raw ? "." + raw.split(/\s+/).slice(0, 3).join(".") : "";
    return el.tagName.toLowerCase() + id + cls;
  };
  const pathTo = (band, el) => {
    const parts = [];
    let n = el;
    while (n && n !== band) { parts.unshift(sel(n)); n = n.parentElement; }
    return parts.join(" > ");
  };
  const visible = (el) => {
    const cs = getComputedStyle(el);
    if (cs.display === "none" || cs.visibility === "hidden") return false;
    if (el.offsetParent === null && cs.position !== "fixed") return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };
  // Two siblings with the same tag AND the same class attribute are items of
  // one repeated set — cards, tiers, grid cells. A heading inside one is that
  // item's heading, not the band's.
  const key = (el) => el.tagName + "|" + (el.getAttribute("class") || "");
  const repeated = (el) => {
    const p = el.parentElement;
    if (!p) return false;
    let n = 0;
    for (const s of p.children) if (key(s) === key(el)) n++;
    return n > 1;
  };
  const depthFrom = (band, el) => {
    let d = 0, n = el;
    while (n && n !== band) { d++; n = n.parentElement; }
    return n === band ? d : -1;
  };
  const bandLevel = (band, el) => {
    const d = depthFrom(band, el);
    if (d < 1 || d > maxDepth) return false;
    let n = el;
    while (n && n !== band) {
      if (NON_CONTENT.has(n.tagName)) return false;
      if (n !== el && repeated(n)) return false;
      n = n.parentElement;
    }
    return true;
  };
  // Content width of the element's containing block. A max-width only bites
  // when it is narrower than this; wider, and the container is the wrap point.
  const containerWidth = (el) => {
    const p = el.parentElement;
    if (!p) return NaN;
    const cs = getComputedStyle(p);
    return p.clientWidth - (parseFloat(cs.paddingLeft) || 0) - (parseFloat(cs.paddingRight) || 0);
  };
  const wrapPoint = (el) => {
    const raw = getComputedStyle(el).maxWidth;
    const container = containerWidth(el);
    let cap = null, unresolved = null;
    if (raw === "none") cap = Number.POSITIVE_INFINITY;
    else if (/px$/.test(raw)) cap = parseFloat(raw);
    else if (/%$/.test(raw)) {
      const pct = parseFloat(raw);
      cap = (isFinite(container) && container > 0 && isFinite(pct))
        ? container * pct / 100 : Number.NaN;
      if (!isFinite(cap)) unresolved = "max-width:" + raw + " over container " + container;
    } else {
      cap = Number.NaN;
      unresolved = "max-width:" + raw + " (not reducible to px)";
    }
    if (!unresolved && cap !== Number.POSITIVE_INFINITY && !isFinite(cap)) {
      unresolved = "max-width:" + raw;
    }
    if (!unresolved && !(isFinite(container) && container > 0)) {
      unresolved = "containing block width " + container;
    }
    return {
      raw: raw,
      container: isFinite(container) ? container : null,
      wrap: unresolved ? null : Math.min(cap, container),
      unresolved: unresolved,
    };
  };

  const bands = [];
  const rendering = [...main.children].filter(
    (el) => !NON_RENDER.has(el.tagName) && (el.textContent || "").trim().length && visible(el)
  );
  rendering.forEach((band, i) => {
    const hero = i === 0
      || band.classList.contains("titleband")
      || band.classList.contains("hero");

    const allHeads = [...band.querySelectorAll("h1,h2")];
    const heads = allHeads.filter(
      (h) => bandLevel(band, h) && visible(h) && (h.textContent || "").trim().length
    );
    const h = heads[0] || null;

    let body = null;
    if (h) {
      for (const p of band.querySelectorAll("p")) {
        if (!(h.compareDocumentPosition(p) & Node.DOCUMENT_POSITION_FOLLOWING)) continue;
        if (!bandLevel(band, p)) continue;
        if (!visible(p) || !(p.textContent || "").trim().length) continue;
        body = p;
        break;
      }
    }

    bands.push({
      i: i,
      sel: sel(band),
      hero: hero,
      headings_seen: allHeads.length,
      headline: h ? {
        sel: sel(h),
        path: pathTo(band, h),
        text: (h.textContent || "").trim().replace(/\s+/g, " ").slice(0, 60),
        px: parseFloat(getComputedStyle(h).fontSize),
        measure: wrapPoint(h),
      } : null,
      body: body ? {
        sel: sel(body),
        path: pathTo(band, body),
        text: (body.textContent || "").trim().replace(/\s+/g, " ").slice(0, 40),
        measure: wrapPoint(body),
      } : null,
    });
  });
  return { bands: bands };
};

(async () => {
  const browser = await puppeteer.launch({
    args: ["--no-sandbox", "--force-device-scale-factor=1"],
  });
  const page = await browser.newPage();
  await page.emulateMediaFeatures([{ name: "prefers-reduced-motion", value: "reduce" }]);
  // Without this the second viewport width re-requests the same URL, the dev
  // server answers 304, res.ok() is false, and the audit reports a load
  // failure for a page that was served perfectly well.
  await page.setCacheEnabled(false);
  const out = [];
  for (const route of routes) {
    for (const w of widths) {
      await page.setViewport({ width: w, height: 1000, deviceScaleFactor: 1 });
      let res;
      try {
        res = await page.goto(base + route, { waitUntil: "load", timeout: 60000 });
      } catch (e) {
        out.push({ route: route, width: w, loadError: String(e).slice(0, 200) });
        continue;
      }
      if (!res || !(res.ok() || res.status() === 304)) {
        out.push({ route: route, width: w, loadError: "HTTP " + (res && res.status()) });
        continue;
      }
      try { await page.evaluate(() => document.fonts && document.fonts.ready); } catch (e) {}
      const got = await page.evaluate(IN_PAGE, MAX_DEPTH);
      out.push(Object.assign({ route: route, width: w }, got));
    }
  }
  await browser.close();
  process.stdout.write(JSON.stringify(out));
})().catch((e) => { console.error(e); process.exit(1); });
"""


def serve(directory: pathlib.Path, port: int):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):  # a 66-route run logs ~900 lines otherwise
            pass

    handler = lambda *a, **kw: Quiet(*a, directory=str(directory), **kw)
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def probe(directory: pathlib.Path, routes, widths, port: int):
    """Render `routes` from `directory` and return per-route band readings."""
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="uncost-type-"))
    try:
        js = tmp / "probe.cjs"
        js.write_text(PROBE_JS, encoding="utf-8")
        httpd = serve(directory, port)
        try:
            proc = subprocess.run(
                ["node", str(js), str(WEBSITE), f"http://127.0.0.1:{port}",
                 json.dumps(list(routes)), json.dumps(list(widths)), str(MAX_DEPTH)],
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
        rel = p.relative_to(directory).as_posix()
        out.append("/" + rel[: -len("index.html")] if rel.endswith("index.html")
                   else "/" + rel)
    return out


# --------------------------------------------------------------------------
# judging
# --------------------------------------------------------------------------
def _modal(values):
    """Most common value. Ties go to the smaller, so the verdict is stable."""
    counts = collections.Counter(round(v, 2) for v in values)
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]


def evaluate(payload):
    errors = []
    counts = {"routes": 0, "headlines": 0, "headline_misses": 0,
              "prose_bands": 0, "measure_mismatches": 0}
    component_only = 0
    seen_routes = set()
    load_failures = 0
    by_width = collections.defaultdict(list)
    modal_by_width = {}
    size_groups = collections.Counter()
    size_example = {}
    measure_groups = collections.Counter()
    measure_example = {}

    for page in payload:
        route, width = page.get("route"), page.get("width")
        seen_routes.add(route)
        if page.get("loadError"):
            load_failures += 1
            errors.append(
                f"LOAD {route}@{width}: {page['loadError']} — an audit that "
                f"cannot see its subject fails, it does not skip"
            )
            continue
        if page.get("noMain"):
            errors.append(
                f"NO-MAIN {route}@{width}: no <main> element, so this page's "
                f"content bands cannot be identified"
            )
            continue
        by_width[width].append(page)
    counts["routes"] = len(seen_routes)

    # --- C19.1 one section-headline size -----------------------------------
    for width in sorted(by_width, reverse=True):
        sized = []
        for page in by_width[width]:
            for band in page["bands"]:
                h = band.get("headline")
                if band["hero"] or not h:
                    if not band["hero"] and band.get("headings_seen"):
                        component_only += 1
                    continue
                where = f"{page['route']}@{width} {band['sel']} > {h['path']}"
                if h["px"] is None or not isinstance(h["px"], (int, float)):
                    errors.append(
                        f"UNRESOLVED {where}: font-size did not resolve to a "
                        f"number ({h['px']!r})"
                    )
                    continue
                sized.append((page["route"], band, h))
        counts["headlines"] += len(sized)
        if not sized:
            continue
        modal = _modal([h["px"] for _r, _b, h in sized])
        modal_by_width[width] = modal
        for route, band, h in sized:
            if abs(h["px"] - modal) <= SIZE_TOL:
                continue
            counts["headline_misses"] += 1
            key = (width, round(h["px"], 2))
            size_groups[key] += 1
            line = (f"HEADLINE-SIZE {route}@{width} {band['sel']} > {h['path']}: "
                    f"{h['px']:g}px, modal section headline at this width is "
                    f"{modal:g}px — text={h['text']!r}")
            size_example.setdefault(key, line)
            errors.append(line)

    # --- C19.2 one wrap point per prose band -------------------------------
    for width in sorted(by_width, reverse=True):
        for page in by_width[width]:
            for band in page["bands"]:
                h, b = band.get("headline"), band.get("body")
                if band["hero"] or not h or not b:
                    continue
                counts["prose_bands"] += 1
                where = f"{page['route']}@{width} {band['sel']}"
                hm, bm = h["measure"], b["measure"]
                bad = False
                for label, m, el in (("headline", hm, h), ("body", bm, b)):
                    if m.get("unresolved") or m.get("wrap") is None:
                        errors.append(
                            f"UNRESOLVED {where} {label} {el['path']}: "
                            f"{m.get('unresolved') or 'no wrap point'} — a wrap "
                            f"point that cannot be resolved is a failure, not a skip"
                        )
                        bad = True
                if bad:
                    continue
                if abs(hm["wrap"] - bm["wrap"]) <= MEASURE_TOL:
                    continue
                counts["measure_mismatches"] += 1
                mkey = (width, hm["raw"], bm["raw"])
                measure_groups[mkey] += 1
                errors.append(
                    f"MEASURE {where}: headline {h['path']} wraps at "
                    f"{hm['wrap']:.1f}px (max-width {hm['raw']}) but body "
                    f"{b['path']} wraps at {bm['wrap']:.1f}px (max-width "
                    f"{bm['raw']}) — one band, two wrap points; "
                    f"headline={h['text']!r}"
                )
                measure_example.setdefault(mkey, errors[-1])

    # An audit that measured nothing has proved nothing.
    if not load_failures and counts["headlines"] == 0:
        errors.append(
            "NO-HEADLINES: not one section headline resolved on any route — "
            "the audit measured nothing, which is a failure, not a pass"
        )

    summary = sorted(
        ({"width": k[0], "px": k[1], "occurrences": v, "example": size_example[k]}
         for k, v in size_groups.items()),
        key=lambda d: (-d["occurrences"], d["width"]),
    )
    counts["widths"] = len(by_width)
    # Bands that carry headings but no BAND-level headline — a card grid or a
    # nav table of contents standing alone. Reported so the exclusion can be
    # argued with rather than silently trusted.
    counts["bands_with_component_headings_only"] = component_only
    counts["modal_headline_px"] = {str(w): modal_by_width[w] for w in sorted(modal_by_width)}
    counts["offending_headline_sizes"] = summary
    counts["measure_mismatch_shapes"] = sorted(
        ({"width": k[0], "headline_max_width": k[1], "body_max_width": k[2],
          "occurrences": v, "example": measure_example[k]}
         for k, v in measure_groups.items()),
        key=lambda d: (-d["occurrences"], d["width"]),
    )
    return errors, counts


# --------------------------------------------------------------------------
# selftest — adversarial fixtures only, never a tracked source
# --------------------------------------------------------------------------
_BASE_CSS = """
*{box-sizing:border-box}
body{margin:0;font:16px/1.5 system-ui,sans-serif;background:#FAF7F0;color:#0E0E0C}
main>*{padding:40px 24px;display:block}
h1,h2{margin:0 0 12px;font-weight:700;line-height:1.03}
p{margin:0}
.eyebrow{font-size:12px;letter-spacing:.1em;text-transform:uppercase}
h2{font-size:60px;max-width:728px}
.blk>p{max-width:728px}
h1{font-size:60px;max-width:728px}
"""

# Consistent on both invariants. Three section headlines at one size, and in
# every band the headline and body wrap at the same point.
GOOD_CONSISTENT = """<!doctype html><meta charset=utf-8><title>consistent</title>
<style>%s</style>
<body><main>
<section class="blk blk--first"><h1>A page hero</h1><p>Hero standfirst.</p></section>
<section class="blk"><div class=eyebrow>One</div><h2>Working harder, still falling behind.</h2><p>Body copy on the same measure as the headline above it.</p></section>
<section class="blk"><div class=eyebrow>Two</div><h2>Point the tools at what keeps people alive.</h2><p>Body copy on the same measure as the headline above it.</p></section>
<section class="blk"><div class=eyebrow>Three</div><h2>We start where the money actually goes.</h2><p>Body copy on the same measure as the headline above it.</p></section>
</main></body>""" % _BASE_CSS

# THE IMPORTANT PASS. The hero is deliberately 96px against 60px section
# headlines, and its own headline/body wrap at deliberately different points.
# A tool that excluded heroes properly reports nothing here. A tool that simply
# ignores size differences would also report nothing — so this fixture is only
# meaningful alongside bad-headline-larger.html, which is the same 96px step
# applied to a band that is NOT the hero and MUST be caught.
GOOD_HERO_LARGER = """<!doctype html><meta charset=utf-8><title>hero larger</title>
<style>%s
.blk--first h1{font-size:96px;max-width:none}
.blk--first p{max-width:600px}
</style>
<body><main>
<section class="blk blk--first"><h1>The hero is allowed to be bigger.</h1><p>Hero standfirst wrapping at its own width.</p></section>
<section class="blk"><h2>Working harder, still falling behind.</h2><p>Body copy on the same measure as the headline above it.</p></section>
<section class="blk"><h2>Point the tools at what keeps people alive.</h2><p>Body copy on the same measure as the headline above it.</p></section>
<section class="blk"><h2>We start where the money actually goes.</h2><p>Body copy on the same measure as the headline above it.</p></section>
</main></body>""" % _BASE_CSS

# Component headings are not section headlines, and on this site they routinely
# come FIRST in their band — the policy routes open with a <nav> table of
# contents whose <h2> is 12px, and a card grid can be a band's entire content.
# Taking "the first <h2> in the band" naively reports both as section headlines
# at 12px and 28px against a 60px modal. Neither is one.
GOOD_COMPONENTS = """<!doctype html><meta charset=utf-8><title>components</title>
<style>%s
.cards{display:grid;grid-template-columns:1fr 1fr;gap:16px;max-width:1200px}
.card h2{font-size:28px;max-width:none}
.card p{max-width:none}
.toc h2{font-size:12px;max-width:none}
.toc p{max-width:none;font-size:13px}
</style>
<body><main>
<section class="blk blk--first"><h1>A page hero</h1><p>Hero standfirst.</p></section>
<section class="blk"><h2>Working harder, still falling behind.</h2><p>Body copy on the same measure as the headline above it.</p></section>
<section class="blk"><div class=eyebrow>The problem, with receipts</div>
  <div class=cards>
    <div class=card><h2>Card one</h2><p>Card body copy.</p></div>
    <div class=card><h2>Card two</h2><p>Card body copy.</p></div>
  </div></section>
<section class="blk"><nav class=toc><h2>Contents</h2><p>Jump to a section.</p></nav>
  <h2>Point the tools at what keeps people alive.</h2><p>Body copy on the same measure as the headline above it.</p></section>
<section class="blk"><h2>We start where the money actually goes.</h2><p>Body copy on the same measure as the headline above it.</p></section>
</main></body>""" % _BASE_CSS

# THE REAL DEFECT. One section headline renders smaller than its peers. Every
# band's headline and body share a measure, so the only thing wrong here is the
# size — if this fixture fails with a MEASURE error the audit caught it by
# accident, which is why the selftest checks the KIND of every failure.
BAD_HEADLINE_SMALLER = """<!doctype html><meta charset=utf-8><title>headline smaller</title>
<style>%s
.shrunk h2{font-size:40px}
</style>
<body><main>
<section class="blk blk--first"><h1>A page hero</h1><p>Hero standfirst.</p></section>
<section class="blk shrunk"><h2>Working harder, still falling behind.</h2><p>Body copy on the same measure as the headline above it.</p></section>
<section class="blk"><h2>Point the tools at what keeps people alive.</h2><p>Body copy on the same measure as the headline above it.</p></section>
<section class="blk"><h2>We start where the money actually goes.</h2><p>Body copy on the same measure as the headline above it.</p></section>
<section class="blk"><h2>Every figure here is a receipt.</h2><p>Body copy on the same measure as the headline above it.</p></section>
</main></body>""" % _BASE_CSS

# The same step in the other direction, on a band that is NOT the hero.
BAD_HEADLINE_LARGER = """<!doctype html><meta charset=utf-8><title>headline larger</title>
<style>%s
.grown h2{font-size:96px;max-width:728px}
</style>
<body><main>
<section class="blk blk--first"><h1>A page hero</h1><p>Hero standfirst.</p></section>
<section class="blk"><h2>Working harder, still falling behind.</h2><p>Body copy on the same measure as the headline above it.</p></section>
<section class="blk grown"><h2>Point the tools at it.</h2><p>Body copy on the same measure as the headline above it.</p></section>
<section class="blk"><h2>We start where the money actually goes.</h2><p>Body copy on the same measure as the headline above it.</p></section>
<section class="blk"><h2>Every figure here is a receipt.</h2><p>Body copy on the same measure as the headline above it.</p></section>
</main></body>""" % _BASE_CSS

# One band, two wrap points: the headline keeps a narrower measure than the
# body it introduces. This is the surviving-ch-measure shape — a headline still
# carrying an old per-band width while the body moved to the site measure.
BAD_MEASURE_SPLIT = """<!doctype html><meta charset=utf-8><title>measure split</title>
<style>%s
.split h2{max-width:480px}
</style>
<body><main>
<section class="blk blk--first"><h1>A page hero</h1><p>Hero standfirst.</p></section>
<section class="blk"><h2>Working harder, still falling behind.</h2><p>Body copy on the same measure as the headline above it.</p></section>
<section class="blk split"><h2>Point the tools at what keeps people alive.</h2><p>Body copy that wraps well past where the headline above it wraps.</p></section>
<section class="blk"><h2>We start where the money actually goes.</h2><p>Body copy on the same measure as the headline above it.</p></section>
</main></body>""" % _BASE_CSS

# The reverse: the headline is capped and the body is not capped at all, so the
# body runs to the full band width while the headline stops short.
BAD_MEASURE_BODY_NONE = """<!doctype html><meta charset=utf-8><title>body uncapped</title>
<style>%s
.loose>p{max-width:none}
</style>
<body><main>
<section class="blk blk--first"><h1>A page hero</h1><p>Hero standfirst.</p></section>
<section class="blk"><h2>Working harder, still falling behind.</h2><p>Body copy on the same measure as the headline above it.</p></section>
<section class="blk loose"><h2>Point the tools at what keeps people alive.</h2><p>Body copy with no measure at all, running the full width of the band while the headline above it stops at the site measure.</p></section>
<section class="blk"><h2>We start where the money actually goes.</h2><p>Body copy on the same measure as the headline above it.</p></section>
</main></body>""" % _BASE_CSS

# (name, markup or None, route, should_pass, expected error kinds)
# A None markup writes no file: the route is deliberately absent, and a route
# that will not load must be an ERROR rather than a quietly shorter run.
CASES = [
    ("good-consistent.html", GOOD_CONSISTENT, "/good-consistent.html", True, set()),
    ("good-hero-larger.html", GOOD_HERO_LARGER, "/good-hero-larger.html", True, set()),
    ("good-components.html", GOOD_COMPONENTS, "/good-components.html", True, set()),
    ("bad-headline-smaller.html", BAD_HEADLINE_SMALLER, "/bad-headline-smaller.html",
     False, {"HEADLINE-SIZE"}),
    ("bad-headline-larger.html", BAD_HEADLINE_LARGER, "/bad-headline-larger.html",
     False, {"HEADLINE-SIZE"}),
    ("bad-measure-split.html", BAD_MEASURE_SPLIT, "/bad-measure-split.html",
     False, {"MEASURE"}),
    ("bad-measure-body-uncapped.html", BAD_MEASURE_BODY_NONE,
     "/bad-measure-body-uncapped.html", False, {"MEASURE"}),
    ("(no file — route absent)", None, "/bad-route-that-does-not-exist.html",
     False, {"LOAD"}),
]

FIXTURE_README = """# type_audit fixtures

Inputs for `python3 tools/type_audit.py --selftest`. Nothing here is a site
source and the selftest never runs against `website/dist` or any tracked page.

Each `bad-*` file carries exactly ONE defect, and the selftest asserts both
that the audit fails on it and that it fails for the INTENDED reason — the
error kind is checked, not just the exit code. A fixture that failed for an
incidental reason would otherwise look like a working audit.

| fixture | must | why |
| --- | --- | --- |
| `good-consistent.html` | PASS | baseline: one headline size, one wrap point per band |
| `good-hero-larger.html` | PASS | the page hero is 96px against 60px section headlines, and its own headline and body wrap at different points. Heroes are excluded from both invariants, so this is clean. It is the counterpart to `bad-headline-larger.html`, which applies the same 96px step to a band that is not the hero and must be caught — together they prove the hero is *excluded* rather than size differences *ignored*. |
| `good-components.html` | PASS | component headings that come FIRST in their band: a card grid whose two `<h2>` are 28px and is a band's entire content, and a `<nav>` table of contents whose `<h2>` is 12px, ahead of the band's real headline. That ordering is the point — "the first `<h2>` in the band" reports both as section headlines against a 60px modal. Neither is one. |
| `bad-headline-smaller.html` | FAIL `HEADLINE-SIZE` | the real defect: "Working harder, still falling behind." renders smaller than its peers |
| `bad-headline-larger.html` | FAIL `HEADLINE-SIZE` | one section headline renders larger than its peers |
| `bad-measure-split.html` | FAIL `MEASURE` | a prose band whose headline keeps a narrower measure than its body |
| `bad-measure-body-uncapped.html` | FAIL `MEASURE` | a prose band whose body has no measure at all while the headline has one |
| (no file) | FAIL `LOAD` | a route that will not load is an error, never a skipped line |

The measure fixtures fail at 1440 and are clean at 390, which is correct: at
390 a 728px cap and no cap at all wrap at the same place, because the viewport
is the binding constraint. The audit judges the WRAP POINT — min(max-width,
containing block width) — not the declared max-width, so it does not invent a
defect at narrow widths.

No expected pixel value is written down anywhere in the audit or in these
fixtures. The expected headline size is the modal size of whatever the page
renders, and the expected body measure is whatever that band's own headline
wraps at, so the tool keeps working when the measure moves from 728px to
min(66vw, 960px) and when the headline scale moves with it.
"""


def write_fixtures():
    FIXTURES.mkdir(parents=True, exist_ok=True)
    for name, markup, _route, _ok, _kinds in CASES:
        if markup is None:
            continue
        (FIXTURES / name).write_text(markup, encoding="utf-8")
    (FIXTURES / "README.md").write_text(FIXTURE_README, encoding="utf-8")


def sample(errors, limit):
    """Truncate round-robin across error kinds.

    A flat head-of-list slice is a misleading sample: 184 MEASURE findings sat
    behind 50 HEADLINE-SIZE ones on the real site, so the first 40 lines showed
    one failure class and no trace of the other. Every kind present gets a
    share of the window, and `error_count` still carries the total.
    """
    if len(errors) <= limit:
        return errors
    buckets = collections.OrderedDict()
    for e in errors:
        buckets.setdefault(e.split(" ", 1)[0], []).append(e)
    out, order = [], list(buckets)
    while len(out) < limit and any(buckets[k] for k in order):
        for k in order:
            if not buckets[k]:
                continue
            out.append(buckets[k].pop(0))
            if len(out) >= limit:
                break
    return out


def kinds_of(errors):
    return {e.split(" ", 1)[0] for e in errors}


def selftest(port: int) -> int:
    write_fixtures()
    failures = []
    for name, _markup, route, should_pass, expect in CASES:
        errors, _counts = evaluate(probe(FIXTURES, [route], WIDTHS, port))
        passed = not errors
        got = kinds_of(errors)
        if passed != should_pass or (not should_pass and got != expect):
            failures.append({
                "fixture": name,
                "route": route,
                "expected": "PASS" if should_pass else "FAIL " + "/".join(sorted(expect)),
                "got": "PASS" if passed else "FAIL " + "/".join(sorted(got)),
                "sample": errors[:3],
            })
    print(json.dumps({"ok": not failures, "selftest_cases": len(CASES),
                      "failures": failures}, indent=2))
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="C19 type audit")
    ap.add_argument("--built", default=str(DEFAULT_BUILT))
    ap.add_argument("--routes", nargs="*")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--max-errors", type=int, default=40)
    args = ap.parse_args()

    if args.selftest:
        return selftest(args.port)

    built = pathlib.Path(args.built).resolve()
    if not built.is_dir():
        print(json.dumps({
            "ok": False,
            "errors": [f"no built directory at {built} — run `npm run build` in website/"],
            "counts": {"routes": 0, "headlines": 0, "headline_misses": 0,
                       "prose_bands": 0, "measure_mismatches": 0},
        }, indent=2))
        return 1
    routes = args.routes or routes_in(built)
    if not routes:
        print(json.dumps({
            "ok": False,
            "errors": [f"no routes found under {built}"],
            "counts": {"routes": 0, "headlines": 0, "headline_misses": 0,
                       "prose_bands": 0, "measure_mismatches": 0},
        }, indent=2))
        return 1
    errors, counts = evaluate(probe(built, routes, WIDTHS, args.port))
    print(json.dumps({
        "ok": not errors,
        "errors": sample(errors, args.max_errors),
        "error_count": len(errors),
        "counts": counts,
    }, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

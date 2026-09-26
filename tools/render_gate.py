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
WIDTHS = [1440, 1290, 390]
# Pixels may differ slightly wherever a responsive derivative is shown instead of
# the export's full-size original — same box, softer pixels. Layout differences
# are far larger than this.
TOLERANCE_PCT = float(os.environ.get("RENDER_TOLERANCE", "3.0"))
# Above this, a difference cannot be explained by the repo's copy being longer
# than the export's draft; it means the page is missing styling.
CONTENT_CEILING_PCT = float(os.environ.get("RENDER_CONTENT_CEILING", "35.0"))

# Named-section exemptions — the same pattern as the AA allowlist in shoot.cjs:
# a section whose difference is a KNOWN, reviewed content decision, which the
# ceiling cannot distinguish from missing styling because it only sees magnitude.
# Each entry is (page-path fragment, exact section label, one-line justification).
# Exemptions are per-section, never per-page: everything else on an exempted page
# is still measured, and every exemption actually exercised is listed in the run
# output, so none of this can rot unnoticed.
SECTION_EXEMPTIONS = [
    # ── Batch N ───────────────────────────────────────────────────────────
    ("news.html", "div.newswrap",
     "N1: /news/ is now a split landing. Both columns are first-class — each "
     "has its own head, its own founder-approved one-line intro, its own "
     "keyword filter and its own link to the full list — the combined intro "
     "sentence is gone, and the updates column renders the real dated items "
     "from _data/news.js instead of the export's three undated placeholders. "
     "Every Cost Watch card also gains the Reported label. That is most of the "
     "section's pixels by design, hence ~41%; the section's x and width still "
     "have to match the export and do, so the gate's geometry check is "
     "unaffected. CANVAS-SYNC items 72 and 73. " "C10 (Batch U): the list runs the container's full width (the 840px "
     "column cap is gone), cards are #FFF and the filter bar is a --cream-2 band. "
     "CANVAS-SYNC item 92."),
    ("projects/", "At a glance",
     "The dossier's reviewed prose is the content authority and runs far longer "
     "than the export's designed one-liner placeholder; structure is identical."),
    ("pledge-thanks", "Notable signers",
     "showCount:false is the intentional pre-launch state — founding-signer copy "
     "renders instead of a signer list, because there are no signers to invent."),
    # Approved changes the canvas has not made yet — each has a CANVAS-SYNC entry.
    ("index.html", "S5 Where we start",
     "Approved content change: the closing note is removed and the 'All fifteen "
     "sectors' button moved into its position. CANVAS-SYNC item 6."),
    ("sectors/", "Sector head",
     "Approved change: the hero illustration renders at double size, position and "
     "aspect unchanged. CANVAS-SYNC item 7."),
    ("projects.html", "How they help",
     "Approved change: 'Every project has to earn its cost claim.' is matched to "
     "the page's other section-heading size. CANVAS-SYNC item 8."),
    ("sectors/", "Related projects",
     "Approved change: the canvas Ledger component (.lg) replaces the previous "
     "prj-table list — same rows and content, new table markup. CANVAS-SYNC item 5."),
    ("receipts", "The register",
     "Approved changes: the band is the whiter cream, each title links its "
     "registered source URL, and the lead's figure count is rendered from the "
     "register instead of the export's stale 'Eleven'. CANVAS-SYNC items 10-12, 18."),
    ("receipts", "The rule",
     "Approved change: the ink headline the export omits below the eyebrow is "
     "added. CANVAS-SYNC item 9."),
    # UNP-82 content pass — founder-approved copy the canvas has not seen.
    ("receipts", "Worked example",
     "Approved change: the export's $X placeholder and its illustrative markers are "
     "replaced by a real register row (SRC-023), rendered from the register so the "
     "example cannot drift from the source it demonstrates. CANVAS-SYNC item 12."),
    ("receipts", "Confidence labels",
     "Approved copy: a one-line note that figure-confidence labels and "
     "sector/project status badges are deliberately separate systems. "
     "CANVAS-SYNC item 16."),
    ("receipts", "Corrections",
     "Approved copy: the launch-state no longer claims nothing has been published, "
     "which the 22-row register above it contradicted. CANVAS-SYNC item 17."),
    ("news", "Cost Watch",
     "Approved change: Cost Watch renders the register's own news-feed rows instead "
     "of a hand-curated list of third-party articles, so its length now tracks the "
     "register rather than the export's fixed three cards. CANVAS-SYNC item 19."),
    ("news", "News — title",
     "Approved copy: the intro band describes Cost Watch as sourced prices rather "
     "than curated external reporting. CANVAS-SYNC item 19."),
    ("sectors.html", "Sectors — title",
     "Approved copy: the intro band names all fifteen sectors and states the "
     "year-one order, replacing the one-line summary. CANVAS-SYNC item 20."),
    ("projects/", "Related sectors",
     "Approved copy: each project states its primary and secondary sectors and the "
     "role each plays, above the swatch row the export ships alone. The line is "
     "per-project and long on a 390px column. CANVAS-SYNC item 21."),
    # UNP-82 v2. These six carry no export counterpart under their label — the
    # movement page was rewritten section by section, and two /case/ sections are
    # new — so the gate has nothing to compare them against by design.
    ("movement", "What this is",
     "Approved rewrite (v2 (a) block 1): replaces the export's introband. The h1 "
     "stays in the titleband, so this block is eyebrow-less lead + body in the "
     "export's own .blk--first. CANVAS-SYNC item 24."),
    ("movement", "What we stand for",
     "Approved rewrite (v2 (a) block 2): replaces the export's 'How it reaches "
     "people' distribution-mechanics section. CANVAS-SYNC item 24."),
    ("movement", "What taking part means",
     "Approved rewrite (v2 (a) block 3): replaces the export's three "
     "Pledge/quiz/share-a-stat cards with the community and Assembly argument. "
     "CANVAS-SYNC item 24."),
    ("movement", "How to take part",
     "Approved rewrite (v2 (a) block 4): the export's .path grid with v2's three "
     "ways in; the button row is dropped because the coral CTA below already "
     "renders v2's two specified buttons. CANVAS-SYNC item 24."),
    ("case", "The mechanism",
     "Approved new section (v2 (b1)): the ownership-concentration argument, "
     "SRC-020 and SRC-024 through the register macro. No export counterpart. "
     "CANVAS-SYNC item 25."),
    ("case", "What living costs",
     "Content restoration, not a design change: the v4.3 re-derivation dropped "
     "this register-backed section when it swapped the essay page for the export's "
     "dashboard preview. Restored from origin/main @ 94d2481 with four figures "
     "(SRC-004, SRC-021, SRC-023, SRC-005). No export counterpart on this page. "
     "CANVAS-SYNC item 26."),
    # The export ships nine policy pages under `data-page="policies-<slug>"`,
    # but sections.css contains ZERO rules for that scope — the whole policy
    # layout is scoped to `data-page="privacy"` instead. So the export's own
    # policy pages render unstyled, and the reference these three sections are
    # measured against is itself broken. Our pages are styled (integration.css
    # re-scopes the export's block verbatim), so the diff is large and expected.
    # Retire all three the moment the canvas scopes the block to the policy
    # pages it already ships. CANVAS-SYNC item 29.
    ("policies/", "Policy header",
     "The export's own policy pages are unstyled: it ships them under "
     "`data-page=\"policies-<slug>\"` and defines no rules for that scope. Ours "
     "render the export's intended ink header. CANVAS-SYNC item 29."),
    ("policies/", "Policy body",
     "Same cause: the export's reference page has no policy layout at all, so "
     "the two-column TOC grid and body typography diverge wholesale. "
     "CANVAS-SYNC item 29."),
    ("policies/", "div.pol-wrap",
     "Same cause. This is the unlabelled wrapper around the TOC and body, which "
     "the gate names by selector rather than data-screen-label; exempting its "
     "two children does not cover it. CANVAS-SYNC item 29."),
    ("policies/", "TOC",
     "Same cause: the sticky contents rail does not exist on the export's own "
     "policy pages. CANVAS-SYNC item 29."),
    # 2026-09-12 visual sweep — approved divergences from the export.
    ("sectors/", "Evidence status",
     "Approved change: \"02 · Evidence status\" moved off ink onto cream2, because "
     "it sat on the same ink as \"01 · Scope\" above it and the two read as one "
     "slab. Inverting a full band's background is a near-total pixel change by "
     "definition, hence ~98%; structure and copy are untouched. The dashed "
     "empty-state card's border and body colour moved with it (both were "
     "ink-band-only). CANVAS-SYNC item 48."),
    ("assembly", "What supporters can do",
     "Approved change: the four participation-loop box interiors are cream2. The "
     "export paints them --cream on a --cream band, so they were the same colour "
     "as their background. Ink borders, grid gaps and coral numerals unchanged. "
     "CANVAS-SYNC item 50."),
    ("sectors.html", "Legend",
     "Approved change: the A1 divider rule moves the boundary from the legend's "
     "bottom edge to the band below it, so the legend loses its own 2px rule and "
     "gains a coral top rule. CANVAS-SYNC item 40."),
    # 2026-09-13 sweep 2 — approved divergences, each citing its CANVAS-SYNC row.
    ("sectors/", "Sources",
     "R5: sector \"05 · Sources\" adopts the reference table format — 2px ink "
     "frame, ink header row, ink row dividers — where the export ships a "
     "hairline list with no frame and no header. CANVAS-SYNC item 58."),
    ("index.html", "S2 The problem",
     "R3: the homepage's three statistics move from the retired `.fact` ink "
     "cards to the shared figure card. Not in the brief's \"Apply to\" list, but "
     "they used `.fact`, so retiring it required converting them. "
     "CANVAS-SYNC item 55."),
    ("receipts", "Keeping current",
     "P2 + R4: \"current\" is accented with --coral-on-ink, and the headline "
     "takes the shared prose scale. As with the CTA, a headline resize on a flat "
     "ink band moves nearly every pixel. CANVAS-SYNC items 56 and 57."),
    ("receipts", "Receipts CTA",
     "R4: this is a prose band, so its headline takes the shared "
     "clamp(34px, 4.2vw, 56px) and its body the 728px measure. On a flat coral "
     "band a headline resize moves nearly every pixel, hence the magnitude; "
     "structure, copy and colour are unchanged. CANVAS-SYNC item 57."),
    ("about", "Your say",
     "Approved copy: the slot vacated by the accessibility statement carries the "
     "member-voice section on the Assembly and the privacy commitment. There is no "
     "export counterpart. CANVAS-SYNC item 22."),
    # ── Sweep 3 (batches G and H) ─────────────────────────────────────────
    ("faq", "The basics",
     "H7: the /faq/ question sections move to --wheat. The export paints this "
     "band #F2EBE1 via .u-45, one of the two unnamed hexes CANVAS-SYNC item 74 "
     "had to work around; the template now drops .u-45 for the named repo class "
     "and the !important fight with it. Inverting a full band's fill changes "
     "nearly every pixel by definition, hence ~99.7%. Measured at 1440: the "
     "section box is 1440x447 in the export and 1440x451 built — same x, same "
     "width, +4px tall — so this is fill, not reflow and not a layout break. "
     "Sweep 3, batch H."),
    ("treasury", "Principles",
     "G1 + G2: the band takes the one headline scale and the 728px measure. "
     "Measured at 1440 the fill is unchanged (cream-2 dominant on both sides) "
     "while the section grows 533px to 754px and its ink coverage goes 1% to "
     "5% — a narrower measure wrapping more lines under a larger headline, "
     "which is the change itself, not a defect in it. Sweep 3, batch G."),
    ("faq", "Money",
     "H7, same change as \"The basics\": the question section moves to --wheat. "
     "Measured at 1440 the section box is 1440x303 in BOTH trees — identical "
     "geometry, zero reflow — and the dominant fill goes #F2EBE1 (95% of the "
     "band) to #E8B84A (95%). The diff is the fill and nothing else. "
     "Sweep 3, batch H."),
    ("faq", "Evidence",
     "H7, same change as \"The basics\": the question section moves to --wheat. "
     "Measured at 1440 the section box is 1440x303 in BOTH trees and the "
     "dominant fill goes #F2EBE1 to #E8B84A at 95% coverage either way. "
     "Sweep 3, batch H."),
    ("faq", "Governance",
     "H7, same change as \"The basics\": the question section moves to --wheat. "
     "Measured at 1440 the section box is 1440x303 in BOTH trees and the "
     "dominant fill goes #F2EBE1 to #E8B84A at 95% coverage either way. "
     "All four .faqsec--wheat sections are now named; there are exactly four. "
     "Sweep 3, batch H. C11 (Batch U): this, the last one, also takes the 48px "
     "that was the CTA's top margin as bottom padding, so its box is 48px taller "
     "(1440x351) and the strip below it is wheat. CANVAS-SYNC item 90."),
    ("index", "S4 What we run",
     "G1 + G2 at mobile: same palette on both sides, section height 919px to "
     "1006px at 390. The homepage's worst band is the one with the most running "
     "text, so it moves most when the headline scale and the measure change. "
     "Sweep 3, batch G."),
    # ── Batch U part 2 (2026-09-25) ───────────────────────────────────────
    ("index.html", "S1 Hero",
     "E2: the hero's second line, \"Uncost the cost of living.\", renders "
     "--coral #D64A1E — the export's own `.u-50` value and the same shade as "
     "\"not billionaires richer\" on the first line. C1's per-band list had "
     "overridden it to --coral-deep. CANVAS-SYNC item 79. C5: the second line "
     "sits .35em lower (27px at 1440, 13px at 390) and the intro breaks after "
     "\"…price tag.\", so the hero is taller than the export's by those "
     "amounts plus one intro line. CANVAS-SYNC item 85."),
    ("join", "div.privacyline",
     "C9: the \"We won't sell your data…\" strip moves from the export's --wheat "
     "to --cream-2, matching the tier cards above it. Same box, fill only. "
     "CANVAS-SYNC item 89."),
    ("sectors/", "Worked example",
     "C17 (Batch U part 1): each sector renders its own worked example, and the "
     "four measurement sectors (Healthcare, Care, Education, Safety) stop after "
     "step 3 with their stop note — content the export's Food-only section does "
     "not have. C14: the six-step list gains its complete 2px ink frame and 24px "
     "cell padding. CANVAS-SYNC item 93."),
    ("assembly", "Standing rules",
     "C14: the standing-rules list gains a complete 2px cream frame (its "
     "dividers are cream on this ink band) and 24px cell padding. CANVAS-SYNC "
     "item 93."),
    ("treasury", "section.",
     "C14: the four KPI cards become one gap grid inside a complete 2px ink "
     "frame drawn by the band itself; the per-card 4px coral tops and "
     "border-right dividers go. CANVAS-SYNC item 93."),
    ("error-404", "div.e-wrap",
     "C14: the split panel gains its complete 2px ink frame; its top edge sits "
     "under the header's own line, so one line shows. CANVAS-SYNC item 93."),
    ("later/", "div.sys",
     "F1: each 'on the way' band holds exactly one card, so its heading is the "
     "band's section headline and takes the one headline scale (56px at 1440, "
     "34px at 390) instead of the card's 40/28px. F2 then puts its body on the "
     "same wrap point. CANVAS-SYNC item 95."),
    ("pledge-thanks", "Share",
     "F1: \"Now make it count double.\" heads its own band and takes the one "
     "section-headline scale (was 22px). F2 aligns its body. CANVAS-SYNC item 95."),
    ("contact", "Contact",
     "formsOpen is false (CHECKLIST H: no page may ship a live form), so the "
     "export's Name/Email/Phone/Message form is replaced by the forms-closed "
     "partial — 'The contact form opens at launch… email works' — restated by "
     "tools/post_patch_pages.py. Measured 35.73% at 390 on the unchanged "
     "2e44290 build as well: it was the gate's one standing FAIL, not a change "
     "from this batch. The email, social and GitHub blocks above it match."),
    ("assembly", "Preview + interest",
     "V22: the PLANNED TOOL chip is removed from the \"A look ahead\" header "
     "row and the ink button reads \"How the Assembly works\". F2 had already "
     "let the headline column fill the row. CANVAS-SYNC item 109."),
    ("contribute", "Volunteer roles",
     "V24: \"Useful roles, right now.\" gains a \"Volunteer now\" ink button to "
     "/contact/ after its closing note — one button row taller than the export. "
     "CANVAS-SYNC item 110."),
]


def exemption_for(page_rel: str, label: str):
    for frag, sect, why in SECTION_EXEMPTIONS:
        if frag in page_rel and sect == label:
            return why
    return None

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


def _mask(img, boxes):
    """Paint allowlisted regions flat so an approved difference cannot register."""
    for x, y, w, h in boxes:
        if w > 0 and h > 0:
            img.paste((255, 0, 255), (max(0, x), max(0, y), min(img.width, x + w), min(img.height, y + h)))
    return img


def _score(a, b):
    d = ImageChops.difference(a, b).convert("L").histogram()
    total = sum(d) or 1
    return round(100.0 * sum(d[8:]) / total, 3)


def pct_diff(a_path, b_path, page_rel=""):
    """Worst per-section difference, each section compared against its own origin.

    Comparing whole pages is misleading: one content-driven height change — the
    repo's longer dossier text wrapping to a second line, say — shifts every
    section below it and turns a local text difference into a 20% whole-page
    diff. Sections are therefore cropped to their own top and compared over
    their overlapping height, so reflow stays local and a real layout break
    still shows up as a large number in its own band.
    """
    a, b = Image.open(a_path).convert("RGB"), Image.open(b_path).convert("RGB")
    ma = json.loads(pathlib.Path(str(a_path).replace(".png", ".json")).read_text())
    mb = json.loads(pathlib.Path(str(b_path).replace(".png", ".json")).read_text())
    _mask(a, ma.get("masks", [])); _mask(b, mb.get("masks", []))
    sa = {s["label"]: s["box"] for s in ma.get("sections", [])}
    sb = {s["label"]: s["box"] for s in mb.get("sections", [])}
    if not sa:
        h = min(a.height, b.height)
        return _score(a.crop((0, 0, a.width, h)), b.crop((0, 0, a.width, h))), "-", False, []
    common = [k for k in sa if k in sb]
    # A section present in one tree and not the other is a CONTENT difference,
    # not a layout break, when it is an optional block: a sector with no related
    # projects omits that section, and the verify page ships one state instead
    # of the export's three-state preview switcher. What must not differ is the
    # geometry of the sections both pages do render.
    only_a, only_b = [k for k in sa if k not in sb], [k for k in sb if k not in sa]
    # Geometry first. A section that sits at the same x and the same width in
    # both trees is laid out identically; only its height can move, and height
    # moves when text reflows. That is the line between a LAYOUT break (which
    # must fail) and a CONTENT difference (the repo's reviewed copy being longer
    # than the export's draft), which is expected and permitted.
    geometry_ok = all(sa[k][0] == sb[k][0] and sa[k][2] == sb[k][2] for k in common)
    worst, worst_i, exempted = 0.0, "-", []
    for i in common:
        why = exemption_for(page_rel, i)
        if why:
            exempted.append((i, why))
            continue
        abox, bbox = sa[i], sb[i]
        h = min(abox[3], bbox[3])
        if h < 4:
            continue
        w = min(a.width, b.width)
        ca = a.crop((0, abox[1], w, min(a.height, abox[1] + h)))
        cb = b.crop((0, bbox[1], w, min(b.height, bbox[1] + h)))
        if ca.size != cb.size:
            hh = min(ca.height, cb.height)
            ca, cb = ca.crop((0, 0, w, hh)), cb.crop((0, 0, w, hh))
        pct = _score(ca, cb)
        if pct > worst:
            worst, worst_i = pct, i
    return worst, worst_i, (geometry_ok and bool(common)), exempted

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
        rows, failed, exemptions_used = [], 0, {}
        for (rel, route), broute in zip(pages, built_routes):
            ename = shot_name("/" + rel)
            bname = shot_name(broute)
            worst, worst_where, geom_ok = 0.0, "-", True
            for w in WIDTHS:
                ep, bp = shots / "export" / f"{ename}@{w}.png", shots / "built" / f"{bname}@{w}.png"
                if not (ep.exists() and bp.exists()):
                    worst = 100.0; break
                pct, where, geom, ex = pct_diff(ep, bp, rel)
                geom_ok = geom_ok and geom
                for label, why in ex:
                    exemptions_used.setdefault((rel, label), why)
                if pct > worst:
                    worst, worst_where = pct, f"{w}px section {where}"
            # CONTENT has a ceiling. Section geometry only compares x and width,
            # so styling lost INSIDE a section — a dropped utility class taking a
            # max-width, colour or margin with it — leaves x/width intact and used
            # to pass as "copy differs". A v4.3 trial rendered the homepage 48%
            # different and sector pages 100% different and still read CONTENT.
            # Beyond the ceiling the difference is too large to be reflow,
            # whatever the geometry says.
            if not geom_ok:
                verdict = "FAIL"          # sections differ in x/width: layout break
            elif worst <= TOLERANCE_PCT:
                verdict = "PASS"
            elif worst > CONTENT_CEILING_PCT:
                verdict = "FAIL"          # too big to be copy: styling is missing
            else:
                verdict = "CONTENT"       # same layout, text reflow only
            failed += 1 if verdict == "FAIL" else 0
            rows.append((rel, worst, verdict, worst_where))
        rows.sort(key=lambda r: r[1])
        print(f"{'page':44} {'worst diff %':>12}  {'verdict':4}  worst band")
        for rel, worst, verdict, where in rows:
            print(f"{rel:44} {worst:>12}  {verdict:7}  {where}")
        npass = sum(1 for r in rows if r[2] == "PASS")
        ncontent = sum(1 for r in rows if r[2] == "CONTENT")
        if exemptions_used:
            print("\nexempted sections (reviewed content decisions, not measured):")
            for (rel, label), why in sorted(exemptions_used.items()):
                print(f"  {rel} :: {label}")
                print(f"      {why}")
        print(f"\n{npass} PASS  {ncontent} CONTENT (layout matches, copy differs)  {failed} FAIL"
              f"   tolerance {TOLERANCE_PCT}%, content ceiling {CONTENT_CEILING_PCT}%, {len(exemptions_used)} section exemptions at {WIDTHS}")
        print(f"screenshots: {shots}")
        return 1 if failed else 0
    finally:
        s1.shutdown(); s2.shutdown()

if __name__ == "__main__":
    raise SystemExit(main())

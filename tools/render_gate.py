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
    ("receipts", "Receipts — title",
     "Approved copy: the hero gains the one-line publishing rule under the H1, in "
     "the band's own ink treatment. CANVAS-SYNC item 15."),
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
    ("about", "Your say",
     "Approved copy: the slot vacated by the accessibility statement carries the "
     "member-voice section on the Assembly and the privacy commitment. There is no "
     "export counterpart. CANVAS-SYNC item 22."),
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

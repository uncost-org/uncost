#!/usr/bin/env python3
"""Structural diff: built dist/ vs the design export's pages/*.html.

The export is the authoritative design — it is what renders correctly in the
canvas. The CSS is byte-identical, so any layout difference is a MARKUP
difference. This compares the element skeleton (tag + classes + layout-bearing
attributes) and ignores text, which is the dynamic-slot layer.
"""
import os, re, sys, json, pathlib
from collections import Counter

EXPORT = pathlib.Path(os.environ.get("UNCOST_DESIGN_SOURCE", "../uncost-private/design-source"))
if EXPORT.name != "pages":
    EXPORT = EXPORT / "pages"
DIST = pathlib.Path("website/dist")

# Export page -> built route. Routes are reconciled to the repository's
# contractual URLs (docs/DESIGN_IMPORT_RUNBOOK.md), and policy slugs are the
# repo's, so the mapping is explicit rather than derived from the filename.
POLICY = {
    "code-of-conduct": "code-of-conduct",
    "conflict-of-interest": "conflict-of-interest",
    "political-activity": "political-activity",
    "responsible-ai": "responsible-ai",
    "assembly-governance": "assembly-governance-participation",
    "financial-controls": "financial-controls-donation",
    "in-kind-gifts": "in-kind-gift-acceptance",
    "safeguarding": "safeguarding-pilot-safety",
    # corrections-source-integrity has no repo counterpart at POL-010; the repo
    # reserves it as POL-011 with its own slug.
    "corrections-source-integrity": "corrections-and-source-integrity",
}
LATER = {"case-dashboard": "case/dashboard", "case-tracker": "case/tracker",
         "community": "community", "events": "news/events", "press": "press",
         "quiz": "quiz", "share": "share"}
FLAT = {"index": "", "error-404": "404.html", "pledge-check-email": "pledge/check-email",
        "pledge-resend": "pledge/resent", "pledge-thanks": "pledge/thanks",
        "pledge-verify": "pledge/verify"}

def route_for(rel: str):
    stem = rel[:-len(".html")]
    if stem.startswith("policies/"):
        s = POLICY.get(stem.split("/", 1)[1])
        return f"policies/{s}/index.html" if s else None
    if stem.startswith("later/"):
        return f"{LATER[stem.split('/',1)[1]]}/index.html"
    if stem.startswith(("sectors/", "projects/")):
        return f"{stem}/index.html"
    if stem in FLAT:
        v = FLAT[stem]
        return "index.html" if v == "" else (v if v.endswith(".html") else f"{v}/index.html")
    return f"{stem}/index.html"

# Layout-bearing attributes. data-* hooks and roles matter (JS + a11y); href
# targets are checked separately since routes are reconciled.
KEEP_ATTRS = ("role", "data-panel", "data-i", "data-acc", "data-form", "data-source",
              "data-screen-label", "data-drawer-open", "data-drawer-close", "data-search",
              "data-search-close", "data-updates-form", "aria-expanded", "aria-haspopup",
              "colspan", "type", "id")
VOID = {"img", "br", "hr", "input", "meta", "link", "source", "i", "use", "path",
        "circle", "rect", "line", "polyline", "polygon", "ellipse", "stop"}

def skeleton(html: str):
    """Sequence of <tag.class.class[attr=val]> tokens. Text is ignored."""
    out = []
    # The image pipeline emits <picture><source…><img>; the export writes <img>.
    html = re.sub(r"</?picture[^>]*>", "", html)
    html = re.sub(r"<source[^>]*>", "", html)
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    for m in re.finditer(r"<(/?)([a-zA-Z][\w-]*)((?:\"[^\"]*\"|'[^']*'|[^>\"'])*)/?>", html):
        close, tag, attrs = m.group(1), m.group(2).lower(), m.group(3)
        if close:
            if tag not in VOID:
                out.append(f"</{tag}>")
            continue
        cls = re.search(r'class="([^"]*)"', attrs)
        classes = ".".join(sorted(cls.group(1).split())) if cls else ""
        keep = []
        for a in KEEP_ATTRS:
            mm = re.search(rf'\b{a}="([^"]*)"', attrs)
            if mm:
                v = mm.group(1).replace("&amp;", "&")
                if a in ("data-source", "id"):
                    v = re.sub(r"SRC-\d{3}", "SRC-###", v)
                keep.append(f"{a}={v}")
            elif re.search(rf'\b{a}(?=[\s>])', attrs):
                keep.append(a)
        # INTENDED additions, excluded from the comparison:
        #  data-source — the content audit's citation mechanism; a figure counts
        #    as cited only inside an element carrying a registered SRC id.
        #  data-form   — CHECKLIST H requires the hooks present and unrenamed,
        #    including in the disabled state the export hardcodes without them.
        keep = [k for k in keep if not k.startswith(("data-source", "data-form"))]
        tok = f"<{tag}" + (f".{classes}" if classes else "") + (f"[{','.join(keep)}]" if keep else "") + ">"
        out.append(tok)
        if tag in VOID:
            continue
    return out

def main_of(html: str):
    m = re.search(r'<main[^>]*>(.*?)</main>', html, re.S)
    return m.group(1) if m else None

def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    rows, missing = [], []
    for p in sorted(EXPORT.rglob("*.html")):
        rel = str(p.relative_to(EXPORT))
        route = route_for(rel)
        if route is None:
            continue
        built = DIST / route
        if not built.exists():
            missing.append((rel, route)); continue
        if only and only not in rel:
            continue
        e_main, b_main = main_of(p.read_text(encoding="utf-8")), main_of(built.read_text(encoding="utf-8"))
        if e_main is None or b_main is None:
            rows.append((rel, route, -1, -1, "NO <main>")); continue
        a, b = skeleton(e_main), skeleton(b_main)
        import difflib
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        ratio = sm.ratio()
        delta = sum(max(i2-i1, j2-j1) for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != "equal")
        rows.append((rel, route, len(a), len(b), f"{ratio:.3f}", delta))
    rows.sort(key=lambda r: float(r[4]) if isinstance(r[4], str) and r[4][0].isdigit() else -1)
    print(f"{'export page':44} {'exp':>5} {'built':>5} {'match':>6} {'delta':>6}")
    for rel, route, na, nb, ratio, *rest in rows:
        d = rest[0] if rest else "?"
        print(f"{rel:44} {na:5} {nb:5} {str(ratio):>6} {d:>6}")
    exact = sum(1 for r in rows if r[4] == "1.000")
    print(f"\npages compared: {len(rows)}   node-for-node identical: {exact}   diverging: {len(rows)-exact}")
    if missing:
        print(f"\nno built route for: {missing}")

if __name__ == "__main__":
    main()

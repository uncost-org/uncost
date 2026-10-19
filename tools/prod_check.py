#!/usr/bin/env python3
"""Production build check — what a public soft launch would serve (CHG-004).

Run it on a build made with NO UNCOST_* environment variables and NO
SITE_ORIGIN, so every feature flag in website/src/_data/features.js is at its
default and the origin is https://uncost.org:

    (cd website && npm run build)            # with UNCOST_* and SITE_ORIGIN unset
    python3 tools/prod_check.py              # website/dist
    python3 tools/prod_check.py --built DIR
    python3 tools/prod_check.py --selftest   # adversarial fixtures

Checks — each an ERROR, never a skipped line (standing rule 1):

  1. ROBOTS: robots.txt names "User-agent: *", allows crawling (no
     "Disallow: /"), and its Sitemap line is exactly
     https://uncost.org/sitemap.xml;
  2. HEADER: _headers carries no X-Robots-Tag. That header is the preview
     posture, which .github/workflows/preview-deploy.yml adds to previews
     only;
  3. NOINDEX: the pages with <meta name="robots" content="noindex"> are
     exactly the expected set — the unlinked placeholders, the two error
     pages and, while UNCOST_FORMS_OPEN is not "on", the four pledge-flow
     pages (nothing to act on with forms off) — none of them is in
     sitemap.xml, and every other page is;
  4. ORIGIN: every canonical, og:url, og:image and twitter:image URL, and
     every sitemap <loc>, starts with https://uncost.org/;
  5. FORM: no <form>, <textarea> or <select> renders, and every <input> is a
     type="search" box (the site search and the keyword filters);
  6. THIRD-PARTY: no asset URL (src, srcset, <link href>, url(), poster) points
     off uncost.org — the rule scripts/audit_website.py enforces in built
     mode, repeated here as a count.

Exit 0 when ok, 1 on any error.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
DIST = ROOT / "website" / "dist"
ORIGIN = "https://uncost.org"
# The six unlinked "on the way" placeholders (CANVAS-SYNC 162) and the two
# error pages. Anything else carrying noindex, or any of these losing it, fails.
EXPECTED_NOINDEX = ["/404.html", "/500.html", "/press/", "/quiz/", "/share/", "/community/",
                    "/case/dashboard/", "/case/tracker/"]
# Pledge-flow pages: noindex while formsOpen is off (formFlow: true in their
# front matter; layouts/base.njk). The build reads UNCOST_FORMS_OPEN, so the
# check reads the same variable from the environment it runs in.
FORM_FLOW_PAGES = ["/pledge/check-email/", "/pledge/verify/", "/pledge/resent/", "/pledge/thanks/"]


def expected_noindex_default(env=os.environ):
    exp = list(EXPECTED_NOINDEX)
    if env.get("UNCOST_FORMS_OPEN") != "on":
        exp += FORM_FLOW_PAGES
    return exp

NOINDEX_RE = re.compile(r'<meta\s+name="robots"\s+content="[^"]*\bnoindex\b', re.I)
META_URL_RE = re.compile(
    r'<link\s+rel="canonical"\s+href="([^"]*)"|<meta\s+(?:property|name)="(?:og:url|og:image|twitter:image)"\s+content="([^"]*)"',
    re.I)
TAG_RE = re.compile(r"<(form|textarea|select|input)\b([^>]*)>", re.I)
ASSET_RE = re.compile(
    r"""(?:\bsrc\s*=|\bsrcset\s*=|\bposter\s*=|url\(\s*)["'(]?\s*(https?://[^/\s"'<>)]+)"""
    # <link> fetches unless it only names a URL (canonical, alternate feed).
    r"""|<link\b(?![^>]*\brel\s*=\s*["']?(?:canonical|alternate)\b)[^>]*?\bhref\s*=\s*["']?(https?://[^/\s"'<>)]+)""",
    re.I)
DATA_URI_RE = re.compile(r"data:[^\"')\s]+")


def route_of(rel: str) -> str:
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[: -len("index.html")]
    return "/" + rel


def check(built: pathlib.Path, expected_noindex=None) -> dict:
    if expected_noindex is None:
        expected_noindex = expected_noindex_default()
    errors, facts = [], {}

    robots_path = built / "robots.txt"
    robots = robots_path.read_text(encoding="utf-8") if robots_path.exists() else ""
    lines = [ln.strip() for ln in robots.splitlines()]
    sitemap_lines = [ln for ln in lines if ln.lower().startswith("sitemap:")]
    facts["robots"] = lines
    if not robots:
        errors.append("ROBOTS: robots.txt is missing or empty")
    if "User-agent: *" not in lines:
        errors.append("ROBOTS: no 'User-agent: *' line")
    if any(re.fullmatch(r"disallow:\s*/", ln, re.I) for ln in lines):
        errors.append("ROBOTS: 'Disallow: /' blocks crawling")
    if sitemap_lines != [f"Sitemap: {ORIGIN}/sitemap.xml"]:
        errors.append(f"ROBOTS: sitemap line is {sitemap_lines}, not 'Sitemap: {ORIGIN}/sitemap.xml'")

    headers_path = built / "_headers"
    headers = headers_path.read_text(encoding="utf-8") if headers_path.exists() else ""
    tagged = [ln.strip() for ln in headers.splitlines() if "x-robots-tag" in ln.lower()]
    facts["x_robots_tag_lines"] = tagged
    if tagged:
        errors.append(f"HEADER: _headers sets {tagged}")

    sitemap_path = built / "sitemap.xml"
    sitemap = sitemap_path.read_text(encoding="utf-8") if sitemap_path.exists() else ""
    locs = re.findall(r"<loc>([^<]+)</loc>", sitemap)
    in_sitemap = {loc[len(ORIGIN):] for loc in locs if loc.startswith(ORIGIN + "/")}
    facts["sitemap_urls"] = len(locs)
    if not locs:
        errors.append("NOINDEX: sitemap.xml is missing or lists no URLs")
    for loc in locs:
        if not loc.startswith(ORIGIN + "/"):
            errors.append(f"ORIGIN: sitemap <loc> {loc}")

    pages = sorted(built.rglob("*.html"))
    noindex, forms, inputs, third, meta_urls = [], [], [], [], 0
    for path in pages:
        rel = str(path.relative_to(built))
        route = route_of(rel)
        html = path.read_text(encoding="utf-8")
        if NOINDEX_RE.search(html):
            noindex.append(route)
        elif route not in in_sitemap:
            errors.append(f"NOINDEX: {route} is indexable but not in sitemap.xml")
        for m in META_URL_RE.finditer(html):
            url = m.group(1) or m.group(2)
            meta_urls += 1
            if not url.startswith(ORIGIN + "/"):
                errors.append(f"ORIGIN: {route} has {url}")
        for m in TAG_RE.finditer(html):
            tag, attrs = m.group(1).lower(), m.group(2)
            if tag == "input" and re.search(r'\btype\s*=\s*"search"', attrs, re.I):
                inputs.append(route)
                continue
            forms.append(f"{route} <{tag}{attrs[:60]}>")
        for line in html.splitlines():
            for m in ASSET_RE.finditer(DATA_URI_RE.sub("", line)):
                host = (m.group(1) or m.group(2)).split("//", 1)[-1].lower()
                if host != "uncost.org" and not host.endswith(".uncost.org"):
                    third.append(f"{route} {host}")
    for path in sorted(list(built.rglob("*.css")) + list(built.rglob("*.js"))):
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            for m in ASSET_RE.finditer(DATA_URI_RE.sub("", line)):
                host = (m.group(1) or m.group(2)).split("//", 1)[-1].lower()
                if host != "uncost.org" and not host.endswith(".uncost.org"):
                    third.append(f"{path.relative_to(built)} {host}")

    if sorted(noindex) != sorted(expected_noindex):
        errors.append(f"NOINDEX: noindex pages are {sorted(noindex)}, expected {sorted(expected_noindex)}")
    for route in noindex:
        if route in in_sitemap:
            errors.append(f"NOINDEX: {route} carries noindex but is in sitemap.xml")
    for f in forms:
        errors.append(f"FORM: {f}")
    for t in third:
        errors.append(f"THIRD-PARTY: {t}")
    facts.update({"pages": len(pages), "noindex": sorted(noindex), "meta_urls_checked": meta_urls,
                  "search_inputs": len(inputs), "search_input_pages": sorted(set(inputs)) if len(set(inputs)) < 8 else f"{len(set(inputs))} pages",
                  "forms_or_other_inputs": len(forms), "third_party_assets": len(third)})
    return {"ok": not errors, "errors": errors, "facts": facts}


def page(body: str, route_path: str, noindex: bool = False, canonical: str | None = None) -> str:
    canonical = canonical or ORIGIN + route_path
    robots = '<meta name="robots" content="noindex">' if noindex else ""
    return (f'<!doctype html><html><head>{robots}<link rel="canonical" href="{canonical}">'
            f'<meta property="og:url" content="{canonical}"></head><body>{body}</body></html>')


def selftest() -> int:
    def site(tmp: pathlib.Path, **over) -> None:
        files = {
            "robots.txt": f"User-agent: *\nAllow: /\nSitemap: {ORIGIN}/sitemap.xml\n",
            "_headers": "/*\n  X-Content-Type-Options: nosniff\n",
            "sitemap.xml": f"<urlset><url><loc>{ORIGIN}/</loc></url><url><loc>{ORIGIN}/about/</loc></url></urlset>",
            "index.html": page('<input id="site-search" type="search">', "/"),
            "about/index.html": page("<p>About</p>", "/about/"),
            "press/index.html": page("<p>Soon</p>", "/press/", noindex=True),
        }
        files.update(over)
        for rel, text in files.items():
            if text is None:
                continue
            p = tmp / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")

    sm = f"<urlset><url><loc>{ORIGIN}/</loc></url><url><loc>{ORIGIN}/about/</loc></url></urlset>"
    cases = {
        "good": ({}, set()),
        "disallow": ({"robots.txt": f"User-agent: *\nDisallow: /\nSitemap: {ORIGIN}/sitemap.xml\n"}, {"ROBOTS"}),
        "preview-sitemap": ({"robots.txt": "User-agent: *\nAllow: /\nSitemap: https://x.pages.dev/sitemap.xml\n"}, {"ROBOTS"}),
        "x-robots": ({"_headers": "/*\n  X-Robots-Tag: noindex, nofollow\n"}, {"HEADER"}),
        "real-page-noindex": ({"about/index.html": page("<p>About</p>", "/about/", noindex=True)}, {"NOINDEX"}),
        # A pledge-flow page that lost its noindex while forms are off.
        "form-flow-indexed": ({"pledge/thanks/index.html": page("<p>Thanks</p>", "/pledge/thanks/"),
                               "sitemap.xml": sm.replace("</urlset>", f"<url><loc>{ORIGIN}/pledge/thanks/</loc></url></urlset>")},
                              {"NOINDEX"}),
        "placeholder-in-sitemap": ({"sitemap.xml": sm.replace("</urlset>", f"<url><loc>{ORIGIN}/press/</loc></url></urlset>")},
                                   {"NOINDEX"}),
        "preview-canonical": ({"about/index.html": page("<p>About</p>", "/about/", canonical="https://abc.pages.dev/about/")},
                              {"ORIGIN"}),
        "form": ({"about/index.html": page('<form action="/x"><input type="email"></form>', "/about/")}, {"FORM"}),
        "third-party": ({"about/index.html": page('<script src="https://cdn.example.com/a.js"></script>', "/about/")},
                        {"THIRD-PARTY"}),
    }
    failures = []
    for name, (over, want) in cases.items():
        with tempfile.TemporaryDirectory() as tmp:
            site(pathlib.Path(tmp), **over)
            got = check(pathlib.Path(tmp), expected_noindex=["/press/"] + (
                ["/pledge/thanks/"] if name == "form-flow-indexed" else []))
        kinds = {e.split(":")[0] for e in got["errors"]}
        if kinds != want:
            failures.append({"case": name, "expected": sorted(want), "got": sorted(kinds), "errors": got["errors"][:4]})
    print(json.dumps({"ok": not failures, "selftest_cases": len(cases), "failures": failures}, indent=2))
    return 0 if not failures else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--built", default=str(DIST))
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    result = check(pathlib.Path(a.built))
    print(json.dumps(result, indent=1))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Link crawl — which built routes does no other page link to?

Every HTML file in the built site is a route. Every <a href> on every page is
read, resolved against the page's own URL, and reduced to a route. A route is
ORPHANED when no page other than itself links to it. Each orphan is reported
with whether sitemap.xml lists it and whether the page carries a robots
noindex, because an unlinked page that is still in the sitemap is reachable
only by search.

STANDING RULE (docs/DESIGN_IMPORT_RUNBOOK.md, 2026-09-19): this fails on
"I don't know". An internal href that resolves to no built route is an ERROR,
not a skipped link, and so is a page that will not parse. External links
(another host, mailto:, tel:, javascript:, data:) are classified as external,
never silently dropped.

    python3 tools/link_crawl.py                      # website/dist
    python3 tools/link_crawl.py --built DIR
    python3 tools/link_crawl.py --expect /404.html /press/   # exit 1 unless the
                                                            # orphan set is exactly this
    python3 tools/link_crawl.py --selftest

Exit 0 when ok, 1 on any error or an --expect mismatch.
"""
from __future__ import annotations

import argparse
import html.parser
import json
import pathlib
import re
import sys
import tempfile
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[1]
DIST = ROOT / "website" / "dist"
EXTERNAL_SCHEMES = ("mailto:", "tel:", "javascript:", "data:", "sms:")


class Page(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hrefs, self.noindex = [], False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and a.get("href") is not None:
            self.hrefs.append(a["href"])
        if tag == "meta" and (a.get("name") or "").lower() == "robots" and "noindex" in (a.get("content") or "").lower():
            self.noindex = True


def route_of(rel: str) -> str:
    """dist-relative file path -> the URL it is served at."""
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[: -len("index.html")]
    return "/" + rel


def resolve(href: str, base_route: str, routes: set[str]):
    """-> ("external", None) | ("self-anchor", None) | ("internal", route) | ("dangling", path)."""
    h = href.strip()
    if not h or h.startswith("#"):
        return "self-anchor", None
    if h.lower().startswith(EXTERNAL_SCHEMES):
        return "external", None
    u = urllib.parse.urlsplit(urllib.parse.urljoin("https://site.invalid" + base_route, h))
    if u.netloc != "site.invalid":
        return "external", None
    path = urllib.parse.unquote(u.path) or "/"
    for cand in (path, path + ("" if path.endswith("/") else "/"), path.rstrip("/") + ".html"):
        if cand in routes:
            return "internal", cand
    # Static assets (PDF, feeds, images) are files, not pages; they are routes
    # only when they are HTML. A link to an existing non-HTML file is fine.
    return "dangling", path


def crawl(dist: pathlib.Path):
    errors, pages = [], {}
    for p in sorted(dist.rglob("*.html")):
        rel = p.relative_to(dist).as_posix()
        parser = Page()
        try:
            parser.feed(p.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001 — any parse failure is an error, by rule
            errors.append({"kind": "unparseable", "page": route_of(rel), "detail": str(e)})
            continue
        pages[route_of(rel)] = parser
    routes = set(pages)
    inbound = {r: set() for r in routes}
    for route, parser in pages.items():
        for href in parser.hrefs:
            kind, target = resolve(href, route, routes)
            if kind == "internal":
                if target != route:
                    inbound[target].add(route)
            elif kind == "dangling":
                if not (dist / target.lstrip("/")).is_file():
                    errors.append({"kind": "dangling", "page": route, "href": href})
    sitemap = set()
    sm = dist / "sitemap.xml"
    if sm.exists():
        for loc in re.findall(r"<loc>([^<]+)</loc>", sm.read_text(encoding="utf-8")):
            sitemap.add(urllib.parse.urlsplit(loc.strip()).path or "/")
    orphans = [{"route": r, "in_sitemap": r in sitemap, "noindex": pages[r].noindex}
               for r in sorted(routes) if not inbound[r]]
    return {"routes": len(routes), "orphans": orphans, "errors": errors}


def selftest() -> int:
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="uncost-crawl-"))
    def page(rel, body, head=""):
        f = tmp / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(f"<!doctype html><html><head>{head}</head><body>{body}</body></html>", encoding="utf-8")
    page("index.html", '<a href="/a/">a</a><a href="b/#x">b</a><a href="mailto:x@y">m</a><a href="https://example.org/">e</a>')
    page("a/index.html", '<a href="/">home</a><a href="/a/">self</a><a href="/file.pdf">pdf</a>')
    page("b/index.html", '<a href="../a/">a</a>')
    page("lonely/index.html", '<a href="/lonely/">self only</a>', '<meta name="robots" content="noindex">')
    page("404.html", "")
    (tmp / "file.pdf").write_bytes(b"%PDF")
    (tmp / "sitemap.xml").write_text("<urlset><url><loc>https://x.org/lonely/</loc></url></urlset>", encoding="utf-8")
    cases = []
    r = crawl(tmp)
    got = [(o["route"], o["in_sitemap"], o["noindex"]) for o in r["orphans"]]
    cases.append(("orphans = 404 + self-linked noindex page", got == [("/404.html", False, False), ("/lonely/", True, True)], got))
    cases.append(("external, mailto, anchors and existing files are not errors", r["errors"] == [], r["errors"]))
    page("b/index.html", '<a href="../a/">a</a><a href="/nowhere/">x</a>')
    r = crawl(tmp)
    cases.append(("a link to no route is an error", [e["kind"] for e in r["errors"]] == ["dangling"], r["errors"]))
    failures = [{"case": n, "got": g} for n, ok, g in cases if not ok]
    print(json.dumps({"ok": not failures, "selftest_cases": len(cases), "failures": failures}, indent=2))
    return 0 if not failures else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--built", default=str(DIST))
    ap.add_argument("--expect", nargs="*", help="the exact orphan routes expected")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    r = crawl(pathlib.Path(a.built))
    ok = not r["errors"]
    if a.expect is not None:
        got = {o["route"] for o in r["orphans"]}
        want = set(a.expect)
        r["expect"] = {"missing": sorted(want - got), "unexpected": sorted(got - want)}
        ok = ok and got == want
    r["ok"] = ok
    print(json.dumps(r, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

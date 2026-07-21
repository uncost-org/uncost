#!/usr/bin/env python3
"""Built-site quality gates: internal links/anchors and zero third-party requests.

Runs against a built output directory (default website/dist). Fails closed:

- LINK / ANCHOR: every internal hyperlink, and every fetched-resource URL,
  must resolve to a file that exists in the built output; a "path#id" or
  same-page "#id" anchor must resolve to an element id present in the target
  document.
- THIRD_PARTY: no automatically-fetched resource (stylesheet, script, image,
  media, iframe, preload, font, CSS url()/@import) may point at an external
  origin. The site must make zero third-party network requests at runtime.
  User-navigable <a href="https://..."> links are allowed (a click is not a
  runtime request) but are reported for visibility.

HTML validity and heading-order are enforced separately by html-validate
(see website/.htmlvalidate.json and the CI step). This script is stdlib-only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urldefrag, urlparse

# <link rel> values that cause the browser to fetch a subresource. Other rel
# values (canonical, alternate, author, license, next/prev) are metadata or
# navigation and are never auto-fetched, so an absolute self-origin URL there
# is not a third-party request.
FETCHING_LINK_RELS = {
    "stylesheet", "preload", "prefetch", "modulepreload", "manifest",
    "icon", "shortcut icon", "apple-touch-icon", "mask-icon", "prerender",
}

# Resource-fetching attributes: the browser requests these automatically.
# <link> is handled separately (rel-aware) in the parser.
FETCH_ATTRS = {
    "script": ["src"],
    "img": ["src", "srcset"],
    "source": ["src", "srcset"],
    "audio": ["src"],
    "video": ["src", "poster"],
    "track": ["src"],
    "iframe": ["src"],
    "embed": ["src"],
    "object": ["data"],
    "input": ["src"],              # type=image submit buttons fetch src
    "use": ["href", "xlink:href"], # SVG sprite references
    "image": ["href", "xlink:href"],  # SVG raster <image> element
}
NAV_ATTRS = {"a": ["href"], "area": ["href"]}
IGNORED_SCHEMES = ("mailto:", "tel:", "data:", "javascript:", "sms:")


def is_external(url: str) -> bool:
    u = url.strip()
    if u.startswith("//"):
        return True
    scheme = urlparse(u).scheme
    return scheme in ("http", "https")


def split_srcset(value: str) -> List[str]:
    # Candidates are separated by comma-then-whitespace. Splitting on bare
    # commas would tear apart a data: URI (its base64/percent body contains
    # commas not followed by whitespace), so use the whitespace-anchored
    # separator. A candidate is "URL [descriptor]"; take the URL.
    parts = []
    for candidate in re.split(r",\s+", value.strip()):
        token = candidate.strip().split()
        if token:
            parts.append(token[0])
    return parts


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: Set[str] = set()
        # (tag, attr, url, line, is_fetch)
        self.refs: List[Tuple[str, str, str, int, bool]] = []
        self.inline_css: List[Tuple[int, str]] = []
        self._in_style = False

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        line = self.getpos()[0]
        attrs_dict = {k: (v or "") for k, v in attrs}
        if "id" in attrs_dict and attrs_dict["id"]:
            self.ids.add(attrs_dict["id"])
        if "style" in attrs_dict:
            self.inline_css.append((line, attrs_dict["style"]))
        if tag == "style":
            self._in_style = True
        if tag == "link":
            href = attrs_dict.get("href", "").strip()
            if href:
                rels = attrs_dict.get("rel", "").lower().split()
                # A link is a fetched subresource only for fetching rels;
                # canonical/alternate/etc. are metadata (self-referential
                # absolute URLs are expected and are not requests).
                is_fetch = any(rel in FETCHING_LINK_RELS for rel in rels)
                self.refs.append(("link", "href", href, line, is_fetch))
        for group, is_fetch in ((FETCH_ATTRS, True), (NAV_ATTRS, False)):
            for attr in group.get(tag, []):
                raw = attrs_dict.get(attr, "").strip()
                if not raw:
                    continue
                urls = split_srcset(raw) if attr == "srcset" else [raw]
                for url in urls:
                    self.refs.append((tag, attr, url, line, is_fetch))

    def handle_endtag(self, tag: str) -> None:
        if tag == "style":
            self._in_style = False

    def handle_data(self, data: str) -> None:
        if self._in_style:
            self.inline_css.append((self.getpos()[0], data))


CSS_URL = re.compile(r"url\(\s*['\"]?([^'\")]+)['\"]?\s*\)")
CSS_IMPORT = re.compile(r"@import\s+['\"]([^'\"]+)['\"]")


def resolve_internal(url: str, page: Path, root: Path) -> Optional[Path]:
    path_part, _ = urldefrag(url)
    if not path_part:
        return page  # pure "#id" — same document
    if path_part.startswith("/"):
        target = root / path_part.lstrip("/")
    else:
        target = (page.parent / path_part).resolve()
    # A directory URL resolves to its index.html.
    if url.endswith("/") or (target.is_dir()):
        target = target / "index.html"
    return target


def check_css_urls(
    css_text: str, line: int, page: Path, root: Path, findings: List[str], rel: str
) -> None:
    for match in list(CSS_URL.finditer(css_text)) + list(CSS_IMPORT.finditer(css_text)):
        url = match.group(1).strip()
        if url.startswith("data:"):
            continue
        if is_external(url):
            findings.append(f"THIRD_PARTY:{rel}:{line}:css-url:{url}")
            continue
        target = resolve_internal(url, page, root)
        if target is not None and not target.exists():
            findings.append(f"BROKEN_LINK:{rel}:{line}:css-url:{url}")


def audit(root: Path) -> Tuple[List[str], Dict[str, int]]:
    findings: List[str] = []
    external_nav = 0
    html_files = sorted(root.rglob("*.html")) + sorted(root.rglob("*.htm"))
    # id sets are needed cross-file for anchor resolution; parse once, cache.
    parsers: Dict[Path, PageParser] = {}
    for path in html_files:
        parser = PageParser()
        parser.feed(path.read_text(encoding="utf-8"))
        parsers[path] = parser

    for path in html_files:
        rel = str(path.relative_to(root))
        parser = parsers[path]
        for tag, attr, url, line, is_fetch in parser.refs:
            if not url or url.startswith(IGNORED_SCHEMES):
                continue
            if url.startswith("#"):
                frag = url[1:]
                if frag and frag not in parser.ids:
                    findings.append(f"BROKEN_ANCHOR:{rel}:{line}:{url}")
                continue
            if is_external(url):
                if is_fetch:
                    findings.append(f"THIRD_PARTY:{rel}:{line}:{tag}.{attr}:{url}")
                else:
                    external_nav += 1
                continue
            target = resolve_internal(url, path, root)
            if target is None:
                continue
            try:
                target.relative_to(root)
            except ValueError:
                findings.append(f"LINK_ESCAPE:{rel}:{line}:{url}")
                continue
            if not target.exists():
                findings.append(f"BROKEN_LINK:{rel}:{line}:{tag}.{attr}:{url}")
                continue
            # Anchor into another document.
            _, frag = urldefrag(url)
            if frag and target.suffix in (".html", ".htm"):
                target_parser = parsers.get(target)
                if target_parser is None:
                    target_parser = PageParser()
                    target_parser.feed(target.read_text(encoding="utf-8"))
                    parsers[target] = target_parser
                if frag not in target_parser.ids:
                    findings.append(f"BROKEN_ANCHOR:{rel}:{line}:{url}")
        for line, css in parser.inline_css:
            check_css_urls(css, line, path, root, findings, rel)

    # Any passthrough/generated CSS in the output is also a fetched resource.
    for css_path in sorted(root.rglob("*.css")):
        rel = str(css_path.relative_to(root))
        check_css_urls(css_path.read_text(encoding="utf-8"), 0, css_path, root, findings, rel)

    return findings, {"html_files": len(html_files), "external_nav_links": external_nav}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("built", nargs="?", default="website/dist", help="built output directory")
    args = parser.parse_args()
    root = Path(args.built).resolve()
    if not root.is_dir():
        raise SystemExit(f"built directory not found: {root}")

    findings, counts = audit(root)
    annotate = __import__("os").environ.get("GITHUB_ACTIONS") == "true"
    for finding in findings:
        print(f"FAIL {finding}")
        if annotate:
            code, *rest = finding.split(":", 3)
            loc = rest[0] if rest else ""
            line = rest[1] if len(rest) > 1 else "1"
            print(f"::error file=website/dist/{loc},line={line},title=site-quality:{code}::{finding}")
    print(json.dumps({"ok": not findings, "fail_count": len(findings), **counts}))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())

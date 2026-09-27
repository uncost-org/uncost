#!/usr/bin/env python3
"""V13 feed check — the RSS feeds are valid, and read as a page in a browser.

The site publishes two RSS 2.0 feeds, /news/feed.xml and
/news/cost-watch/feed.xml. Each carries an <?xml-stylesheet?> line directly
after its XML declaration, naming /news/feed.xsl, so a person who opens a feed
URL in a browser gets a readable page instead of a raw XML tree. Feed readers
ignore that line. This tool checks both halves: that a reader still gets a
valid feed, and that a browser still gets a page.

For every feed, in the built output:

  XML           the file is well-formed XML
  ROOT          the root is <rss version="2.0"> with one <channel>
  CHANNEL       the channel has a non-empty title, link and description
  SELF          atom:link rel="self" is an absolute URL ending in the feed's
                own path — a copied template pointing at the other feed is the
                failure this catches
  ITEM-CONTENT  every item has a title or a description
  ITEM-GUID     every item has a non-empty guid
  DATE          every item's pubDate (and the channel's lastBuildDate, when
                present) is an RFC-822 date: it matches the grammar, names a
                real calendar date, and its day of week is that date's day
  PI            exactly one xml-stylesheet PI, in the prolog, type="text/xsl",
                whose href is a same-origin path to a file in the built output
  XSL           that file is well-formed XSLT 1.0 (browsers run nothing
                later), compiles, and never uses disable-output-escaping
  TOOL          xsltproc is on PATH and finished — without it nothing below
                can be checked, and that is a failure, not a skip
  RENDER        xsltproc transforms the feed with that stylesheet, cleanly, and
                the output carries every item title (or, for an untitled item,
                its description) and the feed's own URL
  CSP           the output obeys the site's CSP (src/_headers: style-src
                'self', script-src 'self'): no <style>, no style="", no inline
                <script>, no on* handler, no javascript: URL
  ASSET         every stylesheet or script the output loads is a same-origin
                path to a file that exists in the built output
  MISSING       an expected feed is not in the built output at all

Every error string starts with its kind. The selftest asserts the KIND of each
failure, not just that one happened: a fixture that fails for an incidental
reason would otherwise look like a working check.

STANDING RULE (docs/DESIGN_IMPORT_RUNBOOK.md, 2026-09-19): this check fails on
"I don't know". A feed it cannot find, parse, or render is an error, never a
skipped line; a later step is only left out when an earlier one has already
failed the same feed.

    python3 tools/feed_check.py [--built DIR]
    python3 tools/feed_check.py --selftest

Prints JSON {ok, errors, counts}. Exit 0 when ok.
"""
from __future__ import annotations

import argparse
import datetime as dt
import email.utils
import html.parser
import json
import pathlib
import re
import shutil
import subprocess
import sys
import urllib.parse
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_BUILT = ROOT / "website" / "dist"
FIXTURES = ROOT / "tools" / "fixtures" / "feed"

# The feeds the site must publish. Any OTHER <rss> file found in the built
# output is checked too, so a new feed cannot ship unchecked.
FEEDS = ("news/feed.xml", "news/cost-watch/feed.xml")

XSLT_NS = "http://www.w3.org/1999/XSL/Transform"
ATOM_NS = "http://www.w3.org/2005/Atom"
XSLTPROC_TIMEOUT = 60

# RFC-822 section 5 as the RSS 2.0 profile uses it. The year is four digits
# (RSS Best Practices Profile); the single-letter military zones are refused
# except Z, since RFC-1123 notes they were specified with the wrong sign.
RFC822 = re.compile(
    r"^(?:(?P<dow>Mon|Tue|Wed|Thu|Fri|Sat|Sun), )?"
    r"(?P<day>\d{1,2}) (?P<mon>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (?P<year>\d{4}) "
    r"(?P<hh>\d{2}):(?P<mm>\d{2})(?::(?P<ss>\d{2}))? "
    r"(?P<zone>[+-]\d{4}|UT|GMT|EST|EDT|CST|CDT|MST|MDT|PST|PDT|Z)$"
)
DOW = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
PSEUDO_ATTR = re.compile(r"""([A-Za-z_][\w.-]*)\s*=\s*(?:"([^"]*)"|'([^']*)')""")


def norm(s) -> str:
    return " ".join((s or "").split())


def rfc822_problem(value: str) -> str | None:
    """None when `value` is a real RFC-822 date, else what is wrong with it."""
    v = norm(value)
    if not v:
        return "empty"
    m = RFC822.match(v)
    if not m:
        return f"{v!r} is not an RFC-822 date (e.g. 'Sat, 01 Aug 2026 09:00:00 +0700')"
    try:
        stamp = email.utils.parsedate_to_datetime(v)
    except (TypeError, ValueError) as e:
        return f"{v!r} matches the grammar but is not a real date ({e})"
    if stamp is None:
        return f"{v!r} could not be parsed"
    if m.group("dow") and DOW[stamp.weekday()] != m.group("dow"):
        return f"{v!r} says {m.group('dow')} but that date is a {DOW[stamp.weekday()]}"
    return None


def resolve_in(built: pathlib.Path, base_rel: str, href: str) -> tuple[pathlib.Path | None, str | None]:
    """Resolve a same-origin href the way a browser would, inside `built`."""
    parts = urllib.parse.urlsplit(href)
    if parts.scheme or parts.netloc:
        return None, f"{href!r} is not a same-origin path"
    path = urllib.parse.unquote(parts.path)
    if not path:
        return None, f"{href!r} has no path"
    base = pathlib.PurePosixPath("/" + base_rel).parent
    joined = pathlib.PurePosixPath(path) if path.startswith("/") else base / path
    target = (built / str(joined).lstrip("/")).resolve()
    root = built.resolve()
    if target != root and root not in target.parents:
        return None, f"{href!r} resolves outside the built output"
    return target, None


# --------------------------------------------------------------------------
# the rendered page
# --------------------------------------------------------------------------
class PageScan(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text: list[str] = []
        self.csp: list[str] = []
        self.loads: list[str] = []      # hrefs/srcs of stylesheets and scripts
        self.titles = 0

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "style":
            self.csp.append("inline <style> element")
        if "style" in a:
            self.csp.append(f"style=\"\" attribute on <{tag}>")
        for k in a:
            if k.startswith("on"):
                self.csp.append(f"{k}= handler on <{tag}>")
        for k in ("href", "src", "action"):
            if a.get(k, "").strip().lower().startswith("javascript:"):
                self.csp.append(f"javascript: URL in <{tag} {k}>")
        if tag == "script":
            if a.get("src"):
                self.loads.append(a["src"])
            else:
                self.csp.append("inline <script>")
        if tag == "link" and "stylesheet" in a.get("rel", "").lower().split():
            self.loads.append(a.get("href", ""))
        if tag == "title":
            self.titles += 1

    def handle_data(self, data):
        self.text.append(data)


def find_xsltproc() -> str | None:
    return shutil.which("xsltproc")


def check_xsl(xsl: pathlib.Path) -> list[str]:
    """Static checks on the stylesheet file; the transform compiles it later."""
    try:
        tree = ET.parse(xsl)
    except ET.ParseError as e:
        return [f"is not well-formed XML ({e})"]
    root = tree.getroot()
    if root.tag not in (f"{{{XSLT_NS}}}stylesheet", f"{{{XSLT_NS}}}transform"):
        return [f"root is <{root.tag}>, not xsl:stylesheet in the XSLT namespace"]
    problems = []
    if root.get("version") != "1.0":
        problems.append(f"version={root.get('version')!r}; browsers run XSLT 1.0 only")
    for el in root.iter():
        if el.get("disable-output-escaping", "").strip() == "yes":
            problems.append("uses disable-output-escaping=\"yes\" — feed text would be written as "
                            "markup (and Firefox does not implement it)")
            break
    return problems


def check_feed(built: pathlib.Path, rel: str, xsltproc: str | None) -> tuple[list[str], dict]:
    errors: list[str] = []
    stats = {"items": 0, "titles_rendered": 0, "stylesheet": None}
    path = built / rel

    def err(kind: str, msg: str):
        errors.append(f"{kind} {rel}: {msg}")

    if not path.is_file():
        err("MISSING", "not in the built output")
        return errors, stats
    data = path.read_bytes()

    # XML -------------------------------------------------------------------
    try:
        root = ET.fromstring(data)
        pull = ET.XMLPullParser(events=("start", "pi"))
        pull.feed(data)
        pull.close()
    except ET.ParseError as e:
        err("XML", f"not well-formed ({e})")
        return errors, stats
    pis, started = [], False
    for event, el in pull.read_events():
        if event == "start":
            started = True
        elif event == "pi" and (el.text or "").split(None, 1)[0:1] == ["xml-stylesheet"]:
            pis.append((el.text, started))

    # ROOT / CHANNEL / SELF --------------------------------------------------
    if root.tag != "rss" or root.get("version") != "2.0":
        err("ROOT", f"root is <{root.tag} version={root.get('version')!r}>, not <rss version=\"2.0\">")
    channels = root.findall("channel")
    if len(channels) != 1:
        err("ROOT", f"{len(channels)} <channel> elements, expected exactly 1")
        return errors, stats
    ch = channels[0]
    for field in ("title", "link", "description"):
        if not norm(ch.findtext(field)):
            err("CHANNEL", f"channel has no {field}")
    selfs = [l for l in ch.findall(f"{{{ATOM_NS}}}link") if l.get("rel") == "self"]
    self_href = selfs[0].get("href", "") if selfs else ""
    if len(selfs) != 1:
        err("SELF", f"{len(selfs)} atom:link rel=\"self\" elements, expected exactly 1")
    elif not re.match(r"^https?://[^/]+/", self_href) or not self_href.endswith("/" + rel):
        err("SELF", f"atom:link rel=\"self\" href {self_href!r} is not an absolute URL ending in /{rel}")
    if ch.find("lastBuildDate") is not None:
        p = rfc822_problem(ch.findtext("lastBuildDate"))
        if p:
            err("DATE", f"lastBuildDate: {p}")

    # ITEMS -----------------------------------------------------------------
    items = ch.findall("item")
    stats["items"] = len(items)
    expect_text = []
    for i, it in enumerate(items, 1):
        title, desc = norm(it.findtext("title")), norm(it.findtext("description"))
        if not title and not desc:
            err("ITEM-CONTENT", f"item {i} has neither a title nor a description")
        else:
            expect_text.append(title or desc)
        if not norm(it.findtext("guid")):
            err("ITEM-GUID", f"item {i} ({title[:60]!r}) has no guid")
        p = rfc822_problem(it.findtext("pubDate") or "")
        if p:
            err("DATE", f"item {i} pubDate: {p}")

    # PI --------------------------------------------------------------------
    if not pis:
        err("PI", "no <?xml-stylesheet?> processing instruction — a browser shows raw XML")
        return errors, stats
    if len(pis) > 1:
        err("PI", f"{len(pis)} xml-stylesheet PIs, expected exactly 1")
        return errors, stats
    pi_text, after_root = pis[0]
    if after_root:
        err("PI", "xml-stylesheet PI comes after the root element; browsers only apply one in the prolog")
        return errors, stats
    attrs = {m.group(1): (m.group(2) if m.group(2) is not None else m.group(3))
             for m in PSEUDO_ATTR.finditer(pi_text)}
    if attrs.get("type") != "text/xsl":
        err("PI", f"xml-stylesheet type={attrs.get('type')!r}, expected 'text/xsl'")
        return errors, stats
    href = attrs.get("href", "")
    xsl, why = resolve_in(built, rel, href)
    if why:
        err("PI", f"xml-stylesheet href: {why}")
        return errors, stats
    if not xsl.is_file():
        err("PI", f"xml-stylesheet href {href!r} is not a file in the built output")
        return errors, stats
    stats["stylesheet"] = "/" + xsl.relative_to(built.resolve()).as_posix()

    # XSL -------------------------------------------------------------------
    problems = check_xsl(xsl)
    if problems:
        for p in problems:
            err("XSL", f"{stats['stylesheet']} {p}")
        return errors, stats

    # RENDER ----------------------------------------------------------------
    if not xsltproc:
        err("TOOL", "xsltproc is not on PATH, so the browser view cannot be rendered or checked")
        return errors, stats
    try:
        proc = subprocess.run([xsltproc, "--nonet", "--novalid", "--nowrite", "--nomkdir",
                               str(xsl), str(path)],
                              capture_output=True, timeout=XSLTPROC_TIMEOUT)
    except subprocess.TimeoutExpired:
        err("TOOL", f"xsltproc did not finish in {XSLTPROC_TIMEOUT}s")
        return errors, stats
    stderr = proc.stderr.decode("utf-8", "replace").strip()
    if proc.returncode in (4, 5):   # xsltproc: stylesheet failed to parse / has errors
        err("XSL", f"{stats['stylesheet']} does not compile (xsltproc exit {proc.returncode}): {stderr[:300]}")
        return errors, stats
    if proc.returncode != 0 or stderr:
        err("RENDER", f"xsltproc exit {proc.returncode}: {stderr[:300] or '(no message)'}")
        return errors, stats
    page = PageScan()
    try:
        page.feed(proc.stdout.decode("utf-8"))
        page.close()
    except UnicodeDecodeError as e:
        err("RENDER", f"transform output is not UTF-8 ({e})")
        return errors, stats
    text = norm(" ".join(page.text))
    if not page.titles:
        err("RENDER", "the rendered page has no <title>")
    for t in expect_text:
        if t in text:
            stats["titles_rendered"] += 1
        else:
            err("RENDER", f"the rendered page does not show the item {t[:80]!r}")
    if self_href and self_href not in text:
        err("RENDER", f"the rendered page does not show the feed's own URL {self_href!r}")
    for c in page.csp:
        err("CSP", c)
    for load in page.loads:
        # The transformed page's URL is the FEED's, so its relative links
        # resolve against the feed, not against the stylesheet file.
        target, why = resolve_in(built, rel, load) if load else (None, "empty href")
        if why:
            err("ASSET", f"the rendered page loads {load!r}: {why}")
        elif not target.is_file():
            err("ASSET", f"the rendered page loads {load!r}, which is not in the built output")
    return errors, stats


def feeds_in(built: pathlib.Path) -> list[str]:
    found = set(FEEDS)
    for p in sorted(built.rglob("*.xml")):
        try:
            head = p.read_bytes()[:4096].decode("utf-8", "replace")
        except OSError:
            continue
        if re.search(r"<rss[\s>]", head):
            found.add(p.relative_to(built).as_posix())
    return sorted(found)


def evaluate(built: pathlib.Path, feeds, xsltproc: str | None) -> tuple[list[str], dict]:
    errors: list[str] = []
    counts = {"feeds": 0, "items": 0, "titles_rendered": 0, "stylesheets": []}
    for rel in feeds:
        e, s = check_feed(built, rel, xsltproc)
        errors += e
        counts["feeds"] += 1
        counts["items"] += s["items"]
        counts["titles_rendered"] += s["titles_rendered"]
        if s["stylesheet"] and s["stylesheet"] not in counts["stylesheets"]:
            counts["stylesheets"].append(s["stylesheet"])
    counts["problems"] = len(errors)
    return errors, counts


def kinds_of(errors) -> set[str]:
    return {e.split(" ", 1)[0] for e in errors}


# --------------------------------------------------------------------------
# selftest — fixtures only, never website/dist
# --------------------------------------------------------------------------
GOOD_XSL = """<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:atom="http://www.w3.org/2005/Atom" exclude-result-prefixes="atom">
  <xsl:output method="html" encoding="utf-8" doctype-system="about:legacy-compat"/>
  <xsl:template match="/">
    <html lang="en"><head><title><xsl:value-of select="rss/channel/title"/></title>
    <link rel="stylesheet" href="/css/feed.css"/></head>
    <body><h1><xsl:value-of select="rss/channel/title"/></h1>
    <p><code><xsl:value-of select="rss/channel/atom:link[@rel='self']/@href"/></code></p>
    <ol><xsl:for-each select="rss/channel/item"><li>
      <h2><xsl:value-of select="title"/></h2>
      <p><xsl:value-of select="description"/></p>
    </li></xsl:for-each></ol>
    </body></html>
  </xsl:template>
</xsl:stylesheet>
"""
ITEM_LOOP = GOOD_XSL[GOOD_XSL.index("<ol>"):GOOD_XSL.index("</ol>") + len("</ol>")]
XSL_FILES = {
    "feed.xsl": GOOD_XSL,
    # A real, compiling stylesheet that simply never prints the items.
    "drops-items.xsl": GOOD_XSL.replace(ITEM_LOOP, "<p>Nothing to see.</p>"),
    # style="" on the output: fine in xsltproc, blocked by the site's CSP.
    "inline-style.xsl": GOOD_XSL.replace("<body>", '<body style="margin:0">'),
    # Links a stylesheet that is not in the built output.
    "missing-css.xsl": GOOD_XSL.replace("/css/feed.css", "/css/not-there.css"),
    "doe.xsl": GOOD_XSL.replace('<xsl:value-of select="description"/>',
                                '<xsl:value-of select="description" disable-output-escaping="yes"/>'),
    "v2.xsl": GOOD_XSL.replace('version="1.0" xmlns:xsl', 'version="2.0" xmlns:xsl'),
    # Well-formed XML that is not a stylesheet at all.
    "not-xslt.xsl": '<?xml version="1.0" encoding="utf-8"?>\n<html><body><p>Not a stylesheet.</p></body></html>\n',
}
CSS_FILES = {"css/feed.css": "body { margin: 0; }\n"}

GOOD_ITEM = ("<item><title>First item</title><link>https://example.test/a</link>"
             "<guid isPermaLink=\"false\">fx-1</guid><pubDate>Sat, 01 Aug 2026 09:00:00 +0700</pubDate>"
             "<description><![CDATA[First body.]]></description></item>")
SECOND_ITEM = ("<item><title>Second &amp; last</title><link>https://example.test/b</link>"
               "<guid isPermaLink=\"false\">fx-2</guid><pubDate>Wed, 12 Aug 2026 09:00:00 +0700</pubDate>"
               "<description><![CDATA[Second body.]]></description></item>")


def feed_xml(name, *, pi='<?xml-stylesheet type="text/xsl" href="/feed.xsl"?>\n', version="2.0",
             description="<description>A fixture feed.</description>", self_path=None,
             items=(GOOD_ITEM, SECOND_ITEM), pi_inside=""):
    return ('<?xml version="1.0" encoding="utf-8"?>\n' + pi +
            f'<rss version="{version}" xmlns:atom="http://www.w3.org/2005/Atom">{pi_inside}\n'
            "  <channel>\n    <title>Fixture feed</title>\n    <link>https://example.test/</link>\n"
            f'    <atom:link href="https://example.test/{self_path or name}" rel="self" '
            'type="application/rss+xml" />\n'
            f"    {description}\n    <lastBuildDate>Wed, 12 Aug 2026 09:00:00 +0700</lastBuildDate>\n    " +
            "\n    ".join(items) + "\n  </channel>\n</rss>\n")


def pi_to(href):
    return f'<?xml-stylesheet type="text/xsl" href="{href}"?>\n'


# (feed file, content or None, should_pass, expected error kinds, xsltproc available)
# None writes no file: the feed is deliberately absent.
CASES = [
    ("good.xml", feed_xml("good.xml"), True, set(), True),
    # An untitled item, and a pubDate with no day of week: both legal RSS. The
    # check must not reject what the spec allows.
    ("good-untitled-item.xml", feed_xml("good-untitled-item.xml", items=(
        GOOD_ITEM,
        "<item><guid isPermaLink=\"false\">fx-3</guid><pubDate>12 Aug 2026 09:00 GMT</pubDate>"
        "<description>An item with a description and no title.</description></item>")), True, set(), True),
    ("bad-missing-guid.xml", feed_xml("bad-missing-guid.xml", items=(
        GOOD_ITEM, SECOND_ITEM.replace('<guid isPermaLink="false">fx-2</guid>', ""))),
     False, {"ITEM-GUID"}, True),
    ("bad-pubdate.xml", feed_xml("bad-pubdate.xml", items=(
        GOOD_ITEM, SECOND_ITEM.replace("Wed, 12 Aug 2026 09:00:00 +0700", "2026-08-12T09:00:00+07:00"))),
     False, {"DATE"}, True),
    # Grammatical, and a real date — but 12 August 2026 is a Wednesday. A
    # lenient parser takes this without complaint.
    ("bad-pubdate-weekday.xml", feed_xml("bad-pubdate-weekday.xml", items=(
        GOOD_ITEM, SECOND_ITEM.replace("Wed, 12 Aug", "Fri, 12 Aug"))),
     False, {"DATE"}, True),
    ("bad-pi-missing-xsl.xml", feed_xml("bad-pi-missing-xsl.xml", pi=pi_to("/missing.xsl")),
     False, {"PI"}, True),
    ("bad-malformed.xml", feed_xml("bad-malformed.xml").replace("</channel>", "</chanel>"),
     False, {"XML"}, True),
    ("bad-no-pi.xml", feed_xml("bad-no-pi.xml", pi=""), False, {"PI"}, True),
    # Inside the root element a browser never applies it.
    ("bad-pi-after-root.xml", feed_xml("bad-pi-after-root.xml", pi="",
                                       pi_inside='<?xml-stylesheet type="text/xsl" href="/feed.xsl"?>'),
     False, {"PI"}, True),
    ("bad-pi-cross-origin.xml", feed_xml("bad-pi-cross-origin.xml",
                                         pi=pi_to("https://cdn.example.test/feed.xsl")),
     False, {"PI"}, True),
    ("bad-pi-type.xml", feed_xml("bad-pi-type.xml",
                                 pi='<?xml-stylesheet type="text/css" href="/feed.xsl"?>\n'),
     False, {"PI"}, True),
    # The copied-template mistake: this feed's self link names the other feed.
    ("bad-self-link.xml", feed_xml("bad-self-link.xml", self_path="good.xml"), False, {"SELF"}, True),
    ("bad-rss-version.xml", feed_xml("bad-rss-version.xml", version="0.91"), False, {"ROOT"}, True),
    ("bad-channel-no-description.xml", feed_xml("bad-channel-no-description.xml", description=""),
     False, {"CHANNEL"}, True),
    ("bad-item-empty.xml", feed_xml("bad-item-empty.xml", items=(
        GOOD_ITEM, "<item><guid isPermaLink=\"false\">fx-4</guid>"
                   "<pubDate>Wed, 12 Aug 2026 09:00:00 +0700</pubDate></item>")),
     False, {"ITEM-CONTENT"}, True),
    ("bad-xsl-not-xslt.xml", feed_xml("bad-xsl-not-xslt.xml", pi=pi_to("/not-xslt.xsl")),
     False, {"XSL"}, True),
    ("bad-xsl-version-2.xml", feed_xml("bad-xsl-version-2.xml", pi=pi_to("/v2.xsl")), False, {"XSL"}, True),
    ("bad-xsl-doe.xml", feed_xml("bad-xsl-doe.xml", pi=pi_to("/doe.xsl")), False, {"XSL"}, True),
    ("bad-render-drops-items.xml", feed_xml("bad-render-drops-items.xml", pi=pi_to("/drops-items.xsl")),
     False, {"RENDER"}, True),
    ("bad-csp-inline-style.xml", feed_xml("bad-csp-inline-style.xml", pi=pi_to("/inline-style.xsl")),
     False, {"CSP"}, True),
    ("bad-asset-missing-css.xml", feed_xml("bad-asset-missing-css.xml", pi=pi_to("/missing-css.xsl")),
     False, {"ASSET"}, True),
    ("bad-absent.xml", None, False, {"MISSING"}, True),
    # The good feed again, with xsltproc made unavailable: the render cannot be
    # checked, so the feed must FAIL rather than pass on the checks that ran.
    ("good.xml", feed_xml("good.xml"), False, {"TOOL"}, False),
]

FIXTURE_README = """# feed_check fixtures

Inputs for `python3 tools/feed_check.py --selftest`, written by the selftest
itself. Nothing here is a site source, and the selftest never reads
`website/dist`. This directory is laid out as a tiny built site: feeds at the
root, stylesheets beside them, and `css/feed.css` for the transform to load.

Each `bad-*` feed is `good.xml` with exactly ONE defect, and the selftest
asserts both that the check fails on it and that it fails for the INTENDED
reason — the error kind is compared, not just the exit code.

| fixture | must | why |
| --- | --- | --- |
| `good.xml` | PASS | baseline: valid RSS 2.0, PI to `/feed.xsl`, renders both titles |
| `good-untitled-item.xml` | PASS | an item with only a description, and a pubDate with no day of week — both legal RSS |
| `bad-missing-guid.xml` | FAIL `ITEM-GUID` | the second item has no guid |
| `bad-pubdate.xml` | FAIL `DATE` | an ISO-8601 pubDate, not RFC-822 |
| `bad-pubdate-weekday.xml` | FAIL `DATE` | "Fri, 12 Aug 2026" — that date is a Wednesday |
| `bad-pi-missing-xsl.xml` | FAIL `PI` | the PI names `/missing.xsl`, which is not there |
| `bad-malformed.xml` | FAIL `XML` | a mismatched closing tag |
| `bad-no-pi.xml` | FAIL `PI` | no xml-stylesheet PI: a browser shows raw XML |
| `bad-pi-after-root.xml` | FAIL `PI` | the PI sits inside `<rss>`, where browsers ignore it |
| `bad-pi-cross-origin.xml` | FAIL `PI` | the PI names another origin's stylesheet |
| `bad-pi-type.xml` | FAIL `PI` | `type="text/css"` on an XSL file |
| `bad-self-link.xml` | FAIL `SELF` | atom:link rel=self names a different feed |
| `bad-rss-version.xml` | FAIL `ROOT` | `<rss version="0.91">` |
| `bad-channel-no-description.xml` | FAIL `CHANNEL` | the channel has no description |
| `bad-item-empty.xml` | FAIL `ITEM-CONTENT` | an item with neither title nor description |
| `bad-xsl-not-xslt.xml` | FAIL `XSL` | the PI names well-formed XML that is not a stylesheet |
| `bad-xsl-version-2.xml` | FAIL `XSL` | an XSLT 2.0 stylesheet; browsers run 1.0 only |
| `bad-xsl-doe.xml` | FAIL `XSL` | the stylesheet writes descriptions with disable-output-escaping |
| `bad-render-drops-items.xml` | FAIL `RENDER` | the stylesheet compiles but never prints the items |
| `bad-csp-inline-style.xml` | FAIL `CSP` | the output carries `style=""`, which the site's CSP blocks |
| `bad-asset-missing-css.xml` | FAIL `ASSET` | the output links a stylesheet that is not in the build |
| (no file) `bad-absent.xml` | FAIL `MISSING` | an expected feed that is not there is an error |
| `good.xml`, no xsltproc | FAIL `TOOL` | a render that cannot be checked fails; it is never skipped |
"""


def write_fixtures():
    FIXTURES.mkdir(parents=True, exist_ok=True)
    (FIXTURES / "css").mkdir(exist_ok=True)
    for name, body in {**XSL_FILES, **CSS_FILES}.items():
        (FIXTURES / name).write_text(body, encoding="utf-8")
    for name, body, *_ in CASES:
        if body is not None:
            (FIXTURES / name).write_text(body, encoding="utf-8")
    absent = [name for name, body, *_ in CASES if body is None]
    for name in absent:
        (FIXTURES / name).unlink(missing_ok=True)
    (FIXTURES / "README.md").write_text(FIXTURE_README, encoding="utf-8")


def selftest() -> int:
    write_fixtures()
    xsltproc = find_xsltproc()
    failures, rows = [], []
    for name, _body, should_pass, expect, has_tool in CASES:
        errors, _counts = evaluate(FIXTURES, [name], xsltproc if has_tool else None)
        passed, got = not errors, kinds_of(errors)
        ok = passed == should_pass and (should_pass or got == expect)
        label = name + ("" if has_tool else " (no xsltproc)")
        rows.append({"fixture": label, "expected": "PASS" if should_pass else "FAIL " + "/".join(sorted(expect)),
                     "got": "PASS" if passed else "FAIL " + "/".join(sorted(got)), "as_expected": ok})
        if not ok:
            failures.append(f"{label}: expected {rows[-1]['expected']}, got {rows[-1]['got']}: {errors[:3]}")
    print(json.dumps({"ok": not failures, "errors": failures,
                      "counts": {"cases": len(CASES), "as_expected": sum(r["as_expected"] for r in rows)},
                      "cases": rows}, indent=2))
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--built", default=str(DEFAULT_BUILT))
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    built = pathlib.Path(args.built).resolve()
    if not built.is_dir():
        print(json.dumps({"ok": False, "errors": [f"MISSING no built directory at {built}"],
                          "counts": {"feeds": 0, "items": 0, "titles_rendered": 0}}, indent=2))
        return 1
    errors, counts = evaluate(built, feeds_in(built), find_xsltproc())
    print(json.dumps({"ok": not errors, "errors": errors, "counts": counts}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

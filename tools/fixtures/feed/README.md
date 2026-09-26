# feed_check fixtures

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

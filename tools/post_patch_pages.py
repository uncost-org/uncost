#!/usr/bin/env python3
"""Re-apply the standing page corrections after regenerating from an export.

tools/gen_static_pages.py writes the export's <main> verbatim, which reverts
every hand fix. These are the fixes that must survive a re-export; run this
immediately after the generator, always.
"""
import re, pathlib, sys

def patch(path, pattern, repl, label, flags=re.S, expect=1, guard=None):
    p = pathlib.Path(path)
    if not p.exists():
        print(f"  - {label}: {path} absent"); return
    s = p.read_text(encoding="utf-8")
    # Idempotent: a re-run after the patch is already applied is a no-op, so the
    # step can be run any number of times after any regeneration.
    # `guard` is required when the replacement opens with a backreference:
    # its first line is a regex fragment, never text that lands in the file.
    marker = guard if guard is not None else repl.strip().split("\n")[0]
    if marker and marker in s:
        print(f"  = {label} (already applied)"); return
    new, n = re.subn(pattern, repl, s, flags=flags)
    if n != expect:
        print(f"  ! {label}: matched {n}, expected {expect}"); sys.exit(1)
    p.write_text(new, encoding="utf-8")
    print(f"  + {label}")

print("Forms — formsOpen is false, so no page may ship a live form (CHECKLIST H):")
patch("website/src/contact.njk", r'<form class="cform".*?</form>\s*(<div class="thanks".*?</div>\s*)?',
      '{% include "partials/forms/contact.njk" %}\n      ', "contact")
patch("website/src/pledge/index.njk", r'<form id="pledge-form".*?</form>',
      '{% include "partials/forms/pledge.njk" %}', "pledge")
patch("website/src/pledge/resent.njk", r'<form id="resend-form".*?</form>',
      '{% include "partials/forms/pledge.njk" %}', "pledge-resend")
patch("website/src/join.njk", r'<form class="iform".*?</form>',
      '{% include "partials/forms/updates.njk" %}', "join interest form")

print("Verify page — the export's state switcher is review furniture (CHECKLIST H):")
p = pathlib.Path("website/src/pledge/verify.njk")
if p.exists() and 'class="switch"' not in p.read_text(encoding="utf-8"):
    print("  = verify page (already applied)")
elif p.exists():
    s = p.read_text(encoding="utf-8")
    for state in ("expired", "used"):
        s = re.sub(r'  <div class="card %s"[^>]*>.*?\n  </div>\n' % state, "", s, flags=re.S)
    s = re.sub(r'<div class="switch"[^>]*>.*?</div>\s*\n', "", s, flags=re.S)
    p.write_text(s, encoding="utf-8")
    print(f"  + one state kept (h1 count {s.count('<h1>')}, switcher {'present' if 'class=\"switch\"' in s else 'removed'})")

print("Outbound hosts — only the movement's reviewed profiles:")
p = pathlib.Path("website/src/pledge/thanks.njk")
if p.exists() and "facebook.com/sharer" not in p.read_text(encoding="utf-8"):
    print("  = thanks page (already applied)")
elif p.exists():
    s = p.read_text(encoding="utf-8")
    s = re.sub(r'<a href="https://www\.facebook\.com/sharer[^"]*"[^>]*>.*?</a>\s*', "", s, flags=re.S)
    s = s.replace("https://www.threads.net/", "https://threads.net/")
    p.write_text(s, encoding="utf-8")
    print("  + thanks: facebook share dropped, threads canonicalised")

print("Heading levels — the export skips a level in these three places:")
for f in ("website/src/about.njk", "website/src/roadmap.njk", "website/src/policies/index.njk"):
    p = pathlib.Path(f)
    if not p.exists(): continue
    s = p.read_text(encoding="utf-8")
    n = s.count("<h4")
    s = s.replace("<h4><i></i>", "<h3><i></i>").replace("<h4>", "<h3>").replace("</h4>", "</h3>")
    p.write_text(s, encoding="utf-8")
    if n: print(f"  + {f}: {n} h4 -> h3")
print("Receipts register — the register IS the citation:")
p = pathlib.Path("website/src/receipts.njk")
if p.exists():
    s = p.read_text(encoding="utf-8")
    start = s.find('<div class="cards">')
    if "{% for row in register.stats %}" in s:
        print("  = receipts register (already applied)")
    if start >= 0 and "{% for row in register.stats %}" not in s:
        end = s.find("</div>", s.rfind('<div class="card">', start))
        # close the last card, then the cards wrapper
        end = s.find("</div>", s.find("</div>", end + 6) + 6) + 6
        close = s.find("</div>", end)
        loop = '''<div class="cards">
{% for row in register.stats %}
    <div class="card" id="{{ row.source_id }}" data-source="{{ row.source_id }}">
      <div class="id">{{ row.source_id }}</div>
      <div class="fig">{{ row.display_value or row.publication_year }}</div>
      <div class="unit">{{ row.data_period }}</div>
      <div class="claim">{{ row.display_caption }}</div>
      <div class="foot">
        <div class="pub">{{ row.publisher }}</div>
        <div class="ttl">{{ row.publication_work }}</div>
        <div class="row">
          <span class="m">Checked {{ row.last_checked }}</span>
          <span class="m">{{ row.region }}</span>
          <span class="rcpt-conf rcpt-conf--{{ "confirmed" if row.confidence.startsWith("confirmed") else "estimate" }}">{{ "Confirmed" if row.confidence.startsWith("confirmed") else "Estimate" }}</span>
        </div>
      </div>
    </div>
{% endfor %}
  </div>'''
        # replace the whole export card list with the register-driven loop
        import re as _re
        s2, n = _re.subn(r'<div class="cards">.*?\n  </div>', loop, s, count=1, flags=_re.S)
        if n == 1:
            p.write_text(s2, encoding="utf-8")
            print("  + receipts: export cards -> register loop with SRC anchors")
        else:
            print("  ! receipts: cards block not matched")

# ---------------------------------------------------------------------------
# UNP-82 content pass (founder-approved copy). gen_static_pages.py rewrites
# receipts.njk and news/index.njk from the export, which carries the pre-content
# wording; these restore the approved copy. Every figure stays register-driven.
# ---------------------------------------------------------------------------
print("UNP-82 — receipts:")
patch("website/src/receipts.njk",
      r'(<div class="u-126"><span class="rcpt-illus">Illustrative only</span>.*?</div>)',
      r'\1\n  <p class="u-131">These four labels describe how much confidence a <b>figure</b> carries.'
      ' They are a deliberately separate system from the status badges on sectors and projects,'
      ' which describe what stage a <b>piece of work</b> is at. The two never mix: a confirmed'
      ' figure can sit on a project that hasn&rsquo;t started, and a project already building can'
      ' rest on an estimate.</p>',
      "confidence-vs-status note", guard="These four labels describe")

# The export's worked example is a $X placeholder with illustrative markers;
# UNP-82 v1 §4c dresses it with a real register row instead.
patch("website/src/receipts.njk",
      r'  <div class="rcpt rcpt-figure--illus demo">.*?<p class="u-128">.*?</p>\n',
      '{% set wex = register.byId["SRC-023"] %}\n'
      '  <div class="rcpt" data-source="{{ wex.source_id }}">\n'
      '    <div class="fig">{{ wex.display_value }}</div>\n'
      '    <div class="cap">{{ wex.display_caption }}</div>\n'
      '    <div class="rcpt-row rcpt-row--hair">\n'
      '      <span class="rcpt-src">SOURCE &mdash; <b>{{ wex.publisher }}, {{ wex.publication_work }}</b> &middot; {{ wex.license | replace("-", " ") }}</span>\n'
      '      <span class="rcpt-updated">Last checked: {{ wex.last_checked }}</span>\n'
      '      <span class="rcpt-conf rcpt-conf--confirmed">Confirmed</span>\n'
      '    </div>\n'
      '  </div>\n',
      "worked example dressed from the register")

patch("website/src/receipts.njk",
      r'<p class="u-130 lead">Eleven sourced figures,',
      '<p class="u-130 lead">{{ register.stats | length }} sourced figures,',
      "register count rendered, not typed", flags=0)

patch("website/src/receipts.njk",
      r'<span class="status status--planned">Log begins at launch</span>\n'
      r'    <p class="u-136">No public figures have been published yet.*?</p>',
      '<span class="status status--planned">No corrections logged yet</span>\n'
      '    <p class="u-136">The corrections log is empty because nothing here has needed a'
      ' correction yet &mdash; not because nothing&rsquo;s been published. Every figure on this'
      ' page above already carries its source, date, and confidence label. The day one needs'
      ' fixing, it&rsquo;ll be logged here: dated, with what changed and why.</p>',
      "corrections launch state")

patch("website/src/receipts.njk",
      r'<p class="u-44 lead">Corrections get priority\..*?</p>',
      '<p class="u-44 lead">Tell us and we&rsquo;ll check it. Every correction gets logged here,'
      ' dated, with a plain description of what changed and why &mdash; nothing is quietly'
      ' edited.</p>',
      "corrections CTA lead")

print("UNP-82 — news Cost Watch (register-driven, not a curated reading list):")
patch("website/src/news/index.njk",
      r'<p>Movement updates on the left\. On the right, a curated <b>Cost Watch</b>.*?</p>',
      '<p>Movement updates on the left. On the right, <b>Cost Watch</b> &mdash; fast-moving'
      ' prices, sourced and dated the same way as everything else on this site.</p>',
      "intro band")

patch("website/src/news/index.njk",
      r'    <p class="cwsub">External reporting.*?<p class="u-97">.*?</p>\n',
      '    <p class="cwsub">Fast-moving prices, sourced and dated the same way as everything else'
      ' on this site &mdash; refreshed on each source&rsquo;s own cadence, not curated'
      ' commentary.</p>\n'
      '{% for row in register.newsFeed %}\n'
      '    <a class="cw" href="{{ row.url }}" target="_blank" rel="noopener" data-source="{{ row.source_id }}">\n'
      '      <div class="src"><span>{{ row.publisher }}</span><span>{{ row.data_period }}</span></div>\n'
      '      <h4>{{ row.display_caption }}</h4>\n'
      '      <span class="ext">Read at {{ row.url.split("/")[2] | replace("www.", "") }} &rarr;</span>\n'
      '    </a>\n'
      '{% endfor %}\n'
      '    <p class="u-97">Checked {{ register.lastChecked }}. Every figure here has a <a href="/receipts#register">receipt</a>.</p>\n',
      "Cost Watch rows")

patch("website/src/news/index.njk",
      r'<p class="u-96" id="rss">More updates arrive as the movement launches\. An RSS feed will be published here at launch\.</p>',
      '<p class="u-96" id="rss">More updates arrive as the movement launches. Prefer a feed? '
      '<a href="/news/feed.xml">Subscribe by RSS</a> &mdash; every update, no algorithm in between.</p>',
      "RSS line (the feed exists; the export predates it)", flags=0)

print("done")

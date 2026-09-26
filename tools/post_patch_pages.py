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
# The confidence-vs-status note patch is RETIRED 2026-09-26 by V11: the section
# it wrote into ("Four honest labels") is retired into the labels drawer, and
# the note now lives in _data/labels.js (the confidence family's `note`), where
# a re-derivation cannot reach it. After a re-derivation the V11 patches at the
# end of this file remove the export's section wholesale.

# (The worked-example patch is retired: P2 removed that section from /receipts/
#  entirely on 2026-09-13, and R3 retired the .fact treatment it used.)

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

# UNP-82 — news: RETIRED 2026-09-19.
#
# Three patches used to restore the Cost Watch intro band, the register-driven
# Cost Watch rows, and the RSS line to website/src/news/index.njk. All three
# now match 0 and exit 1: /news/ has been rewritten twice since they were
# written — first into a two-column split landing, then back into a single
# full Uncost news page — and none of the text they anchor on exists any more.
#
# They are retired rather than re-pointed at the current markup, because
# re-pointing would just rebuild the same trap: a patch that carries a copy of
# the words drifts out of date every time the words move. News copy follows
# /movement/ and /case/ into the content layer instead, where a re-derivation
# cannot reach it.
#
# This failure was not caused by the content-layer migration. It was already
# failing on the previous commit, which is the fail-loud design doing exactly
# its job — loudly, and unmissably, at the next run rather than silently at
# the next deploy.

# ---------------------------------------------------------------------------
# Content layer (closes CANVAS-SYNC item 45).
#
# The six patches that used to live here restored approved WORDS to /movement/
# and /case/ after a re-derivation: two headline accent spans, a third accent,
# and three link texts. They are retired, because the words no longer live in
# a file a re-derivation can overwrite — they live in
# website/src/_data/pageContent.js, which gen_static_pages.py never touches.
#
# What a re-derivation can still destroy is the WIRING: the generator writes
# the export's <main> verbatim, so the template stops reading the data file and
# starts carrying the export's pre-content wording again. So these two patches
# restore the wiring, not the copy. That is a much better failure mode. A patch
# that restores words can silently drift from the words it is supposed to
# restore; a patch that restores wiring either connects the template to the
# content layer or fails loudly, and the copy is safe either way.
# ---------------------------------------------------------------------------
print("Content layer — re-point the re-derived templates at _data/pageContent.js:")

MOVEMENT_BODY = '''<!-- SECTION: movement.What this is -->
{%- set mc = pageContent.movement %}
<section class="blk blk--first" data-screen-label="What this is">
  <h2 class="u-88 sec">{{ mc.whatThisIs.h2 | safe }}</h2>
  <p class="u-89 lead">{{ mc.whatThisIs.lead | safe }}</p>
{% for para in mc.whatThisIs.body %}
  <p class="u-11">{{ para | safe }}</p>
{% endfor %}
</section>

<!-- SECTION: movement.What we stand for -->
<section class="blk blk--wheat" data-screen-label="What we stand for">
  <div class="eyebrow">{{ mc.whatWeStandFor.eyebrow }}</div>
  <h2 class="u-88 sec">{{ mc.whatWeStandFor.h2 | safe }}</h2>
  <p class="u-89 lead">{{ mc.whatWeStandFor.lead | safe }}</p>
{% for para in mc.whatWeStandFor.body %}
  <p class="u-11">{{ para | safe }}</p>
{% endfor %}
</section>

<!-- SECTION: movement.What taking part means -->
<section class="blk blk--cream2" data-screen-label="What taking part means">
  <div class="eyebrow">{{ mc.whatTakingPartMeans.eyebrow }}</div>
  <h2 class="u-6 sec">{{ mc.whatTakingPartMeans.h2 | safe }}</h2>
{% for para in mc.whatTakingPartMeans.body %}
  <p class="u-11">{{ para | safe }}</p>
{% endfor %}
</section>

<!-- SECTION: movement.How to take part -->
<section class="blk blk--ink u-block--ink" data-screen-label="How to take part">
  <div class="u-5 eyebrow">{{ mc.howToTakePart.eyebrow }}</div>
  <h2 class="u-91 sec">{{ mc.howToTakePart.h2 | safe }}</h2>
  <div class="path">
{% for path in mc.howToTakePart.paths %}
    <div class="p"><h3>{{ path.h3 }}</h3><p>{{ path.body | safe }}</p></div>
{% endfor %}
  </div>
  <p class="u-10">{{ mc.howToTakePart.note | safe }}</p>
</section>

<!-- SECTION: movement.Movement CTA -->
<section class="u-93 blk blk--coral" data-screen-label="Movement CTA">
  <h2 class="u-77 sec">{{ mc.cta.h2 | safe }}</h2>
  <p class="u-94 lead">{{ mc.cta.lead | safe }}</p>
  <div class="u-95">
    <a href="/pledge/" class="u-btn u-btn--ink">Sign the Pledge</a>
    <a href="#updates" class="u-btn u-btn--ghost">Get updates</a>
  </div>
</section>
'''

patch("website/src/movement.njk",
      r'<!-- SECTION: movement\.What this is -->.*\Z',
      MOVEMENT_BODY,
      "/movement/ body reads pageContent.movement", guard="pageContent.movement")

CASE_MECHANISM = '''<!-- SECTION: case.The mechanism -->
{%- set cm = pageContent.case.mechanism %}
<section class="blk blk--first blk--cream2" data-screen-label="The mechanism">
  <div class="eyebrow">{{ cm.eyebrow }}</div>
  <h2 class="sec">{{ cm.h2 | safe }}</h2>
  <p class="u-11 lead">{{ cm.lead | safe }}</p>
  <div class="cards cards--2up">
    {{ fig.card(register.byId["SRC-020"]) }}
    {{ fig.card(register.byId["SRC-024"]) }}
  </div>
  <p class="u-11">{{ cm.close | safe }}</p>
</section>

'''

patch("website/src/case/index.njk",
      r'<!-- SECTION: case\.The mechanism -->.*?(?=<!-- SECTION: case\.What living costs -->)',
      CASE_MECHANISM,
      "/case/ mechanism reads pageContent.case", guard="pageContent.case")

print("2026-09-12 sweep — remaining page fixes:")
patch("website/src/contribute.njk",
      r'<a href="/join/" class="u-btn u-btn--ink btn">Tell us how you can help</a>',
      '<a href="/contact/" class="u-btn u-btn--ink btn">Tell us how you can help</a>',
      "D1 /contribute/ CTA -> /contact/", flags=0)

print("R5 — sector 05 Sources adopts the reference table format:")
patch("website/src/sectors/sector.njk",
      r'(  <div class="src"><div class="src-num">SRC-001.*?\n)(</section>)',
      r'  <div class="srcs">\n    <div class="srcs-head"><span>ID</span><span>Source</span></div>\n\1  </div>\n\2',
      "R5 sector sources table", guard='<div class="srcs">')

print("C17 — sector 03 renders THAT sector's worked example, not Food's:")
# The export hard-codes Food's scenario heading into every re-derived sector
# page. The heading, and the research-gated sectors' measurement-only pattern,
# come from _data/sectorContent.js; nothing here authors copy. The gated branch
# restores the rendering first shipped in 552e6c2, which the design-v2
# re-derivation dropped.
SECTOR_WORKED = '''{%- set wx = sc.workedExample if sc else none %}
{%- if wx %}
<section id="worked" class="block" data-screen-label="Worked example">
{%- if wx.measurement %}
  <div class="eyebrow">03 \u00b7 Where the method stops</div>
  <h2>How far the method goes in {{ sector.name }} \u2014 and where it stops.</h2>
{%- else %}
  <div class="eyebrow">03 \u00b7 How {{ sector.name | lower }} gets uncosted</div>
  <h2>{{ wx.scenario }}</h2>
{%- endif %}
  <div class="steps6">
{% for step in wx.steps %}
    {% set bits = step.split(" \u2014 ") %}
    <div class="step6"><div class="n">{{ loop.index }}</div><div><h3><b>{{ bits[0] }}</b></h3><p>{{ bits | slice(1) | first | join(" \u2014 ") if bits.length > 1 else step }}</p></div></div>
{% endfor %}
  </div>
{%- if wx.measurement %}
  <p class="wx-stop"><strong>Then we stop.</strong> Steps 4 to 6 \u2014 matching a mechanism, packaging it for others to run, and tracking whether the cost falls \u2014 would put a tool between a person and their {{ wx.stopBetween }}. That needs {{ wx.stopReason }} \u2014 and none of that exists yet. Until it does, {{ sector.name }} is a measurement sector: we can show what it costs and where the cost sits. We will not package something for a community group to run.</p>
{%- endif %}
</section>
{%- endif %}
'''

patch("website/src/sectors/sector.njk",
      r'<section id="worked" class="block" data-screen-label="Worked example">.*?\n</section>\n',
      SECTOR_WORKED,
      "C17 sector worked example is per-sector", guard="{%- set wx = sc.workedExample")

patch("website/src/sectors/sector.njk",
      r'  <a href="#worked">Worked example <span class="cnt">03</span></a>\n',
      '{%- if sc and sc.workedExample %}\n'
      '  <a href="#worked">Worked example <span class="cnt">03</span></a>\n'
      '{%- endif %}\n',
      "C17 anchor 03 drops with the section", guard="{%- if sc and sc.workedExample %}")

# C5 (Batch U, 2026-09-25) — homepage hero intro: "We aim to significantly…"
# starts a new line after "…price tag." The copy lives in _data/home.json,
# which tools/rederive_home.py re-extracts from the export on every adoption,
# so the break is restated here. No copy changes: the space after the full
# stop becomes a <br>. Fails loudly if the sentence itself has moved.
# (V14, below, supersedes the C5 line break: the sentence after "price tag."
# moved up into the headline, so there is no second sentence to break before.)
# V14 (Batch V, 2026-09-26) — homepage hero, top to bottom: "We aim to
# significantly reduce the cost of living by putting AI and robotics to work for
# humanity." as the headline's first line (display face, ink, half the
# headline's size — CSS item 113) -> "Uncost the cost of living." -> the intro
# cut to its first sentence. Every string already existed on the page; home.json
# is re-extracted from the export on adoption, so both are restated.
patch("website/src/_data/home.json",
      r'("headline": "<span class=\\"u-49\\">).*?(</span><span class=\\"u-50\\">)',
      r'\1We aim to significantly reduce the cost of living by putting AI and robotics to work for humanity.\2',
      "V14 hero headline line one", guard="u-49\\\">We aim to significantly")
patch("website/src/_data/home.json",
      r'("subhead": "Uncost is a nonprofit, nonpartisan movement that believes <u>living should not have a price tag</u>\.)[^"]*(")',
      r'\1\2',
      "V14 hero intro is its first sentence", guard='price tag</u>."')

# C12 (Batch U, 2026-09-25) — /receipts/ "The rule" band goes white. The band's
# CLASS changes, not just its paint: kept as .blk--wheat, C1's wheat rules would
# go on turning its eyebrow and numerals ink on a white ground.
patch("website/src/receipts.njk",
      r'<section class="blk blk--wheat" data-screen-label="The rule">',
      '<section class="blk blk--white" data-screen-label="The rule">',
      "C12 receipts rule band is white")

# V10 (Batch V, 2026-09-26) — exact strings. chrome.json is repo-owned and not
# re-derived; home.json and news/index.njk are, so their two changes are
# restated here.
patch("website/src/_data/home.json",
      r'"cta": "See the projects →"',
      '"cta": "See The Projects →"',
      "V10 homepage CTA reads The Projects", guard='"cta": "See The Projects →"')
patch("website/src/news/index.njk",
      r'<h1><span class="u-1">News</span></h1>',
      '<h1>Uncost.org <span class="u-1">News</span></h1>',
      "V10 /news/ title band reads Uncost.org News", guard='<h1>Uncost.org <span class="u-1">News</span></h1>')

# V18 (Batch V, 2026-09-26) — the /sectors/ headline, exact founder string,
# accent on "fifteen sectors". sectors/index.njk is re-derived by
# tools/rederive_collections.py, which would restore the export's headline (and
# with it would already have lost H5's), so the introband's headline is
# restated here whatever the export wrote into it.
patch("website/src/sectors/index.njk",
      r'(<div class="[^"]*\bintroband\b[^"]*">\s*)<h2>.*?</h2>',
      r'\1<h2>Basic human needs break into <span class="u-1">fifteen sectors</span> &mdash; and we have a plan to reduce the cost of each.</h2>',
      "V18 sectors headline", guard="and we have a plan to reduce the cost of each.")

# V22 (Batch V, 2026-09-26) — /assembly/ "A look ahead": the PLANNED TOOL chip
# goes, and the ink button reads "How the Assembly works", linking the page the
# nav names that way (/assembly/). assembly.njk is re-derived from the export.
# A removal has no text of its own to guard on, so it is guarded by absence.
if "Planned tool</span>" in pathlib.Path("website/src/assembly.njk").read_text(encoding="utf-8"):
    patch("website/src/assembly.njk",
          r'\n\s*<span class="status status--planned">Planned tool</span>', '',
          "V22 assembly look-ahead drops the Planned tool chip")
else:
    print("  = V22 assembly look-ahead drops the Planned tool chip (already applied)")
patch("website/src/assembly.njk",
      r'(<a href=")[^"]*(" class="u-btn u-btn--ink">)View the illustrative mock(</a>)',
      r'\1/assembly/\2How the Assembly works\3',
      "V22 assembly look-ahead button", guard="How the Assembly works</a>")

# V24 (Batch V, 2026-09-26) — /contribute/ "Useful roles, right now." gains a
# "Volunteer now" button to /contact/, after the section's closing note.
# contribute.njk is re-derived from the export.
patch("website/src/contribute.njk",
      r'(<h2 class="[^"]*">Useful roles, right now\.</h2>.*?</p>)(\n</section>)',
      r'\1\n  <div class="roles-cta"><a href="/contact/" class="u-btn u-btn--ink">Volunteer now</a></div>\2',
      "V24 contribute roles: Volunteer now", guard='class="roles-cta"')

# V25 (Batch V, 2026-09-26) — /roadmap/ "How to read these dates" becomes a
# standard prose band: its existing heading (the export's eyebrow text) is the
# band's h2 headline, the eyebrow slot is left empty until approved copy
# arrives, and the body is unchanged. roadmap.njk is re-derived.
patch("website/src/roadmap.njk",
      r'(<section class="blk blk--wheat" data-screen-label="Disclaimer">\n)  <div class="[^"]*\beyebrow\b[^"]*">How to read these dates</div>\n',
      '\\1  {#- V25: a standard prose band. The eyebrow slot stays empty until approved\n'
      '      copy arrives; the band\'s existing heading is its headline. -#}\n'
      '  <h2 class="sec">How to read these dates</h2>\n',
      "V25 roadmap dates band is a prose band", guard='<h2 class="sec">How to read these dates</h2>')

# V21 (Batch V, 2026-09-26) — accent spans, copy unchanged. treasury.njk,
# roadmap.njk and about.njk are re-derived from the export; project.njk is not.
patch("website/src/treasury.njk", r'before a single dollar moves\.</h2>',
      'before a <span class="u-1">single dollar moves</span>.</h2>',
      "V21 treasury accent: single dollar moves", guard='<span class="u-1">single dollar moves</span>')
patch("website/src/treasury.njk", r'Want to help before donations open\?</h2>',
      'Want to <span class="u-1">help</span> before donations open?</h2>',
      "V21 treasury accent: help", guard='Want to <span class="u-1">help</span>')
patch("website/src/roadmap.njk", r'evidence and safety are ready\.</h2>',
      'evidence and safety are <span class="u-1">ready</span>.</h2>',
      "V21 roadmap accent: ready", guard='are <span class="u-1">ready</span>.')
patch("website/src/about.njk", r'<h3>Uncost is</h3>', '<h3>Uncost <u>is</u></h3>',
      "V21 about: underline is", guard='<h3>Uncost <u>is</u></h3>')
patch("website/src/about.njk", r'<h3>Uncost is not</h3>', '<h3>Uncost <u>is not</u></h3>',
      "V21 about: underline is not", guard='<h3>Uncost <u>is not</u></h3>')

# V17 (Batch V, 2026-09-26) — /case/ closing band: "The question is no longer
# whether…" moves from above "Evidence first. Tools next." to directly below
# it, above "The Case feeds The Projects…". case/index.njk is re-derived.
patch("website/src/case/index.njk",
      r'(  <p class="u-39 lead">The question is no longer whether.*?</p>\n)(  <h2 class="u-38 sec">Evidence first\..*?</h2>\n)',
      r'\2\1',
      "V17 case: question lead follows the headline",
      guard='Tools next.</span></h2>\n  <p class="u-39 lead">The question is no longer whether')

# V15 (Batch V, 2026-09-26) — /movement/: the six-step "How it works" band and
# "What taking part means" swap backgrounds (cream <-> cream-2), and the CTA's
# "Get updates" goes to /join/#get-updates. movement.njk is re-derived.
patch("website/src/movement.njk",
      r'<section class="blk blk--cream" data-screen-label="How a cost gets uncosted">(.*?)<section class="blk blk--cream2" data-screen-label="What taking part means">',
      r'<section class="blk blk--cream2" data-screen-label="How a cost gets uncosted">\1<section class="blk blk--cream" data-screen-label="What taking part means">',
      "V15 movement: swap six-step and taking-part backgrounds",
      guard='<section class="blk blk--cream2" data-screen-label="How a cost gets uncosted">')
patch("website/src/movement.njk",
      r'<a href="#updates" class="u-btn u-btn--ghost">Get updates</a>',
      '<a href="/join/#get-updates" class="u-btn u-btn--ghost">Get updates</a>',
      "V15 movement: Get updates -> /join/#get-updates", guard='href="/join/#get-updates"')

# V12 (Batch V, 2026-09-26) — one "How a cost gets uncosted" partial in the
# /about/ format, on /about/ and /movement/; words in _data/uncosted.js. Both
# templates are re-derived from the export, so the call sites are restated.
patch("website/src/about.njk",
      r'<div class="seqhd" data-screen-label="Mechanism">.*?</h2></div>\n<div>\n(?:  <div class="[^"]*step">.*?</p></div></div>\n)+</div>\n',
      '{% import "partials/uncosted.njk" as uc %}\n{{ uc.block(uncosted.about, "Mechanism") }}\n',
      "V12 about: uncosted partial", guard='{{ uc.block(uncosted.about, "Mechanism") }}')
patch("website/src/movement.njk",
      r'(<section class="blk blk--cream2" data-screen-label="How a cost gets uncosted">\n).*?(</section>)',
      r'\1  {% import "partials/uncosted.njk" as uc %}\n  {{ uc.block(uncosted.movement) }}\n\2',
      "V12 movement: uncosted partial", guard="{{ uc.block(uncosted.movement) }}")

# V16 (Batch V, 2026-09-26) — /news/ loads /js/read-more.js (three-line clamp,
# "Read more"). news/index.njk is re-derived from the export, so the include is
# restated after the keyword filter's. cost-watch.njk is repo-owned.
patch("website/src/news/index.njk",
      r'(<script src="/js/keyword-filter.js" defer></script>\n)',
      r'\1<script src="/js/read-more.js" defer></script>\n',
      "V16 news: read-more script", guard='<script src="/js/read-more.js" defer></script>')

V19_SCENARIO = """{#- V19: the scenario phrase — the words after "A worked example:" — takes
    the accent; the full stop stays outside it. A heading with no colon renders
    whole, unaccented. -#}
{%- set sp = wx.scenario.split(": ") %}
{%- set phrase = sp.slice(1).join(": ") %}
{%- set stop = "." if phrase.endsWith(".") else "" %}
  <h2>{% if phrase %}{{ sp[0] }}: <span class="u-1">{{ phrase.slice(0, phrase.length - stop.length) }}</span>{{ stop }}{% else %}{{ wx.scenario }}{% endif %}</h2>
"""

# V19 (Batch V, 2026-09-26) — sector pages and the /sectors/ status legend.
# sector.njk and sectors/index.njk are both re-derived by
# tools/rederive_collections.py, so the three template changes are restated.
# The 03 headline is restated after C17 has put the per-sector heading back.
patch("website/src/sectors/sector.njk",
      r'<h2>Where automation could bite — and what stays visible\.</h2>',
      '<h2>Where automation could <span class="u-1">bite</span> — and what stays visible.</h2>',
      "V19 sector 01 accent on bite", guard='<span class="u-1">bite</span>')
patch("website/src/sectors/sector.njk",
      r'  <h2>\{\{ wx\.scenario \}\}</h2>\n',
      V19_SCENARIO,
      "V19 sector 03 scenario phrase accent", guard="{%- set sp = wx.scenario.split(\": \") %}")
patch("website/src/sectors/index.njk",
      r'(<div class="legend" data-screen-label="Legend">\n  <span>Status:</span>\n)'
      r'((?:  <span class="status [^"]+">[^<]+</span> <span class="u-138">[^<]+</span>\n){4})',
      lambda m: m.group(1) + re.sub(
          r'  (<span class="status [^"]+">[^<]+</span>) (<span class="u-138">[^<]+</span>)\n',
          r'  <span class="lg-pair">\1<span class="lg-colon">:</span>\2</span>\n', m.group(2)),
      "V19 /sectors/ legend: chip, colon, meaning", guard='<span class="lg-pair">')

# V11 (Batch V, 2026-09-26) — the labels drawer. The standalone "Four honest
# labels" section on /receipts/ is retired into it, and the drawer partial is
# included on /receipts/, /projects/, /policies/, /sectors/, /news/ and
# /treasury/ (and /news/cost-watch/, which is repo-owned). All six of those
# templates are re-derived from the export, so both the retirement and the
# includes are restated. The retirement is a removal, so it is guarded by
# absence.
if 'data-screen-label="Confidence labels"' in pathlib.Path("website/src/receipts.njk").read_text(encoding="utf-8"):
    patch("website/src/receipts.njk",
          r'<!-- SECTION: receipts\.Confidence labels -->\n<section [^>]*data-screen-label="Confidence labels">.*?</section>\n\n',
          '', "V11 receipts: Four honest labels retired into the drawer")
else:
    print("  = V11 receipts: Four honest labels retired into the drawer (already applied)")
LABELS_DRAWER = '{% include "partials/labels-drawer.njk" %}\n'
for path, anchor, where in (
    ("website/src/receipts.njk", r'(<!-- SECTION: receipts\.Receipts CTA -->\n)', "before the CTA"),
    ("website/src/projects/index.njk", r'(<!-- SECTION: projects\.Projects CTA -->\n)', "before the CTA"),
    ("website/src/sectors/index.njk", r'(<!-- SECTION: sectors\.Sectors CTA -->\n)', "before the CTA"),
    ("website/src/treasury.njk", r'(<!-- SECTION: treasury\.Treasury CTA -->\n)', "before the CTA"),
    ("website/src/news/index.njk", r'(<script src="/js/keyword-filter\.js" defer></script>\n)', "after the list"),
):
    patch(path, anchor, LABELS_DRAWER + ("\n" if "SECTION" in anchor else "") + r"\1",
          f"V11 {path.split('src/')[1]}: labels drawer {where}", guard=LABELS_DRAWER.strip())
patch("website/src/policies/index.njk",
      r'(data-screen-label="How policies change">.*?</section>\n)',
      r"\1\n" + LABELS_DRAWER,
      "V11 policies/index.njk: labels drawer after the last section", guard=LABELS_DRAWER.strip())

print("done")

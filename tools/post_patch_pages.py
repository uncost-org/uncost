#!/usr/bin/env python3
"""Re-apply the standing page corrections after regenerating from an export.

tools/gen_static_pages.py writes the export's <main> verbatim, which reverts
every hand fix. These are the fixes that must survive a re-export; run this
immediately after the generator, always.
"""
import re, pathlib, sys

def patch(path, pattern, repl, label, flags=re.S, expect=1):
    p = pathlib.Path(path)
    if not p.exists():
        print(f"  - {label}: {path} absent"); return
    s = p.read_text(encoding="utf-8")
    # Idempotent: a re-run after the patch is already applied is a no-op, so the
    # step can be run any number of times after any regeneration.
    marker = repl.strip().split("\n")[0]
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
print("done")

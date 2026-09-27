#!/usr/bin/env python3
"""Re-derive the homepage from the current export, re-wiring its dynamic slots.

The export renumbers its .u-N extraction classes on every regeneration, so a
homepage hand-written against an older export silently picks up wrong rules.
This rebuilds it from the export's own index.html and re-applies the wiring:
the three S2 figures from the register, the S6 counts from the repository's
registers, the S5 focus trio from the sector dossiers, and the S7 updates block
from the forms flag. Copy stays in _data/home.json.
"""
import json, re, subprocess, pathlib, os

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPORT = pathlib.Path(os.environ["UNCOST_DESIGN_SOURCE"])

out = subprocess.run(["python3", str(ROOT / "tools" / "export_to_njk.py"), "index.html"],
                     capture_output=True, text=True, cwd=ROOT)
meta = json.loads(out.stdout.split("\n", 1)[0]); body = out.stdout.split("\n", 1)[1]

# 1. Content slots -> _data/home.json, re-extracted so the inline classes match
#    this export's numbering.
slots = {}
for m in re.finditer(r'<(\w+)[^>]*\bdata-content="([^"]+)"[^>]*>', body):
    tag, key, start = m.group(1), m.group(2), m.end()
    depth, i = 1, start
    for t in re.finditer(r'<(/?)%s\b[^>]*>' % tag, body[start:]):
        depth += -1 if t.group(1) else 1
        if depth == 0:
            i = start + t.start(); break
    slots[key] = body[start:i].strip()
nested = {}
for k, v in sorted(slots.items()):
    cur = nested
    for part in k.split(".")[:-1]:
        cur = cur.setdefault(part, {})
    cur[k.split(".")[-1]] = v
home = {"_note": "DRAFT homepage copy, lifted verbatim from the export's data-content "
                 "slots. Re-extracted on every re-derivation because the export renumbers "
                 "its .u-N classes. The S2 statistics and S6 counts are NOT here — they "
                 "render from sources/register.csv and the repository's registers.", **nested}
(ROOT / "website/src/_data/home.json").write_text(
    json.dumps(home, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# 2. Slot contents -> template variables (leave the element and its classes alone).
def slot_sub(m):
    tag, attrs, key = m.group(1), m.group(2), m.group(3)
    start = m.end(); depth, i = 1, start
    for t in re.finditer(r'<(/?)%s\b[^>]*>' % tag, body[start:]):
        depth += -1 if t.group(1) else 1
        if depth == 0:
            i = start + t.start(); break
    return f"<{tag}{attrs}>{{{{ home.{key} | safe }}}}</{tag}>", i
res, pos = [], 0
for m in re.finditer(r'<(\w+)((?:[^>]*?)\bdata-content="([^"]+)"(?:[^>]*?))>', body):
    if m.start() < pos: continue
    repl, end = slot_sub(m)
    res.append(body[pos:m.start()]); res.append(repl)
    close = re.search(r'</%s>' % m.group(1), body[end:])
    pos = end + (close.end() if close else 0)
res.append(body[pos:])
body = "".join(res)
body = re.sub(r'\s*data-content="[^"]*"', "", body)

# 3. The three S2 figures -> the register.
body = re.sub(r'<div class="facts">.*?</div>\s*</div>\s*</div>',
              '<div class="facts">\n    {{ fig.fact(register.byId["SRC-021"]) }}\n'
              '    {{ fig.fact(register.byId["SRC-022"]) }}\n'
              '    {{ fig.fact(register.byId["SRC-006"]) }}\n  </div>',
              body, count=1, flags=re.S)

# 4. S6 counts -> the repository's own registers.
def counts(m):
    return ('<div class="counts">\n'
            '    <div class="c"><div class="cn">{{ catalog.counts.policies }}</div><div class="cl">Policies</div>'
            '<div class="cs">{{ catalog.counts.policyRange }} &mdash; {{ catalog.counts.policiesDrafted }} public review drafts '
            'and {{ catalog.counts.policiesReserved }} reserved reference, none adopted or in force.</div></div>\n'
            '    <div class="c"><div class="cn">{{ catalog.counts.projects }}</div><div class="cl">Project briefs</div>'
            '<div class="cs">{{ catalog.counts.projectRange }} &mdash; drafts pending independent review.</div></div>\n'
            '    <div class="c"><div class="cn">{{ catalog.counts.sectors }}</div><div class="cl">Sector dossiers</div>'
            '<div class="cs">One per sector, each with its scope, opportunity and guardrail stated.</div></div>\n  </div>')
body = re.sub(r'<div class="counts">.*?\n  </div>', counts, body, count=1, flags=re.S)

# 5. S5 focus trio -> the sector dossiers (name, status chip, illustration, blurb).
focus = ('<div class="focus3">\n'
         '{% for sector in [catalog.sectorsBySlug.shelter, catalog.sectorsBySlug.food, catalog.sectorsBySlug.energy] %}\n'
         '    <a href="/sectors/{{ sector.slug }}/"><div class="img">{% image sector.illustration.src, sector.illustration.alt %}</div>'
         '<div class="tx"><span class="status status--{{ sector.statusClass }}">{{ sector.status }}</span>'
         '<h3>{{ sector.name }}</h3><p>{{ home.s5[sector.slug] | safe }}</p></div></a>\n'
         '{% endfor %}\n  </div>')
body = re.sub(r'<div class="focus3">.*?\n  </div>', focus, body, count=1, flags=re.S)

# 6. S7 updates block -> the forms flag.
body = re.sub(r'<div class="formoff">.*?</div>\s*</div>',
              '{% if features.formsOpen %}{% include "partials/forms/updates.njk" %}'
              '{% else %}<div class="formoff" data-form="updates"><div class="m">Sign-ups open soon.</div>'
              '<div class="s">The updates list opens at launch. Nothing to enter yet.</div></div>{% endif %}',
              body, count=1, flags=re.S)

# 7. Social row -> chrome.json.
body = re.sub(r'<div class="soc-txt">.*?</div>',
              '<div class="soc-txt">{% for s in chrome.social %}{% if s.label != "Email" %}'
              '<a href="{{ s.url }}" target="_blank" rel="noopener">{{ s.label }}</a>{% endif %}{% endfor %}</div>',
              body, count=1, flags=re.S)

# 8. Freshness lines come from the register's own last_checked.
body = re.sub(r'(<span class="rcpt-updated">(?:Figures|Records) checked )[^<]*(</span>)',
              r'\1{{ register.lastChecked }}\2', body)

front = f'''---
layout: layouts/base.njk
home: true
pageId: "{meta['pageId']}"
updatesOff: true
title: "Home"
description: "{meta['description']}"
---
{{#-
  Homepage — re-derived from the export's own index.html, so its .u-N extraction
  classes match this export's numbering. Copy is CONTENT and lives in
  _data/home.json; the S2 figures come from sources/register.csv and the S6
  counts from the repository's registers. No figure is written here.
  Regenerate with tools/rederive_home.py after any export adoption.
-#}}
{{% import "partials/figure.njk" as fig %}}
'''
(ROOT / "website/src/index.njk").write_text(front + body.strip() + "\n", encoding="utf-8")
print(f"homepage re-derived: {len(slots)} content slots, register/catalog/forms re-wired")

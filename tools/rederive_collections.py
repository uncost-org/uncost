#!/usr/bin/env python3
"""Re-derive the sectors index and the three collection templates from the export.

Same reason as the homepage: the export renumbers .u-N on every regeneration, so
these must be rebuilt from its own pages rather than hand-maintained. Dynamic
slots are re-wired to the repository's registers afterwards.
"""
import json, re, subprocess, pathlib, os
ROOT = pathlib.Path(__file__).resolve().parents[1]

def convert(rel):
    out = subprocess.run(["python3", str(ROOT / "tools" / "export_to_njk.py"), rel],
                         capture_output=True, text=True, cwd=ROOT)
    head, body = out.stdout.split("\n", 1)
    return json.loads(head), body

def write(path, front, body):
    p = ROOT / "website/src" / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(front + body.strip() + "\n", encoding="utf-8")
    print(f"  wrote {path}")

# ---------- sectors index -------------------------------------------------
meta, body = convert("sectors.html")
loop = ('<div class="sgrid">\n'
        '{% for sector in catalog.sectors %}\n'
        '  <a class="scard{% if sector.statusClass == \'focus\' %} focus{% endif %}" href="/sectors/{{ sector.slug }}/">'
        '<div class="top"><span class="idx">{{ sector.num }}</span>'
        '<span class="status {{ sector.chipClass }}">{{ sector.status }}</span></div>'
        '{% image sector.illustration.src, sector.illustration.alt %}'
        '<h3>{{ sector.name }}</h3>'
        '<p>{% if sector.includes %}{{ sector.includes }}{% else %}{{ gapInline("sector-includes") }}{% endif %}</p>'
        '<span class="go">Read the dossier &rarr;</span></a>\n'
        '{% endfor %}\n  </div>')
body = re.sub(r'<div class="sgrid">.*?\n  </div>', loop, body, count=1, flags=re.S)
write("sectors/index.njk",
      f'''---
layout: layouts/base.njk
permalink: "/sectors/"
pageId: "{meta['pageId']}"
title: "The Sectors"
description: "{meta['description']}"
---
{{#- Re-derived from the export's sectors.html; the 15 cards loop over the
    repository's sector dossiers. Regenerate with tools/rederive_collections.py. -#}}
{{% from "partials/content-needed.njk" import inline as gapInline %}}
''', body)

# ---------- sector detail -------------------------------------------------
meta, body = convert("sectors/food.html")
R = lambda pat, rep, n=1: (pat, rep, n)
def sub(b, pat, rep, count=1):
    out, k = re.subn(pat, rep.replace("\\", "\\\\"), b, count=count, flags=re.S)
    assert k == count, f"sector: {pat[:40]} matched {k}"
    return out

body = sub(body, r'<h1 class="sector-title">[^<]*</h1>', '<h1 class="sector-title">{{ sector.name }}.</h1>')
body = sub(body, r'<p class="sector-sub">[^<]*</p>',
           '<p class="sector-sub">{% if sector.includes %}{{ sector.includes }}{% else %}{{ gapInline("sector-includes") }}{% endif %}</p>')
body = sub(body, r'<div class="sector-num">.*?</div>',
           '<div class="sector-num"><span class="nb">Sector <b>{{ sector.num }} / 15</b></span> &middot; '
           '<span class="nb"><span class="status status--{{ sector.statusClass }}">{{ sector.status }}</span></span> &middot; '
           '<span class="nb">Dossier <b>{{ sector.id }}</b></span></div>')
body = sub(body, r'\{% image "sectors/sector-food\.png"[^%]*%\}',
           '{% image sector.illustration.src, sector.illustration.alt, "100vw", [320, 640, 960], "lazy", "sector-illus" %}')
body = sub(body, r'<div class="scope">.*?\n  </div>',
           '<div class="scope">\n'
           '    <div><h3><i></i>What it includes</h3><p>{% if sector.includes %}{{ sector.includes }}{% else %}{{ gapInline("sector-includes") }}{% endif %}</p></div>\n'
           '    <div><h3><i></i>The opportunity</h3><p>{% if sector.opportunity %}{{ sector.opportunity }}{% else %}{{ gapInline("sector-opportunity") }}{% endif %}</p></div>\n'
           '    <div><h3><i></i>The guardrail</h3><p>{% if sector.guardrail %}{{ sector.guardrail }}{% else %}{{ gapInline("sector-guardrail") }}{% endif %}</p></div>\n  </div>')
body = sub(body, r'<div class="evd-empty">\s*<h3>[^<]*</h3>',
           '<div class="evd-empty">\n    {% if sector.evidence %}<h3>{{ sector.evidence }}</h3>{% else %}{{ gap("sector-evidence") }}{% endif %}')
body = sub(body, r'<div class="steps6">.*?\n  </div>',
           '<div class="steps6">\n{% for step in sc.workedExample.steps %}\n'
           '    {% set bits = step.split(" — ") %}\n'
           '    <div class="step6"><div class="n">{{ loop.index }}</div><div><h3><b>{{ bits[0] }}</b></h3>'
           '<p>{{ bits | slice(1) | first | join(" — ") if bits.length > 1 else step }}</p></div></div>\n'
           '{% endfor %}\n  </div>')
body = sub(body, r'<blockquote>.*?</blockquote>\s*<div class="attr">.*?</div>',
           '<blockquote>&ldquo;{{ sector.guardrail }}&rdquo;</blockquote>\n'
           '  <div class="attr">&mdash; The {{ sector.name }} guardrail &middot; dossier {{ sector.id }}</div>')
body = sub(body, r'<tbody>.*?</tbody>',
           '<tbody>\n{% for p in sector.relatedProjects %}\n'
           '      <tr><td class="id">{{ p.id }}</td><td class="title"><a href="/projects/{{ p.slug }}/">{{ p.display }}</a>'
           '<span class="sum">{{ p.line }}</span></td><td class="role">{% if p.layer %}{{ p.layer }}{% else %}{{ p.tag | capitalize }}{% endif %}</td>'
           '<td><span class="status status--planned">Draft &mdash; not approved for build</span></td></tr>\n'
           '{% endfor %}\n    </tbody>')
body = sub(body, r'<div class="related">.*?\n  </div>',
           '<div class="related">\n{% for rel in relatedSectors[sector.slug] %}\n'
           '    <a href="/sectors/{{ rel.slug }}/"><span class="sq {{ rel.sq }}"></span> {{ rel.name }}</a>\n{% endfor %}\n'
           '    <a class="bd-dashed" href="/sectors/"><span class="sq sq-outline"></span> All 15 sectors &rarr;</a>\n  </div>')
# Sector name in prose
body = body.replace("food gets uncosted", "{{ sector.name | lower }} gets uncosted")
body = body.replace("Where Food shows up", "Where {{ sector.name }} shows up")
body = body.replace("Help build the food evidence", "Help build the {{ sector.name | lower }} evidence")
body = body.replace("Role for Food", "Role for {{ sector.name }}")

write("sectors/sector.njk", '''---
layout: layouts/base.njk
pagination:
  data: catalog.sectors
  size: 1
  alias: sector
  addAllPagesToCollections: true
permalink: "/sectors/{{ sector.slug }}/"
eleventyComputed:
  pageId: "sectors/{{ sector.slug }}"
  title: "{{ sector.name | safe }} — Sector dossier"
  description: "{{ sector.id }} {{ sector.name }}: what the sector includes, where AI and robotics could reduce costs, the guardrails, and the honest evidence status."
---
{#- Re-derived from the export's sectors/food.html so the .u-N classes match this
    export. Every field comes from the repository's own dossier via _data/catalog.js
    and _data/sectorContent.js; a field the dossier lacks renders [CONTENT NEEDED].
    Regenerate with tools/rederive_collections.py. -#}
{% from "partials/content-needed.njk" import block as gap, inline as gapInline %}
{% import "partials/figure.njk" as fig %}
{% set sc = sectorContent[sector.slug] %}
''', body)
print("done")

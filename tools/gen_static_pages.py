#!/usr/bin/env python3
"""Generate templates for the export pages whose copy is inline draft.

CONTENT.md marks these pages' copy "inline (draft)", so the export IS both the
markup and the content: the body is taken verbatim and only asset paths and
routes are rewritten. Data-backed pages (faq, news, policies, projects,
receipts, privacy, sectors) and the form pages are wired separately.
"""
import json, pathlib, subprocess, sys

# export file -> (output template path, permalink)
PAGES = {
    "about.html":            ("about.njk", "/about/"),
    "movement.html":         ("movement.njk", "/movement/"),
    "assembly.html":         ("assembly.njk", "/assembly/"),
    "treasury.html":         ("treasury.njk", "/treasury/"),
    "roadmap.html":          ("roadmap.njk", "/roadmap/"),
    "contribute.html":       ("contribute.njk", "/contribute/"),
    "case.html":             ("case/index.njk", "/case/"),
    "error-404.html":        ("404.njk", "/404.html"),
    "pledge-check-email.html": ("pledge/check-email.njk", "/pledge/check-email/"),
    "pledge-thanks.html":    ("pledge/thanks.njk", "/pledge/thanks/"),
    "pledge-verify.html":    ("pledge/verify.njk", "/pledge/verify/"),
    "later/case-dashboard.html": ("case/dashboard.njk", "/case/dashboard/"),
    "later/case-tracker.html":   ("case/tracker.njk", "/case/tracker/"),
    "later/community.html":      ("community.njk", "/community/"),
    "later/events.html":         ("news/events.njk", "/news/events/"),
    "later/press.html":          ("press.njk", "/press/"),
    "later/quiz.html":           ("quiz.njk", "/quiz/"),
    "later/share.html":          ("share.njk", "/share/"),
    # Final tranche. These carry repo-authoritative content and/or forms, so the
    # generated body is the export's markup and the dynamic regions are wired
    # afterwards (see the per-page patches in tools/wire_tranche.py).
    "faq.html":                  ("faq.njk", "/faq/"),
    "news.html":                 ("news/index.njk", "/news/"),
    "receipts.html":             ("receipts.njk", "/receipts/"),
    "contact.html":              ("contact.njk", "/contact/"),
    "privacy.html":              ("privacy.njk", "/privacy/"),
    "policies.html":             ("policies/index.njk", "/policies/"),
    "projects.html":             ("projects/index.njk", "/projects/"),
    "pledge.html":               ("pledge/index.njk", "/pledge/"),
    "pledge-resend.html":        ("pledge/resent.njk", "/pledge/resent/"),
    "join.html":                 ("join.njk", "/join/"),
}
SRC = pathlib.Path("website/src")

def esc(s): return s.replace('"', '\\"')

for rel, (outfile, permalink) in PAGES.items():
    r = subprocess.run(["python3", "tools/export_to_njk.py", rel], capture_output=True, text=True)
    head, body = r.stdout.split("\n", 1)
    meta = json.loads(head)
    if meta["notes"]:
        print(f"  !! {rel}: {meta['notes']}")
    title = meta["title"].replace(" — Uncost", "").replace(" · Uncost", "").strip()
    fm = ["---", "layout: layouts/base.njk", f'permalink: "{permalink}"',
          f'pageId: "{meta["pageId"]}"', f'title: "{esc(title)}"',
          f'description: "{esc(meta["description"])}"']
    if meta["mainClass"]:
        fm.append(f'mainClass: "{meta["mainClass"]}"')
    if rel == "error-404.html":
        fm.append("noindex: true")
    fm.append("---")
    note = ("{#- Markup taken verbatim from design-source/pages/%s. CONTENT.md marks this\n"
            "    page's copy \"inline (draft)\", so the export supplies both; only asset\n"
            "    references and routes are rewritten. Do not re-author. -#}\n" % rel)
    p = SRC / outfile
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(fm) + "\n" + note + body.strip() + "\n", encoding="utf-8")
    print(f"  wrote {outfile:28} from {rel}")
print(f"\n{len(PAGES)} templates generated")

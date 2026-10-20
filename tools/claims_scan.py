#!/usr/bin/env python3
"""Money and legal-status claims in a built site — a report, not a gate.

Searches the visible text of every built page (and the feeds and search index)
for: a request for money (donate, give, contribute money, payment providers,
amounts); a claim of tax deductibility or tax exemption; 501(c)(3); a
registered charity or charity status; nonprofit or not-for-profit; being
incorporated (or an LLC, Inc., Ltd., corporation); and fiscal sponsorship.
Each distinct passage is printed once, with the pages it appears on, so a
person can judge it. It also lists every link whose address or text looks
like a payment or donation link.

    python3 tools/claims_scan.py --built website/dist

Exit 0 always: deciding what a passage claims is a person's job (founder
brief, 2026-10-20). Standing rule 4: these are the results to report.
"""
from __future__ import annotations

import argparse
import html
import json
import pathlib
import re

PATTERNS = {
    "money-ask": r"\b(donat\w*|contribut\w* (?:money|funds)|give (?:money|today|now)|chip in|fund us|support us financially|"
                 r"make a gift|pay what|paypal|stripe|ko-fi|patreon|gofundme|venmo|cash ?app|\$\s?\d+ (?:helps|buys|funds))\b",
    "tax": r"\btax[- ]?deductib\w*|\btax[- ]?exempt\w*|\bdeductible\b",
    "501c3": r"\b501\s*\(?\s*c\s*\)?\s*\(?\s*3\s*\)?",
    "charity": r"\bregistered charit\w*|\bcharit(?:y|able) (?:status|registration|number)|\bcharity\b",
    "nonprofit": r"\bnon-?profit\b|\bnot-for-profit\b",
    "incorporated": r"\bincorporat\w*|\b(?:LLC|Inc\.?|Ltd\.?|corporation)\b",
    "fiscal-sponsor": r"\bfiscal(?:ly)? sponsor\w*",
}
PAY_LINK = re.compile(r'<a\b[^>]*href="([^"]*(?:donat|give|paypal|stripe|ko-fi|patreon|gofundme|checkout|/pay)[^"]*)"', re.I)


def text_of(raw: str) -> str:
    t = re.sub(r"<script\b.*?</script>|<style\b.*?</style>", " ", raw, flags=re.S | re.I)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--built", default="website/dist")
    a = ap.parse_args()
    root = pathlib.Path(a.built)
    files = sorted(list(root.rglob("*.html")) + list(root.rglob("*.xml")) + list(root.rglob("*.json")) + list(root.rglob("*.txt")))
    passages: dict = {}
    links = []
    for f in files:
        raw = f.read_text(encoding="utf-8", errors="replace")
        rel = str(f.relative_to(root))
        for m in PAY_LINK.finditer(raw):
            links.append(f"{rel}: {m.group(1)}")
        t = text_of(raw)
        for kind, pat in PATTERNS.items():
            for m in re.finditer(pat, t, re.I):
                # The sentence around the match is the unit a person judges.
                start = max(t.rfind(". ", 0, m.start()) + 2, m.start() - 160, 0)
                end = t.find(". ", m.end())
                end = min(end + 1 if end != -1 else len(t), m.end() + 200)
                key = (kind, t[start:end].strip())
                passages.setdefault(key, set()).add(rel)
    out = [{"kind": k, "passage": p, "pages": sorted(v)[:8], "page_count": len(v)}
           for (k, p), v in sorted(passages.items(), key=lambda kv: (kv[0][0], -len(kv[1])))]
    print(json.dumps({"files": len(files), "payment_or_donation_links": links, "passages": out}, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

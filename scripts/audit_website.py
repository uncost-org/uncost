#!/usr/bin/env python3
"""Website content audit: fail-closed term rules plus flag-for-review figures.

Scans the rendered-content sources (website/, sectors/, policies/, projects/)
and, with --built DIR, built HTML output before deployment. Two tiers:

- FAIL rules exit non-zero: retired economic-system vocabulary, superseded
  branding, governance-mechanism claims, tax-status claims, bare status
  badges, and retired sector names.
- WARN rules never affect the exit code: dollar figures, percentages, and
  large counts that do not carry a source citation (a registered SRC-###
  id on the same line, or an enclosing HTML element whose data-source
  value is a registered SRC-### id).

Legitimate exceptions live in scripts/audit-website-allowlist.json keyed by
(rule, path, sha256 of the stripped line); any edit to the line invalidates
the exception. Built-output findings are fixed at their source, never
allowlisted. See CONTRIBUTING.md for the exception process.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
ALLOWLIST_PATH = ROOT / "scripts" / "audit-website-allowlist.json"
REGISTER_PATH = ROOT / "sources" / "register.csv"

SOURCE_SCOPE = ("website", "sectors", "policies", "projects")

PROSE_SUFFIXES = {".md", ".html", ".htm", ".njk", ".liquid"}
DATA_SUFFIXES = {
    ".json", ".yml", ".yaml", ".csv", ".txt",
    ".js", ".mjs", ".cjs", ".ts", ".jsx", ".tsx", ".vue", ".svelte", "",
}
STYLE_SUFFIXES = {".css", ".svg"}
SCANNED_SUFFIXES = PROSE_SUFFIXES | DATA_SUFFIXES | STYLE_SUFFIXES

BADGE_WORDS = ("Live", "Funded", "Passed", "Approved", "Operating")

VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}

ZERO_WIDTH = dict.fromkeys(map(ord, "​‌‍⁠﻿­"))

# (rule id, pattern, skip_when_match_is_all_lowercase). The lowercase skip
# keeps ordinary English safe (public transit, entertainment options, a dao
# directory path) while any capitalized or all-caps use of a retired sector
# or mechanism name fails.
Rule = Tuple[str, "re.Pattern[str]", bool]

# Applied to the raw text of every scanned file, all suffix classes.
HARD_ALL_RULES: Tuple[Rule, ...] = (
    ("brand-unprice-name", re.compile(r"(?i)\bunprice\b"), False),
    ("brand-unprice-domain", re.compile(r"(?i)unprice\.org"), False),
    ("post-money-broken", re.compile(r"(?i)money\s+is\s+broken"), False),
    ("post-money-free-produce", re.compile(r"(?i)free\s+to\s+produce"), False),
    ("post-money-all-free", re.compile(r"(?i)everything\s+will\s+be\s+free"), False),
    ("post-money-framing", re.compile(r"(?i)\bpost[-\s]?(?:scarcity|market|money|monetary)\b"), False),
    ("crypto-ucst", re.compile(r"(?i)\bucst\b"), False),
    ("governance-quadratic-voting", re.compile(r"(?i)quadratic\s+voting"), False),
    ("governance-liquid-voting", re.compile(r"(?i)liquid\s+voting"), False),
    ("governance-voting-rights", re.compile(r"(?i)voting\s+rights"), False),
    ("tax-deductibility-claim", re.compile(r"(?i)tax[-\s]deductib"), False),
    ("tax-501c3-claim", re.compile(r"501\s*\(\s*c\s*\)\s*\(\s*3\s*\)"), False),
    ("sector-safety-justice", re.compile(r"(?i)safety\s*&\s*justice"), False),
    (
        "sector-retired-name",
        re.compile(
            r"\b(?:finance|governance|work|culture)\s+sector\b"
            r"|\bsector\s*(?:name)?\s*[:=]\s*[\"']?(?:finance|governance|work|culture)\b",
            re.IGNORECASE,
        ),
        False,
    ),
)

# Applied to prose only: markdown with frontmatter masked (rendered code is
# visible text, so code spans and fences are NOT exempt), and HTML text
# nodes plus visible attribute values.
HARD_PROSE_RULES: Tuple[Rule, ...] = (
    ("crypto-token", re.compile(r"(?i)\btokens?\b"), False),
    ("crypto-wallet", re.compile(r"(?i)\bwallets?\b"), False),
    ("crypto-dao", re.compile(r"(?i)\bdao\b"), True),
    ("crypto-on-chain", re.compile(r"(?i)\bon[-\s]?chain\b"), False),
    ("crypto-generic", re.compile(r"(?i)\bcrypto(?:currenc(?:y|ies))?\b"), False),
    ("sector-transit", re.compile(r"(?i)\btransit\b"), True),
    ("sector-entertainment", re.compile(r"(?i)\bentertainment\b"), True),
)

WARN_FIGURE_RULES: Tuple[Tuple[str, "re.Pattern[str]"], ...] = (
    ("figure-dollar", re.compile(r"\$\s?\d")),
    ("figure-percent", re.compile(r"\d+(?:\.\d+)?\s?%")),
    ("figure-count", re.compile(r"\b\d{1,3}(?:,\d{3})+\b|\b\d{5,}\b")),
)

CITATION_MARK = re.compile(r"\bSRC-\d{3}\b")


def clean(text: str) -> str:
    """Remove zero-width characters that could split or hide a banned term."""
    return text.translate(ZERO_WIDTH)


def rule_hit(pattern: "re.Pattern[str]", skip_lower: bool, text: str) -> bool:
    for match in pattern.finditer(clean(text)):
        if not (skip_lower and match.group(0).islower()):
            return True
    return False


def strip_badge_decoration(text: str) -> str:
    stripped = clean(text).strip()
    stripped = re.sub(r"^[|>\-*\s]+|[|\s]+$", "", stripped)
    stripped = stripped.strip("*").strip()
    return re.sub(r"^[^\w]+|[^\w]+$", "", stripped)


def is_badge_text(text: str) -> bool:
    return strip_badge_decoration(text) in BADGE_WORDS


def load_register_ids() -> set:
    if not REGISTER_PATH.exists():
        return set()
    with REGISTER_PATH.open(encoding="utf-8") as handle:
        return {row["source_id"] for row in csv.DictReader(handle) if row.get("source_id")}


def line_is_cited(line: str, register_ids: set) -> bool:
    return any(mark.group(0) in register_ids for mark in CITATION_MARK.finditer(line))


class Finding:
    def __init__(self, tier: str, rule: str, path: str, line: int, excerpt: str):
        self.tier = tier
        self.rule = rule
        self.path = path
        self.line = line
        self.excerpt = excerpt

    def key(self, line_text: str) -> Tuple[str, str, str]:
        return (self.rule, self.path, line_hash(line_text))


def line_hash(line_text: str) -> str:
    return hashlib.sha256(clean(line_text).strip().encode("utf-8")).hexdigest()


def load_allowlist() -> List[Dict[str, str]]:
    if not ALLOWLIST_PATH.exists():
        return []
    entries = json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        raise SystemExit("allowlist must be a JSON list")
    for entry in entries:
        for field in ("rule", "path", "line_sha256", "justification", "added"):
            if not entry.get(field):
                raise SystemExit(f"allowlist entry missing {field}: {entry}")
    return entries


def mask_frontmatter(text: str) -> str:
    """Blank a leading YAML frontmatter block, preserving line offsets.

    Only frontmatter is masked: inline code and fenced blocks render as
    visible text on the site, so prose rules apply to them.
    """

    def blank(match: "re.Match[str]") -> str:
        return re.sub(r"[^\n]", " ", match.group(0))

    return re.sub(r"\A---\n.*?\n---\n", blank, text, count=1, flags=re.S)


def scan_lines(
    raw: str,
    prose: Optional[str],
    rel: str,
    findings: List[Finding],
    line_texts: Dict[Tuple[str, int], str],
    register_ids: set,
    warn_scope: bool,
    badge_scope: bool,
    retired_vocab_scope: bool = True,
) -> None:
    raw_lines = raw.splitlines()
    prose_lines = prose.splitlines() if prose is not None else None

    def record(tier: str, rule: str, number: int) -> None:
        findings.append(Finding(tier, rule, rel, number, raw_lines[number - 1].strip()[:90]))
        line_texts[(rel, number)] = raw_lines[number - 1]

    for rule, pattern, skip_lower in HARD_ALL_RULES:
        for number, line in enumerate(raw_lines, 1):
            if rule_hit(pattern, skip_lower, line):
                record("FAIL", rule, number)

    if prose_lines is not None:
        if retired_vocab_scope:
            for rule, pattern, skip_lower in HARD_PROSE_RULES:
                for number, line in enumerate(prose_lines, 1):
                    if rule_hit(pattern, skip_lower, line):
                        record("FAIL", rule, number)
        if badge_scope:
            for number, line in enumerate(prose_lines, 1):
                if is_badge_text(line):
                    record("FAIL", "status-badge-bare", number)
        if warn_scope:
            for rule, pattern in WARN_FIGURE_RULES:
                for number, line in enumerate(prose_lines, 1):
                    if pattern.search(clean(line)) and not line_is_cited(raw_lines[number - 1], register_ids):
                        record("WARN", rule, number)


class BuiltPageParser(HTMLParser):
    """Extracts visible text and attributes with registered data-source ancestry."""

    SPEAKABLE_ATTRS = (
        "alt", "title", "aria-label", "aria-description",
        "content", "placeholder", "value", "label",
    )

    def __init__(self, valid_source: Callable[[str], bool]) -> None:
        super().__init__()
        self.valid_source = valid_source
        self.chunks: List[Tuple[int, str, bool]] = []
        self.element_text: List[Tuple[int, str]] = []
        self._source_depth = 0
        self._stack: List[Tuple[str, bool, List[str], int]] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        attrs_dict = {name: value or "" for name, value in attrs}
        cited_here = self.valid_source(attrs_dict.get("data-source", "").strip())
        line = self.getpos()[0]
        effective_cited = self._source_depth > 0 or cited_here
        for attr in self.SPEAKABLE_ATTRS:
            attr_value = attrs_dict.get(attr, "").strip()
            if attr_value:
                self.chunks.append((line, attr_value, effective_cited))
        if tag in VOID_ELEMENTS:
            return
        if cited_here:
            self._source_depth += 1
        self._stack.append((tag, cited_here, [], line))

    def handle_endtag(self, tag: str) -> None:
        if tag in VOID_ELEMENTS:
            return
        if not any(entry[0] == tag for entry in self._stack):
            return
        while self._stack:
            open_tag, cited, texts, line = self._stack.pop()
            if cited:
                self._source_depth -= 1
            if open_tag == tag:
                direct = " ".join(t.strip() for t in texts if t.strip()).strip()
                if direct:
                    self.element_text.append((line, direct))
                break

    def handle_data(self, data: str) -> None:
        if not data.strip():
            return
        self.chunks.append((self.getpos()[0], data, self._source_depth > 0))
        if self._stack:
            self._stack[-1][2].append(data)


def scan_built_html(
    path: Path,
    rel: str,
    findings: List[Finding],
    line_texts: Dict[Tuple[str, int], str],
    register_ids: set,
) -> None:
    text = path.read_text(encoding="utf-8")
    raw_lines = text.splitlines()
    parser = BuiltPageParser(lambda value: bool(value) and value in register_ids)
    parser.feed(text)

    def source_line(number: int) -> str:
        return raw_lines[number - 1] if 0 < number <= len(raw_lines) else ""

    for number, chunk, cited in parser.chunks:
        for rule, pattern, skip_lower in HARD_ALL_RULES + HARD_PROSE_RULES:
            if rule_hit(pattern, skip_lower, chunk):
                findings.append(Finding("FAIL", rule, rel, number, chunk.strip()[:90]))
                line_texts[(rel, number)] = source_line(number)
        if not cited:
            for rule, pattern in WARN_FIGURE_RULES:
                if pattern.search(clean(chunk)):
                    findings.append(Finding("WARN", rule, rel, number, chunk.strip()[:90]))
                    line_texts[(rel, number)] = source_line(number)
    for number, direct_text in parser.element_text:
        if is_badge_text(direct_text):
            findings.append(Finding("FAIL", "status-badge-bare", rel, number, direct_text[:90]))
            line_texts[(rel, number)] = source_line(number)


def iter_source_files() -> List[Path]:
    files: List[Path] = []
    for scope in SOURCE_SCOPE:
        base = ROOT / scope
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file() and path.suffix.lower() in SCANNED_SUFFIXES:
                files.append(path)
    return files


def run_scan(built_dir: Optional[Path]) -> int:
    findings: List[Finding] = []
    line_texts: Dict[Tuple[str, int], str] = {}
    register_ids = load_register_ids()

    if built_dir is None:
        for path in iter_source_files():
            rel = str(path.relative_to(ROOT))
            try:
                raw = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                findings.append(Finding("FAIL", "non-utf8", rel, 1, "file is not valid UTF-8"))
                continue
            suffix = path.suffix.lower()
            if suffix == ".md":
                prose: Optional[str] = mask_frontmatter(raw)
            elif suffix in PROSE_SUFFIXES:
                prose = raw
            else:
                prose = None
            # The design-system packet is a quarantine ledger and design-vocabulary
            # surface that never renders on the site and is separately governed by
            # audit_design_handoff.py; retired-vocabulary prose rules would only
            # flag its own prohibition language. Distinctive-string rules
            # (HARD_ALL) still apply to it.
            in_render_scope = not rel.startswith("website/design-system/")
            scan_lines(
                raw,
                prose,
                rel,
                findings,
                line_texts,
                register_ids,
                warn_scope=prose is not None and in_render_scope,
                badge_scope=prose is not None,
                retired_vocab_scope=in_render_scope,
            )
    else:
        for path in sorted(built_dir.rglob("*")):
            if path.is_file() and path.suffix.lower() in {".html", ".htm"}:
                rel = str(path.relative_to(built_dir))
                scan_built_html(path, rel, findings, line_texts, register_ids)

    allowlist = load_allowlist()
    allowed = {(e["rule"], e["path"], e["line_sha256"]) for e in allowlist}
    kept: List[Finding] = []
    suppressed: List[Finding] = []
    for finding in findings:
        text = line_texts.get((finding.path, finding.line), finding.excerpt)
        if built_dir is None and finding.key(text) in allowed:
            suppressed.append(finding)
        else:
            kept.append(finding)

    fails = [f for f in kept if f.tier == "FAIL"]
    warns = [f for f in kept if f.tier == "WARN"]
    annotate = os.environ.get("GITHUB_ACTIONS") == "true"
    for finding in fails + warns:
        kind = "error" if finding.tier == "FAIL" else "warning"
        print(f"{finding.tier} {finding.rule} {finding.path}:{finding.line} — {finding.excerpt}")
        if annotate:
            print(
                f"::{kind} file={finding.path},line={finding.line},"
                f"title=content-audit:{finding.rule}::{finding.excerpt}"
            )
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path and (fails or warns):
        with open(summary_path, "a", encoding="utf-8") as handle:
            handle.write("\n### Website content audit\n\n| Tier | Rule | Location | Excerpt |\n|---|---|---|---|\n")
            for finding in fails + warns:
                excerpt = finding.excerpt.replace("|", "\\|")
                handle.write(
                    f"| {finding.tier} | {finding.rule} | {finding.path}:{finding.line} | {excerpt} |\n"
                )
    print(
        json.dumps(
            {
                "ok": not fails,
                "fail_count": len(fails),
                "warn_count": len(warns),
                "suppressed_count": len(suppressed),
                "mode": "built" if built_dir else "source",
            }
        )
    )
    return 1 if fails else 0


def allowlist_add(rule: str, rel: str, line_number: int, justification: str) -> int:
    path = ROOT / rel
    lines = path.read_text(encoding="utf-8").splitlines()
    if not 0 < line_number <= len(lines):
        raise SystemExit(f"{rel} has no line {line_number}")
    target = lines[line_number - 1]
    duplicates = [n for n, line in enumerate(lines, 1) if clean(line).strip() == clean(target).strip()]
    if len(duplicates) > 1:
        raise SystemExit(
            f"line {line_number} of {rel} is byte-identical to lines {duplicates}; "
            "an exception would cover them all — make the lines distinct or record "
            "a deliberate decision in the justification and re-run with a unique line"
        )
    entries = load_allowlist()
    entry = {
        "rule": rule,
        "path": rel,
        "line_sha256": line_hash(target),
        "justification": justification,
        "added": date.today().isoformat(),
    }
    entries.append(entry)
    entries.sort(key=lambda e: (e["path"], e["rule"], e["line_sha256"]))
    ALLOWLIST_PATH.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
    print(f"added allowlist entry for {rule} at {rel}:{line_number}")
    return 0


def selftest() -> int:
    import tempfile

    failures: List[str] = []

    def expect(condition: bool, label: str) -> None:
        if not condition:
            failures.append(label)

    def hits(rules: Tuple[Rule, ...], text: str) -> List[str]:
        return [rule for rule, pattern, skip in rules if rule_hit(pattern, skip, text)]

    expect("brand-unprice-name" in hits(HARD_ALL_RULES, "the Unprice era"), "unprice name fires")
    expect("brand-unprice-name" in hits(HARD_ALL_RULES, "THE UNPRICE ERA"), "all-caps unprice fires")
    expect(not hits(HARD_ALL_RULES, "unpriced goods stay unpriced"), "unpriced word is safe")
    expect("post-money-framing" in hits(HARD_ALL_RULES, "a post-scarcity world"), "post-scarcity fires")
    expect("post-money-framing" in hits(HARD_ALL_RULES, "a post scarcity world"), "space variant fires")
    expect("tax-deductibility-claim" in hits(HARD_ALL_RULES, "gifts are tax deductible"), "tax deductible fires")
    expect("tax-deductibility-claim" in hits(HARD_ALL_RULES, "claims tax deductibility"), "tax deductibility fires")
    expect("governance-voting-rights" in hits(HARD_ALL_RULES, "members gain Voting Rights"), "voting rights fires")
    expect("sector-retired-name" in hits(HARD_ALL_RULES, "the Finance sector overview"), "finance sector fires")
    expect("sector-retired-name" in hits(HARD_ALL_RULES, "sector: culture"), "sector frontmatter form fires")
    expect(not hits(HARD_ALL_RULES, "governance review of the finance controls"), "plain governance/finance safe")

    expect("crypto-token" in hits(HARD_PROSE_RULES, "buy our token today"), "token fires in prose")
    expect("crypto-token" in hits(HARD_PROSE_RULES, "a `token` in inline code"), "token in code span fires")
    expect("crypto-token" in hits(HARD_PROSE_RULES, "a to​ken with zero-width"), "zero-width split fires")
    expect("crypto-dao" in hits(HARD_PROSE_RULES, "run by a DAO"), "DAO fires")
    expect(not hits(HARD_PROSE_RULES, "the dao path is quarantined"), "lowercase dao path is safe")
    expect("crypto-on-chain" in hits(HARD_PROSE_RULES, "records kept on chain"), "on chain space variant fires")
    expect("sector-transit" in hits(HARD_PROSE_RULES, "the Transit sector"), "Transit fires")
    expect("sector-transit" in hits(HARD_PROSE_RULES, "TRANSIT"), "all-caps TRANSIT fires")
    expect(not hits(HARD_PROSE_RULES, "improve public transit access"), "lowercase transit is safe")
    expect("sector-entertainment" in hits(HARD_PROSE_RULES, "ENTERTAINMENT"), "all-caps ENTERTAINMENT fires")
    expect(not hits(HARD_PROSE_RULES, "leisure and entertainment options"), "lowercase entertainment is safe")

    expect(is_badge_text("| **Live** |"), "badge table cell fires")
    expect(is_badge_text("Approved"), "bare badge line fires")
    expect(is_badge_text("\U0001f7e2 Live"), "badge with icon prefix fires")
    expect(not is_badge_text("Approved by the founder"), "badge prose is safe")
    expect(not is_badge_text("Live music tonight"), "badge inside phrase is safe")

    figure_rules = [(r, p, False) for r, p in WARN_FIGURE_RULES]
    expect("figure-dollar" in hits(tuple(figure_rules), "costs $12 monthly"), "dollar figure warns")
    expect("figure-count" in hits(tuple(figure_rules), "48,210 have signed"), "signed count warns")
    expect(not hits(tuple(figure_rules), "see page 27 of 40"), "small counts are safe")

    expect(line_is_cited("figure per SRC-001 today", {"SRC-001"}), "registered citation suppresses")
    expect(not line_is_cited("figure per SRC-999 today", {"SRC-001"}), "unregistered citation does not suppress")

    masked = mask_frontmatter("---\ntoken: value\n---\nbody `token` text\n")
    expect("token: value" not in masked, "frontmatter is masked")
    expect("`token`" in masked, "code spans are not masked")
    expect(masked.count("\n") == 4, "masking preserves line count")

    html = (
        "<html><body><p>The treasury wallet is gone</p>"
        "<span data-source=\"SRC-001\">$40 grounded</span>"
        "<img data-source=\"SRC-001\" alt=\"chart\">"
        "<p>$99 unsourced</p><td><br>Funded</td>"
        "<input placeholder=\"Connect your wallet\">"
        "<div data-source=\"\">$7 empty-source</div>"
        "</body></html>"
    )
    findings: List[Finding] = []
    texts: Dict[Tuple[str, int], str] = {}
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "index.htm"
        page.write_text(html, encoding="utf-8")
        for path in sorted(Path(tmp).rglob("*")):
            if path.suffix.lower() in {".html", ".htm"}:
                scan_built_html(path, path.name, findings, texts, {"SRC-001"})
    rules_found = [f.rule for f in findings]
    expect("crypto-wallet" in rules_found, "built html wallet fires")
    expect(rules_found.count("crypto-wallet") == 2, "placeholder attribute is scanned")
    expect("status-badge-bare" in rules_found, "badge after void element fires")
    dollar_warns = [f for f in findings if f.rule == "figure-dollar"]
    expect(len(dollar_warns) == 2, "void/empty data-source do not suppress; registered ancestor does")

    if failures:
        for failure in failures:
            print(f"SELFTEST FAIL: {failure}")
        return 1
    print(json.dumps({"ok": True, "selftest": "passed"}))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--built", metavar="DIR", help="scan built HTML output under DIR")
    parser.add_argument("--selftest", action="store_true", help="run embedded rule fixtures")
    parser.add_argument(
        "--allowlist-add",
        nargs=4,
        metavar=("RULE", "PATH", "LINE", "JUSTIFICATION"),
        help="record a reviewed exception for RULE at PATH:LINE",
    )
    args = parser.parse_args()

    if args.selftest:
        return selftest()
    if args.allowlist_add:
        rule, rel, line_number, justification = args.allowlist_add
        return allowlist_add(rule, rel, int(line_number), justification)
    built_dir = Path(args.built).resolve() if args.built else None
    if built_dir is not None and not built_dir.is_dir():
        raise SystemExit(f"built directory not found: {built_dir}")
    return run_scan(built_dir)


if __name__ == "__main__":
    raise SystemExit(main())

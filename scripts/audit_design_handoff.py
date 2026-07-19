#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile
from datetime import datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Set
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "website" / "design-system"
RECEIPT = PACKET / "SOURCE_RECEIPT.json"
REFERENCE = PACKET / "reference" / "index.html"
TOKENS = PACKET / "tokens.css"
COMPONENTS = PACKET / "components.css"
ICON_SPRITE = PACKET / "icons" / "icons.svg"
MANIFEST = ROOT / "website" / "assets" / "brand" / "ASSET_MANIFEST.json"
ARCHIVE_ENV = "UNCOST_DESIGN_HANDOFF_ARCHIVE"
EXTRACTED_ENV = "UNCOST_DESIGN_HANDOFF_EXTRACTED"
FROZEN_ARCHIVE_ROOT_PREFIX = "uncost-design-system/"

FROZEN_SOURCE_PAIRS = (
    {
        "logical_source_path": "project/colors_and_type.css",
        "source_sha256": "cffee798868671c67d7d86197e43444ea198e7850dc34ecf3246e82251d76b52",
        "output_path": "website/design-system/tokens.css",
        "mode": "transform",
    },
    {
        "logical_source_path": "project/ui_kits/components.css",
        "source_sha256": "6ae252e2f87b169d261af0dc1707fbe999faa81c4458be1f8c7c497a1d8bcf24",
        "output_path": "website/design-system/components.css",
        "mode": "transform",
    },
    {
        "logical_source_path": "project/assets/icons/icons.svg",
        "source_sha256": "30b694a2d8fd28c22d8e391adfee14e4678199efba39bd5f9f0271b6703ed505",
        "output_path": "website/design-system/icons/icons.svg",
        "mode": "curate",
    },
)

CONTEXT_SCOPE = (
    ":is(.block--ink, .block--clay, .block--ink-blue, .block--wheat, "
    ".block--sage, .site-footer)"
)
CONTRAST_MATRIX = {
    ".block--ink": {
        "background": "ink",
        "meta": "cream",
        "link": "cream",
        "link-hover": "wheat",
        "focus": "wheat",
    },
    ".block--clay": {
        "background": "clay",
        "meta": "cream",
        "link": "cream",
        "link-hover": "white",
        "focus": "ink",
    },
    ".block--ink-blue": {
        "background": "ink-blue",
        "meta": "cream",
        "link": "cream",
        "link-hover": "white",
        "focus": "wheat",
    },
    ".block--wheat": {
        "background": "wheat",
        "meta": "ink",
        "link": "ink",
        "link-hover": "earth-ink",
        "focus": "ink",
    },
    ".block--sage": {
        "background": "sage",
        "meta": "ink",
        "link": "ink",
        "link-hover": "earth-ink",
        "focus": "ink",
    },
    ".site-footer": {
        "background": "ink",
        "meta": "cream",
        "link": "cream",
        "link-hover": "wheat",
        "focus": "wheat",
    },
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def add_error(errors: List[str], code: str, detail: str) -> None:
    errors.append(f"{code}:{detail}")


def required_path(path: Path, label: str, errors: List[str]) -> None:
    if not path.exists():
        add_error(errors, "REQUIRED_MISSING", f"{label}:{path}")


def parse_hex_tokens(css_text: str) -> Dict[str, str]:
    return {
        name: value.lower()
        for name, value in re.findall(
            r"--([a-z0-9-]+)\s*:\s*(#[0-9a-fA-F]{6})\s*;", css_text
        )
    }


def css_declarations(css_text: str, selector: str) -> Dict[str, str]:
    normalized_css = re.sub(r"\s+", " ", css_text)
    normalized_selector = re.sub(r"\s+", " ", selector)
    match = re.search(
        re.escape(normalized_selector) + r"\s*\{([^}]*)\}", normalized_css, re.S
    )
    if not match:
        return {}
    return {
        name: value.strip()
        for name, value in re.findall(r"([a-zA-Z-]+)\s*:\s*([^;]+);", match.group(1))
    }


def relative_luminance(hex_color: str) -> float:
    channels = [int(hex_color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [
        channel / 12.92
        if channel <= 0.04045
        else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(foreground: str, background: str) -> float:
    lighter, darker = sorted(
        (relative_luminance(foreground), relative_luminance(background)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


def validate_contrast_matrix(errors: List[str]) -> int:
    tokens_text = TOKENS.read_text(encoding="utf-8")
    components_text = COMPONENTS.read_text(encoding="utf-8")
    colors = parse_hex_tokens(tokens_text)
    checked = 0

    required_rules = {
        f"{CONTEXT_SCOPE} .meta": {"color": "var(--context-meta)"},
        f"{CONTEXT_SCOPE} a:not(.button)": {"color": "var(--context-link)"},
        f"{CONTEXT_SCOPE} a:not(.button):hover": {
            "color": "var(--context-link-hover)"
        },
        f"{CONTEXT_SCOPE} :where(a, button, input, select, textarea):focus-visible": {
            "outline-color": "var(--context-focus)"
        },
    }
    for selector, expected_declarations in required_rules.items():
        declarations = css_declarations(components_text, selector)
        if not declarations:
            add_error(errors, "ACCESSIBILITY_CONTEXT_RULE_MISSING", selector)
            continue
        for property_name, expected_value in expected_declarations.items():
            if declarations.get(property_name) != expected_value:
                add_error(
                    errors,
                    "ACCESSIBILITY_CONTEXT_DECLARATION",
                    f"{selector}:{property_name}:{expected_value}",
                )

    for selector, roles in CONTRAST_MATRIX.items():
        declarations = css_declarations(components_text, selector)
        if not declarations:
            add_error(errors, "ACCESSIBILITY_SURFACE_RULE_MISSING", selector)
            continue
        background_name = roles["background"]
        if declarations.get("background") != f"var(--{background_name})":
            add_error(
                errors,
                "ACCESSIBILITY_SURFACE_BACKGROUND",
                f"{selector}:var(--{background_name})",
            )
        background = colors.get(background_name)
        if not background:
            add_error(errors, "ACCESSIBILITY_COLOR_TOKEN_MISSING", background_name)
            continue
        for role in ("meta", "link", "link-hover", "focus"):
            foreground_name = roles[role]
            property_name = f"--context-{role}"
            if declarations.get(property_name) != f"var(--{foreground_name})":
                add_error(
                    errors,
                    "ACCESSIBILITY_CONTEXT_TOKEN",
                    f"{selector}:{property_name}:var(--{foreground_name})",
                )
            foreground = colors.get(foreground_name)
            if not foreground:
                add_error(errors, "ACCESSIBILITY_COLOR_TOKEN_MISSING", foreground_name)
                continue
            minimum = 3.0 if role == "focus" else 4.5
            ratio = contrast_ratio(foreground, background)
            checked += 1
            if ratio + 1e-9 < minimum:
                add_error(
                    errors,
                    "ACCESSIBILITY_CONTRAST",
                    f"{selector}:{role}:{ratio:.3f}<{minimum:.1f}",
                )
    return checked


def validate_source_transformations(
    receipt: Dict[str, object], errors: List[str]
) -> str:
    raw_entries = receipt.get("source_transformations", [])
    entries = raw_entries if isinstance(raw_entries, list) else []
    if len(entries) != len(FROZEN_SOURCE_PAIRS):
        add_error(errors, "SOURCE_TRANSFORMATION_COUNT", str(len(entries)))

    by_output = {
        entry.get("output_path"): entry
        for entry in entries
        if isinstance(entry, dict) and entry.get("output_path")
    }
    for expected in FROZEN_SOURCE_PAIRS:
        entry = by_output.get(expected["output_path"])
        if not entry:
            add_error(errors, "SOURCE_TRANSFORMATION_MISSING", expected["output_path"])
            continue
        for key in ("logical_source_path", "source_sha256", "output_path", "mode"):
            if entry.get(key) != expected[key]:
                add_error(
                    errors,
                    "SOURCE_TRANSFORMATION_IMMUTABLE_MISMATCH",
                    f"{expected['output_path']}:{key}:{entry.get(key)}!={expected[key]}",
                )
        output_path = ROOT / expected["output_path"]
        if output_path.exists() and entry.get("output_sha256") != sha256(output_path):
            add_error(
                errors,
                "SOURCE_TRANSFORMATION_OUTPUT_HASH",
                expected["output_path"],
            )

    verification = receipt.get("source_verification", {})
    expected_verification = {
        "default_mode": "externally-verified-frozen-values",
        "archive_env": ARCHIVE_ENV,
        "extracted_env": EXTRACTED_ENV,
        "extracted_root_policy": "exact-wrapper-or-frozen-prefix-stripped",
    }
    if not isinstance(verification, dict):
        add_error(errors, "SOURCE_VERIFICATION_MISSING", "source_verification")
    else:
        for key, expected in expected_verification.items():
            if verification.get(key) != expected:
                add_error(
                    errors,
                    "SOURCE_VERIFICATION_FIELD",
                    f"{key}:{verification.get(key)}!={expected}",
                )

    archive = receipt.get("archive", {})
    if not isinstance(archive, dict):
        archive = {}
    archive_root_prefix_valid = archive.get("root_prefix") == FROZEN_ARCHIVE_ROOT_PREFIX
    if not archive_root_prefix_valid:
        add_error(
            errors,
            "SOURCE_ARCHIVE_ROOT_PREFIX",
            f"{archive.get('root_prefix')}!={FROZEN_ARCHIVE_ROOT_PREFIX}",
        )

    modes: List[str] = []
    archive_value = os.environ.get(ARCHIVE_ENV)
    extracted_value = os.environ.get(EXTRACTED_ENV)
    archive_path = Path(archive_value).expanduser() if archive_value else None
    extracted_path = Path(extracted_value).expanduser() if extracted_value else None

    if archive_path:
        archive_error_count = len(errors)
        if not archive_path.is_file():
            add_error(errors, "SOURCE_ARCHIVE_MISSING", str(archive_path))
        else:
            if archive_path.stat().st_size != archive.get("bytes"):
                add_error(errors, "SOURCE_ARCHIVE_SIZE", str(archive_path))
            if sha256(archive_path) != archive.get("sha256"):
                add_error(errors, "SOURCE_ARCHIVE_HASH", str(archive_path))
            try:
                with zipfile.ZipFile(archive_path) as frozen_zip:
                    members = [info for info in frozen_zip.infolist() if not info.is_dir()]
                    if len(members) != archive.get("member_count"):
                        add_error(
                            errors,
                            "SOURCE_ARCHIVE_MEMBER_COUNT",
                            f"{len(members)}!={archive.get('member_count')}",
                        )
                    names = {info.filename for info in members}
                    for expected in FROZEN_SOURCE_PAIRS:
                        archive_member = (
                            FROZEN_ARCHIVE_ROOT_PREFIX
                            + expected["logical_source_path"]
                        )
                        if archive_member not in names:
                            add_error(
                                errors,
                                "SOURCE_ARCHIVE_MEMBER_MISSING",
                                archive_member,
                            )
                            continue
                        actual = sha256_bytes(frozen_zip.read(archive_member))
                        if actual != expected["source_sha256"]:
                            add_error(
                                errors,
                                "SOURCE_ARCHIVE_MEMBER_HASH",
                                f"{archive_member}:{actual}",
                            )
            except zipfile.BadZipFile:
                add_error(errors, "SOURCE_ARCHIVE_INVALID", str(archive_path))
        modes.append(
            "archive-mechanically-verified"
            if archive_root_prefix_valid and len(errors) == archive_error_count
            else "archive-verification-failed"
        )

    if extracted_path:
        extracted_error_count = len(errors)
        if not extracted_path.is_dir():
            add_error(errors, "SOURCE_EXTRACTED_MISSING", str(extracted_path))
        else:
            exact_wrapper_root = extracted_path / FROZEN_ARCHIVE_ROOT_PREFIX.rstrip("/")
            if exact_wrapper_root.is_dir():
                source_root = exact_wrapper_root
            elif (extracted_path / "project").is_dir():
                source_root = extracted_path
            else:
                source_root = None
                add_error(
                    errors,
                    "SOURCE_EXTRACTED_ROOT_SHAPE",
                    f"{extracted_path}:expected exact {FROZEN_ARCHIVE_ROOT_PREFIX} wrapper or stripped project/ root",
                )
            if source_root:
                for expected in FROZEN_SOURCE_PAIRS:
                    source_path = source_root / expected["logical_source_path"]
                    if not source_path.is_file():
                        add_error(
                            errors,
                            "SOURCE_EXTRACTED_MEMBER_MISSING",
                            str(source_path),
                        )
                        continue
                    actual = sha256(source_path)
                    if actual != expected["source_sha256"]:
                        add_error(
                            errors,
                            "SOURCE_EXTRACTED_MEMBER_HASH",
                            f"{expected['logical_source_path']}:{actual}",
                        )
        modes.append(
            "extracted-tree-mechanically-verified"
            if len(errors) == extracted_error_count
            else "extracted-tree-verification-failed"
        )

    return "+".join(modes) if modes else "externally-verified-frozen-values"


def validate_changed_file_coverage(
    receipt: Dict[str, object], output_paths: Set[str], errors: List[str]
) -> str:
    coverage = receipt.get("changed_file_coverage", {})
    if not isinstance(coverage, dict):
        add_error(errors, "CHANGED_FILE_COVERAGE_MISSING", "changed_file_coverage")
        return "unavailable"

    base_commit = coverage.get("base_commit")
    review_branch = coverage.get("review_branch")
    if coverage.get("mode") != "git-diff-output-inventory":
        add_error(errors, "CHANGED_FILE_COVERAGE_MODE", str(coverage.get("mode")))
    if base_commit != receipt.get("base", {}).get("base_commit"):
        add_error(errors, "CHANGED_FILE_COVERAGE_BASE", str(base_commit))
    if not isinstance(base_commit, str) or not isinstance(review_branch, str):
        return "unavailable"

    event_path = os.environ.get("GITHUB_EVENT_PATH")
    diff_args: List[str] = []
    mode = "not-applicable-outside-review-branch"
    if event_path and Path(event_path).is_file():
        try:
            event = json.loads(Path(event_path).read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            event = {}
        pull_request = event.get("pull_request", {})
        if pull_request:
            event_base = pull_request.get("base", {}).get("sha")
            event_head = pull_request.get("head", {}).get("sha")
            if event_base and event_head:
                diff_args = [f"{event_base}...{event_head}"]
                mode = f"pull-request-git-diff:{event_base}...{event_head}"

    if not diff_args:
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        ).stdout.strip()
        if branch == review_branch:
            diff_args = [base_commit]
            mode = f"review-branch-working-tree-diff:{base_commit}"

    if not diff_args:
        return mode

    changed = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMRD", *diff_args],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if changed.returncode != 0:
        add_error(errors, "CHANGED_FILE_GIT_DIFF", changed.stderr.strip())
        return "failed"
    changed_paths = {line for line in changed.stdout.splitlines() if line}

    if mode.startswith("review-branch-working-tree"):
        untracked = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if untracked.returncode != 0:
            add_error(errors, "CHANGED_FILE_GIT_UNTRACKED", untracked.stderr.strip())
        else:
            changed_paths.update(line for line in untracked.stdout.splitlines() if line)
    else:
        # Outside the frozen handoff review branch this receipt inventories only
        # the design-system packet, so coverage can only be enforced for packet
        # paths; repository-wide changes are governed by audit_repository.py.
        changed_paths = {
            path
            for path in changed_paths
            if path.startswith("website/design-system/")
        }

    for path in sorted(changed_paths - output_paths):
        add_error(errors, "CHANGED_FILE_NOT_IN_RECEIPT", path)
    return mode


class ReferenceParser(HTMLParser):
    def __init__(self, errors: List[str]) -> None:
        super().__init__()
        self.errors = errors
        self.hrefs: List[str] = []
        self.srcs: List[str] = []
        self.button_types: List[str] = []
        self.form_attrs: List[Dict[str, str]] = []
        self.ids: Set[str] = set()
        self.external_links: List[str] = []
        self.inline_event_handlers: List[str] = []
        self.robots_directives: List[Set[str]] = []
        self.script_count: int = 0
        self.action_forms: int = 0

    def handle_starttag(self, tag: str, attrs: List[tuple[str, str]]) -> None:
        attrs_dict = {k: v for k, v in attrs if v is not None}
        for attr_name, _ in attrs:
            if attr_name.lower().startswith("on"):
                self.inline_event_handlers.append(f"{tag}:{attr_name}")
        if tag == "script":
            self.script_count += 1
        if tag == "meta" and attrs_dict.get("name", "").lower() == "robots":
            directives = {
                directive
                for directive in re.split(r"[\s,]+", attrs_dict.get("content", "").lower())
                if directive
            }
            self.robots_directives.append(directives)
        if tag == "a" and "href" in attrs_dict:
            self.hrefs.append(attrs_dict["href"])
            if attrs_dict["href"].startswith(("http://", "https://")):
                self.external_links.append(attrs_dict["href"])
        if tag == "img":
            src = attrs_dict.get("src", "").strip()
            self.srcs.append(src)
            if not src:
                add_error(self.errors, "REFERENCE_IMG_MISSING_SRC", "<img without src>")
            if attrs_dict.get("alt", "").strip() == "":
                add_error(self.errors, "REFERENCE_IMG_MISSING_ALT", src or "<img without src>")
        if tag == "button":
            self.button_types.append(attrs_dict.get("type", "submit").lower())
        if tag == "form":
            self.form_attrs.append(attrs_dict)
            if "action" in attrs_dict and (attrs_dict["action"] or "").strip() != "":
                self.action_forms += 1
        if "id" in attrs_dict:
            self.ids.add(attrs_dict["id"])


def main() -> int:
    errors: List[str] = []

    required_path(RECEIPT, "SOURCE_RECEIPT", errors)
    required_path(REFERENCE, "reference index", errors)
    required_path(TOKENS, "tokens.css", errors)
    required_path(COMPONENTS, "components.css", errors)
    required_path(ICON_SPRITE, "icon sprite", errors)
    required_path(MANIFEST, "asset manifest", errors)

    if errors:
        print(json.dumps({"ok": False, "errors": errors}))
        return 1

    packet_expected_files = [
        "README.md",
        "AUTHORITY.md",
        "EXCLUSIONS.md",
        "SOURCE_RECEIPT.json",
        "fonts/Inter-OFL.txt",
        "fonts/RobotoCondensed-OFL.txt",
        "fonts/Inter-latin-variable.woff2",
        "fonts/RobotoCondensed-latin-variable.woff2",
        "fonts/README.md",
        "icons/icons.svg",
        "tokens.css",
        "components.css",
        "reference/index.html",
    ]

    for rel in packet_expected_files:
        required_path(PACKET / rel, rel, errors)

    if errors:
        print(json.dumps({"ok": False, "errors": errors}))
        return 1

    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    reference_text = REFERENCE.read_text(encoding="utf-8")
    for required_field in [
        "issue",
        "generated_at",
        "archive",
        "source_transformations",
        "source_verification",
        "changed_file_coverage",
        "outputs",
        "canonical_references",
    ]:
        if required_field not in receipt:
            add_error(errors, "RECEIPT_MISSING_FIELD", required_field)

    generated_at = receipt.get("generated_at")
    if not isinstance(generated_at, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|\+07:00)", generated_at
    ):
        add_error(errors, "RECEIPT_GENERATED_AT_ZONE", str(generated_at))
    else:
        parsed_generated_at = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
        if parsed_generated_at.utcoffset() not in {timedelta(0), timedelta(hours=7)}:
            add_error(errors, "RECEIPT_GENERATED_AT_ZONE", generated_at)

    if "archive" in receipt:
        archive = receipt["archive"]
        for key in ["filename", "sha256", "bytes", "member_count", "root_prefix"]:
            if key not in archive:
                add_error(errors, "RECEIPT_ARCHIVE_FIELD", key)

    outputs = receipt.get("outputs", [])
    if not isinstance(outputs, list):
        outputs = []
        add_error(errors, "RECEIPT_OUTPUTS_TYPE", "outputs must be a list")
    seen_output_paths: Set[str] = set()
    for member in outputs:
        if not isinstance(member, dict):
            add_error(errors, "RECEIPT_OUTPUT_TYPE", str(member))
            continue
        rel = member.get("path")
        if not isinstance(rel, str) or not rel:
            add_error(errors, "RECEIPT_OUTPUT_MISSING_PATH", "output")
            continue
        if rel in seen_output_paths:
            add_error(errors, "RECEIPT_OUTPUT_DUPLICATE", rel)
        seen_output_paths.add(rel)
        if rel == "website/design-system/SOURCE_RECEIPT.json":
            if "sha256" in member:
                add_error(errors, "RECEIPT_SELF_HASH_FORBIDDEN", str(member.get("sha256")))
            if member.get("hash_mode") != "external-post-commit-receipt":
                add_error(errors, "RECEIPT_SELF_HASH_MODE", str(member.get("hash_mode")))
            continue
        member_path = ROOT / rel
        if not member_path.exists():
            add_error(errors, "RECEIPT_OUTPUT_MISSING_FILE", rel)
            continue
        actual = sha256(member_path)
        expected = member.get("sha256")
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
            add_error(errors, "RECEIPT_OUTPUT_HASH_MISSING", rel)
        elif actual != expected:
            add_error(errors, "RECEIPT_OUTPUT_HASH_MISMATCH", f"{rel}:{expected}!={actual}")

    source_verification_mode = validate_source_transformations(receipt, errors)

    text_checks = [
        ("external_url_in_tokens", f"{TOKENS}", [r"https?://"]),
        ("external_url_in_components", f"{COMPONENTS}", [r"https?://"]),
        ("external_url_in_reference", f"{REFERENCE}", [r"https?://"]),
        ("cdn_or_api_text", f"{ROOT}/website/design-system/fonts/README.md", [r"fonts.googleapis.com"]),
    ]
    for label, file_path, patterns in text_checks:
        text = (Path(file_path)).read_text(encoding="utf-8")
        for pattern in patterns:
            if re.search(pattern, text):
                add_error(errors, "REJECTED_TEXT_PATTERN", f"{label}:{pattern}")
    for url in re.findall(r"https?://[^\"'>\\s]+", (ICON_SPRITE).read_text(encoding="utf-8")):
        if "w3.org" not in url:
            add_error(errors, "REJECTED_TEXT_PATTERN", f"external_url_in_svg:{url}")

    prohibited = [
        "money is broken",
        "dao",
        "wallet",
        "on-chain",
        "donate",
        "pledge-total",
        "pledge total",
    ]
    for needle in prohibited:
        if re.search(re.escape(needle), reference_text.lower()):
            add_error(errors, "REJECTED_REFERENCE_TEXT", needle)

    parser = ReferenceParser(errors)
    parser.feed(reference_text)

    for href in parser.hrefs:
        if href.startswith("#") or href.startswith("mailto:"):
            continue
        if href.lower().startswith("javascript:"):
            add_error(errors, "REFERENCE_JAVASCRIPT_LINK", href)
            continue
        if href.startswith(("#", "http://", "https://", "tel:")):
            continue
        parsed = urlparse(href)
        target = (REFERENCE.parent / parsed.path).resolve()
        try:
            target.relative_to(ROOT)
        except ValueError:
            add_error(errors, "REFERENCE_LINK_ESCAPE", href)
        if not target.exists():
            add_error(errors, "REFERENCE_LINK_MISSING", href)

    for src in parser.srcs:
        if src.startswith("data:") or src.startswith("http://") or src.startswith("https://"):
            continue
        if src.startswith("#"):
            continue
        target = (REFERENCE.parent / src).resolve()
        try:
            target.relative_to(ROOT)
        except ValueError:
            add_error(errors, "REFERENCE_SRC_ESCAPE", src)
        if not target.exists():
            add_error(errors, "REFERENCE_SRC_MISSING", src)

    if parser.external_links:
        for link in parser.external_links:
            add_error(errors, "REFERENCE_EXTERNAL_LINK", link)

    if not any({"noindex", "nofollow"}.issubset(value) for value in parser.robots_directives):
        add_error(errors, "REFERENCE_ROBOTS_DIRECTIVE", "noindex,nofollow")
    if parser.script_count:
        add_error(errors, "REFERENCE_SCRIPT_PRESENT", str(parser.script_count))
    for handler in parser.inline_event_handlers:
        add_error(errors, "REFERENCE_INLINE_EVENT_HANDLER", handler)

    if "top" not in parser.ids or "movement" not in parser.ids or "assembly" not in parser.ids:
        add_error(errors, "REFERENCE_ID_MISSING", "required section ids")

    if any(t == "submit" for t in parser.button_types):
        add_error(errors, "REFERENCE_FORM_ACTION", "submit button present in reference")

    for form in parser.form_attrs:
        if "action" in form:
            add_error(errors, "REFERENCE_FORM_ACTION", "form action present")

    # Ensure all button controls are explicitly non-submitting in this packet.
    if any("<button" in line and "type=" not in line.lower() for line in reference_text.splitlines()):
        add_error(errors, "REFERENCE_NONCOMPLIANT_BUTTON", "button missing type attribute")

    # No form submits, no form action endpoints.
    if parser.action_forms > 0:
        add_error(errors, "REFERENCE_FORM_ACTION", "form action attribute detected")
    for form in parser.form_attrs:
        if form.get("method", "get").lower() not in {"", "get"}:
            add_error(errors, "REFERENCE_FORM_METHOD", f"unsupported method:{form.get('method')}")

    # Validate referenced assets against manifest and alt text.
    manifest_data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest_items = manifest_data.get("assets", [])
    manifest_index = {item["path"]: item for item in manifest_items if "path" in item}
    if len(manifest_index) != 86:
        add_error(errors, "MANIFEST_COUNT_MISMATCH", f"assets={len(manifest_index)}")

    critical_assets = {
        "website/assets/brand/logos/mark-only-final-light.png": {
            "hash": "2f5ba137e19809ba07479dcb77f15f854f5d7740e2f4036d5e238b5fcc7d3a45"
        },
        "website/assets/brand/robots/01_waving_transparent.png": {
            "hash": "915e7023a243f36797fbefd08d78ad67739dea1cec95f91bc08b30260e4d31b1"
        },
        "website/assets/brand/sectors/sector-energy.png": {
            "hash": "c945e16e62d449398942a44a38444b42d7807edf430e53a5563fe33d4c9308da"
        },
        "website/assets/brand/sectors/sector-food.png": {
            "hash": "aa77b2f44b65ee6ae130048617045154d0a659d4c3833694051c6ca8fb9e264d"
        },
        "website/assets/brand/sectors/sector-shelter.png": {
            "hash": "432da5fb1bb20ee730a6357084290c78c4c281e09111f47be81019293516dcae"
        },
    }
    for path, checks in critical_assets.items():
        item = manifest_index.get(path)
        if not item:
            add_error(errors, "MANIFEST_MISSING_ASSET", path)
            continue
        if item.get("sha256") != checks["hash"]:
            add_error(errors, "MANIFEST_HASH_MISMATCH", f"{path}:{checks['hash']}")

    # Ensure icon sprite excludes restricted glyph IDs.
    sprite = ICON_SPRITE.read_text(encoding="utf-8")
    symbol_ids = re.findall(r'<symbol[^>]+id="([^"]+)"', sprite)
    for banned in ("vote", "dollar"):
        for symbol_id in symbol_ids:
            if banned in symbol_id:
                add_error(errors, "ICONSET_BANNED_SYMBOL", symbol_id)

    css_text = (PACKET / "components.css").read_text(encoding="utf-8")
    if "--focus-visible" not in css_text.lower() and ":focus-visible" not in css_text:
        add_error(errors, "ACCESSIBILITY_MISSING_FOCUS", ":focus-visible")
    if "prefers-reduced-motion" not in css_text:
        add_error(errors, "ACCESSIBILITY_MISSING_REDUCED_MOTION", "prefers-reduced-motion")
    contrast_pairs = validate_contrast_matrix(errors)

    # Ensure required references exist in receipt and checksums match.
    for rel, expected in {
        "website/design-system/tokens.css": sha256(TOKENS),
        "website/design-system/components.css": sha256(COMPONENTS),
        "website/design-system/icons/icons.svg": sha256(ICON_SPRITE),
        "website/design-system/reference/index.html": sha256(REFERENCE),
    }.items():
        found = False
        for entry in receipt.get("outputs", []):
            if entry.get("path") == rel:
                found = True
                if entry.get("sha256") != expected:
                    add_error(errors, "RECEIPT_HASH_MISMATCH", rel)
                break
        if not found:
            add_error(errors, "RECEIPT_OUTPUT_MISSING", rel)

    # Parse CSS url() references and ensure local files exist.
    for text_path in (TOKENS, COMPONENTS):
        for url in re.findall(r"url\(([^)]+)\)", text_path.read_text(encoding="utf-8")):
            candidate = url.strip().strip("'\"")
            if candidate.startswith("data:") or candidate.startswith("http://") or candidate.startswith("https://"):
                continue
            target = (text_path.parent / candidate).resolve()
            try:
                target.relative_to(ROOT)
            except ValueError:
                add_error(errors, "CSS_URL_ESCAPE", f"{text_path}:{candidate}")
            if not target.exists():
                add_error(errors, "CSS_URL_MISSING", f"{text_path}:{candidate}")

    expected_paths = seen_output_paths
    required_files = [
        ".github/workflows/content-audit.yml",
        "scripts/audit_design_handoff.py",
        "scripts/audit_repository.py",
        "website/design-system/README.md",
        "website/design-system/AUTHORITY.md",
        "website/design-system/EXCLUSIONS.md",
        "website/design-system/tokens.css",
        "website/design-system/components.css",
        "website/design-system/icons/icons.svg",
        "website/design-system/reference/index.html",
        "website/design-system/fonts/README.md",
        "website/design-system/fonts/Inter-OFL.txt",
        "website/design-system/fonts/RobotoCondensed-OFL.txt",
        "website/design-system/fonts/Inter-latin-variable.woff2",
        "website/design-system/fonts/RobotoCondensed-latin-variable.woff2",
        "website/design-system/SOURCE_RECEIPT.json",
    ]
    for rel in required_files:
        if rel not in expected_paths:
            add_error(errors, "RECEIPT_OUTPUT_MISSING", rel)

    for rel in expected_paths:
        if not (ROOT / rel).exists():
            add_error(errors, "RECEIPT_OUTPUT_PATH_MISSING", rel)
        else:
            if rel == "website/design-system/SOURCE_RECEIPT.json":
                continue
            member = next(
                (
                    entry
                    for entry in outputs
                    if isinstance(entry, dict) and entry.get("path") == rel
                ),
                {},
            )
            if member and member.get("sha256"):
                if member["sha256"] != sha256(ROOT / rel):
                    add_error(errors, "RECEIPT_OUTPUT_HASH_MISMATCH", rel)

    coverage_mode = validate_changed_file_coverage(receipt, expected_paths, errors)

    result = {
        "ok": not errors,
        "errors": errors,
        "counts": {
            "outputs": len(receipt.get("outputs", [])),
            "manifest_assets": len(manifest_items),
            "contrast_pairs": contrast_pairs,
        },
        "verification": {
            "source_transformations": source_verification_mode,
            "changed_file_coverage": coverage_mode,
        },
    }
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

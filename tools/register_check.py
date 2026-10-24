#!/usr/bin/env python3
"""Register check — every reader of sources/register.csv parses it as CSV.

Quoted cells in the register hold commas: titles, notes, and every filled
`checked_by` ("agent-checked, human-approved: Matt <UTC timestamp>"). A reader
that splits a row on commas reads the wrong cell. These are the readers that
read columns, and each must read every cell of every row exactly as Python's
csv module does:

  REGISTER_JS  website/src/_data/register.js: parseCsv, and load(), the site's
               data (every page, the search index and the Cost Watch feed read
               the register through it)
  GUARD        register.js reportedConfidenceRows(), the news-label guard in
               website/eleventy.config.js (no "reported" confidence)
  AUDIT_IDS    scripts/audit_website.py load_register_ids() (csv.DictReader)
  AUDIT_HOSTS  scripts/audit_website.py registered_source_hosts() (a URL regex
               over the whole file)

Two more read the file as text, not columns: scripts/audit_repository.py (the
control hash, whitespace, the final newline) and tools/restatement_check.py
(archives sources/ for a rebuild, which reads it through register.js).

  CHECKED_BY   load() accepts blank and the exact format, with or without
               fractional seconds, and fails on any other value or when the
               column is missing.

    python3 tools/register_check.py             # the real register, every reader
    python3 tools/register_check.py --selftest  # tools/fixtures/register/

The fixture is four real rows with SRC-017's checked_by filled, so it holds a
quoted comma; its header must equal the register's.

Exit 0 when ok, 1 on any error.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import io
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTER = ROOT / "sources" / "register.csv"
FIXTURE = ROOT / "tools" / "fixtures" / "register" / "checked-by.csv"
EXAMPLE = "agent-checked, human-approved: Matt 2026-10-31T02:14:07Z"

# Runs register.js on one file and prints what each of its readers saw.
NODE = r"""
const fs = require("node:fs");
console.log = (...a) => process.stderr.write(a.join(" ") + "\n");  // load()'s build line
const reg = require(process.argv[1]);
const text = fs.readFileSync(process.argv[2], "utf8");
const out = { parsed: reg.parseCsv(text), reported: reg.reportedConfidenceRows(text) };
try { out.loaded = reg.load(text).all; } catch (e) { out.error = e.message; }
process.stdout.write(JSON.stringify(out));
"""


def node_read(path: pathlib.Path) -> dict:
    res = subprocess.run(
        ["node", "-e", NODE, str(ROOT / "website" / "src" / "_data" / "register.js"), str(path)],
        cwd=ROOT / "website", capture_output=True, text=True, env=dict(os.environ),
    )
    if res.returncode != 0:
        raise RuntimeError(f"node failed: {res.stderr.strip()}")
    return json.loads(res.stdout)


def audit_website_module():
    spec = importlib.util.spec_from_file_location("audit_website", ROOT / "scripts" / "audit_website.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check(path: pathlib.Path, planted_reported: int | None = None) -> list[str]:
    """Every column reader against one register file; returns the errors."""
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    oracle = [r for r in csv.reader(io.StringIO(text, newline=""))]
    header, rows = oracle[0], oracle[1:]
    name = path.name

    seen = node_read(path)
    # REGISTER_JS: the parser, cell for cell.
    if seen["parsed"] != oracle:
        errors.append(f"{name} REGISTER_JS: parseCsv differs from Python's csv module")
    # REGISTER_JS: load(), every header column of every row.
    if "error" in seen:
        errors.append(f"{name} REGISTER_JS: load() failed: {seen['error']}")
    else:
        for r, obj in zip(rows, seen["loaded"]):
            for col, cell in zip(header, r):
                want = cell.strip() if col == "sector" else cell
                if obj.get(col) != want:
                    errors.append(f"{name} REGISTER_JS: {r[0]} {col} read as {obj.get(col)!r}, not {want!r}")
    # GUARD: the rows whose confidence is "reported", by parsed column.
    want_reported = [i + 2 for i, r in enumerate(rows) if r[header.index("confidence")].strip().lower() == "reported"]
    if seen["reported"] != want_reported:
        errors.append(f"{name} GUARD: reported rows {seen['reported']}, expected {want_reported}")
    if planted_reported is not None and seen["reported"] != [planted_reported]:
        errors.append(f"{name} GUARD: missed the planted reported row {planted_reported}")

    aw = audit_website_module()
    aw.REGISTER_PATH = path
    # AUDIT_IDS
    ids = aw.load_register_ids()
    if ids != {r[0] for r in rows}:
        errors.append(f"{name} AUDIT_IDS: {sorted(ids)} != {sorted(r[0] for r in rows)}")
    # AUDIT_HOSTS: the regex over the whole file finds the same hosts as the
    # same regex over each parsed cell, so no quoted comma splits a URL.
    hosts = aw.registered_source_hosts()
    per_cell = {m.group(1) for r in rows for c in r for m in re.finditer(r"https?://([^/\s,\"']+)", c)}
    if hosts != per_cell:
        errors.append(f"{name} AUDIT_HOSTS: {sorted(hosts ^ per_cell)} differ")
    return errors


def with_cell(src: pathlib.Path, dst: pathlib.Path, source_id: str, col: str, value: str | None) -> None:
    """Copy src to dst with one cell set, or with the column removed (value None)."""
    rows = list(csv.reader(io.StringIO(src.read_text(encoding="utf-8"), newline="")))
    i = rows[0].index(col)
    if value is None:
        rows = [r[:i] + r[i + 1:] for r in rows]
    else:
        for r in rows[1:]:
            if r[0] == source_id:
                r[i] = value
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerows(rows)
    dst.write_text(buf.getvalue(), encoding="utf-8")


def selftest() -> list[str]:
    errors: list[str] = []
    real_header = next(csv.reader(REGISTER.open(newline="", encoding="utf-8")))
    fx_header = next(csv.reader(FIXTURE.open(newline="", encoding="utf-8")))
    if fx_header != real_header:
        errors.append("fixture header differs from sources/register.csv's header")
    fx = FIXTURE.read_text(encoding="utf-8")
    if f'"{EXAMPLE}"' not in fx:
        errors.append("fixture: SRC-017's checked_by is not the example value as a quoted cell")
    # The fixture must defeat a comma split, or it proves nothing.
    ci = fx_header.index("confidence")
    naive_ok = all(l.split(",")[ci] == r[ci] for l, r in zip(fx.splitlines()[1:], list(csv.reader(io.StringIO(fx)))[1:]))
    if naive_ok:
        errors.append("fixture: a comma split reads confidence correctly on every row; it needs quoted commas")

    errors += check(FIXTURE)
    with tempfile.TemporaryDirectory() as d:
        tmp = pathlib.Path(d)
        # GUARD: a "reported" confidence on SRC-002, whose earlier cells hold
        # quoted commas, must be found on its own line (3).
        planted = tmp / "reported.csv"
        with_cell(FIXTURE, planted, "SRC-002", "confidence", "reported")
        errors += check(planted, planted_reported=3)

        cases = [
            ("blank", "", None),
            ("example", EXAMPLE, None),
            ("fractional seconds", "agent-checked, human-approved: Matt 2026-10-31T02:14:07.123456789Z", None),
            ("one fractional digit", "agent-checked, human-approved: Matt 2026-10-31T02:14:07.1Z", None),
            ("no comma", "agent-checked human-approved: Matt 2026-10-31T02:14:07Z", "checked_by"),
            ("another name", "agent-checked, human-approved: Sam 2026-10-31T02:14:07Z", "checked_by"),
            ("space for T", "agent-checked, human-approved: Matt 2026-10-31 02:14:07Z", "checked_by"),
            ("no Z", "agent-checked, human-approved: Matt 2026-10-31T02:14:07", "checked_by"),
            ("ten fractional digits", "agent-checked, human-approved: Matt 2026-10-31T02:14:07.1234567891Z", "checked_by"),
            ("leading space", " " + EXAMPLE, "checked_by"),
            ("anything else", "yes", "checked_by"),
        ]
        for label, value, must_fail in cases:
            f = tmp / "case.csv"
            with_cell(FIXTURE, f, "SRC-017", "checked_by", value)
            seen = node_read(f)
            err = seen.get("error", "")
            if must_fail and must_fail not in err:
                errors.append(f"CHECKED_BY {label}: load() accepted {value!r}")
            if not must_fail and err:
                errors.append(f"CHECKED_BY {label}: load() rejected {value!r}: {err}")
        # The column removed.
        f = tmp / "no-column.csv"
        with_cell(FIXTURE, f, "", "checked_by", None)
        if "no `checked_by` column" not in node_read(f).get("error", ""):
            errors.append("CHECKED_BY column removed: load() did not fail")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    errors = selftest() if a.selftest else check(REGISTER)
    print(json.dumps({"ok": not errors, "mode": "selftest" if a.selftest else "register", "errors": errors}, indent=1))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())

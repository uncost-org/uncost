#!/usr/bin/env python3
"""Restatement check — does post_patch_pages.py reproduce the edited files?

Every edit to a template that is re-derived from the design export is restated
in tools/post_patch_pages.py, so a re-derivation cannot silently undo it. The
claim that matters is that the restatement REPRODUCES the edit: run against the
pre-change file, it must yield the edited file byte for byte.

This exports the tree at REF (the pre-change commit) to a temporary directory,
runs tools/post_patch_pages.py there, and compares every file the script
touched, plus any file named with --files, against the expected version. A file
the script changed that does not match is a failure; so is a named file it left
different, and so is the script exiting non-zero (a patch that matched the
wrong number of times).

By default the script and the expected files are the working tree's. --at
takes both from a commit instead (":" is the index), so one commit can be
checked on its own while later work is still unstaged.

    python3 tools/restatement_check.py --ref origin/main
    python3 tools/restatement_check.py --ref HEAD~1 --files website/src/index.njk
    python3 tools/restatement_check.py --ref HEAD --at :      # the staged commit
    python3 tools/restatement_check.py --ref HEAD~1 --at HEAD

Exit 0 when every compared file matches.
"""
from __future__ import annotations

import argparse
import io
import json
import pathlib
import shutil
import subprocess
import sys
import tarfile
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = "tools/post_patch_pages.py"


def show(ref: str, rel: str):
    """A file's bytes at a commit (":" = the index), or None if it is absent."""
    spec = f":{rel}" if ref == ":" else f"{ref}:{rel}"
    r = subprocess.run(["git", "show", spec], cwd=ROOT, capture_output=True)
    return r.stdout if r.returncode == 0 else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True, help="the pre-change commit")
    ap.add_argument("--files", nargs="*", default=[], help="files that must match after the run")
    ap.add_argument("--at", default=None,
                    help='take the script and the expected files from this commit (":" = the index)')
    a = ap.parse_args()
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="uncost-restate-"))
    try:
        blob = subprocess.run(["git", "archive", "--format=tar", a.ref, "website/src", "sources"],
                              cwd=ROOT, capture_output=True, check=True).stdout
        with tarfile.open(fileobj=io.BytesIO(blob)) as t:
            t.extractall(tmp, filter="data")
        before = {p.relative_to(tmp).as_posix(): p.read_bytes() for p in (tmp / "website/src").rglob("*") if p.is_file()}
        (tmp / "tools").mkdir()
        if a.at is None:
            shutil.copy(ROOT / SCRIPT, tmp / SCRIPT)
        else:
            script = show(a.at, SCRIPT)
            if script is None:
                raise SystemExit(f"{SCRIPT} is not in {a.at}")
            (tmp / SCRIPT).write_bytes(script)
        proc = subprocess.run([sys.executable, SCRIPT], cwd=tmp, capture_output=True, text=True)
        after = {p.relative_to(tmp).as_posix(): p.read_bytes() for p in (tmp / "website/src").rglob("*") if p.is_file()}
        touched = sorted(k for k in after if before.get(k) != after[k])
        compared = sorted(set(touched) | set(a.files))
        results, ok = [], proc.returncode == 0
        for rel in compared:
            if a.at is None:
                work = ROOT / rel
                expected = work.read_bytes() if work.exists() else None
            else:
                expected = show(a.at, rel)
            match = expected is not None and rel in after and expected == after[rel]
            ok = ok and match
            results.append({"file": rel, "changed_by_restatement": rel in touched, "matches": match})
        applied = [l.strip() for l in proc.stdout.splitlines() if l.strip().startswith("+ ")]
        print(json.dumps({"ok": ok, "ref": a.ref, "against": a.at or "working tree",
                          "post_patch_exit": proc.returncode, "patches_applied": applied,
                          "files": results, "stderr": proc.stderr[-1500:] if proc.returncode else ""}, indent=2))
        return 0 if ok else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())

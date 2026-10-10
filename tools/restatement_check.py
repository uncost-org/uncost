#!/usr/bin/env python3
"""Restatement check — does post_patch_pages.py reproduce the edited files?

Every edit to a template that is re-derived from the design export is restated
in tools/post_patch_pages.py, so a re-derivation cannot silently undo it. The
claim that matters is that the restatement REPRODUCES the edit: run against the
pre-change file, it must yield the edited file byte for byte.

This exports the tree at REF (the pre-change commit) to a temporary directory,
runs the working tree's tools/post_patch_pages.py there, and compares every
file the script touched, plus any file named with --files, against the working
tree. A file the script changed that does not match is a failure; so is a
named file it left different, and so is the script exiting non-zero (a patch
that matched the wrong number of times).

    python3 tools/restatement_check.py --ref origin/main
    python3 tools/restatement_check.py --ref HEAD~1 --files website/src/index.njk

Exit 0 when every compared file matches.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import tarfile
import tempfile
import io

ROOT = pathlib.Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True, help="the pre-change commit")
    ap.add_argument("--files", nargs="*", default=[], help="files that must match after the run")
    a = ap.parse_args()
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="uncost-restate-"))
    try:
        blob = subprocess.run(["git", "archive", "--format=tar", a.ref, "website/src", "sources"],
                              cwd=ROOT, capture_output=True, check=True).stdout
        with tarfile.open(fileobj=io.BytesIO(blob)) as t:
            t.extractall(tmp, filter="data")
        before = {p.relative_to(tmp).as_posix(): p.read_bytes() for p in (tmp / "website/src").rglob("*") if p.is_file()}
        (tmp / "tools").mkdir()
        shutil.copy(ROOT / "tools/post_patch_pages.py", tmp / "tools/post_patch_pages.py")
        proc = subprocess.run([sys.executable, "tools/post_patch_pages.py"], cwd=tmp, capture_output=True, text=True)
        after = {p.relative_to(tmp).as_posix(): p.read_bytes() for p in (tmp / "website/src").rglob("*") if p.is_file()}
        touched = sorted(k for k in after if before.get(k) != after[k])
        compared = sorted(set(touched) | set(a.files))
        results, ok = [], proc.returncode == 0
        for rel in compared:
            work = ROOT / rel
            match = work.exists() and rel in after and work.read_bytes() == after[rel]
            ok = ok and match
            results.append({"file": rel, "changed_by_restatement": rel in touched, "matches_working_tree": match})
        applied = [l.strip() for l in proc.stdout.splitlines() if l.strip().startswith("+ ")]
        print(json.dumps({"ok": ok, "ref": a.ref, "post_patch_exit": proc.returncode,
                          "patches_applied": applied, "files": results,
                          "stderr": proc.stderr[-1500:] if proc.returncode else ""}, indent=2))
        return 0 if ok else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())

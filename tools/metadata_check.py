#!/usr/bin/env python3
"""Metadata in served files — nothing personal ships with the site (CHG-007).

Over a built site it reports:

  PDF       each PDF's Info /Author, /Creator, /Producer, /Title and its XMP
            dc:creator. FAIL when an Author or dc:creator is anything but
            "Uncost".
  IMAGES    every PNG, JPEG, WebP and ICO, and each image inside an ICO:
            text chunks (tEXt, iTXt, zTXt), EXIF and XMP. FAIL on any EXIF
            or XMP, or a text chunk other than the technical ones image tools
            write (Software, and date or colour fields).
  COMMENTS  every distinct HTML comment, listed for a person to read; the
            site's own section markers ("SECTION: page.Name") are counted, not
            listed.
  NEEDLES   optionally, strings given in the environment variable
            METADATA_NEEDLES (one per line), searched for in every served
            file's bytes. Only the count of hits is printed, never the
            strings, so a personal name can be checked without writing it
            anywhere.

    python3 tools/metadata_check.py --built website/dist
    METADATA_NEEDLES="$(...)" python3 tools/metadata_check.py --built website/dist

Standard library only. Exit 0 when nothing FAILs, 1 otherwise.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import pathlib
import re
import struct
import zlib

TECHNICAL_TEXT = re.compile(r"^(Software|date:create|date:modify|date:timestamp|Creation Time|ColorSpace|gamma)$", re.I)


def png_chunks(data: bytes):
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    out, i = [], 8
    while i + 8 <= len(data):
        n, kind = struct.unpack(">I4s", data[i:i + 8])
        body = data[i + 8:i + 8 + n]
        out.append((kind.decode("latin-1"), body))
        i += 12 + n
        if kind == b"IEND":
            break
    return out


def png_meta(data: bytes) -> list:
    found = []
    for kind, body in png_chunks(data) or []:
        if kind == "tEXt":
            k, _, v = body.partition(b"\0")
            found.append(("text", k.decode("latin-1"), v.decode("latin-1", "replace")))
        elif kind == "zTXt":
            k, _, rest = body.partition(b"\0")
            found.append(("text", k.decode("latin-1"), zlib.decompress(rest[1:]).decode("latin-1", "replace")))
        elif kind == "iTXt":
            k, _, rest = body.partition(b"\0")
            flag = rest[0]
            rest = rest[2:].split(b"\0", 2)[-1]
            v = zlib.decompress(rest) if flag else rest
            found.append(("xmp" if k == b"XML:com.adobe.xmp" else "text", k.decode("latin-1"), v.decode("utf-8", "replace")))
        elif kind == "eXIf":
            found.append(("exif", "eXIf", f"{len(body)} bytes"))
    return found


def jpeg_webp_meta(data: bytes) -> list:
    found = []
    if b"Exif\0\0" in data[:65536]:
        found.append(("exif", "Exif", "present"))
    if b"http://ns.adobe.com/xap/1.0/" in data or b"<x:xmpmeta" in data:
        found.append(("xmp", "XMP", "present"))
    return found


def ico_images(data: bytes) -> list:
    if data[:4] != b"\0\0\1\0":
        return []
    count = int.from_bytes(data[4:6], "little")
    imgs = []
    for k in range(count):
        e = data[6 + 16 * k: 22 + 16 * k]
        size, off = int.from_bytes(e[8:12], "little"), int.from_bytes(e[12:16], "little")
        imgs.append(data[off:off + size])
    return imgs


def pdf_fields(data: bytes) -> dict:
    """Author-like fields from a PDF's Info dictionary and XMP, where readable."""
    out = {}
    for key in (b"Author", b"Creator", b"Producer", b"Title"):
        m = re.search(rb"/" + key + rb"\s*\(((?:\\.|[^\\)])*)\)", data)
        if m:
            out["Info/" + key.decode()] = m.group(1).decode("latin-1")
    # Info may sit in a compressed object stream; XMP is usually plain.
    for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, re.S):
        chunk = m.group(1)
        try:
            chunk = zlib.decompress(chunk)
        except zlib.error:
            pass
        for key in (b"Author", b"Creator", b"Producer", b"Title"):
            mm = re.search(rb"/" + key + rb"\s*\(((?:\\.|[^\\)])*)\)", chunk)
            if mm and "Info/" + key.decode() not in out:
                out["Info/" + key.decode()] = mm.group(1).decode("latin-1")
        x = re.search(rb"<dc:creator>(.*?)</dc:creator>", chunk, re.S)
        if x:
            out["XMP/dc:creator"] = re.sub(r"<[^>]+>", " ", x.group(1).decode("utf-8", "replace")).strip()
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--built", default="website/dist")
    a = ap.parse_args()
    root = pathlib.Path(a.built)
    needles = [n.strip() for n in os.environ.get("METADATA_NEEDLES", "").splitlines() if n.strip()]
    fails, pdfs, images, comments, section_markers = [], {}, {"files": 0, "with_metadata": {}}, {}, 0
    hits = [0] * len(needles)
    for f in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = str(f.relative_to(root))
        data = f.read_bytes()
        for i, n in enumerate(needles):
            hits[i] += data.lower().count(n.lower().encode())
        ext = f.suffix.lower()
        if ext == ".pdf":
            fields = pdf_fields(data)
            pdfs[rel] = {k: (v if not k.endswith(("Author", "dc:creator")) else ("Uncost" if v == "Uncost" else f"<{len(v)} chars>"))
                         for k, v in fields.items()}
            for k, v in fields.items():
                if k.endswith(("Author", "dc:creator")) and v != "Uncost":
                    fails.append(f"PDF: {rel} {k} is not \"Uncost\" ({len(v)} chars)")
        elif ext in (".png", ".jpg", ".jpeg", ".webp", ".ico"):
            images["files"] += 1
            parts = ico_images(data) if ext == ".ico" else [data]
            for part in parts:
                meta = png_meta(part) if part[:4] == b"\x89PNG" else jpeg_webp_meta(part)
                for kind, key, val in meta:
                    images["with_metadata"].setdefault(rel, []).append(f"{kind}:{key}")
                    if kind in ("exif", "xmp") or not TECHNICAL_TEXT.match(key):
                        fails.append(f"IMAGE: {rel} carries {kind} {key}")
        elif ext == ".html":
            for c in re.findall(r"<!--(.*?)-->", data.decode("utf-8", "replace"), re.S):
                c = " ".join(html.unescape(c).split())
                if re.match(r"^SECTION: \S", c):
                    section_markers += 1
                else:
                    comments.setdefault(c[:160], []).append(rel)
    if needles and any(hits):
        fails.append(f"NEEDLES: {sum(hits)} hits in served files")
    print(json.dumps({
        "ok": not fails, "fail": fails, "pdf": pdfs,
        "images": {"files": images["files"], "with_metadata": images["with_metadata"]},
        "html_comments": {"section_markers": section_markers,
                          "other": {k: {"pages": len(v), "example": v[0]} for k, v in comments.items()}},
        "needles": {"given": len(needles), "hits": sum(hits)},
    }, indent=1, ensure_ascii=False))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())

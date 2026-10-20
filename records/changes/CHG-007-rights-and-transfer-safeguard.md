# CHG-007 — Artwork licence, rights records, the PDF's metadata and the transfer safeguard (amends CHG-006)

**Status:** founder decision, dated by the founder (2026-10-20). Drafted from the founder's rights follow-up brief. It takes effect for the site when this record is merged and the site is next deployed. Amends [CHG-006](CHG-006-privacy-notice-and-records.md).

- **Date:** 2026-10-20
- **Amends:** [CHG-006](CHG-006-privacy-notice-and-records.md), whose rights gaps (PR #82) and UNP-73 question 1 this record settles.
- **Changed claims:**
  1. The published artwork is licensed to Uncost in writing, where it was previously a founder assertion only.
  2. The brand asset manifest's publication scope now says what is published.
  3. *The Case for Uncost* PDF carries no personal name, so its hash pin changes.
  4. Fonts and icons have recorded sources and licences.
  5. /privacy/ names the safeguard for US transfers.
- **Source:** the founder's rights follow-up brief (2026-10-20), and the reads recorded below. No AI decision; this file records what the founder set and what was found.
- **Rationale:** close the rights gaps PR #82 listed, and the UNP-73 transfer question, before the next deployment.

## 1. Artwork licence (founder decision)

Dafuq Industries LLC grants Uncost a non-exclusive, royalty-free, worldwide licence to use, adapt and publish, for Uncost's work, the following:
- the logo marks;
- the Open Graph image;
- the six robots;
- the fifteen sector images that uncost.org publishes;
- the favicon and app icons derived from them.

The licence transfers to Uncost's fiscal sponsor or successor entity on request. Dafuq Industries keeps ownership.

- **Full text and file list:** [`LICENSES/LicenseRef-Dafuq-Industries-Uncost-Art.txt`](../../LICENSES/LicenseRef-Dafuq-Industries-Uncost-Art.txt). The grant is also recorded in `NOTICE.md` and in `website/assets/brand/RIGHTS.md`.
- **Favicon source:** the favicon and app icons are made from `robots/robot_01_front_transparent.png`, which is not one of the six robots the site shows. The licence names that file as the favicon's source, so the derived icons are covered as the founder intended.
- **Open-content licences:** the artwork stays outside this repository's Apache-2.0 and CC BY 4.0 licences.

**Manifest.** `website/assets/brand/ASSET_MANIFEST.json`'s `publication_scope` used to say "GitHub repository intake only; no website deployment, runtime selection, merge, or production publication". It now names the 24 images published on uncost.org since CHG-004 and the favicon source, and points to the licence. `license_boundary` points to the licence too.
- **Unchanged:** the 86 asset entries, their hashes and their per-asset rights fields.
- **Manifest hash:** `1a553c66418a84cab12cbe17975a56d4746a53b552d2979dde0038afff3414ed` before, `6263f38a56a36ffcdc2e56c1b7652b518f67bd98afceb21428f71777aa7dbc07` after.
- **The intake receipts keep the old hash.** `website/design-system/SOURCE_RECEIPT.json` (`base.asset_manifest_sha256`) and `website/assets/brand/FINAL_VALIDATION_RECEIPT.json` (`manifestSha256`) record the manifest as it was validated at intake (2026-07). They are historical receipts and are not rewritten. No audit compares them with the current file.

## 2. Roboto Condensed: which licence the served file carries

Read on 2026-10-20 with fontTools, from the served `website/assets/fonts/RobotoCondensed-variable.woff2`:

| Field | Value |
|---|---|
| Version (name ID 5) | "Version 3.008; 2023" |
| Copyright (name ID 0) | "Copyright 2011 Google Inc. All Rights Reserved." |
| Licence description (name ID 13) | absent |
| Licence URL (name ID 14) | `http://www.apache.org/licenses/LICENSE-2.0` |

Upstream, read the same day:

| Source | What it shows |
|---|---|
| google/fonts, `ofl/robotocondensed/` | `METADATA.pb` reads `license: "OFL"`; its source is googlefonts/roboto-classic release **v3.008**, at commit `8aa699a9a715be7ecf6be41171e2851a580f0fb8`. The directory ships `OFL.txt` ("Copyright 2011 The Roboto Project Authors … licensed under the SIL Open Font License, Version 1.1"). The family was moved into `ofl/` on 2023-08-02 (commit `ae50998cbc`, "move to ofl dir"). `apache/robotocondensed/` no longer exists. |
| google/fonts' own `RobotoCondensed[wght].ttf` | The same version (3.008), and the **same** stale name-table fields: "Licensed under the Apache License, Version 2.0" and the Apache URL. |
| googlefonts/roboto-classic, `OFL.txt` | SIL OFL 1.1. |

**Finding:** the served file is release 3.008, the release google/fonts distributes under OFL 1.1. The Apache-2.0 fields in its name table are the 2011 metadata that the upstream 3.008 binary still carries, not a separate Apache-2.0 release.

**Recorded:** OFL 1.1, as before. `NOTICE.md`'s font line now states the release and why the embedded fields are stale. No Apache-2.0 entry is added for the font. If the founder prefers to treat the embedded field as controlling, `LICENSES/Apache-2.0.txt` is already present and only the NOTICE line would change.

## 3. *The Case for Uncost*: metadata only

**What changed:** the PDF's Author is now "Uncost" in both places it is stored, the Info dictionary (`/Author`) and the XMP metadata (`dc:creator`). Each previously held a personal name. It was rewritten with pikepdf (qpdf), so the old metadata is not left in an earlier revision of the file.

**What did not change:**
- **Pages:** all 14 pages' content streams and images are byte-identical.
- **Rendering:** every page renders pixel-identical (pdftoppm at 60 dpi, compared with Pillow).
- **Other metadata:** Title, Creator, Producer, dates and document ID are unchanged.
- **The old name:** it occurs nowhere in the new file, raw or inside any decoded stream.

**Hashes:**

| | Before | After |
|---|---|---|
| SHA-256 | `4fc813c0f4935502cd5c20bb8bfd6e0341aae0d451261f43595b76cc23021fce` | `b4815c7b44281d6072ef0e0f64dc3e6a65c44b6a37fcedfdaf40b250679f1f87` |
| Size | 3,836,948 bytes | 3,836,927 bytes |

`docs/CONTROL.md` is re-pinned, and it is the only place that pins this file.

**No other served file carries a personal name.** `tools/metadata_check.py` (new) found, over the built site:
- the one PDF's Author and `dc:creator` both read "Uncost";
- the 95 images (PNG, and the images inside the ICO) carry no text, EXIF or XMP metadata at all;
- the HTML comments are 340 section markers and one html-validate directive;
- the old name and its parts, given to the check through the environment and never written down, occur in **no** served file. Run against the old PDF, the same check finds them.

## 4. Icon sources

- **Social icons:** Instagram, Threads, X, Bluesky and TikTok, plus YouTube and Reddit, which are in the template but hidden. All are byte-identical to **Simple Icons 16.35.0**, which is CC0 1.0 (`NOTICE.md`).
- **The interface icons:** the 21 symbols of `website/design-system/icons/icons.svg` and the inline drawings in the header (search) and the pledge pages (envelope, check, refresh, and the X, Threads and mail share icons).
  - They were compared with Lucide 1.60.0 (ISC), Feather 4.29.2 (MIT), Heroicons 2.2.0 (MIT) and Tabler 3.49.0 (MIT) by `tools/icon_provenance.py` (new). The comparison is geometric: every icon is drawn with the same stroke at 64px, and overlap is measured.
  - The design export's records name no icon set.
  - **No set is their source.** None of the non-trivial icons matches any set (best overlap 0.86 or less): search, user, chart, globe, bell, calendar, gear, box, monitor, document, download, share, external link, close and filter.
  - Only trivial shapes coincide: three horizontal lines (menu, Feather), a check stroke (Lucide, Feather), plus and minus (every set), and a rectangle with a V (envelope; Tabler's `mail` has rounded corners where ours are square). Shapes this simple coincide by geometry, so this is not evidence of copying.
  - **Recorded as created for the design export.** No licence is recorded for them; that is for the founder.

## 5. Transfer safeguard: /privacy/ §6 (UNP-73 question 1)

Read on 2026-10-20 at 12:30 UTC from the official list at https://www.dataprivacyframework.gov/list (US Department of Commerce), in headless Chromium through Playwright. The method was the list's own search, its data endpoint, and each participant's page. Screenshots are kept privately.

| Participant | EU-U.S. DPF | UK Extension | Swiss-U.S. DPF | Next certification due | Data |
|---|---|---|---|---|---|
| **Cloudflare, Inc.** (San Francisco; participant 5666) | Active – Re-certification under Review | Active – Re-certification under Review | Active – Re-certification under Review | 15 Sep 2027 | Non-HR |
| **Google LLC** (Mountain View; participant 5780; covers its wholly-owned US subsidiaries) | Active | Active | Active | 13 Sep 2027 | Non-HR |

Both are active participants, UK Extension included. Cloudflare's status shows that its annual re-certification is being reviewed; it remains on the active list. Following the founder's decision:
- /privacy/ §6 now adds: "Cloudflare and Google take part in the EU-U.S. Data Privacy Framework (and its UK Extension), which is the safeguard for these transfers."
- Under the notice's own §12 rule, the notice is now **version 0.3**, with a dated row. This is restated as CP-3 in `tools/post_patch_pages.py`.

**UNP-73:** this closes **question 1** (the transfer mechanism for Cloudflare and Google), by founder decision on the DPF reading above. These stay **open**, for the founder and counsel:
2. Counsel to confirm Dafuq Industries LLC as the controller of record, and the §1 wording.
3. GDPR applicability (Art. 3(1) or 3(2)), an Art. 27 EU representative (and a UK one), and UK-specific wording.
4. The sign-up email provider (Amazon SES, us-east-1) and the datastore region, which are not live.
5. The minimum age for the Pledge and updates sign-ups.
6. Adoption of POL-002.

The private processor register records the reading above against each provider.

## Affected public surfaces

- `/privacy/`: §6, the header (version 0.3) and the version table.
- `/downloads/the-case-for-uncost.pdf`: metadata only.
- Rights records: `NOTICE.md`, `LICENSES/LicenseRef-Dafuq-Industries-Uncost-Art.txt` (new), `website/assets/brand/ASSET_MANIFEST.json` (`publication_scope`, `license_boundary`), `website/assets/brand/RIGHTS.md`, `docs/CONTROL.md` (the pin).

## Provenance

The founder's rights follow-up brief, 2026-10-20. Drafted by Claude Code as `uncost-admin`.

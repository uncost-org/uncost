# CHG-008 — Licences for the interface icons and *The Case for Uncost* (amends CHG-007)

**Status:** founder decision, dated by the founder (2026-10-20). Drafted from the founder's maintenance brief. It takes effect when merged; no file the site serves changes. Amends [CHG-007](CHG-007-rights-and-transfer-safeguard.md), which left both of these without a licence.

- **Date:** 2026-10-20
- **Amends:** [CHG-007](CHG-007-rights-and-transfer-safeguard.md), §4 (icon sources) and §3 (the PDF).
- **Changed claims:** the interface icons have a licence, and so does *The Case for Uncost*. Until now neither had one recorded.
- **Source:** the founder's maintenance brief (2026-10-20). No AI decision; this file records what the founder set.

## 1. Interface icons: added to the Dafuq Industries artwork licence

**Founder:** the interface icons were created for the design export, which Dafuq Industries LLC supplied.

**Which icons:**
- the 21 symbols of `website/design-system/icons/icons.svg`;
- the inline icon drawings in the templates: the header's search icon, and the pledge pages' envelope, check, refresh and share icons.

**Consistent with the evidence:** CHG-007 §4 found that no open icon set (Lucide, Feather, Heroicons, Tabler) is their source.

**Recorded:**
- `LICENSES/LicenseRef-Dafuq-Industries-Uncost-Art.txt` lists them as licensed works, with an amendment line. The grant's terms are unchanged: non-exclusive, royalty-free and worldwide, to use, adapt and publish for Uncost's work; it transfers on request; Dafuq Industries keeps ownership.
- `NOTICE.md` records it.

**Other companies' marks:** the X and Threads share icons stand for those services. Their names and marks remain their owners'; the licence covers the drawings only.

**Not changed:** the social icons (Simple Icons 16.35.0, CC0 1.0).

## 2. *The Case for Uncost*: CC BY 4.0

**Founder:** license the PDF CC BY 4.0, like the repository's other original documentation (`LICENSE` §2). The Uncost name and logo stay excluded, as `LICENSE` §3 says.

**Recorded in `NOTICE.md`.** The PDF also reproduces the Dafuq Industries artwork: sector images, robots and the logo. That artwork stays reserved and licensed to Uncost (CHG-007, and §1 above), so it is outside the CC BY licence too. This follows the existing rule in `NOTICE.md` ("Brand identifiers and artwork … are reserved and excluded from the open-content licence"); it is not a new decision.

**The file is unchanged.** Its bytes and hash pin (`b4815c7b…`, `docs/CONTROL.md`) are as CHG-007 left them, and the licence lives in the repository's records.

## Affected surfaces

- `LICENSES/LicenseRef-Dafuq-Industries-Uncost-Art.txt`, `NOTICE.md`. No page or served file changes.

## Provenance

The founder's maintenance brief, 2026-10-20. Drafted by Claude Code as `uncost-admin`.

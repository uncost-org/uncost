# Public documentation changelog

## 2026-07-16 — Fresh repository initialization

- Created public core documents from the final external Movement Plan and Roadmap and merged portfolio canon.
- Added fifteen sector dossier scaffolds.
- Published POL-001–010 as v1.3 drafts pending independent Claude, founder, and required professional review.
- Published PRJ-001–007 as v1.3 drafts pending independent Claude, founder, and domain review.
- Excluded legacy repository content, stale website copy, private internal planning, credentials, caches, and the unpublished control PDF.

## 2026-07-16 — Policy public-review conformance repair

- Corrected POL-001–010 and the master pack against the final external source.
- Removed private/internal placeholder thresholds and founder-detail wording.
- Added final-plan no-equity, Assembly, physical-pilot, data-gift, and action-specific gates.
- Clarified repository-specific applied licences versus future proposed defaults.
- No policy was adopted or activated.

## 2026-07-19 — Controlling-source re-pin (DEF-01 / CHG-001)

- Re-pinned `docs/CONTROL.md` and `sources/register.csv` to the final July-2026 Movement Plan and Roadmap (27 pages, SHA-256 `a2b640217626a76e9a26f73a5744f8c59051c83351a72bc041150824ac5a3dcd`), declared final by the founder on 2026-07-18. The Day 1 anchor remains 2026-07-15.
- Policy drafts keep their 2026-07-15 derivation stamp and gain explicit `source_superseded_by_sha256` markers; re-review against the July-2026 edition remains pending.
- Recorded as `records/changes/CHG-001-controlling-source-repin.md`. No policy text, adoption status, or roadmap date changed.

## 2026-07-21 — DEF-05 closed: durable design authority recorded

- Recorded in `docs/CONTROL.md` that the 4-part order, the 15-sector order, and the six-class status vocabulary are durably authoritative in the repository (build-enforced in `website/src/_data/catalog.js`; hash-pinned in the design-system CSS), superseding the lost ephemeral `/tmp` overlay cited by earlier planning.
- DEF-05 is a provenance record, not a publication blocker. No content, order, or status vocabulary changed.

## 2026-07-22 — Design-system authority adopted from the finished export

- Moved the design-system visual authority from the 2026-07-16 UNP-46 intermediate handoff to the finished Claude Design export (SHA-256 `8962b207…`), adopting its native component vocabulary. Recorded in `website/design-system/AUTHORITY.md`; earlier CSS recoverable from git history.
- Re-applied three constraints the export's design-system layer had regressed: coral contrast (bright coral → deep coral for small text/links/pills), removal of the `vote`/`dollar` glyphs, and light-theme-only.
- Rewrote `scripts/audit_design_handoff.py` contrast validation to auto-discover every surface and pill (coverage complete by construction; 28 pairs checked, all AA). Regenerated `SOURCE_RECEIPT.json`.
- Status vocabulary changed (DEF-05 dated update in `docs/CONTROL.md`); substance preserved. Added `docs/DESIGN_CONSTRAINTS.md` (paste-ready constraints for Claude Design, derived from the enforcing artifacts).

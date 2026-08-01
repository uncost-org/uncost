# CHG-002 — Source register landed + home/about/FAQ/privacy/news content

**Date:** 2026-08-01 · **Branch:** `feat/content-batch-unp69` · **Status:** in review (not adopted, not deployed)

Research/authoring only from an AI contributor. Nothing here is adopted, launched, or
deployed. Draft policies remain drafts; the Assembly does not operate; donations stay
closed. This is a content + data change for founder review.

## What landed

1. **`sources/register.csv`** — the cost-of-living source register moves from a single
   governance pin (SRC-001) to **SRC-001 + 22 cost-statistic rows (SRC-002…SRC-023)**.
   Schema extended per UNP-69 §1: added `display_caption`, `receipt`, `change_basis`,
   `volatility_flag`, `placement`, plus a `source_line` for on-page attribution.
2. **`website/src/_data/register.js`** — loads the register so pages render figures FROM
   the register (no hardcoded numbers). **`partials/figure.njk`** wraps each stat in
   `data-source="SRC-###"`, which is what the content audit reads as the citation.
3. **`partials/mailto.njk`** — new obfuscated-mailto component (entity-encoded; the string
   `contact@uncost.org` never appears in page source). Used on FAQ and Privacy.
4. **Home (`index.njk`)** — copy per the 2026-07-20 voice brief; three hero stats
   (SRC-020 ownership, SRC-021 median-renter, SRC-004 cost-burden) rendered from the register.
5. **About (`about.njk`)** — "We're early" structure, updated to the current true state.
6. **FAQ (`_data/faq.js` + `faq.njk`)** — 18 Q&As from the Jul-30 `Uncost-FAQ` docx; the two
   founder-final rewrites replace their questions; the three `***` review comments stripped.
7. **Privacy (`privacy.njk`)** — thin/true notice; controller + minimum-age lines carry
   `SPONSOR-GATED` / `COUNSEL-GATED` template-comment markers (source only, not public).
8. **News (`_data/news.js` + `news/index.njk` + `news/feed.xml`)** — three founder-approved
   movement updates, dated 2026-08-01, in the page and the RSS feed.
9. **Receipts (`receipts.njk`)** — renders the register (durable rows) as the public face of
   the sources, so every "Receipt →" link resolves to the exact figure.

## Source provenance

- **UNP-69** doc `unp-67-source-library-v1-1` (rev 2) — captions + new-row receipts + schema.
- **UNP-67** doc `unp-67-source-library-v1` (rev 1) — verbatim receipts for retained rows.
- **UNP-72** doc `unp-67-source-library-v1-1a-r2` — ground beef, SRC-023.
- **UNP-70** doc `unp-70-preflight-verification-record-v1` + comments — PMMS decision,
  Harvard p.29 confirmation, SRC-022 rebase.
- Home/About voice: `voice-brief.md` (2026-07-20) in the design-system handoff zip.

## Open gates and decisions (founder-owned)

- **Census HVS median asking rent — NOT landed.** UNP-70 records it as network-blocked and
  never pulled ("a lead, not a row"). No pasted value exists on the card. SRC-019 (BLS *Rent
  of primary residence*) is the verified shelter-rent companion instead. Pull Table 11A to add it.
- **Freddie Mac PMMS — dropped** (licence; UNP-70 founder decision). Not in the register.
- **SRC-023 (ground beef)** — June-2026 level is superseded by the July CPI on **2026-08-12**;
  re-pull if this is published on or after that date. `last_checked` = 2026-08-01.
- **SEC-014 (Environment)** — default kept (NOAA 2024, $182.7B, year shown). Household-cost
  scope swap remains an optional founder call.
- **Home Four-parts (B4) / six-step (B5)** — kept per the voice brief; this overlaps the parked
  `feat/narrative-layout` decision to move them off home. Reconcile at merge.

## Verification

- `audit_repository.py`, `audit_website.py` (source) and `--built` all green; two consecutive
  builds byte-identical; `html-validate` clean on all pages.

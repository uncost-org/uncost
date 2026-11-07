# CHG-018 — /privacy/ version 0.5: the rate limit also covers the sign-up forms (amends CHG-017)

**Status:** founder decision (2026-11-07). Drafted from the founder's brief after go-live. It takes effect when this record is merged and the production deploy is approved.

- **Date:** 2026-11-07
- **Amends:** [CHG-017](CHG-017-signups-live.md), whose follow-up 3 it closes, and the privacy notice set by [CHG-009](CHG-009-signups.md) (version 0.4). Their history stands as written.
- **Changed claim:** /privacy/ §2 and §3 said the rate limit covers only the contact form. Since go-live, the rate-limiting rule also covers POST `/api/signup/pledge` and `/api/signup/updates` (CHG-017, production step 3).
- **Source:** the founder's brief, 2026-11-07. No AI decision; this file records what the founder set.

## What changes (only while the forms are on)

- **§2, "Security data":** "limit how often the contact form can be used" becomes "limit how often the contact form, the Pledge form and the updates form can be used".
- **§3, "Keeping the site secure":** the same change, in "including limiting how often … can be used".
- **Header:** version 0.5, effective 7 November 2026.
- **§12:** a new row, 0.5, 7 November 2026: "Says that the limit on how often the forms can be used also covers the Pledge and email-updates forms (sections 2 and 3; CHG-018)." This is the notice's own rule: a change updates the effective date at the top and adds a row.
- **`policyVersion`** in `website/src/_data/signups.json` is `privacy-notice-0.5`. Each consent event records it, and §11 says we record "the version of this notice". The consent texts are unchanged, so their fingerprints are too.

Nothing else in the notice changes. **With the switch off,** /privacy/ is still version 0.3, and every page is byte-identical.

## How it is made

`website/src/privacy.njk` is re-derived from the export, so the change is patch CP-5 in `tools/post_patch_pages.py`, applied to the template:
- **Guards:** the four CP-4 patches that CP-5 rewrites (the header's version and date, §2's sign-up item, the 0.4 row) are now guarded on their own row or item, as CP-3 was on the 0.3 row. A re-run then undoes nothing. To allow this, `literal()` and `add_items_after()` take an optional guard.
- **Re-run:** running the tool again applies nothing.
- **From main:** running it on `main`'s template gives exactly this template.

## Effective date

The date is the day this was drafted, 7 November 2026. If it is merged and deployed on a later day, the date changes in one place, `CP5_DATE` in `tools/post_patch_pages.py`, and the tool is re-run on `main`'s template before merging.

## Checks

On this branch, against `main` at `89cce80`. The pull request lists the counts.

## Affected surfaces

- **With the switch off:** none.
- **With it on (production):** /privacy/, and the site search index, which holds its text.
- **Consent events from the deploy on:** they record `privacy-notice-0.5`.
- **Files:**
  - `tools/post_patch_pages.py`;
  - `website/src/privacy.njk`;
  - `website/src/_data/signups.json`;
  - CHG-017 (the follow-up and "Amended by");
  - this record.

## Provenance

The founder's brief, 2026-11-07, after go-live. Drafted by Claude Code as `uncost-admin`.

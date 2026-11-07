# CHG-019 — The cost-of-living quiz at /quiz/

**Status:** founder brief (2026-11-07). It takes effect when this record is merged and the production deploy is approved. Nothing here changes the sign-ups, the Worker, its database, Postmark, DNS or any Cloudflare setting.

- **Date:** 2026-11-07
- **Amends:** the J sweep (2026-10-10; CANVAS-SYNC 162), which kept `/quiz/` as an unlinked, noindexed placeholder "until it has real content".
- **Changed claim:** `/quiz/` is no longer "on the way"; it is the quiz. `/join/` no longer marks "Take the cost-of-living quiz" as Planned, and links to it.
- **Source:** the founder's brief, 2026-11-07. No AI decision; this file records what the founder set.

## Why

- **The Movement Plan** lists "the cost-of-living quiz" as an early engagement tool: a short interactive "guess what living actually costs" test that draws people into the site, teaches something surprising, and offers the full breakdown when you join. The quiz offers the existing updates list instead, with no promise of a breakdown or a frequency (see "The end screen" below).
- **UNP-39 §5.5 and UNP-50** set it as post-launch ("quiz later", no fake data). The site launched on 2026-10-19.

## What changed

- **The quiz:**
  - Five questions, one per register row, in this order: SRC-025 (all items), SRC-019 (shelter), SRC-026 (food), SRC-027 (energy), SRC-003 (water).
  - **The guess:** a slider (−5 to +25, step 0.5) with a linked number input. `js/quiz.js` builds both from attributes in the template, because they only work with JavaScript and a page built with the forms off may ship no form control (`audit_website.py`, form-rendered, never allowlisted).
  - **"Check my guess" reveals the record:** the row's figure and caption through `partials/figure.njk` (inside its `data-source`), its period and region, its source line linked to its URL, and "You guessed X%. The record says Y%." with "within 1 point", "under by …" or "over by …".
  - **The end screen:** the five guesses against the record, then "Get updates by email" with the existing updates form, links to The Case, the sectors and the Pledge, and a "Share the quiz" button.
  - **No new promise about the updates list:** the line is "Get Uncost updates by email: new figures, what they mean, and their sources." It names no frequency. Nothing on the site, in the sign-up emails or in the privacy notice says the list sends a monthly breakdown, so the quiz does not say so either (review fix, 2026-11-07).
- **No fake numbers:**
  - Every answer comes from `sources/register.csv` through `_data/register.js` and `_data/quiz.js`, which holds the five row ids and the question texts and nothing else. The Friday review and the monthly refresh change the answers by updating the register.
  - **A build guard in `_data/quiz.js`** fails the build if any quiz row is missing, or has an empty `display_value`, `display_caption`, `data_period`, `source_line` or `url`, or a `display_value` that does not parse as a percent.
  - **`checked_by` is not required:** it is empty on all five rows today, which is listed for the founder.
- **No new data collection:**
  - The guesses never leave the browser: `js/quiz.js` makes no network request and uses no cookies, storage or analytics.
  - **The email step is the existing updates form** (`partials/forms/updates.njk`, CHG-009), unchanged. Its surface on `/quiz/` is `page`, already in `_data/signups.json`. So there is no sign-up, consent-text, policy-version or Worker change.
  - **With `formsOpen` off,** the partial shows its "open soon" message, as everywhere.
  - **Sharing** shares the page's URL and description, never a score.
- **Without JavaScript,** the page is the five questions with their sourced answers as a plain list, then the end block. **With it,** one question at a time, "Question 2 of 5".
- **No answer shows before the script runs** (review fix, 2026-11-07). `js/quiz.js` is deferred, so on a slow connection the plain list could show first. `js/quiz-early.js`, loaded without `defer` just before the quiz, marks `<html>` with `.quiz-js`; integration.css item 150 then hides the answers, the end block and questions 2 to 5. `js/quiz.js` removes the mark once its own `hidden` state is set. If `js/quiz.js` never arrives, the mark comes off at the load event and the plain list shows. The layout has no per-page `<head>` slot, so the script sits in the page, before the quiz, and no other page changes.
- **Accessibility:**
  - Every control is labelled, and the slider and number input stay in step, both by keyboard.
  - Each reveal is announced in a polite live region. Focus moves to the reveal heading, then to the next question.
  - The comparison is in words, not colour.
  - Targets are at least 24px, and there is no motion.
- **CSP** (`script-src 'self'`, `style-src 'self'`): the behaviour is in `js/quiz.js` and `js/quiz-early.js`, loaded from the site. There is no inline script, style or handler.

## Files

- **The quiz:**
  - `website/src/quiz.njk`. It is repo-authored now; `pageId` stays `later-quiz` because `sections.css` styles the page by it.
  - `website/src/_data/quiz.js`, `website/src/js/quiz.js` and `website/src/js/quiz-early.js`.
- **Styles:** `website/src/css/integration.css` item 150 (CANVAS-SYNC 191). It stacks the export's own quiz-page parts, keeps the R3 figure card as R3 draws it, sets the questions at `--fs-h3` (component headings, `type_audit.py`), sizes the two guess controls, lets `[hidden]` win over `.actions`, and hides the answers under `.quiz-js` until `js/quiz.js` has run. Tokens and existing declarations only.
- **`/join/`:** `website/src/join.njk`, restated as QZ-1 in `tools/post_patch_pages.py`.
- **`/quiz/` is no longer a placeholder:**
  - `tools/gen_static_pages.py` no longer writes `quiz.njk` from the export's placeholder;
  - `tools/post_patch_pages.py` drops it from J's noindex list;
  - `tools/prod_check.py` drops it from the expected noindex pages;
  - `website/SEARCH.md` lists it as indexed.

  It joins `sitemap.xml` and the search index.
- **Records:** `docs/CANVAS-SYNC.md` (row 191; row 162's note) and this record.

**Not changed:** the header navigation, the homepage (see the pull request), the updates form, `_data/signups.json`, `_data/labels.js` ("Planned" is still used on other pages).

## Checks

On branch `quiz-v1`, against `main` at `5155046`. The pull request lists the results, the guard proof and the screenshots.

## Rollback

Revert the pull request. Nothing is stored, so nothing else needs undoing.

## Provenance

The founder's brief, 2026-11-07. Drafted by Claude Code as `uncost-admin`.

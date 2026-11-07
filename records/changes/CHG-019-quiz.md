# CHG-019 — The cost-of-living quiz at /quiz/

**Status:** founder brief (2026-11-07). It takes effect when this record is merged and the production deploy is approved. Nothing here changes the sign-ups, the Worker, its database, Postmark, DNS or any Cloudflare setting.

- **Date:** 2026-11-07; revised 2026-11-08 after the founder's review of the preview (multiple choice, ten questions, the page header).
- **Amends:** the J sweep (2026-10-10; CANVAS-SYNC 162), which kept `/quiz/` as an unlinked, noindexed placeholder "until it has real content".
- **Changed claim:** `/quiz/` is no longer "on the way"; it is the quiz. `/join/` no longer marks "Take the cost-of-living quiz" as Planned, and links to it.
- **Source:** the founder's brief, 2026-11-07. No AI decision; this file records what the founder set.

## Why

- **The Movement Plan** lists "the cost-of-living quiz" as an early engagement tool: a short interactive "guess what living actually costs" test that draws people into the site, teaches something surprising, and offers the full breakdown when you join. The quiz offers the existing updates list instead, with no promise of a breakdown or a frequency (see "The end screen" below).
- **UNP-39 §5.5 and UNP-50** set it as post-launch ("quiz later", no fake data). The site launched on 2026-10-19.

## What changed

- **The quiz (multiple choice since 2026-11-08).** The founder reviewed the first preview (a five-question slider quiz) and set three changes: a standard page header, multiple choice instead of the slider, and the reveal below. The slider and its number input are gone. Ten questions, in this order:

  | # | Kind | Row(s) | Question |
  |---|---|---|---|
  | 1 | Pick the figure | SRC-025 | Over the past year, how much did prices overall go up? |
  | 2 | Which rose most? | SRC-026, SRC-019, SRC-003, SRC-027 | Which of these went up most over the past year? |
  | 3 | Pick the figure | SRC-028 | Forbes estimated the combined wealth of the 400 richest Americans at $6.6 trillion a year earlier. What was its estimate for 2026? |
  | 4 | Pick the figure | SRC-024 | In the second quarter of 2026, what share of the country's net worth did the wealthiest 1% of American households hold? |
  | 5 | Pick the figure | SRC-004 | In 2024, the latest year measured, what share of renter households spent more than 30 percent of their income on rent and utilities? |
  | 6 | Higher or lower | SRC-022 | Between 2001 and 2024, after inflation, did the median rent rise faster or slower than the median renter's income? |
  | 7 | Pick the figure | SRC-023 | What did a pound of ground beef cost in September 2026? |
  | 8 | Pick the figure | SRC-006 | On average, what did a year of family health coverage through an employer cost in 2025? |
  | 9 | Higher or lower | SRC-011 | Before adjusting for inflation, do household appliances cost more or less than they did in 1997? |
  | 10 | Pick the figure | SRC-018 | On a single night in January 2025, how many people were homeless in the United States? |

  The founder may reorder or swap them on the preview. Five are reworded from the brief to follow the rows' notes: #3 says it is Forbes's estimate (SRC-028); #4 and #5 name their period (SRC-004: "never imply current-year"), and #5 says "rent and utilities", as the receipt does; #7 and #8 name their year, and #8 says "on average" (KFF's figure is an average premium); #9 says "before adjusting for inflation", as the caption does. SRC-024 is total net worth, so "owned outside retirement accounts" (SRC-020's rule) does not apply to it.
- **The page header:** the `.titleband` ("The Quiz"), then the export's `.introband`: "How well do you know what living costs?", "10 quick questions on prices, rent and wealth in the United States. Pick an answer, then see the sourced figure." (the count is `quiz.total`) and, smaller, "Your answers stay in this browser." The intro card is gone.
- **The choices:** a native radio group per question, a `<fieldset>` whose `<legend>` is the question, one `<label><input type="radio">` per choice, built by `js/quiz.js` because the content audit allows no form control in the built HTML (form-rendered, never allowlisted). "Check my answer" stays disabled until a choice is picked. After checking, the reader's pick reads "Your answer" and the right choice "The record", in words, never by colour alone, and the group is locked.
  - **Pick the figure:** four choices, low to high. The right one is the row's `display_value` (for SRC-024, the first side of "32.5% versus 2.3%"). `_data/quiz.js` makes the three wrong ones at build time by one fixed rule, with no randomness: a ladder of four values, each 1.5 times the one below, with the record on one rung. Each is rounded to the record's own precision (percents to its decimal places; money and counts to its decimal places when it shows cents, otherwise to its significant figures) and written in the record's style. The rung (so the right answer's position) starts from a fixed order per question and moves on only when a rule fails there. The rules: four distinct choices; each wrong one at least a fifth from the record; a share stays inside the whole; the record is never the only choice whose last digit is, or is not, a zero. No "About" rounding was needed. A fixed ×0.25, ×0.5, ×2 would always put the record second from the top, so the ladder varies the rung instead.
  - **Which rose most:** every choice is a register row; the right one is the highest parsed percent.
  - **Higher or lower:** computed from two values the row states: SRC-022's "30% versus 9%", and SRC-011's index level against its December 1997 base in its receipt.
- **The reveal:** "Right." or "Not quite.", then the row's figure card through `partials/figure.njk` (inside its `data-source`), its period, region and source link, then "Next question". For "Which rose most", the other rows follow as one-line captions, each in its own `data-source`. Focus moves to the reveal heading, the result is announced in a polite live region, and focus then moves to the next question.
- **The score:** the number right out of the total. The end screen says "You got N of 10 right." above the summary (Question, Your answer, The record, Right?), then "Get updates by email" with the existing updates form, links to The Case, the sectors and the Pledge, and "Share the quiz".
- **No new promise about the updates list:** the line is "Get Uncost updates by email: new figures, what they mean, and their sources." It names no frequency. Nothing on the site, in the sign-up emails or in the privacy notice says the list sends a monthly breakdown, so the quiz does not say so either (review fix, 2026-11-07).
- **No fake numbers:**
  - Every answer comes from `sources/register.csv` through `_data/register.js` and `_data/quiz.js`. The Friday review and the monthly refresh change the quiz by updating the register.
  - **A question states a number only if its row does:** each number in a question must be in the same row's caption or receipt, and the question renders inside that row's `data-source`. A "Which rose most" question states none.
  - **The build guard in `_data/quiz.js`** fails the build if any row in the set is missing, or has an empty `display_value`, `display_caption`, `data_period`, `source_line` or `url`; if a question states a number its row does not; if a row's figure card would appear twice; if a pick question's value does not parse, its own text cannot be rebuilt from its value, or no rung passes the rules above; if a "most" row is not a single percent, the rows' periods differ ("Year to September 2026" and "September 2026" are the same period), or the highest is tied; if a compare question's two values cannot be read or are equal; or if every question puts the right answer in the same position.
  - **The wrong choices are not register figures, by design.** `scripts/audit_website.py` exempts them from the figure rules in one place only: text inside an element marked `data-quiz-choice`, on the page whose `<body data-page>` is `later-quiz`. The FAIL rules still read that text, the exemption counts nothing as cited, and the same markup on any other page is audited as usual (self-tests). Nothing else is loosened.
  - **`checked_by` is not required:** it is empty on every row in the set today, which is listed for the founder.
- **No new data collection:**
  - The answers never leave the browser: `js/quiz.js` makes no network request and uses no cookies, storage or analytics. An anonymous score log is a separate, later change.
  - **The email step is the existing updates form** (`partials/forms/updates.njk`, CHG-009), unchanged. Its surface on `/quiz/` is `page`, already in `_data/signups.json`. So there is no sign-up, consent-text, policy-version or Worker change.
  - **With `formsOpen` off,** the partial shows its "open soon" message, as everywhere.
  - **Sharing** shares the page's URL and description, never a score.
- **Without JavaScript,** the page is the ten questions with their sourced answers as a plain list, each with "The answer: …", then the end block; no choices show. **With it,** one question at a time, "Question 2 of 10".
- **No answer shows before the script runs** (review fix, 2026-11-07). `js/quiz.js` is deferred, so on a slow connection the plain list could show first. `js/quiz-early.js`, loaded without `defer` inside the quiz before its questions, marks `<html>` with `.quiz-js`; integration.css item 150 then hides the answers, the end block and every question after the first. `js/quiz.js` removes the mark once its own `hidden` state is set. If `js/quiz.js` never arrives, the mark comes off at the load event and the plain list shows. The layout has no per-page `<head>` slot, so the script sits in the page, and no other page changes. It sits inside `.sys` so the header band and the quiz band stay adjacent for the boundary rule.
- **Accessibility:** native radios in a fieldset named by the question; arrow keys move within a group; every control is labelled; results are marked in words and announced; focus moves to each reveal and then to the next question; targets are at least 24px; there is no motion.
- **CSP** (`script-src 'self'`, `style-src 'self'`): the behaviour is in `js/quiz.js` and `js/quiz-early.js`, loaded from the site. There is no inline script, style or handler.

## Files

- **The quiz:**
  - `website/src/quiz.njk`. It is repo-authored now; `pageId` stays `later-quiz` because `sections.css` styles the page by it.
  - `website/src/_data/quiz.js`, `website/src/js/quiz.js` and `website/src/js/quiz-early.js`.
- **Styles:** `website/src/css/integration.css` item 150 (CANVAS-SYNC 191). It stacks the export's own quiz-page parts; restates the export's introband declarations for this page (sections.css draws the introband page by page and has none for `/quiz/`), minus what integration already sets for every introband, and lets the quiz band own the boundary below it; draws the choices as the pledge form's consent box and rows (`.consents`, `.crow`) with a native radio sized as the contact form's consent box; keeps the R3 figure card as R3 draws it; sets the questions at `--fs-h3` (component headings, `type_audit.py`); lets `[hidden]` win over `.actions`; and hides the answers under `.quiz-js` until `js/quiz.js` has run. Tokens and existing declarations only. No other introband draws a smaller second line, so the secondary line is styled by position (`p + p`), not by a new class.
- **The audit exemption:** `scripts/audit_website.py` (`QUIZ_CHOICE_PAGE`, `QUIZ_CHOICE_ATTR`, and six self-tests).
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

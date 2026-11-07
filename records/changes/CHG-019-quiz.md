# CHG-019 — The cost-of-living quiz at /quiz/

**Status:** founder brief (2026-11-07). The quiz takes effect when this record is merged and the production deploy is approved. The anonymous score tally (below) ships switched off: turning it on, privacy notice 0.6 and its effective date are founder decisions, with the counsel questions tracked under UNP-73. Nothing here changes the sign-ups Worker, its database, Postmark, DNS or any Cloudflare setting.

- **Date:** 2026-11-07; revised 2026-11-08 after the founder's review of the preview (multiple choice, ten questions, the page header); extended 2026-11-08 with the anonymous score tally and two follow-ups (rounded money and count choices; SRC-018's caption in the summary).
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

## The anonymous score tally (2026-11-08; switched off)

So the end screen can say "You got 7 of 10 right. The average is 5.8 from 1,240 people." It launches with the quiz in one merge, switched off; production stays off until the founder turns it on.

- **What is stored:** one row per completed quiz in a new D1 database, `uncost-quiz` (previews: `uncost-quiz-preview`), separate from `uncost-signups`, which holds personal data. The columns are `version` (a 12-character hash of the question set: each question's kind, row ids and right answer, from `_data/quiz.js`, so averages never mix different questions; a register refresh that changes an answer changes it), `correct`, `total`, `answers` (a 1 or 0 per question, in order) and `day` (the UTC date, no time). Nothing else: no IP address, user agent, cookie, fingerprint, email, name or id column. SQLite's internal row number is never read or returned. The schema is `website/migrations/quiz/0001_scores.sql`; its checks refuse any row outside these rules.
- **The endpoints** (Pages Functions, same origin, so the CSP's `connect-src 'self'` already allows them; `website/functions/api/quiz/`, logic in `website/lib/quiz.js`):
  - `POST /api/quiz/score` takes exactly `{version, answers}`. The server counts `correct` and `total` from `answers` itself and refuses anything malformed, an extra field, any version but the current one, or a wrong length (400), and a browser post from another site (403). Success is 204. It reads nothing about the request and logs nothing.
  - `GET /api/quiz/stats?version=…` returns `{count, mean, perQuestion}` for the current version only (any other is 404), from one SQL query, cached at the edge for 60 seconds. The mean and the per-question shares are returned only from 30 scores; below that, `{count, mean: null, perQuestion: null}`.
  - **The current version is built in:** every build writes `website/functions/_generated/build.json` (git-ignored) from `_data/quiz.js`, and the routes import it. The workflows ship `dist/` and `functions/` from the same build, and a deploy without a build fails to bundle: closed, never stale.
  - **Runtime switch:** both answer 404 unless the Pages environment sets `UNCOST_QUIZ_STATS_OPEN=on` AND has the `QUIZ_DB` binding, as `UNCOST_SIGNUPS_OPEN` does for the sign-ups.
- **Retention:** rows are kept for the current question set and the one before it. When the first score for a new set arrives, every row of an older set is deleted (`question_set` keeps the order of the sets, with no per-person data). This proposes the founder's suggested rule, applied at each change of question set rather than monthly.
- **The build switch, and why there are two.** The brief asks that the client send nothing before the end screen, so the page cannot ask the endpoints whether they are on before it shows its intro. Whether a reader is told about the tally is therefore decided at build time: `features.quizStatsOpen` (`UNCOST_QUIZ_STATS_OPEN=on` at build; the production workflow reads the repository variable of that name, and a PR labelled `preview-quiz-stats` builds its preview with it). In that build only:
  - **A reader with JavaScript** reads "We keep an anonymous tally of scores, with no name, email or IP address, to show the average." instead of "Your answers stay in this browser.", from the first paint (under `.quiz-js`). At the end screen `js/quiz.js` sends one POST per page load, then reads the stats.
  - **A reader without JavaScript** still reads "Your answers stay in this browser.", which stays true for them: nothing is sent.
  - **/privacy/ is version 0.6** (below).
  - **It needs `UNCOST_FORMS_OPEN=on`:** notice 0.6 builds on 0.5, and a build with the tally on and the forms off fails.

  With the build switch off (the default), the quiz is exactly as before: no request at all. With it on and the runtime switch off, the one POST gets a 404 and the reader sees their own score. So the order to turn it on is: runtime switch and binding first, then the build switch; to turn it off, the reverse.
- **The end screen:** "You got N of 10 right." then, when the stats load, "The average is X from C people. You scored above / below / the same as the average." and, in the summary's last column, "P% got this right" per question. Below 30 scores: "Not enough players yet to show an average." If a request fails, or the endpoints are off, the reader sees only their own score, never an error. The per-question reveal does not show a share: the stats load at the end screen, after the reveals.
- **Abuse control without storing IPs:** a Cloudflare rate-limiting rule on POST `/api/quiz/score`, enforced and counted by Cloudflare, not logged by us. It is listed for the founder as a dashboard step (see the pull request); nothing was created.
- **Privacy notice 0.6** (`tools/post_patch_pages.py`, patch CP-6; shown only in a build with the tally on): §2 gains "Quiz scores", §3 "Showing how others did on the quiz" (legitimate interest), §6 Cloudflare "keeps the quiz's anonymous tally of scores (Pages Functions and D1)", §7 the retention rule, and the plain-language summary one sentence. §12 gains the 0.6 row, and the header reads 0.6 with the effective date from `_data/signups.json` (`quizNoticeEffective`, empty renders "date to be set"; the founder's to set). Consent events record the version the page shows: in that build the sign-up handlers send `policyVersionQuizStats` (`privacy-notice-0.6`) instead of `policyVersion`, through `functions/_generated/build.json` and `website/lib/signup.js`. With the tally off, /privacy/ and every consent event are unchanged. **A founder decision**, with the counsel questions (whether the tally is personal data at all; the legal basis; the retention rule) for UNP-73.
- **Tests:** `website/test/quiz-stats.test.mjs` (`npm test`, now a step of the preview and production build jobs, after the build; `content-audit.yml` is a hash-pinned handoff file, so it is unchanged), against node:sqlite running the real migration: the switch, validation, the version check, the recount, the stats maths, the 30-score threshold, the cache, retention, errors, the schema's own checks, and that the routes use this build's question set. Each check was shown to fail on a deliberate fault in `lib/quiz.js`.
- **Setup is the founder's**, one step at a time (the pull request lists the exact commands): create `uncost-quiz` and `uncost-quiz-preview`, apply the migration to each, bind `QUIZ_DB` to the Pages project (production and preview databases separately), set the runtime variable, extend the rate-limiting rule, try it on a preview, set `quizNoticeEffective`, then the repository variable. Only a local D1 was used here.

## Two follow-ups (founder's calls, 2026-11-07)

- **Money and count choices are rounded** (#3, #7, #8, #10): the four choices are rounded alike, to two significant figures of the largest, and read "About …" (for example "About $18,000 · About $27,000 · About $40,000 · About $61,000"), because exact wrong choices such as $17,995 looked like real data. The reveal card, the no-JS answer, the announcement and the summary keep the exact register figure. Percent questions are unchanged.
- **SRC-018 in the summary** shows the row's whole `display_caption`, so its two halves (the total fell; chronic homelessness reached a record high) travel together, as the row's notes require (`summary: "caption"` in `_data/quiz.js`).

## Files

- **The quiz:**
  - `website/src/quiz.njk`. It is repo-authored now; `pageId` stays `later-quiz` because `sections.css` styles the page by it.
  - `website/src/_data/quiz.js`, `website/src/js/quiz.js` and `website/src/js/quiz-early.js`.
- **Styles:** `website/src/css/integration.css` item 150 (CANVAS-SYNC 191). It stacks the export's own quiz-page parts; restates the export's introband declarations for this page (sections.css draws the introband page by page and has none for `/quiz/`), minus what integration already sets for every introband, and lets the quiz band own the boundary below it; draws the choices as the pledge form's consent box and rows (`.consents`, `.crow`) with a native radio sized as the contact form's consent box; keeps the R3 figure card as R3 draws it; sets the questions at `--fs-h3` (component headings, `type_audit.py`); lets `[hidden]` win over `.actions`; and hides the answers under `.quiz-js` until `js/quiz.js` has run. Tokens and existing declarations only. No other introband draws a smaller second line, so the secondary line is styled by position (`p + p`), not by a new class.
- **The audit exemption:** `scripts/audit_website.py` (`QUIZ_CHOICE_PAGE`, `QUIZ_CHOICE_ATTR`, and six self-tests).
- **The score tally:** `website/lib/quiz.js`, `website/functions/api/quiz/score.js` and `stats.js`, `website/migrations/quiz/0001_scores.sql`, `website/test/quiz-stats.test.mjs`, `website/package.json` (`npm test`), `website/eleventy.config.js` (writes `functions/_generated/build.json`), `website/.gitignore`, `website/src/_data/features.js` (`quizStatsOpen`), `website/src/_data/signups.json` (`policyVersionQuizStats`, `quizNoticeEffective`), `website/lib/signup.js` (the recorded notice version), `website/src/privacy.njk` and `tools/post_patch_pages.py` (CP-6; one CP-4 patch gains a guard so a re-run undoes nothing), `tools/signup_check.py` (stages the generated file), and the workflows: `deploy-production.yml` (the build switch from the repository variable), `preview-deploy.yml` (the `preview-quiz-stats` label), and both build jobs (`npm test`).
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

Revert the pull request. With the tally never turned on, nothing is stored, so nothing else needs undoing. Once it has been on: turn the repository variable off and deploy (the quiz stops sending and /privacy/ returns to 0.5), then the Pages variable (the endpoints answer 404). The rows in `uncost-quiz` are anonymous; deleting them, or the database, is the founder's call.

## Provenance

The founder's brief, 2026-11-07. Drafted by Claude Code as `uncost-admin`.

# CHG-020 — The quiz's score block as three lines (amends CHG-019)

**Status:** founder request (2026-11-10). It takes effect when this record is merged and the production deploy is approved. Nothing here changes what is stored or sent, the endpoints, the privacy notice, or any Cloudflare setting.

- **Date:** 2026-11-10
- **Amends:** [CHG-019](CHG-019-quiz.md), "The end screen", which set the score block as one paragraph. That record's history stands as written.
- **Changed claim:** none. The words, figures, maths and rounding are CHG-019's; only the layout and emphasis change.
- **Source:** the founder's request, 2026-11-10. No AI decision; this file records what the founder set.

## What changes

The end screen's score block on `/quiz/` becomes up to three lines. Each line is its own paragraph, so it keeps its own row on a phone.

1. "You got **N** out of 10 right." The total is the page's own number of questions (`quiz.total`), not a typed 10.
2. "The current average score is **X.XX**."
3. "You scored **P% higher** than the average." or "You scored **P% lower** than the average." "P% higher" is green (`--sage-deep`) and "P% lower" red (`--red-deep`). "You matched the average." stays plain ink.

Each bold figure is also underlined. In these cases only line 1 shows:

- the tally is off;
- a request failed;
- there are fewer than 30 scores. In this case, line 2 is "Not enough players yet to show an average.", in plain text.

The maths and rounding are unchanged from CHG-019:

- X.XX is the mean the stats return, to two decimals.
- P is the difference from the average as a whole percent of the average.
- A difference that rounds to 0% is a match.
- With an average of 0, any other score reads "You scored **higher** than the average." (green).

- **The figures** are `strong.quiz-fig`: bold, underlined in their own colour. The words carry the meaning; the colour only repeats it.
- **Not a link:** a figure has no `href`, `tabindex` or role, so Tab passes it. It shows the text cursor, never a pointer. Its underline is 3px thick at a 5px offset; every link on the site is 1.5px or 2px thick at 2px or 3px. The lines have a line height of 1.5 and 12px between them, so each underline sits nearer its own figure than the line below.
- **The lines' own text** is the display face at 24px in ink, as before, but in regular weight instead of bold, so the bold figures stand out.
- **Contrast:** green `#4E6C41` is 5.54:1 on the card's `--cream` and red `#9E1C10` is 7.47:1. Both pass AA for body text, and so more than meet the 3:1 that 24px bold needs. The pull request has the contrast audit's measurements.
- **The announcement** (the `aria-live` region) reads line 1 at the end screen as before. When the stats arrive, it reads the whole block in order: line 1, then line 2, then line 3. Until now, the second announcement had only lines 2 and 3.

## Files

- `website/src/quiz.njk`: the block is a `div` holding three `p.quiz-line`, the first with `strong.quiz-fig` for N.
- `website/src/js/quiz.js`:
  - `compared()` returns the figure and its direction;
  - `figLine()` builds a line with its figure from text nodes, with no `innerHTML`;
  - `scoreText()` joins the lines shown, for the announcement;
  - `showStats()` fills lines 2 and 3.
- `website/src/css/integration.css` item 150: the lines; `.quiz-fig` and its two directions. Tokens only, apart from the underline's 3px thickness and 5px offset, which are new so that a figure doesn't look like a link. CANVAS-SYNC row 191.
- **Records:** `docs/CANVAS-SYNC.md` (row 191), CHG-019 (a pointer here) and this record.

**Not changed:** the summary table, the verdicts, the share panel, the endpoints and the stored data, `_data/quiz.js` (the question set's version stays `65d42dabffaf`), the privacy notice.

## Checks

On branch `quiz-score-lines`, against `main` at `d5a0de3`. The pull request lists the results and the screenshots: the four end screens (higher, lower, matched, under 30) at desktop and phone width.

## Rollback

Revert the pull request. Nothing is stored differently, so nothing else needs undoing.

## Provenance

The founder's request, 2026-11-10. Drafted by Claude Code as `uncost-admin`.

# Canvas sync — approved changes the export has not made yet

Changes the founder approved and this repository implements, which the design
canvas has **not** made. Each one therefore diverges from the export on purpose,
so each carries a named exemption in `tools/render_gate.py` (with the same
justification) and appears here.

The point of this file is that the divergence stays visible. A change listed
here should end up in the canvas and arrive by re-export; when it does, delete
its row **and** its gate exemption in the same commit, so the gate goes back to
measuring that section.

| # | Change | Where implemented | Gate exemption |
|---|---|---|---|
| 6 | Homepage S5: drop the closing note ("Water is next…") and move the "All fifteen sectors" button into its position. | `website/src/index.njk`, `_data/home.json` | `index.html :: S5 Where we start` |
| 7 | Sector hero illustration at double size on all 15 pages, position and aspect unchanged. Driven from `.sector-illus-slot`, so the illustration keeps its right-bottom anchor and identical Y across sectors. | `website/src/css/integration.css` | `sectors/ :: Sector head` |
| 8 | `/projects/` — "Every project has to earn its cost claim." matched to the page's other section-heading size. | `website/src/css/integration.css` | `projects.html :: How they help` |
| 9 | `/receipts/` — add the ink headline below the "The rule, three ways" eyebrow: "If we can't show where a number came from, we don't print it." The export ships the eyebrow straight into the three-column grid with no headline. | `website/src/receipts.njk` | `receipts :: The rule` |

## Blocked, not implemented

| # | Change | Status |
|---|---|---|
| 5 | Sector-page related-projects section restyled to the canvas **Ledger** table component. | **Waiting on the snippet from Claude Design.** The data and columns are already correct — ID / Project / Role for *[Sector]* / Status, from the same source — so only the component's markup and styling are missing. Not invented here: guessing at a named canvas component would produce something that has to be undone when the real one lands. |

## Also worth folding into the canvas

Not founder-requested changes, but corrections this build carries that the
export keeps re-shipping. They are re-applied automatically by
`tools/post_patch_css.py` and `tools/post_patch_pages.py` after every adoption.

- **WCAG 2.2 AA** — the export puts `#FFFFFF` (4.32:1) or `--ink` (4.47:1) on
  brand coral and `--link: var(--coral)` (4.04:1) on cream. All below the 4.5
  floor. See `website/design-system/AUTHORITY.md`.
- **Focus-ring visibility** — a `--coral` ring on a coral fill measures ~1:1.
- **Heading levels** — the export skips a level on about, roadmap, the policies
  index and the project At-a-glance grid.
- **21 undefined classes** — v4.3's pages reference classes its stylesheets do
  not define (116 occurrences); recovered in
  `website/src/css/integration-v43-gap.css`. Worth an §A0 check: *every class a
  page references is defined by the stylesheets*.

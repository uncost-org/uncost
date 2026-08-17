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
| 5 | Sector pages' Related projects section rendered with the canvas **Ledger** component (`.lg`), four-column variant: ID / Project / Role for *[Sector]* / Status. Same rows and data as the list it replaces. The component's `<style>` block was moved into the shared stylesheet — CSP is `style-src 'self'`, so an inline `<style>` would not apply, and the extraction rule holds regardless. Class names unchanged, so it drops in when the canvas ships it in `sections.css`. | `website/src/css/integration.css`, `website/src/sectors/sector.njk` | `sectors/ :: Related projects` |
| 6 | Homepage S5: drop the closing note ("Water is next…") and move the "All fifteen sectors" button into its position, with the vertical gap the note used to provide restored beneath the sector grid. | `website/src/index.njk`, `_data/home.json` | `index.html :: S5 Where we start` |
| 7 | Sector hero illustration **sized to fit its column** on all 15 pages. The first attempt (a fixed slot height, ~2x) made the box taller than the column was wide, so `object-fit: contain` letterboxed the artwork and the empty space read as the illustration wrapping below the title. Width now drives: the artwork fills the column and the slot takes its height from the fixed 1531x1029 aspect — 564x379 at 1440 against the original 432x290 (+30% linear, +70% area), no letterboxing at any width, and the identical-Y guarantee verified at 279px across all 15. | `website/src/css/integration.css` | `sectors/ :: Sector head` |
| 8 | `/projects/` — "Every project has to earn its cost claim." matched to the page's other section-heading size. | `website/src/css/integration.css` | `projects.html :: How they help` |
| 10 | Footer: the "RSS" link is removed — no feed or feed page exists. | `_data/chrome.json` | *(chrome; no section exemption — the footer sits outside `<main>`)* |
| 11 | Footer: the bottom bar no longer repeats links already in the columns above it. Deduplicated by **target**, not label, since the columns carry "Corrections & changelog" pointing at the same `/receipts/#corrections`. Only "Accessibility" remains. | `_data/chrome.json` | *(chrome; outside `<main>`)* |
| 12 | `/receipts/` — the "A figure, fully dressed" demo section is removed; the register band takes the whiter cream; each figure's title links to its registered source URL (all 22 rows have one). | `website/src/receipts.njk` | `receipts :: The register` |
| 9 | `/receipts/` — add the ink headline below the "The rule, three ways" eyebrow: "If we can't show where a number came from, we don't print it." The export ships the eyebrow straight into the three-column grid with no headline. | `website/src/receipts.njk` | `receipts :: The rule` |

## Flagged for Claude Design

- **Related-sectors status chips.** The related-sectors block on sector pages was
  asked to carry the coloured FOCUS / NEXT / FUTURE STUDY / DOSSIER chips the main
  sector cards have. **The export does not define a chip there** — its markup is a
  coloured square plus the sector name (`<span class="u-149 sq"></span> Water`) and
  nothing else. Not added here: inventing a chip position for a named canvas block
  is how the build and the canvas drift apart. Needs a canvas decision.

## Nits to fix in the canvas

Adopted as delivered rather than silently "corrected", so the canvas and this
repository do not drift:

- `ledger-table` uses a raw `#FFF` on `.lg` where `--white` exists, and a
  `#B23A14` literal as the `var(--coral-deep, …)` fallback on `.src a`. Both are
  the only raw hex values the component carries.

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

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
| 13 | Nav labels: "Sectors" → "Cost of Living Sectors" (The Case); "Dashboard" → "Human Essentials Dashboard" and "Tracker" → "Cost of Living Tracker" (The Projects); "How it works" → "How the Assembly works" (The Assembly). "Dashboard" removed from The Case, ambiguous against the Projects entry. | `_data/chrome.json` | *(chrome; outside `<main>`)* |
| 14 | `/accessibility/` — new page carrying the accessibility statement that was the bottom section of About; the footer "Accessibility" link now points at it. **Resolved 2026-08-22:** the slot About was left with now carries the UNP-82 v1 §2 member-voice section (“You get a genuine say, not a spectator seat.”); no marker remains. | `website/src/accessibility.njk`, `about.njk`, `_data/chrome.json` | *(new route; no export counterpart)* |
| 12 | `/receipts/` — the register band takes the whiter cream; each figure's title links to its registered source URL (all 22 rows have one). **Amended 2026-08-22:** the earlier removal of the "A figure, fully dressed" section is reversed — UNP-82 v1 §4c dresses it with a real register row (SRC-023) instead of the export's `$X` placeholder, so the section returns without the illustrative markers or the placeholder disclaimer. | `website/src/receipts.njk`, `tools/post_patch_pages.py` | `receipts :: The register`, `receipts :: Worked example` |
| 9 | `/receipts/` — add the ink headline below the "The rule, three ways" eyebrow: "If we can't show where a number came from, we don't print it." The export ships the eyebrow straight into the three-column grid with no headline. | `website/src/receipts.njk` | `receipts :: The rule` |

| 15 | `/receipts/` — the hero gains a one-line statement of the publishing rule under the H1 (“Source, date, region — or it doesn’t publish.”). The band takes the export’s own `.u-block--ink` so the text inherits cream-on-ink; only the lead’s centring is new CSS. | `website/src/receipts.njk`, `website/src/css/integration.css` | `receipts :: Receipts — title` |
| 16 | `/receipts/` — a one-line note that the four confidence labels and the sector/project status badges are deliberately separate systems. Closes the conflict UNP-82 v1 escalated. | `website/src/receipts.njk` | `receipts :: Confidence labels` |
| 17 | `/receipts/` — the corrections launch-state no longer says “no public figures have been published yet”, which contradicted the 22-row register rendered above it on the same page. Badge follows: “Log begins at launch” → “No corrections logged yet”. | `website/src/receipts.njk` | `receipts :: Corrections` |
| 18 | `/receipts/` — the register lead said “Eleven sourced figures” against 22 rendered rows. The count is now rendered from the register, so it cannot drift again. | `website/src/receipts.njk` | `receipts :: The register` |
| 19 | `/news/` — **Cost Watch is no longer a hand-curated reading list.** It renders the register’s own `placement=news-feed` rows, so each entry is a sourced, dated figure under the same rule as the rest of the site. The export’s three hardcoded third-party links and its “inclusion isn’t endorsement” note went with that model. | `website/src/news/index.njk`, `website/src/_data/register.js` | `news :: Cost Watch`, `news :: News — title` |
| 20 | `/sectors/` — the intro band carries the approved copy: it names all fifteen sectors and states the year-one order (Shelter, Food, Energy, then Water) instead of the one-line summary. | `website/src/sectors/index.njk` | `sectors :: Sectors — title` |
| 21 | Project pages ×7 — every dossier field now carries differentiated, founder-approved copy from `_data/projectContent.js` instead of shared boilerplate, and the “Related sectors” section gains a primary/secondary role line. Stage chips read **Draft** rather than the export’s “In development”, which every dossier’s `status: draft` contradicts. | `website/src/projects/project.njk`, `website/src/_data/projectContent.js` | `projects/* :: Project head`, `At a glance`, `Overview`, `Funding & status`, `Related sectors`, `Project CTA` |
| 22 | `/about/` — the slot vacated by the accessibility statement carries the UNP-82 v1 §2 member-voice section on the Assembly and the privacy commitment. | `website/src/about.njk` | `about :: Your say` |
| 23 | `/downloads/the-case-for-uncost.pdf` — the 14-page publication is committed and served first-party, hash-pinned in `docs/CONTROL.md`. No on-page download block yet: its copy is in the v2 content document, which has not reached the repository. | `website/assets/downloads/`, `website/eleventy.config.js`, `docs/CONTROL.md` | *(asset; no section)* |
| 24 | `/movement/` — **full copy rewrite** (UNP-82 v2 (a)): identity and offer, not audience-capture strategy. The export's "How it reaches people" (distribution mechanics) and the three Pledge/quiz/share-a-stat cards are gone; the body is now what the movement *is*, what taking part means, and the Assembly. Block 1 uses the export's own `.blk--first` in place of the introband, because v2 writes it as eyebrow + lead + body rather than the introband's h2 + p. The ink block's button row is dropped — v2's specified `[Sign the Pledge] [Get updates]` are the coral CTA directly below, which already renders exactly those two. | `website/src/movement.njk` | `movement :: What this is`, `What we stand for`, `What taking part means`, `How to take part` |
| 25 | `/case/` — UNP-82 v2 (b) additions: **b1** the mechanism argument as a new section after the hero (SRC-020 + SRC-024 through the register macro); **b2** the six-step "How a cost gets uncosted" method inside the export's own Methodology drawer, alongside "The rules" and "Confidence labels"; **b3** the closing lead above the unchanged "Evidence first. Tools next."; **b5** the PDF download line under the hero lead. | `website/src/case/index.njk` | `case :: The mechanism`, `The Case — title`, `Methodology drawer`, `Case CTA` |
| 26 | `/case/` — **content restoration, not a design change.** The v4.3 re-derivation replaced the essay page with the export's dashboard preview and dropped the register-backed "What living costs" section with it. Under the standing authority split the export owns look and the repo owns content, so the section is restored from `origin/main` @ `94d2481` and rendered in the export's receipts vocabulary via `figure.njk`. Carries four real figures — SRC-004, **SRC-021** (v2's b4, directly after SRC-004), SRC-023, SRC-005 — placed after the b1 mechanism section, before the dashboard-preview material. The export's KPI/basket `$X` placeholders stay exactly as shipped: they are the honest labelled preview of a tool that isn't built. Real figures argue the case; labelled placeholders preview the tool. | `website/src/case/index.njk` | `case :: What living costs` |
| 27 | `/news/` Cost Watch now renders **four** register rows, not one. Founder-confirmed 2026-08-22 after browser-rendered verification of each source: SRC-017 refreshed ($4.049, week ending 2026-08-17) and SRC-025/026/027 added (CPI-U all items +3.4%, food at home +2.7%, energy +14.7%, July 2026). SRC-023 refreshed to the July print and SRC-024 added in the same write. No template change was needed — `placement=news-feed` drives it. | `sources/register.csv` | `news :: Cost Watch` |
## Nits to fix in the canvas

Adopted as delivered rather than silently "corrected", so the canvas and this
repository do not drift:

- `ledger-table` uses a raw `#FFF` on `.lg` where `--white` exists, and a
  `#B23A14` literal as the `var(--coral-deep, …)` fallback on `.src a`. Both are
  the only raw hex values the component carries.

- `sectors.html` marks its three year-one cards `class="scard focus"`, but no
  export stylesheet has ever defined `.focus` — not v3.1, not v4.3 — so the
  modifier renders nothing and the three focus cards are visually identical to
  the other twelve. Recorded rather than invented: giving `.focus` a treatment
  here would be authoring design. It is the site's only undefined class
  reference (3 occurrences, all on `/sectors/`).

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

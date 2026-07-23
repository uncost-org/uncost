# receipts

- route note: Receipts-first explainer
- export page: project/site/receipts.html
- dossier: none
- purpose: Explains Uncost's open methodology and source layer to a reader — the rule that every published number has a source, a date, and a stated confidence, plus how confidence labels work, how figures are kept current, and how corrections are logged.

---

Note on tags: this page has no dossier. Blocks marked `DOSSIER-BACKED` cite the July controlling source (`docs/MOVEMENT_PLAN.md`), the only citable source available for this page. Blocks with no dossier and no July-source basis are marked `DESIGN-AUTHORED (no source)`.

---

> DESIGN-AUTHORED (no source)

## Receipts — title

The Receipts

---

> DOSSIER-BACKED: MOVEMENT_PLAN.md "The snapshot" (Trust posture: receipts first) and "How a cost gets uncosted" step 2 (Publish sources, dates, methods, and confidence)

## Intro band

Every number, out in the open.

The Receipts is the methodology and source layer under everything we publish. The rule is simple: every number has a source, every source has a date, and every model states its assumptions. If a claim can't be sourced, we label it — plainly — as an estimate, a scenario, or a hypothesis, not a fact.

---

> DOSSIER-BACKED: MOVEMENT_PLAN.md "How a cost gets uncosted" step 2 (sources, dates, methods, and confidence) — the three-way split (Sourced / Dated / Labelled) is a design-authored elaboration of that single source line

## The rule

The rule, three ways

01 — Sourced
Every figure carries a source and a license, so anyone can trace it back and reuse it lawfully.

02 — Dated
Every source shows when it was captured and when it was last reviewed. Stale data is flagged, not hidden.

03 — Labelled
Every figure carries a confidence tag, and anything hypothetical is marked illustrative — unmissably.

---

> DESIGN-AUTHORED (no source)
Note: The July source references "confidence" (MOVEMENT_PLAN.md "How a cost gets uncosted" step 2) but does not enumerate these four specific labels or their definitions. This four-label vocabulary is authored by the design and is distinct from the honest-status vocabulary fixed in CONTROL.md (`status--{live, dev, planned, focus, next, dossier, future}`, changed 2026-07-22).

## Confidence labels

What the confidence tags mean

Four honest labels.

| Label | What it tells you |
| --- | --- |
| Confirmed | Drawn directly from a named, dated, licensed public source. Check it yourself. |
| Estimate | Derived from sourced inputs plus stated assumptions. The assumptions are published alongside. |
| Scenario | A modelled "what if" — a possible outcome under specific conditions, not a prediction. |
| Needs refresh | The underlying source is past its review date. Treat with caution until updated. |

Illustrative only — any hypothetical figure on the site carries this hatched marker, so a placeholder is never mistaken for real data.

---

> DESIGN-AUTHORED (no source)
Note: This block is an explicitly illustrative placeholder demo. The figure "$X" and date "[date]" are marked "Illustrative only" and "Scenario," so they are not uncited factual claims — they are labelled placeholders.

## Worked example

What the furniture looks like in place

A figure, fully dressed.

$X
Monthly essential basket for one adult, Region A
SOURCE — Uncost Basic Needs Cost Model
Last updated: [date]
Scenario
Illustrative only

Placeholder figure shown to demonstrate the format. Real dashboard figures will replace $X and [date] with sourced values, and drop the illustrative marker only when a real, dated source stands behind them.

---

> DOSSIER-BACKED: MOVEMENT_PLAN.md "The snapshot" (Flagship: regional, source-led Human Essentials Dashboard) and "Current ask" (multi-region Human Essentials Dashboard is near-term funding work) — the "funding priority" framing derives from the July source; the specific mechanics (visible last-updated dates, regular review cadence) are a design elaboration

## Keeping current

Because data goes stale

Built to stay current.

The dashboards pull from public sources where possible, show visible "last updated" dates, and follow a regular review cadence. Automating those data pipelines is a funding priority — precisely so the evidence stays fresh instead of decaying quietly.

---

> DOSSIER-BACKED: MOVEMENT_PLAN.md "The snapshot" (Trust posture: receipts first, open corrections)

## Corrections

Corrections & changelog

We log our mistakes.

Every correction is recorded publicly with a date and a plain description of what changed and why. Nothing is quietly edited. The full version-controlled history lives in the public records.
⚠ DIVERGES FROM JULY SOURCE: the "public records" link points to `github.com/uncost-org/uncost`, but CONTROL.md names the merged canon repository as `dafuqindustries/portfolio-canon`. Surfacing the repo-pointer mismatch — source wins.
⚠ UNCITED: that a public, version-controlled corrections history exists at `github.com/uncost-org/uncost` (link target unverified against CONTROL.md).

Log begins at launch
No public figures have been published yet, so there's nothing to correct. The moment the first sourced number goes live, this log starts — and stays append-only.
⚠ REPO-VERIFIABLE (sources/register.csv — no published cost-stat sources registered): "No public figures have been published yet" — a state assertion with no cited source (consistent with the pre-launch posture in MOVEMENT_PLAN.md "Current ask," but not itself sourced on this page).

View public records on GitHub (links to https://github.com/uncost-org/uncost)

---

> DESIGN-AUTHORED (no source)

## Receipts CTA

Found a number we got wrong?

Corrections get priority. Tell us what's off and point us at the better source.

Report a correction (links to contact.html)
Back to The Case (links to case.html)

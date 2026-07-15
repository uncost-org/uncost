---
title: "PRJ-001 — Human Essentials Dashboard"
created: 2026-06-12
updated: 2026-07-16
version: "1.3"
status: draft
review_status: independent-claude-review-pending
registry_status: final-control-aligned
privacy: public
---

> **DRAFT — NOT APPROVED FOR BUILD OR LAUNCH.** Independent Claude review, founder review, and relevant domain/professional review are pending. Roadmap dates are movable targets.

# PRJ-001 — Human Essentials Dashboard

## Snapshot
- **Project:** Human Essentials Dashboard — the flagship of The Case.
- **Role in the system:** presentation layer of a three-part system. PRJ-002 (Cost-of-Living Tracker) supplies current and historical price data; PRJ-003 (Basic Needs Cost Model) supplies reduction scenarios; PRJ-001 presents both to the public. The three ship as one experience.
- **Status:** Draft; existing UI concepts are reusable design input, but data pipeline, methodology, and public implementation are not authorized.
- **Roadmap:** First public cost visual targets the first 90 days (through 2026-10-13); a 2–3-region dashboard prototype targets Months 4–6 (approximately 2026-10-15 to 2027-01-15). Dates are movable and gates control.

## Sectors
- **Primary:** Shelter, Food, Energy (the Year-1 focus sectors — the plan's stated first-phase emphasis).
- **Secondary (data lines as sources allow):** Water, Transportation, Healthcare*, Communication. (*Healthcare appears as a measured cost line only; the sector itself remains future-study — measuring what people pay is in scope, intervention claims are not.)
- **Cross-cutting handling (methodology decision required):** Environment, Safety, and Materials are cost *drivers*, not monthly basket line-items. The dashboard treats them as overlays/drivers, not basket rows, and the methodology page says so explicitly — otherwise the plan's "each part of the basket maps to a sector" claim becomes an attack surface.

## The problem and the cost being reduced
People argue about the cost of living with vibes and headlines. The dashboard replaces that with sourced, dated, regional numbers: what essentials cost, how that compares to income, whether the gap is closing, and where automation or shared infrastructure could plausibly reduce it. The "cost" it reduces directly is the information cost of knowing the truth; everything else in the movement builds on it.

## What it is / what it is not
It is a public, regional, source-led evidence product where every figure carries a source, date, and confidence label. It is not a benefits calculator, not financial advice, not a real-time price feed, not a policy scorecard, and not a promise that any listed automation path will be built.

## MVP deliverables
1. Public dashboard for **2–3 launch regions** across the three focus sectors, with the honest coverage banner ("Data available for N of M regions" — N is whatever is real, even if it is 2).
2. Basket definition v1 per region (what "essentials" includes, published as a methodology page).
3. Historical trend view (the final plan's requirement: tracking whether interventions actually work requires history from day one).
4. Per-figure receipts: SRC- ID, source name, date, confidence badge.
5. Public methodology + corrections/changelog page.

**Explicitly cut from MVP:** user accounts, comparisons between more than ~3 regions, income-adjusted personalization, API access, non-focus sectors, forecasting.

## How it works
Region → basket → line-items → sources. Each line-item stores value, unit, region, date, SRC- reference, confidence, and collection method. The Tracker (PRJ-002) writes the data; the Model (PRJ-003) writes scenario records against the same line-items; the public interface must render both with receipts furniture: source labels, last-updated stamps, confidence badges, and illustrative flags.

**Confidence taxonomy (plan-canonical, plus one addition):** `confirmed` / `estimate` / `scenario` / `needs refresh`, plus **`derived`** for figures calculated from two or more sources (e.g., a "% of military spend" ratio) — derived figures display all contributing SRC- IDs, never a single source badge.

## AI role and human gates
AI assists source discovery, extraction, normalization, freshness checks, and draft annotations. Humans approve every public figure, every methodology change, and every correction (POL-007). No figure publishes without a human-verified SRC- entry.

## Success metrics (MVP)
100% of public figures carry SRC- IDs and confidence labels; 0 unlabeled derived figures; 2–3 regions live across 3 sectors; freshness SLA met (no `confirmed` figure older than its stated refresh window without flipping to `needs refresh`); a public corrections log with ≥0 entries handled per process (the log existing matters more than it being empty); dashboard cited by at least one external writer/researcher in the first 6 months.

## Resource posture

No budget is approved. Resourcing requires a separate plan, evidence, and founder approval after the applicable policy, sponsor, methodology, safety, legal, and partner gates. Historical estimates are not authorization.

## Timeline (phase-gated, no calendar dates)
Gate 1: basket + methodology v1 drafted → Gate 2: first region's focus-sector data fully sourced → Gate 3: internal red-team of every figure → Gate 4: public launch with corrections process live. Rough effort: 8–14 weeks of focused work after PRJ-002's first data delivery.

## Risk level and policy dependencies
- **Risk level:** medium (reputational — the receipts page failing its own standard is the worst possible failure mode).
- **Safety review required:** no (no vulnerable-person contact).
- **Policy dependencies:** POL-002 (analytics privacy), POL-007 (AI claims gates), POL-009 (source data licenses recorded in the SRC- register before republication), POL-001 (figures touching government programs get election-season review).

## Dependencies and sequencing
Requires PRJ-002 data first; PRJ-003 scenarios can follow launch. Blocks: The Case page going live with real data; share-a-stat assets (which must pull only from published, SRC-backed figures).

## Open questions / decision records needed
DR needed: basket composition per launch region; DR needed: which 2–3 launch regions (recommend one US metro, one non-US, founder's call); DR needed: cross-cutting sector display treatment (driver overlay vs. exclusion at MVP).

## Public summary
The Human Essentials Dashboard shows what the essentials of life actually cost, region by region, with a source and date behind every number — and tracks whether those costs are falling over time.

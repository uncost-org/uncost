---
title: "PRJ-002 — Cost-of-Living Tracker"
created: 2026-06-12
updated: 2026-07-16
version: "1.3"
status: draft
review_status: independent-claude-review-pending
registry_status: final-control-aligned
privacy: public
---

> **DRAFT — NOT APPROVED FOR BUILD OR LAUNCH.** Independent Claude review, founder review, and relevant domain/professional review are pending. Roadmap dates are movable targets.

# PRJ-002 — Cost-of-Living Tracker

## Snapshot
- **Project:** Cost-of-Living Tracker — the data layer of The Case.
- **Role in the system:** supplies current and historical price data to PRJ-001 (presentation) and PRJ-003 (scenarios). It has no public surface of its own beyond the SRC- register; its product is trustworthy data.
- **Status:** Draft; not started. First data deliverable on the public evidence critical path.
- **Roadmap:** First source library targets the first 90 days (through 2026-10-13). It precedes public dashboard data. Dates are movable and source/licence gates control.

## Sectors
- **Primary:** Shelter, Food, Energy. **Secondary:** Water, Transportation, Communication, Healthcare (cost lines only). Expansion follows the sector roadmap, not enthusiasm.

## The problem and the cost being reduced
Every claim the movement makes stands on data someone collected, dated, and licensed properly. Without a disciplined tracker, the dashboard becomes screenshots of other people's numbers — undated, unlicensed, unmaintainable. The cost reduced is the recurring labor of finding, verifying, and re-verifying cost data, done once and shared openly.

## What it is / what it is not
It is a versioned dataset plus a source register plus a refresh process. It is not a scraper farm (official and licensed sources first), not a real-time feed, and not an analysis product — interpretation lives in PRJ-003 and the dossiers.

## MVP deliverables
1. **SRC- register v1** (the final plan's public source prefix): every source gets an ID, publisher, URL, license, refresh cadence, region coverage, and reliability note. The register itself is public.
2. Normalized line-item dataset for the launch regions' focus sectors: value, unit, currency, region, date-observed, SRC- reference, confidence, collection method.
3. Refresh calendar with staleness flags (auto-flip to `needs refresh` past each source's cadence).
4. Version history from record one — the dashboard's historical view depends on it.
5. Export feeding PRJ-001, plus a small "fact card" export feeding share-a-stat so social assets can only be generated from published, SRC-backed figures.

**Explicitly cut:** crowd-sourced price submission (privacy and quality problems; revisit post-launch with POL-002 review), commercial data purchases, any source whose license forbids republication.

## How it works
Official-statistics-first hierarchy: national statistical agencies and international bodies → regulators and utilities → reputable research institutions → licensed commercial indices only where irreplaceable and affordable → never sources that fail the license check. Each source's terms are recorded at intake (POL-009); anything with republication limits is marked and the dashboard renders it as "view at source" rather than reproducing it.

## AI role and human gates
AI does source discovery, document extraction, unit normalization, anomaly flagging ("this rent figure moved 40% in one refresh — verify"), and staleness monitoring. A human approves every source at intake and every figure before it becomes publishable (POL-007).

## Success metrics (MVP)
Every published figure traceable to a registered SRC- in ≤2 clicks; 100% of sources with recorded licenses; ≥90% of `confirmed` figures within their refresh window at any time; zero republished data whose license forbids it; anomaly-flag review time under one week.

## Resource posture

No budget is approved. Resourcing requires a separate plan, evidence, and founder approval after the applicable policy, sponsor, methodology, safety, legal, and partner gates. Historical estimates are not authorization.

## Timeline (phase-gated)
Gate 1: SRC- register schema + first 10 sources licensed and logged → Gate 2: one region's focus sectors fully populated → Gate 3: refresh process runs one full cycle cleanly → hand off to PRJ-001. Rough effort: 6–10 weeks.

## Risk level and policy dependencies
- **Risk level:** low-medium (licensing errors and stale data are the failure modes).
- **Safety review required:** no.
- **Policy dependencies:** POL-009 (license register — hard dependency), POL-007 (extraction verification), POL-002 (no personal data enters the dataset).

## Dependencies and sequencing
Blocks PRJ-001 and PRJ-003; blocked by nothing. This is the correct first build of the whole project stack.

## Open questions / decision records needed
DR needed: launch regions (shared decision with PRJ-001); DR needed: currency handling for cross-region views (display local + normalized, or local only at MVP — recommend local only, normalize later).

## Public summary
The Cost-of-Living Tracker is the movement's data backbone: a public register of every source we use and a versioned dataset of what essentials cost, kept fresh on a published schedule.

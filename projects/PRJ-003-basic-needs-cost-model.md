---
title: "PRJ-003 — Basic Needs Cost Model"
created: 2026-06-12
updated: 2026-07-16
version: "1.3"
status: draft
review_status: independent-claude-review-pending
registry_status: final-control-aligned
privacy: public
---

> **DRAFT — NOT APPROVED FOR BUILD OR LAUNCH.** Independent Claude review, founder review, and relevant domain/professional review are pending. Roadmap dates are movable targets.

# PRJ-003 — Basic Needs Cost Model

## Snapshot
- **Project:** Basic Needs Cost Model (canonical name per the final-control registry; "Basic Needs Cost Dashboard" retained as alias).
- **Role in the system:** the scenario layer of The Case. PRJ-002 says what things cost; this model says which parts of that cost are plausibly reducible, how, and under what assumptions. PRJ-001 presents both.
- **Status:** Draft; not started. Follows PRJ-002 baseline and methodology work.
- **Roadmap:** Begins after PRJ-002 has a reviewed baseline and methodology; contributes to the Months 4–6 prototype. No hard date or budget is authorized.

## Sectors
- **Primary:** Shelter, Food, Energy. **Secondary:** none at MVP — scenario modeling is expensive to do honestly; depth beats coverage.

## The problem and the cost being reduced
The movement's core claim is that automation can reduce specific costs. That claim is only credible decomposed: this cost splits into labor, energy, land, materials, waste, market structure, financing, fees, and policy; automation bites *these* components, by roughly *this much*, if *these* assumptions hold. The model is the machine that produces that decomposition — and, critically, that publishes when the answer is "automation doesn't win here."

## What it is / what it is not
It is a transparent scenario model with published assumptions, ranges, and sensitivity notes, implementing the plan's six-step mechanism (measure → publish → break down → match → package → track). It is not a forecast, not investment analysis, not a promise, and not a black box — every scenario is reproducible from its published inputs.

## MVP deliverables
1. **Cost-stack decomposition template** — the standard structure splitting any essential's cost into its components with a SRC- reference per component.
2. **Intervention library v1:** a structured record per mechanism (automation type, which cost components it addresses, capital/energy/maintenance requirements, evidence quality, regulatory constraints), seeded from the three focus sectors.
3. **Three worked scenarios** — one per focus sector, including the plan's food example done with real regional numbers, and at least the Shelter scenario confronting the land/entitlement problem head-on (the decomposition must show where automation cannot bite).
4. **Negative-results protocol:** scenarios where the intervention loses to the status quo once full capital, energy, maintenance, safety, and operating costs are counted are published with the same prominence as wins (plan commitment, made mechanical).
5. External expert review of methodology before anything ships publicly.

**Explicitly cut:** user-adjustable public modeling UI (post-MVP), non-focus sectors, region counts beyond the launch set.

## How it works
Each scenario: baseline cost stack (from PRJ-002 data) → intervention applied to specific components → modeled range with stated assumptions → confidence label (`scenario`, always) → sensitivity note (which assumption moves the result most) → verdict including "no net reduction plausible here." Scenarios version like code; changes get changelog entries.

## AI role and human gates
AI drafts decompositions, searches intervention evidence, runs sensitivity variations, and flags internal inconsistencies. Humans set assumptions, approve every published scenario, and sign the negative-results calls (POL-007). No scenario publishes without external expert review at MVP.

## Success metrics (MVP)
Three published scenarios with full assumption sets; ≥1 published negative or null result in the first batch (if all three come out positive, the red-team asks why); every scenario reproducible by an outsider from published inputs; at least two external reviewers signed off per scenario; zero scenarios quoted publicly without their `scenario` label.

## Resource posture

No budget is approved. Resourcing requires a separate plan, evidence, and founder approval after the applicable policy, sponsor, methodology, safety, legal, and partner gates. Historical estimates are not authorization.

## Timeline (phase-gated)
Gate 1: decomposition template + methodology reviewed → Gate 2: intervention library seeded for focus sectors → Gate 3: three scenarios drafted and red-teamed → Gate 4: external review → publish through PRJ-001. Rough effort: 10–16 weeks after PRJ-002's first delivery.

## Risk level and policy dependencies
- **Risk level:** medium-high (this is where the movement is most attackable — overclaiming here damages everything).
- **Safety review required:** no direct contact risk; methodology review is the analogous gate.
- **Policy dependencies:** POL-007 (hard gates on claims, uncertainty language, no overpromising), POL-001 (scenarios touching policy-driven costs stay education-framed), POL-009 (intervention evidence sources licensed and registered).

## Dependencies and sequencing
Blocked by PRJ-002 (needs real baselines). Blocks: sector dossiers' quantitative sections; any project brief that claims a cost-reduction range; PRJ-004 and PRJ-007, which consume its intervention library.

## Open questions / decision records needed
DR needed: reviewer panel composition and honoraria policy; DR needed: how ranges display publicly (recommend ranges only, never point estimates).

## Public summary
The Basic Needs Cost Model breaks each essential's cost into its real components and tests — openly, with published assumptions — where AI, robotics, and shared infrastructure can genuinely reduce it, and where they can't. When the honest answer is "this doesn't work here," we publish that too.

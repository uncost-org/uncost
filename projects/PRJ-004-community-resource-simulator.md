---
title: "PRJ-004 — Community Resource Simulator"
created: 2026-06-12
updated: 2026-07-16
version: "1.3"
status: draft
review_status: independent-claude-review-pending
registry_status: final-control-aligned
privacy: public
---

> **DRAFT — NOT APPROVED FOR BUILD OR LAUNCH.** Independent Claude review, founder review, and relevant domain/professional review are pending. Roadmap dates are movable targets.

# PRJ-004 — Community Resource Simulator

## Snapshot
- **Project:** Community Resource Simulator.
- **Role in the system:** the "what if, for us" layer. Takes an *existing* community's real context and compares candidate interventions from PRJ-003's library against it. Distinct from PRJ-007 (Basic Needs Planner), which sizes what a *proposed or planned* site would need — the simulator compares options for a place that already exists; the planner drafts requirements for one that doesn't yet.
- **Status:** Draft; not started. Year 2 direction.
- **Roadmap:** Year 2 direction, after the Case trio is credible and intervention records exist. Dates are movable.

## Sectors
- **Primary:** Energy, Food, Goods (the three with the most community-runnable interventions: shared solar, community growing, tool libraries). **Secondary:** Water, Materials.

## The problem and the cost being reduced
Community groups considering a shared resource face weeks of bespoke feasibility guesswork. The simulator reduces that planning cost: enter your community's basics, pick candidate interventions, get an honest comparison with ranges — enough to decide whether a real feasibility study is worth commissioning.

## What it is / what it is not
It is a decision-support comparison tool producing labeled, range-based scenarios. It is not an engineering assessment, not a permit application, not a financing plan, and never a substitute for licensed professionals — every output carries that disclaimer, structurally, not as fine print.

## MVP deliverables
1. Community intake schema (size, region, relevant costs from PRJ-002 where covered, existing assets).
2. Three intervention modules — shared solar + storage, tool library (consuming PRJ-005's kit economics), community food growing — each built on PRJ-003's intervention records.
3. Comparison output: modeled range per intervention, key assumptions surfaced, sensitivity note, "what a real feasibility study would need to check" list.
4. **False-precision guardrails:** ranges only; deliberately coarse inputs; a hard rule that outputs cannot render a single-number "you will save $X."
5. Two pilot runs with real community groups, published as case studies with their consent (POL-002).

**Explicitly cut:** automated site assessment, financing modeling, contractor matching, any sector with safety-gated interventions.

## AI role and human gates
AI drives guided intake, matches context to intervention records, drafts the comparison narrative, and flags missing assumptions. Humans review every published case study and the module logic; the tool self-labels as automated per POL-007.

## Success metrics (MVP)
Two pilot communities complete the flow and rate the output actionable; zero outputs presenting point estimates; every module's assumptions traceable to PRJ-003 records; at least one pilot proceeding to a real feasibility step (the tool's actual purpose).

## Resource posture

No budget is approved. Resourcing requires a separate plan, evidence, and founder approval after the applicable policy, sponsor, methodology, safety, legal, and partner gates. Historical estimates are not authorization.

## Timeline (phase-gated)
Gate 1: intake schema + one module → Gate 2: three modules with guardrails verified → Gate 3: pilots → Gate 4: public release. Rough effort: 10–14 weeks after PRJ-003's intervention library exists.

## Risk level and policy dependencies
- **Risk level:** medium (users over-trusting outputs is the failure mode; guardrails are the mitigation).
- **Safety review required:** only if a pilot community involves vulnerable populations (then POL-008 applies).
- **Policy dependencies:** POL-007 (labeling, no overclaiming), POL-002 (pilot community data), POL-008 (conditional).

## Dependencies and sequencing
Blocked by PRJ-003 (intervention library) and partially PRJ-005 (tool-library economics). Feeds PRJ-007's eventual planner with validated module logic.

## Open questions / decision records needed
DR needed: pilot community selection criteria; DR needed: whether outputs are public by default or private to the community (recommend private by default, public with consent).

## Public summary
The Community Resource Simulator lets a neighborhood, co-op, or campus honestly compare what shared solar, a tool library, or community growing would plausibly change for them — with assumptions shown, ranges instead of promises, and a clear list of what a real feasibility study would still need to verify.

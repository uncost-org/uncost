---
title: "PRJ-007 — Basic Needs Planner"
created: 2026-06-12
updated: 2026-07-16
version: "1.3"
status: draft
review_status: independent-claude-review-pending
registry_status: final-control-aligned
privacy: public
---

> **DRAFT — NOT APPROVED FOR BUILD OR LAUNCH.** Independent Claude review, founder review, and relevant domain/professional review are pending. Roadmap dates are movable targets.

# PRJ-007 — Basic Needs Planner

## Snapshot
- **Project:** Basic Needs Planner (canonical; "AI Basic Needs Planner" as alias).
- **Role in the system:** the forward-planning layer, and the bridge toward the "Beyond" roadmap items. Distinct from PRJ-004: the simulator compares intervention options for an *existing* community; the planner drafts requirements for a *proposed* site, campus, co-op, or initiative that doesn't exist yet. It is also the disciplined precursor to any future autonomous-basic-needs demonstration (longer-horizon integrated-demonstration territory) — no integrated demonstration should be scoped except through this tool's honest requirements output.
- **Status:** Draft; not started. Later dependent build.
- **Roadmap:** Later build after PRJ-003 and PRJ-004 stabilize; no integrated demonstration is scoped from this draft.

## Sectors
- **Primary:** Food, Water, Shelter, Energy (the physical-basics core of any site plan). **Secondary:** Transportation, Communication, Safety (resilience framing only).

## The problem and the cost being reduced
Groups exploring a community land project, campus, or co-op face enormous early planning costs before they can even ask professionals the right questions. The planner reduces that pre-professional planning and documentation labor — turning local context into a structured draft: capacity requirements, resource map, data gaps, risk register, regulatory checklist, and a "who you now need to hire" list.

## What it is / what it is not
It is a requirements-drafting assistant whose every output is explicitly a draft for professional review. It is not an engineering assessment, not a legal or zoning opinion, not a viability guarantee, and never an emergency, medical, or safety planning tool. The plan's own caution applies verbatim: high risk of users treating outputs as authoritative — so authority-refusal is designed into the output format itself.

## MVP deliverables
1. **Intake schema:** site basics, population served, climate/region class, existing infrastructure, applicable PRJ-002 regional costs where covered.
2. **Requirements engine** built on PRJ-003's intervention library and PRJ-004's validated module logic: per-sector capacity estimates as ranges with assumptions surfaced.
3. **Safe-output format (the core design deliverable):** every plan renders as — draft requirements with ranges → explicit data gaps → risk register → regulatory/professional checklist ("this plan requires a licensed civil engineer for X, water rights counsel for Y…") → next-step packet. A hard rule: outputs cannot render as approvals, certifications, or single-number budgets.
4. **Refusal boundaries:** the planner declines emergency scenarios, medical capacity planning, and anything POL-008-gated, with signposting to appropriate professionals.
5. Two facilitated pilots with real groups considering real sites, published with consent.

**Explicitly cut:** autonomous site selection, financing plans, construction scheduling, anything implying permits or professional sign-off.

## AI role and human gates
AI runs guided intake, drafts the requirements packet, flags missing assumptions, and generates the professional-review checklist. Humans review pilot outputs and all module logic; the tool self-identifies as automated and drafts-only (POL-007). Pilots involving vulnerable communities trigger POL-008 review first.

## Success metrics (MVP)
Two pilot groups rate the packet as materially accelerating their professional engagement; 100% of outputs include the data-gaps and professional-checklist sections; zero outputs rendering point-estimate budgets or approval language; at least one pilot group proceeds to commissioning real professional work using the packet.

## Resource posture

No budget is approved. Resourcing requires a separate plan, evidence, and founder approval after the applicable policy, sponsor, methodology, safety, legal, and partner gates. Historical estimates are not authorization.

## Timeline (phase-gated)
Gate 1: intake schema + safe-output format designed and reviewed → Gate 2: requirements engine for the four primary sectors → Gate 3: red-team against misuse ("can we make it promise something?") → Gate 4: pilots → release. Rough effort: 12–20 weeks after PRJ-003 and PRJ-004 stabilize — realistically a Year-2/3 build.

## Risk level and policy dependencies
- **Risk level:** high (over-trust risk; the plan's own assessment).
- **Safety review required:** yes — safe-output boundaries reviewed before any pilot; POL-008 conditional on pilot populations.
- **Policy dependencies:** POL-007 (hard), POL-008 (conditional), POL-002 (pilot data), POL-009 (module licensing).

## Dependencies and sequencing
Blocked by PRJ-003 (intervention library) and PRJ-004 (validated modules); consumes PRJ-002 data. Blocks: any credible scoping of "Beyond"-phase integrated demonstrations.

## Open questions / decision records needed
DR needed: pilot selection criteria (recommend one rural land project + one urban co-op for contrast); DR needed: output privacy default (recommend private to the group, public only with consent).

## Public summary
The Basic Needs Planner helps a group exploring a community site or initiative turn their context into a structured draft plan — what capacity they'd need, what data they're missing, what risks to register, and exactly which professionals to engage next. It drafts; it never certifies.

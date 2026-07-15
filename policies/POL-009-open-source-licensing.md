---
title: "POL-009 — Open-Source Licensing Policy (P1)"
updated: 2026-07-16
version: "1.3"
status: draft
review_status: independent-claude-review-pending
privacy: public
---

> **DRAFT — NOT ADOPTED — NOT IN FORCE.** Independent Claude review, founder review, and required legal/fiscal-sponsor review are pending.

# POL-009 — Open-Source Licensing Policy (P1)

**Owner:** Founder. **Applies to:** all public repos, published content, datasets, brand assets, and inbound contributions.

## Purpose
Open by default, precise about what "open" means: code, content, data, brand, and personal stories carry different rights, and conflating them creates legal exposure and community disputes.

## Rules
1. **Code:** Apache-2.0 is the current repository default (permissive plus explicit patent grant). Any change requires founder and legal review plus a written repository rationale.
2. **Documentation and educational content:** CC BY 4.0 is the current repository default, except where third-party material, personal stories, brand material, or partner restrictions apply.
3. **Original datasets:** CC BY 4.0 or ODC-BY for datasets Uncost fully owns; third-party data always retains its source license, attribution, and usage limits — the SRC- register records the license of every source, and the dashboards must not republish data whose terms forbid it.
4. **Brand:** the Uncost name, logo, wordmark, slogans, and campaign identity are **not** open-licensed; a brand-use page governs permitted use. Open tools, protected identity.
5. **Personal stories and community contributions of a personal nature are never open by default**; they require specific, scoped, revocable consent (POL-002).
6. **Inbound contributions:** DCO sign-off (or CLA if the sponsor requires) before substantial contributions; contributors confirm they hold the rights to what they submit; AI-assisted contributions disclosed where material and reviewed for license contamination.
7. **Repo hygiene:** every public repo carries LICENSE, README, CONTRIBUTING.md, CODE_OF_CONDUCT.md (POL-003), and SECURITY.md with a private disclosure contact and a response-window commitment.

## Adoption checklist
Confirm Apache-2.0 + CC BY 4.0 defaults at repo rebuild; create the four repo template files; publish the brand-use page; record every existing source's license in the SRC- register before dashboard launch.

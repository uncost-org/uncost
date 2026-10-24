# Website implementation status

A routing scaffold (Eleventy, `website/src/`, placeholder templates only) builds locally and in CI, and its built output is content-audited on every pull request. Page design and copy arrive via the governed design handoff, and form markup via the UNP-57 page contract. The build from `main` has been public at https://uncost.org since the soft launch of 2026-10-19 ([CHG-004](../records/changes/CHG-004-public-soft-launch.md)). Since [CHG-010](../records/changes/CHG-010-production-deploys-from-github.md), production deploys run through `.github/workflows/deploy-production.yml`, after the founder approves each one; see `docs/INFRA-DOMAINS.md`, "Deploys".

## Content control

Future website copy must derive from the final external Movement Plan and this repository's reviewed public documents. Legacy April 2026 site copy is stale and must not be copied wholesale.

Required top-level information architecture:

- The Movement
- The Case
- The Projects
- The Assembly

Primary front-door language should use **“Living should not have a price tag.”** and **“Uncost the cost of living.”** The primary CTA is The Pledge. Donation UI remains absent until fiscal sponsorship is confirmed.

## Design handoff status

The founder-authorized final **image-asset set** now lives in [`website/assets/brand/`](assets/brand/): seven logo/mark variants, fifteen canonical sector illustrations, sixty-four robot illustrations, exact source/output hashes, alt text, rights boundaries, deterministic receipts and a closed hold ledger. All 86 images passed fresh alpha and visual QA on canonical cream, ink and coral backgrounds.

This is repository intake only. It does not select runtime assets, rebuild or deploy the website, approve sponsor materials, or publish a production design. The remaining implementation handoff still requires design tokens/components, verified font binaries/licences, responsive layouts, interaction notes and copy/data-placeholder reconciliation against current control.

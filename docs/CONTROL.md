# Public source control and authority

Updated: 2026-07-19

## Controlling movement source

- Logical source: **Uncost final external Movement Plan and Roadmap (July 2026 edition)**
- Edition finality: declared final by the founder on **2026-07-18**
- SHA-256: `a2b640217626a76e9a26f73a5744f8c59051c83351a72bc041150824ac5a3dcd`
- Size: 27 pages, 37,576,547 bytes
- Day 1 anchor: **2026-07-15** (unchanged; see the date rule below)
- Authority: final controlling source for Uncost mission, positioning, sequencing, safeguards, and roadmap.
- Supersedes: the 2026-07-15 edition, SHA-256 `5b99100ecbeeb068b89c7f5a19d38e5382b01ee79f991d35df98106764d48670` (24 pages). Documents stamped with the superseded hash as `source_sha256` were derived from that edition; they keep the derivation stamp plus a `source_superseded_by_sha256` marker until re-reviewed against this edition. See `records/changes/CHG-001-controlling-source-repin.md`.
- Publication boundary: the source PDF is not embedded in this repository. These documents are public derivatives; a separately designed public edition can be added after its own review.

## Merged canon baseline

- Repository: `dafuqindustries/portfolio-canon`
- Merged commit: `4cf34402129525c375ce873be189c897eea5d7e6`
- Paths: `uncost/canon/brief.md`, `business-plan.md`, `current-state.md`, and `access.md`
- Role: current authority map and implementation boundary derived from the controlling source.

## Subordinate material

- Draft policies and projects may add operational detail only where they conform to the controlling source and canon.
- Private internal planning remains private and non-controlling. It must not be copied into public files merely because it is useful context.
- Historical repository and website material is provenance only. It is not a content source for this fresh repository unless revalidated explicitly.

## Durable design authority (order and status vocabulary)

The four-part order (The Movement, The Case, The Projects, The Assembly), the fixed 15-sector order, and the honest status vocabulary are durably authoritative in this repository and require no external overlay file: the sector order is enforced at build time in `website/src/_data/catalog.js` (the build fails on any reorder), and the status vocabulary is fixed in the hash-pinned design-system CSS (`website/design-system/components.css`, pinned by `SOURCE_RECEIPT.json`). This supersedes the ephemeral `/tmp` copy/status/order overlay cited by earlier planning (defect DEF-05); that artifact is not durable and is not required — its content is reproducible from the repository. DEF-05 is a provenance record, not a publication blocker.

**Status vocabulary — changed 2026-07-22.** When first recorded (2026-07-21, defect DEF-05 closure) the honest-status set was the six classes `status--{prelaunch, draft, scaffold, planned, blocked, receipt}`. Adopting the finished Claude Design export (SHA-256 `8962b207…`) changed the set to `status--{live, dev, planned, focus, next, dossier, future}`. The change was made through a reviewed, audited pull request — which is precisely this durable authority working, not a bypass. The **substance is preserved**: every status renders honest text and no bare `Live`/`Funded`/`Approved`/`Operating` badge appears (for example `.status--live` renders "Designed — opens at launch", never the word "Live"; the content audit's badge ban is on rendered text, not class names). Recorded as a contract-relevant change against the UNP-50 rev 4 frozen contract, and in `website/design-system/AUTHORITY.md`.

## Conflict rule

When a subordinate statement conflicts with the controlling external plan, change or quarantine the subordinate statement. Do not rewrite the final external plan to fit older material.

## Date rule

Roadmap conversions use 2026-07-15 as Day 1. Derived dates are movable planning targets, not hard promises. Stage order, evidence, legal review, safety, sponsor requirements, and founder approval outrank dates.

# Uncost civic-block design source

> **Review reference only — not a rebuilt or deployed website.**

This directory is the safe, reconciled intake of the final Claude Design handoff for UNP-46. It preserves the handoff's useful visual system without importing its stale demo copy, fabricated figures, obsolete governance surfaces, duplicate image binaries, broken previews, development CDNs, or unproven bundled fonts.

The packet is an implementation input for the later website build. It does not select runtime assets, publish copy, activate forms, authorize a merge, or authorize deployment.

## What is authoritative

- Public copy and claims: [`docs/CONTROL.md`](../../docs/CONTROL.md), the accepted UNP-39 sitemap, and the accepted UNP-41 content map.
- Repository copy: current reviewed public documents in this repository, subject to [`REVIEW_STATUS.md`](../../REVIEW_STATUS.md).
- Image files, hashes, rights, and alt text: [`website/assets/brand/ASSET_MANIFEST.json`](../assets/brand/ASSET_MANIFEST.json).
- Visual primitives only: this directory's tokens, components, icon subset, and static reference page.

See [AUTHORITY.md](AUTHORITY.md) for the complete precedence and use boundary.

## Packet contents

| Path | Role |
|---|---|
| [`tokens.css`](tokens.css) | Reconciled color, type, spacing, layout, and motion tokens. |
| [`components.css`](components.css) | Accessible civic-block primitives with safe status vocabulary and responsive rules. |
| [`icons/icons.svg`](icons/icons.svg) | Curated handoff icon subset; obsolete voting and money glyphs were not carried forward. |
| [`reference/index.html`](reference/index.html) | Static, noindex visual specimen using canonical repo assets and non-operating controls. |
| [`fonts/`](fonts/) | Fresh Google Fonts Latin variable subsets plus immutable OFL license receipts. |
| [`SOURCE_RECEIPT.json`](SOURCE_RECEIPT.json) | Frozen archive, transformation, canonical-asset, font-source, and output hashes. |
| [`EXCLUSIONS.md`](EXCLUSIONS.md) | Complete archive exclusion/quarantine ledger. |
| [`scripts/audit_design_handoff.py`](../../scripts/audit_design_handoff.py) | Reproducible integrity, link, safety, and baseline accessibility checks. |

## Local review

From the repository root:

```sh
python3 -m http.server 4173
```

Then open `http://127.0.0.1:4173/website/design-system/reference/`. This is a local static review surface only. It performs no network requests and submits no data.

Run the focused checks with:

```sh
python3 scripts/audit_design_handoff.py
python3 scripts/audit_repository.py
```

The frozen ZIP is intentionally not committed. Its exact wrapper prefix is `uncost-design-system/`; receipt transformations use logical paths below that prefix. The audit never uses suffix matching. To revalidate source bytes mechanically, provide either the exact archive or an extracted directory containing that exact wrapper. An extracted root after stripping only that frozen prefix, with `project/` directly below it, is also accepted:

```sh
UNCOST_DESIGN_HANDOFF_ARCHIVE=/path/to/Uncost\ Design\ System-handoff\ \(1\).zip python3 scripts/audit_design_handoff.py
UNCOST_DESIGN_HANDOFF_EXTRACTED=/path/to/extracted-root python3 scripts/audit_design_handoff.py
```

## Material reconciliations

- The original coral remains a brand accent. Normal-size links and actions use the deeper coral with cream text because the original normal-text pairings miss WCAG AA.
- Clay and ink-blue blocks mandate cream foreground text. Ink and coral are not interchangeable on those surfaces.
- Only honest statuses are available: pre-launch, public review draft, scaffold, planned, blocked, and receipt-backed.
- The original continuously animated sector carousel was omitted. The packet has no required motion, and reduced-motion rules disable the remaining short color transitions.
- Image binaries are referenced from the existing 86-asset manifest instead of copied.
- The stale handoff WOFF2 files were rejected. Fresh official Google-hosted variable subsets and OFL texts are vendored with exact hashes.
- The specimen contains no live form, payment, donation, pledge submission, analytics, or external runtime.

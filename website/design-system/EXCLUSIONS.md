# Claude Design archive exclusion and quarantine ledger

The frozen archive contains 417 files. No archive member is copied verbatim into runtime-ready website code. Three source members contribute transformed visual primitives; the remainder are reference-only or excluded. The raw ZIP is not committed.

## Complete archive accounting

| Archive class | Files | Disposition | Reason |
|---|---:|---|---|
| Root/project instructions, metadata, generated bundle, thumbnail files | 8 | Reference-only or excluded | Useful for intake context, not production source; project description contains superseded claims. |
| `_tmp/` | 6 | Quarantined | Internal/private documents and working images. |
| `assets/` | 101 | 1 icon sprite transformed; 100 excluded or referenced | 86 current logo/sector/robot binaries already have canonical repository copies; 14 archived sector files use a retired taxonomy; the icon sprite is curated into a smaller safe subset. |
| `colors_and_type.css` | 1 | Transformed into `tokens.css` | Palette/type/spacing retained; unproven font files and failing text-color uses corrected. |
| `docs/` | 2 | Excluded | Prototype content, not controlled public copy. |
| `fonts/` | 2 | Rejected and replaced | No bundled source or license proof; fresh official subsets and licenses are included instead. |
| `preview/` | 20 | Reference-only | Visual specimens informed the transform; obsolete/broken robot previews and demo copy were not copied. |
| `scrap/`, `scraps/`, `screenshots/` | 12 | Quarantined | Working checks and generated review material. |
| `slides/` | 2 | Excluded | Prototype presentation with uncontrolled claims. |
| `social/` | 1 | Excluded | Prototype post copy is outside the accepted content map. |
| `ui_kits/` | 21 | 1 CSS file transformed; 20 reference-only/excluded | Component appearance informed this packet; templates and JSX contain stale copy, obsolete routes, demo figures, or development-only structure. |
| `uploads/` | 241 | Quarantined | Raw duplicates, source photos, screenshots, private/internal material, watermarked video, working documents, and generated files. |
| **Total** | **417** | Fully accounted | — |

## Mandatory exclusions applied

- The 377.9 MB ZIP itself.
- Every file under `_tmp/`, `uploads/`, `scrap/`, `scraps/`, and `screenshots/`.
- DOCX, JPG/JPEG, MP4, source-photo, screenshot, and generated duplicate material.
- All bundled logo, sector, and robot binaries; use the current canonical manifest instead.
- The stale `11_holding_sign` image from the handoff. Only the repaired canonical repository asset may be considered later.
- The missing robot dance video reference and ten missing robot option SVG references.
- The bundled WOFF2 files.
- The obsolete governance kit and any token, wallet, on-chain, binding-vote, or demo-treasury treatment.
- Prototype claims, counters, pledge totals, treasury totals, and unsupported cost figures.
- CDN React/Babel execution, Google Fonts runtime CSS, and other development runtime dependencies.

## Broken-reference disposition

The source audit found eleven missing relative targets: one robot dance video and ten robot option SVGs. None of the affected previews is included. The static specimen in this packet has its own link and asset check and does not refer to those targets.

## Canonical binary reconciliation

- 22 of 22 bundled current logo/sector files match existing canonical assets and are not recommitted.
- 63 of 64 robot files match existing canonical assets and are not recommitted.
- The handoff sign-holding robot is stale. The canonical repository version is the repaired file recorded in the asset manifest.
- The canonical manifest remains the only path/hash/alt-text authority for image use.


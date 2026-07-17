# Uncost brand assets — final reviewed image set

**Status:** all 86 image assets approved for repository intake. Repository intake is not website deployment, runtime selection, merge, sponsor publication, or production release.

## Contents

- `logos/`: seven full, tight and mark-only variants.
- `sectors/`: fifteen canonical sector illustrations.
- `robots/`: forty action scenes, eighteen expression crops and six turnarounds.
- `ASSET_MANIFEST.json` / `.csv`: exact source/output lineage, hashes, dimensions, alpha statistics, alt text and rights status.
- `SHA256SUMS.txt`: exact repository-relative output hashes.
- `QA_RECEIPT.json`: deterministic and visual QA disposition.
- `HELD.md`: closed-hold record for this exact set.
- `RIGHTS.md`: reserved-rights boundary.

## Provenance and QA

The supplied source archive is `uncost-transparent-images-v4-fixed 2.zip`, SHA-256 `db9ba296c41beae222c4c9dde102b69a4f43f097f7f0d774c989e7d38980a3cc`. Its bundled checksum/manifest metadata was stale, so repository metadata was regenerated from actual decoded bytes.

`robots/11_holding_sign_transparent.png` received one founder-authorized deterministic repair: the largest enclosed alpha-zero sign-panel component was restored from exact source parent SHA-256 `23a8d426e93ea53473bc0766bd793bb2e80fb637593aaca251f43df3a2340783`. Exactly 553,630 panel pixels changed; every RGBA pixel outside bbox `[295,73]–[1335,614]` remained identical. Final output SHA-256: `8d3faad4da445684a2e459878b830579cce8ca5c565bcc0f32468f99bc3f2d76`.

All 86 assets passed fresh decoding, hash, dimensions, alpha and visual checks on cream `#FAF7F0`, ink `#0E0E0C` and coral `#D64A1E`.

## Use rules

- Preserve logo and mark aspect ratios. Never stretch, squash or crop a lockup.
- `*-light.png` contains dark/ink art for light/cream surfaces.
- `*-dark.png` contains light art for dark surfaces.
- `logo-final-transparent.png` is an intentional byte-identical alias of `logo-final-light.png`.
- Use informative manifest alt text; logos and meaningful illustrations are not decorative.
- Preserve the full sector canvases and canonical product order.
- `robots/01_waving_transparent.png` is the approved friendly default cover pose.
- Ink composites validate alpha behavior; black linework is not automatically dark-mode adaptive. Production contrast remains a separate selection check.

## Boundary

These are reserved brand assets. Repository presence does not place them under the repository’s open-content licence and does not deploy or select them for production.

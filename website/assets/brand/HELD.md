# Held / excluded Uncost brand assets

**Status:** do not copy into this repository, use in sponsor materials, select for production, or deploy.

## Pack-wide robot hold

All Manus v2 transparent robot derivatives are held after rendered use exposed opaque white background islands inside intended negative-space regions. The required repair must preserve opaque light-grey robot material while making true gaps between legs, arms/torso, elbows, hands/tools and objects transparent; it must also remove white edge mattes.

Known examples:

| File | Held SHA-256 | Reason |
|---|---|---|
| `02_standing_confident_transparent.png` | `34b8f230ac3662810f235c674071954ab01fc0930ddcda85d634115d300599bf` | Opaque white negative-space regions in rendered use; hands-on-hips pose is also not approved as the document-cover default. |
| `30_handshake_transparent.png` | `49fc5a4c14c0ba97370b1e1c8b49b73f666d4418adcb3f8925370d704a85b63f` | Opaque white negative-space regions, including the visible gap between the legs. |
| `29_giving_food_transparent.png` | `ec8c37cdb69b2a4d7ba2f53325d0c9d91ee608bf8ba105f448e94b196a7d6cd6` | Derived from the wrong 1632×2176 parent instead of selected original SHA-256 `ec3954571911619ba2c59bd8d6d5ef69b1448bd8cd9ac85b216d5af016a40873`. |

The desired cover default after repair is the canonical friendly `01_waving.png` pose with the happy/subtle-smile expression. No robot file is included in tranche 1.

## Clipped logo hold

| File | Held SHA-256 | Reason |
|---|---|---|
| `logo-tight-light.png` | `879aba58446830aea5c69c09d489787742d337ddf7c26c5827d0f30b65dac1f8` | Lowercase `g` descender is clipped at the bottom canvas edge. |
| `logo-tight-dark.png` | `9df9ad57887a15ffa62072299f3fec6f88cced8b45046fa8165e4bb295f26712` | Lowercase `g` descender is clipped at the bottom canvas edge. |

## Other exclusions

- Inter and Roboto Condensed binaries: exact upstream binary identity/licence-chain verification remains open.
- Icon sprite: rights/provenance not included in this narrow tranche.
- Archived prior-sector illustrations: non-canonical/superseded.
- Pasted/generation uploads and watermarked MP4s: unselected and/or rights/quality blocked.
- Manus v2 tree-hash claim: not reproducible from the supplied method.

A corrected asset must arrive under a new versioned package, with source parent, output SHA-256, dimensions, alpha statistics, rights basis, and checkerboard/cream/ink/coral visual QA. A filename such as `fixed`, `final`, or `v2` is not evidence of correction.

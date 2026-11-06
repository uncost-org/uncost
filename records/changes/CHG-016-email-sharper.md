# CHG-016 — Sign-up email: sharper images, centred, more space, a larger "One last step:" (amends CHG-015)

**Status:** founder decision (2026-11-07). Drafted from the founder's brief after the preview check of CHG-015. It takes effect when this record is merged. **Sign-ups stay off in production:** nothing here turns them on.

- **Date:** 2026-11-07
- **Amends:** [CHG-015](CHG-015-email-badge.md), for both images' resolution, their alignment, the space under the badge and the size of "One last step:". Its history stands as written.
- **Changed claim:** with the switch off, the two files at `/email/` are replaced, and nothing else differs.
- **Source:** the founder's check of the Pledge email from the preview, 2026-11-06 (CHG-015, "Email preview result"): right in Spark, the robot a little blurry on Android. No AI decision; this file records what the founder set.

## What the founder set

- **Sharper on phones:** both images are re-exported at 3× their display width, in full colour from the sources. The robot is 540px wide, shown at 180px. The logo badge is 432px wide, shown at 144px.
- **Centred:** the logo badge and the robot are centred, with `align="center"` on their cells and `margin: 0 auto` on the images. The heading, text, button and footer stay left-aligned.
- **Spacing:** 12px more between the logo badge and the heading.
- **"One last step:"** is about 20% larger than the rest of its line, still bold and underlined, in both emails. The rest of the line stays as it is.

## The two images, re-exported

Both come from the same sources as CHG-015, with Pillow. They stay at `website/email/`, served at `/email/`, outside the sitemap. CHG-015 lists the previous files.

| File | Source (`website/assets/brand/`) | Source SHA-256 | Made by | Size | SHA-256 |
|---|---|---|---|---|---|
| `logo.png` | `logos/logo-tight-light.png` | `13e05467a57b8582f68df6fb91547049e58a66c4fcaedc634f44f936e09d823d` | flattened on `#FAF7F0`, Lanczos resize to 336px wide, full colour, then set on a `#FAF7F0` rounded rectangle with transparent corners (RGBA) | 432×329, 71,241 bytes | `cbbd08f3a6d2eb762bb012c8ee6bd5178eecc39bc8ef12e7bdfe41c00ccfee6d` |
| `robot-thumbs-up.png` | `robots/06_thumbs_up_transparent.png` | `058bd0e1837a77e201511bf57dccf85d0620fb9879341252f8dd36bd82b29a11` | Lanczos resize to 540px wide in premultiplied alpha, full colour with transparency (RGBA) | 540×720, 185,911 bytes | `ee6c4e6fc84c974d2e3c91114dbdc899bc6c068a3ecca47cd67c5cbec2d1e6d7` |

**The badge**, CHG-015's geometry at 3×:
- **Logo:** 336px wide, shown at 112px as before.
- **Margin:** 48px on every side (16px as shown), 14.3% of the logo's width.
- **Corner radius:** 43px (14.3px as shown), 9.95% of the badge's width. The corners are drawn at 8× and averaged down: 1,464 pixels are fully transparent and 276 partly.
- **Opaque cream:** the margin is wider than the radius, so the logo lies wholly on it.

**Colour readback.**
- **Logo dot:** the dot's centre, now pixel (271, 253) of the badge, reads RGB(184, 69, 40), the same as CHG-015 and the source.
- **Robot:** the CHG-014 check, on the new file. For each of the source's six main colours, it reads the export only at pixels whose Lanczos footprint lies wholly inside a flat area of that colour in the source. Every such pixel is within 3 levels of the source, with a mean error of 1.3 levels or less. With a smaller footprint, the worst is 5 levels, on the light grey, and the mean on the six main colours is 1.4 or less.
- **On the manifest's two QA backgrounds:** on `#FAF7F0` the badge does not show; on `#1F1F1F` it shows as a rounded cream badge.

**Asset manifest (`website/assets/brand/ASSET_MANIFEST.json`).**
- **`derived_copies`:** both entries carry the new SHA-256, bytes, size and transparency counts, the new derivation, and this record.
- **`publication_scope`:** now also says CHG-016 re-exported the copies at 3× display width.
- **`assets`:** still the approved 86 files.
- **Manifest hash:** `cd1491ce59fed04ea832ab87626b0786cc91a925206a385a3eab3cadbd35ab34` before, `870e323f42de508e4c36281d92fa510545d83845ec6e4ec3de0a16382555c0ad` after.

**Licence:** not changed, for the reason given in CHG-015. `NOTICE.md` and `website/assets/brand/RIGHTS.md` are not changed.

## The email (uncost-org/uncost-api, `src/mail/compose.js`)

- **Centred:**
  - the logo badge's and the robot's cells carry `align="center"`;
  - both images carry `display:block;margin:0 auto`;
  - their display widths stay 144px and 180px;
  - no other cell is centred.
- **Spacing:** the logo row's bottom padding is 16px, up from 4px, so the badge sits 16px above the heading.
- **"One last step:":** 19px (16px × 1.2 = 19.2, rounded), bold from its paragraph, and underlined, in an inline span in the HTML part of both emails. The rest of the line stays 16px bold and is not underlined.
- **Plain text:** unchanged.

**Not changed:** the wording, the small print, the subjects, the button, the footer and the light-only colour scheme.

## Checks

On this branch, against `main` at `7b92ecc`:
- `npm test` in uncost-api passes.
- `scripts/audit_website.py --built` passes on the default, production and switch-on builds.
- **Byte-identical with the switch off:** in fresh checkouts, the default and production builds differ only in `email/logo.png` and `email/robot-thumbs-up.png`.

The pull request lists the counts.

## Email preview result

To be filled in after the founder's next check, once this change is deployed: a new Pledge sign-up on the preview, read in Spark and on Android.

## Affected surfaces

- **With the switch off:** `/email/logo.png` and `/email/robot-thumbs-up.png` are replaced. Every page and `/sitemap.xml` are byte-identical.
- **Files:**
  - `website/email/logo.png`, `website/email/robot-thumbs-up.png`;
  - `website/assets/brand/ASSET_MANIFEST.json`;
  - CHG-015.
- **uncost-org/uncost-api:** `src/mail/compose.js`, `test/units.test.js`, `README.md`.

## Provenance

The founder's brief, 2026-11-07, after the preview check of CHG-015. Drafted by Claude Code as `uncost-admin`.

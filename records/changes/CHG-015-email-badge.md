# CHG-015 — Sign-up email: the logo badge in the image, a bigger robot, an underline (amends CHG-014)

**Status:** founder decision (2026-11-07). Drafted from the founder's brief after the preview re-check of CHG-014. It takes effect when this record is merged. **Sign-ups stay off in production:** nothing here turns them on.

- **Date:** 2026-11-07
- **Amends:** [CHG-014](CHG-014-email-fixes.md), for the logo's badge, the robot's size and the lead line's underline. Its history stands as written.
- **Changed claim:** with the switch off, the two files at `/email/` are replaced, and nothing else differs.
- **Source:** the founder's re-check of the Pledge email from the preview, read in Spark on the Mac in dark mode on 2026-11-06 (CHG-014, "Email preview result"). No AI decision; this file records what the founder set.

## What the founder set

- **Logo badge:** the 8px padding and 6px radius on the logo cell did not render in Spark. They are removed, and the badge is baked into `website/email/logo.png` instead: the logo on a cream `#FAF7F0` rounded rectangle, with a margin of about 14% of the logo's width on every side, a corner radius of about 10% of the badge's width, and transparent corners. Full colour, at 2× the display width. The logo itself stays the same size.
- **Robot:** 180px wide, from a 360px full-colour file.
- **Wording:** in both emails, "One last step:" is underlined, and only that. The rest of the line stays bold and is not underlined. The plain-text parts are unchanged.

## The two images, re-exported

Both come from the same sources as CHG-014, with Pillow. They stay at `website/email/`, served at `/email/`, outside the sitemap. CHG-014 lists the previous files.

| File | Source (`website/assets/brand/`) | Source SHA-256 | Made by | Size | SHA-256 |
|---|---|---|---|---|---|
| `logo.png` | `logos/logo-tight-light.png` | `13e05467a57b8582f68df6fb91547049e58a66c4fcaedc634f44f936e09d823d` | the CHG-014 logo (flattened on `#FAF7F0`, Lanczos resize to 224px wide, full colour), set on a `#FAF7F0` rounded rectangle with transparent corners (RGBA) | 288×219, 40,533 bytes | `16d56e2d579d813d624b66c4b10445b13a6c66c2c8c6530715e6453b6150e8be` |
| `robot-thumbs-up.png` | `robots/06_thumbs_up_transparent.png` | `058bd0e1837a77e201511bf57dccf85d0620fb9879341252f8dd36bd82b29a11` | Lanczos resize to 360px wide in premultiplied alpha, full colour with transparency (RGBA) | 360×480, 97,869 bytes | `87af0c02132fd942fa097927221b2313e4595b5e2712460fbd29072795b2f3c9` |

**The badge.**
- **Margin:** 32px at 2× on every side (16px as shown), 14.3% of the logo's 224px width.
- **Corner radius:** 29px at 2× (14.5px as shown), 10.1% of the badge's 288px width. The corners are drawn at 8× and averaged down, so they are smooth: 632 pixels are fully transparent and 212 partly.
- **The logo inside** is the CHG-014 file, pixel for pixel, placed at (32, 32). The margin is wider than the radius, so the logo lies wholly on opaque cream.
- **Shown at 144px wide**, so the logo inside stays 112px.

**Colour readback.**
- **Logo dot:** the dot's centre, now pixel (181, 168) of the badge, reads RGB(184, 69, 40), the same as CHG-014 and the source.
- **Robot:** the CHG-014 check, on the new file. For each of the source's six main colours, it reads the export only at pixels whose Lanczos footprint lies wholly inside a flat area of that colour in the source. Every such pixel is within 3 levels of the source, with a mean error of 1.2 levels or less. With a smaller footprint, the worst is 8 levels, on the light grey where the resize rings at its edges, and the mean is 0.9 or less.
- **On the manifest's two QA backgrounds:** on `#FAF7F0` the badge does not show; on `#1F1F1F` it shows as a rounded cream badge.

**Asset manifest (`website/assets/brand/ASSET_MANIFEST.json`).**
- **`derived_copies`:** both entries carry the new SHA-256, bytes, mode, size and transparency counts, the new derivation, and this record.
- **`publication_scope`:** now also says CHG-015 re-exported the copies.
- **`assets`:** still the approved 86 files.
- **Manifest hash:** `e2dec6e3209693421e34baa14b549d5ac37e2cc40076b952167fb122647bed1e` before, `cd1491ce59fed04ea832ab87626b0786cc91a925206a385a3eab3cadbd35ab34` after.

**Licence:** not changed. `LICENSES/LicenseRef-Dafuq-Industries-Uncost-Art.txt` names both files by path. It describes the logo copy as "resized and flattened onto cream"; the badge adds a cream margin and rounded transparent corners, which its grant to "use, adapt and publish" covers. Naming the badge in that file list would be a licence amendment, which is the founder's to make. `NOTICE.md` and `website/assets/brand/RIGHTS.md` are not changed.

## The email (uncost-org/uncost-api, `src/mail/compose.js`)

- **Logo:** the cell with the cream background, 8px padding and 6px radius is gone. The image stands alone, at `width="144"`. The logo row's padding is 16px less on each side (`16px 8px 4px`), so in the light design the logo stays where it was.
- **Robot:** shown at 180px wide.
- **Underline:** in the HTML part, "One last step:" in both emails sits in an inline `<span style="text-decoration:underline">`. The rest of the line stays bold and is not underlined.
- **Plain text:** unchanged.
- **Dark mode:** the light-only colour scheme from CHG-014 stays.

**Not changed:** the wording, the small print, the subjects, the button and the footer.

## Checks

On this branch, against `main` at `02ee63a`:
- `npm test` in uncost-api passes.
- `scripts/audit_website.py --built` passes on the default, production and switch-on builds.
- **Byte-identical with the switch off:** in fresh checkouts, the default and production builds differ only in `email/logo.png` and `email/robot-thumbs-up.png`.

The pull request lists the counts.

## Email preview result

To be filled in after the founder's next check, once this change is deployed: a new Pledge sign-up on the preview, read in Spark (light and dark) and in Gmail on the phone.

## Affected surfaces

- **With the switch off:** `/email/logo.png` and `/email/robot-thumbs-up.png` are replaced. Every page and `/sitemap.xml` are byte-identical.
- **Files:**
  - `website/email/logo.png`, `website/email/robot-thumbs-up.png`;
  - `website/assets/brand/ASSET_MANIFEST.json`;
  - CHG-014.
- **uncost-org/uncost-api:** `src/mail/compose.js`, `test/units.test.js`, `README.md`.

## Provenance

The founder's brief, 2026-11-07, after the preview re-check of CHG-014. Drafted by Claude Code as `uncost-admin`.

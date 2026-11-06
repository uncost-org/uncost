# CHG-014 — Sign-up email fixes after the founder's review (amends CHG-013)

**Status:** founder decision (2026-11-06). Drafted from the founder's brief "Uncost sign-up emails: fixes after Matt's review". It takes effect when this record is merged. **Sign-ups stay off in production:** nothing here turns them on.

- **Date:** 2026-11-06
- **Amends:** [CHG-013](CHG-013-signups-go-live-prep.md), for the two email images, the robot's size, the email wording and dark mode. Its history stands as written.
- **Changed claim:** with the switch off, the two files at `/email/` are replaced, and nothing else differs.
- **Source:** the founder's review of the test email from the preview, 2026-11-06. No AI decision; this file records what the founder set.

## What the review found

- **Logo colour:** in `website/email/logo.png` the coral dot in ".org" came out about RGB(96, 81, 76), not the source's RGB(184, 69, 40). The 64-colour palette had no colour close to it.
- **Robot:** too small at 72px.
- **Dark mode:** in Spark on the Mac, in dark mode, the cream logo showed as a light box on a dark background.
- **Wording:** the confirmation step should come straight after the heading.

## The two images, re-exported

Both are re-exported in full colour from the same sources, with Pillow (Lanczos resize). They stay at `website/email/`, served at `/email/`, outside the sitemap. CHG-013 lists the previous files.

| File | Source (`website/assets/brand/`) | Source SHA-256 | Made by | Size | SHA-256 |
|---|---|---|---|---|---|
| `logo.png` | `logos/logo-tight-light.png` | `13e05467a57b8582f68df6fb91547049e58a66c4fcaedc634f44f936e09d823d` | flattened on `#FAF7F0`, resized, full colour (RGB) | 224×155, 35,132 bytes | `36c7d98c1d73c0a82ee3473231f473550a0ec066f6eec3f0a41f3e151c2cc277` |
| `robot-thumbs-up.png` | `robots/06_thumbs_up_transparent.png` | `058bd0e1837a77e201511bf57dccf85d0620fb9879341252f8dd36bd82b29a11` | resized in premultiplied alpha, full colour with transparency (RGBA) | 240×320, 52,155 bytes | `4c19de608ee345a7f26bcbc6d9b920731a99de4c1b37a0c59ba260c1f56681ff` |

**Colour readback.**
- **Logo dot:** in the source, most of the dot's core is RGB(184, 69, 40). At the dot's centre in the email copy, pixel (149, 136), the reading was RGB(96, 81, 76) before and RGB(184, 69, 40) after.
- **Robot:** the check took the source's six main colours. For each one it read the export only at pixels whose resize footprint lies wholly inside a flat area of that colour in the source. In the new file every such pixel is within 3 levels of the source (worst 5 with a smaller footprint), and the mean error is 1.4 levels or less. In the old 128-colour file the orange was up to 8 levels off.

**The robot is shown at 120px wide**, so the 240px file is 2×. The logo stays at 112px from its 224px file.

**Asset manifest (`website/assets/brand/ASSET_MANIFEST.json`).**
- **`derived_copies`:** both entries carry the new SHA-256, bytes, mode, size and transparency counts, the new derivation, and this record.
- **`publication_scope`:** now says the copies are live since CHG-013's production deploy of 2026-11-06, and re-exported by this change.
- **`assets`:** still the approved 86 files.
- **Manifest hash:** `19245c66612718f59fefaeffa8e0f44e546391a86b87250a3d135d9bd9de96fb` before, `e2dec6e3209693421e34baa14b549d5ac37e2cc40076b952167fb122647bed1e` after.

**Licence:** not changed. `LICENSES/LicenseRef-Dafuq-Industries-Uncost-Art.txt` names both files by path, and its descriptions still hold ("resized and flattened onto cream"; "the copy resized from it"). `NOTICE.md` and `website/assets/brand/RIGHTS.md` are not changed either.

## The email (uncost-org/uncost-api, `src/mail/compose.js`)

**Pledge email:**
- The heading stays: "Thank you for signing the Uncost Pledge."
- Straight after it, one bold line: "One last step: your signature only counts once you confirm it."
- "Please confirm your email address to count your signature:" is removed.
- The button stays.
- The first small-print paragraph is now "The link is valid for 24 hours. Confirming is how we keep the tally honest." The other two are unchanged.

**Updates email:**
- Straight after its heading, one bold line: "One last step: confirm below to start getting updates."
- "Please confirm your email address to start them:" is removed.
- The small print follows the pledge email where the two say the same thing:
  - "The link is valid for 7 days."
  - "If you didn't ask for updates, ignore this email. No updates are sent, and unconfirmed sign-ups are deleted after 7 days."

  The second paragraph mirrors the pledge's "Nothing is counted, and…", and takes over the old "We won't send any updates unless you confirm."

The plain-text parts carry the same wording. In them the confirmation link follows the bold line.

**Dark mode.** The email asks for a light colour scheme in three ways: `<meta name="color-scheme" content="light">`, `<meta name="supported-color-schemes" content="light">`, and `:root { color-scheme: light; }` in the email's one style block, which loads nothing. Clients that respect these keep the light design. The logo now sits on its own cream tile, with 8px padding and a 6px radius, so a client that darkens the email anyway shows a deliberate badge, not a stray box. There is no dark-mode logo variant. The logo row's padding is 8px less on each side, so in the light design the logo has not moved.

**Not changed:**
- the /pledge/check-email/ page, which still says "Your pledge isn't counted until you confirm". That is a page on the site, not the email;
- the footer, the subjects and the button text.

## Checks

On this branch, against `main` at `a8632a4`:
- `npm test` in uncost-api passes.
- `scripts/audit_website.py --built` passes on the default, production and switch-on builds.
- **Byte-identical with the switch off:** in fresh checkouts, the default and production builds differ only in `email/logo.png` and `email/robot-thumbs-up.png`.

The pull request lists the counts.

## Email preview result

To be filled in after the founder's re-check, once this change is deployed: a new Pledge sign-up on the preview, read in Gmail on the phone (light and dark) and in Spark.

## Affected surfaces

- **With the switch off:** `/email/logo.png` and `/email/robot-thumbs-up.png` are replaced. Every page and `/sitemap.xml` are byte-identical.
- **Files:**
  - `website/email/logo.png`, `website/email/robot-thumbs-up.png`;
  - `website/assets/brand/ASSET_MANIFEST.json`;
  - CHG-013.
- **uncost-org/uncost-api:** `src/mail/compose.js`, `test/units.test.js`, `README.md`.

## Provenance

The founder's brief, 2026-11-06, after reviewing the test email on the preview. Drafted by Claude Code as `uncost-admin`.

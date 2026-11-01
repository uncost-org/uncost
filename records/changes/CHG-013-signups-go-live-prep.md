# CHG-013 — Sign-ups go-live, prepared and not flipped (amends CHG-009 and CHG-012)

**Status:** founder decision, dated by the founder (2026-11-01). Drafted from the founder's go-live brief, part 1. It takes effect when this record is merged. **Sign-ups stay off in production:** nothing here turns them on. That is still decision 1 in [CHG-009](CHG-009-signups.md).

- **Date:** 2026-11-01
- **Amends:** [CHG-009](CHG-009-signups.md), for the email design, its dated decisions and the production steps; [CHG-012](CHG-012-postmark.md), for the deletion copy; and the artwork licence of [CHG-007](CHG-007-rights-and-transfer-safeguard.md), for the email robot. Their history stands as written.
- **Changed claim:** with the switch off, the site serves two new image files at `/email/`, and nothing else differs. With it on, the deletion pages also say what stays with Postmark.
- **Source:** the founder's go-live brief (2026-11-01). No AI decision; this file records what the founder set.

## The email design

In uncost-org/uncost-api, branch `email-design` (`src/mail/compose.js`). The copy is unchanged.

- **Layout:** on cream `#FAF7F0`, 560px at most: logo (alt "uncost.org", 112px), bold heading, body, a coral `#D64A1E` button with white bold text, small print in `#5A574F`, the thumbs-up robot (72px, alt "") with no sign-off, then a white footer.
- **Footer:** "This email is from Uncost (uncost.org).", the why-line, the three links and the postal address. "Operated by Dafuq Industries LLC" comes out of both parts; /privacy/ §1 still says who operates the site.
- **Markup:** tables and inline styles, system fonts, no web fonts, no tracking. Each email has the same two image URLs, with nothing per-recipient in them.
- **Plain-text part:** the same as before, minus the operator name.
- **Contrast:** white on this coral is 4.32:1, which WCAG allows only for large text, so the button text is 19px bold.
- **Dark mode:** the emails ask for a light colour scheme, but a mail client may still change their colours. The logo is flattened onto cream, because the source is dark on transparent and would vanish on a dark background.

## The two images

At `website/email/`, served at `/email/`. Each is a new binary, so this is its lineage. They are static, are not pages, and are not in the sitemap.

| File | Source (`website/assets/brand/`) | Source SHA-256 | Made by | Size | SHA-256 |
|---|---|---|---|---|---|
| `logo.png` | `logos/logo-tight-light.png` | `13e05467a57b8582f68df6fb91547049e58a66c4fcaedc634f44f936e09d823d` | flattened on `#FAF7F0`, resized, 64 colours | 224×155, 10,407 bytes | `ac8d747f51c9f01c0828ee8b0f3006aef4a0994e1896c4d6005a62c8425f19d4` |
| `robot-thumbs-up.png` | `robots/06_thumbs_up_transparent.png` | `058bd0e1837a77e201511bf57dccf85d0620fb9879341252f8dd36bd82b29a11` | resized, 128 colours, transparency kept | 144×192, 4,927 bytes | `5c2447f8cd6f598f6acf4dc4532a90022247082eed54cd065d48e5cd6752a333` |

Both were made with Pillow (Lanczos resize) and checked by eye in the rendered email, in Chromium at 640px and 390px. They must be live on `uncost.org` before any branded email is sent.

**Licence extended, 2026-11-01, by the decision of Matt, owner of Dafuq Industries LLC.** The artwork licence (`LICENSES/LicenseRef-Dafuq-Industries-Uncost-Art.txt`) named six robots, and `robots/06_thumbs_up_transparent.png` was not one of them. It now also covers that file and its derived `website/email/robot-thumbs-up.png`. The logo was already licensed, and the licence's grant to adapt covers `logo.png`.

## The deletion wording

/signup/deleted/ and the delete confirm page (`website/functions/api/signup/delete.js`) now also say:

> Postmark, which sends our emails, keeps its copy of the emails it sent you for up to 45 days, its default. If an email to you hard-bounced or you reported one as spam, your address also stays on Postmark's own list, so that it won't send to it.

This settles the conflict CHG-012 listed. /privacy/ §11 is **not changed**: it already says this, from CHG-012 ("Postmark's copy of the emails it sent you stays until its 45 days are up…"). If the Postmark account moves off 45 days, these two pages must change with /privacy/ §7 and §11.

## The workflow variable

`.github/workflows/deploy-production.yml` used to unset `UNCOST_FORMS_OPEN` in the build. The build job now reads the **repository variable** `UNCOST_FORMS_OPEN`:
- unset, or anything but `on`: the forms stay off;
- `on`: the forms are built on, and both checks of the build expect that.

`tools/prod_check.py`, which the build job runs, used to refuse any sign-up form, so setting the variable to `on` would have failed the run and deployed nothing. It now reads the same switch and allows what `scripts/audit_website.py` allows: the live updates form on any page and the live Pledge form on /pledge/ and /pledge/resent/, requires them on / and /pledge/, and expects the sign-up result pages noindex. With the switch off it still refuses them.

The variable is not set by this change. It changes only what gets built. The run still waits for the founder's approval, and the handlers stay dark until the project `uncost` has the `SIGNUPS` binding and `UNCOST_SIGNUPS_OPEN=on`.

`noticeEffective` in `_data/signups.json` stays unset here. It is set on the go-live day.

## Founder decisions recorded in CHG-009

Dated by the founder:
- decision 2, D1 as the datastore: 2026-10-20;
- decision 4, the retention rule: 2026-10-25;
- decision 5, minimum age 18: 2026-10-25.

Decision 1 (turning on) and decision 3 (code home) stay open until go-live. The founder records the AWS transfer-safeguard question as closed by CHG-012 (Postmark, under the Data Privacy Framework through ActiveCampaign).

## Go-live checklist

For the go-live day, drawn from CHG-009's production steps and CHG-012. It replaces CHG-009's list, which was written for SES. The founder's go-live brief, part 2, governs where it differs.

1. Date decisions 1 and 3 in CHG-009, and set `noticeEffective`, in one PR. Merge it.
2. Recreate the D1 database `uncost-signups` empty and apply the migrations, so no test row or test suppression goes live. Keep every `HMAC_KEY_V<n>`.
3. Confirm that the Worker runs main and that `LINK_ORIGINS` covers `https://uncost.org`.
4. Confirm that the Postmark account is approved and that its DPA applies, and add the private register rows.
5. Point Postmark's webhook at `https://uncost.org/api/signup/postmark-events`, with the same Basic auth.
6. Confirm that the rate-limiting rule covers `/api/signup/pledge` and `/api/signup/updates` (CHG-009, Cloudflare step 6).
7. On the production project `uncost`: the Service binding `SIGNUPS` → `uncost-signups`, and `UNCOST_SIGNUPS_OPEN=on`. Pages applies these to new deployments only.
8. Set the repository variable `UNCOST_FORMS_OPEN` to `on`, run `deploy-production`, and approve it.
9. Sign up with a new address on `uncost.org`, confirm, unsubscribe and delete. Check that the images load.
10. Record the deploy and the date in `docs/INFRA-DOMAINS.md`.

Removing the SES records, topic and IAM user comes after go-live (CHG-012).

## Rollback

1. Set the repository variable `UNCOST_FORMS_OPEN` to anything but `on`, or delete it.
2. On the project `uncost`, remove the `SIGNUPS` binding and `UNCOST_SIGNUPS_OPEN`.
3. Run `deploy-production` and approve it. Pages applies a binding change only to new deployments, so the redeploy is what closes the handlers.

For speed, the dashboard's rollback to the previous deployment restores the earlier pages and handlers (CHG-010). Data stays in D1 until it is deleted. Record the rollback here with its date and reason.

## Conflicts, listed and not resolved

- **The licence's summaries.** `NOTICE.md` and `website/assets/brand/RIGHTS.md` still list "six robots". The licence file is the full text, and the founder's decision named that file and this record, so the summaries are not changed here.
- **POL-002 Rule 6 and its "adequate written terms".** CHG-012 left the founder's confirmation of Postmark's DPA, and counsel's view of the transfer wording, open. Closing the AWS question does not close those.

## Email preview result

To be filled in after the founder checks the email in Gmail, on the web and the phone, in light and dark.

## Affected surfaces

- **With the switch off:** `/email/logo.png` and `/email/robot-thumbs-up.png` are new. Every page and `/sitemap.xml` are byte-identical.
- **With it on:** /signup/deleted/ and the delete confirm page.
- **Files:**
  - `website/email/` (new), `website/eleventy.config.js`;
  - `website/src/signup/deleted.njk`, `website/functions/api/signup/delete.js`, `tools/signup_check.py`;
  - `.github/workflows/deploy-production.yml`, `tools/prod_check.py`;
  - `LICENSES/LicenseRef-Dafuq-Industries-Uncost-Art.txt`;
  - CHG-009 and CHG-012.

## Provenance

The founder's go-live brief, part 1, 2026-11-01. Its design spec file was not reachable from the working machine, so the design follows the brief's summary. Drafted by Claude Code as `uncost-admin`.

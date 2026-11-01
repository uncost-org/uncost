# CHG-012 — Sign-up email moves from Amazon SES to Postmark (amends CHG-009)

**Status:** founder decision, dated by the founder (2026-11-01). Drafted from the founder's Postmark brief. It takes effect when this record is merged. Sign-ups stay off in production: turning them on is still decision 1 in [CHG-009](CHG-009-signups.md). Amends [CHG-009](CHG-009-signups.md).

- **Date:** 2026-11-01
- **Amends:** [CHG-009](CHG-009-signups.md), for the provider that sends sign-up email and for its setup steps. CHG-009's history stands as written.
- **Changed claim:** with the switch on, sign-up emails are sent by Postmark, not Amazon SES. With the switch off, nothing changes: no page or `/sitemap.xml` differs.
- **Source:** the founder's Postmark brief (2026-11-01). No AI decision; this file records what the founder set, and the sources read for the privacy wording.

## Why

AWS refused SES production access twice, in the cases of 4 August and 1 November 2026, and gave no reason. Without production access, SES can send only to verified addresses, so the sign-ups could not open on it.

## The provider

**Postmark, operated by AC PM LLC, part of ActiveCampaign, in the United States.** The founder's brief expected "ActiveCampaign, LLC". What the sources say:
- Postmark's terms are with "AC PM, LLC", and its DPA names "AC PM LLC" as the data importer.
- ActiveCampaign's privacy policy calls Postmark's services "owned and operated by AC PM LLC", and AC PM LLC the data controller for them.

**The code,** in uncost-org/uncost-api (`MAIL_PROVIDER = "postmark"`; the SES settings stay, so switching back is one line):
- sends through `POST https://api.postmarkapp.com/email`, on message stream `outbound`, with `TrackOpens: false` and `TrackLinks: "None"`;
- answers "closed" unless `POSTMARK_SERVER_TOKEN`, `POSTMARK_WEBHOOK_SECRET` and `MAIL_POSTAL_ADDRESS` are all set.

## DNS records added

To be filled in when the founder publishes them, with their date, in this record and in the change log of `docs/INFRA-DOMAINS.md`. Postmark's domain page gives the exact values. Two records are expected:
- a **DKIM TXT** record at the host Postmark generates (`<selector>._domainkey.uncost.org`);
- a **Return-Path CNAME**, `pm-bounces.uncost.org` → `pm.mtasv.net`.

No `_dmarc` record is added. The apex record stays Cloudflare-managed at `p=none` (`docs/INFRA-DOMAINS.md`), and DMARC aligns through DKIM `d=uncost.org`.

## The webhook and its authentication

Postmark's bounce, spam-complaint and subscription-change webhooks post to `/api/signup/postmark-events`. That Pages Function forwards the body and the `Authorization` header to the Worker's `/v1/postmark-events`.

- **Authentication:** HTTP Basic, username `postmark`, password `POSTMARK_WEBHOOK_SECRET`, compared in constant time in the Worker. Postmark does not sign its webhooks; Basic auth is what its documentation recommends. A wrong or missing password gets 401 and changes nothing.
- **Limits:** the body is capped at 256 KB. The route answers 200, 400 or 401 with no body, and is dark (404) unless the Pages environment switches sign-ups on.
- **On the preview:** Cloudflare Access needs a Bypass policy for this path, as it has for `/api/signup/ses-events`.

| Event | Suppression |
|---|---|
| `Bounce` with `Type` `HardBounce`, `BadEmailAddress` or `ManuallyDeactivated` | `hard_bounce` |
| `SpamComplaint` | `complaint` |
| `SubscriptionChange` with `SuppressSending: true` | `HardBounce` → `hard_bounce`, `SpamComplaint` → `complaint`, `ManualSuppression` → `unsubscribe` |
| Anything else, including soft bounces and `Delivery` | none; answers 200 |

It uses the same suppression and audit code as the SES path, with no address in logs or audit.

## The privacy wording

/privacy/ stays version 0.4, not yet effective, shown only while `formsOpen` is on. Amazon Web Services, SES and SNS are replaced in §6, §11 and the version row. Version 0.3, which the live site shows, is unchanged.

- **§6:** Postmark, operated by AC PM LLC (part of ActiveCampaign), sends the sign-up emails and says when one bounces or is reported as spam, from the United States.
- **§6, the transfer:** AC PM LLC takes part in the EU-U.S. Data Privacy Framework and its UK Extension, through ActiveCampaign's certification, and that is the safeguard. This closes, for email, the mechanism CHG-009 left open under UNP-73 question 4.
- **§7 and §11:** Postmark keeps each email's content and activity for 45 days, its default, and keeps its own list of addresses that hard-bounced or complained.

**What was read, on 2026-11-01:**
- **[The Data Privacy Framework list](https://www.dataprivacyframework.gov/list), entry for ActiveCampaign, LLC:** Active Participant; other covered entities AC PM LLC and AC Snudrovia LLC. EU-U.S. framework Active (original certification 2016-09-19), UK Extension Active (2023-08-25), Swiss-U.S. Active (2018-11-21), all for non-HR data, next certification due 2027-09-24.
- **[ActiveCampaign's privacy policy](https://www.activecampaign.com/legal/privacy-policy)** (last updated 2026-10-01): Postmark's services are "owned and operated by AC PM LLC", and "ActiveCampaign, AC PM LLC and AC Snudrovia LLC comply with the EU-U.S. Data Privacy Framework".
- **[Postmark's DPA](https://postmarkapp.com/dpa)** (new customers, effective 2025-11-17): "AC PM has certified its compliance to the EU-U.S. Data Privacy Framework Principles", with the Standard Contractual Clauses (2021/914/EU, Module Two) where Data Protection Laws require them. It applies to customers who signed up on or after 2024-12-10.
- **[Postmark's terms](https://postmarkapp.com/terms-of-service):** the agreement is with "AC PM, LLC".
- **[Postmark on message storage](https://postmarkapp.com/support/article/how-long-are-inbound-and-outbound-messages-stored-in-activity)** (modified 2026-10-26): "email content, events (e.g. delivery, click, open), and metadata for all messages for 45 days by default".
- **[Postmark's Retention Add-on](https://postmarkapp.com/support/article/how-does-the-retention-add-on-work)** (modified 2026-10-26): 7 to 365 days, account-wide, on paid plans, set under Plans & Add-ons → Custom Activity Retention. If the account moves off 45 days, §7 and §11 must change with it.
- **[Postmark on inactive addresses](https://postmarkapp.com/support/article/903-an-address-has-been-marked-as-inactive-how-can-i-reactivate-it)** (modified 2026-10-26): hard bounces can be reactivated by the account; spam complaints only through Postmark, at the recipient's request. No time limit is stated.
- **[Postmark's email API](https://postmarkapp.com/developer/api/email-api) and its [webhook pages](https://postmarkapp.com/developer/webhooks/webhooks-overview):** the request, the payload fields and the retry rules the code follows.

## What stays

The SES domain identity, its DNS records (Easy DKIM, custom MAIL FROM `mail.uncost.org`), the configuration set, the SNS topic, the AWS IAM user and its keys, and `/v1/ses-events` all stay, unused. They are to be removed after go-live.

The contact form is unchanged; it sends through Cloudflare Email Routing.

## Conflicts, listed and not resolved

- **The deletion copy.** /signup/deleted/ and the delete confirm page say "We keep only a scrambled record…". The email Postmark sent, with the plain address, stays there for 45 days, and a hard-bounced or complaining address stays on Postmark's own list, with no stated limit. /privacy/ §7 and §11 now say so. Those two pages are not changed here; the brief covers the notice. They render only with the forms on, so this needs settling before go-live.
- **`docs/INFRA-DOMAINS.md`.** It names `mail.uncost.org` (SES) as the transactional identity. It is not changed here, because no Postmark record exists yet; it changes when the records are published.
- **POL-002 Rule 6 and its "adequate written terms".** The founder confirms Postmark's DPA applies to the account. Whether the transfer wording is right remains for counsel, as with the rest of /privacy/ 0.4.

## Re-test result

To be filled in after CHG-009's preview test is re-run through Postmark.

## Affected surfaces

- **With the switch off:** none. Every page and `/sitemap.xml` are byte-identical. `/api/signup/postmark-events` exists but answers 404.
- **With it on:** /privacy/ §6, §7, §11 and the version row.
- **Files:**
  - `website/functions/api/signup/postmark-events.js` (new);
  - `website/lib/signup.js` (`forward()` can pass on `Authorization`, for this route only);
  - `website/src/privacy.njk`, `tools/post_patch_pages.py` (the same text), `tools/signup_check.py`;
  - CHG-009 (one line under its setup heading).

## Provenance

The founder's Postmark brief, 2026-11-01. Drafted by Claude Code as `uncost-admin`.

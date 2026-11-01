# CHG-012 — Sign-up email moves from Amazon SES to Postmark (amends CHG-009)

**Status:** founder decision, dated by the founder (2026-11-01). Drafted from the founder's Postmark brief. It takes effect when this record is merged. Sign-ups stay off in production: turning them on is still decision 1 in [CHG-009](CHG-009-signups.md). Amends [CHG-009](CHG-009-signups.md).

- **Date:** 2026-11-01
- **Amended by:** [CHG-013](CHG-013-signups-go-live-prep.md), for the deletion copy.
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

The founder published two records on 1 Nov 2026, and they are in the change log of `docs/INFRA-DOMAINS.md`. Both show Verified in Postmark, as the founder reports.

| Name | Type | Value | TTL |
|---|---|---|---|
| `20261101110558pm._domainkey.uncost.org` | TXT (DKIM) | `k=rsa;p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCD5QPPll6gWvHdX3qx0ceGN6arMgOyPxK2wmby8Q/EWGfDhUbTRwN3yit3dMi7hJszY6WudA83yvnfqLNoiB7OoKr7EmMr8vwwjUTirCzwWZC2BGYJkMDXLIFbI1njwc9DKraE66SD5Lji7yGwZqjSpmo6bU3+r8Zhq0H2/1uKuwIDAQAB` | 300 |
| `pm-bounces.uncost.org` | CNAME (Return-Path) | `pm.mtasv.net` | 300 |

**How they were checked (1 Nov 2026):**
- The DKIM value is the same from 1.1.1.1, 8.8.8.8 and the zone's own Cloudflare nameserver. It is a well-formed 1024-bit RSA public key.
- It was not compared with the value on Postmark's domain page, which needs the Postmark login. Postmark's Verified status is that comparison.
- The SES records answer as before: `mail.uncost.org` still has its MX and SPF. The apex SPF and `_dmarc` (`p=none`) are unchanged.

No `_dmarc` record is added. The apex record stays Cloudflare-managed at `p=none` (`docs/INFRA-DOMAINS.md`), and DMARC aligns through DKIM `d=uncost.org`.

## The webhook and its authentication

Postmark's bounce, spam-complaint and subscription-change webhooks post to `/api/signup/postmark-events`. That Pages Function forwards the body and the `Authorization` header to the Worker's `/v1/postmark-events`.

- **Authentication:** HTTP Basic, username `postmark`, password `POSTMARK_WEBHOOK_SECRET`, compared in constant time in the Worker. Postmark does not sign its webhooks; Basic auth is what its documentation recommends. A wrong or missing password gets 401 and changes nothing.
- **Limits:** the body is capped at 256 KB. The route answers 200, 400 or 401 with no body, and is dark (404) unless the Pages environment switches sign-ups on.
- **On the preview:** Cloudflare Access has a Bypass policy for this path, as it has for `/api/signup/ses-events`. With it in place, a request with no password or the wrong one gets 401 on the preview (1 Nov 2026).

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

- **The deletion copy.** /signup/deleted/ and the delete confirm page say "We keep only a scrambled record…". The email Postmark sent, with the plain address, stays there for 45 days, and a hard-bounced or complaining address stays on Postmark's own list, with no stated limit. /privacy/ §7 and §11 now say so. Those two pages are not changed here; the brief covers the notice. **Settled by [CHG-013](CHG-013-signups-go-live-prep.md)**, which adds the same facts to both pages.
- **POL-002 Rule 6 and its "adequate written terms".** The founder confirms Postmark's DPA applies to the account. Whether the transfer wording is right remains for counsel, as with the rest of /privacy/ 0.4.

## Re-test result

**Result: all nine steps done, with the limits below.** The founder ran CHG-009's nine steps through Postmark on 1 Nov 2026, 19:45–19:57 ICT, and three actions missing from that run's evidence in a top-up at about 22:22 ICT. **No real spam complaint has been tested**, and the two repeat Confirm presses rest on the founder's report.

- **Tested:** `signups-test` (deployment `4edcc28f`, this PR at `e9e27f0`), against the Worker `uncost-signups` version `024d868f` (uncost-api `48d1fb4`, with the founder's secrets).
- **Evidence:** for the main run, the log of every Worker request and D1 rows read without addresses. For the top-up, D1 rows only. By the founder's decision, D1 rows replace step 6's admin export. What a page or an inbox showed rests on the founder's report.
- **Failures:** none logged in the main run: no send failures and no exceptions. The log was not running for the top-up.

| Step | What the log and D1 show | Result |
|---|---|---|
| 1. Sign | `/v1/pledge` 202 at 19:45:45. | Shown |
| 2. Confirm | `/v1/confirm` 200 at 19:46:29, with `confirm_pledge` and `confirm_updates` in the audit. Only one `/v1/confirm` request in that run; the second press is in the top-up. | First press shown; second press on the founder's report |
| 3. Sign again | `/v1/pledge` 202 at 19:48:49. That "no email" went out rests on the founder's report: step 6 removed the subject and its tokens. | Shown, on the founder's report |
| 4. Updates only | `/v1/updates` 202 at 19:51:39. Its `updates_confirm` token is unused and no `/v1/confirm` request follows, so that run did not confirm it. The top-up did. | Shown in the top-up |
| 5. Unsubscribe | `/v1/unsubscribe` 200 at 19:52:04, an `unsubscribe` row, and that subscription `unsubscribed`. No later `/v1/updates` request in that run; the second sign-up is in the top-up. | Shown; second sign-up in the top-up |
| 6. Delete | `/v1/delete` 200 at 19:52:24, audit `delete` via link, a `deletion` row, and step 1's subject gone. | Shown |
| 7. Without JS | `/v1/pledge` 202 at 19:54:00, `/v1/confirm` 200 at 19:54:32, pledge `accepted_unique`, updates `confirmed`. The Worker cannot see whether JavaScript was off. | Shown, on the founder's report |
| 8. Bounce | Signed as `hardbounce@bounce-testing.postmarkapp.com` at 19:54:50. A `hard_bounce` row at 19:57:16, and that subscription `unsubscribed`. | Shown; **2 min 26 s**, not CHG-009's "within a minute" |
| 9. Spam notification | Signed as `spamnotification@bounce-testing.postmarkapp.com` at 19:55:05. One webhook 200 at 19:57:12 with no audit row, and no suppression. The log does not name the event type, so linking the two is an inference. | Shown as expected, see below |

**Step 9 could not test a complaint.** [Postmark's test addresses do not cover spam complaints](https://postmarkapp.com/support/article/1239-how-to-test-bounces) ("will default to a Hard Bounce"; [also here](https://postmarkapp.com/developer/user-guide/sandbox-mode/generate-fake-bounces); both read 1 Nov 2026). A spam notification is a different event, and the code rightly adds no suppression for it. The `complaint` path rests on:
- the unit tests;
- one `complaint` row at 19:37:11 from a webhook event that carried the right password, before the test started. It is taken to be the founder's test event from Postmark; the log had not started, so this is not confirmed.

No real complaint has come through Postmark.

**Also seen:**
- The hard bounce produced two `suppress` audit rows a second apart, and one suppression row. The audit count can run above the row count, with no effect on who is suppressed.
- The preview's D1 database has more test rows now. CHG-009's follow-up stands: recreate it before production.

**The top-up, about 22:22 ICT, with one new address for steps 4 and 5 and step 7's address for a repeat press:**

| Action | What D1 shows | Result |
|---|---|---|
| Sign up for updates | A new subject at 22:22:14, consent `given` on the footer form. | Shown |
| Confirm | `updates_confirm` token used at 22:22:34, `confirmed_at` set, one `confirm_updates` audit row. | Shown |
| Confirm again, on that link | Still one audit row, and the token's `used_at` is unchanged. A repeat press writes nothing, by design, so D1 shows that nothing changed and cannot show the press. | On the founder's report |
| Unsubscribe | `unsubscribe` token used at 22:23:17, an `unsubscribe` row, and the subscription `unsubscribed`. | Shown |
| Sign up again | No token, consent event or subject change after 22:23:17. A suppressed sign-up stops before it writes anything, so D1 shows that no link was issued and cannot show the request. | No email shown; the request on the founder's report |
| Confirm again, on step 7's link | No token used and no audit row since the main run. The same limit applies. | On the founder's report |

## Affected surfaces

- **With the switch off:** none. Every page and `/sitemap.xml` are byte-identical. `/api/signup/postmark-events` exists but answers 404.
- **With it on:** /privacy/ §6, §7, §11 and the version row.
- **Files:**
  - `website/functions/api/signup/postmark-events.js` (new);
  - `website/lib/signup.js` (`forward()` can pass on `Authorization`, for this route only);
  - `website/src/privacy.njk`, `tools/post_patch_pages.py` (the same text), `tools/signup_check.py`;
  - CHG-009 (one line under its setup heading);
  - `docs/INFRA-DOMAINS.md` (the Postmark records, the mail posture, the change log).

## Provenance

The founder's Postmark brief, 2026-11-01. Drafted by Claude Code as `uncost-admin`.

# CHG-009 — The Pledge and email updates sign-ups, built and switched off (amends CHG-007)

**Status:** drafted from the founder's sign-ups brief (2026-10-21). The sign-ups are built and tested, and they stay **off in production**. Nothing in this record turns them on: that is founder decision 1 below, still open. One founder decision is recorded as made (the postal address). Amends [CHG-007](CHG-007-rights-and-transfer-safeguard.md), the latest privacy record, and follows [CHG-008](CHG-008-icon-and-pdf-licences.md).

- **Date:** 2026-10-21
- **Amends:** [CHG-007](CHG-007-rights-and-transfer-safeguard.md), whose §5 transfer safeguard names Cloudflare and Google only. It also partly closes UNP-73 question 4 ([CHG-006](CHG-006-privacy-notice-and-records.md), "Sign-up providers") and settles nothing else in CHG-006's open list.
- **Changed claims:** none while sign-ups are off. With the build switch off, every page the site serves is byte-identical to the build before this change. Only `/js/ui.js` and `/css/integration.css` differ, and `/sitemap.xml` lists the same 55 URLs with /privacy/ in a different place (pages are ordered by file date). With the switch on, /privacy/ becomes version 0.4 (below) and the forms post to working handlers.
- **Source:** the founder's sign-ups brief (2026-10-21). The governing spec is UNP-57 revision 5 (`d55be3b5`) and the UNP-63 build plan; where the brief is narrower, the brief wins, and what it leaves out is listed below. No AI decision; this file records what the founder set and what was built.
- **Rationale:** have the backend for the two forms the site already shows built, tested on a preview and ready, so that opening them is a switch and a dated founder decision rather than a build.

## What is built

**The backend: `uncost-org/uncost-api`** (private), the Worker `uncost-signups` and its D1 database `uncost-signups`. Pull request: [uncost-org/uncost-api#1](https://github.com/uncost-org/uncost-api/pull/1).
- **Shape.** The Worker has no public URL (`workers_dev` and preview URLs are off). It is reached only through a Service binding, `SIGNUPS`, from this site's Pages Functions. It is JavaScript ES modules with no runtime dependency.
- **Data.**
  - The address is held only AES-256-GCM encrypted, and found by an HMAC-SHA-256 key of the normalized address (UNP-57 §9.1), with key versions (§9.2).
  - Pledges: `pending_verification`, `accepted_unique` or `withdrawn`, with an optional name that is never shown.
  - Updates subscriptions: `pending_confirm`, `confirmed` or `unsubscribed`.
  - Consent events: append-only, holding the policy version and a SHA-256 of the exact text shown. The purposes `assembly_interest` and `public_recognition` exist in the schema, but a trigger refuses them.
  - Tokens: stored as a hash only, single use. Pledge links last 24 hours and updates links 7 days.
  - A keyed suppression list, and an append-only audit log.
  - The count of confirmed pledges is a query (`scripts/admin.mjs count`); there is no public counter.
- **Behaviour.**
  - The same answer for a new, repeated, pending or suppressed address. A suppressed address is never emailed: suppression is checked at intake and again before every send.
  - Double opt-in. The Pledge's "also email me updates" box creates a subscription that the same link confirms, with its own consent event.
  - One-click unsubscribe (RFC 8058), or a no-JS confirm page.
  - Deletion by a signed single-use link. It keeps only the suppression row and the audit event.
  - SES bounce and complaint handling, through a verified SNS signature and topic.
  - A daily retention job, safe to run twice.
  - An admin script that exports or deletes by address, run with wrangler.
- **Email.**
  - One sender interface: Amazon SES v2 in `us-east-1` (the default), or Postmark (a fallback, not in use), chosen by `MAIL_PROVIDER`.
  - Sent From `Uncost <confirm@uncost.org>`, as plain text plus a simple HTML part, with no tracking, images or third-party links.
  - Every message ends with who it is from and why, unsubscribe and delete links, /privacy/ and the postal address.
  - With `MAIL_POSTAL_ADDRESS` empty, nothing is sent and the forms answer as if closed.

**The site, in this repository.**
- **Handlers.** `website/functions/api/signup/` holds the Pages Functions:
  - `pledge` and `updates` (POST);
  - `confirm`, `unsubscribe` and `delete` (GET shows a no-JS page with a button; only that page's same-origin POST acts, so a mail scanner that opens a link changes nothing);
  - `ses-events` (POST).

  Their shared code is `website/lib/signup.js`. Each handler checks Origin and Sec-Fetch-Site on POST and forwards through `SIGNUPS`. A sign-up whose forward fails, or that gets any Worker answer other than accepted, refused or closed, is answered as not sent. They set no cookies.
- **Forms and pages.**
  - The live forms are `partials/forms/pledge.njk` and `partials/forms/updates.njk`. The updates form's ids carry its surface, because it appears twice on `/` and `/join/`.
  - `_data/signups.json` holds the consent texts and the minimum age. The templates render the same texts that the handlers hash.
  - `ui.js` sends the forms with fetch and shows the result in place.
  - New plain pages: /updates/check-email/, /updates/confirmed/, /signup/not-sent/, /signup/unsubscribed/, /signup/deleted/ and /signup/link-expired/.
  - /privacy/ version 0.4 (CP-4), and integration.css item 146 (the resend page's form, phone widths, and the updates form inside a cream page).
- **Checks.** `tools/signup_check.py` and the forms rule in `scripts/audit_website.py`.

## Two switches, both off

1. **Build:** `features.formsOpen` (`UNCOST_FORMS_OPEN=on`). While it is off, no sign-up input renders anywhere; only "Sign-ups open soon."
2. **Runtime:** every `/api/signup/*` handler answers 404 unless the Pages environment sets `UNCOST_SIGNUPS_OPEN=on` **and** carries the `SIGNUPS` binding. A Worker that is not set up for mail answers 503, and the handler turns that into 404 as well.

The Content-Security-Policy does not change: `form-action 'self'` and `connect-src 'self'` already cover same-origin handlers. The confirm, unsubscribe and delete pages are rendered by a Function, which `_headers` does not reach, so they send their own stricter policy (`default-src 'none'`, no script).

## Founder decision recorded (2026-10-21)

1. **Postal address in every email.** The postal address shown in every sign-up email is the mailbox **96 Clinton Ave, PMB 111, Newark, NJ 07114**. It is a published business mailbox, not a personal address, and it appears in every email. It is set as the Worker's plain variable `MAIL_POSTAL_ADDRESS` in the Cloudflare dashboard; the code holds no address, and without the variable nothing is sent.

## Founder decisions still open (each dated by the founder)

1. **Turning sign-ups on in production** — YYYY-MM-DD. This includes setting `noticeEffective` in `_data/signups.json`, the effective date of /privacy/ version 0.4, which renders "date to be set" until then.
2. **Datastore: Cloudflare D1 instead of Neon** (the UNP-63 plan) — YYYY-MM-DD.
   - Location hint `enam` (eastern North America).
   - D1 Time Travel restores to any minute in the last **30 days on Workers Paid and 7 days on Workers Free**, in place, overwriting the database. Source: Cloudflare's D1 Time Travel and limits pages (last updated 2026-04-21), read on 2026-10-21. This is UNP-66 condition 3.
3. **Code home: `uncost-org/uncost-api`** — YYYY-MM-DD. This closes CHG-005 decision 4, which accepted the contact form's backend in this repository "to be revisited when any data system is built". The contact form stays where it is.
4. **Retention rule for sign-ups** — YYYY-MM-DD. Proposed, and shown in /privacy/ §7 only while the switch is on:
   - unconfirmed sign-ups and their links: deleted after 7 days;
   - a Pledge signature: kept until the person asks for deletion;
   - an updates subscription: kept until unsubscribe. With nothing left, the address and consent records go within about a week;
   - spent links: deleted 7 days after they expire;
   - the keyed do-not-email record: kept while the opt-out must be honoured, and reviewed every year;
   - dated audit notes with no address: kept.

   POL-002 Rule 5 requires a rule before collection.
5. **Minimum age** — YYYY-MM-DD. The default is 18, matching the contact form (CHG-005 decision 3), and it is one value, `minAge` in `_data/signups.json`. UNP-73 CF-1 leaves it with the founder and counsel.

## UNP-73 question 4: partly closed

- **Providers: chosen.**
  - Cloudflare, Inc.: Pages Functions, Workers and D1 (eastern North America).
  - Amazon Web Services, Inc.: SES and SNS in `us-east-1` (United States).
  - Postmark is a fallback in the code, not in use.
- **Transfer mechanism: open.** /privacy/ §6 (version 0.4) says AWS sends the emails from the United States, but names no safeguard for that transfer. The safeguard sentence still covers only Cloudflare and Google (CHG-007). The mechanism is for the founder and counsel to settle before sign-ups open in production.

## /privacy/ version 0.4 (shown only while the switch is on)

CP-4 in `tools/post_patch_pages.py` restates it; `privacy.njk` is re-derived. Built with the switch off, the page is byte-identical to version 0.3, and §11 is exact. Built with it on:
- **§11** becomes "Sign-ups: the Pledge and email updates". It covers:
  - what is collected, why, and on what basis (consent);
  - confirming by email, with the 24-hour and 7-day links and deletion after 7 days;
  - who provides each part;
  - retention, by reference to §7;
  - unsubscribe, delete and access;
  - what happens if Uncost changes hands.
- **§2, §3, §6, §7 and §8** gain the sign-up lines: what is collected, the legal basis (consent, and legitimate interests for the do-not-email record), the providers and where they process data, the proposed retention, and the links in every email.
- **The header** reads version 0.4, and **§12** has a 0.4 row with the date left for the founder.

## Rollback

Unset `UNCOST_SIGNUPS_OPEN` on the Pages project, rebuild without `UNCOST_FORMS_OPEN`, and redeploy. Pages applies a variable change to new deployments, so the redeploy is what closes the handlers:

```
cd website && rm -rf dist && npm ci && npm run build
python3 ../scripts/audit_website.py --built dist
npx wrangler pages deploy dist --project-name=<project>
```

The data stays in D1 until it is deleted. Record the rollback here with its date and reason.

## Conflicts, listed and not resolved

- **UNP-57 §4 and §17 test 28.** The newsletter's double opt-in is meant to be separate from Pledge verification ("pledge verification does **not** confirm the newsletter"). The brief has the Pledge's updates box confirmed by the same link. Built as the brief says.
- **UNP-57 §4.** Every marketing *and confirmation* send carries `List-Unsubscribe`. The brief puts the header on every message that is not a confirmation. Today every message is a confirmation, so none carries it, although every message's footer has the unsubscribe link.
- **UNP-57 §6A and §17 test 29.** The packet says the root domain does not send and sending uses subdomains. The brief sends From `confirm@uncost.org`, the apex, with MAIL FROM `mail.uncost.org`. DMARC alignment is relaxed through DKIM `d=uncost.org`. The apex DMARC stays Cloudflare-managed at `p=none` (`docs/INFRA-DOMAINS.md`), and no `_dmarc` record is added.
- **UNP-57 §3.5 and §17 test 25, and §4A `consent_transfer_ack`.** These ask for a transfer disclosure at each form's consent point, acknowledged by a required box. It is not on the forms. /privacy/ §11 (0.4) says a sign-up passes to a fiscal sponsor or successor under the notice, which is new wording for counsel to check.
- **POL-002 Rule 1 and UNP-57 §4.1.** "Reviewed age/guardian handling": the age is 18 by default and open (decision 5).
- **POL-002 Rule 5.** A retention rule is needed before collection: proposed, open (decision 4).
- **POL-002 Rule 6, Rule 3 and CHG-006 question 4.** Transfer mechanisms and "adequate written terms" are needed before cross-border processing. The AWS transfer mechanism is open, and AWS's data processing terms are to be confirmed by the founder.
- **POL-002 adoption checklist.** It still requires "qualified privacy/legal review". POL-002 is not adopted, and this record does not adopt it.
- **CHG-005 decision 4.** The backend now lives in a separate repository: decision 3 above.
- **The /pledge/ page.** Its "What happens when you sign" band (export copy) still says "You can register interest in the advisory Assembly". The live form has no Assembly box, because Assembly interest is never written. The copy is not changed here.
- **The /join/ page.** The export's interest form there is replaced by the updates form (`tools/post_patch_pages.py`, CHECKLIST H). With the switch on, that form sits under the export's heading "The interest form." and its promise to "reply from a human inbox". The copy is not changed here.
- **The deletion copy.** The delete confirm page and /signup/deleted/ say what deletion keeps (the do-not-email record and a dated note), as the brief asks. UNP-57 §5 also asks deletion to "propagate to the ESP". SES keeps no list of ours, but SES's account-level suppression list would keep a bounced or complaining address in plain text. Setup step A5 turns it off for the configuration set.

## Left out: the brief is narrower than UNP-57

- **The public counter and its receipt** (§10, §12; §17 tests 3–7 and 40's counter parts). `signatureCounter` stays off.
- **The abuse ladder** (§11; tests 12, 16 and 32): risk scoring, challenges, quarantine and signed form tokens. Abuse control is the honeypot, the Origin and Sec-Fetch-Site checks, the per-address 10-minute resend window, and a suggested Cloudflare rate-limit rule.
- **Soft-bounce counting** (§13.1; test 27's second half). Only permanent bounces and complaints suppress.
- **Merge semantics** (§9.3; test 39). A confirmed signer who signs again changes nothing: no name update and no fresh consent event.
- **Assembly interest and public recognition.** They are in the enum only and are never written.
- **Correction of a stored name** (§5). It is handled by email request, like access.

## Evidence

From committed scripts, 2026-10-21:
- the Worker's test suite (`npm test` in uncost-api, Miniflare with a local D1);
- `tools/signup_check.py`;
- `scripts/audit_website.py --built`, run three ways;
- `tools/prod_check.py`, `tools/contact_form_check.py`, `tools/axe_check.py` and `tools/restatement_check.py`.

The pull request lists the results.

## Setup, in order (founder; nothing here was done by Claude Code)

**Cloudflare**
1. Create the D1 database `uncost-signups`, location hint `enam`. Put its id in `wrangler.toml`, then apply the migrations: `npx wrangler d1 migrations apply uncost-signups --remote`.
2. Set the Worker's secrets: `HMAC_KEY_V1` and `ENC_KEY` (32 random bytes each, base64), `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`. Keep a copy of both keys outside Cloudflare: the admin script needs them, and every HMAC key ever used must be kept.
3. Deploy the Worker by hand from uncost-api (`npx wrangler deploy`). Then set its plain variables `MAIL_POSTAL_ADDRESS = 96 Clinton Ave, PMB 111, Newark, NJ 07114` and `SNS_TOPIC_ARN`. `keep_vars` keeps them across deploys.
4. On the **preview** Pages project only (`uncost-site-preview`, Preview environment): the Service binding `SIGNUPS` → `uncost-signups`, and the variable `UNCOST_SIGNUPS_OPEN=on`.
5. Cloudflare Access on the preview: a Bypass policy for `/api/signup/ses-events` only, so that SNS can reach it. The Worker verifies every SNS message's signature and topic.
6. Rate limiting. On the Free plan the zone has one rate-limiting rule, with path-only expressions, a 10-second period and a 10-second block. Extend the `/api/contact` rule (CHG-005) rather than adding one, for example to `(http.request.uri.path in {"/api/contact" "/api/signup/pledge" "/api/signup/updates"})`, counted by IP, with a threshold such as 5 requests per 10 seconds. The confirm, unsubscribe, delete and SNS paths stay out of it.

**AWS (the Uncost account, `us-east-1`)**
1. In SES, confirm that the domain identity `uncost.org` is verified, with Easy DKIM, and custom MAIL FROM `mail.uncost.org`. The DNS records are recorded in `docs/INFRA-DOMAINS.md` as existing; no DNS change, and no `_dmarc` record.
2. An IAM user for the Worker, allowed only `ses:SendEmail`, on two resources: the `uncost.org` identity and the configuration set `uncost-signups`. Condition: `ses:FromAddress` = `confirm@uncost.org`. Create an access key pair for it (step Cloudflare 2).
3. The configuration set `uncost-signups`, with open and click tracking off.
4. An SNS topic (for example `uncost-ses-events`) as the configuration set's event destination for Bounce and Complaint. Subscribe it over HTTPS to `https://<preview host>/api/signup/ses-events`, with raw message delivery off. The Worker confirms the subscription itself.
5. In the configuration set's suppression settings, turn off SES's account-level suppression list for this set. The Worker keeps its own keyed list, so AWS then holds no plain address after a bounce or complaint.
6. While the SES account is in the sandbox, verify the one test inbox you will use as an identity. The SES mailbox simulator addresses work without that.

**Preview build and test.** Build: `cd website && UNCOST_CONTACT_FORM_OPEN=on UNCOST_FORMS_OPEN=on npm run build && npx wrangler pages deploy dist --project-name=uncost-site-preview --branch=signups-test`. Then, on that preview:

1. **Sign.** Sign the Pledge with the test inbox and the updates box ticked. The page shows "Check your inbox" in place. The email arrives From `Uncost <confirm@uncost.org>`, with the footer and the postal address.
2. **Confirm.** Open the link: a page asks you to confirm, and nothing has changed yet. Press Confirm: you land on /pledge/verify/. Open the link and press Confirm again: the same page, and nothing changes.
3. **Sign again.** The same answer, and no email.
4. **Updates only.** Sign up for updates from the footer with a second address. Open its link and press Confirm: you land on /updates/confirmed/.
5. **Unsubscribe.** Use the email's unsubscribe link, then the confirm page's button. You land on /signup/unsubscribed/, and signing up for updates again sends nothing.
6. **Delete.** Use the delete link and confirm. You land on /signup/deleted/. `node scripts/admin.mjs export <address>` then shows only the suppression row.
7. **Without JS.** Repeat step 1 with JavaScript off: you land on /pledge/check-email/.
8. **Bounce.** Sign the Pledge as `bounce@simulator.amazonses.com`. Within a minute, the admin export for that address shows suppression `hard_bounce`.
9. **Complaint.** Sign the Pledge as `complaint@simulator.amazonses.com`. Its suppression shows `complaint`.
10. **Retention.** The next day, `npx wrangler d1 execute uncost-signups --remote --command "SELECT created_at, detail FROM audit_event WHERE action = 'retention'"` shows the daily job's row.

**What changes later, for production** (after decision 1):
- Recreate `uncost-signups` empty (or delete every test row), so no test data or test suppression goes live.
- Request SES production access.
- Add the `SIGNUPS` binding and `UNCOST_SIGNUPS_OPEN=on` to the production project `uncost`.
- Re-point the SNS subscription to `https://uncost.org/api/signup/ses-events`.
- Set `noticeEffective`.
- Build with `UNCOST_FORMS_OPEN=on` and deploy.
- Record the deploy in `docs/INFRA-DOMAINS.md`.
- Settle the AWS transfer safeguard, the age and the retention rule first.

## Private records (outside this repository)

The data inventory and the processor register stay private, as CHG-006 says. The new rows go to the founder with this change, in CHG-006's columns:
- **inventory:** the Pledge, the updates subscription, consent events, the suppression list and link tokens;
- **processors:** Cloudflare D1; AWS SES and SNS; Postmark, marked "fallback, not in use".

## Affected public surfaces

- **With the switch off:** none. Every page is byte-identical; `/js/ui.js` and `/css/integration.css` change, `/sitemap.xml` reorders one entry, and `/api/signup/*` exists but answers 404.
- **With it on:**
  - /pledge/ and /pledge/resent/;
  - the updates form in every page's footer, on / and on /join/;
  - /privacy/ (version 0.4);
  - the six new pages;
  - the pledge-flow pages, which leave noindex (layouts/base.njk, as before).

## Provenance

The founder's sign-ups brief, 2026-10-21. Drafted by Claude Code as `uncost-admin`.

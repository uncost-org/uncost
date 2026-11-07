# CHG-017 — Sign-ups go live in production (amends CHG-009 and CHG-013)

**Status:** founder decision (2026-11-07). Drafted from the founder's go-live brief, part 2. **Sign-ups are live in production since 2026-11-07 12:47 UTC**, when the founder approved the forms-on deploy (Pages deployment `07fc3f05-d0d8-426a-8aa9-bb768f6ecd6c`). The live check passed except for one test, and one follow-up is open (below).

- **Date:** 2026-11-07
- **Amended by:** [CHG-018](CHG-018-privacy-rate-limit.md) (2026-11-07), for follow-up 3: /privacy/ version 0.5.
- **Amends:** [CHG-009](CHG-009-signups.md), whose decisions 1 (turning on) and 3 (code home) it dates, and whose database it replaces; [CHG-013](CHG-013-signups-go-live-prep.md), whose go-live checklist the brief governs where they differ (listed below). Their history stands as written.
- **Changed claim:** with the forms-on build deployed, the Pledge and the email updates take sign-ups on uncost.org, and /privacy/ version 0.4 is effective from 7 November 2026. With the switch off, every page is unchanged by this record.
- **Source:** the founder's go-live brief, part 2 (2026-11-07). No AI decision; this file records what the founder set.

## Founder decisions recorded in CHG-009

Dated by the founder, 2026-11-07:
- **decision 1, turning sign-ups on in production;** `noticeEffective` in `website/src/_data/signups.json` is "7 November 2026", the effective date /privacy/ shows for version 0.4 while the forms are on;
- **decision 3, code home:** `uncost-org/uncost-api`.

## The production database

- **New:** the D1 database `uncost-signups-live`, created on 2026-11-07 with location hint `enam` (eastern North America). Migration `0001_signups.sql` is applied: 8 tables, 5 indexes and 4 triggers. Read back after the migration, every table was empty.
- **Kept:** the preview's database `uncost-signups` is left untouched as the test record. At go-live it held the preview's test rows only: 11 people, 9 Pledge rows, 11 updates subscriptions, 26 consent events, 33 link tokens, 12 suppression rows and 44 audit notes. **It is to be deleted on or after 2026-12-07** (30 days).
- **This replaces CHG-013's checklist step 2,** which recreated `uncost-signups` empty. No test row or test suppression reaches the new database. Every `HMAC_KEY_V<n>` stays set.

## The Worker (`uncost-org/uncost-api`)

- **Database binding:** [uncost-org/uncost-api#4](https://github.com/uncost-org/uncost-api/pull/4) points the binding `DB` at `uncost-signups-live`. After #4 was merged, the Worker was deployed by hand from `main` (`9ac9dd0`) on 2026-11-07 at 12:22:52 UTC, with the founder's approval: version `caa69997-e9ee-4713-a357-06cdc484202e`, read back with `DB` bound to `uncost-signups-live`. Code and `LINK_ORIGINS` (which covers `https://uncost.org`) are as on `main` (CHG-013 step 3).
- **AWS secrets removed (2026-11-07):** `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`, since Postmark sends the email (CHG-012). The Worker keeps its HMAC key, its email key and the two Postmark secrets.
- **AWS (the founder, 2026-11-07):** the IAM user `uncost-signups-worker`'s access key was deactivated, then deleted, in the AWS console. The SES identity and its DNS records stay for now.

## Production steps (the founder, in the dashboards)

1. **Cloudflare, Pages `uncost`, Production:** the Service binding `SIGNUPS` → `uncost-signups`, and the text variable `UNCOST_SIGNUPS_OPEN` = `on`. Pages applies both to new deployments only.
2. **GitHub, repository variable:** `UNCOST_FORMS_OPEN` = `on`.
3. **Cloudflare, uncost.org zone, rate limiting:** the existing `/api/contact` rule also covers `/api/signup/pledge` and `/api/signup/updates`, counted by IP, 5 requests per 10 seconds, blocking for 10 seconds. The confirm, unsubscribe, delete and webhook paths are left out (CHG-013 step 6).
4. **Postmark, Default Transactional Stream:** the webhook URL is `https://uncost.org/api/signup/postmark-events`, with the same Basic auth, and a test Bounce shows Verified (CHG-013 step 5).
5. **The preview:** on the Pages project `uncost-site-preview`, Preview environment, the `SIGNUPS` binding and `UNCOST_SIGNUPS_OPEN` are removed, so a preview test can't write to the production database. The Access application `uncost signups SNS` is deleted.

The founder did these on 2026-11-07, then re-ran the production deploy with the forms on and approved it.

**Postmark's webhook test:** the webhook URL could not be verified before that deploy. `/api/signup/*` answers 404 until a deployment carries the `SIGNUPS` binding and `UNCOST_SIGNUPS_OPEN`, so saving it first failed on Spam Complaint and Subscription Change. The founder sent the tests again after the deploy and saved it; Postmark shows the webhook as Verified.

**The deploys, in order:**
1. #105's waiting deploy (`949c055`) was approved.
2. #107 was merged and deployed with the forms off: deployment `e9cdc061-67ea-4ae2-b6ce-62e31ca6775b`, `3f53cdb`.
3. The founder made the dashboard changes, and re-ran that deploy (run 42371803058, attempt 2) with `UNCOST_FORMS_OPEN=on`: deployment `07fc3f05-d0d8-426a-8aa9-bb768f6ecd6c`, built 12:46 UTC, deployed 12:47:52 UTC.

## Where the brief differs from CHG-013's checklist

- **Step 2:** a new database instead of recreating the old one (above).
- **Step 4:** the founder confirmed that the Postmark account was approved (2026-11-01). The DPA and the private register rows are done.
- **Step 9:** the live check is sign, confirm, then delete, with a hard bounce to Postmark's test address. Unsubscribe is not in the brief.
- **Step 10:** the deploy and its date go into `docs/INFRA-DOMAINS.md` with the live check result, in a later record.

## Live check result

2026-11-07, read from the Worker's log (`wrangler tail`) and the database, with no address recorded. All times are UTC.

- **The deployment:** `07fc3f05-d0d8-426a-8aa9-bb768f6ecd6c` (Production, `3f53cdb`). The previous deployment was `e9cdc061-67ea-4ae2-b6ce-62e31ca6775b`.
- **The pages:**
  - `/pledge/` shows the Pledge form.
  - The updates form is in the footer of `/`, `/join/`, `/privacy/` and `/about/`.
  - /privacy/ shows version 0.4, "Effective 7 November 2026", in both places.
- **The handlers:**
  - An empty POST to `/api/signup/pledge` or `/api/signup/updates` is now sent on to `/signup/not-sent/` (303), where it answered 404 before.
  - `/api/signup/postmark-events` without credentials answers 401.
- **The founder's Pledge:**
  - Signed with updates at 12:50:20, and the email was sent.
  - Confirmed at 12:51:17: the Pledge and the updates subscription.
  - Deleted with the email's link at 12:51:32.
  - Read back after the deletion: the person's record, Pledge, subscription, consent events and links are gone. Left are a do-not-email record (reason "deletion", no address) and three sign-up notes.
- **The email:** the logo badge and the robot both showed (Spark, dark mode).
- **The hard bounce, not run:**
  - A Pledge with Postmark's hard-bounce test address was accepted at 12:49:47 (202).
  - Postmark refused to send it (HTTP 422, ErrorCode 406): the address was already inactive on Postmark's own list from the CHG-012 tests. So there was no email, no bounce and no suppression row.
  - At the founder's direction the address stays inactive. That sign-up's pending row is removed by the retention job after 7 days.
- **Postmark's webhook tests:** each was answered 200 by the Worker.
  - Bounce (12:52:00) added a suppression row, reason "hard_bounce".
  - Spam Complaint (12:53:38) added one with reason "complaint".
  - Subscription Change (12:53:42) was read as a hard bounce for the same sample address. The Worker keeps one row per address and reason, so it added only a sign-up note.
  - Saving the webhook (12:53:49) sent three more events, which matched those rows.
- **Uptime and the contact form:** `scripts/uptime_check.py` passed against production at about 12:55: home, www, robots, sitemap, contact and security.
- **The database after the check:**

  | Table | Rows |
  |---|---|
  | People | 1 (the hard-bounce test, pending) |
  | Pledges | 1 |
  | Updates subscriptions | 0 |
  | Consent events | 1 |
  | Links | 3 |
  | Suppression | 3 (deletion, hard bounce, complaint) |
  | Sign-up notes | 9 |

## Follow-ups

1. **When Postmark refuses an inactive address (ErrorCode 406), no local suppression row is added.** The Worker logs "not sent" and nothing more. Postmark still blocks the address, but our own do-not-email list doesn't know about it, and the sign-up waits for the retention job. One possible fix in `uncost-org/uncost-api` is to treat 406 as a hard bounce for that address. Founder's call.
2. **Delete the test database `uncost-signups` on or after 2026-12-07.**
3. **The rate limit in /privacy/:** §2 and §3 name the rate limit only for the contact form. Since 2026-11-07 it also covers the two sign-up forms. Changing that wording is a notice change (POL-002), so it is listed here, not made. Done in [CHG-018](CHG-018-privacy-rate-limit.md).
4. **Preview deployments made before the preview's `SIGNUPS` binding was removed keep it.** They are behind Access, but a sign-up on one would still reach the production database until they are redeployed or deleted.
5. **The remaining AWS setup** (the SES identity and DNS, the SNS topic, the IAM user) is removed later (CHG-012).

## Rollback

CHG-013's rollback stands:
1. Set the repository variable `UNCOST_FORMS_OPEN` to anything but `on`, or delete it.
2. On the project `uncost`, remove the `SIGNUPS` binding and `UNCOST_SIGNUPS_OPEN`.
3. Run `deploy-production` and approve it. Pages applies a binding change only to new deployments, so the redeploy is what closes the handlers.

For speed, the dashboard's rollback to the previous deployment restores the earlier pages and handlers (CHG-010). The deployment before go-live is `e9cdc061-67ea-4ae2-b6ce-62e31ca6775b`: the same commit, built with the forms off and without the binding.

**The data stays** in `uncost-signups-live` until it is deleted. Deletion requests are still answered with the uncost-api admin script. Pointing the Worker back at `uncost-signups` would mix production rows with test rows, so it is not part of the rollback. Record any rollback here with its date and reason.

## Private records

The founder's processor register and data inventory (CHG-006) were updated after the live check, on 2026-11-07. They now record the production database, list the sign-up categories as live, and no longer list Amazon SES and SNS. They stay outside this repository.

## Checks

On this branch, against `main` at `3dd9f3f`. The pull request lists the counts.

## Affected surfaces

- **With the switch off:** none. Every page is byte-identical.
- **With it on:** /privacy/ shows version 0.4 as effective from 7 November 2026, instead of "date to be set". The forms, the handlers and the pages CHG-009 lists open in production only with the steps above.
- **Files:**
  - `website/src/_data/signups.json` (`noticeEffective`);
  - CHG-009 (decisions 1 and 3);
  - CHG-013 ("Amended by");
  - this record.
- **uncost-org/uncost-api:** `wrangler.toml` and `README.md` (#4).

## Provenance

The founder's go-live brief, part 2, 2026-11-07. Drafted by Claude Code as `uncost-admin`.

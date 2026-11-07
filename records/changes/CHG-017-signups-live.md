# CHG-017 — Sign-ups go live in production (amends CHG-009 and CHG-013)

**Status:** founder decision (2026-11-07). Drafted from the founder's go-live brief, part 2. It records the decision and the steps. **Sign-ups are live only once the production deploy with the forms on is approved**; until then nothing here changes what uncost.org serves. The steps below say which are done and which wait for the founder.

- **Date:** 2026-11-07
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

- **Database binding:** [uncost-org/uncost-api#4](https://github.com/uncost-org/uncost-api/pull/4) points the binding `DB` at `uncost-signups-live`. The Worker is to be deployed from that pull request's head before the forms-on deploy; until then it still uses `uncost-signups`. Code and `LINK_ORIGINS` (which covers `https://uncost.org`) are as on `main` (CHG-013 step 3).
- **AWS secrets removed (2026-11-07):** `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`, since Postmark sends the email (CHG-012). The Worker keeps its HMAC key, its email key and the two Postmark secrets.
- **AWS (the founder):** the IAM user `uncost-signups-worker`'s access key is deactivated, then deleted, in the AWS console. The SES identity and its DNS records stay for now.

## Production steps (the founder, in the dashboards)

1. **Cloudflare, Pages `uncost`, Production:** the Service binding `SIGNUPS` → `uncost-signups`, and the text variable `UNCOST_SIGNUPS_OPEN` = `on`. Pages applies both to new deployments only.
2. **GitHub, repository variable:** `UNCOST_FORMS_OPEN` = `on`.
3. **Cloudflare, uncost.org zone, rate limiting:** the existing `/api/contact` rule also covers `/api/signup/pledge` and `/api/signup/updates`, counted by IP, 5 requests per 10 seconds, blocking for 10 seconds. The confirm, unsubscribe, delete and webhook paths are left out (CHG-013 step 6).
4. **Postmark, Default Transactional Stream:** the webhook URL is `https://uncost.org/api/signup/postmark-events`, with the same Basic auth, and a test Bounce shows Verified (CHG-013 step 5).
5. **The preview:** on the Pages project `uncost-site-preview`, Preview environment, the `SIGNUPS` binding and `UNCOST_SIGNUPS_OPEN` are removed, so a preview test can't write to the production database. The Access application `uncost signups SNS` is deleted.

Then the founder runs the production deploy with the forms on, and approves it.

## Where the brief differs from CHG-013's checklist

- **Step 2:** a new database instead of recreating the old one (above).
- **Step 4:** the founder confirms that the Postmark account is approved before the forms-on deploy. The DPA and the private register rows are done.
- **Step 9:** the live check is sign, confirm, then delete, with a hard bounce to Postmark's test address. Unsubscribe is not in the brief.
- **Step 10:** the deploy and its date go into `docs/INFRA-DOMAINS.md` with the live check result, in a later record.

## Live check result

To be filled in after the forms-on deploy:
- the deployment;
- `/pledge/` and the footer forms;
- /privacy/ version 0.4 with its date;
- `/api/signup/pledge` answering;
- a Pledge signed, confirmed and deleted, read back from the database with no address;
- the email's images;
- a hard bounce landing as a suppression row;
- uptime and the contact form.

## Rollback

CHG-013's rollback stands:
1. Set the repository variable `UNCOST_FORMS_OPEN` to anything but `on`, or delete it.
2. On the project `uncost`, remove the `SIGNUPS` binding and `UNCOST_SIGNUPS_OPEN`.
3. Run `deploy-production` and approve it. Pages applies a binding change only to new deployments, so the redeploy is what closes the handlers.

For speed, the dashboard's rollback to the previous deployment restores the earlier pages and handlers (CHG-010).

**The data stays** in `uncost-signups-live` until it is deleted. Deletion requests are still answered with the uncost-api admin script. Pointing the Worker back at `uncost-signups` would mix production rows with test rows, so it is not part of the rollback. Record any rollback here with its date and reason.

## Private records

The founder's processor register and data inventory (CHG-006) record the production database and move the sign-up categories to live after the live check. They stay outside this repository.

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

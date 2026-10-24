# CHG-010 — Production deploys run from GitHub, after the founder's approval (amends CHG-004)

**Status:** founder decision, dated by the founder (2026-10-22). Drafted from the founder's auto-deploy brief. It takes effect when this record is merged. The Cloudflare token and the GitHub environment `production` (below) are set up before the merge, and the merge's own run is the first deploy through the workflow. Amends [CHG-004](CHG-004-public-soft-launch.md). Amended by [CHG-011](CHG-011-previews-need-approval.md), which makes preview deploys wait for approval too, because a Cloudflare Pages token can't be limited to one project.

- **Date:** 2026-10-22
- **Amends:** [CHG-004](CHG-004-public-soft-launch.md), in how its build reaches production. Since the launch the founder deployed it by hand with wrangler (`docs/INFRA-DOMAINS.md`, "Deploys").
- **Changed claim:** production deploys run through `.github/workflows/deploy-production.yml`, and each one needs the founder's approval in GitHub. A deploy by hand is the fallback only.
- **Source:** the founder's auto-deploy brief (2026-10-22). No AI decision; this file records what the founder set.

## How a deploy runs

1. **Trigger:** a push to `main` that changes anything under `website/`, or a manual run (`workflow_dispatch`). Nothing a pull request or a fork does can start it.
2. **Build** (no secrets): `npm ci`, then the build of the hand deploys, with every other switch unset and only `UNCOST_CONTACT_FORM_OPEN=on`. `scripts/audit_website.py --built dist` and `tools/prod_check.py --built dist` must pass, with the same value. `website/dist` and `website/functions` are kept as the run's artifact.
3. **Approval:** the deploy job runs in the GitHub environment `production` and waits there until the founder approves it.
4. **Deploy:** it downloads the artifact and, from `website/`, runs `wrangler pages deploy dist --project-name=uncost --branch=main`, so `./functions` ships with it. wrangler is version 4.151.3, the version of the hand deploys.
5. **After:** `scripts/uptime_check.py` checks the live site. The run's summary records the commit, the deployment ID and the previous deployment ID.

## Controls

- **Workflow:** `permissions: contents: read`; every action pinned by commit SHA; one deploy at a time (`concurrency: production-deploy`, never cancelling a run in progress).
- **Token:** a Cloudflare API token limited to Account → Cloudflare Pages → Edit on the Uncost account. It is stored with the account ID as the secrets `CF_PRODUCTION_TOKEN` and `CF_PRODUCTION_ACCOUNT_ID` of the environment `production`, not as repository secrets, so only an approved deploy job can read it. The names differ from the preview secrets, so a missing production secret cannot fall back to a repository secret.
- **Environment `production`:** the founder is the required reviewer; it accepts deployments from `main` only; administrators cannot bypass it.

## Unchanged

- **Scope:** what CHG-004 and CHG-005 authorize. No feature switch changes, and the build is the one the hand deploys made.
- **The contact Worker:** `uncost-contact-mailer` is still deployed by hand (`workers/contact-mailer/`). The workflow deploys the Pages project only and changes none of its settings: bindings, variables and Web Analytics stay as configured in Cloudflare.
- **Rollback:** Cloudflare dashboard → Workers & Pages → `uncost` → **Deployments** → the previous deployment → **Rollback**. Record it in `docs/INFRA-DOMAINS.md`.
- **Switching the contact form off** (CHG-005, "Rollback") is done by hand as before, or by a pull request that changes the workflow's build line.

## Records

Deploys through the workflow are recorded in each run's summary. `docs/INFRA-DOMAINS.md` keeps its table for the deploys made by hand. GitHub keeps this repository's run logs for 90 days; Cloudflare's deployment list is the lasting record.

## Affected surfaces

- `.github/workflows/deploy-production.yml` (new), `docs/INFRA-DOMAINS.md` ("Deploys"), `SECURITY.md` (Scope), `website/README.md` (its deploy line), and CHG-004's status line. No page or served file changes.

## Provenance

The founder's auto-deploy brief, 2026-10-22. Drafted by Claude Code as `uncost-admin`.

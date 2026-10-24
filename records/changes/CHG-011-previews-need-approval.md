# CHG-011 — Preview deploys wait for the founder's approval (amends CHG-010)

**Status:** founder decision, dated by the founder (2026-10-24). Drafted from the founder's preview-approval brief. It takes effect when this record is merged and the old preview token is revoked (below). Amends [CHG-010](CHG-010-production-deploys-from-github.md).

- **Date:** 2026-10-24
- **Amends:** [CHG-010](CHG-010-production-deploys-from-github.md), whose approval gate a second token could get round.
- **Changed claim:** a pull-request preview deploys only after the founder approves it, as a production deploy does.
- **Source:** the founder's preview-approval brief (2026-10-24). No AI decision; this file records what the founder set.

## Why

The preview project `uncost-site-preview` shares its Cloudflare account with the production project `uncost`. A Cloudflare Pages token can't be limited to one project, so the repository secret the previews used (`CF_PAGES_TOKEN`), which any same-repository pull-request workflow could read, could deploy production with no approval click. That defeats CHG-010's gate.

## What changes

- **The workflow:** `.github/workflows/preview-deploy.yml` has two jobs.
  - **`build`** reads no secrets and runs without a click: the build, the noindex posture and the content audits.
  - **`preview`** waits in the GitHub environment `preview` and then deploys the checked build.
- **The environment `preview`:** the founder (`uncost-admin`) is the required reviewer; self-review is allowed; administrators cannot bypass it. It accepts all branches, because previews run on pull-request branches.
- **The token:** a new Cloudflare token, `uncost-previews-ci`, limited to Account → Cloudflare Pages → Edit on the Uncost account, with no IP filter. It is stored with the account ID as the `preview` environment's secrets `CF_PREVIEW_TOKEN` and `CF_PREVIEW_ACCOUNT_ID`.
- **The old pair:** the names are new, so the preview job can't succeed on the old repository-level pair. After this merges, the founder deletes `CF_PAGES_TOKEN` and `CF_ACCOUNT_ID` from the repository and revokes the old token in Cloudflare.
- **Dependabot's pull requests** are built and checked but not deployed, as before: its runs get no secrets.

## Unchanged

- **The preview project:** Cloudflare Access on its previews, the noindex posture, and the `preview-contact-form` label.
- **The tests that need a Worker:** the contact form's and the sign-ups' tests keep working on previews, because the preview project's Service bindings reach Workers on its own account.
- **Production:** CHG-010's workflow, environment and token.

## Considered and not chosen

Moving previews to a separate Cloudflare account. A Service binding reaches only a Worker on the same account, so previews could no longer reach the contact or sign-ups Workers.

## What the approval does and does not cover

The preview token can still deploy production, because it is on the same account; only an approved preview job can read it. A pull request can change what its own preview job runs, since a pull request's workflow comes from that pull request. So before approving a preview, check whether the pull request changes `.github/workflows/`.

## Affected surfaces

- `.github/workflows/preview-deploy.yml`, a comment in `.github/workflows/deploy-production.yml`, `docs/INFRA-DOMAINS.md` ("Deploys"), `SECURITY.md`, and CHG-010's status line. No page or served file changes.

## Provenance

The founder's preview-approval brief, 2026-10-24. Drafted by Claude Code as `uncost-admin`.

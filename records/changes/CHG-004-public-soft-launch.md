# CHG-004 — Public soft launch of uncost.org

**Status:** DRAFT for founder decision. Nothing here is decided or in effect until the founder confirms the date below and the record is merged. Prepared from the founder's pre-launch brief (2026-10-18).

- **Date:** YYYY-MM-DD (founder to confirm)
- **Changed claim:** the publication boundary. Until now this repository authorized access-gated preview deployments only (`SECURITY.md`, 2026-07-19), and public launch was not authorized. This record would authorize a **public soft launch of uncost.org**: the static site goes public on its own domain, with everything that collects data, takes money or runs a vote still switched off.
- **Source:** the founder's authorization, to be confirmed by the founder on the date above. No AI decision; this file records the scope the founder set.
- **Rationale:** the static site is the evidence layer — sourced figures, dossiers, project briefs and draft policies — and it can be published on its own. Forms, donations, data collection and the Assembly each have their own gates (fiscal sponsorship, POL-002, POL-004, POL-006 and the reviews they require), and this record does not open any of them.

## What goes live

- The static site built from `main` (`website/`, Eleventy), served at https://uncost.org.
- It is built with **no `UNCOST_*` environment variables and no `SITE_ORIGIN`**, so every feature flag in `website/src/_data/features.js` is at its default — forms, donations, the signature counter and founding signers off; the compile-time site search on (no backend, no third-party request) — and canonical and Open Graph URLs use https://uncost.org.
- Crawling is allowed (`robots.txt` points at https://uncost.org/sitemap.xml). The unlinked placeholder pages keep `noindex` and stay out of the sitemap.

## What stays off

Not authorized by this record, and unchanged by it:

- **forms** — pledge, updates and contact (`formsOpen` stays false; no form or input renders except the site search);
- **donations** — no donate ask anywhere (`donationsOpen` stays false) until fiscal sponsorship is confirmed (POL-004);
- **the signature counter and founding signers** (`signatureCounter` and `foundingSigners` stay false);
- **pledge and data collection** — the site collects no personal data; email to contact@uncost.org is the only way in;
- **the Assembly** — no sign-up, no participation system, no vote.

No policy's draft or adoption status changes. No project budget or build is authorized. DNS and email changes beyond serving the static site, and any data system, remain outside this record.

## Rollback

Re-deploy the holding page that uncost.org served before launch. That returns the domain to its pre-launch state; record the rollback here with its date and reason.

## Affected public surfaces

- `SECURITY.md` (Scope) and `REVIEW_STATUS.md` (Meaning of publication) point here for the static-site launch and keep everything else not authorized.
- No page copy changes because of this record. The pre-launch copy fixes in the same pull request stand on their own.

## Provenance

Founder pre-launch brief, 2026-10-18: "Draft it, don't decide it." Drafted by Claude Code as `uncost-admin`. The authorization date and the decision itself are the founder's.

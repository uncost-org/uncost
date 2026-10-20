# CHG-006 — Privacy notice for the live site, and the CHG-005 records (amends CHG-005)

**Status:** founder decision, dated by the founder (2026-10-20). Drafted from the founder's compliance brief. It takes effect for the site when this record is merged and the site is next deployed. Amends [CHG-005](CHG-005-contact-form.md) (contact form) and builds the records CHG-005 lists under "Follow-ups".

- **Date:** 2026-10-20
- **Amends:** [CHG-005](CHG-005-contact-form.md), which amends [CHG-004](CHG-004-public-soft-launch.md).
- **Changed claim:** /privacy/ becomes the privacy notice for the site as it runs today, version 0.2, in effect from 20 October 2026, under the reference POL-002. Until now it described the pledge, the updates list and the Assembly as if they were running, named no one responsible for the data and carried the export's reference POL-001.
- **Source:** the founder's compliance brief (2026-10-20) and the founder's answers in that session. No AI decision; this file records what the founder set.
- **Rationale:** the site is public and the contact form is live (CHG-004, CHG-005), so the notice has to say what actually happens to data today, be complete for California (CalOPPA) and the EU and UK (GDPR Art. 13) as far as these decisions reach, and keep everything that is not open yet clearly in the future.

## Founder decisions (2026-10-20)

1. **Who is responsible.** Until a fiscal sponsor takes this on, uncost.org is operated by **Dafuq Industries LLC**, which is responsible for the personal data the notice describes. Privacy requests go to contact@uncost.org. This changes when a fiscal sponsor is confirmed, and the notice says so. No person is named. This replaces "the adopted version will name the responsible legal entity".
2. **Only what is live is described as live.** Live today: the contact form, emails sent to contact@uncost.org, Cloudflare Web Analytics and the host's security processing (including the rate limit on /api/contact). Not live, and described only under "When sign-ups open": the Pledge, the updates list, the Assembly and its anti-manipulation signals, the sign-up email provider and donations.
3. **Legal bases.**
   - The contact form: consent, given by the required checkbox (CHG-005).
   - Analytics, and security including rate limiting: legitimate interests.
   - Emails sent to contact@uncost.org directly: legitimate interests.
   - Answering a request about someone's data: legal obligation.
4. **Providers and transfers.**
   - Cloudflare, Inc. is named for hosting, the contact form's Pages Function and Worker, Email Routing (which also forwards contact@uncost.org), Web Analytics and security.
   - Google (Gmail) is named as the inbox where messages are kept.
   - The notice says data may be processed in the United States.
5. **Rights.** §8 (formerly §7) keeps the existing rights and adds two things: the right to complain to a data protection authority, and that requests are answered within one month.
6. **CalOPPA.**
   - **Do Not Track:** the site doesn't track anyone across sites, so there is nothing to switch off.
   - **Global Privacy Control:** a GPC signal is treated as an opt-out from any sale or sharing, which does not happen anyway.
   - **Changes:** they are announced by the effective date, the version table and the public change record.
   - **Effective date:** 20 October 2026, with a dated version row (0.2).
7. **Cookies.** The notice says the site sets no cookies and stores nothing in the browser, so no consent banner is needed. This was checked before it was written (see "Evidence").
8. **Policy number.** The export's POL-001 labels on /privacy/ (meta description, ref badge, §9) now read POL-002, this repository's privacy policy.
9. **Wording elsewhere.** /policies/ no longer says "Because Uncost handles donations"; it now says that when Uncost accepts donations, through a fiscal sponsor, it will handle money. Every "nonprofit" line and the conditional tax-deductible lines (/faq/, /roadmap/) stay as they are; the founder accepts them.

**One reading, flagged:** emails sent to contact@uncost.org directly are kept and deleted the same way as contact-form messages (CHG-005: kept only as long as needed to reply, deleted within 12 months of the last reply). They land in the same inbox, and CHG-005's rule is written for "contact messages".

## Evidence: no cookies, nothing stored

Recorded on 2026-10-20 by `tools/storage_check.py` (committed).

**Live site:**
- **Pages:** 8 pages of https://uncost.org opened in a fresh Chromium profile through Playwright, with every script running, including what Cloudflare injects at the edge.
- **Cookies:** no `Set-Cookie` header on any response, and no cookie in the browser.
- **Browser storage:** localStorage, sessionStorage and IndexedDB were empty.
- **Scripts:** none of the six scripts loaded uses a storage API. These were the site's own `ui.js`, `site-search.js`, `keyword-filter.js` and `show-more.js`, Cloudflare's `email-decode.min.js` and the Web Analytics `beacon.min.js` (which uses `navigator.sendBeacon` only).

**The build:** no `.js` file uses `document.cookie`, `localStorage`, `sessionStorage`, `indexedDB`, the Cache API or a service worker.

## CHG-005 follow-ups: where each went

- **Data inventory** (POL-002, "Prospective data inventory"): built. For each category it records what is collected, the purpose, the legal basis, the provider, where it is held, who can access it, retention, the deletion route, the transfer and the rights that apply. The categories are contact-form messages, direct emails, page views, security data and rights requests. It is a **private** record, kept with the processor register outside this repository, as POL-002 §6 and UNP-73 §2 require ("not published to the repo"). It holds no address or personal data.
- **Processor entries** (POL-002 Rule 6, the private processor/security register): built in the same private register. Cloudflare has one entry per service: Pages, Pages Functions, Workers, Email Routing, Web Analytics and security. Google (Gmail) has an entry for the founder inbox. Each entry records processing location (United States, as the notice says) and the transfer mechanism, which is **open** (below).
- **The legal entity named in /privacy/:** done, §1 (decision 1).
- **UNP-73** (the privacy lane's US transfer disclosure, "REQUIRED-AT-LAUNCH", blocked on founder and counsel). This change discharges, for the live site only, the disclosure that data may be processed in the United States, and the operator line. These questions are still open; they are for the founder and counsel, and none is answered here:
  1. **Transfer mechanism** for EU and UK personal data sent to Cloudflare and to Google in the US: reliance on the EU-U.S. Data Privacy Framework and/or Standard Contractual Clauses, under each provider's data processing terms. UNP-73 requires the providers' certification status and terms to be read live, with source, date and method recorded, and reviewed by counsel. GDPR Art. 13(1)(f) expects the notice to name the safeguard. Until this is settled, /privacy/ says only that data may be processed in the United States, so it is **not yet complete on this point**.
  2. **Controller wording.** UNP-73 §6 narrowed the options to a named natural person (A) or a role-only designation (D). The founder has instead named an operating company, Dafuq Industries LLC. Counsel to confirm that this company is the controller of record and that the wording in §1 is accurate and serviceable.
  3. **Applicability and representation:** whether GDPR applies under Art. 3(1) or 3(2); whether an Art. 27 EU representative (and a UK one) is needed; and whether UK-specific transfer wording is needed (UNP-73 Q-C4, Q-C5, Q-C7).
  4. **Sign-up providers.** The email provider for sign-ups (Amazon SES, us-east-1, per UNP-66) and the sign-up datastore's region are not live. Their rows in the POL-002 §6 map stay open until the forms open (UNP-63, UNP-66).
  5. **Minimum age for sign-ups.** The contact form uses 18 (CHG-005). The age for the Pledge and updates sign-ups is still a founder and counsel decision (UNP-73 CF-1).
  6. **POL-002 adoption** stays with the founder and counsel. The policy is still a public review draft; this record does not adopt it.

## Status of CHG-005

As with CHG-004, CHG-005's status line now records the founder's approval and the date the contact form went live, 2026-10-19. The founder approved it, and it was deployed with the public soft launch (`docs/INFRA-DOMAINS.md`, "Deploys").

## What this does not change

- POL-002 (`policies/POL-002-privacy-and-data-protection.md`) is not edited and is not adopted.
- No form, feature switch, provider, Cloudflare setting or deployment changes.
- The contact form's text, consent box and 12-month retention are unchanged.

## Affected public surfaces

- /privacy/: description, header, contents and body (§1–§13), and its closing call to action.
- /policies/: the opening paragraph.
- /accessibility/: the statement's date, the standard, the known issues and the contact for problems. This is the compliance pass's accessibility part, recorded here for completeness; it is not a privacy decision.

## Provenance

The founder's compliance brief, 2026-10-20, and the founder's answers in the same session: the inbox provider, the basis for direct emails and where the private registers are kept. Drafted by Claude Code as `uncost-admin`.

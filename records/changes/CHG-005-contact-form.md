# CHG-005 — Contact form at the public soft launch (amends CHG-004)

**Status:** DRAFT for founder decision, dated by the founder. Nothing here is decided by this record. It takes effect once merged, and even then the form stays off until the founder has tested delivery and set the switch (see "Turning it on").

- **Date:** 2026-10-19
- **Amends:** [CHG-004](CHG-004-public-soft-launch.md) (public soft launch, 2026-10-19). CHG-004 kept every form off. This record turns on **the contact form only**.
- **Changed claim:** the /contact/ form may be live at the public soft launch. It asks for a name (optional), an email address, a phone number (optional) and a message, and sends them by email to the founder inbox behind contact@uncost.org. Nothing is stored on the site.
- **Source:** the founder's contact-form brief (2026-10-19). No AI decision; this file records the scope the founder set.
- **Rationale:** a working way to reach a person at launch, without opening the pledge or updates sign-ups, which keep their own gates (UNP-57, POL-002).

## What it turns on

- **Its own switch.** `features.contactFormOpen` (`UNCOST_CONTACT_FORM_OPEN=on` at build time) renders the form on /contact/ and nowhere else, plus two noindex pages for posts made without JavaScript, /contact/sent/ and /contact/not-sent/. `formsOpen`, which opens the pledge and updates forms, stays off.
- **First-party delivery, nothing stored.** The form posts to the same-origin `/api/contact` (`website/functions/api/contact.js`, a Cloudflare Pages Function). The handler checks the fields server-side (email and message required; length limits; email format; a hidden honeypot) and rejects a failed check quietly. It then hands the message, through a Service binding, to the `uncost-contact-mailer` Worker (`workers/contact-mailer/`). The Worker sends it with Cloudflare Email Routing's send binding to the founder inbox, a verified destination address. From is `contact@uncost.org`, and the visitor's address is Reply-To, never From. No form vendor, no third-party script, no database, and no copy kept or logged on our side.
- **Dark unless switched on.** The handler answers 404 unless the Pages project's environment sets `UNCOST_CONTACT_FORM_OPEN` to `on` and carries the `CONTACT_MAILER` binding.
- **Privacy notice.** /privacy/ §2 says what the form collects, that it is used only to reply, that it is not stored on the site, and that it is kept in the founder inbox.

## What stays off

Unchanged by this record: the **pledge** and **updates** forms (`formsOpen`); **donations**; the **signature counter** and **founding signers**; the **Assembly**. No policy's draft or adoption status changes.

## Turning it on

The founder confirms each of these before setting the switch on production:

1. The Worker is deployed, with its `CONTACT_TO` secret set to the founder inbox.
2. The Pages project carries the `CONTACT_MAILER` Service binding and the `UNCOST_CONTACT_FORM_OPEN=on` variable.
3. The rate-limiting rule on `/api/contact` is in place.
4. A test message sent from a preview built with the switch on has arrived in the founder inbox, with the visitor as Reply-To.

The open policy points are listed in the pull request that adds this record. They include UNP-57's "no phone on any form", its three consent purposes, its retention schedule and its backend-repository requirement, and POL-002's pre-collection requirements. They are for the founder to settle; this record does not settle them.

## Rollback

Rebuild without `UNCOST_CONTACT_FORM_OPEN` and redeploy:

```
cd website && rm -rf dist && npm ci && npm run build
python3 ../scripts/audit_website.py --built dist
npx wrangler pages deploy dist --project-name=<production-project>
```

That removes the form and its two pages. To close the handler at once, without a rebuild, set the Pages variable `UNCOST_CONTACT_FORM_OPEN` to anything but `on` (or remove it); `/api/contact` then answers 404. Record the rollback here with its date and reason.

## Affected public surfaces

- /contact/ (the form, when on); /contact/sent/ and /contact/not-sent/ (noindex, only when on); /privacy/ §2.
- `SECURITY.md` (Scope) and `REVIEW_STATUS.md` (Meaning of publication) point here for the contact form.

## Provenance

Founder contact-form brief, 2026-10-19: "Draft it, don't decide it", with the date set by the founder. Drafted by Claude Code as `uncost-admin`.

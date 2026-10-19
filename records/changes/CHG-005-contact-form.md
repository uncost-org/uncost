# CHG-005 — Contact form at the public soft launch (amends CHG-004)

**Status:** DRAFT for founder decision, dated by the founder. Nothing here is decided by this record. It takes effect once merged, and even then the form stays off until the founder has tested delivery and set the switch (see "Turning it on").

- **Date:** 2026-10-19
- **Amends:** [CHG-004](CHG-004-public-soft-launch.md) (public soft launch, 2026-10-19). CHG-004 kept every form off. This record turns on **the contact form only**.
- **Changed claim:** the /contact/ form may be live at the public soft launch. It asks for a name (optional), an email address and a message, plus one required, unticked consent box, and sends them by email to the founder inbox behind contact@uncost.org. Nothing is stored on the site. Messages are kept in that inbox only as long as needed to reply and deleted within 12 months of the last reply.
- **Source:** the founder's contact-form brief (2026-10-19). No AI decision; this file records the scope the founder set.
- **Rationale:** a working way to reach a person at launch, without opening the pledge or updates sign-ups, which keep their own gates (UNP-57, POL-002).

## What it turns on

- **Its own switch.** `features.contactFormOpen` (`UNCOST_CONTACT_FORM_OPEN=on` at build time) renders the form on /contact/ and nowhere else, plus two noindex pages for posts made without JavaScript, /contact/sent/ and /contact/not-sent/. `formsOpen`, which opens the pledge and updates forms, stays off.
- **First-party delivery, nothing stored.** The form posts to the same-origin `/api/contact` (`website/functions/api/contact.js`, a Cloudflare Pages Function). The handler checks the fields server-side (email, message and the consent box required; length limits; email format; a hidden honeypot) and rejects a failed check quietly. It then hands the message, through a Service binding, to the `uncost-contact-mailer` Worker (`workers/contact-mailer/`). The Worker sends it with Cloudflare Email Routing's send binding to the founder inbox, a verified destination address. From is `contact@uncost.org`, and the visitor's address is Reply-To, never From. No form vendor, no third-party script, no database, and no copy kept or logged on our side.
- **Dark unless switched on.** The handler answers 404 unless the Pages project's environment sets `UNCOST_CONTACT_FORM_OPEN` to `on` and carries the `CONTACT_MAILER` binding.
- **Privacy notice.** /privacy/ §2 says what the form collects (name, optional; email; message; the age confirmation), that it is used only to reply, that it is not stored on the site, and that it is kept in the founder inbox only as long as needed to reply and deleted within 12 months of the last reply.
- **Consent box.** One required, unticked checkbox before the send button: "I’m 18 or older, and I agree that Uncost may use my name, email address and message only to reply to this message." It is a native checkbox with a real `<label>`, so the browser blocks and announces an unticked send. It is checked again on the server, where an unticked box is a quiet failure. Each email to the founder inbox quotes the box's text and the retention rule.

## What stays off

Unchanged by this record: the **pledge** and **updates** forms (`formsOpen`); **donations**; the **signature counter** and **founding signers**; the **Assembly**. No policy's draft or adoption status changes.

## Turning it on

The founder confirms each of these before setting the switch on production:

1. The Worker is deployed, with its `CONTACT_TO` secret set to the founder inbox.
2. The Pages project carries the `CONTACT_MAILER` Service binding and the `UNCOST_CONTACT_FORM_OPEN=on` variable.
3. The rate-limiting rule on `/api/contact` is in place.
4. A test message sent from a preview built with the switch on has arrived in the founder inbox, with the visitor as Reply-To and the consent line quoted.

## Founder decisions (2026-10-19)

On the policy conflicts listed in the pull request:

1. **No phone field.** UNP-57 §4A excludes phone from every form, and a reply by email does not need one. It is removed from the form, the handler, the Worker and /privacy/.
2. **Retention: 12 months.** Contact messages are kept in the founder inbox only as long as needed to reply, and deleted within 12 months of the last reply. This is the purpose-tied retention rule that POL-002 Rule 5 requires for this category.
3. **Consent and age: one required checkbox.** It is unticked and states the one purpose (a reply to this message only) and the minimum age, **18**. The founder first set 16 and raised it to 18 before launch (2026-10-19). POL-002 names no minimum age (Rule 1 requires only "reviewed age/guardian handling"). 18 is UNP-57 §4.1 Option B, the packet's recommended default, which "avoids minor data entirely (no POL-008 exposure)"; §4.1 still expects legal review to confirm the threshold. The box is checked on the server as well.
4. **Backend in this repository: accepted for the soft launch.** The founder accepts the handler (`website/functions/api/contact.js`) and the Worker (`workers/contact-mailer/`) living in this repository for the soft launch, as an exception to UNP-57 SC2 ("Backend has no code home; S1 needs a designated separate repository first"). To be revisited when any data system is built.
5. **Analytics: accepted.** The founder treats Cloudflare Web Analytics, provided by the site's host, as acceptable under UNP-57 §3 item 8 ("no cookies, no consent banner, no third-party analytics") for the soft launch, within the cookieless, no-profile limits that /privacy/ states.

## Not built: UNP-57 asks for more than a no-storage contact form can do

- **A consent-event ledger.** §4 asks each consent control to record the "presented-text hash + policy version at submission (append-only consent event)". That needs storage, and this form stores nothing by design. Each email to the founder inbox quotes the consent box's exact text instead, which is a record kept with the message, not a ledger.
- **The at-collection transfer disclosure (§3.5).** This is the notice, on each form, that data may pass to a fiscal sponsor or successor controller. Its wording depends on the controller identity (§3.1), which is still open, so it is not added.
- **Withdrawal links in receipt emails (§4).** The form sends the visitor no email. Withdrawal and deletion work by email to contact@uncost.org (/privacy/ §7 and §10).

## Follow-ups

Tracked here, not built:

- **Private data inventory** (POL-002, "Prospective data inventory"): a row for contact messages, covering category, purpose, basis, vendor, storage region, access, retention (12 months), deletion route, transfer and rights.
- **Processor entries** (POL-002 Rule 6, private processor/security register): Cloudflare (Pages, Pages Functions, Workers, Email Routing, Web Analytics) and the provider of the founder inbox.
- **The legal entity named in /privacy/.** §1 still says the adopted version will name the responsible legal entity (UNP-57 §3.1 controller identity, open).
- **UNP-73**, the privacy lane's US transfer disclosure, marked "REQUIRED-AT-LAUNCH" (currently blocked).

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

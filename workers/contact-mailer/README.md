# uncost-contact-mailer

Emails one /contact/ message to the founder inbox. The authorization record is
[CHG-005](../../records/changes/CHG-005-contact-form.md).

```
browser ──POST /api/contact──▶ Pages Function (website/functions/api/contact.js)
                                 validates; no storage
                                 │ Service binding CONTACT_MAILER
                                 ▼
                               this Worker ──send_email (SEND_EMAIL)──▶ founder inbox
                                                                        (verified destination)
```

- **Why a Worker.** Pages Functions have no `send_email` binding; Workers do. A
  Pages Function can call a Worker through a Service binding.
- **Cost.** Email Routing sends to *verified destination addresses* free on every
  plan, with only Email Routing configured.
- **Sender.** From is `contact@uncost.org`, an address on the routing domain;
  Email Routing sends only from routing domains. The visitor's address is
  Reply-To, never From.
- **Recipient.** `CONTACT_TO` is a secret, so no personal address is in this
  repository.
- **No public URL.** `workers_dev` and `preview_urls` are off, so the Worker
  answers only through the binding.
- **Nothing stored.** It does not store or log messages.

## Deploy (by hand; nothing in CI deploys it)

```
cd workers/contact-mailer
npx wrangler deploy
npx wrangler secret put CONTACT_TO   # the founder inbox: a verified Email Routing destination
```

Then give the Pages projects:
- the Service binding `CONTACT_MAILER` → `uncost-contact-mailer`;
- the variable `UNCOST_CONTACT_FORM_OPEN=on`.

Without both, `/api/contact` answers 404.

The Pages Function ships with every Pages deploy run **from `website/`**:
`npx wrangler pages deploy dist` reads `./functions` relative to the working
directory.

## Test

`python3 tools/contact_form_check.py --unit-only` runs the handler and this
Worker against mocks. With `--built DIR` (a build made with
`UNCOST_CONTACT_FORM_OPEN=on`) it also drives the form in a browser.

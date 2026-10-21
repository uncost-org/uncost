# Domain and DNS policy — uncost.org

Updated: 2026-08-02

Authoritative policy for how the `uncost.org` domain and its subdomains are used,
plus a dated log of every DNS change. This is documentation and policy only;
publishing or changing any DNS record is a separate, founder-gated action — when
one happens, record it in the change log at the foot of this file with its date.

The detailed, ready-to-apply email records live in
[`docs/EMAIL_DNS.md`](EMAIL_DNS.md); this file is the higher-level domain policy
and supersedes the parts of that document listed under
[Relationship to EMAIL_DNS.md](#relationship-to-email_dnsmd).

## One name, one job

| Name | Role | Sends mail? | Status |
|---|---|---|---|
| **`uncost.org`** (apex) | The website and **all** content routes; also the inbound human mailbox (`contact@`). | Inbound only (Cloudflare Email Routing). Never bulk. | Live |
| **`mail.uncost.org`** | Amazon SES **custom MAIL FROM** for **transactional** mail only (pledge/verification/receipts/withdrawal links). | Transactional only. | Exists — SES, `us-east-1`, Easy DKIM |
| `news.uncost.org` *(or `marketing.`)* | Bulk email — the newsletter / email-updates stream. Its **own** SPF/DKIM. | Bulk only. | **RESERVED** — create only when the system exists |
| `api.uncost.org` | Application/API endpoint. | No | **RESERVED** — create only when the system exists |
| `docs.uncost.org` | Documentation site. | No | **RESERVED** — create only when the system exists |
| `status.uncost.org` | Status page. | No | **RESERVED** — create only when the system exists |
| `join.uncost.org` | Optional future **vanity redirect** to `/pledge`. | No | Optional / future |

**RESERVED means: do not create the DNS record until the system it serves
actually exists.** A subdomain that resolves to nothing (or a parked page) is an
attack surface and a support liability.

## The apex holds all content — content is never split onto subdomains

Every content route is served from `uncost.org` itself, e.g.:

`/case` · `/projects` · `/assembly` · `/treasury` · `/reports` · `/receipts` ·
`/sectors/` · `/roadmap` · `/movement` · `/pledge` · `/news` · `/contribute` · …

Content is **never** moved to a subdomain (no `case.uncost.org`,
`docs.uncost.org`-for-content, etc.). Subdomains are for *systems* (mail, API,
status), not for pages. The only content-adjacent subdomain permitted is a
future `join.` **redirect** to `/pledge`, which serves no content of its own.

## Mail posture

- **Inbound (`contact@uncost.org`)** — Cloudflare Email Routing to the founder
  inbox. Working since 2026-07-21.
- **Transactional (`mail.uncost.org`)** — Amazon SES custom MAIL FROM in
  `us-east-1` with **Easy DKIM**. Transactional mail only.
- **Bulk / marketing** — must send from its own reserved subdomain
  (`news.`/`marketing.`) with its **own** SPF and DKIM. **Bulk mail is never
  sent from the apex, and never from the transactional identity** — a complaint
  spike on the newsletter must not be able to damage verification-mail
  deliverability.

### DMARC — one record, at the apex

There is **one DMARC record, at the apex** (`_dmarc.uncost.org`),
**Cloudflare-managed** (Cloudflare DMARC Management owns the single `_dmarc` TXT
and receives the aggregate reports). Do **not** hand-publish a second `_dmarc`
record — only one `_dmarc` TXT per name is valid.

- **Today: `p=none`** (monitoring). Hold here.
- **Tighten to `p=quarantine` then `p=reject` only after SES sending is stable**
  and the aggregate (`rua`) reports show no legitimate mail failing alignment.
  This is a founder decision and must not run ahead of live, aligned SES sending.

## Relationship to EMAIL_DNS.md

`docs/EMAIL_DNS.md` (2026-07-21) predates SES selection and is **superseded in
part** by this policy:

- **Transactional identity:** EMAIL_DNS.md plans `t.uncost.org`; the live
  transactional identity is **`mail.uncost.org`** (SES custom MAIL FROM). Treat
  `mail.` as the transactional name.
- **ESP:** EMAIL_DNS.md leaves the ESP unselected (`<...>` tokens). The ESP is
  **Amazon SES** (`us-east-1`, Easy DKIM).
- **DMARC:** EMAIL_DNS.md targets **per-subdomain** `_dmarc.t` / `_dmarc.news` at
  `p=reject`; current policy is **one apex DMARC** (`sp=` governs subdomains),
  held at `p=none` until SES sending is stable.
- **Unchanged and still governing:** the apex inbound routing, root SPF (`~all`)
  and DKIM via Cloudflare Email Routing, the transactional/marketing separation
  principle, disabling ESP open/click tracking (POL-002), and the launch
  sequencing / warm-up lead time.

The exact SES records (MAIL FROM MX + SPF TXT, Easy DKIM CNAMEs) should be
captured in EMAIL_DNS.md when published; this file records that the change
happened and when.

## DNS change log

Record every DNS change here: date, name/record, what changed, and who/why.
Entries newest first.

| Date | Name / record | Change | Notes |
|---|---|---|---|
| 2026-08-02 | — | This policy documented; `mail.uncost.org` SES transactional identity recorded as existing. | Baseline. Exact SES-record creation dates predate this doc and are to be confirmed against the SES console / Cloudflare DNS history. |
| ≤2026-08-02 | `mail.uncost.org` | Amazon SES custom MAIL FROM established (`us-east-1`, Easy DKIM); transactional identity. | Exists per founder; exact date to confirm. |
| 2026-07-21 | `_dmarc.uncost.org` (TXT) | Cloudflare DMARC Management enabled, `p=none`, aggregate reports to dashboard. | Founder action. |
| 2026-07-21 | apex SPF / DKIM | Cloudflare Email Routing added apex SPF (`~all`) and DKIM; `contact@` inbound routing live. | Founder action. |
| ≤2026-08-02 | apex (`uncost.org`) | Apex serves the website via Cloudflare Pages; `www.uncost.org` 301-redirects to the apex. | Exact date to confirm against Cloudflare. |

## Deploys

Production is the Cloudflare Pages project `uncost` (production branch `main`). It is Git-disconnected and deployed by hand from `website/`: `npx wrangler pages deploy dist --project-name=uncost --branch=main`. Running from `website/` makes `website/functions/` ship with it. Entries newest first.

| Date | Commit | Deployment ID | Previous deployment ID | What |
|---|---|---|---|---|
| 2026-10-21 15:06 UTC (22:06 ICT) | `497bb3d` | `04781a12-b381-44c7-920a-e2bb61a0f1a4` | `caadb648-9f90-40ae-8e7e-81abeb93b6e4` (the 2026-10-20 15:30 UTC deploy, recorded in #88) | `main` with #87 (npm audit fix, icon and PDF licences) and #89 (sharp favicon from a vector redraw of the robot's head). Built the same way as the launch, with only `UNCOST_CONTACT_FORM_OPEN=on`; `audit_website.py` and `prod_check.py` passed on the build. `website/functions/` and `workers/` are unchanged, so the contact Worker was not redeployed. |
| 2026-10-20 15:30 UTC (22:30 ICT) | `4185bd0` | `caadb648-9f90-40ae-8e7e-81abeb93b6e4` | `640ce5ee-763f-4611-9247-5fb085a8cafa` (the 14:19 UTC deploy) | `main` with #85 (the previous deploy's record) and #87 (maintenance: npm audit fix and Eleventy 3.1.7; licences for the interface icons and the PDF). Built the same way, with only `UNCOST_CONTACT_FORM_OPEN=on`; `audit_website.py` and `prod_check.py` passed on the build. Wrangler uploaded no new files: #87 changed only the build tools' lockfile and licence records, so the served files match the previous deployment. Live: titles, `/favicon.ico` and `/.well-known/security.txt` 200, the contact form shown, a POST without consent answered `{"ok":false}`; the uptime workflow (run 39449141196) passed all six checks. `website/functions/` and `workers/` are unchanged, so the contact Worker was not redeployed. |
| 2026-10-20 14:19 UTC (21:19 ICT) | `0735d1b` | `640ce5ee-763f-4611-9247-5fb085a8cafa` | `28a08eb0-c0a9-4444-859d-054b6f445bb2` (the 12:30 UTC deploy) | `main` with #83 (the previous deploy's record) and #84 (rights follow-up: artwork licence, font and icon sources, the PDF without a personal name in its metadata, /privacy/ 0.3 naming the Data Privacy Framework safeguard). Built the same way, with only `UNCOST_CONTACT_FORM_OPEN=on`; `audit_website.py` and `prod_check.py` passed on the build. Live: titles, `/favicon.ico` and `/.well-known/security.txt` 200, the contact form shown, a POST without consent answered `{"ok":false}`, the PDF at its new pin; the uptime workflow (run 39438263491) passed all six checks. `website/functions/` and `workers/` are unchanged since `fc656f9`, so the contact Worker was not redeployed. |
| 2026-10-20 12:30 UTC (19:30 ICT) | `fc47e83` | `28a08eb0-c0a9-4444-859d-054b6f445bb2` | `eaa96b34-1461-48b2-86f1-94f6cd915065` (the launch deploy) | `main` with #81 (page titles, preview aliases, security.txt, report-only checks) and #82 (compliance pass: privacy notice, records, accessibility, rights, uptime, favicon). Built the same way as the launch, with only `UNCOST_CONTACT_FORM_OPEN=on`; `audit_website.py` and `prod_check.py` passed on the build. `website/functions/` and `workers/` are unchanged since `fc656f9`, so the contact Worker was not redeployed. |
| 2026-10-19 23:54 UTC (2026-10-20 06:54 ICT) | `fc656f9` | `eaa96b34-1461-48b2-86f1-94f6cd915065` | `dd7bbe15-4535-451e-bb6c-1c50a45a4bc2` (the "coming soon" page) | Public soft launch under [CHG-004](../records/changes/CHG-004-public-soft-launch.md) and [CHG-005](../records/changes/CHG-005-contact-form.md). Built with only `UNCOST_CONTACT_FORM_OPEN=on`, with Cloudflare Web Analytics enabled. The contact Worker is `uncost-contact-mailer`, version `a7678af1-908b-4164-8ecd-45af81f957b3`. |

**Rollback:** in the Cloudflare dashboard, Workers & Pages → `uncost` → **Deployments** → the previous deployment → **Rollback**. Record any rollback here.

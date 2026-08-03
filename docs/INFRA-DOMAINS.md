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

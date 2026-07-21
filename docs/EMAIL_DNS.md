# Email sending DNS records — documentation only

**Apply nothing from this file.** These are the exact DNS records to publish
later, gated on vendor selection and an explicit founder DNS action. Publishing
any DNS record is out of scope for this repository. This document is the
repo-tracked companion to the governing plan in the Launch Operations &
Infrastructure Readiness Packet (UNP-60 §1); where they differ, the packet
controls. Provider-specific values appear as `<...>` tokens because they are
issued by the mailbox provider and the ESP, and the ESP is not yet selected.

## Subdomain model (why three names)

| Name | Role | Sends |
|---|---|---|
| `uncost.org` (root) | Human mailbox only | People reading and replying; never bulk mail. Must be spoof-proof even though it does not send bulk. |
| `t.uncost.org` | Transactional | Pledge verification, newsletter double-opt-in confirmation, receipts, deletion/withdrawal links. |
| `news.uncost.org` | Marketing | The newsletter / email-updates stream only. |

Separating transactional from marketing means a complaint spike on the
newsletter can never damage the deliverability of verification mail (the
funnel). Each subdomain has its own SPF, DKIM, and DMARC.

## Root domain — live now via Cloudflare (2026-07-21)

The root `uncost.org` mail posture is **active**, managed by Cloudflare, and does
**not** depend on the ESP. It was enabled by the founder on 2026-07-21:

| Control | Observed state | Notes |
|---|---|---|
| DMARC | **`p=none` (monitoring), active** | Cloudflare **DMARC Management** owns the single `_dmarc` TXT record and receives the aggregate reports to a dashboard. Do **not** hand-publish a second `_dmarc` record — only one `_dmarc` TXT per domain is valid; a manual record would break Cloudflare's. There is no `dmarc@uncost.org` mailbox. First reports expected within 24h. |
| SPF | **soft fail (`~all`)**, auto-added | Added by Cloudflare Email Routing. |
| DKIM | **in use**, via Email Routing | |
| `contact@uncost.org` | **working** | Routes through Cloudflare Email Routing to the founder inbox. |
| BIMI | not in use, not applicable | Needs a VMC and a registered trademark. |

**Policy progression is a founder decision and must not run ahead of the ESP.**
Advancing DMARC to `p=quarantine` then `p=reject` stays the founder's call and
**must not happen before the ESP is live and alignment data exists** — Cloudflare
will keep prompting to strengthen the policy, but tightening before the sending
subdomains are authenticated and producing clean alignment reports would risk
failing our own legitimate mail. Hold at `p=none` until the sending-subdomain
records below are live and their `rua` reports are clean.

## Sending-subdomain records — target state (later, gated on ESP)

These remain unpublished, waiting on ESP selection. They are unchanged.

### Root `uncost.org` — sending authorization (only if/when root ever sends bulk)

| Host | Type | Value | Purpose |
|---|---|---|---|
| `@` | `TXT` (SPF) | `v=spf1 include:<mailbox-provider-spf> -all` | Authorize only the human mailbox provider. Cloudflare Email Routing manages the current root SPF (`~all`); replace only if the root's sending posture changes. |
| `<sel>._domainkey` | `TXT` or `CNAME` | `<mailbox-provider-dkim>` | DKIM-sign human replies (Email Routing currently provides DKIM). |

### Transactional `t.uncost.org`

| Host | Type | Value | Purpose |
|---|---|---|---|
| `t` | `TXT` (SPF) | `v=spf1 include:<esp-transactional-spf> -all` | Authorize ESP transactional sending. |
| `<esp-selector>._domainkey.t` | `CNAME` or `TXT` | `<esp-transactional-dkim>` | DKIM. |
| `<esp-bounce-label>.t` | `CNAME` | `<esp-returnpath-target>` | Custom Return-Path / bounce domain for SPF alignment. |
| `_dmarc.t` | `TXT` | `v=DMARC1; p=reject; rua=mailto:dmarc@t.uncost.org; adkim=s; aspf=s; pct=100` | Strict from day one — new subdomain, no legacy mail. |

### Marketing `news.uncost.org`

Identical pattern to `t.` with `<esp-marketing-*>` tokens, and `_dmarc.news` at
`p=reject`.

## Alignment and privacy

- DMARC passes if SPF **or** DKIM aligns. Primary reliance is DKIM alignment
  (`d=` equals the sending subdomain; survives forwarding); SPF alignment is
  secondary via the custom Return-Path. Because the `From:` is exactly the
  subdomain, alignment holds under both relaxed and strict — use **strict on
  the subdomains** (they only ever send our mail) and **relaxed on the root**.
- Privacy hardening (POL-002 / zero-tracking): disable ESP open/click tracking.

## Sequencing (this is the launch critical path)

Per the packet, DNS and deliverability need **~30–60 days of lead time** and are
the earliest thing to start — before the site is even publicly live. The site
can launch with forms disabled ("Sign-ups open soon") while this warm-up runs;
live form submission stays blocked on it plus vendor selection, the privacy
notice, and counsel items.

- **L−60 → L−45:** **root DMARC `p=none` is done** (Cloudflare DMARC Management,
  active 2026-07-21, collecting `rua` to a dashboard — see the root-domain
  section above). Publish the sending-subdomain records once the ESP is selected;
  subdomains start at `p=reject`. Enroll Google Postmaster Tools, Microsoft
  SNDS + JMRP for `t.` and `news.`.
- **L−45 → L−30:** low-volume seed tests from `t.` to founder-controlled inboxes
  across Gmail/Outlook/Yahoo/Apple/Proton; verify DKIM=pass, SPF=pass,
  DMARC=pass, and inbox (not spam) placement.
- **L−30 → L−14:** gentle real ramp; confirm `rua` shows no legitimate mail
  failing root DMARC.
- **L−14 → L−7:** root DMARC `p=none → p=quarantine`, then `→ p=reject` once
  reports stay clean — **founder decision, and not before the ESP is live and
  alignment data exists** (tightening early would risk our own mail).

## What is not authorized here

Publishing any record, selecting or signing any ESP or mailbox vendor, and
sending any mail. Each is a separate gated action. This file only records the
exact records so they can be applied quickly when the founder opens those gates.

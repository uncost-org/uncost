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

## Records to publish (later, gated)

### Root `uncost.org` — spoof-proof, does not send bulk

| Host | Type | Value | Purpose |
|---|---|---|---|
| `@` | `TXT` (SPF) | `v=spf1 include:<mailbox-provider-spf> -all` | Authorize only the human mailbox provider. If `contact@` is forward-only and never sends, use `v=spf1 -all`. |
| `<sel>._domainkey` | `TXT` or `CNAME` | `<mailbox-provider-dkim>` | DKIM-sign human replies. |
| `_dmarc` | `TXT` | `v=DMARC1; p=none; rua=mailto:dmarc@t.uncost.org; fo=1; adkim=r; aspf=r; pct=100` | Anti-spoof plus aggregate reports. Progress to `p=quarantine` then `p=reject` once reports are clean. |

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

- **L−60 → L−45:** publish all records. Root DMARC `p=none`; subdomains
  `p=reject`. Start collecting `rua`. Enroll Google Postmaster Tools, Microsoft
  SNDS + JMRP for `t.` and `news.`.
- **L−45 → L−30:** low-volume seed tests from `t.` to founder-controlled inboxes
  across Gmail/Outlook/Yahoo/Apple/Proton; verify DKIM=pass, SPF=pass,
  DMARC=pass, and inbox (not spam) placement.
- **L−30 → L−14:** gentle real ramp; confirm `rua` shows no legitimate mail
  failing root DMARC.
- **L−14 → L−7:** root DMARC `p=none → p=quarantine`, then `→ p=reject` once
  reports stay clean.

## What is not authorized here

Publishing any record, selecting or signing any ESP or mailbox vendor, and
sending any mail. Each is a separate gated action. This file only records the
exact records so they can be applied quickly when the founder opens those gates.

# Uncost design constraints (for Claude Design and any design source)

Paste this whole document at the start of every Claude Design session. It exists
because the design tool does not know Uncost's constraints, so each finished
export tends to regress them — the 2026-07-22 import alone re-surfaced three
(coral contrast, banned glyphs, dark theme). Every constraint below is
**enforced in the repository**; the citation for each is the artifact that
enforces it, so this document and CI cannot drift apart. Where a constraint is
enforced only by an audit constant with no separate human-readable statement,
that is called out.

> **This document must be updated whenever a new constraint is discovered.**
> The next import will find more. Add the constraint here with its enforcing
> citation in the same pull request that fixes it.

## Colour and contrast

1. **Bright coral (`#D64A1E`) is for decoration and large display only.** Normal-size
   text, links, and small pills must use **deep coral (`#B23A14`) with cream** to
   meet contrast. Bright coral on cream is only 4.04, and ink-on-bright-coral is
   4.47 — both below AA.
   *Enforced:* `website/design-system/AUTHORITY.md` (human-readable rule) and the
   auto-discovery contrast check in `scripts/audit_design_handoff.py`
   (`validate_contrast_matrix`).
2. **Every full-bleed block surface and every pill must meet WCAG 2.2 AA** — 4.5:1
   for text, 3.0:1 for focus rings / non-text UI. The audit auto-discovers every
   surface and pill in the CSS and checks each; there is no exemption list.
   *Enforced:* `scripts/audit_design_handoff.py` constants `CONTRAST_MIN_TEXT` /
   `CONTRAST_MIN_FOCUS`. *Note:* the precise per-pair thresholds live only in this
   audit constant — there is no separate prose specification beyond this document.
3. **Light theme only.** Do not ship a dark theme (no `prefers-color-scheme: dark`,
   no `[data-theme="dark"]` inversion). A dark theme requires its own contrast audit
   before it can ship.
   *Enforced:* `website/design-system/AUTHORITY.md` (deliberate deviation) and by
   absence in `website/design-system/tokens.css` (the audit checks contrast on the
   shipped light tokens only).

## Iconography

4. **No `vote` or `money`/`dollar` glyph in the icon set.** This is a content-safety
   omission, not an oversight.
   *Enforced:* `website/design-system/EXCLUSIONS.md` (human-readable) and the
   banned-symbol check in `scripts/audit_design_handoff.py` (rejects any `<symbol>`
   id containing `vote` or `dollar`).

## Assets, fonts, and network

5. **Self-hosted fonts and zero third-party runtime requests.** No CDN, no Google
   Fonts, no external scripts, styles, images, or fetches. Fonts are vendored WOFF2
   with OFL receipts.
   *Enforced:* `scripts/audit_design_handoff.py` (no `https?://` in the packet CSS,
   no `fonts.googleapis.com`) and `scripts/audit_site_quality.py` (zero third-party
   fetched resources in built output).
6. **Images come only from the approved brand manifest.** Paths, hashes, and alt
   text are authoritative in `website/assets/brand/ASSET_MANIFEST.json`; build-time
   derivatives are never committed.
   *Enforced:* `website/design-system/AUTHORITY.md` and the manifest checks in
   `scripts/audit_design_handoff.py` (exact asset count + critical hashes).

## Content and structure

7. **The fifteen sectors are in fixed order and never reordered:** Food, Water,
   Shelter, Energy, Healthcare, Care, Education, Transportation, Clothing, Goods,
   Materials, Communication, Safety, Environment, Leisure.
   *Enforced:* `website/src/_data/catalog.js` (the build fails on any reorder) and
   recorded durably in `docs/CONTROL.md` (DEF-05).
8. **Status labels render honest text; never a bare `Live`/`Funded`/`Passed`/`Approved`/`Operating`
   badge.** Status *class* names may exist (for example `.status--live`), but the
   rendered text must be honest — `.status--live` renders "Designed — opens at
   launch", not "Live". The ban is on rendered badge text, not class names.
   *Enforced:* the badge rule in `scripts/audit_website.py` (`status-badge-bare`,
   which matches rendered text) and `website/design-system/AUTHORITY.md`.
9. **Never invent a figure, count, date, name, or handle.** Any dollar amount,
   percentage, or large count must carry a source citation; anything unsourced stays
   a visible `[CONTENT NEEDED]` / `[PLACEHOLDER]` marker.
   *Enforced:* the flag-for-review figure rules in `scripts/audit_website.py`
   (warning tier + review queue) and the repository `CLAUDE.md` boundaries.

## How this list was built

Derived from the artifacts that already enforce these rules — `AUTHORITY.md`,
`EXCLUSIONS.md`, `docs/CONTROL.md`, `catalog.js`, and the two audit scripts —
rather than hand-written in parallel, so a rule here always corresponds to
something CI checks. If you add a constraint that has no enforcement yet, say so
explicitly and open a follow-up to add the check; an unenforced rule in this
document is a request, not a guarantee.

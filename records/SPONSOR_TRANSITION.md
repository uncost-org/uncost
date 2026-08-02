# Sponsor / incorporation transition map

When Uncost confirms a **fiscal sponsor**, **incorporates**, or gets **counsel**
sign-off, a set of public statements and repository documents go out of date in
the same moment. This is the checklist of every such statement, so none is
missed. Update the statement, then tick it here.

Line numbers are **verified against `main` at commit `eab9565` (2026-08-02)**;
the exact wording is quoted so each entry stays findable if lines drift.

> ⚠️ **This map reflects current `main`, which does NOT yet include PR #45**
> (narrative copy pass 2). PR #45 rewrites The Movement, The Case, The Projects,
> The Assembly, Roadmap, and Contribute — which moves several of the entries
> below and adds its own `SPONSOR-GATED` / `INCORPORATION-GATED` markers to those
> pages. See "Pending: PR #45" at the foot of this file. When #45 merges, refresh
> the affected rows.

## Triggers

- **SPONSOR** — a fiscal sponsor is confirmed. Donations can open, The Treasury
  activates, and every "seeking fiscal sponsorship" / "cannot accept donations"
  / "coming soon" / "no donate button" statement changes.
- **COUNSEL** — legal counsel confirms wording. The data-controller identity,
  the minimum-age threshold, and any **tax-deductibility** claim are provisional
  until counsel signs off (tax-deductibility also depends on the sponsor's own
  501(c)(3) and receipt guidance — do not assert it before both).
- **INCORPORATION** — Uncost incorporates as its own legal entity. Every "not
  incorporated" / "no legal structure yet" statement changes, and the data
  controller becomes the entity rather than the founder.

A statement can carry more than one trigger (e.g. "not incorporated so cannot
accept donations" is **INCORPORATION + SPONSOR**).

## Marker convention (template comments)

In `.njk` templates, flag a gated statement with a whitespace-trimming Nunjucks
comment immediately above it:

```njk
{#- SPONSOR-GATED: donations open only when a fiscal sponsor is confirmed. -#}
{#- INCORPORATION-GATED · COUNSEL-GATED: controller identity is provisional. -#}
```

Rules:

- Trigger words are exactly **`SPONSOR-GATED`**, **`COUNSEL-GATED`**,
  **`INCORPORATION-GATED`**. Combine with ` · ` when a line has more than one.
- Use a Nunjucks comment `{#- … -#}` (not an HTML comment) so the marker is
  **stripped from rendered HTML** — these are internal notes, never public.
- The build **fails** if any `*-GATED` marker text reaches rendered HTML
  (`scripts/audit_website.py --built`, rule `gated-marker-leak`). That guard is
  why the marker must live in a Nunjucks comment, not an HTML comment or visible
  text.

Markdown repo documents (FUNDING.md, README.md, …) carry no inline markers —
this file is their checklist.

## The map — public website pages

| File | Line | Statement (quoted) | Trigger |
|---|---|---|---|
| `website/src/about.njk` | 29 | "We are not incorporated." | INCORPORATION |
| `website/src/about.njk` | 30 | "We have no fiscal sponsor confirmed." | SPONSOR |
| `website/src/about.njk` | 31 | "We cannot accept donations." | SPONSOR |
| `website/src/privacy.njk` | 28 | controller = "the founder operating the unincorporated project Uncost … provisional … once the legal home (incorporation or a fiscal sponsor) is settled" | INCORPORATION · SPONSOR · COUNSEL |
| `website/src/privacy.njk` | 37 | "signing up will ask you to confirm you are 18 or older … confirmed with counsel before any form opens" | COUNSEL |
| `website/src/contribute.njk` | 18 | "Uncost is seeking fiscal sponsorship before accepting public donations … no money changes hands today" | SPONSOR |
| `website/src/contribute.njk` | 25 | "Give — when donations open" | SPONSOR |
| `website/src/roadmap.njk` | 19 | "Tax-deductible donations open **only** after sponsorship is confirmed." | SPONSOR · COUNSEL |
| `website/src/treasury.njk` | 4 | description: "Not yet active — Uncost is seeking fiscal sponsorship before public donations open" | SPONSOR |
| `website/src/treasury.njk` | 16–18 | "Not yet active." / "seeking fiscal sponsorship before accepting public donations. No donations are open, and there are no funds to report yet." | SPONSOR |
| `website/src/assembly.njk` | 16 | "Not yet operational." | SPONSOR · INCORPORATION |
| `website/src/assembly.njk` | 43 | "… remain with responsible leadership and the fiscal sponsor. Any binding authority would require legal structure that does not yet exist." | SPONSOR · INCORPORATION |
| `website/src/_data/faq.js` | 11 | standfirst: "donations closed, sign-ups not yet open" | SPONSOR |
| `website/src/_data/faq.js` | 51 | "Uncost is not incorporated so cannot accept donations (coming soon!) …" | INCORPORATION · SPONSOR |
| `website/src/_data/faq.js` | 64 | "seeking fiscal sponsorship … there is no donate button anywhere on this site, and nothing here should be read as a solicitation" | SPONSOR |
| `website/src/_data/faq.js` | 67 | question: "When donations open, where will the money go?" | SPONSOR |
| `website/src/_data/faq.js` | 113 | "donations: we can't accept them yet but we hope to be able to accept support soon" | SPONSOR |

## The map — footer / layout

| File | Line | Statement | Trigger |
|---|---|---|---|
| `website/src/_includes/layouts/base.njk` | 52 | footer: "Nonprofit and nonpartisan." — stable (nonprofit **in purpose**); revisit wording only if incorporation changes the legal descriptor | INCORPORATION (wording review only) |
| `website/src/_includes/layouts/base.njk` | 51 | footer: "Get updates — [PLACEHOLDER …] Sign-ups open soon." | PRODUCT-LAUNCH (see below), not sponsor/incorporation |

## The map — repository documents

| File | Line | Statement | Trigger |
|---|---|---|---|
| `FUNDING.md` | 3 | "seeking fiscal sponsorship before accepting public tax-deductible donations. A path to an independent nonprofit entity remains a longer-term option under review." | SPONSOR · COUNSEL · INCORPORATION |
| `FUNDING.md` | 8 | "No donation should be represented as tax-deductible until a fiscal sponsor is confirmed …" | SPONSOR · COUNSEL |
| `FUNDING.md` | 23 | "Once funding begins, The Treasury should publish …" | SPONSOR |
| `FAQ.md` | 29 | "Not as tax-deductible donations. That waits for fiscal-sponsor confirmation and the required controls." | SPONSOR · COUNSEL |
| `GOVERNANCE.md` | 11 | "Fiscal sponsorship first. Uncost intends to launch through a fiscal sponsor; its own nonprofit entity remains a longer-term option under review." | SPONSOR · INCORPORATION |
| `OPEN_LETTER.md` | 17 | "It seeks fiscal sponsorship before accepting public tax-deductible donations." | SPONSOR · COUNSEL |
| `README.md` | 17 | "Fiscal sponsorship is sought before any public tax-deductible donation launch." | SPONSOR · COUNSEL |
| `ASSEMBLY.md` | 19 | "… remain with responsible leadership and the fiscal sponsor." | SPONSOR |

## Checked — no sponsor/incorporation statement

- **The Case closing paragraph** (`website/src/case/index.njk`): the closing
  section ("Evidence first. Tools next.") is about evidence and projects and
  carries **no** donation/sponsor/incorporation statement. Nothing to change at
  the sponsor gate.

## Related, but a different trigger — product launch

These change when the **email-capture form / that page ships**, not at the
sponsor or incorporation gate. Listed for awareness; **not** part of the sponsor
transition:

- "sign-ups open soon" / "when sign-ups open": `base.njk:51` (footer
  placeholder), `join.njk:23`, `privacy.njk:54`, `_data/news.js:13`,
  `_data/faq.js:11`, `_data/faq.js:113`.
- "planned … not yet built" placeholder pages: `press.njk`, `community.njk`,
  `quiz.njk`, `share.njk`, `news/events.njk`, `case/dashboard.njk`,
  `case/tracker.njk`.

## Pending: PR #45 (narrative copy pass 2) — not yet on `main`

PR #45 rewrites six narrative pages. When it merges, refresh these rows against
the rewritten files (the rewrites move the statements and add their own gated
markers, so the leak assertion will then cover them):

- **`contribute.njk`** — Status and "Give" blocks are rewritten and gain
  `SPONSOR-GATED` markers; the status paragraph adds the "hope to accept support
  soon" line. Line numbers shift.
- **`roadmap.njk`** — the tax-deductible gate line stays but moves; a
  `SPONSOR-GATED` marker is added above it. Line numbers shift.
- **`assembly.njk`** — the "Not yet operational" status and the "reserved
  matters" paragraph are rewritten; a `SPONSOR-GATED · INCORPORATION-GATED`
  marker is added to reserved matters. Line numbers shift.
- **`movement.njk`** — the Contribute tier becomes a live statement ("Donations
  open once a fiscal sponsor is confirmed") with a `SPONSOR-GATED` marker, where
  today it is only a `gap()` placeholder note.
- **`case/index.njk`**, **`projects/index.njk`** — no sponsor/incorporation
  statements added; no rows here change.

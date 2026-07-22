# Authority and production-use boundary

## Precedence

Use these sources in order. A lower item cannot override a higher one.

1. The final external Movement Plan and Roadmap recorded in [`docs/CONTROL.md`](../../docs/CONTROL.md).
2. The accepted UNP-39 canonical sitemap, revision 2, and accepted UNP-41 page-by-page content map, revision 1.
3. Current reviewed public documents in this repository.
4. [`website/assets/brand/ASSET_MANIFEST.json`](../assets/brand/ASSET_MANIFEST.json) for image identity, hashes, rights boundaries, and alt text.
5. This packet for visual tokens, layout behavior, and component appearance only.
6. The raw Claude Design prototypes as historical design evidence only.

The controlling source in item 1 is the final July-2026 Movement Plan and Roadmap, SHA-256 `a2b640217626a76e9a26f73a5744f8c59051c83351a72bc041150824ac5a3dcd` (27 pages), as pinned in `docs/CONTROL.md`; it supersedes the 2026-07-15 edition.

## Design-system authority moved to the finished export (2026-07-22)

This packet's visual authority (item 5) moved from the **2026-07-16 UNP-46 intermediate handoff** to the **finished Claude Design export, SHA-256 `8962b207d54d6536bef89ff8a96d5fc8ecb96007c01071dbdafbf03933730441`**. Reason: the UNP-46 handoff predated the finished pages — it was an intermediate intake, and the repo transformed its component vocabulary (`.u-block--` renamed to `.block--`, an accessibility layer added). The finished export contains all pages built on the export's native vocabulary (`.u-block`, `.blk`, `.rcpt-*`, `.status--*`), so the design-system now adopts that vocabulary directly rather than a rename that no page uses. The change was made through a reviewed, audited pull request; the earlier CSS remains recoverable from git history. See the source receipt (`SOURCE_RECEIPT.json`) for exact source hashes.

Three constraints the repo already enforced were **re-applied** on the adopted CSS, because the finished export's design-system layer had regressed each (the audit catches them; they are documented in `docs/DESIGN_CONSTRAINTS.md`):

- **Coral contrast rule.** Bright coral (`#D64A1E`) is for decoration and large-display only; normal-size text, links, and small pills use **deep coral (`#B23A14`) with cream** to meet WCAG 2.2 AA. Links, the `needs-refresh` and `focus` pills, and the coral CTA block were moved to deep coral (bright coral failed at 4.04–4.47).
- **No `vote` or `dollar` glyph** in the icon set (content-safety omission, per `EXCLUSIONS.md`). The export re-introduced both; they were stripped.
- **Light theme only.** The export's attribute-only dark theme was stripped (recoverable from the export archive).

## Status vocabulary (changed with this adoption)

The honest-status class set is now `status--{live, dev, planned, focus, next, dossier, future}` (adopted from the finished export), replacing the earlier `status--{prelaunch, draft, scaffold, planned, blocked, receipt}`. The substance is unchanged and preserved: every status renders honest text and no bare `Live`/`Funded`/`Approved`/`Operating` badge appears — for example `.status--live` renders **"Designed — opens at launch"**, never the word "Live." The content audit's badge ban is on rendered text, not class names. This is recorded as a contract-relevant change (UNP-50 rev 4) and in `docs/CONTROL.md` (DEF-05).

If visual reference copy conflicts with control, control wins. If an image path, hash, or alt string conflicts with the asset manifest, the manifest wins. Stop and preserve unresolved conflicts rather than inventing a result.

## Accepted structural constraints represented here

- The four top-level parts remain in this order: The Movement, The Case, The Projects, The Assembly.
- The primary CTA label is “Sign the Pledge,” but this packet provides no submitting behavior.
- Uncost remains pre-launch. The Assembly is advisory and not operating.
- No public number appears without a source, date, method, confidence, and correction path.
- Forms, email capture, payments, and donations remain inert until their separate privacy, vendor, policy, sponsor, security, and founder gates clear.
- Public copy must not revive retired economic-system, token, wallet, on-chain, or binding-governance framing.

## Visual authority supplied by this packet

- Civic-block composition: full-width flat blocks, square corners, no shadows, and strong rules.
- Roboto Condensed for display roles and Inter for body roles.
- Cream and ink foundations, coral emphasis, and the wheat, clay, sage, and ink-blue sector palette.
- Mobile-first vertical flow, responsive grids, clear focus states, and reduced-motion support.
- Receipts-first claim furniture and honest status labels.
- A small, currentColor icon subset with square caps and miter joins.

## Deliberate deviations from the prototype

- Normal-size actions use deep coral with cream text to meet contrast; the original coral is limited to decoration and large display use.
- The continuously moving carousel, demo counters, illustrative dollar figures, and unsupported sector claims are absent.
- `live`, `funded`, `approved`, and similar status variants are not implemented.
- Prototype React/Babel CDN execution and external font runtime requests are absent.
- Asset references point to the canonical repository manifest. Duplicate logo, sector, and robot files are not included here.
- The icon subset omits the old voting and dollar symbols. Their omission is a content-safety decision, not a claim that financial or participation interfaces can never exist after their gates clear.

## What this does not authorize

This directory does not authorize merge, deploy, DNS or Cloudflare changes, public launch, data collection, form submission, fiscal-sponsor claims, payments, donations, outreach, policy adoption, project build, or Assembly operation. Those actions require their own explicit approvals and evidence.


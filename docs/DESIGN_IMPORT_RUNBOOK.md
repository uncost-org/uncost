# Design-import runbook — staging the Claude Design export into public history

This procedure exists because public git history is permanent. The Claude
Design export is the single highest-risk import in the project: it is known to
contain retired framing (for example "Money is broken") and placeholder
figures, and a public pull-request branch is already public history. A stale
string pushed "temporarily" to a public branch cannot be recalled. So the
export is cleaned in a **private** staging repository and only its audited,
clean result is moved to a public branch — in one commit.

Do not push the raw export, or any intermediate cleaning state, to
`uncost-org/uncost` (public) on any branch.

## Roles and repositories

- **Private staging:** `uncost-org/uncost-design-staging` — private, no
  Cloudflare Pages, no Actions secrets. Founder creates it when the export is
  ready. Iteration and cleaning happen here.
- **Public target:** `uncost-org/uncost` — the clean tree lands here as one
  audited commit on a feature branch, then a normal reviewed pull request.

## Prerequisites

- The two audit scripts and the website scaffold are already on the public
  `main` (they are; this runbook post-dates them). The staging repo starts as
  a clone of public `main` so `scripts/audit_website.py`,
  `scripts/audit_repository.py`, and the Eleventy build are present and behave
  identically to public CI.
- A local checkout with the hooks enabled (`sh scripts/setup-hooks.sh`).
- Node 22 and Python 3.12, matching CI.

## Step 1 — receive and unpack the export in isolation

1. Founder places the export archive on the build machine at a path **outside**
   any public repository working tree (for example under
   `~/Projects/uncost-private/design-export/`). Never unpack it inside
   `uncost-org/uncost`.
2. Record the archive's SHA-256 and byte count before unpacking; note them in
   the staging pull request so the exact source is pinned (the same discipline
   the design-system `SOURCE_RECEIPT.json` already uses).
3. Unpack into a scratch directory, also outside any public working tree.
4. Inventory what arrived: a design-system update (tokens/components/assets)
   and page content. Separate the two — the design-system packet is governed by
   `website/design-system/AUTHORITY.md` and its receipt; page content becomes
   template and copy under `website/src/`.

## Step 2 — clean in the staging repository, never in public

1. In `uncost-org/uncost-design-staging`, create a working branch.
2. Bring the export content in and reconcile it against control:
   - copy derives from the final Movement Plan and reviewed repo documents
     (`docs/CONTROL.md` authority chain); legacy site copy does not ship;
   - image references resolve to `website/assets/brand/ASSET_MANIFEST.json`
     paths and alt text (the manifest is the sole image authority);
   - no invented figures, counts, dates, names, or social handles — anything
     not yet sourced/verified stays a visible `[PLACEHOLDER]`.
3. Run the audit against the export **before the first commit**, and keep
   running it as you clean:
   ```sh
   python3 scripts/audit_website.py          # source scan
   npm --prefix website ci && npm --prefix website run build
   python3 scripts/audit_website.py --built website/dist   # built-output scan
   python3 scripts/audit_repository.py       # structure + hygiene + design receipt
   ```
   Fix every FAIL at its source. Do not add allowlist entries to silence real
   stale content — the allowlist is only for legitimate uses (for example a
   prohibition sentence that names the mechanism it bans), each with a written
   justification and reviewed like any change.
4. Commit freely in the staging repo. Staging history is private and
   disposable; that is the point.

## Step 3 — "green twice" gate

The clean tree must pass the full audit chain **twice, from a clean state**,
with no changes between the two runs:

1. From a clean working tree in staging, run all four commands above; confirm
   `python3 scripts/audit_website.py` reports `fail_count: 0` in both source and
   built modes, and `python3 scripts/audit_repository.py` reports `ok: true`.
2. Run the identical sequence a second time without editing anything. It must
   produce byte-identical audit verdicts (zero fails, same suppressed and queue
   counts). A second run that differs means something is non-deterministic
   (build output, a timestamp, an ordering) and must be resolved before the
   import is considered clean.

"Green twice" means: two consecutive clean-state runs, both fully green, with no
edits in between. One green run is not sufficient — the second run is what
proves the clean state is stable and reproducible, not a one-time artifact of
the working tree.

Warnings (`WARN`) and review-queue items (`QUEUE`) do not block the gate, but
every `WARN` must be dispositioned before the public commit: either cite the
figure, reword it as a target rather than a measurement, or record a queue
entry with a written note. No `[PLACEHOLDER]` marker may remain on a page that
is meant to ship as final content.

## Step 4 — move the clean tree to public in one audited commit

Do not merge staging history into public. Move the **result**, not the history:

1. In a fresh worktree of `uncost-org/uncost` off current `main`, create the
   import branch (for example `feat/design-import`).
2. Copy the cleaned files from staging into that worktree (the design-system
   update and the `website/src/` content). If the design-system packet changed,
   regenerate its `SOURCE_RECEIPT.json` output hashes in the same change, and
   record the export archive's SHA-256/bytes in the receipt or the pull-request
   body.
3. If this import is also the first real content, it carries the Pagefind
   implementation per `website/SEARCH.md` (search at launch is a founder
   decision, scheduled to the first-real-content pull request), including the
   index-scope CI assertions that document requires.
4. Run the full audit chain locally; the committed hooks run it again on commit
   and push. Everything must be green before the push.
5. One commit, one push, one pull request. The pull request body pins the export
   source hash, discloses AI assistance, and states what remains placeholder or
   queued. Founder reviews and merges; CI is the third line of defence behind
   the local pre-commit and pre-push hooks.

## Step 5 — retire staging

Once the public pull request is merged, the founder deletes
`uncost-org/uncost-design-staging`. The private cleaning history is not needed
and should not persist.

## Why this shape

- The audit runs **before the first commit** and again on every commit/push via
  hooks, so stale content never reaches even a private commit unaudited, and
  never reaches public history at all until it is clean.
- Cleaning happens in private, so the inevitable intermediate states (raw
  export, half-fixed copy) are never public.
- The public repository receives a single clean commit, so its permanent history
  contains no stale-content revisions to explain away later.

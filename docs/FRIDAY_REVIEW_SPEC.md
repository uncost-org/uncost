# Uncost Friday review — reviewer specification

**DRAFT — Phase 1C, 30 September 2026. Design only; nothing installed or activated.**

This specifies later work; it is not that work's execution approval. Matt must approve A (canon amendment), B ([criteria](COST_WATCH_CRITERIA.md)) and C (this specification), then later review the dry run and explicitly authorize go-live before scheduling. No fetcher or bot exists as a result of this PR. [Source hierarchy](CONTROL.md) and the existing UNP-83 confirmation rule remain controlling. Proposed implementation choices below are sign-off questions, not newly imposed founder controls.

## 1. Scope and evidence

Job name everywhere: **Uncost Friday review**. Owner: Uncost.org. Astra (`gpt-6-astra`) through `openai-codex` on Matt's existing ChatGPT subscription; no paid API, new API key, signup, other model or fallback. Bot credential creation by Matt is the explicit later-phase transport exception, not permission to buy a data/model API.

Runtime GitHub identity: **uncost-admin**, isolated `GH_CONFIG_DIR`, with `GH_TOKEN` and `GITHUB_TOKEN` absent. Check `gh api user` before any authenticated operation. Only `uncost-org/uncost`; only `reviewer/*` PRs, no direct-main writes, no production deploy, Cloudflare/email/other-company credentials or Paperclip writes. Use a sanitized process environment; a separate Hermes profile alone does not prevent access to ambient credentials. Do not inherit MCP connectors, broad memory, secret stores, CLI homes or credential helpers from another company. Fail closed rather than borrowing access.

The sole Phase 1A exception is one draft PR in `dafuqindustries/portfolio-canon` by the normal canon coordinator, never uncost-admin. It does not extend into this job. Uncost News can cite merged, public, non-sensitive canon bytes available without another-company credentials; otherwise use merged Uncost repo changes only. Do not quote private canon into public news.

Phase 0 Paperclip closure is **founder-supplied reviewer evidence**, read 30 September at 21:00 ICT; accepted without an independent Carlbot read or a new credential/browser-profile route:

- **UNP-70 DONE.** Founder comment at `2026-09-27T23:39Z`; agent close at 23:40Z (internal comment handles retained only in private drafting evidence). PMMS dropped. Census median asking rent is a candidate, subject to the single-workbook rule below. ACS 2024 publication date: `2025-09-11`. SEC-014 retains NOAA 2024 with the date visible. These are supplied instructions, not freshly verified source values.
- **UNP-83 IN_REVIEW.** Founder rule, verbatim: “actual print values for all four get a verification pass with my explicit confirmation before any row is marked confirmed and wired, and all four get a final freshness check at the publish gate.”
- The pending `request_confirmation` of 22 August (interaction handle retained only in private drafting evidence) has stale gas week ending 08/17 and July CPI. Matt will not confirm it. Fresh first-live Register cards replace those values for this workflow. The Paperclip interaction is not closed, edited, answered or recreated. SRC-024 is additionally in scope, using SRC-020's method.
- Paperclip, Marketing and relay holds stand. No issues, comments, approvals, interactions or new control. `@dafuq_relay_bot` publisher/receiver stays untouched; the proposed separate content receiver is not a relay replacement.

GitHub design baseline: Uncost main `949f80c22ce601244d5c9f6866a16ed9d53f5dbe`; `sources/register.csv` has 27 data rows (26 cost statistics and one governance control), with no `checked_by` column. The actual cadence module is **`website/src/_data/register.js`**, not `sources/register.js`. The fresh pre-draft inventory includes Batch X #58 (`content/batch-x`, head `fb7ac10c1b8be73b3b0f5eec089271a94d88dff6`) and Dependabot #59 (`ip-address` 10.7.2). These are dated baseline pins, not future live checks.

## 2. Portable core and private plain-file state

Scoring, criteria and state use versioned UTF-8 Markdown/JSON/JSONL/plain evidence files, not Telegram history, opaque model memory, a vendor database or a bot-owned business state machine. Telegram only renders core cards and submits authenticated action events. Replacing it must preserve item IDs, evidence, feedback, decisions, outbox reservations and receipts. Future TotalAgents migration as its own company is not currently authorized.

Proposed private state root (not created): **`~/.local/state/uncost-friday-review/`**. Home-relative paths below are intentional specification locators requested by Matt, not disclosures of a machine username, group ID or secret.

| Relative file/directory | Proposed contents |
|---|---|
| `manifest.json` | Schema/core version, owner, mode (`draft`, `dry-run`, `live`), criteria commit/hash, run IDs, readiness facts. Mode cannot grant authority. |
| `config/criteria.md` | Exact approved criteria snapshot, pinned to merged commit and hash; public source of truth is `docs/COST_WATCH_CRITERIA.md`. |
| `config/scoring.json` | Proposed B components and deterministic tie-break; no private token or silently learned policy. |
| `config/runtime.json` | Non-secret repo/identity, timezone, limits, source configuration, secret references, installed version pins. |
| `config/telegram.json` | Private verified numeric Matt user ID, bot ID/username, group ID and the six topic IDs; absent until setup. |
| `evidence/<sha256>/` | Minimum lawful public evidence extracts, URLs, retrieved-at UTC, method, table/cell/series locators, source-byte digest and licence notes. No wholesale publisher copying or secrets. |
| `items/<item_id>/<version>.json` | Immutable card, content/evidence hashes, row-before hash, proposed diff, dates, score explanation and approval scope. |
| `events.jsonl` | Append-only authoritative core transitions with event ID, sequence, prior-event hash, timestamp and item/version. |
| `state/items.json` | Rebuildable current-item projection; never authority over the event log. |
| `reviewer/feedback.jsonl` | Private decision training records with the exact fields below. Never in public git. |
| `outbox.jsonl` | Durable send-intent reservations, exact payload hashes and sent/failed/unknown outcomes. |
| `receipts.jsonl` | PR/head/check/merge readbacks and local failure receipts; no credential-bearing URLs. |
| `runs/<run_id>.json` | Limits, fetched/skipped/failed sources, carried/expired items and pinned source/code versions. |
| `adapter/telegram/updates.jsonl` | Accepted update IDs and callback ownership; durable dedup, not a second decision ledger. |
| `backup/receipts.jsonl` | Snapshot hashes, destination availability, restore-test result, retention and RPO observations. |
| `dry-run/` | Fully separated simulation events/outbox/feedback; excluded from live replay and training. |

Permissions proposal: owning user only, directories 0700, files 0600, umask 077, FileVault-backed host storage; no sync into public repository or portfolio data. A single process lock protects atomic state changes. Append durable event + fsync before acknowledging; projections use temporary-file + fsync + atomic rename and parent-directory fsync. Partial/truncated records halt writes for recovery, never skip to the next record. No arbitrary downloaded content is executable.

## 3. Exact proposed scheduler/profile and secrets — NOT INSTALLED

- Hermes profile name: **`uncost-friday-review`**.
- Proposed home: **`~/.hermes/profiles/uncost-friday-review/`**; not created, cloned, selected or registered by Phase 1. A blank profile is preferred over cloning another profile's credentials/skills/memory.
- Proposed profile config: `timezone: Asia/Ho_Chi_Minh`; `model.default: gpt-6-astra`; `model.provider: openai-codex`; `cron.model: gpt-6-astra`; `cron.model_provider: openai-codex`. Pin the eventual jobs to this route, with no alternate provider/fallback. Before installation verify the current supported config and effective route; stale config must block rather than silently fall back.
- Two stages of the same **Uncost Friday review**: Friday preparation `0 20 * * 5`; Saturday delivery `0 8 * * 6`, both interpreted in Asia/Ho_Chi_Minh. Stage labels are metadata, not a renamed portfolio job. Each starts disabled until the post-dry-run go-live approval.
- Profile-scoped Hermes cron will invoke bounded core/adapter entrypoints, with scheduler delivery **local only**, so it cannot duplicate the dedicated bot's outbox. Friday produces no Telegram messages. Saturday posts decisions plus one compact source-health line even with no candidates. The user-facing empty result is “Nothing needs you this week.” Never say that if preparation failed; say “Review unavailable this week — source checks incomplete” with an honest health summary.
- Receiver: later proposed dedicated local long-polling Telegram adapter; no public webhook server and no reuse of the Dafuq relay. It shares the single locked durable event protocol with the job.
- Scheduler availability is not yet verified. If the host is off/asleep, exact 08:00 delivery is impossible; no wake/power/service changes are authorized here. Before go-live prove an awake scheduler in the selected timezone and capture next-run times. A missed slot may be sent late only if no prior send-intent exists and sources remain current; label it late. An existing unknown intent is never replayed.

**Keychain entry proposal:** macOS generic-password **service `org.uncost.friday-review.telegram`**, **account `uncost-review-bot`**, label **`Uncost Friday review — Telegram bot token`**, in the owning user's login Keychain. No entry was created, queried for a value or changed. Use the Security framework to load into memory only; no token in argv, shell history, stdout/stderr, configuration, logs or Telegram. Telegram token-bearing request URLs must be redacted before exception/log handling. If unattended Keychain access is denied, stop; no UI auto-click or broad ACL bypass.

Phase 2 will supply Matt a reviewed silent-input token-storage command. It must not pass the entered token in a process argument (including `security ... -w <token>`). No executable token command is installed or run at Phase 1. Existing Codex subscription auth must be provenance-checked at setup; profile-local state does not automatically isolate model auth because Hermes can fall back to the global provider store. Do not copy another company's keys or claim new independent billing. If the permitted subscription cannot operate without other credentials, stop for Matt.

References: [Hermes profiles](https://hermes-agent.nousresearch.com/docs/user-guide/profiles), [Hermes cron](https://hermes-agent.nousresearch.com/docs/user-guide/features/cron). Both official docs were read during design. The installed timezone resolver additionally uses `HERMES_TIMEZONE` before profile `timezone`; reject a conflicting inherited override. These are design references, not proof of installed jobs or successful scheduling.

## 4. Backup / restore coverage proposal — NOT CONFIGURED

All of the private state root in section 2 is covered, including feedback, immutable item versions, source evidence, decision events, outbox intents/unknowns, callback update IDs, receipts, criteria snapshots, projections and backup metadata. Also cover non-secret profile/runtime configuration, approved core/adapter commit hashes and dependency pins; rebuild executables from reviewed source. Never back up the whole ambient Hermes home or other-company credentials as a shortcut.

Proposed target: an **encrypted external APFS volume labelled `Uncost Review Backup`**, subtree `uncost-friday-review/`. This target is proposed, not detected/provisioned; no disk formatting, mount or backup-policy change is authorized now. Same-disk snapshots alone are not disaster-recovery coverage. The volume's identity, encryption and access controls must be recorded privately and verified before activation; use existing approved storage if Matt chooses a different target at sign-off.

- Snapshot under the state lock after Friday preparation and each decision/side-effect-intent batch; include a file list, byte counts and SHA-256 manifest with last event sequence and outbox high-water mark. Publish an archive only by atomic rename after checksum validation. No pruning until a newer backup has verified.
- Every externally effecting send/commit/merge requires its durable intent to be included in a verified backup **before** the external call. If unavailable, retain decisions locally, stop further side effects and record health; do not proceed on an assumed backup. Already delivered messages are not resent to report a backup failure.
- Proposed retention: 30 daily and 12 weekly encrypted snapshots, plus the latest verified pre-upgrade snapshot. Record actual RPO; do not promise zero loss for post-call acknowledgements. A lost acknowledgement restores as reserved/unknown and remains no-replay.
- Token values are excluded from these plain-file archives. Keychain is separate credential custody: restore requires Matt's Keychain recovery or token re-entry/rotation at the silent prompt. Codex/GitHub auth is re-established through approved existing routes, never exported into the state backup. No secrets in the restore report.
- Restore only under a separately authorized procedure: keep schedules/receiver disabled, validate archive manifest and hashes, restore into a separate staging directory, enforce modes, rebuild projections from events, check feedback count/order, item hashes, event chain and outbox/update high-water marks. Reconcile GitHub commits/PRs/merges by read-only exact IDs before deciding outstanding work; never replay unknown external effects.
- Test restoration before go-live, monthly, and before changing state schema. Require a round-trip comparison against the source snapshot, including a simulated delivered/unknown send and consumed callback. No network sends or real commits in a restore test. Promotion from staging and any resumption require explicit authorization; restoration is not activation.

Current coverage verdict: **designed only; permissions, encryption, destination availability, unattended Keychain access, backup execution and restore success are unverified**. Phase 1 approval does not claim otherwise.

## 5. Preparation, freshness and queues

### Register

Use the **merged site's actual** cadence logic and schema pinned to a commit. At the design base: weekly 7 days, monthly 31, quarterly 92, annual 366; due when whole UTC days since `last_checked` are **strictly greater** than the period. `on-change` has no age clock. Missing/malformed checked dates are due; undefined cadence is a visible health condition, not proof of freshness. A future checked date is invalid for this job and needs review.

The required later behavior is **biennial = 731 days, final = never**; main at the design pin has undefined `biennial` and `retired-final-edition`. Do not copy logic from open Batch X and call it merged. After #58 merges, inspect the actual cadence names/mapping and prove parity with site boundary fixtures, including the retained NOAA final-edition alias. No silent reinterpretation of `retired-final-edition` as `final` and no change to the CSV's confidence merely to remove a freshness badge.

Normal weekly selection: one card per due cost-statistic row, oldest checked date first, invalid dates first, ties by SRC ID; **maximum 10** across new and still-pending Register cards in that delivery. The governance pin is not a numeric refresh card. Additional rows carry over without resetting age. Pending cards keep their original message/expiry; do not repost their Approve keyboard weekly. Source changes supersede the old version and require fresh evidence/approval.

**First-live bootstrap proposal requiring Matt's sign-off in C:** refresh the four existing Cost Watch rows `SRC-017`, `SRC-025`, `SRC-026`, `SRC-027`, plus `SRC-024`, within the same ten-card cap, before filling remaining slots oldest-first. This explicitly proposes a one-time priority exception because the stale confirmation must be replaced at first live delivery and SRC-024 may not yet be due by quarterly age. No silent promotion of SRC-024 to “due.” Sort the four overdue rows oldest-first within their group, then SRC-024, then normal remaining rows. Thereafter revert to normal oldest-first. If this exception is not approved, do not claim the first-live confirmation requirement and strict oldest-first ordering are both met; hold the first-live batch for reconciliation.

Each Register card carries SRC ID/series, exact old value/period/publication/checked date, new value/period/publication date, exact source URL, retrieved-at timestamp, verification method, units, region, caveats, numerical receipt, row-before hash, proposed diff and evidence hash. **A real page load** of the publisher's table/release (or source workbook inspection), not a summarizing fetch/snippet, is required. Use independently visible table cells/series and programmatic arithmetic/rounding; never mental transcription alone. If original-page access fails, mark unavailable and do not invent a number or treat another summarizer as verification.

- No bare-year display value. New `display_value` must occur verbatim in its own caption; retain valid region/data period, units, licence, comparison basis and site schema.
- All four Cost Watch prints receive final original-source freshness checks at the publish gate. A changed print invalidates the frozen approval; prepare a new version. “Checked again” cannot silently update the approved values/text. Apply the same safeguard to other changed Register claims.
- **SRC-017 proposal:** keep the EIA gasoline series in the Register as the single source/evidence record, with weekly cadence and `placement=news-feed`; render it only in Cost Watch, not durable sector/thesis headlines. Thus it is not a choice between provenance and feed: the Register stores it and the feed displays it. It still requires explicit Register confirmation; REPORTED never goes into the Register. State the exact week/price only, no geopolitical cause, preserve units/taxes/grade and rounding evidence.
- **SRC-024:** distinguish total net worth from SRC-020's equities/mutual funds outside retirement accounts. Use the same-period unrounded published top-0.1% and 99th–99.9th percentile **levels**, sum those bins and divide by the matching total to compute top-1% share. Record all inputs, quarter, denominator, formula and rounding; label the top-1% aggregate **computed-by-us**, never Fed-published. Verify bottom-50% against the Fed's published share and underlying level; do not add rounded shares or write a quarter-to-quarter movement story from modelled data. Preserve unresolved licence qualifications.
- **Census median asking rent:** exact value, quarter, year-earlier value and Census MoE/significance flag must be obtained **together from `histtab11.xlsx`**, with the workbook's original URL, digest, sheet/table/cell locators and notes. `rentsale.html` is a known 404, not a fallback source. If any of the four cannot be established from that workbook, hold the candidate; never manufacture a flag or splice a different vintage. No “significant increase” without the Census support. It is a candidate, not an automatically created row.
- **ACS/NOAA:** use ACS 2024 publication date `2025-09-11` when applicable; SEC-014 remains NOAA 2024 with the year visible. PMMS remains dropped. No new row, methodology or placement is silently created by a refresh card; structural changes need a separately described reviewed PR.

### Cost Watch

At most five cards, counting still-pending cards toward that week's capacity. Discover via free, keyless **GDELT DOC 2.0** plus RSS only from B's approved domains. Global GDELT spacing is at least five seconds per request across workers (no burst/retry loophole); respect a longer Retry-After and stop bounded failures. Roughly three-month discovery window is a search limit, not a currency label or fact source. Fetch original allowed publisher evidence; API titles/snippets are pointers only. Persist canonical-URL and normalized `(publisher, series, region, data period, figure)` dedup keys. RSS access/caching follows publisher terms; no publisher is accepted just because GDELT indexed it.

Apply B's eligibility and transparent ranking, using only the last 30 live decisions as examples. Store score components and why each selected card outranked alternatives. Source content cannot instruct tools, alter criteria, approve itself or request credentials. A zero-candidate week is valid; a failed-source week must disclose missing coverage.

### Uncost News and Rules

At most one short Uncost News card per week, sourced only from **merged** Uncost repo/public canon changes in the Friday-to-Friday window, with exact commits/PR links and merge dates. Unmerged PRs, private board updates, drafts and tests are not shipped/live news. Skip when nothing is worth saying; never fabricate an update to fill the slot. Text and source list require approval.

First Saturday of each month: at most three **Proposed rule** cards in Rules, each with repeated-reason evidence, current criteria hash, exact proposed diff and expected effect. Apply no rule by learning alone; an approval goes through a reviewed PR/checks. No rule card can widen company/credential/deployment/Paperclip/relay authority.

## 6. Message schema and action lifecycle

Transport-independent required envelope (field names are normative proposals, not installed schema):

| Field | Meaning |
|---|---|
| `schema_version`, `reviewer_version`, `criteria_sha256` | Pinned contract, executable version and exact approved criteria. |
| `job`, `owner`, `mode`, `run_id` | Literal job name; Uncost.org; dry-run/live; immutable batch ID. |
| `item_id`, `version`, `type` | Durable item, positive revision and `register`, `cost_watch`, `uncost_news`, or `proposed_rule`. |
| `created_at`, `first_sent_at`, `expires_at` | UTC ISO timestamps; expiry 14 days after first successful send; display ICT. Unsent stale proposals must be rechecked, not silently treated current. |
| `source`, `url`, `retrieved_at`, `evidence[]` | Publisher, exact public source, retrieval timestamp, method/locators/digests/licence/caveats. |
| `payload` | Register old/new series fields; B's full Cost Watch fields; News text+merged sources; or exact criteria diff. |
| `proposed_diff`, `base_commit`, `row_before_sha256` | Exact Git scope and preconditions; null row hash outside Register. |
| `content_sha256`, `evidence_sha256`, `approval_sha256` | Hash exact immutable payload/evidence/decision envelope, excluding volatile transport status. |
| `score_components`, `why_selected`, `example_ids` | Transparent ranking explanation; null where not applicable. |
| `decision`, `decided_by`, `decided_at`, `reason_code`, `reason_text`, `edited_text` | Empty until durably recorded; private identifiers never committed publicly. |

Canonical hash serialization: UTF-8 JSON, sorted keys, no extra whitespace, no floating-point numeric evidence (store decimal strings), exact string bytes and SHA-256. Define/test this before implementation; a displayed abbreviation is never the equality check. The approval hash binds owner/repo/branch class, type, item/version, base/diff, source evidence, criteria version and mode.

Telegram mapping lives only in the private adapter state: verified group, topic, message ID, numeric actor ID, update ID and an opaque callback token of at most 64 bytes. Token maps to the complete immutable envelope and allowed action; never contains a secret or the full document. Validate Matt's numeric user ID, bot/group/topic/message, current version, unexpired state and exact full hash server-side. Group admin status, display names, forwards and replies from other users never grant approval.

Actions: **Approve**, **Reject**, **Edit** (text items only: Cost Watch/News; not numeric Register fields or proposed-rule diffs).

1. Single-writer compare-and-set reserves the first valid action before any prompt/reply; duplicate or conflicting later clicks get **“already recorded”**, with no second effect.
2. Approve records the exact envelope and queues only its approved change. No card delivery, timeout, model score or previous row confidence counts as confirmation.
3. Reject irrevocably blocks approval for that version, then opens **Off-topic · Weak source · Duplicate · Not cost-of-living · Wrong number · Other**. Other asks for one line. Continuation is accepted only from the same actor for the reserved reject event. If no reason arrives, keep rejected with null reason; never turn it back into pending/approved.
4. Edit reserves/consumes that version, requests replacement text and records it privately. It produces a new version after source/criteria checks, requiring a new explicit Approve. Edit is not a back door to change numbers, sources or a rule diff. A stalled edit stays non-approved.
5. Unknown callback-record outcome is resolved from the durable ledger, not by applying the action again. Separate callback transport dedup from logical item/version dedup.
6. Unanswered cards carry over; after 14 days they expire with one Health note. No automatic approval or renewal. Expiry also ends incomplete reject-reason/edit continuations without reversing a rejection. Expired/changed cards need fresh evidence and a new version. Old keyboards can be disabled best-effort, but server checks remain authoritative.

Private feedback record, exactly the requested fields:

`{ts, item_id, type, source, url, decision, reason_code, reason_text, edited_text, reviewer_version}`

Use null for unused fields; timestamps UTC; decision is approve/reject/edit/expire as appropriate. Last-30 training selects approvals and rejections only, excluding edits, expiry, dry-run and duplicates. Events retain the bound hash/version; feedback references its unique item-version key. Append once per completed decision; missing reject reasons remain null, with any later reason represented through an event-backed rebuild rather than duplicate training examples. No public feedback file.

## 7. Approval to reviewed PR and receipt — future live behavior only

Before later writes, re-read all open PR file lists including rename-old paths. **Never write any path an open PR is changing**, including Batch X #58 until merged and all Dependabot PRs (including #59). Closed-but-unmerged #58 still does not release its explicit lock. Do not edit packages, lockfiles or workflows to make this design pass. Own in-progress PR is the only excluded entry for its already-owned paths. Drift or collision blocks that change with Health, not a force-push/override.

**Schema dependency:** after Batch X merges, add `checked_by` and the necessary CSV/`website/src/_data/register.js` changes in their **own reviewed PR**, with site compatibility tests. This Phase 1 PR does not add the column. Do not activate Register commits until that reviewed schema is merged and verified. Preserve every existing row's confirmation meaning; no blanket retroactive `checked_by`.

After go-live and an individual exact approval:

- Prepare the approved patch on `reviewer/YYYY-Www` using the ICT week's ISO week-year; serialize all job writes. Use the week's existing PR while open. If it is already merged, do not silently invent another branch pattern or reuse stale commits: carry late approvals to the next weekly batch, rechecking evidence and requiring a new approval if content changed. No duplicate PR on an ambiguous creation response.
- For each approved Register row set `checked_by` to **`agent-checked, human-approved: Matt <timestamp>`**, using that row's actual UTC approval timestamp. Proposed non-Register content uses the same attribution in item frontmatter if supported, otherwise an explicit PR-body/commit receipt linked to the item; no unsupported schema field is injected. Agent-check timestamp remains distinct.
- Agent checking alone cannot mark a row confirmed or wire it. Existing legacy `confirmed` cells do not establish fresh authorization. Only the exact newly approved rows may be updated; preserve unrelated rows. A changed base-row hash invalidates the patch and returns it for review.
- Recheck original-source freshness at the publish gate, all four required prints together, as well as schema/site guards and licence conditions. A changed print/text/evidence requires a new version and approval. Block a batch that cannot meet the all-four freshness check; do not claim partially verified publication.
- Open the PR, pin exact head, wait for required checks and any repository review requirements. **Squash-merge only if all required checks are green at that head and the later live authorization permits it.** No missing/pending/skipped/neutral check counted as green; no admin bypass, auto-merge setting or self-approval workaround. Failure or branch-protection block leaves PR open and posts Health.
- Phase 1 is an explicit exception to execution: documentation draft PRs only, **no merge by Carlbot**. Canon merge is always Matt's action. A future content merge is not a production deployment; if any workflow would deploy production, hold before that side effect and seek separate authorization.
- Receipt: item IDs/hashes, approval times, PR URL, reviewed head, merged commit SHA, required-check names/conclusions/head and merged-at readback. Say “merged in repository; not production-deployed” unless a separate deployment is proved. Health failures identify the affected item/PR and one decision required, not raw logs or secrets.

## 8. Exactly-once intent, not imaginary exactly-once delivery

Before any Telegram send, reserve immutable `(run, topic, item/version or weekly-summary)` intent and payload hash in `outbox.jsonl`, fsync and back it up. One network attempt only for that reserved intent. Record a returned message ID as sent, a definite rejection as failed, and timeout/connection loss/ambiguous response as **unknown**. **Unknown send outcome = log it, never replay.** No generic network retry middleware, scheduler redelivery or automatic restored-queue resend may bypass this. A new item version is not a retry disguise.

Use the same reservation/readback discipline for PR creation, commits and merges; read-only lookup may reconcile an exact ID/head, but ambiguity does not authorize another mutation. A human reconciliation action can be proposed without repeating the uncertain send.

Saturday requirement is an obligation to attempt the verified summary, not a claim Telegram guarantees receipt. If the summary send itself is unknown, record locally and do not replay it. An independent later Health notice may describe the unresolved incident once, only under a separately reserved notice key, never duplicate the original cards. Health output stays compact and actionable; ordinary internal steps stay local.

## 9. Later phase sequence and acceptance tests

**Phase 1 ends now at the draft review STOP.** Only after Matt explicitly approves A/B/C:

1. Matt creates “Uncost Review” via BotFather, chooses the final username, disables privacy, creates a private Topics-enabled “Uncost Review” group, adds the bot as admin, and creates **Register · Cost Watch · Uncost News · Rules · Receipts · Health**. Token is entered only at the approved silent local prompt. No setup happens from this document.
2. Capture and verify numeric identities/topic mappings; one “setup check” in Health under the later setup authority. Never guess IDs or copy the existing relay's receiver/credentials. Implementation remains a separately scoped task after the draft gate.
3. Verify frozen implementation, core-file portability, no ambient credentials, cadence/schema parity, source parsers and arithmetic, callback authentication/idempotency, first-live bootstrap ordering, ten/five/one limits, monthly-three cap, source-health fallback and publish-gate all-four checks.
4. Tests must include duplicate/conflicting callbacks, reject continuation, edit reapproval, expired card, changed print, open-PR collision, missing required checks, backup unavailable, permission denial, concurrent writers, interrupted event append, unknown send, process crash after reservation and archive restoration without replay. Real-source parser smoke tests must report access failures honestly. No live network side effect inside unit/restore tests.
5. **One DRY RUN**: every card and summary visibly DRY RUN; buttons log only, no real PR/commit/merge, no live feedback learning. Supply Matt the send log and private feedback sample as a protected attachment, with exact run/code/criteria hashes; never publish the feedback sample in git. Dry-run send authority is not go-live authority.
6. **STOP for explicit go-live.** Only then enable the verified Friday/Saturday schedule. Report the first live Saturday's actual receipts, not a promise.

### Decisions requested with this draft

- Approve A/B/C as design only, with SRC-017 retained as Register provenance and feed-only presentation.
- Approve or revise the explicitly described first-live five-row bootstrap exception within the ten-card cap.
- Approve or revise proposed plain-file custody, exact Keychain/profile names and encrypted external-backup target/retention. No target, profile, secret or backup installation is implied.
- AP remains disabled until an accessible corrections-policy readback; no bypass is requested.

**STOP. No fetcher, bot, receiver, job-state directory, Keychain entry, profile, backup, schedule, merge, production deployment, Paperclip interaction or relay modification is authorized by publishing these drafts.**

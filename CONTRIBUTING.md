# Contributing

Uncost is pre-launch. Contributions are welcome as review proposals, but no contributor should represent a draft as adopted, deployed, funded, or operational.

## Useful early contributions

- source and licence review;
- methodology and statistical review;
- privacy, accessibility, nonprofit, safety, and governance review;
- documentation corrections;
- small, testable tooling for source records and reproducible calculations;
- translations after the English source is stable.

## Before opening a pull request

1. Read [docs/CONTROL.md](docs/CONTROL.md) and [REVIEW_STATUS.md](REVIEW_STATUS.md).
2. Keep observed facts, derived values, estimates, and scenarios visibly distinct.
3. Add a source record before adding a public factual claim.
4. Do not include secrets, personal data, internal documents, credentials, legal originals, donor data, or private correspondence.
5. Do not remove policy/safety gates to simplify implementation.
6. Run `python3 scripts/audit_repository.py` and `python3 scripts/audit_website.py`.
7. Explain what changed, the source basis, and what remains unverified.

By contributing, you certify that you have the right to submit the contribution and agree to the repository's applicable licensing terms. Material AI assistance must be disclosed in the pull request.

## Content guardrails and local hooks

Public git history is permanent: prohibited or stale content pushed "temporarily" persists in history forever, so the content audits must pass before commit and push, not only in CI.

1. Enable the committed hooks once per clone: `sh scripts/setup-hooks.sh`. This points `core.hooksPath` at `.githooks/`, so both audits run on every commit and every push.
2. `scripts/audit_website.py` scans `website/`, `sectors/`, `policies/`, and `projects/` (and, with `--built DIR`, built HTML output before deployment). Failure rules exit non-zero. Figure rules — dollar amounts, percentages, and large counts without a `SRC-###` citation on the same line or a `data-source` ancestor element — only warn, for human review.
3. Every finding prints its rule id, file, line, and excerpt; in CI the same findings appear as pull-request annotations and in the job summary.

### Exceptions

A legitimate use of restricted vocabulary (for example, a policy sentence that prohibits the mechanism it names) is recorded in `scripts/audit-website-allowlist.json`, keyed by rule id, file, and the SHA-256 of the exact line — any edit to the line invalidates the exception.

1. Run `python3 scripts/audit_website.py` and note the finding's rule id, file, and line number.
2. Record it with a written justification: `python3 scripts/audit_website.py --allowlist-add RULE PATH LINE "why this use is legitimate"`.
3. Commit the allowlist change in the same pull request as the content that needs it; the entry is reviewed like any other change and stands or falls with founder review at merge.

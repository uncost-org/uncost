# Security policy

## Reporting

Please do not open a public issue for a vulnerability, exposed credential, personal-data leak, or safeguarding concern. Use GitHub's private vulnerability reporting / Security Advisory flow for this repository.

Include the affected path or component, reproduction details, likely impact, and any safe mitigation you have identified. Do not access or retain more data than necessary to demonstrate the issue.

## Scope

This repository currently contains public documentation, draft project material, and the source of the static website (`website/`). Access-gated preview deployments of pull-request builds are founder-authorized (2026-07-19): previews must be served behind Cloudflare Access, are deployed with a robots-disallow and noindex posture, carry no forms or data collection, and serve no production domain. Public launch of the static site — the build from `main`, served at uncost.org with forms, donations and data collection off — is authorized by [CHG-004](records/changes/CHG-004-public-soft-launch.md), from the date that record gives (founder to confirm). Everything else remains not authorized by this repository state: any other production deployment, DNS and email changes beyond serving that site, data systems, forms, pledge collection, donations, the signature counter and founding signers, and community systems including the Assembly.

Security reports do not authorize testing against production services, third parties, or personal data.

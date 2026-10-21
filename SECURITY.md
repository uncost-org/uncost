# Security policy

## Reporting

Please do not open a public issue for a vulnerability, exposed credential, personal-data leak, or safeguarding concern. Use GitHub's private vulnerability reporting / Security Advisory flow for this repository.

Include the affected path or component, reproduction details, likely impact, and any safe mitigation you have identified. Do not access or retain more data than necessary to demonstrate the issue.

## Scope

This repository currently contains public documentation, draft project material, and the source of the static website (`website/`). Access-gated preview deployments of pull-request builds are founder-authorized (2026-07-19): previews must be served behind Cloudflare Access, are deployed with a robots-disallow and noindex posture, carry no forms or data collection, and serve no production domain. Public launch of the static site — the build from `main`, served at uncost.org with forms, donations and data collection off — is authorized by [CHG-004](records/changes/CHG-004-public-soft-launch.md), from 2026-10-19. The contact form alone is authorized by [CHG-005](records/changes/CHG-005-contact-form.md), an amendment to CHG-004: it emails a message to the founder inbox through a Cloudflare Pages Function and Worker and stores nothing. The Pledge and email updates sign-ups are built under [CHG-009](records/changes/CHG-009-signups.md) and are **off**: their handlers (`website/functions/api/signup/`) answer 404 unless the Pages environment sets `UNCOST_SIGNUPS_OPEN=on` and binds the `SIGNUPS` Worker (`uncost-signups`, in the private repository uncost-org/uncost-api), and the forms render only in a build with `UNCOST_FORMS_OPEN=on`. Turning them on in production is a founder decision CHG-009 leaves open. Everything else remains not authorized by this repository state: any other production deployment, DNS and email changes beyond serving that site, data systems other than the switched-off sign-ups, pledge collection, donations, the signature counter and founding signers, and community systems including the Assembly.

Security reports do not authorize testing against production services, third parties, or personal data.

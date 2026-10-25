# Sources and receipts

Every public factual figure should resolve to a `SRC-###` record containing:

- publisher and title;
- stable URL or public identifier;
- publication and last-checked dates;
- region and units;
- licence / republication terms;
- collection or calculation method;
- confidence (`confirmed`, `estimate`, `derived`, `scenario`, or `needs refresh`);
- refresh cadence;
- corrections or limitations;
- sector (`sector`, the column after `region`): the slug of the sector dossier the figure belongs to — `food`, `water`, `shelter`, `energy`, `healthcare`, `care`, `education`, `transportation`, `clothing`, `goods`, `materials`, `communication`, `safety`, `environment` or `leisure` — or empty when the figure is not one sector's cost (governance, wealth and ownership, all-items CPI). A figure card with a sector shows a SECTOR chip linking that dossier; the site build fails on any value that is not one of those slugs.
- Friday review attribution (`checked_by`, the register's last column): blank, or exactly `agent-checked, human-approved: Matt <UTC approval timestamp>`, for example `agent-checked, human-approved: Matt 2026-10-31T02:14:07Z` (fractional seconds are allowed, as in `…:07.123Z`). Only a Friday review card that Matt approved writes it ([`docs/FRIDAY_REVIEW.md`](../docs/FRIDAY_REVIEW.md)), with the UTC time of that approval. Blank means the row has not been approved through the Friday review. Every row that predates the column is blank, and none is filled in retroactively. The value contains a comma, so it is always a quoted CSV cell. The site build fails on any other value, and the site does not show it yet.

The control plan is registered for governance provenance, not as evidence for a public cost figure. The initial cost-source library has not yet been reviewed or published.

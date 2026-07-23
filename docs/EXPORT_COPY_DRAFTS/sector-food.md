# sector-food

- **route note:** sector detail
- **export page:** project/site/sectors/food.html
- **dossier:** sectors/SEC-001-food.md
- **purpose:** The Food sector detail page — tells a reader what the Food sector covers, where AI and robotics could reduce cost, the guardrail on those claims, the honest evidence status (no figures yet), a worked example of how a food cost gets "uncosted," the related projects, and the source register.

---

## Sector head

> DOSSIER-BACKED: SEC-001 title + Includes ("Nutrition, farming, storage, cooking, and distribution.") + Roadmap status (Focus) + dossier ID

Food.

Nutrition, farming, storage, cooking, and distribution.

Sector 01 / 15 · Focus · Dossier SEC-001
(Note: "01 / 15" matches the fixed 15-sector canon and "Focus" matches SEC-001 roadmap status — no divergence.)

---

## Scope

> DESIGN-AUTHORED (no source)

01 · Scope, opportunity, guardrail

Where automation could bite — and what stays visible.

> DOSSIER-BACKED: SEC-001 Includes / Opportunity / Guardrail (three cards map 1:1 to the dossier fields)

What it includes — Nutrition, farming, storage, cooking, and distribution.

The opportunity — AI-managed greenhouses, robotic farming, aquaponics, automated storage, and local production planning.

The guardrail — Count energy, capital, maintenance, food safety, and local conditions — and publish negative results.

> DOSSIER-BACKED: SEC-001 Roadmap status (Focus); "three first-phase sectors, with Shelter and Energy" derives from MOVEMENT_PLAN.md ("Shelter, Food, and Energy are the first deep focus")

Roadmap status: Focus — one of the three first-phase sectors, with Shelter and Energy. Status is sequencing, not importance.

---

## Evidence status

> DESIGN-AUTHORED (no source)

02 · Evidence status

No number ships without a receipt.

> DOSSIER-BACKED: SEC-001 Evidence status ("No public quantitative claim is registered in this dossier yet.") — first sentence verbatim; the rest of the paragraph describing the receipt schema is not in the dossier

No public quantitative claim is registered in this dossier yet.

> DESIGN-AUTHORED (no source)

Reviewed source records come before figures. When the first Food figures publish, each line will carry: value, unit, region, date observed, a source ID from the public register, a confidence label, and the collection method.

> DESIGN-AUTHORED (no source)

Confidence labels: Confirmed · Estimate · Scenario · Needs refresh

> DESIGN-AUTHORED (no source)

Register: sources/register.csv — public on GitHub · Checked July 19, 2026
⚠ REPO-VERIFIABLE (sources/register.csv last_checked): "Checked July 19, 2026" — asserts a register-review date; no review record is cited, and page was captured 2026-07-23.

---

## Worked example

> DESIGN-AUTHORED (no source) — illustrative scenario. Step verbs (Measure / Publish / Break down / Match / Package / Track) mirror MOVEMENT_PLAN.md "How a cost gets uncosted," but every concrete food/produce specific below is invented for the example and is not in SEC-001 (which registers no quantitative claim). This block is the archetype the founder flagged for uncited-claim review.

03 · How food gets uncosted

The worked example: fresh produce in a confined urban space.

1. Measure the cost pressure — Regional data shows what a household spends on fresh produce — and how much of that cost is transport, spoilage, and seasonal scarcity.
⚠ UNCITED: that a household's fresh-produce cost decomposes into "transport, spoilage, and seasonal scarcity" — no regional data source, region, date, or method cited.

2. Publish the sources — Sources and assumptions are posted openly so anyone can check them.

3. Break down the cost — The cost is split into land, energy, labor, water, and logistics.
⚠ UNCITED: the cost-stack components "land, energy, labor, water, and logistics" for fresh produce — asserted with no source or method.

4. Match mechanisms to components — A controlled-environment farm uses AI to manage climate, lighting, and nutrients, and robotics to plant, tend, and harvest — potentially cutting labor, transport, spoilage, and seasonal price swings.
⚠ UNCITED: that a controlled-environment farm "potentially cutting labor, transport, spoilage, and seasonal price swings" — a reduction claim with no evidence, figure, or source.

5. Package the playbook — Uncost publishes the open model, the sources, a project brief, and an automation playbook. Uncost does not own the farm; a community group, co-op, school, or nonprofit runs it.

6. Track the result — The dashboard follows whether produce costs actually fall where the model is applied. Where energy, capital, and maintenance mean automation does not beat conventional supply, that negative result is published too.
⚠ UNCITED: implicit factual premise that automation may "not beat conventional supply" once energy/capital/maintenance are counted — stated as scenario, no data cited (consistent with the guardrail, but no receipt).

---

## Guardrail callout

> DOSSIER-BACKED: SEC-001 Guardrail (quoted; export uses a comma before "food safety" and a semicolon before "publish negative results" — matches dossier punctuation)

"Count energy, capital, maintenance, food safety, and local conditions; publish negative results."

— The Food guardrail · dossier SEC-001

---

## Related projects

> DESIGN-AUTHORED (no source) — SEC-001 has no projects section; project names, roles, and summaries below are authored for the site, not drawn from the dossier or MOVEMENT_PLAN.md.

04 · Related projects

Where Food shows up in The Projects.

> DESIGN-AUTHORED (no source) — the "three focus sectors at launch" phrasing derives from MOVEMENT_PLAN.md; the project entries themselves are design-authored.

PRJ-001 — Human Essentials Dashboard — Presents what food costs by region, with sources and history — Food is one of the three focus sectors at launch. Role for Food: Presentation layer. Status: Draft — not approved for build.

PRJ-002 — Cost-of-Living Tracker — Supplies the food price data: sourced, dated, licensed, and refreshed on a published schedule. Role for Food: Data layer. Status: Draft — not approved for build.

PRJ-003 — Basic Needs Cost Model — Tests where automation can genuinely reduce food costs — including the worked produce scenario with real regional numbers. Role for Food: Scenario layer. Status: Draft — not approved for build.
⚠ UNCITED: "with real regional numbers" — asserts real regional numbers exist for the worked scenario; SEC-001 registers no quantitative claim, so none are cited.

---

## Sources

> DESIGN-AUTHORED (no source)

05 · Sources

The register comes before the figures.

> DESIGN-AUTHORED (no source)

Every source Uncost uses gets a public ID, publisher, date, license, refresh cadence, and region coverage. The Food dossier draws on the register as reviewed records are added.

> DOSSIER-BACKED: derives from the controlling-source register, but the citation is stale

SRC-001 — Uncost final external Movement Plan and Roadmap — Governance-control source · 2026-07-15 · confidence: confirmed
⚠ SUPERSEDED SOURCE: cites the 2026-07-15 plan edition (SHA `5b99100e…`). Per docs/CONTROL.md the controlling source is the July 2026 edition declared final 2026-07-18 (SHA `a2b64021…`), which supersedes 2026-07-15; documents on the old hash carry a `source_superseded_by_sha256` marker until re-reviewed.
⚠ DIVERGES FROM JULY SOURCE: the link text names the "Movement Plan and Roadmap" but the href points to `sources/register.csv` (the source register CSV, not the plan); the register is not the plan — source wins.

> DESIGN-AUTHORED (no source)

Sector-specific source records are added with review. Propose a source on GitHub. Official statistics first · licenses recorded at intake.

---

## Related sectors

> DESIGN-AUTHORED (no source) — in-page cross-links, not dossier content.

Related sectors — Keep reading.

Water · Shelter · Energy · All 15 sectors →

---

## Sector CTA

> DESIGN-AUTHORED (no source)

Help build the food evidence. Sources before slogans.

Early useful roles: source and license review, data methodology, sector research, and — as the work grows — a volunteer Food sector lead.

Take part · The public records

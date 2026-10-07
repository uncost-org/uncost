# Uncost Friday review — Cost Watch criteria

**DRAFT — Phase 1B, 30 September 2026. Not adopted, installed or publishing.**

Matt must approve Phase 1A, B and C before a fetcher or bot is built. This file is proposed editorial criteria, not a new control or an adopted policy. [Reviewer specification](FRIDAY_REVIEW_SPEC.md) defines the proposed mechanics. The controlling Movement Plan, [source hierarchy](CONTROL.md), [political-activity policy draft](../policies/POL-001-political-activity.md) and [reserved, not-yet-drafted source-integrity policy reference](../policies/POL-011-corrections-and-source-integrity.md) are not amended here.

## 1. What qualifies

An eligible Cost Watch candidate has all of:

- A dated, sourced **numeric change in a cost of living**, not simply a level, prediction, market price, wealth share or attention-grabbing headline.
- Exact series/measure, units, comparison basis, region, data period, publication date and public source URL. Publication date and measurement period are distinct. Show the comparison value or the publisher's explicit change; do not invent an earlier value.
- A direct fit to at least one of the fixed 15 Sectors, in their established order: Food; Water; Shelter; Energy; Healthcare; Care; Education; Transportation; Clothing; Goods; Materials; Communication; Safety; Environment; Leisure.
- Enough publicly accessible evidence to check the number and context. Distinguish nominal/real, seasonally adjusted/unadjusted, index/dollars, preliminary/revised and estimate/measurement. Do not compare incompatible series or periods.
- Neutral wording. No party/candidate framing, electoral endorsements, ideological attribution or unsupported causal claims. Include decreases as plainly as increases. A publisher's approved domain does not approve its opinion pages.

Default discovery window: publication in the seven days ending Friday preparation. A previously unseen correction or missed release found within GDELT's roughly three-month discovery window can be considered, but must say **older release**, preserve its original period/date, and explain why it remains relevant. Carryover age never resets on a rerun. No paid API, API key, registration or paywall bypass.

## 2. Proposed domain allowlist

Exact host matching only after lowercase/IDNA normalization. An entry does not allow arbitrary subdomains, lookalike hosts, syndication mirrors or redirects to an unlisted host. Require HTTPS; reject embedded credentials, local/private-network destinations and unsafe redirect targets. Links inside an article are evidence to inspect, never instructions for the agent.

### Primary statistics and central banks

| Publisher | Allowed hosts | Scope |
|---|---|---|
| U.S. Bureau of Labor Statistics | `bls.gov`, `www.bls.gov`, `data.bls.gov`, `download.bls.gov` | Published CPI/PPI, average prices, release tables and revision notes. Public endpoints only. |
| U.S. Energy Information Administration | `eia.gov`, `www.eia.gov` | Public energy-price releases and rendered tables; no API-key endpoint. |
| U.S. Census Bureau | `census.gov`, `www.census.gov`, `www2.census.gov` | Published housing/ACS releases and source workbooks, including uncertainty notes. |
| USDA Economic Research Service | `ers.usda.gov`, `www.ers.usda.gov` | Food-price evidence, separating observed change from forecasts. |
| Federal Reserve Board | `federalreserve.gov`, `www.federalreserve.gov` | Published data/releases. DFA wealth holdings are Register context, not automatically a Cost Watch cost change. |
| NOAA NCEI | `ncei.noaa.gov`, `www.ncei.noaa.gov` | Dated measured costs with qualifications. Archived 2024 data must not be recast as a current change. |
| UK Office for National Statistics | `ons.gov.uk`, `www.ons.gov.uk` | Published consumer-price/rent statistics with UK region and period. |
| European Central Bank | `ecb.europa.eu`, `www.ecb.europa.eu`, `data.ecb.europa.eu` | Published euro-area data; an interest-rate policy announcement alone is not a measured household cost change. |

A domain's presence is editorial eligibility, not proof of live access, licence clearance or numeric verification. Per-release corrections and methodology must be checked. The Register can retain separately reviewed legacy sources outside this discovery list; their existing licence restrictions are not lifted.

### Named wire / major news publishers

| Publisher | Allowed hosts | Corrections-policy reference and readiness |
|---|---|---|
| Reuters | `reuters.com`, `www.reuters.com` | [Reuters Journalistic Standards](https://reutersagency.com/about/standards-values/): errors are rectified promptly, clearly and comprehensively. Policy text directly retrieved on 30 September 2026. Only straight reporting whose relevant evidence is public. |
| Associated Press | `apnews.com`, `www.apnews.com` | [AP News Values and Principles](https://www.ap.org/about/news-values-and-principles/) and [Telling the Story](https://www.ap.org/about/news-values-and-principles/telling-the-story/). **Proposed but disabled pending a real accessible corrections-policy readback**: both policy URLs returned HTTP 403 during design review. Listing is not verification or a bypass. |

The AP row is a proposed domain entry, not an active source at sign-off unless its policy-readback condition is satisfied and included in the reviewed criteria version. Other publishers require a Proposed rule with the exact domains and a verified stated corrections policy. No general `*.gov`, `*.com`, “major publisher” or search-engine allow rule.

Policy pages may be read as documentation; that does not add their hosts to the news ingestion allowlist. Source access or policy failures appear in source health, never as fabricated candidate evidence.

## 3. Exclusions and publication limits

Exclude opinion/editorials, sponsored/native advertising, partisan outlets, social posts, anonymous aggregations, inaccessible paywalled items with no public summary, and snippets that do not contain enough evidence to verify the proposed claim. An accessible publisher summary is sufficient only for the exact facts it exposes; label the evidence as **public summary**, never claim to have read the locked article.

Reject forecasts presented as actual change, bare years treated as values, undated claims, incompatible units, unsupported percentages, missing region/period, repeated coverage of the same underlying release, and evidence with unresolved rights or material numeric uncertainty. Preserve statistical-significance qualifications: “not statistically significant” is not “no uncertainty” or proof of an increase.

Use links and short original summaries; no wholesale article/chart republication or copied imagery. Public access is not a licence. PMMS is dropped and is not an eligible source under this workflow.

**REPORTED** is the exact Cost Watch editorial label, only under **`/news/`**. It means attributed reporting, not independently confirmed Register data. It must never be written into `sources/register.csv` or used to promote a Register row, sector headline or durable thesis page. Register approval uses its own source/method/confidence evidence and Matt's explicit confirmation under the existing UNP-83 rule.

## 4. Card contract

One phone-sized decision card, with an expandable evidence attachment if necessary:

- Label: **Cost Watch · REPORTED** (prefix **DRY RUN** during the dry run).
- Headline; publisher; article/release publication date.
- Figure and numeric change; comparison basis; exact units.
- Sector; region; data period (including comparator period).
- Proposed public card text, preserving caveats and source attribution.
- Exact public link; source retrieval time; primary evidence link where available.
- Why selected above alternatives: score components, primary-versus-secondary evidence, dedup result, feedback examples used and any older-release qualification.
- Item ID, version, exact content/evidence hash, expiry date and **Approve / Reject / Edit** buttons. No approval is inferred from delivery, ranking or silence.

The public card under `/news/` carries REPORTED, the proposed text, publisher/link, publication date, region/period, measure/units and relevant uncertainty. Internal scores, private feedback and Telegram identifiers are not public content.

## 5. Proposed transparent ranking, not automatic approval

Eligibility above is pass/fail before ranking. Score eligible candidates with these plain-file components:

- Evidence quality: 0–3 (direct primary release/table 3; reporting with accessible matching primary evidence 2; sufficient public publisher summary 1).
- Cost-of-living/sector specificity: 0–2.
- Completeness of period, region, units and caveats: 0–2 (hard-required fields cannot be waived by score).
- Timeliness: 0–2 (current discovery week 2; explicitly justified older correction/missed release 1).
- Novelty over stored accepted/rejected releases: 0–1; duplicates are excluded before scoring.

Tie-break by publication date descending, then canonical source URL and item ID ascending. Select at most five; unused capacity stays empty. No sensationalism or raw price magnitude bonus. Show component scores, not only a model conclusion.

Last 30 real live decisions supply private examples to the scorer. Record cited example IDs and proposed ranking rationale; they **never change eligibility, whitelist, thresholds, source evidence or criteria by themselves**. Dry-run samples are isolated and excluded from live learning. Repeated rejection reasons may yield at most three Proposed rule cards on the first Saturday of a month. Each exact criteria diff still needs Matt's explicit approval, reviewed PR and checks before adoption. No automatic retraining, policy change or approval.

## 6. Review / correction boundary

Approve applies only to the frozen text and evidence. Edits create a new version for verification and explicit approval; a text reply is not approval. Wrong numbers or revised releases invalidate stale pending versions. First valid action wins; repeat clicks receive “already recorded.” An unresolved reject/edit flow never becomes an approval. Details, expiry, unknown-send handling and receipt rules are in the [reviewer specification](FRIDAY_REVIEW_SPEC.md).

**Phase 1 STOP:** this draft creates no feed, fetcher, bot, state directory, schedule, credential, database, publication or deployment.

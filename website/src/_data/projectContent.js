// Approved public-facing copy for the seven project dossiers (PRJ-001–007).
//
// AUTHORITY: UNP-82 content pass v1 §5, approved by the founder. The words here
// are content-owned and wired verbatim; only typography was normalised (straight
// quotes → curly, the single markdown emphasis → <em>). Same pattern as
// _data/sectorContent.js: authored copy lives in the data layer so the template
// names a field rather than carrying prose, and so a dossier rewrite in
// projects/PRJ-00N-*.md cannot silently overwrite reviewed public copy.
//
// The template renders these with `| safe` because they carry one <em>. That is
// sound only while the copy contains no other raw markup, which the guard below
// enforces at build time — a stray "<", ">" or bare "&" fails the build rather
// than reaching a page.
//
// Stage labels are NOT set here: every dossier is `status: draft`, so the
// template renders "Draft — not approved for build" for all seven. The design
// export's "In development" was dropped as unsupported by the dossiers.

const CONTENT = {
  "PRJ-001": {
    // P6-copy: founder-approved opener for the "At a glance" section.
    opener: {
      eyebrow: "What you\u2019ll see",
      h2: "The picture, region by region.",
      intro: "The Dashboard is the presentation layer: what one adult needs, what it costs where you live, and whether that cost is moving \u2014 every figure with its receipt.",
    },
    publicSummary: "The public, regional picture of what one human needs and what those needs cost — the flagship of The Case.",
    atAGlance: {
      targets: "The essentials basket for one adult, region by region, honestly mapped to the fifteen sectors — with three of them (Environment, Safety, Materials) treated as cost <em>drivers</em> layered across the basket, not basket line-items themselves.",
      mechanism: "Presents the Cost-of-Living Tracker’s sourced price data and the Basic Needs Cost Model’s scenarios in one public view, with a plain coverage banner (“data available for N of M regions” — N is whatever is real) instead of a false single national number.",
      costPath: "It doesn’t lower a cost by itself. It’s the presentation layer: it shows a reader exactly where money goes and which of the other two projects’ reduction paths look real, so the movement’s public case rests on the same evidence it publishes.",
    },
    overview: "The dashboard exists because arguing about the cost of living with vibes and headlines gets nobody anywhere. It replaces that with sourced, dated, regional numbers, tracked over time so anyone can see whether a gap is actually closing. Early versions cover only a handful of launch regions and say so plainly, expanding from there — never faking national coverage to look more finished than it is.",
    relatedSectors: "Shelter, Food, Energy (primary — the year-one focus). Water, Transportation, Communication, Healthcare next (Healthcare appears only as a measured cost line, not as a claim about the sector itself).",
    support: "engineering, data methodology, and source-review volunteers; in-kind compute or model access.",
    cta: "Help build the first regional view.",
  },
  "PRJ-002": {
    // P6-copy: founder-approved opener for the "At a glance" section.
    opener: {
      eyebrow: "What feeds it",
      h2: "The data underneath.",
      intro: "The Tracker is the data layer: sourced, dated, licensed prices, refreshed on a published schedule. The Dashboard reads from it.",
    },
    publicSummary: "The sourced, dated price data that everything else in The Case stands on.",
    atAGlance: {
      targets: "A disciplined register of prices and their sources. It has no public page of its own — its product is trustworthy data, not a dashboard.",
      mechanism: "Official-statistics-first sourcing: national statistical agencies and regulators first, licensed commercial indices only where irreplaceable. Every source is logged with its licence, region coverage, and refresh cadence, and auto-flags “needs refresh” once it goes stale.",
      costPath: "Removes the recurring cost of re-finding and re-verifying data. Done once, licensed properly, and published openly, so the rest of the movement — and outside researchers — can reuse it instead of re-scraping the same numbers.",
    },
    overview: "Without a disciplined tracker, the dashboard becomes screenshots of other people’s numbers — undated, unlicensed, unmaintainable. This project is not a scraper farm; official and licensed sources come first, and anything whose licence forbids republication is marked and linked out to rather than reproduced.",
    relatedSectors: "Shelter, Food, Energy (primary). Water, Transportation, Communication, Healthcare (secondary — cost lines only).",
    support: "data engineering, source and licence review, and public-data partnerships.",
    cta: "Help keep the register honest.",
  },
  "PRJ-003": {
    publicSummary: "The math behind every claim that automation could lower a specific cost — including when it can’t.",
    atAGlance: {
      targets: "Breaking a cost into its real components (labor, energy, land, materials, waste, market structure, financing, fees, policy) so a reduction claim can be checked, not just asserted.",
      mechanism: "A published cost-stack decomposition plus an intervention library, run as reproducible scenarios with stated assumptions and a sensitivity note — never a single-number promise.",
      costPath: "It doesn’t lower a cost directly. It tells the movement, and anyone else, which components of a cost automation can plausibly address, by roughly how much, and under which assumptions — and it publishes that just as loudly when the honest answer is “this doesn’t beat the status quo.”",
    },
    overview: "This is where the movement’s core claim gets tested rather than assumed. Every scenario is reproducible by an outsider from its published inputs, and negative results are published with the same prominence as wins — including, if it happens, on the movement’s own flagship claim.",
    relatedSectors: "Shelter, Food, Energy only — no secondary sectors at MVP; scenario modelling is expensive to do honestly, and depth beats coverage.",
    support: "modelling and economics expertise; peer reviewers willing to stress-test assumptions.",
    cta: "Help stress-test the assumptions.",
  },
  "PRJ-004": {
    publicSummary: "A decision-support comparison for a community that already exists, weighing real intervention options side by side.",
    atAGlance: {
      targets: "An existing community’s real context — size, region, existing assets — compared against candidate interventions drawn from the Basic Needs Cost Model’s library.",
      mechanism: "Guided intake plus three intervention modules (shared solar and storage, a tool library, community food growing), producing range-based comparisons with assumptions shown. A hard rule blocks any output from rendering a single “you will save $X” figure.",
      costPath: "Cuts the weeks of bespoke feasibility guesswork a community group faces before it can even decide whether commissioning a real feasibility study is worth it.",
    },
    overview: "Distinct from the Basic Needs Planner below: the Simulator compares options for a place that already exists; the Planner drafts requirements for one that doesn’t exist yet. Every output carries a structural disclaimer that it is not an engineering assessment, permit, or substitute for licensed professionals.",
    relatedSectors: "Energy, Food, Goods (primary — the three with the most community-runnable interventions). Water, Materials (secondary).",
    support: "community pilot partners, module engineering, and facilitation for pilot runs.",
    cta: "Help run a pilot with your community.",
  },
  "PRJ-005": {
    publicSummary: "Documentation and templates for launching a shared-tool library — liability and safety first, because that’s where these projects usually die.",
    atAGlance: {
      targets: "Households that individually own expensive, rarely used equipment, and the groups trying to fix that with a shared library who stall on the unglamorous parts: liability, insurance, governance.",
      mechanism: "A liability and safety pack (waiver templates, insurance guidance by jurisdiction class, incident response, recall monitoring), a governance pack, and an operations pack — reviewed by experienced library-of-things operators and, for the liability guide, counsel, before publication.",
      costPath: "Cuts the setup and risk cost of getting the unglamorous parts right, so a community can share equipment instead of everyone buying their own.",
    },
    overview: "This is a documentation and templates product, not inventory, funding, or insurance itself, and Uncost does not operate the libraries. One pilot partnership with an existing library-of-things is planned before publication — learning from operators who’ve already solved most of this, not reinventing it.",
    relatedSectors: "Goods (primary). Materials — repair, Leisure — recreation equipment libraries as a later template (secondary).",
    support: "experienced library-of-things operators, and legal counsel for the liability guide.",
    cta: "Help review the liability guide.",
  },
  "PRJ-006": {
    publicSummary: "A nonpartisan, pre-registered study of where automation’s gains actually go — and the conditions under which they’ve reached consumer prices.",
    atAGlance: {
      targets: "The movement’s own central claim, tested rather than assumed: that productivity keeps rising while essential costs don’t fall accordingly.",
      mechanism: "Methodology and data sources published before analysis begins; at least two external reviewers with differing economic perspectives, named in the report, sign off before publication.",
      costPath: "It doesn’t lower a cost directly. It’s the evidence base under every other cost-reduction claim the movement makes — including a constructive chapter documenting cases, like solar’s cost curve, where automation gains verifiably did reach prices.",
    },
    overview: "Strictly nonpartisan and education-framed: no policy recommendations in the first report, and the political-activity review applies to the whole study, not just excerpts. If the evidence complicates the movement’s own thesis, that gets published too — the negative-results commitment applies to the flagship narrative as much as to any single scenario.",
    relatedSectors: "Cross-sector by nature, anchored in Shelter, Food, Energy first; Transportation and Goods second.",
    support: "economists and researchers willing to serve as named external reviewers.",
    cta: "Help keep this one honest — reviewers wanted.",
  },
  "PRJ-007": {
    publicSummary: "A requirements-drafting assistant for a proposed site or initiative that doesn’t exist yet — every output a draft for professional review, never an approval.",
    atAGlance: {
      targets: "Groups exploring a community land project, campus, or co-op, before they can even ask professionals the right questions.",
      mechanism: "Guided intake plus a requirements engine, built on the Basic Needs Cost Model’s library and the Community Resource Simulator’s validated modules, that outputs ranges, explicit data gaps, a risk register, and a professional-review checklist. It cannot render a single-number budget or approval language — that’s a hard design rule, not a style choice.",
      costPath: "Cuts the pre-professional planning and documentation labour a group faces early on. It’s also deliberately the only route through which any future integrated demonstration gets scoped, so nothing skips the honest-requirements step.",
    },
    overview: "The planner declines emergency, medical-capacity, and safeguarding-gated scenarios outright, with signposting to appropriate professionals — refusal is designed into the output format itself, not left to good judgment. Distinct from the Community Resource Simulator: this drafts requirements for a place that doesn’t exist yet, rather than comparing options for one that does.",
    relatedSectors: "Food, Water, Shelter, Energy (primary). Transportation, Communication, Safety — resilience framing only (secondary).",
    support: "facilitators and pilot groups considering a real site.",
    cta: "Help pilot a real plan.",
  },
};

// Build-time guard: the copy above is rendered unescaped, so it must contain no
// raw markup beyond the reviewed <em>. Anything else is a build failure.
const ALLOWED_TAG = /<\/?em>/g;
(function guard(node, trail) {
  for (const [key, value] of Object.entries(node)) {
    const where = trail ? `${trail}.${key}` : key;
    if (typeof value === "string") {
      const residue = value.replace(ALLOWED_TAG, "");
      if (/[<>&]/.test(residue)) {
        throw new Error(`projectContent: ${where} contains raw markup`);
      }
    } else {
      guard(value, where);
    }
  }
})(CONTENT, "");

module.exports = CONTENT;

// The drawer (X11, Batch X, 2026-09-27; first shipped as V11's labels drawer).
// ONE partial, partials/labels-drawer.njk, driven by this file: for each page
// a header, THE RULES (a bullet list) and THE LABELS (chip | what it tells
// you). Every string here is founder-approved verbatim from the Batch X brief,
// except the four confidence definitions, which read exactly as they always
// have (the brief: "confidence definitions unchanged").
//
// W40 DEFINITIONS (founder-approved 26 Sep; delivered with Batch X.1 on
// 28 Sep as the missing "Batch W text"). Verbatim, except that each opens
// with a capital because it stands alone in the table's "What it tells you"
// cell (in the brief it followed "Label:"). They replace the two interim
// definitions X10 and X9 had moved in from on-site text.
//
// The news-label guard (eleventy.config.js) still holds: the confidence
// labels appear on no page under /news/, and Reported on none outside it.

// Every label a drawer shows: its chip (the class string the page itself uses
// for it) and its definition, or null.
const LABELS = {
  "Confirmed": { chip: "rcpt-conf rcpt-conf--confirmed",
    definition: "Drawn directly from a named, dated, licensed public source. Check it yourself." },
  "Estimate": { chip: "rcpt-conf rcpt-conf--estimate",
    definition: "Derived from sourced inputs plus stated assumptions. The assumptions are published alongside." },
  "Scenario": { chip: "rcpt-conf rcpt-conf--scenario",
    definition: "A modelled “what if” — a possible outcome under specific conditions, not a prediction." },
  "Needs refresh": { chip: "rcpt-conf rcpt-conf--needs-refresh",
    definition: "The underlying source is past its review date. Treat with caution until updated." },
  // Sectors (W40).
  "Focus": { chip: "status status--focus", definition: "A year-one sector; research and figures are being built now." },
  "Next": { chip: "status s-next", definition: "Queued after the year-one three." },
  "Dossier": { chip: "status s-dossier", definition: "Groundwork only: scope, opportunity and guardrail written, no figures yet." },
  "Future study": { chip: "status s-future", definition: "Study-level only until safety, legal and partner gates pass." },
  // Projects (W40). "In build" is defined in the brief only if the chip is
  // rendered anywhere; it is rendered nowhere (X13 made the homepage chip
  // "Draft"), so it is not listed. "Brief" (the homepage Dashboard card) and
  // "Planned" (join, press, quiz, events and the later pages) are rendered,
  // so they are defined here, though no drawer page carries them today.
  "Draft": { chip: "status status--dev", definition: "A public review draft; nothing is authorised until review completes." },
  "Brief": { chip: "status status--planned", definition: "A written brief; no build yet." },
  "Planned": { chip: "status status--planned", definition: "On the roadmap; not started." },
  // Policies (W40).
  "Draft — not in force": { chip: "status status--dev", definition: "Open for comment; not adopted." },
  "Public review drafts": { chip: "status status--planned", definition: "The whole set is open for comment ahead of launch." },
  // News / Cost Watch (W40).
  "Reported": { chip: "lbl lbl--reported",
    definition: "A price or cost figure as published by the linked source, with its date. Verified figures live in The Receipts." },
  // Treasury (W40).
  "Not yet active": { chip: "status status--planned", definition: "No funds received; reporting begins when donations lawfully open." },
};

// Per page, keyed by URL (/news/ and /news/cost-watch/ share a pageId).
//   id        the drawer's anchor (/receipts/#how-it-works is linked from /case/)
//   summary   the header row
//   rules     THE RULES, in order
//   labels    THE LABELS, in order — exactly the brief's list for the page
//   elsewhere a label the drawer explains although this page does not carry
//             it, and where it is used (the brief: Reported on /news/,
//             "noted as used on Cost Watch")
//   unlisted  chips the page renders that the brief's list leaves out, named
//             so the build guard can tell a known gap from a new one (both are
//             reported to the founder)
const PAGES = {
  "/receipts/": {
    id: "how-it-works",
    summary: "How The Receipts work",
    rules: [
      "Every number has a source, a date and a region.",
      "Every source carries a licence and a review cadence.",
      "A figure past its review date is relabelled Needs refresh rather than quietly left standing.",
      "Estimates and scenarios state their assumptions.",
      "Every change is recorded in the corrections log.",
    ],
    labels: ["Confirmed", "Estimate", "Scenario", "Needs refresh"],
    unlisted: ["No corrections logged yet"],
  },
  "/sectors/": {
    id: "how-sectors-are-sequenced",
    summary: "How sectors are sequenced",
    rules: [
      "All fifteen sectors stay visible — hiding a cost isn’t lowering it.",
      "Status shows sequence, not importance.",
      "Year one goes deep on Shelter, Food and Energy; Water is next.",
      "Healthcare, Care, Education and Safety stay study-level until safety, legal and partner gates pass.",
    ],
    labels: ["Focus", "Next", "Dossier", "Future study"],
  },
  "/projects/": {
    id: "how-projects-are-staged",
    summary: "How projects are staged",
    rules: [
      // W40: the page's rule line, first (it was not among X11's rules).
      "Stage shows how far the build has got, not how strong the evidence is.",
      "Every project has to earn its cost claim with published evidence.",
      "Nothing is built until review completes and funding exists.",
      "Uncost publishes the plans and software; communities and qualified partners build.",
      "Negative results are published as prominently as wins.",
    ],
    labels: ["Draft"],
  },
  "/policies/": {
    id: "how-policies-are-adopted",
    summary: "How policies are adopted",
    rules: [
      "Every policy keeps a permanent reference number.",
      "A change keeps the number and bumps the version, with full history public.",
      // W40's rule line for Policies is "Nothing here is in force until it is
      // adopted."; X11 (a day later) already carries it as this line, one
      // word shorter, so it is treated as present rather than doubled.
      "Nothing is in force until it is adopted.",
      "Legal, fiduciary and safeguarding duties can’t be weakened by popular vote.",
    ],
    labels: ["Draft — not in force", "Public review drafts"],
    unlisted: ["Not yet drafted"],
  },
  "/news/": {
    id: "how-we-publish-news",
    summary: "How we publish news",
    rules: [
      // W40: the News / Cost Watch rule line, first.
      "Cost Watch is a watch list, not a receipt.",
      "Every update is dated.",
      "Updates that aren’t good news are published too.",
      "Corrections are logged, never edited silently.",
      "Prices in the news live on Cost Watch.",
    ],
    labels: ["Reported"],
    elsewhere: { "Reported": { name: "Cost Watch", href: "/news/cost-watch/" } },
  },
  "/news/cost-watch/": {
    id: "how-cost-watch-works",
    summary: "How Cost Watch works",
    rules: [
      // W40: the News / Cost Watch rule line, first.
      "Cost Watch is a watch list, not a receipt.",
      "Every item links to its publisher, with its date.",
      "Every item carries a price or cost figure.",
      "Reported figures aren’t receipts; a figure we verify moves to The Receipts.",
      "Opinion pieces aren’t included.",
    ],
    labels: ["Reported"],
  },
  "/treasury/": {
    id: "how-the-treasury-will-report",
    summary: "How The Treasury will report",
    rules: [
      "No donations until a lawful structure is confirmed.",
      "Donations never buy conclusions, coverage, votes or influence.",
      "Every expense keeps a receipt and approval trail.",
      "Reports are summarised, with donor identities protected and totals preserved.",
    ],
    labels: ["Not yet active"],
  },
};

// The column headings, from the brief ("THE RULES", "THE LABELS"; the drawer's
// heading style sets the capitals), the table's column heads (the retired
// /receipts/ table's own), and the /news/ note's lead-in ("noted as used on
// Cost Watch" — the brief names the note, not its words beyond these).
const HEADINGS = { rules: "The rules", labels: "The labels", label: "Label", meaning: "What it tells you", usedOn: "Used on" };

// Build-time guards: every page names only labels that exist, and has rules.
for (const [url, page] of Object.entries(PAGES)) {
  for (const name of page.labels) {
    if (!LABELS[name]) throw new Error(`labels: ${url} lists unknown label "${name}"`);
  }
  if (!page.rules || !page.rules.length) throw new Error(`labels: ${url} has no rules`);
  // The table shows its "What it tells you" column only where at least one
  // label on the page has an approved definition.
  page.hasDefinitions = page.labels.some((name) => Boolean(LABELS[name].definition));
}

module.exports = { labels: LABELS, pages: PAGES, headings: HEADINGS };

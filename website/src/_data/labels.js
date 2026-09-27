// The labels drawer (V11, Batch V, 2026-09-26) — one partial,
// partials/labels-drawer.njk, driven by this file.
//
// FAMILIES are the site's label vocabularies. PAGES says which families each
// drawer shows: exactly the families that page renders, and no others. The
// two vocabularies the news-label guard in eleventy.config.js keeps apart stay
// apart here too — the confidence labels never appear under /news/, and
// Reported appears nowhere else.
//
// WORDS. Only the four confidence labels carry definitions, and they read
// exactly as the retired "Four honest labels" table on /receipts/ read them,
// with that section's approved confidence-vs-status note (UNP-82). Every other
// family renders its label names only: `title: null` and no `definition`
// until the founder's approved glossary text arrives, and a null renders
// nothing. The one title that does render, "Confidence labels", is the
// heading the /case/ Methodology drawer already uses for the same four.
// Nothing in this file is new copy; the names are the chips' own rendered
// text, and each `chip` is the class string the page already uses for it.
//
// A page listed with no families (/news/: its updates carry no label) renders
// no drawer at all rather than an empty one.

const FAMILIES = {
  confidence: {
    title: "Confidence labels",
    columns: ["Label", "What it tells you"],
    labels: [
      { name: "Confirmed", chip: "rcpt-conf rcpt-conf--confirmed",
        definition: "Drawn directly from a named, dated, licensed public source. Check it yourself." },
      { name: "Estimate", chip: "rcpt-conf rcpt-conf--estimate",
        definition: "Derived from sourced inputs plus stated assumptions. The assumptions are published alongside." },
      { name: "Scenario", chip: "rcpt-conf rcpt-conf--scenario",
        definition: "A modelled “what if” — a possible outcome under specific conditions, not a prediction." },
      { name: "Needs refresh", chip: "rcpt-conf rcpt-conf--needs-refresh",
        definition: "The underlying source is past its review date. Treat with caution until updated." },
    ],
    // UNP-82, founder-approved; moved here from the retired /receipts/ section.
    note: "These four labels describe how much confidence a <b>figure</b> carries. They are a deliberately separate system from the status badges on sectors and projects, which describe what stage a <b>piece of work</b> is at. The two never mix: a confirmed figure can sit on a project that hasn’t started, and a project already building can rest on an estimate.",
  },
  // The hatched "Illustrative only" marker. No page carries it today — its one
  // appearance was the specimen in the retired /receipts/ table — so no drawer
  // lists it (the build guard would fail one that did). Kept so the marker has
  // a family the day a page uses it.
  illustrative: {
    title: null,
    labels: [{ name: "Illustrative only", chip: "rcpt-illus" }],
  },
  corrections: {
    title: null,
    labels: [{ name: "No corrections logged yet", chip: "status status--planned" }],
  },
  sectorStatus: {
    title: null,
    labels: [
      { name: "Focus", chip: "status status--focus" },
      { name: "Next", chip: "status s-next" },
      { name: "Future study", chip: "status s-future" },
      { name: "Dossier", chip: "status s-dossier" },
    ],
  },
  projectStatus: {
    title: null,
    labels: [
      { name: "Draft", chip: "status status--dev" },
      { name: "Not approved for build", chip: "status status--planned" },
    ],
  },
  policyStatus: {
    title: null,
    labels: [
      { name: "Draft — not in force", chip: "status status--dev" },
      { name: "Not yet drafted", chip: "status status--planned" },
      { name: "Public review drafts", chip: "status status--planned" },
    ],
  },
  treasuryStatus: {
    title: null,
    labels: [{ name: "Not yet active", chip: "status status--planned" }],
  },
  news: {
    title: null,
    labels: [{ name: "Reported", chip: "lbl lbl--reported" }],
  },
};

// Keyed by page URL. /news/ and /news/cost-watch/ share a pageId, so the URL
// is the only key that tells them apart.
const PAGES = {
  "/receipts/": ["confidence", "corrections"],
  "/projects/": ["projectStatus"],
  "/policies/": ["policyStatus"],
  "/sectors/": ["sectorStatus"],
  "/news/": [],
  "/news/cost-watch/": ["news"],
  "/treasury/": ["treasuryStatus"],
};

// Build-time guards. The note renders unescaped for its two <b>s, so it may
// carry no other markup; every page must name only families that exist; and a
// family without a title or definitions must really be names-only.
for (const [key, fam] of Object.entries(FAMILIES)) {
  if (fam.note && /[<>&]/.test(fam.note.replace(/<\/?b>/g, ""))) {
    throw new Error(`labels: ${key}.note contains raw markup beyond <b>`);
  }
  if (key !== "confidence" && (fam.title || fam.labels.some((l) => l.definition))) {
    throw new Error(`labels: ${key} carries words beyond label names before the glossary is approved`);
  }
}
for (const [url, keys] of Object.entries(PAGES)) {
  for (const k of keys) {
    if (!FAMILIES[k]) throw new Error(`labels: ${url} names unknown family "${k}"`);
  }
}

// The drawer's own name, from the brief's item title ("V11 — Labels drawer").
// It is the one string here that did not already render on the site.
const SUMMARY = "Labels";

module.exports = { summary: SUMMARY, families: FAMILIES, pages: PAGES };

// Seed News items — the three founder-approved movement updates, published on
// 2026-08-01 (ICT). Rendered on /news (Movement updates) and in /news/feed.xml.
// These are movement updates, not the curated "Cost Watch" of external reporting.
// pubDate is RFC-822 for the RSS feed; date is the human label.
//
// C3 (sweep 2026-10-10): every item carries exactly one `label` from the news
// vocabulary (C2) — Update, Perspective or Correction — rendered as a chip on
// the item's date row (partials/news-cards.njk) and as the feed item's
// <category>. The vocabulary is defined in _data/labels.js; the check at the
// end of this file fails the build if an item has no label, or one that is not
// in the vocabulary, or the vocabulary's chip class stops matching the one the
// card renders.
const NEWS_LABELS = ["Update", "Perspective", "Correction"];

const items = [
  {
    slug: "an-open-letter",
    // The "Perspectives: " prefix went with C3: the chip now says it.
    title: "An open letter",
    label: "Perspective",
    date: "1 August 2026",
    dateISO: "2026-08-01",
    pubDate: "Sat, 01 Aug 2026 09:00:00 +0700",
    body:
      "Living should not have a price tag. That sentence is the whole argument, and this letter is where it starts. We produce more than any generation in history — more food, more housing capacity, more energy — with less human effort than ever. And yet for most people, the essentials keep getting more expensive. Uncost exists to close that gap deliberately: measure what living actually costs, publish every source, find where AI, robotics and shared infrastructure could bring costs down, and give the results away. This site is the beginning of that work, in public, with the receipts showing. Read The Case, look at The Sectors, and if you think it’s worth testing — add your name when sign-ups open.",
  },
  {
    slug: "the-repository-is-public",
    title: "The repository is public",
    label: "Update",
    date: "1 August 2026",
    dateISO: "2026-08-01",
    pubDate: "Sat, 01 Aug 2026 09:00:00 +0700",
    body:
      "From today, the work behind this site is public: the movement plan, fifteen sector dossiers, seven project briefs, ten draft policies, and the source register that backs every figure we publish. Anyone can inspect it, correct it, or build on it. That is not a gesture — it is the method. A movement that asks to be trusted about numbers should be checkable, and now it is.",
  },
  {
    slug: "ten-policy-drafts-open-for-review",
    title: "Ten policy drafts open for review",
    label: "Update",
    date: "1 August 2026",
    dateISO: "2026-08-01",
    pubDate: "Sat, 01 Aug 2026 09:00:00 +0700",
    body:
      "Ten policies — covering privacy, funding transparency, AI accountability, editorial independence and more — are now published as drafts, and none of them is in force. That is deliberate. Policies adopted quietly by one person are just preferences; policies reviewed in the open become commitments. Read them, find the holes, and tell us. Every draft carries its status honestly until review is real.",
  },
];

const { labels } = require("./labels.js");
for (const name of NEWS_LABELS) {
  const l = labels[name];
  if (!l) throw new Error(`news: label "${name}" is not defined in _data/labels.js`);
  if (l.chip !== `lbl lbl--${name.toLowerCase()}`) {
    throw new Error(`news: label "${name}" has chip "${l.chip}" in _data/labels.js; the card renders "lbl lbl--${name.toLowerCase()}"`);
  }
}
for (const item of items) {
  if (!item.label) throw new Error(`news: item "${item.slug}" has no label — every update carries one (${NEWS_LABELS.join(", ")})`);
  if (!NEWS_LABELS.includes(item.label)) {
    throw new Error(`news: item "${item.slug}" has label "${item.label}", which is not one of ${NEWS_LABELS.join(", ")}`);
  }
}

module.exports = items;

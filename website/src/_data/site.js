// Canonical site identity. The production origin is used for absolute URLs
// in sitemap.xml, per-page canonical links, the RSS feed, and Open Graph
// tags. It is overridable via SITE_ORIGIN so preview builds can carry their
// own origin without hard-coding production anywhere; production connection
// remains a separate, gated decision.
module.exports = {
  origin: (process.env.SITE_ORIGIN || "https://uncost.org").replace(/\/$/, ""),
  name: "Uncost",
  tagline: "Living should not have a price tag.",
  description:
    "Uncost is a nonprofit, nonpartisan movement to reduce the cost of living for human essentials.",
  // Brand artwork only for social cards — never a fabricated statistic.
  ogImage: "/img/og/mark-only-final-light-1200.png",
  locale: "en",
};

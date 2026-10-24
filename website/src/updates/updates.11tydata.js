// /updates/check-email/ and /updates/confirmed/ — the email updates sign-up's
// plain pages (records/changes/CHG-009). A browser that posted the updates form
// WITHOUT JavaScript lands on check-email; the confirmation link in the email
// lands on confirmed. They exist only in a build with features.formsOpen on
// (no permalink otherwise, so nothing is written) and are noindex: never in
// the sitemap or the search index.
module.exports = {
  layout: "layouts/base.njk",
  noindex: true,
  pageId: "pledge-check-email",
  eleventyComputed: {
    permalink: (data) =>
      data.features && data.features.formsOpen ? `/updates/${data.page.fileSlug}/` : false,
  },
};

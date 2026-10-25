// /signup/not-sent/, /signup/unsubscribed/, /signup/deleted/ and
// /signup/link-expired/ — where the sign-up handlers
// (website/functions/api/signup/*.js; records/changes/CHG-009) send a browser
// without JavaScript, or one that followed a link from an email. They exist
// only in a build with features.formsOpen on (no permalink otherwise) and are
// noindex. They reuse the pledge flow's card (pageId pledge-check-email).
module.exports = {
  layout: "layouts/base.njk",
  noindex: true,
  pageId: "pledge-check-email",
  eleventyComputed: {
    permalink: (data) =>
      data.features && data.features.formsOpen ? `/signup/${data.page.fileSlug}/` : false,
  },
};

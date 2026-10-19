// /contact/sent/ and /contact/not-sent/ — where the contact form's handler
// (website/functions/api/contact.js) sends a browser that posted WITHOUT
// JavaScript. They exist only in a build with features.contactFormOpen on (no
// permalink otherwise, so nothing is written), and are noindex: never in the
// sitemap or the search index.
module.exports = {
  layout: "layouts/base.njk",
  noindex: true,
  eleventyComputed: {
    permalink: (data) =>
      data.features && data.features.contactFormOpen ? `/contact/${data.page.fileSlug}/` : false,
  },
};

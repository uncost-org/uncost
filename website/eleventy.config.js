const markdownIt = require("markdown-it");

module.exports = function (eleventyConfig) {
  // html: false — content sources are plain markdown; raw HTML stays inert.
  const md = markdownIt({ html: false });
  eleventyConfig.addFilter("md", (content) => md.render(content || ""));

  // Design-system primitives only. The reference specimen, receipts, and
  // authority documents are repository governance, not site output.
  eleventyConfig.addPassthroughCopy({ "design-system/tokens.css": "design-system/tokens.css" });
  eleventyConfig.addPassthroughCopy({ "design-system/components.css": "design-system/components.css" });
  eleventyConfig.addPassthroughCopy({ "design-system/fonts": "design-system/fonts" });
  eleventyConfig.addPassthroughCopy({ "design-system/icons": "design-system/icons" });
  // Logos only for now: the full 86-image brand set is ~121 MB of source
  // PNGs; sector and robot art ships with the design pass and its image
  // pipeline, not with the routing scaffold.
  eleventyConfig.addPassthroughCopy({ "assets/brand/logos": "assets/brand/logos" });

  return {
    dir: { input: "src", output: "dist", includes: "_includes" },
    markdownTemplateEngine: "njk",
    htmlTemplateEngine: "njk",
  };
};

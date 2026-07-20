const path = require("node:path");
const markdownIt = require("markdown-it");
const Image = require("@11ty/eleventy-img");

const BRAND_ROOT = path.resolve(__dirname, "assets", "brand");

module.exports = function (eleventyConfig) {
  // html: false — content sources are plain markdown; raw HTML stays inert.
  const md = markdownIt({ html: false });
  eleventyConfig.addFilter("md", (content) => md.render(content || ""));

  // Render a markdown document to be embedded UNDER an existing page <h1>:
  // every heading is demoted one level so the page keeps a single h1 and a
  // valid, unbroken heading order (enforced by html-validate). Used where a
  // source document is nested inside another page (for example the
  // longer-horizon list on /projects).
  eleventyConfig.addFilter("mdSection", (content) => {
    const html = md.render(content || "");
    return html.replace(/<(\/?)h([1-5])(\b[^>]*)>/g, (_, slash, level, rest) => {
      return `<${slash}h${Number(level) + 1}${rest}>`;
    });
  });

  // Design-system primitives only. The reference specimen, receipts, and
  // authority documents are repository governance, not site output.
  eleventyConfig.addPassthroughCopy({ "design-system/tokens.css": "design-system/tokens.css" });
  eleventyConfig.addPassthroughCopy({ "design-system/components.css": "design-system/components.css" });
  eleventyConfig.addPassthroughCopy({ "design-system/fonts": "design-system/fonts" });
  eleventyConfig.addPassthroughCopy({ "design-system/icons": "design-system/icons" });

  // Brand image pipeline. Source PNGs under assets/brand/ remain the sole
  // canonical, manifest-pinned authority (website/assets/brand/ASSET_MANIFEST.json);
  // every rendered variant is a build-time DERIVATIVE written into dist/img/
  // and NEVER committed, so the approved 86-hash set is untouched. Alt text
  // must come from the manifest (the `image` shortcode requires an explicit
  // alt argument; empty alt only for decorative marks).
  //
  // Usage in a template:
  //   {% image "logos/logo-tight-light.png", "Uncost.org", "(max-width: 40rem) 8rem, 10rem", [160, 320], "eager" %}
  async function image(src, alt, sizes = "100vw", widths = [320, 640, 960], loading = "lazy") {
    if (alt === undefined) {
      throw new Error(`image shortcode: missing alt text for ${src}`);
    }
    const input = path.join(BRAND_ROOT, src);
    const metadata = await Image(input, {
      widths: [...widths, null], // null keeps an original-width fallback
      formats: ["avif", "webp", "png"],
      outputDir: path.join(__dirname, "dist", "img"),
      urlPath: "/img/",
      // Deterministic, content-addressed names: reproducible builds, so the
      // built-output audit and any golden checks stay stable.
      filenameFormat: (id, s, width, format) => `${path.parse(s).name}-${width}.${format}`,
    });
    return Image.generateHTML(metadata, {
      alt,
      sizes,
      loading,
      decoding: "async",
    });
  }
  eleventyConfig.addNunjucksAsyncShortcode("image", image);

  return {
    dir: { input: "src", output: "dist", includes: "_includes" },
    markdownTemplateEngine: "njk",
    htmlTemplateEngine: "njk",
  };
};

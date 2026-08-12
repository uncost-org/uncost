const path = require("node:path");
const markdownIt = require("markdown-it");
const Image = require("@11ty/eleventy-img");

const BRAND_ROOT = path.resolve(__dirname, "assets", "brand");

module.exports = function (eleventyConfig) {
  // Belt-and-braces with website/.eleventyignore: the design export is
  // reference-only. It is never site input and never reaches dist/.
  eleventyConfig.ignores.add("design-source/**");
  eleventyConfig.watchIgnores.add("design-source/**");
  // Strip whitespace around block tags so `{% if %}`/`{% for %}` on their own
  // lines do not emit indented blank lines (html-validate no-trailing-whitespace).
  // Affects only block-tag whitespace — never rendered content.
  eleventyConfig.setNunjucksEnvironmentOptions({ trimBlocks: true, lstripBlocks: true });

  // html: false — content sources are plain markdown; raw HTML stays inert.
  const md = markdownIt({ html: false });
  eleventyConfig.addFilter("md", (content) => md.render(content || ""));

  // A URL is sitemap-eligible only if it renders an HTML page (ends in "/"
  // or ".html"); .xml/.txt/.json outputs are excluded.
  eleventyConfig.addFilter("isIndexable", (url) => {
    if (typeof url !== "string") return false;
    return url.endsWith("/") || url.endsWith(".html");
  });

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
  //
  // The four stylesheets are the design export's own, adopted byte-identically
  // into the governed packet (website/design-system/) and served at the paths
  // the export's markup already uses: /css/{tokens,components,site,sections}.css,
  // loaded in that order. Authoring happens in the design canvas and arrives by
  // re-export — never by patching these files here.
  eleventyConfig.addPassthroughCopy({ "design-system/tokens.css": "css/tokens.css" });
  eleventyConfig.addPassthroughCopy({ "design-system/components.css": "css/components.css" });
  eleventyConfig.addPassthroughCopy({ "design-system/site.css": "css/site.css" });
  eleventyConfig.addPassthroughCopy({ "design-system/sections.css": "css/sections.css" });
  // Repo-owned build shim, loaded last. Carries no design values.
  eleventyConfig.addPassthroughCopy({ "src/css/integration.css": "css/integration.css" });
  // Curated icon sprite, served where the export's markup references it. The
  // `vote` and `dollar` symbols the export ships are withheld per EXCLUSIONS.md.
  eleventyConfig.addPassthroughCopy({ "design-system/icons/icons.svg": "assets/icons.svg" });
  // Self-hosted variable fonts (OFL, already in the repo under the packet's
  // names; these are byte-identical copies carrying the export's filenames so
  // the adopted @font-face rules resolve without editing the export's CSS).
  eleventyConfig.addPassthroughCopy({ "assets/fonts": "assets/fonts" });
  // Behaviour only — menu, drawer, search overlay, accordion. No markup, no
  // dependencies, no third-party requests.
  eleventyConfig.addPassthroughCopy({ "src/js": "js" });
  eleventyConfig.addPassthroughCopy({ "src/_headers": "_headers" });

  // Brand image pipeline. Source PNGs under assets/brand/ remain the sole
  // canonical, manifest-pinned authority (website/assets/brand/ASSET_MANIFEST.json);
  // every rendered variant is a build-time DERIVATIVE written into dist/img/
  // and NEVER committed, so the approved 86-hash set is untouched. Alt text
  // must come from the manifest (the `image` shortcode requires an explicit
  // alt argument; empty alt only for decorative marks).
  //
  // Usage in a template:
  //   {% image "logos/logo-tight-light.png", "Uncost.org", "(max-width: 40rem) 8rem, 10rem", [160, 320], "eager", "robot" %}
  async function image(src, alt, sizes = "100vw", widths = [320, 640, 960], loading = "lazy", className = "") {
    if (alt === undefined) {
      throw new Error(`image shortcode: missing alt text for ${src}`);
    }
    const input = path.join(BRAND_ROOT, src);
    // ONE format, so eleventy-img emits a bare <img srcset> and never a
    // <picture> wrapper. The design's CSS is written against a bare <img> as
    // the direct child of its container — .hero-grid is a two-column grid whose
    // second child IS the robot — and a wrapper changes which element is the
    // grid/flex item. `picture { display: contents }` did not save it: that
    // promotes the <source> elements to grid items too, so .hero-grid got four
    // children and the robot dropped to a second row. Responsive widths are
    // kept via srcset; the format matches the manifest's PNG so the markup is
    // shaped exactly like the export's.
    const metadata = await Image(input, {
      widths: [...widths, null], // null keeps an original-width fallback
      formats: ["png"],
      outputDir: path.join(__dirname, "dist", "img"),
      urlPath: "/img/",
      // Deterministic, content-addressed names: reproducible builds, so the
      // built-output audit and any golden checks stay stable.
      filenameFormat: (id, s, width, format) => `${path.parse(s).name}-${width}.${format}`,
    });
    // className lands on the <img>, not the <picture>: the design's rules are
    // written against a bare <img> (.robot caps the hero at 440px,
    // .sector-illus fixes the dossier illustration's height), and the wrapper
    // is display:contents so it is invisible to layout. Dropping the class here
    // is what made the hero robot render at full size.
    return Image.generateHTML(metadata, {
      alt,
      sizes,
      loading,
      decoding: "async",
      ...(className ? { class: className } : {}),
    });
  }
  eleventyConfig.addNunjucksAsyncShortcode("image", image);

  // Open Graph card image: a build-time 1200-wide PNG derivative of the
  // approved brand mark, written to dist/img/og/. Brand artwork only — never
  // a fabricated statistic. Not committed; regenerated every build.
  eleventyConfig.on("eleventy.before", async () => {
    await Image(path.join(BRAND_ROOT, "logos", "mark-only-final-light.png"), {
      widths: [1200],
      formats: ["png"],
      outputDir: path.join(__dirname, "dist", "img", "og"),
      urlPath: "/img/og/",
      filenameFormat: (id, s, width, format) => `${path.parse(s).name}-${width}.${format}`,
    });
  });

  return {
    dir: { input: "src", output: "dist", includes: "_includes" },
    markdownTemplateEngine: "njk",
    htmlTemplateEngine: "njk",
  };
};

const fs = require("node:fs");
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

  // Capitalise only the first character, leaving the rest alone — unlike
  // Nunjucks' `capitalize`, which lowercases the remainder and would turn
  // "Week ending 17 August 2026" into "Week ending 17 august 2026".
  eleventyConfig.addFilter("sentenceCase", (v) => {
    const s = String(v == null ? "" : v);
    return s ? s.charAt(0).toUpperCase() + s.slice(1) : s;
  });

  // First n of a list — the split landing shows the latest 3 updates and the
  // latest 5 Cost Watch items, while the dedicated routes show everything.
  eleventyConfig.addFilter("take", (arr, n) => (Array.isArray(arr) ? arr.slice(0, n) : arr));

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
  eleventyConfig.addPassthroughCopy({ "src/css/integration-v43-gap.css": "css/integration-v43-gap.css" });
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
  // First-party publication: "The Case for Uncost" (August 2026, 14 pages).
  // Hash-pinned in docs/CONTROL.md; served from our own origin so the page has
  // no third-party download host. Binary is committed — it IS the deliverable.
  eleventyConfig.addPassthroughCopy({
    "assets/downloads/the-case-for-uncost.pdf": "downloads/the-case-for-uncost.pdf",
  });
  eleventyConfig.addPassthroughCopy({ "src/_headers": "_headers" });
  // Cloudflare Pages redirect table. Routes that have moved keep working
  // rather than 404ing, and the old URL is not left to rot in someone's
  // bookmarks or a feed reader.
  eleventyConfig.addPassthroughCopy({ "src/_redirects": "_redirects" });
  // V13: the XSLT that both RSS feeds name in their <?xml-stylesheet?> line,
  // so a feed opened in a browser reads as a page, and the one small
  // stylesheet that page links. Feed readers ignore both.
  eleventyConfig.addPassthroughCopy({ "src/news/feed.xsl": "news/feed.xsl" });
  eleventyConfig.addPassthroughCopy({ "src/css/feed.css": "css/feed.css" });

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
  // ── N4 news-label guard ────────────────────────────────────────────────
  // Two vocabularies, deliberately kept apart:
  //
  //   Confirmed / Estimate / Scenario / Needs refresh  — the confidence labels.
  //     They describe how much confidence a verified FIGURE carries. They live
  //     on /receipts/, /case/ and the sector pages, and they are never applied
  //     to anything under /news/.
  //
  //   Reported — the only label used anywhere under /news/. It says a price
  //     was published by the linked source on a date. Cost Watch is a watch
  //     list, not a receipt, so "Reported" must never appear on /receipts/,
  //     /case/, a sector page, or in sources/register.csv.
  //
  // Either leak is a build failure, not a lint warning: a Cost Watch item
  // wearing a confidence label would claim verification the register never
  // did, and a receipt wearing "Reported" would understate one that it did.
  // The check is on the class markers, not on prose — the plain English words
  // "reported" and "confirmed" are free to appear in body copy.
  eleventyConfig.on("eleventy.after", async ({ dir, results }) => {
    // Scan the files Eleventy actually WROTE, not a directory reconstructed
    // from config. `dir.output` is the configured value and ignores the CLI
    // `--output` flag, so a build written anywhere else was silently checked
    // against a stale ./dist and passed without inspecting anything — proven
    // by building a deliberate leak to another directory and getting exit 0.
    // An audit that cannot see its subject must fail, not pass quietly
    // (standing rule, DESIGN_IMPORT_RUNBOOK 2026-09-19).
    const written = (results || []).map((r) => r.outputPath).filter(Boolean);
    const out = written.length
      ? path.resolve(written.reduce((a, b) => {
          let i = 0;
          while (i < a.length && i < b.length && a[i] === b[i]) i++;
          return a.slice(0, i);
        }))
      : path.resolve(__dirname, dir.output);
    if (!written.length && !fs.existsSync(out)) {
      throw new Error(
        `News label guard could not find any build output to inspect (looked in ${out}). ` +
        `Refusing to report a clean result on a build it never saw.`
      );
    }
    const REPORTED = /class="[^"]*\blbl--reported\b/;
    const CONFIDENCE = /class="[^"]*\brcpt-conf\b/;
    const leaks = [];

    const walk = (d) => {
      for (const entry of fs.readdirSync(d, { withFileTypes: true })) {
        const full = path.join(d, entry.name);
        if (entry.isDirectory()) { walk(full); continue; }
        if (!entry.name.endsWith(".html")) continue;
        const rel = "/" + path.relative(out, full).split(path.sep).join("/");
        const html = fs.readFileSync(full, "utf8");
        const underNews = rel === "/news/index.html" || rel.startsWith("/news/");
        if (underNews && CONFIDENCE.test(html)) {
          leaks.push(`${rel} carries a confidence label (.rcpt-conf); only "Reported" is allowed under /news/.`);
        }
        if (!underNews && REPORTED.test(html)) {
          leaks.push(`${rel} carries the Reported label (.lbl--reported); it is allowed only under /news/.`);
        }
      }
    };
    if (fs.existsSync(out)) walk(out);

    // The register is the other direction of the same rule: "reported" is not
    // a confidence value, so it must never appear in that column.
    const csv = path.resolve(__dirname, "..", "sources", "register.csv");
    if (fs.existsSync(csv)) {
      const [head, ...rows] = fs.readFileSync(csv, "utf8").trim().split(/\r?\n/);
      const col = head.split(",").indexOf("confidence");
      if (col !== -1) {
        rows.forEach((line, i) => {
          // Confidence is a bare enum value, so a naive split is enough to spot
          // it without pulling in a CSV parser; quoted prose fields cannot
          // produce the exact token "reported" in this position by accident.
          const cells = line.split(",");
          if ((cells[col] || "").trim().toLowerCase() === "reported") {
            leaks.push(`sources/register.csv row ${i + 2}: confidence="reported" — Reported is a /news/ label, not a confidence value.`);
          }
        });
      }
    }

    if (leaks.length) {
      throw new Error(
        "News label guard failed — the /news/ and /receipts/ label vocabularies leaked:\n  - " +
          leaks.join("\n  - ")
      );
    }
  });

  // ── V11 labels-drawer guard ─────────────────────────────────────────────
  // The labels drawer (partials/labels-drawer.njk) must list EXACTLY the label
  // families its page renders — the brief's rule is "each page shows only the
  // label families it uses". _data/labels.js declares the families per page
  // by hand, so this checks the declaration against the built page, both
  // directions:
  //   - every label chip in <main> outside the drawer belongs to one of the
  //     families the drawer lists (a label the reader sees is explained), and
  //     is a name labels.js knows at all (a new label cannot slip in unlisted);
  //   - every family the drawer lists has at least one of its names rendered
  //     outside the drawer (no family the page does not use);
  //   - a page with families has the drawer; one without has none.
  // Chips are read from the rendered markup by their class markers, the same
  // way the news-label guard reads them.
  eleventyConfig.on("eleventy.after", async ({ dir, results }) => {
    const labels = require("./src/_data/labels.js");
    const written = new Map((results || []).map((r) => [r.url, r.outputPath]));
    const CHIP = /<span class="(?:[^"]*\s)?(?:rcpt-conf|rcpt-illus|status|lbl)(?:\s[^"]*)?">([\s\S]*?)<\/span>/g;
    const text = (h) => h.replace(/<[^>]+>/g, "").replace(/&mdash;/g, "\u2014").replace(/\s+/g, " ").trim();
    const owner = new Map();
    for (const [key, fam] of Object.entries(labels.families)) {
      for (const l of fam.labels) owner.set(l.name, [...(owner.get(l.name) || []), key]);
    }
    const problems = [];
    for (const [url, fams] of Object.entries(labels.pages)) {
      const out = written.get(url);
      if (!out || !fs.existsSync(out)) {
        problems.push(`${url}: listed in _data/labels.js but not built — a guard that cannot see its page fails`);
        continue;
      }
      const html = fs.readFileSync(out, "utf8");
      const main = (html.match(/<main[\s\S]*?<\/main>/) || [""])[0];
      const drawer = (main.match(/<details class="ldrawer"[\s\S]*?<\/details>/) || [""])[0];
      const outside = main.replace(drawer, "");
      if (fams.length && !drawer) problems.push(`${url}: lists ${fams.join(", ")} but renders no labels drawer`);
      if (!fams.length && drawer) problems.push(`${url}: lists no families but renders a labels drawer`);
      const shown = [...drawer.matchAll(/data-label-family="([^"]+)"/g)].map((m) => m[1]);
      if (shown.join() !== fams.join()) problems.push(`${url}: drawer shows [${shown}] but labels.js lists [${fams}]`);
      const used = new Set();
      for (const m of outside.matchAll(CHIP)) {
        const name = text(m[1]);
        const keys = owner.get(name);
        if (!keys) { problems.push(`${url}: label "${name}" is in no family in _data/labels.js`); continue; }
        const hit = keys.filter((k) => fams.includes(k));
        if (!hit.length) problems.push(`${url}: label "${name}" (${keys}) is rendered but its family is not in this page's drawer`);
        hit.forEach((k) => used.add(k));
      }
      for (const k of fams) {
        if (!used.has(k)) problems.push(`${url}: drawer lists family "${k}" but the page renders none of its labels`);
      }
    }
    if (problems.length) {
      throw new Error("Labels drawer guard failed:\n  - " + problems.join("\n  - "));
    }
  });

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

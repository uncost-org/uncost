const fs = require("node:fs");
const path = require("node:path");
const markdownIt = require("markdown-it");
const Image = require("@11ty/eleventy-img").default;

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
  //   Two vocabularies live under /news/ (C4, sweep 2026-10-10):
  //   Reported — Cost Watch items. It says a price was published by the
  //     linked source on a date. Cost Watch is a watch list, not a receipt,
  //     so "Reported" must never appear on /receipts/, /case/, a sector page,
  //     or in sources/register.csv.
  //   Update / Perspective / Correction — Uncost's own updates (C2/C3). They
  //     say what kind of update an item is, and mean nothing outside /news/.
  //
  // Three directions, each a build failure, not a lint warning: no confidence
  // label under /news/ (a Cost Watch item wearing one would claim
  // verification the register never did); no Reported outside /news/ (a
  // receipt wearing it would understate one that it did); and no news label
  // outside /news/.
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
    const NEWS_LABEL = /class="[^"]*\blbl--(?:update|perspective|correction)\b/;
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
          leaks.push(`${rel} carries a confidence label (.rcpt-conf); under /news/ only Reported and the news labels are allowed.`);
        }
        if (!underNews && REPORTED.test(html)) {
          leaks.push(`${rel} carries the Reported label (.lbl--reported); it is allowed only under /news/.`);
        }
        if (!underNews && NEWS_LABEL.test(html)) {
          leaks.push(`${rel} carries a news label (.lbl--update/.lbl--perspective/.lbl--correction); they are allowed only under /news/.`);
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

  // ── Drawer guard (V11, reworked by X11) ────────────────────────────────
  // Each page's drawer (partials/labels-drawer.njk; since C1, sweep
  // 2026-10-10, an always-open <section class="ldrawer">, no longer a
  // <details>) must show exactly the labels _data/labels.js lists for it —
  // the founder's list, in order — and that list must match the page:
  //   - the drawer explains labels this page actually carries: at least one
  //     listed label is rendered outside the drawer, or declared `elsewhere`
  //     (a label the drawer explains for a page that does not carry it; none
  //     today — /news/ did this for Reported until C2 gave it its own labels).
  //     A list may name a whole vocabulary — /receipts/
  //     explains all four confidence labels though no register row is an
  //     Estimate or a Scenario today — so each listed label is not required;
  //   - every label chip in <main> outside the drawer is either in the list
  //     or declared `unlisted` — a chip the brief's list leaves out, named so
  //     a known gap is not mistaken for a new one — and every `unlisted` entry
  //     is really rendered (no stale declarations);
  //   - the drawer carries the id labels.js gives it (/receipts/#how-it-works
  //     is linked from /case/).
  // Chips are read from the rendered markup by their class markers, the same
  // way the news-label guard reads them.
  eleventyConfig.on("eleventy.after", async ({ results }) => {
    delete require.cache[require.resolve("./src/_data/labels.js")];
    const labels = require("./src/_data/labels.js");
    const written = new Map((results || []).map((r) => [r.url, r.outputPath]));
    const CHIP = /<span class="(?:[^"]*\s)?(?:rcpt-conf|rcpt-illus|status|lbl)(?:\s[^"]*)?">([\s\S]*?)<\/span>/g;
    const text = (h) => h.replace(/<[^>]+>/g, "").replace(/&mdash;/g, "\u2014").replace(/&amp;/g, "&").replace(/\s+/g, " ").trim();
    const problems = [];
    for (const [url, page] of Object.entries(labels.pages)) {
      const out = written.get(url);
      if (!out || !fs.existsSync(out)) {
        problems.push(`${url}: listed in _data/labels.js but not built — a guard that cannot see its page fails`);
        continue;
      }
      const html = fs.readFileSync(out, "utf8");
      const main = (html.match(/<main[\s\S]*?<\/main>/) || [""])[0];
      // C1 (sweep 2026-10-10): the drawer is an always-open <section>, not a
      // <details>. It holds no nested <section>, so the first close ends it.
      const drawer = (main.match(/<section class="ldrawer"[\s\S]*?<\/section>/) || [""])[0];
      if (!drawer) { problems.push(`${url}: labels.js lists a drawer but the page renders none`); continue; }
      if (!drawer.includes(`id="${page.id}"`)) problems.push(`${url}: drawer does not carry id="${page.id}"`);
      const shown = [...drawer.matchAll(/data-label="([^"]+)"/g)].map((m) => m[1].replace(/&amp;/g, "&"));
      if (shown.join("|") !== page.labels.join("|")) problems.push(`${url}: drawer shows [${shown}] but labels.js lists [${page.labels}]`);
      const outside = new Set([...main.replace(drawer, "").matchAll(CHIP)].map((m) => text(m[1])));
      const elsewhere = Object.keys(page.elsewhere || {});
      if (!page.labels.some((name) => outside.has(name) || elsewhere.includes(name))) {
        problems.push(`${url}: the drawer lists [${page.labels}] but the page renders none of them`);
      }
      for (const name of outside) {
        if (!page.labels.includes(name) && !(page.unlisted || []).includes(name)) problems.push(`${url}: label "${name}" is rendered but is neither in this page's drawer nor declared unlisted`);
      }
      for (const name of page.unlisted || []) {
        if (!outside.has(name)) problems.push(`${url}: "${name}" is declared unlisted but the page no longer renders it`);
      }
    }
    for (const [url] of written) {
      if (labels.pages[url]) continue;
      const out = written.get(url);
      if (out && out.endsWith(".html") && fs.existsSync(out) && /<section class="ldrawer"/.test(fs.readFileSync(out, "utf8"))) {
        problems.push(`${url}: renders a drawer but has no entry in _data/labels.js`);
      }
    }
    if (problems.length) {
      throw new Error("Drawer guard failed:\n  - " + problems.join("\n  - "));
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

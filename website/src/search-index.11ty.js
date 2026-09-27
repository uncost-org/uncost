// Compile-time search index for the site-search overlay (partials/search.njk,
// js/site-search.js). Emitted as ONE static JSON file at /search-index.json and
// fetched from our own origin on demand — no backend, no third-party service,
// no runtime query round-trip. CSP is script-src 'self' / default-src 'self',
// so a same-origin fetch of this static asset is the only network work search
// ever does.
//
// SCOPE — one rule, no second list to drift (SEARCH.md):
// a route is indexed iff the sitemap would list it, i.e. it renders HTML
// (url ends in "/" or ".html") and carries no `noindex`. That is the same
// predicate src/sitemap.njk applies, so search-index eligibility and robots
// indexability cannot diverge. Today that excludes exactly /404.html and
// /500.html, and every non-HTML output (the two RSS feeds, robots.txt,
// sitemap.xml, _headers, _redirects).
//
// LEANNESS — `templateContent` is the page's own rendered body WITHOUT its
// layout, so the header, mega menu, mobile drawer, footer and this very
// overlay never enter the index. Without that, every one of the 67 routes
// would match the same site furniture and a query for "Contact" would return
// the whole site. Figure cards are stripped too and indexed once as register
// records (see below), so the 35 card renderings across /, /case/ and
// /receipts/ cost the index 26 records rather than 35 copies of prose.
//
// The output is deterministic: no timestamp, no build id, so two builds of the
// same sources produce a byte-identical index.

const REGISTER_ROUTE = "/receipts/";
// Anchor for a register row that has no card of its own on /receipts/. Every
// row in register.stats is rendered by receipts.njk as
// `<div class="card" id="SRC-###">`, so #SRC-### resolves for all of them
// today; #register is the section id that always exists, used as the fallback
// so a row can never point at a hash with nothing behind it.
const REGISTER_FALLBACK_HASH = "#register";

// Named character references the templates actually use. markdown-it and the
// export's copy emit these, and a reader searching for "doesn't" or "—" must
// match the text they can see, not the entity that encodes it.
const ENTITIES = {
  amp: "&", lt: "<", gt: ">", quot: '"', apos: "'", nbsp: " ",
  mdash: "—", ndash: "–", hellip: "…",
  lsquo: "‘", rsquo: "’", ldquo: "“", rdquo: "”",
  times: "×", middot: "·", bull: "•", deg: "°",
  pound: "£", euro: "€", cent: "¢", copy: "©",
  reg: "®", trade: "™", laquo: "«", raquo: "»",
  shy: "", thinsp: " ", ensp: " ", emsp: " ",
};

function decodeEntities(text) {
  return text.replace(/&(#x?[0-9a-fA-F]+|[a-zA-Z][a-zA-Z0-9]*);/g, (whole, body) => {
    if (body[0] === "#") {
      const code = body[1] === "x" || body[1] === "X"
        ? parseInt(body.slice(2), 16)
        : parseInt(body.slice(1), 10);
      return Number.isFinite(code) ? String.fromCodePoint(code) : whole;
    }
    const hit = ENTITIES[body];
    return hit === undefined ? whole : hit;
  });
}

// Remove an element and everything inside it, counting nested <div> so a card
// that contains divs (every figure card does) is removed whole rather than up
// to its first closing tag.
function stripBalancedDivs(html, startRe) {
  let out = "";
  let pos = 0;
  startRe.lastIndex = 0;
  let match;
  while ((match = startRe.exec(html)) !== null) {
    if (match.index < pos) continue;
    out += html.slice(pos, match.index);
    const tagRe = /<(\/?)div\b[^>]*>/g;
    tagRe.lastIndex = match.index;
    let depth = 0;
    let end = html.length;
    let tag;
    while ((tag = tagRe.exec(html)) !== null) {
      depth += tag[1] ? -1 : 1;
      if (depth === 0) { end = tagRe.lastIndex; break; }
    }
    pos = end;
    startRe.lastIndex = end;
  }
  return out + html.slice(pos);
}

// Figure cards (partials/figure.njk `card`) carry a register row's own text.
// They are indexed once, as register records pointing at /receipts/#SRC-###,
// rather than 35 times as page body.
const FIGURE_CARD_RE = /<div class="card" id="SRC-[^"]*" data-source="SRC-[^"]*">/g;

function toText(html) {
  const plain = html
    .replace(/<!--[\s\S]*?-->/g, " ")                    // <!-- SECTION: ... --> markers
    .replace(/<(script|style|svg)\b[\s\S]*?<\/\1>/gi, " ")
    .replace(/<[^>]+>/g, " ");                           // attributes go with the tag
  return collapse(decodeEntities(plain));
}

function collapse(text) {
  return text.replace(/\s+/g, " ").trim();
}

function headingsOf(html) {
  const found = [];
  const re = /<h([1-6])\b[^>]*>([\s\S]*?)<\/h\1>/gi;
  let m;
  while ((m = re.exec(html)) !== null) {
    const text = toText(m[2]);
    if (text && found.indexOf(text) === -1) found.push(text);
  }
  return found;
}

module.exports = class {
  data() {
    return {
      permalink: "/search-index.json",
      // Must not index itself, and must not make the collection it reads
      // depend on its own rendering.
      eleventyExcludeFromCollections: true,
    };
  }

  render(data) {
    const docs = [];

    for (const item of data.collections.all || []) {
      const url = item.url;
      if (typeof url !== "string") continue;
      // HTML routes only — the RSS feeds, robots.txt and sitemap.xml are not
      // pages and must never appear as a search result.
      if (!(url.endsWith("/") || url.endsWith(".html"))) continue;
      // Search-index eligibility EQUALS robots indexability.
      if (item.data && item.data.noindex) continue;

      const raw = item.templateContent || "";
      const body = stripBalancedDivs(raw, FIGURE_CARD_RE);

      docs.push({
        t: String((item.data && item.data.title) || "").trim(),
        r: url,
        h: headingsOf(body),
        b: toText(body),
      });
    }

    docs.sort((a, b) => a.r.localeCompare(b.r));

    // Register figures, indexed by their claim and publisher so a number on
    // /receipts/ is findable from site search. Never a hardcoded figure: every
    // field here comes from sources/register.csv via _data/register.js.
    const register = (data.register && data.register.stats) || [];
    const figs = register.map((row) => ({
      t: collapse(String(row.display_caption || "")),
      p: collapse(String(row.publisher || "")),
      r: REGISTER_ROUTE + (row.source_id ? "#" + row.source_id : REGISTER_FALLBACK_HASH),
      m: collapse([row.data_period, row.region].filter(Boolean).join(" · ")),
      id: String(row.source_id || ""),
    }));

    return JSON.stringify({ v: 1, docs, figs });
  }
};

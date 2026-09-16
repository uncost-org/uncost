// Loads the public source register (sources/register.csv) so pages render every
// figure FROM the register — never a hardcoded number. Each row's display_caption
// is the plain-language layer a reader sees; receipt is the verbatim technical
// line; source_line is the short attribution shown under a stat.
//
// Templates render a stat through partials/figure.njk, which wraps it in
// data-source="SRC-###". The content audit (scripts/audit_website.py) treats a
// figure as cited only when it sits inside an element whose data-source is a
// registered SRC id — so the register IS the citation.
const fs = require("node:fs");
const path = require("node:path");

const CSV_PATH = path.resolve(__dirname, "..", "..", "..", "sources", "register.csv");

// Minimal RFC-4180 CSV parser: handles quoted fields, embedded commas/newlines,
// and "" escaped quotes. No dependency (the repo ships no CSV library).
function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let inQuotes = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQuotes) {
      if (c === '"') {
        if (text[i + 1] === '"') { field += '"'; i++; }
        else { inQuotes = false; }
      } else {
        field += c;
      }
    } else if (c === '"') {
      inQuotes = true;
    } else if (c === ",") {
      row.push(field); field = "";
    } else if (c === "\n") {
      row.push(field); field = "";
      rows.push(row); row = [];
    } else if (c === "\r") {
      // ignore; newline handled on \n
    } else {
      field += c;
    }
  }
  // trailing field/row (file may or may not end in newline)
  if (field.length > 0 || row.length > 0) { row.push(field); rows.push(row); }
  return rows;
}

module.exports = function () {
  const text = fs.readFileSync(CSV_PATH, "utf8");
  const table = parseCsv(text).filter((r) => r.length > 1 || (r.length === 1 && r[0] !== ""));
  const header = table[0];
  const all = table.slice(1).map((cells) => {
    const obj = {};
    header.forEach((key, idx) => { obj[key] = cells[idx] !== undefined ? cells[idx] : ""; });
    return obj;
  });

  // Publication year, split out once here so templates never do string surgery
  // on a date (Nunjucks has no substring filter and `slice` chunks arrays).
  for (const row of all) {
    row.publication_year = (row.publication_date || "").slice(0, 4);
    // The register's title is "Publisher — Work". The design italicises the work
    // on the face of a statistic (<b>Source</b>Publisher, <em>Work</em>.), so the
    // two parts are split here rather than reassembled in a template.
    const dash = row.title.indexOf(" — ");
    row.publication_work =
      dash > -1 ? row.title.slice(dash + 3).trim() : row.title.trim();
  }

  const byId = {};
  for (const row of all) byId[row.source_id] = row;

  // Cost statistics only (excludes the governance-control pin SRC-001).
  const stats = all.filter((r) => r.type === "cost-statistic");
  // R3 figure card: the caption echoes its own display value in the numeral's
  // colour. register.js already guarantees the value appears verbatim in the
  // caption, so this only has to find it. The caption is escaped FIRST and the
  // span injected after, so the result is safe to render unescaped and can
  // never carry markup from the register.
  const esc = (t) => String(t)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  for (const row of stats) {
    let html = esc(row.display_caption);
    if (row.display_value) {
      for (const part of row.display_value.split(" versus ")) {
        const e = esc(part);
        const at = html.indexOf(e);           // first verbatim occurrence only
        if (at > -1) {
          html = html.slice(0, at) + '<span class="echo">' + e + "</span>" +
                 html.slice(at + e.length);
        }
      }
    }
    row.captionHtml = html;

    // C3d/C4: date chips colour by RECENCY, computed at build time, not by
    // literal year — so the palette never needs a new colour in January.
    const thisYear = new Date().getUTCFullYear();
    const era = (y) => {
      const n = Number(y);
      if (!n) return "unknown";
      if (n >= thisYear) return "current";
      if (n === thisYear - 1) return "prior";
      return "older";
    };
    row.checkedEra = era((row.last_checked || "").slice(0, 4));
    row.publishedEra = era(row.publication_year);
    // Region chips colour by region CODE. Every row is United States today, so
    // this renders one colour; the mapping is here so it does not have to be
    // invented when the first non-US row lands.
    row.regionCode = /united states/i.test(row.region || "") ? "us" : "other";
  }

  // display_value is the headline numeral a page renders large (the design's
  // 104px figure). It is a PRESENTATION EXTRACT of the row, never an
  // independent number: it must appear verbatim inside the row's own
  // display_caption, so the big figure and the sourced claim cannot drift
  // apart. Fail the build rather than publish a numeral the register does not
  // support. ("30% versus 9%" is a comparison — each side is checked.)
  for (const row of stats) {
    if (!row.display_value) continue;
    for (const part of row.display_value.split(" versus ")) {
      if (!row.display_caption.includes(part)) {
        throw new Error(
          `register: ${row.source_id} display_value "${part}" is not in its display_caption`
        );
      }
    }
    // A bare year is a PERIOD, not a figure. Two rows shipped with the
    // caption's opening year ("2024,") in the big-figure slot, which passed the
    // verbatim check above precisely because the caption starts with it. The
    // year still shows in the period slot, where it belongs.
    if (/^(19|20)\d{2}[.,;:]?$/.test(row.display_value.trim())) {
      throw new Error(
        `register: ${row.source_id} display_value "${row.display_value}" is a year, not a figure`
      );
    }
    // Region and period are shown on the face of every published figure (the
    // receipts rule); a displayed figure missing either is a build error.
    if (!row.region || !row.data_period) {
      throw new Error(
        `register: ${row.source_id} is displayed as a figure but lacks region/data_period`
      );
    }
  }

  // "Figures checked <month year>" — the most recent last_checked date in the
  // register, so the freshness line on a page is a fact about the register
  // rather than a date someone typed.
  const checked = stats
    .map((r) => r.last_checked)
    .filter(Boolean)
    .sort()
    .pop();
  const MONTHS = ["January", "February", "March", "April", "May", "June", "July",
    "August", "September", "October", "November", "December"];
  const [y, m] = (checked || "").split("-");
  const lastChecked = y && m ? `${MONTHS[Number(m) - 1]} ${y}` : "";

  // Cost Watch (/news/) renders exactly the rows the register itself tags as
  // fast-moving. `placement` is the register's own column, so adding or
  // retiring a Cost Watch entry is a register edit, never a template edit.
  // RFC-822 stamp for the Cost Watch feed, derived from the date the source
  // printed the figure. 09:00 +0700 matches the movement updates in
  // _data/news.js, so the two feeds sort together in a reader.
  const RFC822_DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const RFC822_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const rfc822 = (iso) => {
    const d = new Date(`${iso}T02:00:00Z`); // 09:00 +0700
    if (Number.isNaN(d.getTime())) return "";
    return `${RFC822_DAYS[d.getUTCDay()]}, ${String(d.getUTCDate()).padStart(2, "0")} ` +
      `${RFC822_MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()} 09:00:00 +0700`;
  };

  // Newest first, so "latest 5" on /news/ and the Cost Watch RSS agree without
  // either template having to know the register's file order. publication_date
  // is the date the source printed the figure; source_id breaks ties so the
  // build stays deterministic.
  const newsFeed = stats
    .filter((r) => r.placement === "news-feed")
    .map((r) => ({ ...r, pubDate: rfc822(r.publication_date) }))
    .sort((a, b) => {
      const d = String(b.publication_date || "").localeCompare(String(a.publication_date || ""));
      return d !== 0 ? d : String(a.source_id).localeCompare(String(b.source_id));
    });

  return { all, byId, stats, newsFeed, lastChecked };
};

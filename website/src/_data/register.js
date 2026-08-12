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

  return { all, byId, stats, lastChecked };
};

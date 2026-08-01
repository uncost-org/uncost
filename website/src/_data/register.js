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

  const byId = {};
  for (const row of all) byId[row.source_id] = row;

  // Cost statistics only (excludes the governance-control pin SRC-001).
  const stats = all.filter((r) => r.type === "cost-statistic");

  return { all, byId, stats };
};

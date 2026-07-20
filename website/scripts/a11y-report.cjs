#!/usr/bin/env node
// Accessibility report (WCAG 2.2 AA via pa11y/axe+htmlcs) over every built
// page. REPORTING ONLY — always exits 0 so it never blocks a merge or a
// launch; violations are surfaced in the job summary for human triage. The
// blocking correctness gates live in the required content-audit workflow.
const fs = require("node:fs");
const path = require("node:path");
const pa11y = require("pa11y");

const DIST = path.resolve(__dirname, "..", "dist");

function htmlFiles(dir) {
  const out = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...htmlFiles(full));
    else if (entry.name.endsWith(".html")) out.push(full);
  }
  return out;
}

async function main() {
  if (!fs.existsSync(DIST)) {
    console.error("dist/ not found — run the build first");
    process.exit(0);
  }
  const files = htmlFiles(DIST).sort();
  const rows = [];
  let total = 0;
  for (const file of files) {
    const rel = path.relative(DIST, file);
    try {
      const result = await pa11y("file://" + file, {
        standard: "WCAG2AA",
        chromeLaunchConfig: { args: ["--no-sandbox", "--disable-setuid-sandbox"] },
        timeout: 30000,
      });
      const errors = result.issues.filter((i) => i.type === "error");
      total += errors.length;
      if (errors.length) {
        rows.push([rel, errors.length, errors.slice(0, 3).map((e) => e.message).join("; ")]);
      }
      console.log(`${errors.length === 0 ? "ok" : "ISSUES"} ${rel} (${errors.length})`);
    } catch (err) {
      rows.push([rel, "error", String(err).slice(0, 100)]);
      console.log(`ERROR ${rel}: ${String(err).slice(0, 100)}`);
    }
  }

  const summary = process.env.GITHUB_STEP_SUMMARY;
  if (summary) {
    let md = `\n### Accessibility report (WCAG 2.2 AA) — ${files.length} pages, ${total} error-level issues\n\n`;
    md += "_Reporting only; not a merge gate. Triage before public launch._\n\n";
    if (rows.length) {
      md += "| Page | Issues | Sample |\n|---|---|---|\n";
      for (const [rel, count, sample] of rows) {
        md += `| ${rel} | ${count} | ${String(sample).replace(/\|/g, "\\|")} |\n`;
      }
    } else {
      md += "No error-level accessibility issues detected.\n";
    }
    fs.appendFileSync(summary, md);
  }
  console.log(JSON.stringify({ pages: files.length, error_issues: total }));
  process.exit(0);
}

main();

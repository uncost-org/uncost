const fs = require("node:fs");
const path = require("node:path");

const REPO = path.resolve(__dirname, "..", "..", "..");

// Canonical 15-sector order (UNP-39 §5.8, reaffirmed REV4 B6). Never
// reordered: the build fails if the sector files disagree with this list.
const SECTOR_ORDER = [
  "Food", "Water", "Shelter", "Energy", "Healthcare", "Care", "Education",
  "Transportation", "Clothing", "Goods", "Materials", "Communication",
  "Safety", "Environment", "Leisure",
];

// Policy slugs are contractual (UNP-39 §5.19) and intentionally differ from
// some filenames (for example POL-006's permanent URL carries
// "assembly-governance-participation").
const POLICY_SLUGS = {
  "POL-001": "political-activity",
  "POL-002": "privacy-data-protection",
  "POL-003": "code-of-conduct",
  "POL-004": "financial-controls-donation",
  "POL-005": "conflict-of-interest",
  "POL-006": "assembly-governance-participation",
  "POL-007": "responsible-ai",
  "POL-008": "safeguarding-pilot-safety",
  "POL-009": "open-source-licensing",
  "POL-010": "in-kind-gift-acceptance",
};

function splitFrontmatter(text) {
  const match = text.match(/^---\n[\s\S]*?\n---\n/);
  if (!match) return { frontmatter: {}, body: text };
  const frontmatter = {};
  for (const line of match[0].split("\n").slice(1, -2)) {
    const idx = line.indexOf(":");
    if (idx > 0) {
      frontmatter[line.slice(0, idx).trim()] = line
        .slice(idx + 1)
        .trim()
        .replace(/^"(.*)"$/, "$1");
    }
  }
  return { frontmatter, body: text.slice(match[0].length) };
}

function loadSectors() {
  const dir = path.join(REPO, "sectors");
  const files = fs
    .readdirSync(dir)
    .filter((f) => /^SEC-\d{3}-.*\.md$/.test(f))
    .sort();
  const sectors = files.map((file) => {
    const text = fs.readFileSync(path.join(dir, file), "utf8");
    const h1 = text.match(/^# (SEC-\d{3}) — (.+)$/m);
    if (!h1) throw new Error(`sector heading not found in ${file}`);
    const statusMatch = text.match(/\*\*Roadmap status:\*\* (.+)$/m);
    if (!statusMatch) throw new Error(`roadmap status not found in ${file}`);
    const status = statusMatch[1];
    return {
      id: h1[1],
      name: h1[2].trim(),
      slug: file.replace(/^SEC-\d{3}-/, "").replace(/\.md$/, ""),
      status: status.trim(),
      body: text,
    };
  });
  const names = sectors.map((s) => s.name);
  if (JSON.stringify(names) !== JSON.stringify(SECTOR_ORDER)) {
    throw new Error(
      `sector order mismatch — files give [${names.join(", ")}] but the canonical order is fixed`
    );
  }
  return sectors;
}

function loadPolicies() {
  const dir = path.join(REPO, "policies");
  const files = fs
    .readdirSync(dir)
    .filter((f) => /^POL-\d{3}-.*\.md$/.test(f))
    .sort();
  return files.map((file) => {
    const id = file.slice(0, 7);
    const slug = POLICY_SLUGS[id];
    if (!slug) throw new Error(`no contractual slug for ${id}`);
    const { frontmatter, body } = splitFrontmatter(
      fs.readFileSync(path.join(dir, file), "utf8")
    );
    const display = (frontmatter.title || id)
      .replace(/^POL-\d{3} — /, "")
      .replace(/ \(P\d\)$/, "");
    return { id, slug, display, frontmatter, body };
  });
}

function loadProjects() {
  const dir = path.join(REPO, "projects");
  const files = fs
    .readdirSync(dir)
    .filter((f) => /^PRJ-\d{3}-.*\.md$/.test(f))
    .sort();
  const projects = files.map((file) => {
    const id = file.slice(0, 7);
    const slug = file.replace(/^PRJ-\d{3}-/, "").replace(/\.md$/, "");
    const { frontmatter, body } = splitFrontmatter(
      fs.readFileSync(path.join(dir, file), "utf8")
    );
    const display = (frontmatter.title || id).replace(/^PRJ-\d{3} — /, "");
    return { id, slug, display, frontmatter, body };
  });
  const longerHorizon = fs.readFileSync(
    path.join(dir, "LONGER-HORIZON.md"),
    "utf8"
  );
  return { projects, longerHorizon };
}

module.exports = function () {
  const { projects, longerHorizon } = loadProjects();
  return {
    sectors: loadSectors(),
    policies: loadPolicies(),
    projects,
    longerHorizon,
  };
};

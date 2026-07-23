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

// Parse "## Heading\n\nbody" sections of a dossier into { heading: body }.
// Used to wire detail-page fields to reviewed dossier prose (content stays in
// the markdown source; the template only names the field). Headings are
// lower-cased and trimmed so lookups are stable.
function sectionMap(text) {
  const out = {};
  const parts = text.split(/^## +/m);
  for (const part of parts.slice(1)) {
    const nl = part.indexOf("\n");
    if (nl < 0) continue;
    const heading = part.slice(0, nl).trim().toLowerCase();
    out[heading] = part.slice(nl + 1).trim();
  }
  return out;
}

// Manifest is the sole authority for image paths + alt text (AUTHORITY.md).
// Build a basename→alt map so detail templates can resolve alt without
// hard-coding it.
function manifestAlt() {
  const manifest = JSON.parse(
    fs.readFileSync(
      path.join(REPO, "website", "assets", "brand", "ASSET_MANIFEST.json"),
      "utf8"
    )
  );
  const map = {};
  for (const a of manifest.assets || []) {
    if (a.path && a.alt_text) map[path.basename(a.path)] = a.alt_text;
  }
  return map;
}

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
  const alt = manifestAlt();
  const files = fs
    .readdirSync(dir)
    .filter((f) => /^SEC-\d{3}-.*\.md$/.test(f))
    .sort();
  const sectors = files.map((file, i) => {
    const text = fs.readFileSync(path.join(dir, file), "utf8");
    const h1 = text.match(/^# (SEC-\d{3}) — (.+)$/m);
    if (!h1) throw new Error(`sector heading not found in ${file}`);
    const statusMatch = text.match(/\*\*Roadmap status:\*\* (.+)$/m);
    if (!statusMatch) throw new Error(`roadmap status not found in ${file}`);
    const status = statusMatch[1];
    const slug = file.replace(/^SEC-\d{3}-/, "").replace(/\.md$/, "");
    const sec = sectionMap(text);
    const illFile = `sector-${slug}.png`;
    // Honest status pill: the dossier text is rendered verbatim; the class is
    // one of the defined .status--* variants. No bare "Live"/"Funded" badge.
    const statusClass =
      { Focus: "focus", Next: "next", "Future study": "future", Dossier: "dossier" }[
        status.trim()
      ] || "planned";
    return {
      id: h1[1],
      name: h1[2].trim(),
      slug,
      // 01..15 in canonical order (validated below), for "NN / 15" display.
      num: String(i + 1).padStart(2, "0"),
      status: status.trim(),
      statusClass,
      // Dossier-backed fields the detail template wires by name. Absent
      // sections resolve to undefined so the template can show [CONTENT NEEDED].
      includes: sec["includes"],
      opportunity: sec["opportunity"],
      guardrail: sec["guardrail"],
      evidence: sec["evidence status"],
      illustration: { src: `sectors/${illFile}`, alt: alt[illFile] },
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
    const raw = fs.readFileSync(path.join(dir, file), "utf8");
    const { frontmatter, body } = splitFrontmatter(raw);
    const display = (frontmatter.title || id).replace(/^PRJ-\d{3} — /, "");
    const sec = sectionMap(raw);
    return {
      id,
      slug,
      display,
      frontmatter,
      // Reviewed public-facing copy the detail template can wire directly;
      // undefined → [CONTENT NEEDED] in the template.
      publicSummary: sec["public summary"],
      resourcePosture: sec["resource posture"],
      status: frontmatter.status,
      body,
    };
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

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
  // POL-011 is a RESERVED reference, not one of the contractual UNP-39 §5.19
  // slugs. Its slug follows this repository's own naming ("...-and-...", as in
  // POL-002 and POL-004) rather than the design export's shorter form, because
  // the repository is the authority for reference numbers and their URLs.
  "POL-011": "corrections-and-source-integrity",
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
    // The sectors index uses a second chip vocabulary: the export writes
    // `status status--focus` for Focus but `status s-next` / `s-future` /
    // `s-dossier` for the rest, and adds a `focus` modifier to the card itself.
    // Both come from the dossier's own Roadmap status, never from a literal.
    const chipClass = statusClass === "focus" ? "status--focus" : `s-${statusClass}`;
    return {
      id: h1[1],
      name: h1[2].trim(),
      slug,
      // 01..15 in canonical order (validated below), for "NN / 15" display.
      num: String(i + 1).padStart(2, "0"),
      status: status.trim(),
      statusClass,
      chipClass,
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
    // A reserved reference holds a citable number for a policy nobody has
    // written yet. It renders the stub state rather than a body, and it is
    // never counted as a review draft.
    const reserved =
      frontmatter.canonical_status === "reference-reserved-not-drafted";
    // The design renders a policy as a numbered section list with a matching
    // contents rail: <nav class="pol-toc"> links to <section id="sN">, each
    // headed <h3 class="s"><span class="num">N</span>Title</h3>. Split the
    // reviewed markdown on its own "## " headings so the repo's text fills that
    // shape — the prose is untouched, only its container is the design's.
    const sections = [];
    const parts = body.split(/^## +/m);
    // The design's .pol-hd already renders the policy title as the page <h1>,
    // so the markdown's own "# POL-0NN — Title" line is dropped here rather
    // than emitting a second <h1> into .pol-body.
    const preamble = parts[0].replace(/^#\s+POL-\d{3}[^\n]*\n/m, "").trim();
    parts.slice(1).forEach((part, i) => {
      const nl = part.indexOf("\n");
      sections.push({
        anchor: `s${i + 1}`,
        num: i + 1,
        title: (nl < 0 ? part : part.slice(0, nl)).trim(),
        body: (nl < 0 ? "" : part.slice(nl + 1)).trim(),
      });
    });
    return { id, slug, display, frontmatter, body, preamble, sections, reserved, drafted: !reserved };
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
    // Primary sectors this brief names, for the design's "Where it applies
    // first" row. Derived from the dossier's own "## Sectors" section — the
    // same rule the sector pages use in reverse — with the design's swatch
    // colours cycled so the row matches the export's node shape.
    const SQ = ["bg-sage", "bg-clay", "bg-coral", "bg-ink-blue"];
    const sectorText = (sec["sectors"] || "").split(/secondary/i)[0];
    const named = SECTOR_ORDER.filter((n) => new RegExp(`\\b${n}\\b`, "i").test(sectorText));
    const projectSectors = named.slice(0, 3).map((n, i) => ({
      name: n,
      slug: n.toLowerCase(),
      sq: SQ[i % SQ.length],
    }));
    return {
      id,
      slug,
      display,
      frontmatter,
      sections: sectionMap(raw),
      sectors: projectSectors,
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

// The three core projects form "one system, three parts"; the sector-page
// related-projects line for each is a template with the sector name slotted in
// (mechanical, not per-sector authoring). Other projects use their reviewed
// public-summary sentence. Layers are a categorisation, not a claim.
const CORE_PROJECT_ROLE = {
  "PRJ-001": {
    layer: "Presentation layer",
    line: (s) => `Presents what ${s} costs by region, with sources and history.`,
  },
  "PRJ-002": {
    layer: "Data layer",
    line: (s) => `Supplies the ${s} price data: sourced, dated, licensed, and refreshed on a published schedule.`,
  },
  "PRJ-003": {
    layer: "Scenario layer",
    line: (s) => `Tests where automation can genuinely reduce ${s} costs.`,
  },
};

// Membership is DERIVED from each project dossier's "## Sectors" section — a
// project appears on a sector page only if its own dossier names that sector.
// No judgement: the sector name's presence in the Primary/Secondary text is the
// whole rule. Returns sectorName -> [ {id, display, slug, layer, line, tag} ].
function relatedProjectsBySector(projects, sectors) {
  const sectorNames = sectors.map((s) => s.name);
  const map = Object.fromEntries(sectorNames.map((n) => [n, []]));
  for (const p of projects) {
    const sec = sectionMap(p.body)["sectors"] || "";
    // Split at the first "Secondary" so we can tag primary vs secondary.
    const splitIdx = sec.search(/secondary/i);
    const primaryText = splitIdx >= 0 ? sec.slice(0, splitIdx) : sec;
    const secondaryText = splitIdx >= 0 ? sec.slice(splitIdx) : "";
    const firstSentence = (p.publicSummary || "")
      .split(/(?<=[.])\s/)[0]
      .trim();
    for (const name of sectorNames) {
      const re = new RegExp(`\\b${name}\\b`, "i");
      const inPrimary = re.test(primaryText);
      const inSecondary = re.test(secondaryText);
      if (!inPrimary && !inSecondary) continue;
      // Healthcare is a measured cost line only in the dashboard/tracker.
      const costLineOnly =
        name === "Healthcare" && /cost line/i.test(sec);
      const core = CORE_PROJECT_ROLE[p.id];
      map[name].push({
        id: p.id,
        display: p.display,
        slug: p.slug,
        layer: core ? core.layer : null,
        line: core ? core.line(name.toLowerCase()) : firstSentence,
        tag: costLineOnly
          ? "cost line only"
          : inPrimary
            ? "primary sector"
            : "secondary sector",
      });
    }
  }
  // Core three first (Presentation, Data, Scenario), then the rest by id.
  const order = ["PRJ-001", "PRJ-002", "PRJ-003"];
  for (const name of sectorNames) {
    map[name].sort(
      (a, b) =>
        (order.indexOf(a.id) < 0 ? 99 : order.indexOf(a.id)) -
          (order.indexOf(b.id) < 0 ? 99 : order.indexOf(b.id)) ||
        a.id.localeCompare(b.id)
    );
  }
  return map;
}

module.exports = function () {
  const { projects, longerHorizon } = loadProjects();
  const sectors = loadSectors();
  const related = relatedProjectsBySector(projects, sectors);
  for (const s of sectors) s.relatedProjects = related[s.name] || [];
  const policies = loadPolicies();
  return {
    sectors,
    // Slug lookups so a template can name a sector or project by its permanent
    // slug (the homepage focus trio, the nav) without re-deriving anything.
    sectorsBySlug: Object.fromEntries(sectors.map((s) => [s.slug, s])),
    policies,
    projects,
    projectsBySlug: Object.fromEntries(projects.map((p) => [p.slug, p])),
    longerHorizon,
    // Counts rendered on the homepage trust band. Derived from the repository's
    // own registers, never a literal, so adding a policy or project updates the
    // page and the reference range stays true.
    counts: {
      policies: policies.length,
      projects: projects.length,
      sectors: sectors.length,
      policyRange: `${policies[0].id} to ${policies[policies.length - 1].id}`,
      // Split out so page copy can stay true: a reserved reference is not a
      // review draft, and saying "11 public review drafts" would not be.
      policiesDrafted: policies.filter((p) => p.drafted).length,
      policiesReserved: policies.filter((p) => p.reserved).length,
      projectRange: `${projects[0].id} to ${projects[projects.length - 1].id}`,
    },
  };
};

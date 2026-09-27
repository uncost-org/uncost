// Founder-approved body copy for the standalone pages, lifted out of the
// templates that gen_static_pages.py rewrites from the design export.
//
// WHY THIS FILE EXISTS (closes CANVAS-SYNC item 45). The export is the
// authority for page STRUCTURE, and re-deriving a page overwrites its <main>
// verbatim. Until now the approved copy for /movement/ and the /case/
// mechanism section lived inside those templates, which meant a re-derivation
// silently destroyed it — and the tools/post_patch_pages.py entries that were
// supposed to restore it would then fail loudly against a body that no longer
// existed, which is a late and confusing way to find out. Copy that lives here
// cannot be destroyed by a re-derivation, because a re-derivation does not
// touch _data.
//
// Same pattern as sectorContent.js and projectContent.js: structure stays in
// the template, words live in data.
//
// The values are HTML FRAGMENTS, not plain text, and the templates emit them
// with `| safe`. That is deliberate: an accent span (`.hl`, `.u-1`) is part of
// the sentence's meaning — which phrase is emphasised — not part of the page's
// layout, so it belongs with the words. Storing fragments also makes the
// migration provably lossless: the rendered text of every route is
// byte-identical before and after.
//
// Entities are written as entities (&rsquo;, &mdash;) exactly as the approved
// copy had them, so nothing is re-typed and no smart-quote transform is
// introduced.

module.exports = {
  movement: {
    whatThisIs: {
      h2: 'Technology should make living cheaper, <span class="hl">not billionaires richer</span>.',
      lead: 'A nonprofit, nonpartisan movement that treats the cost of living as a problem to be measured and solved &mdash; not endured.',
      // W1 (Batch X, 2026-09-27), founder-approved — "Why we exist".
      body: [
        'Life keeps getting more expensive. Technology that can lower costs keeps getting better. We&rsquo;re working to close that gap: AI- and robotics-based projects and research aimed at real costs, with all our findings published free.',
      ],
    },
    whatWeStandFor: {
      eyebrow: 'What we stand for',
      h2: 'Living should not have a <span class="u-1">price tag</span>.',
      lead: 'That&rsquo;s the whole argument in one line. Everything else on this site is the evidence and the tools behind it.',
      body: [
        'We start from what a person actually needs &mdash; measured, region by region, across fifteen sectors from Food and Shelter to Communication and Leisure &mdash; not from ideology. Where a cost could plausibly come down because of automation or shared infrastructure, we say so, in public, with the method shown. Where it can&rsquo;t, we say that too: an organisation that only publishes its wins isn&rsquo;t doing research, it&rsquo;s marketing.',
        'We&rsquo;re nonpartisan by design, not by accident &mdash; cost-of-living arguments drift toward party politics easily, and we hold the line because a movement that picks a side stops being useful to everyone else. We&rsquo;re not a service provider either: we don&rsquo;t build housing, deliver care, or generate power ourselves. We make the case, do the math, publish the receipts, and stay alongside the people who build with them.',
      ],
    },
    // howACostGetsUncosted: RETIRED 2026-09-27 by X1. The six steps are one
    // block, in the /about/ format, rendered identically on /about/ and
    // /movement/ from _data/uncosted.js.
    whatTakingPartMeans: {
      eyebrow: 'What taking part means',
      h2: 'You get a real part in something, <span class="hl">not a feed to follow</span>.',
      // W2 (Batch X, 2026-09-27), founder-approved.
      body: [
        'Joining Uncost isn&rsquo;t about signing up for messages. Every signed pledge adds to a public count that institutions can&rsquo;t wave away. Every hour spent checking a figure or researching a sector strengthens evidence anyone can use &mdash; open, free, reusable. Plus there&rsquo;s a voice for everyone inside the Assembly where supporters propose, prioritise and object &mdash; one person, one vote. Coming soon.',
      ],
    },
    howToTakePart: {
      eyebrow: 'How to take part',
      h2: 'Three ways <span class="u-1">in</span>.',
      // Link text is part of the copy: the export shipped bare route paths
      // ("/pledge") as link text, which reads as a URL rather than an
      // invitation. The approved wording is the verb.
      paths: [
        { h3: 'Sign the pledge', body: 'Free, and it takes a moment. Its only function is to show how many people want this &mdash; which is the argument that opens doors institutions would otherwise keep shut. <a href="/pledge/">Sign the Pledge</a>' },
        // W4 (Batch X, 2026-09-27), founder-approved; links as briefed.
        { h3: 'Follow our news', body: 'Uncost.org updates are available via <a href="/news/">Uncost News</a> and its RSS feed, all dated and honest. <a href="/news/cost-watch/">Cost Watch</a> tracks price movements in the news, with its own updates and RSS feed.' },
        { h3: 'Volunteer your skills', body: 'The most valuable work available right now is data collection and verification: checking figures against primary sources, reviewing licences, researching a sector, translating. <a href="/join/">Join now</a>' },
      ],
      note: 'Donations open once a fiscal sponsor is confirmed; until then there is nothing to give &mdash; time and skills are worth more anyway.',
    },
    cta: {
      h2: 'The simplest first step is to join.',
      lead: 'It&rsquo;s free, and it shows the world how many of us want this.',
    },
  },

  // /projects/ — X13 (Batch X, 2026-09-27), founder-approved headlines.
  projects: {
    intro: { h2: 'From evidence to <span class="u-1">real cost reduction</span>.' },
    later: { h2: '<span class="u-1">Gated</span> on funding and safety.' },
    howTheyHelp: { h2: 'Every project has to <span class="u-1">earn</span> its cost claim.' },
  },

  // /sectors/ — founder-approved (Batch X, 2026-09-27).
  sectors: {
    intro: {
      // W9 — the headline (V18's string, now in the content layer).
      h2: 'Basic human needs break into <span class="u-1">fifteen sectors</span> &mdash; and we have a plan to reduce the cost of each.',
      // W10 — the intro; sector names bold, coloured by the band's accent rule.
      lead: 'Living isn&rsquo;t one bill &mdash; it&rsquo;s fifteen: <b>Food</b>, <b>Water</b>, <b>Shelter</b>, <b>Energy</b>, <b>Healthcare</b>, <b>Care</b>, <b>Education</b>, <b>Transportation</b>, <b>Clothing</b>, <b>Goods</b>, <b>Materials</b>, <b>Communication</b>, <b>Safety</b>, <b>Environment</b> and <b>Leisure</b>. Each of these fifteen sectors gets a dossier: what it covers, where technology could cut its cost, the guardrail that keeps us honest, and where the evidence stands.',
    },
  },

  // Sector pages (×15) — founder-approved (Batch X, 2026-09-27).
  sector: {
    // W12 — the "01 · Scope" headline (V19's accent, now in the content layer).
    scope: { h2: 'Where automation could <span class="u-1">bite</span> &mdash; and what stays visible.' },
    // W13 — the "02 · Evidence status" empty state, inside the white dotted
    // box, while a sector has no registered figures. It replaces the dossier's
    // SRC-### line and the "Reviewed source records come before figures…"
    // paragraph.
    // W14 — "03" heading on the four research-gated measurement sectors
    // (Healthcare, Care, Education, Safety), which have no scenario phrase:
    // the accent sits on "where it stops", the heading's pivot, so all
    // fifteen 03 headings carry one. {name} is the sector's name.
    measurementH2: 'How far the method goes in {name} &mdash; and <span class="u-1">where it stops</span>.',
    evidenceEmpty: 'Research and analysis for this sector hasn&rsquo;t started yet. When the first figures are ready they&rsquo;ll appear here &mdash; each with its source, date, region and confidence label.',
  },

  // /news/ — W5 (Batch X, 2026-09-27), founder-approved introband headline.
  news: {
    intro: { h2: 'What we&rsquo;ve done, and <span class="u-1">what&rsquo;s next</span>.' },
  },

  // /news/cost-watch/ — X10 (Batch X, 2026-09-27), founder-approved. The
  // intro band's headline and body, and the one line below the filter.
  costWatch: {
    intro: {
      h2: 'Prices in the <span class="u-1">news</span>.',
      lead: 'What agencies, newspapers and trade press are reporting about the cost of living &mdash; each item with its publisher, its date and a link. These are reported figures, not receipts: we haven&rsquo;t checked them against a primary source. Verified figures live in <a href="/receipts/">The Receipts</a>.',
    },
    xref: 'For Uncost&rsquo;s own updates, see <a href="/news/">Uncost.org News</a>.',
  },

  // /about/ — founder-approved (Batch X, 2026-09-27).
  about: {
    yourSay: {
      // W33 — replaces the three Assembly / privacy / principles paragraphs.
      lead: 'Supporters aren&rsquo;t an audience. The Assembly gives every supporter a recorded voice to propose, prioritise, or object. One person, one vote, no payment or donation buying extra weight. We never sell, rent or trade your data, and never use it for partisan targeting. Receipts first, open wherever rights and safety allow, and nonpartisan &mdash; we critique systems, never candidates or parties.',
    },
  },

  // /receipts/ — X8 (Batch X, 2026-09-27), founder-approved headlines; the
  // accent span carries the emphasis, the band's accent rule its colour.
  receipts: {
    intro: { h2: 'Every <span class="u-1">number</span>, out in the open.' },
    register: { h2: 'Every figure we publish, with its <span class="u-1">receipt</span>.' },
    rule: { h2: 'If we can&rsquo;t show where a number came from, <span class="u-1">we don&rsquo;t print it</span>.' },
    corrections: { h2: 'We <span class="u-1">log</span> our mistakes.' },
  },

  case: {
    // The introband. W6 (Batch X, 2026-09-27), founder-approved.
    intro: {
      // X7 (Batch X, 2026-09-27), founder-approved.
      h2: 'The <span class="u-1">receipts</span> behind every claim we make.',
      lead: 'The Case is Uncost&rsquo;s evidence layer. What humans need, what it costs by region, where technology could help, and the receipts behind every claim.',
    },
    mechanism: {
      eyebrow: 'The mechanism',
      // W7 (Batch X, 2026-09-27), founder-approved.
      h2: 'Technology that could cut the cost of living for all is <span class="hl">making its owners wealthier instead</span>.',
      // W8 (Batch X, 2026-09-27), founder-approved. Both figures are SRC-020's
      // (Fed DFA, equities and funds outside retirement accounts); the template
      // wraps this paragraph in data-source="SRC-020" so the built audit counts
      // them as cited.
      lead: 'When a company automates to cut costs, its value rises, and that value goes to whoever owns the company. Ownership itself is concentrated: the bottom half of American households hold about 1% of stocks and funds outside retirement accounts; the top 1% hold about half.',
      // The two figures between lead and close are rendered FROM the register
      // by the template (SRC-020, SRC-024). They are citations, not copy, and
      // deliberately do not live here.
      close: 'Nobody is doing the deliberate work of routing automation&rsquo;s gains back toward the price of rent, groceries, and electricity instead of the value of assets. It&rsquo;s why Uncost exists: to measure where a specific technology could plausibly lower a specific cost, publish the method, and hand it to the people who can act on it.',
    },
    // X7 (Batch X, 2026-09-27), founder-approved: the "What living costs"
    // headline, and the one-line link that replaces the Methodology drawer.
    livingCosts: { h2: 'The numbers, with their <span class="u-1">receipts</span>.' },
    receiptsLink: { text: 'How The Receipts work &rarr;', href: '/receipts/#how-it-works' },
  },
};

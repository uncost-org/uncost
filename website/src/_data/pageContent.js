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
      body: [
        'Uncost exists because life keeps getting more expensive while the technology to make it cheaper keeps getting better. We&rsquo;re the people who think that gap is worth closing on purpose &mdash; with evidence, with AI and robotics pointed at real costs instead of just used to describe them, and with everything we produce given away, free, for anyone to check or copy. The Movement is what it looks like when enough people agree that&rsquo;s worth doing, and say so.',
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
    // H2 (2026-09-19): moved here from the /case/ Methodology drawer. It is a
    // description of how the movement works, not a footnote about how the
    // receipts are formatted, and it was doing nothing for anyone folded
    // inside a collapsed <details> on a different page. The drawer keeps THE
    // RULES and CONFIDENCE LABELS, which are genuinely methodology.
    howACostGetsUncosted: {
      eyebrow: 'How it works',
      h2: 'How a cost gets uncosted',
      intro: 'Six steps, applied the same way every time, in every sector:',
      steps: [
        '<b>Measure.</b> Establish what a household in a defined region actually spends on the thing in question, using public data, with the date and the region attached.',
        '<b>Publish.</b> Put the sources and assumptions up before the conclusions, so anyone can check the starting point rather than being asked to accept it.',
        '<b>Break down.</b> Separate the price into its real components &mdash; land, energy, labour, materials, finance, regulation, maintenance. A cost that can&rsquo;t be decomposed is a cost that can&rsquo;t be reduced.',
        '<b>Match.</b> Identify which components a specific, named mechanism could plausibly move &mdash; and count what it adds as well as what it saves.',
        '<b>Package.</b> Publish the model, the sources, the brief, and the playbook so a community group, co-operative, nonprofit, or public body can run it.',
        '<b>Track.</b> Follow whether the total cost actually falls where the approach is applied, and publish the answer either way.',
      ],
      close: 'The sixth step is what makes the other five worth doing. Proposing that some technology would reduce a cost is easy. Going back afterwards to check honestly whether it did is rare &mdash; and it&rsquo;s usually the step that gets skipped.',
    },
    whatTakingPartMeans: {
      eyebrow: 'What taking part means',
      h2: 'You get a real part in something, <span class="hl">not a feed to follow</span>.',
      body: [
        'Joining Uncost isn&rsquo;t signing up to receive messages. Every pledge signed adds to a public count that gives the movement standing institutions can&rsquo;t wave away. Every hour someone spends verifying a figure, reviewing a source licence, or researching a sector strengthens evidence that anyone can use &mdash; including people who never join at all, because everything we publish is open, free, and reusable.',
        'There&rsquo;s a structured voice waiting inside it, too. <strong>The Assembly</strong> is where supporters propose ideas, prioritise sectors and regions, and raise objections &mdash; one person, one vote, no extra weight for money. It&rsquo;s advisory today, honestly, because the governance rules that would make it binding haven&rsquo;t cleared review yet &mdash; we&rsquo;d rather say that plainly than pretend otherwise. <a href="/assembly/">Read how it works &rarr;</a>',
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
        { h3: 'Follow the news', body: 'Updates land on <a href="/news/">News</a> and its <a href="/news/feed.xml">RSS feed</a>, dated and honest about what is and isn&rsquo;t done &mdash; including the updates that aren&rsquo;t good news.' },
        { h3: 'Volunteer your skills', body: 'The most valuable work available right now is data collection and verification: checking figures against primary sources, reviewing licences, researching a sector, translating. <a href="/join/">Join now</a>' },
      ],
      note: 'Donations open once a fiscal sponsor is confirmed; until then there is nothing to give &mdash; time and skills are worth more anyway.',
    },
    cta: {
      h2: 'The simplest first step is to join.',
      lead: 'It&rsquo;s free, and it shows the world how many of us want this.',
    },
  },

  case: {
    mechanism: {
      eyebrow: 'The mechanism',
      h2: 'The technology that could make living cheaper is <span class="hl">instead making ownership more valuable</span>.',
      lead: 'Automation is extraordinarily effective at cutting the cost of producing things &mdash; that&rsquo;s not in dispute. The question is who receives the benefit when it does. When a company automates, its costs fall and its value rises, and that value accrues to whoever owns the company. Ownership itself is concentrated: the bottom half of American households collectively hold about 1% of the stocks and funds owned outside retirement accounts. The wealthiest 1% hold about half. On the broader measure &mdash; total household net worth &mdash; the top 1% still hold roughly thirty per cent.',
      // The two figures between lead and close are rendered FROM the register
      // by the template (SRC-020, SRC-024). They are citations, not copy, and
      // deliberately do not live here.
      close: 'Nobody is doing the deliberate work of routing automation&rsquo;s gains back toward the price of rent, groceries, and electricity instead of the value of assets. It&rsquo;s why Uncost exists: to measure where a specific technology could plausibly lower a specific cost, publish the method, and hand it to the people who can act on it.',
    },
  },
};

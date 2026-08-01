// FAQ content of record: Uncost-FAQ (Jul-30 docx). The two questions the founder
// flagged in that docx ("Automation takes jobs…" and "How can I help right now?")
// carry the founder-final rewrites, not the docx drafts. The docx's three ***
// review comments are stripped, not implemented. Answers render as HTML via | safe;
// [[EMAIL]] is replaced at render with the obfuscated-mailto component.
//
// Mutable statements (donations closed, sign-ups not yet open) are true as of the
// date shown and change only when reality does.
module.exports = {
  standfirst:
    "The questions a sceptic asks — answered in our own words. Every changeable statement here (donations closed, sign-ups not yet open) is true as of the date shown, and changes only when reality does.",
  sections: [
    {
      heading: "The basics",
      items: [
        {
          q: "What is Uncost?",
          a: "Uncost is a nonprofit, nonpartisan social movement to significantly reduce the cost of living by putting AI and robotics to work for humanity. We measure what things actually cost and publish every source, then work out where AI, robotics and shared infrastructure could bring those costs down, and share the results freely so communities can act on them.",
        },
        {
          q: "Why is it called “Uncost”?",
          a: "Because the cost of living keeps rising even as AI and automation make producing almost everything cheaper — the machines got better but the bills got bigger anyway. To uncost something is to take that contradiction apart: find what makes something expensive, use these tools to bring the cost down, and share what works, free, with the communities that need it. Uncost the cost of living — that is the whole job.",
        },
        {
          q: "Is this a political movement? Whose side are you on?",
          a: "Nobody’s, and we work hard at that. Uncost doesn’t endorse candidates or parties, doesn’t campaign, and doesn’t tell you who’s to blame. Costs are measurable; blame is not. We publish what things cost, where the cost sits, and what could reduce it — and we write it so that a reader from any political direction can check the sources and reach their own view.",
        },
        {
          q: "Do you want to get rid of money, markets, or jobs?",
          a: "No. Money is how the world coordinates, and markets are not the enemy — the price of living is. The plan’s claim is deliberately narrow and testable: using AI, automation and open tools, the real cost of specific essentials can be driven down, and what works can be shared freely so communities everywhere benefit. And we’re not anti-work. We’re against survival depending on working. People should work for ambition, craft, contribution and purpose — whether you can survive shouldn’t depend on it.",
        },
      ],
    },
    {
      heading: "Trust and numbers",
      items: [
        {
          q: "Why should I trust your numbers?",
          a: "You shouldn’t have to. Every figure we publish carries its source, its date and the region it covers, and each one traces to a primary document — the institution that actually measured it, not an article about it. If we can’t show you where a number came from, we don’t print it. <a href=\"/receipts\">The register</a> is public, so you can check any figure yourself.",
        },
        {
          q: "What happens when you get something wrong?",
          a: "We publish the correction with the same prominence as the original claim — and the same goes for negative results. If an approach we examine turns out not to reduce total cost, that finding is published as loudly as a success would have been. An organisation that only reports its wins isn’t doing research.",
        },
        {
          q: "Who runs Uncost?",
          a: "It’s founder-led for the moment, with advisers actively being recruited now. The public identity deliberately centres the movement and the evidence rather than any specific individual — but we do plan to have regional leads as well as sector experts nominated and announced soon.",
        },
        {
          q: "What actually exists today — honestly?",
          a: "A published method and movement plan. Fifteen sector dossiers. Ten draft policies and seven project briefs, all public and open to criticism. A public repository anyone can inspect. A source library with its first verified entries. And here is what doesn’t exist yet: Uncost is not incorporated so cannot accept donations (coming soon!), has no adopted policies, no operating Assembly, no built dashboard, no employees and no revenue. We’d rather show you an empty shelf than a full one we can’t stand behind.",
        },
        {
          q: "A website can’t lower my rent. Isn’t this naive?",
          a: "On its own, a website lowers nothing — which is why the method matters more than the site. Every cost gets the same six steps. Measure what it really costs, from public data. Publish the sources before the conclusions. Break the price into its real parts. Match specific technology to specific parts — counting what it adds as well as what it saves. Package the result so a community can actually run it. Then track whether the cost fell, and publish the answer either way. None of that is magic; every step is checkable work. What the movement adds is scale — enough people saying the same thing makes institutions engage — and open tools mean nobody needs our permission, or our existence, to act on what we find.",
        },
      ],
    },
    {
      heading: "Money",
      items: [
        {
          q: "Can I donate?",
          a: "Not yet — and we’d rather tell you that plainly than take money we can’t properly account for. Uncost is seeking fiscal sponsorship so that donations can be received, administered and reported correctly. Until that’s confirmed, there is no donate button anywhere on this site, and nothing here should be read as a solicitation. When it changes, we’ll say so clearly.",
        },
        {
          q: "When donations open, where will the money go?",
          a: "Into the work and on the record through <a href=\"/treasury\">The Treasury</a> — a public ledger of money received and money spent, visible to anyone, written into our draft policies before a single dollar exists. The first funded priorities are the evidence base and the Human Essentials Dashboard, not salaries or offices; there are currently neither.",
        },
        {
          q: "Can money buy influence here?",
          a: "No. One person, one vote is The Assembly’s design, and contributions never purchase governance, coverage, ranking or editorial control. A movement arguing that wealth shouldn’t determine outcomes shouldn’t let wealth determine its own.",
        },
      ],
    },
    {
      heading: "AI, robots and jobs",
      items: [
        {
          q: "What does AI actually do here?",
          a: "Two things. It’s part of the subject — AI and robotics are among the mechanisms that could genuinely lower the cost of essentials, and we study where that’s real and where it isn’t. And it’s a tool we use in the research itself. What it never does: approve a public claim, authorise spending, publish content or make a safety decision. A human is accountable for each of those, and that doesn’t change as the tools improve.",
        },
        {
          // Founder-final rewrite (replaces the docx draft flagged with ***).
          q: "Automation takes jobs. Why are you cheering for it?",
          a: "We’re not cheering; we’re preparing. Automation is already changing how work is done — and what work is, and how much of it there will be. Pretending otherwise doesn’t protect anyone. That’s why our method counts both columns before anything is proposed: what a mechanism could save, and what it adds — including the work it would displace. The honest version of the future is one where many of today’s traditional jobs are no longer the default path, and the question that matters is whether the essentials of life get cheaper before that transition bites. That is the work we are doing now: building the evidence and the tools so that as automation reshapes work, the cost of living falls with it — and the gains reach households, not only the people who already own the machines.",
        },
        {
          q: "Will Uncost build robot farms and housing factories?",
          a: "No. We produce evidence, models, briefs and playbooks — and then we stay alongside the communities, co-ops, nonprofits and public bodies that build and run things, with guidance and shared learning as they do.",
        },
      ],
    },
    {
      heading: "The pledge and your data",
      items: [
        {
          q: "What is the pledge, and what happens when I sign?",
          a: "The pledge is a short public statement of what this movement stands for — you can read it in full on the <a href=\"/pledge\">pledge page</a>. Signing is free, and its function is scale: demonstrating how many people want this is the argument that makes institutions engage.",
        },
        {
          q: "Do you track me on this site?",
          a: "No. No analytics, no advertising pixels, no fingerprinting, no third-party requests at all — every asset on this site is served from uncost.org, which you can verify in your browser’s network tab. There’s no cookie banner because there’s nothing to consent to.",
        },
      ],
    },
    {
      heading: "Taking part",
      items: [
        {
          // Founder-final rewrite (replaces the docx draft flagged with ***).
          q: "How can I help right now?",
          a: "Start with the pledge — it is the single most useful small act, because scale is the argument that makes institutions engage. Beyond that, we are actively looking for people who want to help build our movement: experts to help lead sectors and regions, researchers to verify figures against primary documents, reviewers for source licences and methodology, translators, and organisations that could pilot the work — co-ops, community groups, research teams, public bodies. If that is you, write to us; [[EMAIL]]. And donations: we can’t accept them yet but we hope to be able to accept support soon. When we can, we’ll say so clearly.",
        },
      ],
    },
  ],
};

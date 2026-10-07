// X1 (Batch X, 2026-09-27): ONE "How a cost gets uncosted" block, rendered
// identically on /about/ and /movement/ by partials/uncosted.njk.
//
// Founder-approved copy, verbatim (typography only: ' → &rsquo;, — → &mdash;).
// The FORMAT is /about/'s — metalabel + headline, numbered step rows, and now
// a closing line — and so is the step text for steps 1, 2 and 6. Steps 3, 4
// and 5 and the closing line are the approved replacements. The /movement/
// variant (its own eyebrow, intro and step text, from UNP-82 v2 via
// pageContent.js) is retired entirely: V12 shared the format and kept two sets
// of words; X1 makes it one set.
//
// Headline: ink, with "uncosted" coral and underlined and the full stop in ink
// (the <u> carries the accent; integration.css item 118 paints it).

module.exports = {
  label: "The mechanism",
  heading: 'How a cost gets <u class="u-1">uncosted</u>.',
  steps: [
    { label: "Measure", text: "Measure the current cost and its context, starting from public data." },
    { label: "Publish", text: "Publish the sources, dates, methods, and confidence labels &mdash; openly, so anyone can check the work." },
    { label: "Break down", text: "Split the cost into its real parts &mdash; land, energy, labour, materials, maintenance, and so on." },
    { label: "Match", text: "Work out where AI, robotics or automation can reduce costs, component by component." },
    { label: "Package", text: "Turn the result into free, open-source tools or playbooks any community can review and implement." },
    { label: "Track", text: "Track whether total cost actually falls &mdash; and publish negative results with the same prominence as wins." },
  ],
  close: "We do the research, run the analysis, give the resources away free, and track the results &mdash; with one aim: lower costs, in every sector, in every region.",
};

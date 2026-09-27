// V12 (2026-09-26): ONE "How a cost gets uncosted" block, in the /about/
// format, rendered on /about/ and /movement/ by partials/uncosted.njk.
//
// The two pages have carried DIFFERENT step text since UNP-82 v2 moved a
// six-step block onto /movement/, and the founder's instruction is that the
// step text stays unchanged until an approved version arrives. So the format
// is shared now and the words are not: each page keeps its own, verbatim.
//
//   about     lifted verbatim from about.njk, where re-derivation from the
//             export would otherwise overwrite it
//   movement  derived from _data/pageContent.js (movement.howACostGetsUncosted)
//             without changing a character: each "<b>Label.</b> text" step is
//             split into its label and its text
//
// When the approved text arrives it replaces both sets at once, here.
const pc = require("./pageContent.js");

const mv = pc.movement.howACostGetsUncosted;
const split = (s) => {
  const m = /^<b>([\s\S]*?)<\/b>\s*([\s\S]*)$/.exec(s);
  if (!m) throw new Error("uncosted.js: movement step is not '<b>Label</b> text': " + s.slice(0, 60));
  return { label: m[1], text: m[2] };
};

module.exports = {
  about: {
    label: "The mechanism",
    heading: "How a cost gets uncosted.",
    steps: [
      { label: "Measure", text: "Measure the current cost and its context, starting from public data." },
      { label: "Publish", text: "Publish the sources, dates, methods, and confidence labels — openly, so anyone can check the work." },
      { label: "Break down", text: "Split the cost stack into its real components: labor, energy, land, materials, waste, market structure, financing, fees, and policy." },
      { label: "Match", text: "Match plausible AI, robotics, sharing, infrastructure, or public-interest mechanisms to specific components." },
      { label: "Package", text: "Package the result as open evidence, software, a brief, or a playbook local groups can use. Uncost publishes; local operators decide and act." },
      { label: "Track", text: "Track whether total cost actually falls — and publish negative results with the same prominence as wins." },
    ],
  },
  movement: {
    label: mv.eyebrow,
    heading: mv.h2,
    intro: mv.intro,
    steps: mv.steps.map(split),
    close: mv.close,
  },
};

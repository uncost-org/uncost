// Progressive-activation feature gates.
//
// Everything here defaults OFF and is turned on by CONFIG only when its
// real-world precondition is met — never by the mere presence of a block in a
// template. This keeps the "present in the markup, dark by default, activated
// by config" pattern in one place so it stays consistent across the site (the
// signature counter and the founding-signer recognition both gate here, at the
// same 100-signature milestone).
//
// Activation is a build-time env flag so the milestone can be flipped without a
// code change, the same way SITE_ORIGIN is handled in site.js.
module.exports = {
  // Public signature counter — on only when there is a real, sourced count to
  // show. Until then the Thanks page states the count "will appear as the
  // movement grows" rather than rendering a number.
  signatureCounter: process.env.UNCOST_SIGNATURE_COUNTER === "on",

  // ---- Design-export flags (design-source/data/site.json → flags) ----------
  //
  // formsOpen is the single switch for every form on the site. While it is
  // false, NO input, checkbox or submit button is rendered anywhere — only
  // "Sign-ups open soon." That is deliberate and is an accessibility
  // requirement, not a cosmetic one: a visually dimmed form is still
  // keyboard-focusable and submittable. The markup that ships when it opens is
  // vendor-agnostic and carries only the data-form hooks — no endpoint, no
  // vendor script, no third-party request.
  formsOpen: process.env.UNCOST_FORMS_OPEN === "on",

  // No donate ask may appear anywhere while this is false. The gate is
  // lawfulness (POL-004 financial controls), not design.
  donationsOpen: process.env.UNCOST_DONATIONS_OPEN === "on",

  // Site search is not built. The overlay ships with honest copy and shortcut
  // links rather than a dead input.
  searchEnabled: process.env.UNCOST_SEARCH_ENABLED === "on",

  // Founding-signer recognition — the first signers, shown at the same
  // 100-signature milestone as the counter, listed factually with no editorial
  // ranking (no "notable" hierarchy).
  //
  // HARD BLOCK — the gate is CONSENT, not design. Do NOT set this on until a
  // public-display consent purpose exists in the UNP-57 consent model AND has
  // been collected from each person shown. UNP-57 rev 5 has exactly three
  // purposes — signing, email updates, and Assembly interest — and none of them
  // authorizes displaying a signer's name publicly. Activating without that
  // reserved purpose would retrofit a use onto people who never agreed to it.
  // The reservation is being carried to UNP-57 (as §3.2 reserved donation-intent
  // was) so activation later is an amendment, not a retrofit.
  foundingSigners: process.env.UNCOST_FOUNDING_SIGNERS === "on",
};

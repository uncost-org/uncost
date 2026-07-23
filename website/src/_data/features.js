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

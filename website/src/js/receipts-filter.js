/* Receipts keyword filter — progressive enhancement only.
 *
 * The register is fully rendered server-side; with JS off this file simply
 * never runs and every card stays visible. The filter bar ships hidden and is
 * revealed here, so a reader without JS is never shown a control that does
 * nothing.
 *
 * No form submission and no network: the input is not inside a <form>, and the
 * only work done is toggling the `hidden` attribute on cards already in the
 * DOM. CSP is script-src 'self', so this is an external file, never inline.
 */
(function () {
  "use strict";
  var bar = document.querySelector("[data-receipts-filter]");
  var grid = document.getElementById("register-cards");
  if (!bar || !grid) return;

  var input = bar.querySelector("input[type='search']");
  var count = bar.querySelector("[data-filter-count]");
  var cards = Array.prototype.slice.call(grid.querySelectorAll(".card"));

  // Index each card once: its id plus all of its visible text, lower-cased.
  var index = cards.map(function (card) {
    return { el: card, text: (card.textContent || "").toLowerCase() };
  });

  function apply() {
    var q = (input.value || "").trim().toLowerCase();
    var shown = 0;
    index.forEach(function (row) {
      var hit = q === "" || row.text.indexOf(q) !== -1;
      row.el.hidden = !hit;
      if (hit) shown++;
    });
    if (count) {
      count.textContent = q === ""
        ? String(cards.length) + " figures"
        : String(shown) + " of " + String(cards.length) + " figures";
    }
    grid.setAttribute("data-filtered", q === "" ? "false" : "true");
  }

  input.addEventListener("input", apply);
  input.addEventListener("keydown", function (e) {
    if (e.key === "Escape") { input.value = ""; apply(); }
  });

  bar.hidden = false;   // reveal only once the behaviour exists
  apply();
})();

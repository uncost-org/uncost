/* Keyword filter — progressive enhancement only.
 *
 * One file, several instances: the register on /receipts/, and one per list
 * under /news/ (both columns of the split landing, then one on each dedicated
 * route). A bar declares which list it filters, so nothing here knows about
 * any particular page.
 *
 *   <div class="rfilter" data-keyword-filter
 *        data-filter-for="register-cards" data-filter-noun="figures" hidden>
 *
 * Every list is fully rendered server-side; with JS off this file simply never
 * runs and every item stays visible. The bar ships hidden and is revealed
 * here, so a reader without JS is never shown a control that does nothing.
 *
 * No form submission and no network: the input is not inside a <form>, and the
 * only work done is toggling the `hidden` attribute on items already in the
 * DOM. CSP is script-src 'self', so this is an external file, never inline.
 *
 * After every pass this file dispatches a `keyword-filter:apply` CustomEvent on
 * the target grid ({query, shown, total}). It is purely additive: a list with
 * no listener behaves exactly as before. /js/show-more.js listens on the
 * receipts register so filtering and paging cannot fight over the same
 * `hidden` attribute — while a query is active, paging stands down and every
 * match is shown. The index above is built from ALL items, so a query always
 * searches the whole list regardless of how much of it is currently paged in.
 *
 * `hidden` only hides if nothing outranks it — `.cards .card{display:flex}`
 * beat it once and the filter counted correctly while hiding nothing. The
 * stylesheet now states `[hidden]{display:none!important}` for every item type
 * this file touches (integration.css items 66 and 73), and the check is on
 * RENDERED items, never on the counter's own text.
 */
(function () {
  "use strict";

  var ITEMS = ".card, [data-news-item]";

  function wire(bar) {
    var grid = document.getElementById(bar.getAttribute("data-filter-for"));
    if (!grid) return;

    var input = bar.querySelector("input[type='search']");
    var count = bar.querySelector("[data-filter-count]");
    var noun = bar.getAttribute("data-filter-noun") || "items";
    if (!input) return;

    var items = Array.prototype.slice.call(grid.querySelectorAll(ITEMS));
    if (!items.length) return;

    // Index each item once: all of its visible text, lower-cased.
    var index = items.map(function (el) {
      return { el: el, text: (el.textContent || "").toLowerCase() };
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
          ? String(items.length) + " " + noun
          : String(shown) + " of " + String(items.length) + " " + noun;
      }
      grid.setAttribute("data-filtered", q === "" ? "false" : "true");

      // Announce the pass on the grid so another enhancement can react to it
      // without this file knowing anything about that enhancement. Nothing
      // listens by default, so lists that only want filtering are unaffected.
      // /js/show-more.js uses this to restore its paging once a query is
      // cleared, and to stand its control down while one is active.
      grid.dispatchEvent(new CustomEvent("keyword-filter:apply", {
        detail: { query: q, shown: shown, total: items.length }
      }));
    }

    input.addEventListener("input", apply);
    input.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { input.value = ""; apply(); }
    });

    bar.hidden = false;   // reveal only once the behaviour exists
    apply();
  }

  Array.prototype.forEach.call(
    document.querySelectorAll("[data-keyword-filter]"),
    wire
  );
})();

/* Show more — progressive enhancement only.
 *
 * Pages a fully server-rendered list down to a first batch and reveals a
 * control that adds one more batch per click. A control declares which list it
 * pages and how big a batch is:
 *
 *   <p class="u-75" data-show-more data-show-more-for="register-cards"
 *      data-show-more-step="12" hidden>
 *     <button type="button" class="u-btn u-btn--ghost">Show more receipts</button>
 *   </p>
 *
 * Every item is rendered server-side; with JS off this file never runs, the
 * whole list stays visible and the control stays hidden. So a reader without
 * JS is never shown a control that does nothing and never loses content — the
 * same contract keyword-filter.js keeps for its bar.
 *
 * CASCADE TRAP (the reason the wrapper carries `hidden`, not the button):
 * `hidden` only hides if nothing outranks it. `[hidden]` is a UA rule here, so
 * ANY author `display` declaration beats it — `.u-btn{display:inline-block}`
 * would leave a `hidden` button rendering, exactly as `.cards .card{display:flex}`
 * once did to the filter (integration.css item 66). The wrapper this file
 * toggles must therefore carry no class that sets `display`. Verified on
 * RENDERED elements (offsetParent), never on a counter's text.
 *
 * INTERACTION WITH THE KEYWORD FILTER — while a query is active, paging is
 * suspended: every match is shown and this control is hidden. The filter is a
 * narrowing tool, so a reader who has already narrowed the list should not have
 * to page through what is left; it also keeps the filter's own "N of M" count
 * honest, because N is then exactly what renders. Clearing the query restores
 * paging at whatever batch the reader had already reached, so they do not lose
 * their place. The filter indexes the full list either way, so a query always
 * searches everything, not just what is paged in.
 *
 * CSP is script-src 'self', so this is an external file, never inline.
 */
(function () {
  "use strict";

  var ITEMS = ".card, [data-news-item]";

  function wire(ctl) {
    var grid = document.getElementById(ctl.getAttribute("data-show-more-for"));
    if (!grid) return;

    var btn = ctl.querySelector("button");
    if (!btn) return;

    var step = parseInt(ctl.getAttribute("data-show-more-step"), 10);
    if (!(step > 0)) step = 12;

    var items = Array.prototype.slice.call(grid.querySelectorAll(ITEMS));
    if (items.length <= step) return;  // nothing to page: leave the control hidden

    var limit = step;

    function render() {
      // A query is active: the filter has already set `hidden` on every item to
      // match, and all matches stay shown. Only stand the control down.
      if (grid.getAttribute("data-filtered") === "true") {
        ctl.hidden = true;
        return;
      }
      for (var i = 0; i < items.length; i++) {
        items[i].hidden = i >= limit;
      }
      ctl.hidden = limit >= items.length;
    }

    btn.addEventListener("click", function () {
      var firstNew = items[limit] || null;
      limit += step;
      render();
      // Last batch: the control has just gone, so focus would be stranded on a
      // hidden element. Hand it to the first item that was just revealed.
      if (ctl.hidden && firstNew) {
        firstNew.setAttribute("tabindex", "-1");
        firstNew.focus();
      }
    });

    // keyword-filter.js announces every pass, including its own start-up one.
    grid.addEventListener("keyword-filter:apply", render);

    // An anchor that is paged out has no layout box, so the browser has
    // nothing to scroll to and /receipts/#SRC-017 lands silently at the top of
    // the page. That breaks every inbound link, bookmark and citation to a row
    // below the first batch — 14 of the 26 register anchors — not just site
    // search. Page forward until the target is revealed, in whole batches, so
    // the control never disagrees with what is on screen.
    function revealHash() {
      var id = (location.hash || "").slice(1);
      if (!id) return;
      var target = document.getElementById(id);
      if (!target) return;
      var at = items.indexOf(target);
      if (at === -1 || at < limit) return;
      limit = Math.ceil((at + 1) / step) * step;
      render();
      target.scrollIntoView();   // the hash already fired; do it again
    }
    window.addEventListener("hashchange", revealHash);

    render();  // reveals the control only once the behaviour exists
    revealHash();
  }

  Array.prototype.forEach.call(
    document.querySelectorAll("[data-show-more]"),
    wire
  );
})();

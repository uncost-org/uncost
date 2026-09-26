/* Read more — progressive enhancement only (V16, CANVAS-SYNC 118).
 *
 * Truncates each news item's body to three lines and adds a "Read more"
 * control to the items whose text runs longer. Serves /news/ (`.up-item`) and
 * /news/cost-watch/ (`.cw`), both of which mark their items `data-news-item`.
 *
 * Every item is rendered at full length server-side. The three-line clamp is a
 * class this file adds, so with JS off it never runs: no item is truncated and
 * no control exists. A reader without JS is never cut off mid-sentence with
 * nothing to press.
 *
 * A control exists only where the clamp is actually cutting text — measured on
 * the rendered paragraph (scrollHeight against clientHeight), never guessed
 * from a character count — and it is re-measured on resize and once the web
 * fonts land, because a paragraph that fits three lines at 1440px does not at
 * 390px. Pressing it removes the clamp and the control together: the full text
 * is then simply on the page. There is no collapse control, because the only
 * approved string is "Read more".
 *
 * A Cost Watch card is itself a link (`<a class="cw">`), and a button may not
 * sit inside an `<a>`. Its control is therefore placed immediately AFTER the
 * card and styled as the card's foot (integration.css item 114). The keyword
 * filter hides items with the `hidden` attribute; `.cw[hidden] + .readmore`
 * hides the foot with its card, and the filter's pass triggers a re-measure,
 * because a hidden item has no box to measure.
 *
 * CSP is script-src 'self', so this is an external file, never inline.
 */
(function () {
  "use strict";

  var CLAMP = "is-clamped";
  var entries = [];

  Array.prototype.forEach.call(
    document.querySelectorAll("[data-news-item]"),
    function (item, i) {
      var body = item.querySelector("p");
      if (!body) return;
      if (!body.id) body.id = "news-body-" + (i + 1);
      entries.push({ item: item, body: body, btn: null, open: false });
    }
  );
  if (!entries.length) return;

  function expand(e) {
    e.open = true;
    e.body.classList.remove(CLAMP);
    if (e.btn) {
      e.btn.parentNode.removeChild(e.btn);
      e.btn = null;
    }
    // The control has just gone, so focus would be stranded. Hand it to the
    // text it revealed, so a keyboard reader carries on from where they were.
    e.body.setAttribute("tabindex", "-1");
    e.body.focus({ preventScroll: true });
  }

  function control(e) {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "readmore";
    btn.setAttribute("data-read-more", "");
    btn.setAttribute("aria-controls", e.body.id);
    btn.textContent = "Read more";
    btn.addEventListener("click", function () { expand(e); });
    return btn;
  }

  function measure(e) {
    if (e.open) return;
    if (e.item.offsetParent === null) return;   // filtered out: nothing to measure
    e.body.classList.add(CLAMP);
    var cut = e.body.scrollHeight > e.body.clientHeight + 1;
    if (cut && !e.btn) {
      e.btn = control(e);
      if (e.item.tagName === "A") e.item.insertAdjacentElement("afterend", e.btn);
      else e.body.insertAdjacentElement("afterend", e.btn);
    } else if (!cut && e.btn) {
      e.btn.parentNode.removeChild(e.btn);
      e.btn = null;
    }
  }

  function measureAll() {
    for (var i = 0; i < entries.length; i++) measure(entries[i]);
  }

  var queued = false;
  function queue() {
    if (queued) return;
    queued = true;
    window.requestAnimationFrame(function () {
      queued = false;
      measureAll();
    });
  }

  window.addEventListener("resize", queue);
  // keyword-filter.js announces each pass on its grid without bubbling; a
  // capturing listener on the document still hears it.
  document.addEventListener("keyword-filter:apply", queue, true);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(queue);

  measureAll();
})();

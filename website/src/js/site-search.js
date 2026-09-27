/* Uncost — site search. Progressive enhancement only.
 *
 * The overlay's markup (partials/search.njk) ships the search box with the
 * `hidden` attribute and this file is the only thing that removes it, exactly
 * as the register/Cost Watch keyword filter does. With JS off this file never
 * runs, the box stays hidden, and the reader sees the shortcut link blocks —
 * never a focusable control that does nothing.
 *
 * No backend and no form: the input is not inside a <form>, nothing submits,
 * and the only network work is ONE same-origin fetch of /search-index.json,
 * a static file built at compile time by src/search-index.11ty.js. CSP is
 * script-src 'self' / default-src 'self', so this is an external file (never
 * inline) and that fetch is same-origin.
 *
 * Results are built with createElement/createTextNode, never innerHTML: index
 * text and the reader's query both reach the DOM as text nodes only.
 *
 * Cooperating with js/ui.js: ui.js owns the overlay's open/close lifecycle and
 * focuses the first focusable element (the close button) when it opens. This
 * file does not touch that. It watches `.search-ov` for the `open` class ui.js
 * sets and moves focus to the input afterwards — the observer callback runs
 * after ui.js's synchronous focus() call, so the two never fight.
 */
(function () {
  "use strict";

  var INDEX_URL = "/search-index.json";
  var LEAD = 60;    // characters of snippet before the matched term
  var TRAIL = 110;  // characters after it
  var TF_CAP = 5;   // term-frequency is counted no further than this per record

  var overlay = document.querySelector(".search-ov");
  if (!overlay) return;

  var box = overlay.querySelector("[data-search-box]");
  var input = overlay.querySelector("input[type='search']");
  var resultsList = overlay.querySelector("[data-search-results]");
  var status = overlay.querySelector("[data-search-status]");
  if (!box || !input || !resultsList || !status) return;

  /* ---- index -------------------------------------------------------- */

  var records = null;
  var pending = null;

  function load() {
    if (records) return Promise.resolve(records);
    if (!pending) {
      pending = fetch(INDEX_URL, { credentials: "same-origin" })
        .then(function (res) {
          if (!res.ok) throw new Error("search index HTTP " + res.status);
          return res.json();
        })
        .then(function (data) {
          records = build(data);
          return records;
        })
        .catch(function (err) {
          pending = null;
          throw err;
        });
    }
    return pending;
  }

  function build(data) {
    var out = [];

    (data.docs || []).forEach(function (doc) {
      var heads = (doc.h || []).join(" · ");
      var title = doc.t || doc.r;
      var body = doc.b || "";
      out.push({
        title: title,
        route: doc.r,
        body: body,
        titleLow: title.toLowerCase(),
        headLow: heads.toLowerCase(),
        bodyLow: body.toLowerCase()
      });
    });

    // Register figures: the claim is the result title, the publisher and the
    // row's own scope line are the body, so a figure is findable by either.
    (data.figs || []).forEach(function (fig) {
      var title = fig.t || fig.id;
      var body = [fig.p, fig.m, fig.id].filter(Boolean).join(" · ");
      out.push({
        title: title,
        route: fig.r,
        body: body,
        titleLow: title.toLowerCase(),
        headLow: "",
        bodyLow: body.toLowerCase()
      });
    });

    return out;
  }

  /* ---- matching ------------------------------------------------------ */

  function words(query) {
    return query.toLowerCase().split(/\s+/).filter(function (w) { return w.length > 0; });
  }

  function isWordStart(haystack, at) {
    if (at === 0) return true;
    return !/[a-z0-9]/.test(haystack.charAt(at - 1));
  }

  // Occurrences of `term`, counted no further than `cap` so the work stays
  // bounded however long a page is.
  function countUpTo(hay, term, cap) {
    var n = 0;
    var at = hay.indexOf(term);
    while (at > -1 && n < cap) {
      n++;
      at = hay.indexOf(term, at + term.length);
    }
    return n;
  }

  // AND across terms: every term must appear somewhere in the record, or the
  // record scores zero and is dropped.
  //
  // Title beats heading beats body, and a match at a word start beats one
  // inside a longer word ("rent" in "Rents rose" over "rent" in "different").
  // Body matches also carry term frequency, which is what separates the page
  // a word is ABOUT from a page that mentions it once in passing: "microgrids"
  // appears twice on /sectors/energy/ and once in the homepage's sector
  // teaser, and without this the homepage won on the tie-break alone.
  function score(rec, terms) {
    var total = 0;
    for (var i = 0; i < terms.length; i++) {
      var term = terms[i];
      var inTitle = rec.titleLow.indexOf(term);
      var inHead = rec.headLow.indexOf(term);
      var inBody = rec.bodyLow.indexOf(term);
      if (inTitle === -1 && inHead === -1 && inBody === -1) return 0;
      if (inTitle > -1) total += isWordStart(rec.titleLow, inTitle) ? 12 : 8;
      if (inHead > -1) total += isWordStart(rec.headLow, inHead) ? 5 : 3;
      if (inBody > -1) {
        total += (isWordStart(rec.bodyLow, inBody) ? 2 : 1) +
          (countUpTo(rec.bodyLow, term, TF_CAP) - 1);
      }
    }
    return total;
  }

  function search(terms) {
    var hits = [];
    if (!terms.length || !records) return hits;
    for (var i = 0; i < records.length; i++) {
      var s = score(records[i], terms);
      if (s > 0) hits.push({ rec: records[i], score: s });
    }
    hits.sort(function (a, b) {
      if (b.score !== a.score) return b.score - a.score;
      return a.rec.title.length - b.rec.title.length;
    });
    return hits;
  }

  /* ---- snippet ------------------------------------------------------- */

  // Window of body text around the earliest matched term, snapped outward to
  // whole words. When a term matched only the title, the opening of the body
  // is shown instead, so a result always carries context.
  function snippet(rec, terms) {
    var at = -1;
    var len = 0;
    for (var i = 0; i < terms.length; i++) {
      var k = rec.bodyLow.indexOf(terms[i]);
      if (k > -1 && (at === -1 || k < at)) { at = k; len = terms[i].length; }
    }
    if (at === -1) { at = 0; len = 0; }

    var start = Math.max(0, at - LEAD);
    var end = Math.min(rec.body.length, at + len + TRAIL);
    if (start > 0) {
      var sp = rec.body.indexOf(" ", start);
      if (sp > -1 && sp < at) start = sp + 1;
    }
    if (end < rec.body.length) {
      var ep = rec.body.lastIndexOf(" ", end);
      if (ep > at + len) end = ep;
    }
    return (start > 0 ? "…" : "") +
      rec.body.slice(start, end) +
      (end < rec.body.length ? "…" : "");
  }

  // Text nodes and <mark> only — never innerHTML.
  function paint(target, text, terms) {
    var low = text.toLowerCase();
    var i = 0;
    while (i < text.length) {
      var at = -1;
      var len = 0;
      for (var t = 0; t < terms.length; t++) {
        var k = low.indexOf(terms[t], i);
        if (k > -1 && (at === -1 || k < at)) { at = k; len = terms[t].length; }
      }
      if (at === -1) break;
      if (at > i) target.appendChild(document.createTextNode(text.slice(i, at)));
      var mark = document.createElement("mark");
      mark.textContent = text.slice(at, at + len);
      target.appendChild(mark);
      i = at + len;
    }
    if (i < text.length) target.appendChild(document.createTextNode(text.slice(i)));
  }

  /* ---- rendering ----------------------------------------------------- */

  function clear(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
  }

  function row(hit, terms) {
    var li = document.createElement("li");
    li.className = "so-result";

    var link = document.createElement("a");
    link.className = "so-result-link";
    link.href = hit.rec.route;

    var title = document.createElement("span");
    title.className = "so-result-title";
    paint(title, hit.rec.title, terms);

    var snip = document.createElement("span");
    snip.className = "so-result-snippet";
    paint(snip, snippet(hit.rec, terms), terms);

    var route = document.createElement("span");
    route.className = "so-result-route";
    route.textContent = hit.rec.route;

    link.appendChild(title);
    link.appendChild(snip);
    link.appendChild(route);
    li.appendChild(link);
    return li;
  }

  function render(query) {
    var terms = words(query);
    clear(resultsList);
    if (!terms.length) { status.textContent = ""; return; }

    var hits = search(terms);
    status.textContent = hits.length
      ? String(hits.length) + (hits.length === 1 ? " result" : " results")
      : "No results";

    // EVERY hit is rendered — there is no "first N" cut. The index holds 90
    // records, so the worst case is 90 list items, and a count that does not
    // equal what is on screen is a counter that lies. The list scrolls; the
    // number does not need to be trimmed to make it fit.
    var frag = document.createDocumentFragment();
    hits.forEach(function (hit) {
      frag.appendChild(row(hit, terms));
    });
    resultsList.appendChild(frag);
  }

  function update() {
    var query = input.value.trim();
    if (!query) { clear(resultsList); status.textContent = ""; return; }
    if (records) { render(query); return; }
    load().then(function () {
      // The reader may have typed on while the index was in flight.
      render(input.value.trim());
    }).catch(function () {
      clear(resultsList);
      status.textContent = "Search is unavailable.";
    });
  }

  /* ---- wiring -------------------------------------------------------- */

  input.addEventListener("input", update);

  // Enter opens the first result. This is a link navigation, not a submit:
  // the input is not in a form and nothing is posted anywhere.
  input.addEventListener("keydown", function (e) {
    if (e.key !== "Enter") return;
    var first = resultsList.querySelector("a.so-result-link");
    if (first) { e.preventDefault(); first.click(); }
  });

  // ui.js sets .open on the overlay. Warm the index and take focus once it is
  // open, after ui.js has done its own focus() for this tick.
  if (typeof MutationObserver === "function") {
    var wasOpen = overlay.classList.contains("open");
    new MutationObserver(function () {
      var isOpen = overlay.classList.contains("open");
      if (isOpen === wasOpen) return;
      wasOpen = isOpen;
      if (!isOpen) return;
      load().catch(function () { /* reported on the next keystroke */ });
      input.focus();
    }).observe(overlay, { attributes: true, attributeFilter: ["class"] });
  }

  box.hidden = false;   // reveal only once the behaviour exists
})();

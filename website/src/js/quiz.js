/* The cost-of-living quiz at /quiz/ (records/changes/CHG-019).
 *
 * Progressive enhancement of quiz.njk: without this file the page is a plain
 * list of the five questions with their sourced answers. With it, the page
 * asks one question at a time, a slider and a linked number input take the
 * guess, and "Check my guess" reveals the record.
 *
 * Every number shown comes from the page: each answer's value and display
 * figure sit in data attributes that quiz.njk fills from sources/register.csv.
 * No figure is typed in this file.
 *
 * Privacy: the guesses never leave the browser. This file makes no network
 * request and uses no cookies, localStorage, sessionStorage or analytics. The
 * only data that goes anywhere is what someone types into the updates form,
 * which ui.js handles exactly as on every other page.
 *
 * CSP (website/src/_headers): loaded from 'self'; no inline script, style or
 * on* handler is used or created.
 */
(function () {
  "use strict";

  var root = document.querySelector("[data-quiz]");
  if (!root) return;

  var items = Array.prototype.slice.call(root.querySelectorAll("[data-quiz-q]"));
  var end = root.querySelector("[data-quiz-end]");
  var live = root.querySelector("[data-quiz-live]");
  if (!items.length || !end) return;

  var guesses = [];
  var WITHIN = 1; // a guess within one percentage point counts as close

  // "−2.5" for display: a typographic minus, and no trailing ".0".
  function fmt(n) {
    var s = (Math.round(n * 10) / 10).toString();
    return s.charAt(0) === "-" ? "−" + s.slice(1) : s;
  }

  function points(n) {
    var s = fmt(Math.abs(n));
    return s + (s === "1" ? " point" : " points");
  }

  // The comparison in words, never by colour alone.
  function verdict(diff) {
    if (Math.abs(diff) <= WITHIN) return "within " + points(WITHIN);
    return (diff < 0 ? "under by " : "over by ") + points(diff);
  }

  function announce(text) {
    if (!live) return;
    live.textContent = "";
    // A fresh text node after clearing makes screen readers read it again.
    window.setTimeout(function () { live.textContent = text; }, 50);
  }

  function show(el, on) { if (el) el.hidden = !on; }

  function clamp(input, n) {
    var min = Number(input.min), max = Number(input.max);
    return Math.min(max, Math.max(min, n));
  }

  // The guess controls, built here because they only work with JavaScript:
  // a labelled slider and a labelled number input with the same range, both
  // keyboard operable. Their range and wording come from quiz.njk.
  function el(tag, attrs, text) {
    var e = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    if (text) e.textContent = text;
    return e;
  }

  function buildControls(guess) {
    var n = guess.getAttribute("data-quiz-n");
    var bounds = {
      min: guess.getAttribute("data-min"), max: guess.getAttribute("data-max"),
      step: guess.getAttribute("data-step"), value: guess.getAttribute("data-start"),
    };
    var rangeId = "qz-" + n + "-range", numId = "qz-" + n + "-num";
    var label = el("label", { "class": "quiz-label", "for": rangeId }, guess.getAttribute("data-label"));
    var range = el("input", Object.assign({ "class": "quiz-range", type: "range", id: rangeId, "data-quiz-range": "" }, bounds));
    var wrap = el("div", { "class": "quiz-num" });
    wrap.appendChild(el("label", { "for": numId }, guess.getAttribute("data-num-label")));
    wrap.appendChild(el("input", Object.assign({ type: "number", id: numId, inputmode: "decimal", "data-quiz-num": "" }, bounds)));
    wrap.appendChild(el("span", { "aria-hidden": "true" }, "%"));
    var actions = guess.querySelector(".actions");
    guess.insertBefore(label, actions);
    guess.insertBefore(range, actions);
    guess.insertBefore(wrap, actions);
  }

  items.forEach(function (item, i) {
    var guess = item.querySelector("[data-quiz-guess]");
    if (guess) buildControls(guess);
    var range = item.querySelector("[data-quiz-range]");
    var num = item.querySelector("[data-quiz-num]");
    var check = item.querySelector("[data-quiz-check]");
    var reveal = item.querySelector("[data-quiz-reveal]");
    var said = item.querySelector("[data-quiz-verdict]");
    var nextWrap = item.querySelector("[data-quiz-next-wrap]");
    var next = item.querySelector("[data-quiz-next]");
    var heading = item.querySelector("h2");
    var revealHeading = reveal && reveal.querySelector("h3");
    if (!guess || !range || !num || !check || !reveal || !said || !next) return;

    // Enhanced state: the controls show, the answer waits, one question at a time.
    show(guess, true);
    show(reveal, false);
    show(item, i === 0);
    if (i === items.length - 1) next.textContent = "See my results";

    // The slider and the number input stay in step.
    range.addEventListener("input", function () { num.value = range.value; });
    num.addEventListener("input", function () {
      var n = parseFloat(num.value);
      if (!isNaN(n)) range.value = String(clamp(range, n));
    });
    num.addEventListener("change", function () {
      var n = parseFloat(num.value);
      num.value = String(isNaN(n) ? range.value : clamp(num, n));
      range.value = num.value;
    });

    check.addEventListener("click", function () {
      var n = parseFloat(num.value);
      var g = clamp(range, isNaN(n) ? parseFloat(range.value) : n);
      num.value = String(g);
      range.value = String(g);
      var record = parseFloat(reveal.getAttribute("data-quiz-value"));
      var display = reveal.getAttribute("data-quiz-display");
      var diff = g - record;
      guesses[i] = { guess: g, diff: diff };

      var text = "You guessed " + fmt(g) + "%. The record says " + display + ". " +
        "Your guess was " + verdict(diff) + ".";
      said.textContent = text;
      show(said, true);
      range.disabled = true;
      num.disabled = true;
      show(check.parentNode, false);
      show(reveal, true);
      show(nextWrap, true);
      announce(text);
      if (revealHeading) revealHeading.focus();
    });

    next.addEventListener("click", function () {
      show(item, false);
      var following = items[i + 1];
      if (following) {
        show(following, true);
        var h = following.querySelector("h2");
        if (h) h.focus();
        return;
      }
      finish();
    });

    if (heading) heading.setAttribute("tabindex", "-1");
  });

  function finish() {
    var rows = end.querySelectorAll("[data-quiz-sum-row]");
    Array.prototype.forEach.call(rows, function (row, i) {
      var r = guesses[i];
      var g = row.querySelector("[data-quiz-sum-guess]");
      var d = row.querySelector("[data-quiz-sum-diff]");
      if (g) g.textContent = r ? fmt(r.guess) + "%" : "Not answered";
      if (d) d.textContent = r ? verdict(r.diff).replace(/^./, function (c) { return c.toUpperCase(); }) : "";
    });
    show(end.querySelector("[data-quiz-nojs]"), false);
    show(end.querySelector("[data-quiz-summary]"), true);
    show(end.querySelector("[data-quiz-share-wrap]"), true);
    show(end, true);
    announce("Your guesses vs. the record.");
    var h = end.querySelector("h2");
    if (h) h.focus();
  }

  // The end block waits until the last question.
  show(end, false);

  // js/quiz-early.js hid the answers until now (integration.css item 150).
  // Every part now carries its own `hidden` state, so the mark comes off and
  // that state decides from here on.
  document.documentElement.classList.remove("quiz-js");

  // Share the quiz, never the score: the shared text is the page's own
  // description and URL, with nothing about the reader's guesses.
  var share = root.querySelector("[data-quiz-share]");
  var note = root.querySelector("[data-quiz-share-note]");
  if (share) {
    share.addEventListener("click", function () {
      var url = root.getAttribute("data-quiz-url");
      var data = { title: document.title, text: root.getAttribute("data-quiz-text") || "", url: url };
      if (navigator.share) {
        navigator.share(data).catch(function () { /* cancelled: nothing to do */ });
        return;
      }
      var said = function (t) { if (note) note.textContent = t; };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(
          function () { said("Link copied."); },
          function () { said("Copy this link: " + url); }
        );
      } else {
        said("Copy this link: " + url);
      }
    });
  }
})();

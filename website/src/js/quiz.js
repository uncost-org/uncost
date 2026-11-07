/* The cost-of-living quiz at /quiz/ (records/changes/CHG-019).
 *
 * Progressive enhancement of quiz.njk: without this file the page is a plain
 * list of the ten questions with their sourced answers. With it, the page asks
 * one question at a time as multiple choice: a native radio group (a fieldset
 * whose legend is the question), "Check my answer" once a choice is picked,
 * then the record.
 *
 * Every choice and every number shown comes from the page: quiz.njk lists each
 * question's choices (data-quiz-choice, the right one marked
 * data-quiz-correct), all made at build time from sources/register.csv by
 * _data/quiz.js. No figure is typed in this file. The radios are built here
 * because the content audit allows no form control in the built HTML.
 *
 * Privacy: the answers never leave the browser. This file makes no network
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

  // One entry per question once it is checked: the text picked, and whether it
  // was the right choice.
  var answers = [];

  function announce(text) {
    if (!live) return;
    live.textContent = "";
    // A fresh text node after clearing makes screen readers read it again.
    window.setTimeout(function () { live.textContent = text; }, 50);
  }

  function show(el, on) { if (el) el.hidden = !on; }

  function el(tag, attrs, text) {
    var e = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    if (text) e.textContent = text;
    return e;
  }

  // The radio group, built from the page's own list of choices. The question
  // heading moves into the legend, so the group is named by the question and
  // the question is read once.
  function buildGroup(item, n) {
    var heading = item.querySelector("h2");
    var list = item.querySelector("[data-quiz-choices]");
    if (!heading || !list) return null;
    var choices = Array.prototype.map.call(list.querySelectorAll("[data-quiz-choice]"), function (li) {
      return { text: li.textContent.trim(), correct: li.hasAttribute("data-quiz-correct") };
    });
    if (choices.length < 2 || choices.filter(function (c) { return c.correct; }).length !== 1) return null;
    var fieldset = el("fieldset", { "class": "quiz-choices" });
    var legend = el("legend", { "class": "quiz-legend" });
    var box = el("div", { "class": "quiz-options" });
    heading.parentNode.insertBefore(fieldset, heading);
    legend.appendChild(heading);
    fieldset.appendChild(legend);
    fieldset.appendChild(box);
    choices.forEach(function (c, j) {
      var id = "qz-" + n + "-c" + (j + 1);
      var label = el("label", { "class": "quiz-choice", "for": id });
      var input = el("input", { type: "radio", id: id, name: "qz-" + n, value: String(j) });
      var body = el("span", { "class": "quiz-choice-body" });
      var mark = el("span", { "class": "quiz-mark", "data-quiz-mark": "" });
      mark.hidden = true;
      body.appendChild(el("span", { "class": "quiz-choice-text" }, c.text));
      body.appendChild(mark);
      label.appendChild(input);
      label.appendChild(body);
      box.appendChild(label);
      c.input = input;
      c.mark = mark;
    });
    list.parentNode.removeChild(list);
    return { fieldset: fieldset, choices: choices };
  }

  items.forEach(function (item, i) {
    var n = String(i + 1);
    var guess = item.querySelector("[data-quiz-guess]");
    var check = item.querySelector("[data-quiz-check]");
    var reveal = item.querySelector("[data-quiz-reveal]");
    var said = item.querySelector("[data-quiz-verdict]");
    var nextWrap = item.querySelector("[data-quiz-next-wrap]");
    var next = item.querySelector("[data-quiz-next]");
    if (!guess || !check || !reveal || !said || !next) return;
    var group = buildGroup(item, n);
    if (!group) return;
    var revealHeading = reveal.querySelector("h3");

    // Enhanced state: the choices show, the answer waits, one question at a time.
    show(guess, true);
    show(reveal, false);
    show(item, i === 0);
    if (i === items.length - 1) next.textContent = "See my results";

    // "Check my answer" waits for a choice.
    check.disabled = true;
    group.fieldset.addEventListener("change", function () { check.disabled = false; });

    check.addEventListener("click", function () {
      var picked = null;
      var right = null;
      group.choices.forEach(function (c) {
        if (c.input.checked) picked = c;
        if (c.correct) right = c;
      });
      if (!picked || !right) return;
      // Marked in words, never by colour alone.
      picked.mark.textContent = picked === right ? "Your answer · The record" : "Your answer";
      show(picked.mark, true);
      if (picked !== right) {
        right.mark.textContent = "The record";
        show(right.mark, true);
      }
      group.choices.forEach(function (c) {
        if (c === picked) c.input.parentNode.setAttribute("data-quiz-picked", "");
        if (c === right) c.input.parentNode.setAttribute("data-quiz-right", "");
      });
      answers[i] = { text: picked.text, correct: picked === right };
      group.fieldset.disabled = true;

      said.textContent = picked === right ? "Right." : "Not quite.";
      show(said, true);
      show(check.parentNode, false);
      show(reveal, true);
      show(nextWrap, true);
      announce(picked === right
        ? "Right. The record: " + right.text + "."
        : "Not quite. Your answer: " + picked.text + ". The record: " + right.text + ".");
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
  });

  function finish() {
    var score = 0;
    var rows = end.querySelectorAll("[data-quiz-sum-row]");
    Array.prototype.forEach.call(rows, function (row, i) {
      var a = answers[i];
      if (a && a.correct) score += 1;
      var mine = row.querySelector("[data-quiz-sum-answer]");
      var right = row.querySelector("[data-quiz-sum-right]");
      if (mine) mine.textContent = a ? a.text : "Not answered";
      if (right) right.textContent = a && a.correct ? "Yes" : "No";
    });
    var count = end.querySelector("[data-quiz-score-n]");
    if (count) count.textContent = String(score);
    show(end.querySelector("[data-quiz-score]"), true);
    show(end.querySelector("[data-quiz-summary]"), true);
    show(end.querySelector("[data-quiz-share-wrap]"), true);
    show(end, true);
    var line = end.querySelector("[data-quiz-score]");
    announce(line ? line.textContent.replace(/\s+/g, " ").trim() : "Your answers vs. the record.");
    var h = end.querySelector("h2");
    if (h) h.focus();
  }

  // The no-JavaScript lines ("The answer: …", the end block's note) and the
  // end block wait: the choices and the summary say the same.
  Array.prototype.forEach.call(root.querySelectorAll("[data-quiz-nojs]"), function (p) { show(p, false); });
  show(end, false);

  // js/quiz-early.js hid the answers until now (integration.css item 150).
  // Every part now carries its own `hidden` state, so the mark comes off and
  // that state decides from here on.
  document.documentElement.classList.remove("quiz-js");

  // Share the quiz, never the score: the shared text is the page's own
  // description and URL, with nothing about the reader's answers.
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

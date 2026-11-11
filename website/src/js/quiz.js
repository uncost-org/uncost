/* The cost-of-living quiz at /quiz/ (records/changes/CHG-019).
 *
 * Progressive enhancement of quiz.njk: without this file the page is a plain
 * list of the ten questions with their sourced answers. With it, the page asks
 * one question at a time as multiple choice: a native radio group (a fieldset
 * whose legend is the question), "Check my answer" once a choice is picked,
 * then the verdict ("Correct!" or "Not quite.", in words, never by colour
 * alone) and the sourced figure. The choices are tagged "Your answer" and
 * "Correct answer"; the announcement uses the same words.
 *
 * Every choice and every number shown comes from the page: quiz.njk lists each
 * question's choices (data-quiz-choice, the right one marked
 * data-quiz-correct), all made at build time from sources/register.csv by
 * _data/quiz.js. No figure is typed in this file. The radios are built here
 * because the content audit allows no form control in the built HTML.
 *
 * Privacy: this file sets no cookies and uses no localStorage,
 * sessionStorage or analytics, ever. In a
 * build with the anonymous score tally off (the default), this file makes no
 * network request: the answers never leave the browser. In a build with it on
 * (features.quizStatsOpen; data-quiz-stats on the quiz), and only then, it
 * sends ONE request when the reader reaches the end screen — POST
 * /api/quiz/score with the question set's version and a 0 or 1 per question,
 * nothing else — and, if that is accepted, reads the tally for this question
 * set (GET /api/quiz/stats) to show the average. Nothing is sent before the
 * end screen, and nothing twice. If either request fails, or the endpoints are
 * switched off (404), the reader sees their own score only, never an error.
 * Both requests are same-origin and go with credentials: "same-origin", as
 * the page's own requests do, so they carry only cookies the browser already
 * holds for this site. The site sets none; on a preview, Cloudflare Access's
 * sign-in cookie, without which Access answers with a redirect to its login
 * and the score never arrives (CHG-019, 2026-11-09). The endpoints read no
 * cookie and store none.
 * The only other data that goes anywhere is what someone types into the
 * site footer's updates form, which ui.js handles as on every other page.
 * The share panel's links are navigation the reader chooses, to a network's
 * own share page, carrying the quiz's address and share text only (as the
 * /pledge/thanks/ share row does); nothing from any network loads here.
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
  var statsOn = root.hasAttribute("data-quiz-stats");
  var sent = false;

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
    // The right answer as the register gives it (a pick question's choice may
    // read "About …"; this is the exact figure, as the figure card shows it).
    var record = guess.getAttribute("data-quiz-record");

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
      picked.mark.textContent = picked === right ? "Your answer · Correct answer" : "Your answer";
      show(picked.mark, true);
      if (picked !== right) {
        right.mark.textContent = "Correct answer";
        show(right.mark, true);
      }
      group.choices.forEach(function (c) {
        if (c === picked) c.input.parentNode.setAttribute("data-quiz-picked", "");
        if (c === right) c.input.parentNode.setAttribute("data-quiz-right", "");
      });
      answers[i] = { text: picked.text, correct: picked === right };
      group.fieldset.disabled = true;

      // The verdict line: words first; integration.css item 150 colours it
      // by data-quiz-result (green for right, red for wrong).
      said.textContent = picked === right ? "Correct!" : "Not quite.";
      said.setAttribute("data-quiz-result", picked === right ? "right" : "wrong");
      show(said, true);
      show(check.parentNode, false);
      show(reveal, true);
      show(nextWrap, true);
      var recordText = record || right.text;
      announce(picked === right
        ? "Correct! Your answer: " + picked.text + ". Correct answer: " + recordText + "."
        : "Not quite. Your answer: " + picked.text + ". Correct answer: " + recordText + ".");
      said.focus();
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
    var bits = "";
    var rows = end.querySelectorAll("[data-quiz-sum-row]");
    Array.prototype.forEach.call(rows, function (row, i) {
      var a = answers[i];
      if (a && a.correct) score += 1;
      bits += a && a.correct ? "1" : "0";
      var mine = row.querySelector("[data-quiz-sum-answer]");
      var right = row.querySelector("[data-quiz-sum-right]");
      if (mine) mine.textContent = a ? a.text : "Not answered";
      if (right) {
        right.textContent = "";
        right.appendChild(el("span", { "class": "quiz-result", "data-quiz-result": a && a.correct ? "right" : "wrong" },
          a && a.correct ? "Correct!" : "Not quite."));
      }
    });
    var count = end.querySelector("[data-quiz-score-n]");
    if (count) count.textContent = String(score);
    show(end.querySelector("[data-quiz-score]"), true);
    show(end.querySelector("[data-quiz-summary]"), true);
    show(end.querySelector("[data-quiz-share]"), true);
    show(end, true);
    announce(scoreText() || "Your answers.");
    var h = end.querySelector("h2");
    if (h) h.focus();
    if (items.every(function (_, i) { return !!answers[i]; })) tally(bits, score, rows);
  }

  // The anonymous tally (only in a build with it on): one POST per page load,
  // at the end screen, then the tally for this question set. Any failure, or a
  // 404 from switched-off endpoints, leaves the reader's own score alone.
  var MIN_COUNT = 30;
  function getJson(url, init) {
    return window.fetch(url, init).then(function (r) {
      if (!r.ok) throw new Error(String(r.status));
      return r.status === 204 ? null : r.json();
    });
  }
  function tally(bits, score, rows) {
    if (!statsOn || sent || !window.fetch) return;
    sent = true;
    var version = root.getAttribute("data-quiz-version") || "";
    var stop = window.AbortController ? new AbortController() : null;
    var timer = stop ? window.setTimeout(function () { stop.abort(); }, 10000) : 0;
    // "same-origin", not "omit": a preview sits behind Cloudflare Access,
    // which redirects a request without its cookie (see the header comment).
    var init = { credentials: "same-origin", cache: "no-store", signal: stop ? stop.signal : undefined };
    getJson("/api/quiz/score", Object.assign({ method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ version: version, answers: bits }) }, init))
      .then(function () { return getJson("/api/quiz/stats?version=" + encodeURIComponent(version), Object.assign({ method: "GET" }, init)); })
      .then(function (s) { showStats(s, score, rows); })
      .catch(function () { /* own score only */ })
      .then(function () { window.clearTimeout(timer); });
  }
  // The rest of the score block, one line each (CHG-020): the average (two
  // decimals, as the stats give it), then how far this score is from it, as a
  // whole percent of the average. A difference that rounds to 0% is a match
  // (null: "You matched the average.", plain); otherwise the figure ("21%
  // higher") and its direction, which only sets its colour.
  function compared(score, mean) {
    if (mean === 0) return score === 0 ? null : { fig: "higher", dir: "higher" };
    var p = Math.round(Math.abs(score - mean) / mean * 100);
    if (p === 0) return null;
    var dir = score > mean ? "higher" : "lower";
    return { fig: p + "% " + dir, dir: dir };
  }
  // A line of plain text with one figure in it: strong.quiz-fig, bold and
  // underlined, not a link (no href, no tabindex, no pointer).
  function figLine(p, before, fig, after, dir) {
    p.textContent = "";
    p.appendChild(document.createTextNode(before));
    var f = el("strong", { "class": "quiz-fig" }, fig);
    if (dir) f.setAttribute("data-quiz-dir", dir);
    p.appendChild(f);
    p.appendChild(document.createTextNode(after));
  }
  // The score block's shown lines, in order, as the announcement reads them.
  function scoreText() {
    var lines = end.querySelectorAll("[data-quiz-score] .quiz-line");
    return Array.prototype.filter.call(lines, function (p) { return !p.hidden; })
      .map(function (p) { return p.textContent.replace(/\s+/g, " ").trim(); })
      .filter(Boolean).join(" ");
  }
  function showStats(s, score, rows) {
    var avg = end.querySelector("[data-quiz-average]");
    var cmp = end.querySelector("[data-quiz-compare]");
    if (!avg || !cmp || !s || typeof s.count !== "number") return;
    if (s.count < MIN_COUNT || typeof s.mean !== "number") {
      avg.textContent = "Not enough players yet to show an average.";
    } else {
      var mean = Math.round(s.mean * 100) / 100;
      figLine(avg, "The current average score is ", mean.toFixed(2), ".");
      var c = compared(score, mean);
      if (c) figLine(cmp, "You scored ", c.fig, " than the average.", c.dir);
      else cmp.textContent = "You matched the average.";
      show(cmp, true);
      if (Array.isArray(s.perQuestion)) {
        Array.prototype.forEach.call(rows, function (row, i) {
          var share = s.perQuestion[i];
          var cell = row.querySelector("[data-quiz-sum-right]");
          if (cell && typeof share === "number") {
            cell.appendChild(el("span", { "class": "quiz-share" }, Math.round(share * 100) + "% got this right"));
          }
        });
      }
    }
    show(avg, true);
    // The whole block again, in order: the score, then the new line or lines.
    announce(scoreText());
  }

  // The no-JavaScript lines ("The answer: …", the end block's note) and the
  // end block wait: the choices and the summary say the same.
  Array.prototype.forEach.call(root.querySelectorAll("[data-quiz-nojs]"), function (p) { show(p, false); });

  // In a build with the tally on, this reader (with JavaScript) will send
  // their score at the end, so the intro says so. integration.css already
  // showed the tally line under .quiz-js; this keeps it once the mark is off.
  var tallyNote = document.querySelector("[data-quiz-tally-note]");
  if (statsOn && tallyNote) {
    show(document.querySelector("[data-quiz-local-note]"), false);
    show(tallyNote, true);
  }
  show(end, false);

  // js/quiz-early.js hid the answers until now (integration.css item 150).
  // Every part now carries its own `hidden` state, so the mark comes off and
  // that state decides from here on.
  document.documentElement.classList.remove("quiz-js");

  // Share the quiz, never the score: the panel's links (quiz.njk) carry the
  // page's own address and share text, with nothing about the reader's
  // answers, and so does the system share sheet. Where the browser has one
  // and the screen is a phone's (600px and below, as /pledge/thanks/ decides),
  // "Share this quiz" opens the sheet; everywhere else, or if the sheet fails,
  // it opens the panel. Escape closes the panel and puts focus back on the
  // button.
  var share = root.querySelector("[data-quiz-share]");
  var panel = root.querySelector("[data-quiz-share-panel]");
  var copy = root.querySelector("[data-quiz-copy]");
  var note = root.querySelector("[data-quiz-share-note]");
  var url = root.getAttribute("data-quiz-url");
  var said = function (t) { if (note) note.textContent = t; };
  function setPanel(open, refocus) {
    if (!panel || !share) return;
    show(panel, open);
    share.setAttribute("aria-expanded", open ? "true" : "false");
    if (open) {
      var first = panel.querySelector("a, button");
      if (first) first.focus();
    } else if (refocus) {
      share.focus();
    }
  }
  if (panel) {
    show(panel, false);
    show(root.querySelector("[data-quiz-copy-wrap]"), true);
    panel.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !panel.hidden) { e.preventDefault(); setPanel(false, true); }
    });
  }
  if (share) {
    share.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && panel && !panel.hidden) { e.preventDefault(); setPanel(false, true); }
    });
    share.addEventListener("click", function () {
      if (panel && !panel.hidden) { setPanel(false, false); return; }
      var phone = window.matchMedia && window.matchMedia("(max-width: 600px)").matches;
      if (navigator.share && phone) {
        navigator.share({ title: document.title, text: root.getAttribute("data-quiz-text") || "", url: url })
          .catch(function (err) { if (!err || err.name !== "AbortError") setPanel(true); });
        return;
      }
      setPanel(true);
    });
  }
  if (copy) {
    copy.addEventListener("click", function () {
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

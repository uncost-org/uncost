/* The cost-of-living quiz at /quiz/ (records/changes/CHG-019): the early step.
 *
 * quiz.njk loads this without defer, just before the quiz, so it runs before
 * the parser reaches the answers. It marks <html> with .quiz-js, and
 * integration.css item 150 then hides the answers, the end block and every
 * question after the first. js/quiz.js (deferred) removes the mark once it
 * has set its own state, so from then on its `hidden` toggling decides.
 *
 * If js/quiz.js never runs (it failed to load), the mark comes off at the
 * window's load event, which follows every deferred script, and the page is
 * the plain no-JavaScript list again.
 *
 * No network request, no cookies, no storage. CSP: loaded from 'self'.
 */
(function () {
  "use strict";
  var html = document.documentElement;
  html.classList.add("quiz-js");
  window.addEventListener("load", function () { html.classList.remove("quiz-js"); });
})();

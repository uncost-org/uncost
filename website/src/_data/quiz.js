// The cost-of-living quiz at /quiz/ (records/changes/CHG-019).
//
// Ten multiple-choice questions, in the order the quiz asks them. This file
// holds the question list and nothing else that a reader sees as a figure:
// every answer — and every number a question states — comes from
// sources/register.csv through _data/register.js, so the Friday review and the
// monthly refresh change the quiz by updating the register. Never type a figure
// here, in quiz.njk, in js/quiz.js or in the copy.
//
// Three kinds of question:
//
//   pick     Pick the figure (four choices). The right choice is the row's
//            display_value (or one side of an "X versus Y" value, `part`). The
//            three wrong choices are made here, at build time, by one fixed
//            rule (no randomness, so every build is the same): a ladder of
//            four values, each LADDER times the one below, with the record on
//            one rung. They are rounded to the record's own precision —
//            percents to its decimal places, money and counts to its decimal
//            places when it shows cents and otherwise to its significant
//            figures — and written in the record's own style. Choices are shown
//            low to high, so the record's rung is its position: each question
//            starts from the next rung in RANK_ORDER, and moves to the next
//            rung only when a rule below fails there.
//   most     Which rose most? (three or four choices). Every choice is a real
//            register row; the right one is the row whose percent is highest.
//   compare  Higher or lower (two choices). The answer is computed from two
//            values the row states: its "X versus Y" display_value, or two
//            numbers read out of its receipt by `pattern`.
//
// Build guard (no fake numbers). The build fails if, for any row in the set:
//   - it is missing from the register, or has an empty display_value,
//     display_caption, data_period, source_line or url;
//   - a question states a number that is not in the same row's caption or
//     receipt (a "most" question may state none);
//   - a row's figure card would appear twice on the page (cards carry an id);
// and, by kind:
//   - pick: the value does not parse, the record's own text cannot be rebuilt
//     from its value, or no rung gives four distinct choices, each wrong one at
//     least MIN_GAP (a fifth) away from the record, inside the bounds (a share
//     stays between nothing and the whole), without the record being the only
//     choice whose last digit is or is not a zero;
//   - most: a value is not a single percent, the data periods are not the same
//     period, or the highest value is tied;
//   - compare: the two values cannot be read, or they are equal;
// and if every question puts the right answer in the same position.
// checked_by is deliberately NOT required: it is empty on every row today (a
// finding for the founder, not something to fill in here).
const register = require("./register.js");

const QUESTIONS = [
  { kind: "pick", id: "SRC-025", topic: "Prices overall",
    question: "Over the past year, how much did prices overall go up?" },
  { kind: "most", topic: "What went up most",
    question: "Which of these went up most over the past year?",
    choices: [
      { id: "SRC-026", label: "Groceries" },
      { id: "SRC-019", label: "Rent" },
      { id: "SRC-003", label: "Water and sewer bills" },
      { id: "SRC-027", label: "Energy" },
    ] },
  { kind: "pick", id: "SRC-028", topic: "The Forbes 400",
    question: "Forbes estimated the combined wealth of the 400 richest Americans at $6.6 trillion a year earlier. What was its estimate for 2026?" },
  { kind: "pick", id: "SRC-024", part: 0, share: true, topic: "The wealthiest households",
    question: "In the second quarter of 2026, what share of the country's net worth did the wealthiest 1% of American households hold?" },
  { kind: "pick", id: "SRC-004", share: true, topic: "Renters and housing costs",
    question: "In 2024, the latest year measured, what share of renter households spent more than 30 percent of their income on rent and utilities?" },
  { kind: "compare", id: "SRC-022", topic: "Rent and renters' income",
    question: "Between 2001 and 2024, after inflation, did the median rent rise faster or slower than the median renter's income?",
    // display_value "A versus B": rent, then income. choices[0] when A > B.
    choices: ["Faster", "Slower"] },
  { kind: "pick", id: "SRC-023", topic: "Ground beef",
    question: "What did a pound of ground beef cost in September 2026?" },
  { kind: "pick", id: "SRC-006", topic: "Family health coverage",
    question: "On average, what did a year of family health coverage through an employer cost in 2025?" },
  { kind: "compare", id: "SRC-011", topic: "Household appliances",
    question: "Before adjusting for inflation, do household appliances cost more or less than they did in 1997?",
    // The receipt's index level against its own base: A is the latest level,
    // B the base. choices[0] when A > B.
    pattern: /base December 1997=(\d+(?:\.\d+)?): (\d+(?:\.\d+)?) \(September 2026\)/, a: 2, b: 1,
    choices: ["More", "Less"] },
  { kind: "pick", id: "SRC-018", topic: "Homelessness",
    question: "On a single night in January 2025, how many people were homeless in the United States?" },
];

const REQUIRED = ["display_value", "display_caption", "data_period", "source_line", "url"];
// "3.7%", "-0.4%", "+2%", "20.4 %": a signed decimal followed by a percent sign.
const PERCENT = /^([+\-−]?\d+(?:\.\d+)?)(\s?)%$/;
// "$6.79", "$26,993", "$8 trillion".
const MONEY = /^\$(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d+))?(?:\s(trillion|billion|million))?$/;
// "745,652".
const COUNT = /^(\d{1,3}(?:,\d{3})+|\d+)$/;
const VERSUS = " versus ";
// A number a question states: "$6.6 trillion", "30 percent", "1%", "2024", "400".
const STATED = /\$?\d(?:[\d,]*\d)?(?:\.\d+)?(?:\s?%|\s(?:percent|trillion|billion|million)\b)?/g;

const LADDER = 1.5;
const MIN_GAP = 0.2;
const RANK_ORDER = [0, 1, 3, 2];

function rowProblems(id, row) {
  if (!row) return [`${id}: not in sources/register.csv`];
  return REQUIRED.filter((f) => !String(row[f] || "").trim()).map((f) => `${id}: ${f} is empty`);
}

// The record's figure and its written style, or null when it does not parse.
function parseFigure(text) {
  const t = String(text).trim();
  let m = PERCENT.exec(t);
  if (m) {
    const num = m[1].replace("−", "-").replace("+", "");
    const dot = num.indexOf(".");
    return { kind: "percent", value: Number(num), decimals: dot < 0 ? 0 : num.length - dot - 1, space: m[2] };
  }
  m = MONEY.exec(t) || COUNT.exec(t);
  if (m) {
    const money = t.startsWith("$");
    const whole = m[1].replace(/,/g, "");
    const cents = money ? m[2] || "" : "";
    const digits = cents ? (whole.replace(/^0+/, "") + cents) : whole.replace(/^0+/, "").replace(/0+$/, "");
    return {
      kind: money ? "money" : "count",
      value: Number(whole + (cents ? "." + cents : "")),
      decimals: cents.length,
      sig: Math.max(1, digits.length),
      unit: money ? m[3] || "" : "",
    };
  }
  return null;
}

// Rounding through toPrecision(12) first, so 3.395 rounds as written, not as
// 3.39499999… in binary.
function roundTo(x, decimals) {
  const f = Math.pow(10, decimals);
  return Math.round(Number((x * f).toPrecision(12))) / f;
}

function roundSig(x, sig) {
  if (x === 0) return 0;
  const p = Math.floor(Math.log10(Math.abs(x))) - sig + 1;
  return p < 0 ? roundTo(x, -p) : Math.round(Number((x / Math.pow(10, p)).toPrecision(12))) * Math.pow(10, p);
}

function roundLike(fig, x) {
  return fig.kind === "percent" || fig.decimals > 0 ? roundTo(x, fig.decimals) : roundSig(x, fig.sig);
}

function formatLike(fig, x) {
  const sign = x < 0 ? "−" : "";
  const fixed = Math.abs(x).toFixed(fig.decimals);
  if (fig.kind === "percent") return sign + fixed + fig.space + "%";
  const [whole, cents] = fixed.split(".");
  const grouped = whole.replace(/\B(?=(\d{3})+(?!\d))/g, ",") + (cents ? "." + cents : "");
  return fig.kind === "money" ? sign + "$" + grouped + (fig.unit ? " " + fig.unit : "") : sign + grouped;
}

const endsInZero = (text) => /0\D*$/.test(text);

// The four choices on one rung of the ladder, or the reason the rung fails.
function rung(fig, recordText, rank, share) {
  const values = [0, 1, 2, 3].map((i) => (i === rank ? fig.value : roundLike(fig, fig.value * Math.pow(LADDER, i - rank))));
  const texts = values.map((v, i) => (i === rank ? recordText : formatLike(fig, v)));
  const wrong = values.filter((_, i) => i !== rank);
  if (share && values.some((v) => v <= 0 || v >= 100)) return { fail: "a share outside the whole" };
  if (fig.kind !== "percent" && wrong.some((v) => v <= 0)) return { fail: "a choice of nothing" };
  if (new Set(texts).size !== 4) return { fail: "two choices read the same" };
  if (wrong.some((v) => Math.abs(v - fig.value) < MIN_GAP * Math.abs(fig.value))) return { fail: "a wrong choice too close to the record" };
  if (texts.every((t, i) => i === rank || endsInZero(t) !== endsInZero(recordText))) return { fail: "the record would stand out by its last digit" };
  return { texts };
}

function pick(q, row, k, problems) {
  let recordText = String(row.display_value).trim();
  if (q.part !== undefined) recordText = recordText.split(VERSUS)[q.part] || "";
  const fig = parseFigure(recordText);
  if (!fig) {
    problems.push(`${q.id}: display_value "${row.display_value}" does not parse as a percent, money or count`);
    return null;
  }
  if (formatLike(fig, fig.value) !== recordText) {
    problems.push(`${q.id}: "${recordText}" cannot be rebuilt from its value, so its choices could not share its style`);
    return null;
  }
  const first = RANK_ORDER[k % RANK_ORDER.length];
  const reasons = [];
  for (let step = 0; step < 4; step++) {
    const rank = (first + step) % 4;
    const r = rung(fig, recordText, rank, q.share);
    if (r.texts) return { choices: r.texts, answer: rank };
    reasons.push(`position ${rank + 1}: ${r.fail}`);
  }
  problems.push(`${q.id}: no position gives four fair choices (${reasons.join("; ")})`);
  return null;
}

function most(q, reg, problems) {
  const rows = q.choices.map((c) => reg.byId[c.id]);
  if (q.choices.length < 3 || q.choices.length > 4) problems.push(`"${q.topic}": a "most" question has three or four choices`);
  const values = [];
  const periods = new Set();
  rows.forEach((row, i) => {
    const m = row && PERCENT.exec(String(row.display_value || "").trim());
    if (!m) {
      if (row) problems.push(`${q.choices[i].id}: display_value "${row.display_value}" is not a single percent`);
      return;
    }
    values[i] = Number(m[1].replace("−", "-").replace("+", ""));
    periods.add(String(row.data_period).replace(/^Year to /i, "").trim());
  });
  if (values.filter((v) => v !== undefined).length !== rows.length) return null;
  if (periods.size !== 1) {
    problems.push(`"${q.topic}": the rows cover different periods (${[...periods].join(" / ")})`);
    return null;
  }
  const top = Math.max(...values);
  if (values.filter((v) => v === top).length !== 1) {
    problems.push(`"${q.topic}": the highest value is tied`);
    return null;
  }
  return { choices: q.choices.map((c) => c.label), answer: values.indexOf(top) };
}

function compare(q, row, problems) {
  let a, b;
  if (q.pattern) {
    const m = q.pattern.exec(String(row.receipt || ""));
    if (m) { a = Number(m[q.a]); b = Number(m[q.b]); }
  } else {
    const parts = String(row.display_value).split(VERSUS).map(parseFigure);
    if (parts.length === 2 && parts[0] && parts[1]) { a = parts[0].value; b = parts[1].value; }
  }
  if (a === undefined || b === undefined || Number.isNaN(a) || Number.isNaN(b)) {
    problems.push(`${q.id}: the two values to compare cannot be read from the row`);
    return null;
  }
  if (a === b) {
    problems.push(`${q.id}: the two values are equal, so neither answer is right`);
    return null;
  }
  return { choices: q.choices.slice(), answer: a > b ? 0 : 1 };
}

// Every number the question states must be in the same row's caption or
// receipt; the template renders the question inside that row's data-source.
function statedProblems(q, rows) {
  const stated = String(q.question).match(STATED) || [];
  if (q.kind === "most") return stated.length ? [`"${q.topic}": a "most" question states ${stated.join(", ")}; it may state no number`] : [];
  const row = rows[0];
  const text = `${row.display_caption} ${row.receipt}`;
  return stated
    .filter((s) => !new RegExp(`(^|[^\\d.,])${s.replace(/[$.]/g, "\\$&")}(?![\\d])`).test(text))
    .map((s) => `${q.id}: the question states "${s}", which is not in the row's caption or receipt`);
}

function build(reg) {
  const problems = [];
  const cardIds = new Set();
  let picks = 0;
  const questions = QUESTIONS.map((q, i) => {
    const ids = q.kind === "most" ? q.choices.map((c) => c.id) : [q.id];
    const rows = ids.map((id) => reg.byId[id]);
    const missing = ids.flatMap((id, j) => rowProblems(id, rows[j]));
    problems.push(...missing);
    if (missing.length) return null;
    problems.push(...statedProblems(q, rows));
    let made;
    if (q.kind === "pick") made = pick(q, rows[0], picks++, problems);
    else if (q.kind === "most") made = most(q, reg, problems);
    else made = compare(q, rows[0], problems);
    if (!made) return null;
    // The row whose figure card the reveal shows, and (for "most") the others,
    // each shown as its one-line caption.
    const row = q.kind === "most" ? rows[made.answer] : rows[0];
    if (cardIds.has(row.source_id)) problems.push(`${row.source_id}: its figure card would appear twice`);
    cardIds.add(row.source_id);
    return {
      n: i + 1,
      kind: q.kind,
      topic: q.topic,
      question: q.question,
      // The question's own row, for its data-source; none for "most".
      sourceId: q.kind === "most" ? "" : q.id,
      choices: made.choices.map((text, j) => ({ text, correct: j === made.answer })),
      answer: made.answer,
      answerText: made.choices[made.answer],
      row,
      others: q.kind === "most" ? rows.filter((r) => r !== row) : [],
    };
  });
  if (!problems.length && new Set(questions.map((q) => q.answer)).size < 2) {
    problems.push("every question puts the right answer in the same position");
  }
  if (problems.length) {
    throw new Error("Quiz guard failed (no fake numbers) — fix sources/register.csv or _data/quiz.js:\n  - " + problems.join("\n  - "));
  }
  return { questions, total: questions.length };
}

module.exports = function () {
  return build(register());
};
Object.assign(module.exports, { QUESTIONS, REQUIRED, PERCENT, LADDER, MIN_GAP, RANK_ORDER, parseFigure, roundLike, formatLike, build });

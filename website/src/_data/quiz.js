// The cost-of-living quiz at /quiz/ (records/changes/CHG-019).
//
// Ten multiple-choice questions, in the order the quiz asks them. This file
// holds the question list and nothing else that a reader sees as a figure:
// every answer — and every number a question states — comes from
// sources/register.csv through _data/register.js, so the Friday review and the
// monthly refresh change the quiz by updating the register. Never type a figure
// here, in quiz.njk, in js/quiz.js or in the copy. The one exception is a
// question's listed wrong choices (`wrong`, below): they are not register
// figures, by design, and are never shown as one.
//
// Three kinds of question:
//
//   pick     Pick the figure (four choices). The right choice is the row's
//            display_value (or one side of an "X versus Y" value, `part`).
//            The three wrong choices are either listed (`wrong`, the
//            founder's, 2026-11-08) or made here, at build time, by one fixed
//            rule (no randomness, so every build is the same): a ladder of
//            four values, each LADDER times the one below, with the record on
//            one rung. Percent choices are rounded to the record's own decimal
//            places and written in its style. Money and count choices are all
//            rounded the same way, to two significant figures of the largest,
//            and read "About …" (founder's call, 2026-11-08: exact wrong
//            choices such as $17,995 looked like real data); the reveal card,
//            the no-JS answer and the announcement keep the exact register
//            figure. A `change` question asks which way and how far a figure
//            moved: its right choice reads "Down about 15%" or "Up about 15%",
//            the size from the row's display_value and the direction from two
//            numbers read out of its receipt by `change.pattern`.
//            Choices are shown low to high, so the record's place among them
//            is its position. A ladder question starts from the next rung in
//            RANK_ORDER (counting ladder questions only), and moves to the
//            next rung only when a rule below fails there. RANK_ORDER is
//            [1, 3, 2] since four questions took listed choices (2026-11-08):
//            it keeps every ladder question's choices as they were.
//   most     Which rose most? (three or four choices). Every choice is a real
//            register row; the right one is the row whose percent is highest.
//   compare  Higher or lower (two choices). The answer is computed from two
//            values the row states: its "X versus Y" display_value, or two
//            numbers read out of its receipt by `pattern`. No question uses it
//            since 2026-11-08 (#6 and #9 became pick questions); it stays.
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
//   - pick with listed choices: there are not exactly three, one is not a
//     number, one would not be shown exactly as listed (a percent at the
//     record's decimal places, a money or count choice at the "About" step,
//     a change in whole percent), the four do not read differently, the
//     right one does not appear exactly once, a wrong one is less than
//     MIN_GAP_LISTED (15%) away from the record, or one is outside the bounds;
//   - change: the receipt's two numbers cannot be read or are equal, or the
//     direct read of the index scale, (to - from) / from, does not round to
//     the row's display_value;
//   - most: a value is not a single percent, the data periods are not the same
//     period, or the highest value is tied;
//   - compare: the two values cannot be read, or they are equal;
// and if every question puts the right answer in the same position.
// checked_by is deliberately NOT required: it is empty on every row today (a
// finding for the founder, not something to fill in here).
//
// `version` is a short hash of the question set — each question's kind, row
// ids and right answer (the exact register figure) — so the anonymous score
// tally (functions/api/quiz/) never mixes two sets. A register refresh that
// changes an answer changes it. eleventy.config.js writes it, with `total`,
// into functions/_generated/build.json, which the score endpoints import.
//
// The end screen's "Correct answer" column shows the right choice as the
// reader saw it ("About $7", "Down about 15%"). `summary: "caption"` shows the
// row's whole caption there instead: SRC-018's notes say its two halves (the
// total fell; chronic homelessness reached a record high) travel together.
const crypto = require("node:crypto");
const register = require("./register.js");

const QUESTIONS = [
  { kind: "pick", id: "SRC-025", topic: "Prices overall",
    question: "Over the past year, how much did prices overall go up?",
    wrong: [1.2, 2.6, 5.5] },
  { kind: "most", topic: "What went up most",
    question: "Which of these went up most over the past year?",
    choices: [
      { id: "SRC-026", label: "Groceries" },
      { id: "SRC-019", label: "Rent" },
      { id: "SRC-003", label: "Water and sewer bills" },
      { id: "SRC-027", label: "Energy" },
    ] },
  { kind: "pick", id: "SRC-028", topic: "The Forbes 400",
    // "in 2025": the receipt quotes Forbes, "up from $6.6 trillion in 2025".
    question: "Forbes estimated the combined wealth of the 400 richest Americans at $6.6 trillion in 2025. What was its estimate for 2026?" },
  { kind: "pick", id: "SRC-024", part: 0, share: true, topic: "The wealthiest households",
    question: "In the second quarter of 2026, what share of the country's net worth did the wealthiest 1% of American households hold?" },
  { kind: "pick", id: "SRC-004", share: true, topic: "Renters and housing costs",
    question: "In 2024, the latest year measured, what share of renter households spent more than 30 percent of their income on rent and utilities?" },
  { kind: "pick", id: "SRC-022", part: 0, topic: "Rent and renters' income",
    // display_value "A versus B": rent (part 0), then income (the 9%).
    question: "Between 2001 and 2024, after adjusting for inflation, the median renter's income grew 9%. How much did the median rent grow?",
    wrong: [18, 22, 41] },
  { kind: "pick", id: "SRC-023", topic: "Ground beef",
    question: "What did a pound of ground beef cost in September 2026?",
    wrong: [5, 10, 15] },
  { kind: "pick", id: "SRC-006", topic: "Family health coverage",
    question: "On average, what did a year of family health coverage through an employer cost in 2025?" },
  { kind: "pick", id: "SRC-011", topic: "Household appliances",
    question: "Before adjusting for inflation, how much has the price of household appliances changed since 1997?",
    // The row's wording rule: a direct read of the index scale against its
    // December 1997 base (100), before inflation. The size is the row's
    // display_value; the direction is the latest level against the base.
    change: { pattern: /base December 1997=(\d+(?:\.\d+)?): (\d+(?:\.\d+)?) \(September 2026\)/, from: 1, to: 2 },
    wrong: [-25, 5, 20] },
  { kind: "pick", id: "SRC-018", topic: "Homelessness", summary: "caption",
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
const MIN_GAP_LISTED = 0.15;
const RANK_ORDER = [1, 3, 2];

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

// Money and counts: every choice, the record's too, rounded to one step (two
// significant figures of the largest) and read "About …".
function about(fig, raw) {
  const step = Math.pow(10, Math.floor(Math.log10(Math.max(...raw))) - 1);
  const decimals = step < 1 ? Math.round(-Math.log10(step)) : 0;
  const values = raw.map((v) => roundTo(Math.round(Number((v / step).toPrecision(12))) * step, decimals));
  return { values, texts: values.map((v) => "About " + formatLike({ ...fig, decimals }, v)) };
}

// The four choices on one rung of the ladder, or the reason the rung fails.
function rung(fig, recordText, rank, share) {
  const raw = [0, 1, 2, 3].map((i) => fig.value * Math.pow(LADDER, i - rank));
  let values, texts;
  if (fig.kind === "percent") {
    values = raw.map((v, i) => (i === rank ? fig.value : roundLike(fig, v)));
    texts = values.map((v, i) => (i === rank ? recordText : formatLike(fig, v)));
  } else {
    ({ values, texts } = about(fig, raw));
  }
  const wrong = values.filter((_, i) => i !== rank);
  const record = values[rank];
  if (!(record > 0) && fig.kind !== "percent") return { fail: "the record rounds to nothing" };
  if (share && values.some((v) => v <= 0 || v >= 100)) return { fail: "a share outside the whole" };
  if (fig.kind !== "percent" && wrong.some((v) => v <= 0)) return { fail: "a choice of nothing" };
  if (new Set(texts).size !== 4) return { fail: "two choices read the same" };
  if (wrong.some((v) => Math.abs(v - record) < MIN_GAP * Math.abs(record))) return { fail: "a wrong choice too close to the record" };
  if (texts.every((t, i) => i === rank || endsInZero(t) !== endsInZero(texts[rank]))) return { fail: "the record would stand out by its last digit" };
  return { texts };
}

// The record's text (the row's display_value, or one side of it) and its
// parsed figure, or null when either fails.
function figureOf(q, row, problems) {
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
  return { fig, recordText };
}

// "Down about 15%", "Up about 20%": a change in the record's percent style.
const changeText = (fig, v) => (v < 0 ? "Down" : "Up") + " about " + formatLike(fig, Math.abs(v));

// A change question's record, signed: the size is the row's display_value;
// the direction is the receipt's latest level (`to`) against its base
// (`from`). The direct read of the scale must round to the display_value.
function changeRecord(q, row, fig, problems) {
  const m = q.change.pattern.exec(String(row.receipt || ""));
  const from = m ? Number(m[q.change.from]) : NaN;
  const to = m ? Number(m[q.change.to]) : NaN;
  if (!(from > 0) || !Number.isFinite(to) || from === to) {
    problems.push(`${q.id}: the change's two numbers cannot be read from the receipt, or they are equal`);
    return null;
  }
  if (fig.kind !== "percent" || !(fig.value > 0)) {
    problems.push(`${q.id}: a change question needs a display_value that is a percent above nothing`);
    return null;
  }
  const read = ((to - from) / from) * 100;
  if (roundTo(Math.abs(read), fig.decimals) !== fig.value) {
    problems.push(`${q.id}: the receipt reads a change of ${read.toFixed(3)}%, which does not round to the display_value`);
    return null;
  }
  return to < from ? -fig.value : fig.value;
}

// A pick question with its wrong choices listed (`wrong`). The right choice is
// still the row's: its figure, rounded alike for money and counts, or its
// change. Shown low to high; every wrong choice exactly as listed.
function listed(q, row, problems) {
  const got = figureOf(q, row, problems);
  if (!got) return null;
  const { fig, recordText } = got;
  const wrong = q.wrong;
  if (!Array.isArray(wrong) || wrong.length !== 3 || !wrong.every((v) => typeof v === "number" && Number.isFinite(v))) {
    problems.push(`${q.id}: its listed wrong choices must be exactly three numbers`);
    return null;
  }
  const record = q.change ? changeRecord(q, row, fig, problems) : fig.value;
  if (record === null) return null;
  const before = problems.length;
  const items = [{ v: record, right: true }, ...wrong.map((v) => ({ v, right: false }))].sort((x, y) => x.v - y.v);
  let texts;
  let shown;
  if (q.change) {
    texts = items.map((it) => changeText(fig, it.v));
    shown = items.map((it) => (it.right ? it.v : roundTo(it.v, fig.decimals)));
    if (wrong.some((v) => v === 0)) problems.push(`${q.id}: a listed change of nothing`);
  } else if (fig.kind === "percent") {
    texts = items.map((it) => (it.right ? recordText : formatLike(fig, it.v)));
    shown = items.map((it) => (it.right ? it.v : roundTo(it.v, fig.decimals)));
  } else {
    const a = about(fig, items.map((it) => it.v));
    texts = a.texts;
    shown = items.map((it, i) => (it.right ? it.v : a.values[i]));
    if (items.some((it) => !(it.v > 0))) problems.push(`${q.id}: a listed money or count choice of nothing`);
  }
  const answer = items.findIndex((it) => it.right);
  items.forEach((it, i) => {
    if (it.right) return;
    if (shown[i] !== it.v) problems.push(`${q.id}: the listed choice ${it.v} would be shown as ${texts[i]}`);
    if (Math.abs(it.v - record) < MIN_GAP_LISTED * Math.abs(record)) problems.push(`${q.id}: the listed choice ${texts[i]} is less than ${MIN_GAP_LISTED * 100}% from the record`);
  });
  if (new Set(texts).size !== 4) problems.push(`${q.id}: two of its choices read the same (${texts.join(" / ")})`);
  if (texts.filter((t) => t === texts[answer]).length !== 1) problems.push(`${q.id}: the right choice does not appear exactly once`);
  if (q.share && items.some((it) => it.v <= 0 || it.v >= 100)) problems.push(`${q.id}: a share outside the whole`);
  if (problems.length > before) return null;
  return { choices: texts, answer, record: q.change ? changeText(fig, record) : recordText };
}

function pick(q, row, k, problems) {
  const got = figureOf(q, row, problems);
  if (!got) return null;
  const { fig, recordText } = got;
  const first = RANK_ORDER[k % RANK_ORDER.length];
  const reasons = [];
  for (let step = 0; step < 4; step++) {
    const rank = (first + step) % 4;
    const r = rung(fig, recordText, rank, q.share);
    if (r.texts) return { choices: r.texts, answer: rank, record: recordText };
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
  const answer = values.indexOf(top);
  return { choices: q.choices.map((c) => c.label), answer, record: q.choices[answer].label };
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
  return { choices: q.choices.slice(), answer: a > b ? 0 : 1, record: q.choices[a > b ? 0 : 1] };
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
  // Ladder questions only: a pick question with listed choices takes no rung.
  let ladders = 0;
  const questions = QUESTIONS.map((q, i) => {
    const ids = q.kind === "most" ? q.choices.map((c) => c.id) : [q.id];
    const rows = ids.map((id) => reg.byId[id]);
    const missing = ids.flatMap((id, j) => rowProblems(id, rows[j]));
    problems.push(...missing);
    if (missing.length) return null;
    problems.push(...statedProblems(q, rows));
    let made;
    if (q.kind === "pick" && (q.wrong !== undefined || q.change)) made = listed(q, rows[0], problems);
    else if (q.kind === "pick") made = pick(q, rows[0], ladders++, problems);
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
      // The right answer as the register gives it: the exact figure for a
      // pick question (its choice may read "About …"), "Down about 15%" for a
      // change, the row's label for "most", the answer for "compare". The
      // reveal, the no-JS answer and the announcement use it.
      recordText: made.record,
      // The end screen's "Correct answer" column: the right choice as the
      // reader saw it, or the whole caption.
      summaryText: q.summary === "caption" ? row.display_caption : made.choices[made.answer],
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
  const set = questions.map((q) => ({ kind: q.kind, ids: q.kind === "most" ? [q.row.source_id, ...q.others.map((r) => r.source_id)].sort() : [q.sourceId], answer: q.recordText }));
  const version = crypto.createHash("sha256").update(JSON.stringify(set)).digest("hex").slice(0, 12);
  return { questions, total: questions.length, version };
}

module.exports = function () {
  return build(register());
};
Object.assign(module.exports, { QUESTIONS, REQUIRED, PERCENT, LADDER, MIN_GAP, MIN_GAP_LISTED, RANK_ORDER, parseFigure, roundLike, formatLike, build });

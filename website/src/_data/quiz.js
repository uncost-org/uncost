// The cost-of-living quiz at /quiz/ (records/changes/CHG-019).
//
// The quiz's row list lives here and nowhere else: five register rows, in the
// order the quiz asks them, each with its question. The questions are fixed
// text; the ANSWERS are not. Every answer — the figure, its caption, period,
// region, source line and link — is read from sources/register.csv through
// _data/register.js, so the Friday review and the monthly refresh change the
// quiz simply by updating the register. Never type a figure here, in
// quiz.njk, in js/quiz.js or in the copy.
//
// Build guard (no fake numbers): the build fails if any quiz row is missing
// from the register, has an empty display_value, display_caption,
// data_period, source_line or url, or has a display_value that does not parse
// as a percent. checked_by is deliberately NOT required: it is empty on all
// five rows today (a finding for the founder, not something to fill in here).
const register = require("./register.js");

const QUESTIONS = [
  { id: "SRC-025", sector: "All items", question: "Over the past year, how much did prices overall go up?" },
  { id: "SRC-019", sector: "Shelter", question: "Over the past year, how much did rents go up?" },
  { id: "SRC-026", sector: "Food", question: "Over the past year, how much did groceries go up?" },
  { id: "SRC-027", sector: "Energy", question: "Over the past year, how much did energy go up?" },
  { id: "SRC-003", sector: "Water", question: "Over the past year, how much did water and sewer bills go up?" },
];

const REQUIRED = ["display_value", "display_caption", "data_period", "source_line", "url"];
// "3.7%", "-0.4%", "+2%", "20.4 %": a signed decimal followed by a percent sign.
const PERCENT = /^([+\-−]?\d+(?:\.\d+)?)\s*%$/;

function build(reg) {
  const problems = [];
  const questions = QUESTIONS.map((q, i) => {
    const row = reg.byId[q.id];
    if (!row) {
      problems.push(`${q.id}: not in sources/register.csv`);
      return null;
    }
    for (const field of REQUIRED) {
      if (!String(row[field] || "").trim()) problems.push(`${q.id}: ${field} is empty`);
    }
    const m = PERCENT.exec(String(row.display_value || "").trim());
    if (!m) {
      problems.push(`${q.id}: display_value "${row.display_value}" does not parse as a percent`);
      return null;
    }
    return {
      n: i + 1,
      id: q.id,
      sector: q.sector,
      question: q.question,
      row,
      // The record as a number, for comparing a guess. Derived from the
      // register's own display_value, never typed.
      value: Number(m[1].replace("−", "-")),
    };
  });
  if (problems.length) {
    throw new Error("Quiz guard failed (no fake numbers) — fix sources/register.csv:\n  - " + problems.join("\n  - "));
  }
  return { questions, total: questions.length };
}

module.exports = function () {
  return build(register());
};
Object.assign(module.exports, { QUESTIONS, REQUIRED, PERCENT, build });

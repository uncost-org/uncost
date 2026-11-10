// Unit tests for the quiz's anonymous score tally (CHG-019): lib/quiz.js and
// the two routes in functions/api/quiz/. Run after a build (the routes import
// functions/_generated/build.json): `npm run build && npm test`.
//
// D1 is stood in for by node:sqlite running the real migration
// (migrations/quiz/0001_scores.sql), with D1's prepare/bind/run/first/batch.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { DatabaseSync } from "node:sqlite";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import path from "node:path";
import * as quiz from "../lib/quiz.js";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const WEB = path.join(HERE, "..");
const MIGRATION = readFileSync(path.join(WEB, "migrations", "quiz", "0001_scores.sql"), "utf8");
const CURRENT = { version: "0123456789ab", total: 10 };
const ORIGIN = "https://uncost.org";

class Statement {
  constructor(db, sql) { this.db = db; this.sql = sql; this.args = []; }
  bind(...args) { this.args = args; return this; }
  async run() { const r = this.db.prepare(this.sql).run(...this.args); return { success: true, meta: { changes: Number(r.changes) } }; }
  async first() { return this.db.prepare(this.sql).get(...this.args) ?? null; }
  async all() { return { results: this.db.prepare(this.sql).all(...this.args) }; }
}
function d1() {
  const db = new DatabaseSync(":memory:");
  db.exec(MIGRATION);
  return {
    raw: db,
    prepare: (sql) => new Statement(db, sql),
    batch: async (stmts) => { const out = []; for (const s of stmts) out.push(await s.run()); return out; },
  };
}
const ON = (db) => ({ UNCOST_QUIZ_STATS_OPEN: "on", QUIZ_DB: db });

function post(body, { headers = {}, raw } = {}) {
  return new Request(`${ORIGIN}/api/quiz/score`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Origin: ORIGIN, "Sec-Fetch-Site": "same-origin", ...headers },
    body: raw !== undefined ? raw : JSON.stringify(body),
  });
}
const get = (version) => new Request(`${ORIGIN}/api/quiz/stats?version=${encodeURIComponent(version)}`);
const score = (env, req, now) => quiz.handleScore({ request: req, env }, CURRENT, now);
const stats = (env, req, waitUntil) => quiz.handleStats({ request: req, env, waitUntil }, CURRENT);
const rows = (db) => db.raw.prepare("SELECT version, correct, total, answers, day FROM score ORDER BY rowid").all().map((r) => ({ ...r }));

test("switch off: both routes answer 404 and store nothing", async () => {
  const db = d1();
  for (const env of [{}, { QUIZ_DB: db }, { UNCOST_QUIZ_STATS_OPEN: "on" }, { UNCOST_QUIZ_STATS_OPEN: "ON", QUIZ_DB: db }, { UNCOST_QUIZ_STATS_OPEN: "1", QUIZ_DB: db }]) {
    assert.equal((await score(env, post({ version: CURRENT.version, answers: "1111100000" }))).status, 404);
    assert.equal((await stats(env, get(CURRENT.version))).status, 404);
  }
  assert.deepEqual(rows(db), []);
});

test("a valid score is stored as five columns, correct and total recounted, the UTC date only", async () => {
  const db = d1();
  const res = await score(ON(db), post({ version: CURRENT.version, answers: "1101000111" }), new Date("2026-11-08T23:59:59+07:00"));
  assert.equal(res.status, 204);
  assert.equal(res.headers.get("Set-Cookie"), null);
  assert.deepEqual(rows(db), [{ version: CURRENT.version, correct: 6, total: 10, answers: "1101000111", day: "2026-11-08" }]);
  const columns = db.raw.prepare("PRAGMA table_info(score)").all().map((c) => c.name);
  assert.deepEqual(columns, ["version", "correct", "total", "answers", "day"]);
});

test("malformed, unknown-version, wrong-length and cross-site scores are refused and nothing is stored", async () => {
  const db = d1();
  const v = CURRENT.version;
  const cases = [
    [post({ version: "fedcba987654", answers: "1111100000" }), 400, "an unknown version"],
    [post({ version: "0123456789AB", answers: "1111100000" }), 400, "a version in capitals"],
    [post({ version: v, answers: "111110000" }), 400, "nine answers"],
    [post({ version: v, answers: "11111000001" }), 400, "eleven answers"],
    [post({ version: v, answers: "11111000x0" }), 400, "a character other than 0 or 1"],
    [post({ version: v, answers: 1111100000 }), 400, "answers as a number"],
    [post({ version: v, answers: "1111100000", correct: 10 }), 400, "an extra field (the client may not claim a score)"],
    [post({ version: v, answers: "1111100000", total: 10 }), 400, "an extra total"],
    [post({ version: v, answers: "1111100000", zone: "x" }), 400, "an extra field sorting after version"],
    [post({ answers: "1111100000" }), 400, "no version"],
    [post([v, "1111100000"]), 400, "an array"],
    [post(null, { raw: "not json" }), 400, "not JSON"],
    [post(null, { raw: "x".repeat(2000) }), 400, "an over-long body"],
    [post({ version: v, answers: "1111100000" }, { headers: { "Content-Type": "text/plain" } }), 400, "not application/json"],
    [post({ version: v, answers: "1111100000" }, { headers: { Origin: "https://example.com" } }), 403, "another site's Origin"],
    [post({ version: v, answers: "1111100000" }, { headers: { "Sec-Fetch-Site": "cross-site" } }), 403, "Sec-Fetch-Site cross-site"],
  ];
  for (const [req, status, label] of cases) assert.equal((await score(ON(db), req)).status, status, label);
  assert.deepEqual(rows(db), []);
});

test("parseScore recounts from the bits and ignores nothing else", () => {
  assert.deepEqual(quiz.parseScore({ version: CURRENT.version, answers: "0000000000" }, CURRENT), { version: CURRENT.version, answers: "0000000000", correct: 0, total: 10 });
  assert.deepEqual(quiz.parseScore({ answers: "1111111111", version: CURRENT.version }, CURRENT).correct, 10);
  assert.equal(quiz.parseScore("1111111111", CURRENT), null);
});

test("stats: the count always; the mean and per-question shares only from 30 scores", async () => {
  const db = d1();
  // 29 scores: 10 right-on-everything, 19 with only question 1 right.
  for (let i = 0; i < 10; i++) await score(ON(db), post({ version: CURRENT.version, answers: "1111111111" }));
  for (let i = 0; i < 19; i++) await score(ON(db), post({ version: CURRENT.version, answers: "1000000000" }));
  let res = await stats(ON(db), get(CURRENT.version));
  assert.equal(res.status, 200);
  assert.deepEqual(await res.json(), { count: 29, mean: null, perQuestion: null });
  // The 30th: questions 1 and 2 right.
  await score(ON(db), post({ version: CURRENT.version, answers: "1100000000" }));
  res = await stats(ON(db), get(CURRENT.version));
  const s = await res.json();
  assert.equal(s.count, 30);
  // (10×10 + 19×1 + 1×2) / 30 = 121 / 30 = 4.0333…
  assert.equal(s.mean, 4.03);
  // Q1: 30/30; Q2: 11/30 = 0.3666…; Q3–Q10: 10/30.
  assert.deepEqual(s.perQuestion, [1, 0.37, 0.33, 0.33, 0.33, 0.33, 0.33, 0.33, 0.33, 0.33]);
  assert.equal(res.headers.get("Cache-Control"), "public, max-age=60");
});

test("stats count only the asked version and only rows of the current length", async () => {
  const db = d1();
  db.raw.prepare("INSERT INTO question_set (version) VALUES (?)").run(CURRENT.version);
  for (let i = 0; i < 30; i++) db.raw.prepare("INSERT INTO score VALUES (?, ?, ?, ?, ?)").run(CURRENT.version, 5, 10, "1111100000", "2026-11-08");
  for (let i = 0; i < 40; i++) db.raw.prepare("INSERT INTO score VALUES (?, ?, ?, ?, ?)").run("aaaaaaaaaaaa", 0, 10, "0000000000", "2026-11-08");
  db.raw.prepare("INSERT INTO score VALUES (?, ?, ?, ?, ?)").run(CURRENT.version, 1, 5, "10000", "2026-11-08");
  const s = await (await stats(ON(db), get(CURRENT.version))).json();
  assert.equal(s.count, 30);
  assert.equal(s.mean, 5);
  assert.deepEqual(s.perQuestion, [1, 1, 1, 1, 1, 0, 0, 0, 0, 0]);
});

test("stats: a malformed version is 400, any version but the current one is 404", async () => {
  const db = d1();
  assert.equal((await stats(ON(db), get("nope"))).status, 400);
  assert.equal((await stats(ON(db), get("fedcba987654"))).status, 404);
});

test("stats are cached at the edge for 60 seconds, keyed by version only", async () => {
  const db = d1();
  const store = new Map();
  globalThis.caches = { default: { match: async (k) => store.get(k.url)?.clone(), put: async (k, r) => { store.set(k.url, r); } } };
  try {
    const waits = [];
    const first = await stats(ON(db), get(CURRENT.version), (p) => waits.push(p));
    await Promise.all(waits);
    assert.equal(first.status, 200);
    assert.deepEqual([...store.keys()], [`${ORIGIN}/api/quiz/stats?version=${CURRENT.version}`]);
    db.raw.exec("DROP TABLE score");   // a second read that reached D1 would now be 503
    const second = await stats(ON(db), new Request(`${ORIGIN}/api/quiz/stats?version=${CURRENT.version}&x=1`));
    assert.deepEqual(await second.json(), { count: 0, mean: null, perQuestion: null });
  } finally {
    delete globalThis.caches;
  }
});

test("retention: a new question set keeps its own rows and the previous set's, and deletes older ones", async () => {
  const db = d1();
  const sets = ["aaaaaaaaaaa1", "aaaaaaaaaaa2", "aaaaaaaaaaa3"];
  for (const v of sets) {
    const cur = { version: v, total: 10 };
    for (let i = 0; i < 3; i++) await quiz.handleScore({ request: post({ version: v, answers: "1111100000" }), env: ON(db) }, cur);
  }
  const kept = db.raw.prepare("SELECT version, COUNT(*) AS n FROM score GROUP BY version ORDER BY version").all().map((r) => ({ ...r }));
  assert.deepEqual(kept, [{ version: "aaaaaaaaaaa2", n: 3 }, { version: "aaaaaaaaaaa3", n: 3 }]);
  assert.deepEqual(db.raw.prepare("SELECT version FROM question_set ORDER BY seq").all().map((r) => r.version), ["aaaaaaaaaaa2", "aaaaaaaaaaa3"]);
});

test("a database error is 503, never a stack trace", async () => {
  const broken = { prepare: () => ({ bind: () => ({ run: async () => { throw new Error("boom"); }, first: async () => { throw new Error("boom"); } }) }), batch: async () => [] };
  const res = await score(ON(broken), post({ version: CURRENT.version, answers: "1111100000" }));
  assert.equal(res.status, 503);
  assert.deepEqual(await res.json(), { ok: false });
  assert.equal((await stats(ON(broken), get(CURRENT.version))).status, 503);
});

test("the schema refuses a row outside the rules", () => {
  const db = d1();
  const bad = [
    ["0123456789ab", 11, 10, "1111111111", "2026-11-08"],
    ["0123456789ab", 5, 10, "11111", "2026-11-08"],
    ["0123456789ab", 5, 10, "11111x0000", "2026-11-08"],
    ["short", 5, 10, "1111100000", "2026-11-08"],
    ["0123456789ab", 5, 10, "1111100000", "2026-11-08T12:00"],
  ];
  for (const r of bad) assert.throws(() => db.raw.prepare("INSERT INTO score VALUES (?, ?, ?, ?, ?)").run(...r));
});

test("the routes use this build's question set (functions/_generated/build.json)", async () => {
  const build = JSON.parse(readFileSync(path.join(WEB, "functions", "_generated", "build.json"), "utf8"));
  const require = createRequire(import.meta.url);
  const data = require(path.join(WEB, "src", "_data", "quiz.js"))();
  assert.deepEqual(build.quiz, { version: data.version, total: data.total });
  const { onRequestPost } = await import("../functions/api/quiz/score.js");
  const { onRequestGet } = await import("../functions/api/quiz/stats.js");
  const db = d1();
  assert.equal((await onRequestPost({ request: post({ version: data.version, answers: "1".repeat(data.total) }), env: ON(db) })).status, 204);
  assert.equal((await onRequestPost({ request: post({ version: data.version, answers: "1".repeat(data.total) }), env: {} })).status, 404);
  assert.equal((await onRequestGet({ request: get(data.version), env: ON(db) })).status, 200);
  const signups = require(path.join(WEB, "src", "_data", "signups.json"));
  const features = require(path.join(WEB, "src", "_data", "features.js"));
  assert.equal(build.policyVersion, features.quizStatsOpen ? signups.policyVersionQuizStats : signups.policyVersion);
});

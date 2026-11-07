// The quiz's anonymous score tally (records/changes/CHG-019), shared by
// functions/api/quiz/score.js and stats.js. It sits outside functions/ so it is
// not a route, and takes the current question set as an argument so the unit
// tests (test/quiz-stats.test.mjs) can run it without a build.
//
// Dark unless the Pages environment sets UNCOST_QUIZ_STATS_OPEN to "on" AND
// carries the QUIZ_DB binding (D1 uncost-quiz; migrations/quiz/): every route
// then answers 404, exactly as if there were no handler.
//
// What is stored, per completed quiz: the question set's version, the number
// right, the number of questions, right or wrong per question, and the UTC
// date. Nothing about the request is read or kept: no IP address, user agent,
// cookie or header value, and nothing is logged. The rate limit is
// Cloudflare's (a dashboard rule), not ours.

export const MIN_COUNT = 30;   // the average is shown from this many scores
export const MAX_BODY = 1024;
const VERSION = /^[0-9a-f]{12}$/;
const BITS = /^[01]+$/;
const NO_STORE = { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" };

export const isOpen = (env) => !!env && env.UNCOST_QUIZ_STATS_OPEN === "on" && !!env.QUIZ_DB;

export function notFound() {
  return new Response("Not found", { status: 404, headers: NO_STORE });
}

function json(status, body, headers = NO_STORE) {
  return new Response(JSON.stringify(body), { status, headers: { ...headers, "Content-Type": "application/json" } });
}

// A browser POST from another site is refused.
export function sameOrigin(request) {
  const origin = request.headers.get("Origin");
  const site = request.headers.get("Sec-Fetch-Site");
  if (site && site !== "same-origin") return false;
  if (origin && origin !== new URL(request.url).origin) return false;
  return true;
}

// The score a client sends, checked against the current question set:
// exactly {version, answers}, the current version, and one 0 or 1 per
// question. The server counts `correct` and `total` itself. Anything else is
// null.
export function parseScore(body, current) {
  if (!body || typeof body !== "object" || Array.isArray(body)) return null;
  const keys = Object.keys(body).sort();
  if (keys.length !== 2 || keys[0] !== "answers" || keys[1] !== "version") return null;
  const { version, answers } = body;
  if (typeof version !== "string" || !VERSION.test(version) || version !== current.version) return null;
  if (typeof answers !== "string" || !BITS.test(answers) || answers.length !== current.total) return null;
  let correct = 0;
  for (const c of answers) if (c === "1") correct += 1;
  return { version, answers, correct, total: answers.length };
}

export const today = (now = new Date()) => now.toISOString().slice(0, 10);

// Retention: keep the current question set and the one before it. Run when a
// score arrives for a set not seen before.
export async function recordSet(db, version) {
  const added = await db.prepare("INSERT OR IGNORE INTO question_set (version) VALUES (?)").bind(version).run();
  if (!added.meta || !added.meta.changes) return false;
  await db.batch([
    db.prepare("DELETE FROM score WHERE version NOT IN (SELECT version FROM question_set ORDER BY seq DESC LIMIT 2)"),
    db.prepare("DELETE FROM question_set WHERE seq NOT IN (SELECT seq FROM question_set ORDER BY seq DESC LIMIT 2)"),
  ]);
  return true;
}

export async function handleScore(context, current, now = new Date()) {
  const { request, env } = context;
  if (!isOpen(env)) return notFound();
  if (!sameOrigin(request)) return json(403, { ok: false });
  if (!(request.headers.get("Content-Type") || "").toLowerCase().startsWith("application/json")) return json(400, { ok: false });
  if (Number(request.headers.get("Content-Length") || 0) > MAX_BODY) return json(400, { ok: false });
  let body;
  try {
    const text = await request.text();
    if (text.length > MAX_BODY) return json(400, { ok: false });
    body = JSON.parse(text);
  } catch {
    return json(400, { ok: false });
  }
  const score = parseScore(body, current);
  if (!score) return json(400, { ok: false });
  try {
    await recordSet(env.QUIZ_DB, score.version);
    await env.QUIZ_DB.prepare("INSERT INTO score (version, correct, total, answers, day) VALUES (?, ?, ?, ?, ?)")
      .bind(score.version, score.correct, score.total, score.answers, today(now)).run();
  } catch {
    return json(503, { ok: false });
  }
  return new Response(null, { status: 204, headers: NO_STORE });
}

// One query: the count, the mean score, and per question the number right.
export function statsSql(total) {
  const per = Array.from({ length: total }, (_, i) => `SUM(substr(answers, ${i + 1}, 1) = '1') AS q${i + 1}`);
  return `SELECT COUNT(*) AS n, AVG(correct) AS mean, ${per.join(", ")} FROM score WHERE version = ? AND total = ?`;
}

// The answer for a set: the count always; the mean (to two decimals) and the
// share right per question (to two decimals) only from MIN_COUNT scores, so a
// handful of rows is never shown.
export function statsFrom(row, total) {
  const count = Number((row && row.n) || 0);
  if (count < MIN_COUNT) return { count, mean: null, perQuestion: null };
  const r2 = (x) => Math.round(x * 100) / 100;
  return {
    count,
    mean: r2(Number(row.mean)),
    perQuestion: Array.from({ length: total }, (_, i) => r2(Number(row[`q${i + 1}`] || 0) / count)),
  };
}

export async function handleStats(context, current) {
  const { request, env } = context;
  if (!isOpen(env)) return notFound();
  const version = new URL(request.url).searchParams.get("version") || "";
  if (!VERSION.test(version)) return json(400, { ok: false });
  if (version !== current.version) return notFound();
  const cache = typeof caches !== "undefined" ? caches.default : null;
  const key = new Request(new URL(`/api/quiz/stats?version=${version}`, request.url).toString(), { method: "GET" });
  if (cache) {
    const hit = await cache.match(key);
    if (hit) return hit;
  }
  let row;
  try {
    row = await env.QUIZ_DB.prepare(statsSql(current.total)).bind(version, current.total).first();
  } catch {
    return json(503, { ok: false });
  }
  const answer = json(200, statsFrom(row, current.total), { "Cache-Control": "public, max-age=60", "X-Content-Type-Options": "nosniff" });
  if (cache) {
    const put = cache.put(key, answer.clone());
    if (context.waitUntil) context.waitUntil(put); else await put;
  }
  return answer;
}

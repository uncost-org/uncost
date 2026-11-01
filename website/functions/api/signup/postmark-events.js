// POST /api/signup/postmark-events — Postmark's webhook: bounces, spam complaints
// and subscription changes (records/changes/CHG-012). The body and the
// Authorization header go to the Worker untouched; the Worker checks the Basic
// credentials before trusting any of it, and suppresses hard bounces and
// complaints. Answers 200, 400 or 401 with no body. Dark unless switched on.
import { forward, isOpen, notFound } from "../../../lib/signup.js";

const MAX = 256 * 1024;

export async function onRequestPost({ request, env }) {
  if (!isOpen(env)) return notFound();
  if (Number(request.headers.get("Content-Length") || 0) > MAX) return new Response(null, { status: 413 });
  const body = await request.text();
  if (body.length > MAX) return new Response(null, { status: 413 });
  const r = await forward(env, "/v1/postmark-events", body, { authorization: request.headers.get("Authorization") });
  return new Response(null, { status: [200, 400, 401].includes(r.status) ? r.status : 502, headers: { "Cache-Control": "no-store" } });
}

// POST /api/signup/ses-events — Amazon SNS delivering SES bounce and complaint
// notifications (records/changes/CHG-009). The body goes to the Worker
// untouched; the Worker verifies the SNS signature and topic before trusting
// any of it, confirms the subscription handshake, and suppresses hard bounces
// and complaints. Answers 200, 400 or 401 with no body. Dark unless switched on.
import { forward, isOpen, notFound } from "../../../lib/signup.js";

const MAX = 256 * 1024;

export async function onRequestPost({ request, env }) {
  if (!isOpen(env)) return notFound();
  if (Number(request.headers.get("Content-Length") || 0) > MAX) return new Response(null, { status: 413 });
  const body = await request.text();
  if (body.length > MAX) return new Response(null, { status: 413 });
  const r = await forward(env, "/v1/ses-events", body);
  return new Response(null, { status: [200, 400, 401].includes(r.status) ? r.status : 502, headers: { "Cache-Control": "no-store" } });
}

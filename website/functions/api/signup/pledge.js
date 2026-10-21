// POST /api/signup/pledge — the Pledge form (records/changes/CHG-009). Dark
// (404) unless UNCOST_SIGNUPS_OPEN is "on" and the SIGNUPS binding exists; see
// website/lib/signup.js. With "Accept: application/json" (ui.js's fetch) the
// answer is JSON {"ok": true|false}; a no-JS post is sent on with a 303 to
// /pledge/check-email/ or /signup/not-sent/. The answer is the same for a new,
// repeated, pending or suppressed address.
import { consentFor, formFields, forward, isOpen, jsonAnswer, notFound, redirect, sameOrigin, wantsJson } from "../../../lib/signup.js";

export async function onRequestPost({ request, env }) {
  if (!isOpen(env)) return notFound();
  const json = wantsJson(request);
  if (!sameOrigin(request)) return json ? jsonAnswer(403, { ok: false }) : redirect(request, "/signup/not-sent/");
  const fields = await formFields(request, ["email", "name", "agree", "updates", "age", "hp_url"]);
  if (!fields) return json ? jsonAnswer(400, { ok: false }) : redirect(request, "/signup/not-sent/");
  const r = await forward(env, "/v1/pledge", { fields, consent: await consentFor("pledge", fields), origin: new URL(request.url).origin });
  if (r.status === 503) return notFound();          // closed at the Worker: no postal address or mail set up
  const ok = r.status === 202;
  if (json) return jsonAnswer(ok ? 202 : 400, { ok });
  return redirect(request, ok ? "/pledge/check-email/" : "/signup/not-sent/");
}

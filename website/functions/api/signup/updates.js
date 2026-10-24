// POST /api/signup/updates — the email updates form, wherever it appears
// (footer, home, join; records/changes/CHG-009). Dark unless switched on; see
// website/lib/signup.js. JSON for ui.js's fetch; a no-JS post lands on
// /updates/check-email/ or /signup/not-sent/. Same answer for every address;
// a forward that fails is answered as not sent (lib/signup.js, answerIntake).
import { answerIntake, consentFor, formFields, forward, isOpen, jsonAnswer, notFound, redirect, sameOrigin, wantsJson } from "../../../lib/signup.js";

export async function onRequestPost({ request, env }) {
  if (!isOpen(env)) return notFound();
  const json = wantsJson(request);
  if (!sameOrigin(request)) return json ? jsonAnswer(403, { ok: false }) : redirect(request, "/signup/not-sent/");
  const fields = await formFields(request, ["email", "consent", "age", "surface", "hp_url"]);
  if (!fields) return json ? jsonAnswer(400, { ok: false }) : redirect(request, "/signup/not-sent/");
  return answerIntake(request, json, async () =>
    forward(env, "/v1/updates", { fields, consent: await consentFor("updates", fields), origin: new URL(request.url).origin }), "/updates/check-email/");
}

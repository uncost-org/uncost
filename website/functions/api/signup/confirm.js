// GET /api/signup/confirm?t=… — the link in a confirmation email
// (records/changes/CHG-009). It confirms, then sends the browser to a plain page:
//   pledge confirmed (or the link already used) → /pledge/verify/
//   updates confirmed (or already used)          → /updates/confirmed/
//   pledge link expired                          → /pledge/resent/ (send a new one)
//   anything else                                → /signup/link-expired/
// A reused link is a harmless no-op. Dark unless switched on.
import { forward, isOpen, notFound, redirect, tokenFrom } from "../../../lib/signup.js";

export async function onRequestGet({ request, env }) {
  if (!isOpen(env)) return notFound();
  let res = { result: "invalid" };
  try {
    const r = await forward(env, "/v1/confirm", { token: tokenFrom(request) });
    if (r.ok) res = await r.json();
  } catch { /* answered below as an expired link */ }
  if (res.result === "confirmed" || res.result === "already") {
    return redirect(request, res.kind === "pledge" ? "/pledge/verify/" : "/updates/confirmed/");
  }
  if (res.result === "expired" && res.kind === "pledge") return redirect(request, "/pledge/resent/");
  return redirect(request, "/signup/link-expired/");
}

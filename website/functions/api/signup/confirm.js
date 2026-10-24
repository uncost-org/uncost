// /api/signup/confirm?t=… — the link in a confirmation email (records/changes/CHG-009)
//   GET   a no-JS page with a Confirm button. Opening the link confirms
//         nothing, so a mail scanner that follows it changes nothing.
//   POST  that page's form (same origin only): confirms, then sends the
//         browser to a plain page:
//     pledge confirmed (or the link already used) → /pledge/verify/
//     updates confirmed (or already used)          → /updates/confirmed/
//     pledge link expired                          → /pledge/resent/ (send a new one)
//     anything else                                → /signup/link-expired/
// A reused link is a harmless no-op. Dark unless switched on.
import { confirmPage, formFields, forward, isOpen, notFound, redirect, sameOrigin, tokenFrom } from "../../../lib/signup.js";

export async function onRequestGet({ request, env }) {
  if (!isOpen(env)) return notFound();
  return confirmPage({
    title: "Confirm your email", eyebrow: "Almost there", heading: "Confirm your email?",
    paragraphs: [
      "Press Confirm to finish. If you signed the Pledge, your signature then counts; if you asked for email updates, they start.",
      "If you didn’t sign up, close this page: nothing happens unless you press the button.",
    ],
    action: "/api/signup/confirm", token: tokenFrom(request), button: "Confirm",
  });
}

export async function onRequestPost({ request, env }) {
  if (!isOpen(env)) return notFound();
  if (!sameOrigin(request)) return redirect(request, "/signup/link-expired/");
  const fields = await formFields(request, ["t"]);
  if (!fields) return redirect(request, "/signup/link-expired/");
  let res = { result: "invalid" };
  try {
    const r = await forward(env, "/v1/confirm", { token: tokenFrom(request, fields) });
    if (r.ok) res = await r.json();
  } catch { /* answered below as an expired link */ }
  if (res.result === "confirmed" || res.result === "already") {
    return redirect(request, res.kind === "pledge" ? "/pledge/verify/" : "/updates/confirmed/");
  }
  if (res.result === "expired" && res.kind === "pledge") return redirect(request, "/pledge/resent/");
  return redirect(request, "/signup/link-expired/");
}

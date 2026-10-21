// /api/signup/unsubscribe?t=… (records/changes/CHG-009)
//   GET   the no-JS confirm page for the link in an email's footer
//   POST  "List-Unsubscribe=One-Click" (RFC 8058, from a mail provider): 200, empty
//   POST  the confirm page's form: 303 to /signup/unsubscribed/
// It takes effect at once and answers the same for any link. Dark unless
// switched on.
import { confirmPage, formFields, forward, isOpen, notFound, redirect, sameOrigin, tokenFrom } from "../../../lib/signup.js";

export async function onRequestGet({ request, env }) {
  if (!isOpen(env)) return notFound();
  return confirmPage({
    title: "Unsubscribe", eyebrow: "Email", heading: "Unsubscribe?",
    paragraphs: ["Stop all email from Uncost to this address. It takes effect at once, and we won’t email this address again."],
    action: "/api/signup/unsubscribe", token: tokenFrom(request), button: "Unsubscribe",
  });
}

export async function onRequestPost({ request, env }) {
  if (!isOpen(env)) return notFound();
  const fields = await formFields(request, ["t", "List-Unsubscribe"]);
  if (!fields) return new Response(null, { status: 400 });
  const oneClick = fields["List-Unsubscribe"] === "One-Click";
  if (!oneClick && !sameOrigin(request)) return redirect(request, "/signup/link-expired/");
  let res = { result: "done" };
  try {
    const r = await forward(env, "/v1/unsubscribe", { token: tokenFrom(request, fields) });
    if (r.ok) res = await r.json();
  } catch { /* fall through */ }
  if (oneClick) return new Response(null, { status: 200, headers: { "Cache-Control": "no-store" } });
  return redirect(request, res.result === "expired" ? "/signup/link-expired/" : "/signup/unsubscribed/");
}

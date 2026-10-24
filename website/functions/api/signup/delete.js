// /api/signup/delete?t=… — delete my data (records/changes/CHG-009)
//   GET   the no-JS confirm page for the link in an email's footer
//   POST  the confirm page's form: deletes, then 303 to /signup/deleted/
// It needs the signed, single-use link sent to the address, so nobody can
// delete someone else. Dark unless switched on.
import { confirmPage, formFields, forward, isOpen, notFound, redirect, sameOrigin, tokenFrom } from "../../../lib/signup.js";

export async function onRequestGet({ request, env }) {
  if (!isOpen(env)) return notFound();
  return confirmPage({
    title: "Delete my data", eyebrow: "Your data", heading: "Delete your data?",
    paragraphs: [
      "This deletes your email address, your name if you gave one, your pledge signature and your email updates.",
      "We keep only a scrambled record that this address asked not to be emailed, which cannot be turned back into the address, and a dated note that a deletion happened. It can’t be undone.",
    ],
    action: "/api/signup/delete", token: tokenFrom(request), button: "Delete my data",
  });
}

export async function onRequestPost({ request, env }) {
  if (!isOpen(env)) return notFound();
  if (!sameOrigin(request)) return redirect(request, "/signup/link-expired/");
  const fields = await formFields(request, ["t"]);
  if (!fields) return redirect(request, "/signup/link-expired/");
  let res = { result: "invalid" };
  try {
    const r = await forward(env, "/v1/delete", { token: tokenFrom(request, fields) });
    if (r.ok) res = await r.json();
  } catch { /* fall through */ }
  return redirect(request, res.result === "deleted" ? "/signup/deleted/" : "/signup/link-expired/");
}

// POST /api/contact — the /contact/ form's handler (records/changes/CHG-005).
//
// First party only. Cloudflare Pages Functions have no Email Routing
// send_email binding, so this Function validates the message and hands it,
// through a Service binding (CONTACT_MAILER), to the uncost-contact-mailer
// Worker (workers/contact-mailer/), which emails it to the founder inbox with
// Email Routing's send_email binding. No form vendor, no third-party script,
// no database: nothing is stored on our side, and the message is not logged.
//
// Dark unless switched on at runtime: the Pages project's environment must set
// UNCOST_CONTACT_FORM_OPEN to "on" AND carry the CONTACT_MAILER binding.
// Otherwise this answers 404, exactly as if there were no handler. (The same
// variable at BUILD time renders the form; features.contactFormOpen.)
//
// Replies: with "Accept: application/json" (ui.js's fetch) the answer is JSON
// {"ok": true|false}; without it (a no-JS form post) a 303 to /contact/sent/
// or /contact/not-sent/. A failed check is rejected quietly: no reason is
// given, and a filled honeypot gets the success answer without anything being
// sent.

export const LIMITS = { name: 200, email: 254, phone: 40, message: 5000 };
const MAX_BODY = 32 * 1024;
// One @, no spaces or angle brackets, a dot in the domain, and a TLD of two or
// more letters. Deliberately strict: the address becomes the Reply-To header.
const EMAIL_RE = /^[^\s@<>()[\]\\,;:"]{1,64}@(?=.{3,253}$)[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)*\.[A-Za-z]{2,63}$/;

// A single line: no CR/LF or other control characters (they could forge
// headers), runs of space collapsed.
const oneLine = (s) => s.replace(/[\u0000-\u001f\u007f]+/g, " ").replace(/\s+/g, " ").trim();
// The message keeps its line breaks but loses other control characters.
const body = (s) => s.replace(/\r\n?/g, "\n").replace(/[\u0000-\u0008\u000b-\u001f\u007f]/g, "").trim();

export function validate(fields) {
  const get = (k) => (typeof fields[k] === "string" ? fields[k] : "");
  if (get("hp_url").trim() !== "") return { spam: true };
  const msg = {
    name: oneLine(get("name")),
    email: oneLine(get("email")),
    phone: oneLine(get("phone")),
    message: body(get("message")),
  };
  if (!msg.email || !msg.message) return { ok: false };
  for (const [k, max] of Object.entries(LIMITS)) if (msg[k].length > max) return { ok: false };
  if (!EMAIL_RE.test(msg.email)) return { ok: false };
  if (msg.phone && !/^[0-9+().\-\s]{3,40}$/.test(msg.phone)) return { ok: false };
  return { ok: true, msg };
}

function sameOrigin(request) {
  const origin = request.headers.get("Origin");
  const site = request.headers.get("Sec-Fetch-Site");
  if (site && site !== "same-origin") return false;
  if (origin && origin !== new URL(request.url).origin) return false;
  return true;
}

function answer(request, ok) {
  const headers = { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" };
  if ((request.headers.get("Accept") || "").includes("application/json")) {
    return new Response(JSON.stringify({ ok }), { status: 200, headers: { ...headers, "Content-Type": "application/json" } });
  }
  const to = new URL(ok ? "/contact/sent/" : "/contact/not-sent/", request.url);
  return new Response(null, { status: 303, headers: { ...headers, Location: to.toString() } });
}

export async function onRequestPost({ request, env }) {
  if (env.UNCOST_CONTACT_FORM_OPEN !== "on" || !env.CONTACT_MAILER) {
    return new Response("Not found", { status: 404, headers: { "Cache-Control": "no-store" } });
  }
  if (!sameOrigin(request)) return answer(request, false);
  const length = Number(request.headers.get("Content-Length") || 0);
  if (length > MAX_BODY) return answer(request, false);

  let fields;
  try {
    const form = await request.formData();
    fields = Object.fromEntries([...form.entries()].filter(([, v]) => typeof v === "string"));
  } catch {
    return answer(request, false);
  }

  const checked = validate(fields);
  if (checked.spam) return answer(request, true);
  if (!checked.ok) return answer(request, false);

  try {
    const sent = await env.CONTACT_MAILER.fetch("https://contact-mailer.internal/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(checked.msg),
    });
    return answer(request, sent.ok);
  } catch {
    return answer(request, false);
  }
}

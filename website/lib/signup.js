// Shared by the sign-up Pages Functions (website/functions/api/signup/*.js;
// records/changes/CHG-009). It sits outside functions/ so it is not a route.
//
// Same shape as the contact form (functions/api/contact.js): every handler is
// dark — 404, exactly as if there were no handler — unless the Pages
// environment sets UNCOST_SIGNUPS_OPEN to "on" AND carries the SIGNUPS Service
// binding to the uncost-signups Worker (uncost-org/uncost-api). The Worker
// does the validation, storage and email; these handlers check the request's
// origin, hash the consent texts the form showed, and forward.
// No cookies are set anywhere.

import signups from "../src/_data/signups.json" with { type: "json" };

export const MAX_BODY = 16 * 1024;
const NO_STORE = { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" };

export const isOpen = (env) => env.UNCOST_SIGNUPS_OPEN === "on" && !!env.SIGNUPS;

export function notFound() {
  return new Response("Not found", { status: 404, headers: NO_STORE });
}

// A browser POST from another site is refused. A POST with no Origin and no
// Sec-Fetch-Site (a mail provider's RFC 8058 one-click, SNS) is let through.
export function sameOrigin(request) {
  const origin = request.headers.get("Origin");
  const site = request.headers.get("Sec-Fetch-Site");
  if (site && site !== "same-origin") return false;
  if (origin && origin !== new URL(request.url).origin) return false;
  return true;
}

export const wantsJson = (request) => (request.headers.get("Accept") || "").includes("application/json");

export function redirect(request, path) {
  return new Response(null, { status: 303, headers: { ...NO_STORE, Location: new URL(path, request.url).toString() } });
}

export function jsonAnswer(status, body) {
  return new Response(JSON.stringify(body), { status, headers: { ...NO_STORE, "Content-Type": "application/json" } });
}

export async function formFields(request, names) {
  const length = Number(request.headers.get("Content-Length") || 0);
  if (length > MAX_BODY) return null;
  try {
    const form = await request.formData();
    const out = {};
    for (const n of names) { const v = form.get(n); if (typeof v === "string") out[n] = v; }
    return out;
  } catch {
    return null;
  }
}

async function sha256Hex(text) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

export const ageText = () => signups.texts.age.replace("{minAge}", String(signups.minAge));

// The consent block for the Worker: per purpose, the SHA-256 of the exact text
// the form showed for it followed by the age confirmation's text (both boxes
// had to be ticked), plus the policy version and the surface.
export async function consentFor(kind, fields) {
  const age = ageText();
  const texts = {};
  if (kind === "pledge") {
    texts.signing = await sha256Hex(`${signups.texts.signing}\n${age}`);
    if (fields.updates === "yes") texts.email_updates = await sha256Hex(`${signups.texts.email_updates_pledge}\n${age}`);
  } else {
    texts.email_updates = await sha256Hex(`${signups.texts.email_updates}\n${age}`);
  }
  const surface = kind === "pledge" ? "pledge" : signups.surfaces.includes(fields.surface) ? fields.surface : "footer";
  return { policyVersion: signups.policyVersion, surface, texts };
}

// The answer to a sign-up post. `forwarding` is a function that forwards it
// to the Worker, which answers 202 (accepted), 400 (refused) or 503 (closed,
// answered as dark). A forward that fails, or any other answer, means the
// sign-up was not sent: JSON 502 {"ok": false}, or a 303 to /signup/not-sent/.
export async function answerIntake(request, json, forwarding, okPath) {
  let status = 0;
  try { status = (await forwarding()).status; } catch { /* not sent */ }
  if (status === 503) return notFound();
  const ok = status === 202;
  if (json) return jsonAnswer(ok ? 202 : status === 400 ? 400 : 502, { ok });
  return redirect(request, ok ? okPath : "/signup/not-sent/");
}

export function forward(env, path, payload) {
  return env.SIGNUPS.fetch(`https://signups.internal${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: typeof payload === "string" ? payload : JSON.stringify(payload),
  });
}

export const tokenFrom = (request, fields = {}) =>
  (new URL(request.url).searchParams.get("t") || fields.t || "").slice(0, 100);

const escapeHtml = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

// The no-JS confirm page for a link from an email (confirm, unsubscribe,
// delete): it asks before acting, so a mail scanner that opens the link
// changes nothing. Only the page's POST acts.
// It reuses the pledge flow's card and the site's own stylesheets. _headers
// does not reach a Function's response, so the page sends its own security
// headers; its CSP is stricter than the site's (no script at all).
const PAGE_HEADERS = {
  ...NO_STORE,
  "Content-Type": "text/html; charset=utf-8",
  "Content-Security-Policy": "default-src 'none'; style-src 'self'; img-src 'self'; font-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'",
  // same-origin, not no-referrer: a browser's form POST from a no-referrer page
  // carries Origin: null, which sameOrigin() refuses, so every Confirm press
  // landed on link-expired (preview test, 2026-10-24). same-origin still sends
  // nothing to another site, and the page loads nothing from one.
  "Referrer-Policy": "same-origin",
  "X-Frame-Options": "DENY",
  "Cross-Origin-Opener-Policy": "same-origin",
  "X-Robots-Tag": "noindex",
};

export function confirmPage({ title, eyebrow, heading, paragraphs, action, token, button }) {
  const body = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>${escapeHtml(title)} · Uncost</title>
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon.ico" sizes="16x16 32x32 48x48">
<link rel="stylesheet" href="/css/tokens.css">
<link rel="stylesheet" href="/css/components.css">
<link rel="stylesheet" href="/css/site.css">
<link rel="stylesheet" href="/css/sections.css">
<link rel="stylesheet" href="/css/integration.css">
<link rel="stylesheet" href="/css/integration-v43-gap.css">
</head>
<body data-page="pledge-check-email">
<main id="main">
<div class="sys">
  <div class="card">
    <div class="bd">
      <div class="eq">${escapeHtml(eyebrow)}</div>
      <h1>${escapeHtml(heading)}</h1>
${paragraphs.map((p) => `      <p>${escapeHtml(p)}</p>`).join("\n")}
      <form class="actions" method="post" action="${escapeHtml(action)}">
        <input type="hidden" name="t" value="${escapeHtml(token)}">
        <button class="u-btn u-btn--ink" type="submit">${escapeHtml(button)}</button>
        <a class="u-btn u-btn--ghost" href="/">Back to uncost.org</a>
      </form>
    </div>
  </div>
</div>
</main>
</body>
</html>`;
  return new Response(body, { status: 200, headers: PAGE_HEADERS });
}

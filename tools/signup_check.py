#!/usr/bin/env python3
"""Sign-up check — the Pledge and email updates handlers, and the forms in a browser.

The /pledge/ form and the email updates form (features.formsOpen;
records/changes/CHG-009) post to website/functions/api/signup/*.js, which
forward through the SIGNUPS Service binding to the uncost-signups Worker
(uncost-org/uncost-api, tested there). Nothing here talks to Cloudflare: the
handlers run in Node against a mocked binding, and the browser half
intercepts /api/signup/*. Standing rule 4: these are the results to report.

  HANDLERS (Node): every route is dark (404) unless UNCOST_SIGNUPS_OPEN is
    "on" AND the SIGNUPS binding exists, and a closed Worker (503) reads as
    dark too. A cross-origin post, a cross-site Sec-Fetch-Site or an
    over-long body is refused and nothing is forwarded. A sign-up forwards
    the fields with the consent block: the policy version, the surface, and
    per purpose the SHA-256 of the exact text the form shows (from
    _data/signups.json) plus the age box's text. JSON for fetch; a plain post
    is sent to /pledge/check-email/, /updates/check-email/ or
    /signup/not-sent/. A forward that fails, or a Worker answer other than
    202, 400 or 503, is answered as not sent (JSON 502 {"ok": false}, or
    /signup/not-sent/). The confirm, unsubscribe and delete links show a
    no-JS confirm page (noindex, no script, its own CSP) and act only on its
    POST, which must be same-origin; a confirmed link sends each Worker
    answer to its page; an RFC 8058 one-click POST unsubscribes with a bare
    200. SES events pass through untouched. No
    response sets a cookie.
  BROWSER (puppeteer, a build with UNCOST_FORMS_OPEN=on): each form's
    controls have labels, the boxes are unticked, the required set is right,
    the form links /privacy/,
    the honeypot is not rendered and never takes focus, and the box texts are
    exactly the texts the handler hashes; ids are unique where the updates
    form appears twice; with JS on the form is sent with fetch (Accept:
    application/json) and the result is written in place for 202, 400, 404,
    429 and a network failure; an unticked age box sends nothing and native
    validation focuses it; with JS off the post lands on the check-email page.

    python3 tools/signup_check.py --built DIR   # a build with UNCOST_FORMS_OPEN=on
    python3 tools/signup_check.py --unit-only

Exit 0 when ok, 1 on any error.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from contact_form_check import serve  # noqa: E402  (same static server)

ROOT = pathlib.Path(__file__).resolve().parents[1]
WEBSITE = ROOT / "website"
FUNCTIONS = WEBSITE / "functions" / "api" / "signup"
LIB = WEBSITE / "lib" / "signup.js"
DATA = WEBSITE / "src" / "_data" / "signups.json"

UNIT_JS = r"""
import { readFileSync } from "node:fs";
import * as pledge from "./functions/api/signup/pledge.js";
import * as updates from "./functions/api/signup/updates.js";
import * as confirm from "./functions/api/signup/confirm.js";
import * as unsubscribe from "./functions/api/signup/unsubscribe.js";
import * as del from "./functions/api/signup/delete.js";
import * as ses from "./functions/api/signup/ses-events.js";
const data = JSON.parse(readFileSync(new URL("./src/_data/signups.json", import.meta.url), "utf8"));
const errors = [], results = [];
const ORIGIN = "https://uncost.org";
const age = data.texts.age.replace("{minAge}", String(data.minAge));
const sha = async (t) => [...new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(t)))].map((b) => b.toString(16).padStart(2, "0")).join("");

function worker(answer = () => new Response(JSON.stringify({ ok: true }), { status: 202 })) {
  const calls = [];
  return { calls, fetch: async (url, init) => { calls.push({ path: new URL(url).pathname, body: init.body }); return answer(new URL(url).pathname, init); } };
}
const env = (w, on = "on") => ({ UNCOST_SIGNUPS_OPEN: on, SIGNUPS: w });
function post(path, fields, { json = true, origin = ORIGIN, site = "same-origin", length } = {}) {
  const fd = new FormData();
  for (const [k, v] of Object.entries(fields)) fd.append(k, v);
  const h = new Headers();
  if (json) h.set("Accept", "application/json");
  if (origin) h.set("Origin", origin);
  if (site) h.set("Sec-Fetch-Site", site);
  if (length) h.set("Content-Length", String(length));
  return new Request(ORIGIN + path, { method: "POST", body: fd, headers: h });
}
const get = (path) => new Request(ORIGIN + path, { method: "GET" });
function check(name, got, want) {
  results.push({ name, ...got });
  for (const [k, v] of Object.entries(want)) {
    if (JSON.stringify(got[k]) !== JSON.stringify(v)) errors.push(`${name}: ${k} = ${JSON.stringify(got[k])}, expected ${JSON.stringify(v)}`);
  }
}
async function call(fn, request, e) {
  const res = await fn({ request, env: e });
  if (res.headers.get("Set-Cookie")) errors.push(`COOKIE: ${new URL(request.url).pathname} set a cookie`);
  const ct = res.headers.get("Content-Type") || "";
  const body = ct.includes("json") ? await res.json() : await res.text();
  return { status: res.status, location: res.headers.get("Location"), body, headers: res.headers };
}
const goodPledge = { email: "ann@example.org", name: "Ann", agree: "yes", age: "yes", hp_url: "" };
const goodUpdates = { email: "ann@example.org", consent: "yes", age: "yes", surface: "home", hp_url: "" };

// Dark unless switched on, with the binding.
for (const [label, e] of [["switch off", env(worker(), "off")], ["no binding", { UNCOST_SIGNUPS_OPEN: "on" }]]) {
  const w = e.SIGNUPS;
  const r = [
    await call(pledge.onRequestPost, post("/api/signup/pledge", goodPledge), e),
    await call(updates.onRequestPost, post("/api/signup/updates", goodUpdates), e),
    await call(confirm.onRequestGet, get("/api/signup/confirm?t=x"), e),
    await call(confirm.onRequestPost, post("/api/signup/confirm", { t: "x" }, { json: false }), e),
    await call(unsubscribe.onRequestGet, get("/api/signup/unsubscribe?t=x"), e),
    await call(unsubscribe.onRequestPost, post("/api/signup/unsubscribe?t=x", { "List-Unsubscribe": "One-Click" }, { origin: null, site: null }), e),
    await call(del.onRequestGet, get("/api/signup/delete?t=x"), e),
    await call(del.onRequestPost, post("/api/signup/delete", { t: "x" }), e),
    await call(ses.onRequestPost, new Request(ORIGIN + "/api/signup/ses-events", { method: "POST", body: "{}" }), e),
  ].map((x) => x.status);
  check(`dark: ${label}`, { statuses: r, forwarded: w ? w.calls.length : 0 }, { statuses: [404, 404, 404, 404, 404, 404, 404, 404, 404], forwarded: 0 });
}

// Pledge.
let w = worker(), r = await call(pledge.onRequestPost, post("/api/signup/pledge", goodPledge), env(w));
let sent = w.calls[0] ? JSON.parse(w.calls[0].body) : {};
check("pledge: valid", { status: r.status, body: r.body, path: w.calls[0] && w.calls[0].path, signing: sent.consent && sent.consent.texts.signing,
  updatesHash: sent.consent && sent.consent.texts.email_updates || null, surface: sent.consent && sent.consent.surface,
  policyVersion: sent.consent && sent.consent.policyVersion, origin: sent.origin, fields: sent.fields },
  { status: 202, body: { ok: true }, path: "/v1/pledge", signing: await sha(data.texts.signing + "\n" + age), updatesHash: null,
    surface: "pledge", policyVersion: data.policyVersion, origin: ORIGIN, fields: goodPledge });
w = worker(); r = await call(pledge.onRequestPost, post("/api/signup/pledge", { ...goodPledge, updates: "yes" }), env(w));
sent = w.calls[0] ? JSON.parse(w.calls[0].body) : {};
check("pledge: with updates", { status: r.status, updatesHash: sent.consent && sent.consent.texts.email_updates },
  { status: 202, updatesHash: await sha(data.texts.email_updates_pledge + "\n" + age) });
w = worker(); r = await call(pledge.onRequestPost, post("/api/signup/pledge", goodPledge, { json: false }), env(w));
check("pledge: plain post", { status: r.status, location: r.location }, { status: 303, location: ORIGIN + "/pledge/check-email/" });
w = worker(() => new Response('{"ok":false}', { status: 400 }));
r = await call(pledge.onRequestPost, post("/api/signup/pledge", goodPledge), env(w));
check("pledge: refused (json)", { status: r.status, body: r.body }, { status: 400, body: { ok: false } });
r = await call(pledge.onRequestPost, post("/api/signup/pledge", goodPledge, { json: false }), env(w));
check("pledge: refused (plain)", { status: r.status, location: r.location }, { status: 303, location: ORIGIN + "/signup/not-sent/" });
w = worker(() => new Response('{"ok":false,"closed":true}', { status: 503 }));
r = await call(pledge.onRequestPost, post("/api/signup/pledge", goodPledge), env(w));
check("pledge: Worker closed", { status: r.status }, { status: 404 });
// A failed forward, or an unexpected Worker answer: not sent.
for (const [label, answer] of [["forward fails", () => { throw new Error("down"); }], ["forward rejects", () => Promise.reject(new Error("down"))], ["Worker 500", () => new Response("{}", { status: 500 })]]) {
  for (const [mod, path, fields] of [[pledge, "/api/signup/pledge", goodPledge], [updates, "/api/signup/updates", goodUpdates]]) {
    w = worker(answer);
    const j = await call(mod.onRequestPost, post(path, fields), env(w));
    const pl = await call(mod.onRequestPost, post(path, fields, { json: false }), env(w));
    check(`${path.split("/").pop()}: ${label}`, { json: j.status, body: j.body, plain: pl.status, location: pl.location },
      { json: 502, body: { ok: false }, plain: 303, location: ORIGIN + "/signup/not-sent/" });
  }
}
for (const [label, opts] of [["cross origin", { origin: "https://evil.example" }], ["cross site", { site: "cross-site" }], ["same site", { site: "same-site" }]]) {
  w = worker(); r = await call(pledge.onRequestPost, post("/api/signup/pledge", goodPledge, opts), env(w));
  check(`pledge: ${label}`, { status: r.status, forwarded: w.calls.length }, { status: 403, forwarded: 0 });
}
w = worker(); r = await call(pledge.onRequestPost, post("/api/signup/pledge", goodPledge, { length: 20000 }), env(w));
check("pledge: body too long", { status: r.status, forwarded: w.calls.length }, { status: 400, forwarded: 0 });

// Updates.
w = worker(); r = await call(updates.onRequestPost, post("/api/signup/updates", goodUpdates), env(w));
sent = w.calls[0] ? JSON.parse(w.calls[0].body) : {};
check("updates: valid", { status: r.status, path: w.calls[0] && w.calls[0].path, hash: sent.consent && sent.consent.texts.email_updates,
  signing: sent.consent && sent.consent.texts.signing || null, surface: sent.consent && sent.consent.surface },
  { status: 202, path: "/v1/updates", hash: await sha(data.texts.email_updates + "\n" + age), signing: null, surface: "home" });
w = worker(); await call(updates.onRequestPost, post("/api/signup/updates", { ...goodUpdates, surface: "<script>" }), env(w));
check("updates: unknown surface", { surface: JSON.parse(w.calls[0].body).consent.surface }, { surface: "footer" });
w = worker(); r = await call(updates.onRequestPost, post("/api/signup/updates", goodUpdates, { json: false }), env(w));
check("updates: plain post", { status: r.status, location: r.location }, { status: 303, location: ORIGIN + "/updates/check-email/" });
w = worker(); r = await call(updates.onRequestPost, post("/api/signup/updates", goodUpdates, { origin: "https://evil.example", json: false }), env(w));
check("updates: cross origin (plain)", { status: r.status, location: r.location, forwarded: w.calls.length }, { status: 303, location: ORIGIN + "/signup/not-sent/", forwarded: 0 });

// Confirm: the POST from the confirm page sends each Worker answer to its page.
const answers = [
  [{ result: "confirmed", kind: "pledge" }, "/pledge/verify/"], [{ result: "already", kind: "pledge" }, "/pledge/verify/"],
  [{ result: "confirmed", kind: "updates" }, "/updates/confirmed/"], [{ result: "already", kind: "updates" }, "/updates/confirmed/"],
  [{ result: "expired", kind: "pledge" }, "/pledge/resent/"], [{ result: "expired", kind: "updates" }, "/signup/link-expired/"],
  [{ result: "invalid" }, "/signup/link-expired/"],
];
for (const [answer, page] of answers) {
  w = worker(() => new Response(JSON.stringify(answer), { status: 200 }));
  r = await call(confirm.onRequestPost, post("/api/signup/confirm", { t: "tok123" }, { json: false }), env(w));
  check(`confirm: ${answer.result} ${answer.kind || ""}`, { status: r.status, location: r.location, path: w.calls[0] && w.calls[0].path, token: w.calls[0] && JSON.parse(w.calls[0].body).token },
    { status: 303, location: ORIGIN + page, path: "/v1/confirm", token: "tok123" });
}
w = worker(() => { throw new Error("down"); });
r = await call(confirm.onRequestPost, post("/api/signup/confirm", { t: "tok123" }, { json: false }), env(w));
check("confirm: Worker unreachable", { status: r.status, location: r.location }, { status: 303, location: ORIGIN + "/signup/link-expired/" });
for (const [label, opts] of [["cross origin", { origin: "https://evil.example" }], ["cross site", { origin: null, site: "cross-site" }]]) {
  w = worker(() => new Response('{"result":"confirmed","kind":"pledge"}', { status: 200 }));
  r = await call(confirm.onRequestPost, post("/api/signup/confirm", { t: "tok123" }, { json: false, ...opts }), env(w));
  check(`confirm: ${label}`, { location: r.location, forwarded: w.calls.length }, { location: ORIGIN + "/signup/link-expired/", forwarded: 0 });
}

// Confirm, unsubscribe and delete: opening the link shows a confirm page and
// changes nothing; only its POST acts.
for (const [mod, path, label] of [[confirm, "/api/signup/confirm", "confirm"], [unsubscribe, "/api/signup/unsubscribe", "unsubscribe"], [del, "/api/signup/delete", "delete"]]) {
  w = worker();
  r = await call(mod.onRequestGet, get(`${path}?t=tok"<x`), env(w));
  const csp = r.headers.get("Content-Security-Policy") || "";
  check(`${label}: GET shows a confirm page`, { status: r.status, forwarded: w.calls.length, noindex: /<meta name="robots" content="noindex">/.test(r.body),
    script: /<script/i.test(r.body), postsToken: r.body.includes(`<form class="actions" method="post" action="${path}">`) && r.body.includes('value="tok&quot;&lt;x"'),
    csp: /default-src 'none'/.test(csp) && /form-action 'self'/.test(csp) && !/script-src/.test(csp) },
    { status: 200, forwarded: 0, noindex: true, script: false, postsToken: true, csp: true });
}
// A browser's press on each confirm page. A form POST carries the Origin the
// browser derives from that page's Referrer-Policy (Fetch standard, "append a
// request Origin header"): "no-referrer" makes it Origin: null, which
// sameOrigin() rightly refuses, so the press would land on link-expired
// without reaching the Worker (the preview test, 2026-10-24).
const browserOrigin = (policy, pageOrigin) =>
  (policy || "").split(",").map((x) => x.trim()).filter(Boolean).pop() === "no-referrer" ? "null" : pageOrigin;
for (const [mod, path, label, answer, page] of [
  [confirm, "/api/signup/confirm", "confirm", { result: "confirmed", kind: "pledge" }, "/pledge/verify/"],
  [unsubscribe, "/api/signup/unsubscribe", "unsubscribe", { result: "done" }, "/signup/unsubscribed/"],
  [del, "/api/signup/delete", "delete", { result: "deleted" }, "/signup/deleted/"],
]) {
  w = worker(() => new Response(JSON.stringify(answer), { status: 200 }));
  const shown = await call(mod.onRequestGet, get(`${path}?t=tokB`), env(w));
  const origin = browserOrigin(shown.headers.get("Referrer-Policy"), ORIGIN);
  r = await call(mod.onRequestPost, post(path, { t: "tokB" }, { json: false, origin, site: "same-origin" }), env(w));
  check(`${label}: a browser's press on the confirm page`, { origin, location: r.location, forwarded: w.calls.length },
    { origin: ORIGIN, location: ORIGIN + page, forwarded: 1 });
}
w = worker(() => new Response('{"result":"done"}', { status: 200 }));
r = await call(unsubscribe.onRequestPost, post("/api/signup/unsubscribe?t=tok1", { "List-Unsubscribe": "One-Click" }, { origin: null, site: null, json: false }), env(w));
check("unsubscribe: RFC 8058 one-click", { status: r.status, body: r.body, token: w.calls[0] && JSON.parse(w.calls[0].body).token }, { status: 200, body: "", token: "tok1" });
w = worker(() => new Response('{"result":"done"}', { status: 200 }));
r = await call(unsubscribe.onRequestPost, post("/api/signup/unsubscribe", { t: "tok2" }, { json: false }), env(w));
check("unsubscribe: confirm page", { status: r.status, location: r.location, token: w.calls[0] && JSON.parse(w.calls[0].body).token },
  { status: 303, location: ORIGIN + "/signup/unsubscribed/", token: "tok2" });
w = worker(() => new Response('{"result":"expired"}', { status: 200 }));
r = await call(unsubscribe.onRequestPost, post("/api/signup/unsubscribe", { t: "tok3" }, { json: false }), env(w));
check("unsubscribe: expired link", { location: r.location }, { location: ORIGIN + "/signup/link-expired/" });
w = worker(); r = await call(unsubscribe.onRequestPost, post("/api/signup/unsubscribe", { t: "tok4" }, { json: false, origin: "https://evil.example" }), env(w));
check("unsubscribe: cross origin", { location: r.location, forwarded: w.calls.length }, { location: ORIGIN + "/signup/link-expired/", forwarded: 0 });
w = worker(() => new Response('{"result":"deleted"}', { status: 200 }));
r = await call(del.onRequestPost, post("/api/signup/delete", { t: "tok5" }, { json: false }), env(w));
check("delete: confirm page", { status: r.status, location: r.location, token: w.calls[0] && JSON.parse(w.calls[0].body).token },
  { status: 303, location: ORIGIN + "/signup/deleted/", token: "tok5" });
w = worker(() => new Response('{"result":"invalid"}', { status: 200 }));
r = await call(del.onRequestPost, post("/api/signup/delete", { t: "used" }, { json: false }), env(w));
check("delete: used or invalid link", { location: r.location }, { location: ORIGIN + "/signup/link-expired/" });
w = worker(); r = await call(del.onRequestPost, post("/api/signup/delete", { t: "tok6" }, { json: false, origin: null, site: "cross-site" }), env(w));
check("delete: cross site", { location: r.location, forwarded: w.calls.length }, { location: ORIGIN + "/signup/link-expired/", forwarded: 0 });

// SES events: the body passes through untouched; the Worker's verdict is the status.
for (const [status, want] of [[200, 200], [400, 400], [401, 401], [500, 502]]) {
  w = worker(() => new Response("{}", { status }));
  const body = '{"Type":"Notification","Message":"{}"}';
  r = await call(ses.onRequestPost, new Request(ORIGIN + "/api/signup/ses-events", { method: "POST", body, headers: { "Content-Type": "text/plain" } }), env(w));
  check(`ses-events: Worker ${status}`, { status: r.status, passed: w.calls[0] && w.calls[0].body === body && w.calls[0].path === "/v1/ses-events" }, { status: want, passed: true });
}
w = worker();
r = await call(ses.onRequestPost, new Request(ORIGIN + "/api/signup/ses-events", { method: "POST", body: "x".repeat(300000) }), env(w));
check("ses-events: too large", { status: r.status, forwarded: w.calls.length }, { status: 413, forwarded: 0 });
process.stdout.write(JSON.stringify({ errors, results: results.map((x) => x.name) }));
"""

BROWSER_JS = r"""
const puppeteer = require(require.resolve("puppeteer", { paths: [process.argv[2]] }));
const base = process.argv[3];
const data = JSON.parse(process.argv[4]);
(async () => {
  const browser = await puppeteer.launch({ args: ["--no-sandbox"] });
  const errors = [], steps = [];
  const age = data.texts.age.replace("{minAge}", String(data.minAge));
  async function page(path, js, respond) {
    const p = await browser.newPage();
    await p.setCacheEnabled(false);
    await p.setJavaScriptEnabled(js);
    await p.setViewport({ width: 1280, height: 900 });
    const posts = [];
    await p.setRequestInterception(true);
    p.on("request", (rq) => {
      if (rq.url().includes("/api/signup/")) {
        posts.push({ url: rq.url(), method: rq.method(), accept: rq.headers()["accept"] || "", body: rq.postData() || "" });
        return respond(rq);
      }
      rq.continue();
    });
    await p.goto(base + path, { waitUntil: "networkidle0" });
    return { p, posts };
  }
  const answer = (status) => (rq) => rq.respond({ status, contentType: "application/json", body: JSON.stringify({ ok: status === 202 }) });
  const settle = () => new Promise((r) => setTimeout(r, 300));
  const FORMS = {
    pledge: { path: "/pledge/", form: 'form[data-form="pledge"]', note: 'form[data-form="pledge"] .err', required: ["email", "agree", "age"],
              texts: { agree: data.texts.signing, updates: data.texts.email_updates_pledge, age } },
    updates: { path: "/", form: '.ft-updates form[data-form="updates"]', note: ".ft-updates [data-updates-note]", required: ["email", "consent", "age"],
               texts: { consent: data.texts.email_updates, age } },
  };

  for (const [kind, F] of Object.entries(FORMS)) {
    // Markup: labels, unticked boxes, required set, honeypot, exact box texts.
    let { p } = await page(F.path, true, answer(202));
    const m = await p.evaluate((sel) => {
      const f = document.querySelector(sel);
      const fields = [...f.querySelectorAll("input")].filter((el) => el.type !== "hidden" && el.name !== "hp_url");
      const labelOf = (el) => el.closest("label") || (el.id && document.querySelector(`label[for="${el.id}"]`));
      const boxText = (el) => { const l = el.closest("label"); if (!l) return ""; const c = l.cloneNode(true); c.querySelectorAll(".req, a").forEach((n) => n.remove()); return c.textContent.replace(/\s+/g, " ").trim(); };
      const ids = [...document.querySelectorAll("[id]")].map((el) => el.id);
      const hp = f.querySelector('[name="hp_url"]');
      return { unlabelled: fields.filter((el) => !labelOf(el)).map((el) => el.name),
               ticked: fields.filter((el) => el.type === "checkbox" && el.checked).map((el) => el.name),
               required: fields.filter((el) => el.required).map((el) => el.name),
               boxes: Object.fromEntries(fields.filter((el) => el.type === "checkbox").map((el) => [el.name, boxText(el)])),
               hpRendered: !!hp && hp.getClientRects().length > 0, hpId: hp && hp.id,
               duplicateIds: ids.filter((id, i) => ids.indexOf(id) !== i),
               privacyLink: !!f.querySelector('a[href^="/privacy/"]'),
               action: f.getAttribute("action"), method: f.getAttribute("method"), novalidate: f.hasAttribute("novalidate") };
    }, F.form);
    steps.push({ step: `${kind}: markup`, ...m });
    if (m.unlabelled.length) errors.push(`${kind} LABEL: no label on ${m.unlabelled}`);
    if (m.ticked.length) errors.push(`${kind} CONSENT: ticked by default: ${m.ticked}`);
    if (JSON.stringify(m.required) !== JSON.stringify(F.required)) errors.push(`${kind} REQUIRED: ${m.required}`);
    if (m.hpRendered) errors.push(`${kind} HONEYPOT: rendered`);
    if (m.duplicateIds.length) errors.push(`${kind} IDS: duplicated ${m.duplicateIds}`);
    if (!m.privacyLink) errors.push(`${kind} PRIVACY: the form does not link /privacy/`);
    if (m.action !== `/api/signup/${kind}` || m.method !== "post" || m.novalidate) errors.push(`${kind} FORM: action ${m.action} method ${m.method} novalidate ${m.novalidate}`);
    for (const [name, text] of Object.entries(F.texts)) {
      if (m.boxes[name] !== text) errors.push(`${kind} TEXT: the ${name} box reads "${m.boxes[name]}", but the handler hashes "${text}"`);
    }
    // Keyboard: the honeypot never takes focus.
    await p.focus(`${F.form} input[type="email"]`);
    const order = [];
    for (let i = 0; i < 8; i++) { order.push(await p.evaluate(() => document.activeElement.id || document.activeElement.name || document.activeElement.textContent.trim().slice(0, 16))); await p.keyboard.press("Tab"); }
    if (order.includes(m.hpId) || order.includes("hp_url")) errors.push(`${kind} HONEYPOT: takes keyboard focus`);
    await p.close();

    const fill = async (pg, { ageBox = true } = {}) => {
      await pg.type(`${F.form} input[type="email"]`, "ann@example.org");
      for (const name of F.required.filter((n) => n !== "email")) {
        if (name === "age" && !ageBox) continue;
        await pg.click(`${F.form} input[name="${name}"]`);
      }
    };
    // JS on: each answer is written in place.
    const expect = { 202: /Check your inbox/, 400: /wasn’t accepted/, 404: /closed/, 429: /wait a few minutes/, 0: /didn’t go through/ };
    for (const status of [202, 400, 404, 429, 0]) {
      const pp = await page(F.path, true, status ? answer(status) : (rq) => rq.abort("failed"));
      await fill(pp.p);
      await pp.p.click(`${F.form} button[type="submit"]`); await settle();
      const note = await pp.p.$eval(F.note, (n) => n.textContent.trim());
      const reset = await pp.p.$eval(`${F.form} input[type="email"]`, (i) => i.value === "");
      steps.push({ step: `${kind}: js on, ${status || "network error"}`, note, reset, accept: (pp.posts[0] || {}).accept });
      if (!expect[status].test(note)) errors.push(`${kind} ${status || "network"}: the note reads "${note}"`);
      if (!/application\/json/.test((pp.posts[0] || {}).accept || "")) errors.push(`${kind}: the request did not ask for JSON`);
      if ((status === 202) !== reset) errors.push(`${kind} ${status}: reset is ${reset}`);
      await pp.p.close();
    }
    // JS on, age box unticked: nothing is sent; focus goes to it.
    let pp = await page(F.path, true, answer(202));
    await fill(pp.p, { ageBox: false });
    await pp.p.click(`${F.form} button[type="submit"]`); await settle();
    const focus = await pp.p.evaluate(() => document.activeElement && document.activeElement.name);
    steps.push({ step: `${kind}: age unticked`, posts: pp.posts.length, focus });
    if (pp.posts.length) errors.push(`${kind} AGE: sent without the age box`);
    if (focus !== "age") errors.push(`${kind} AGE: focus is on ${focus}`);
    await pp.p.close();
    // JS off: a plain post lands on the check-email page.
    const landing = kind === "pledge" ? "/pledge/check-email/" : "/updates/check-email/";
    pp = await page(F.path, false, (rq) => rq.respond({ status: 303, headers: { Location: base + landing }, body: "" }));
    await fill(pp.p);
    await Promise.all([pp.p.waitForNavigation({ waitUntil: "networkidle0" }), pp.p.click(`${F.form} button[type="submit"]`)]);
    const landed = { url: pp.p.url(), h1: await pp.p.$eval("h1", (h) => h.textContent.trim()), method: (pp.posts[0] || {}).method, body: (pp.posts[0] || {}).body };
    steps.push({ step: `${kind}: js off`, url: landed.url, h1: landed.h1, method: landed.method });
    if (!landed.url.endsWith(landing) || !/Check your inbox/.test(landed.h1)) errors.push(`${kind} NOJS: landed on ${landed.url} ("${landed.h1}")`);
    if (landed.method !== "POST" || !/age=yes/.test(landed.body || "")) errors.push(`${kind} NOJS: the browser did not post the form with the age box`);
    await pp.p.close();
  }
  // A real browser's Confirm press. The page is the confirm handler's own GET
  // output, headers included; Chromium submits its form, and the headers it
  // sent go to the real POST handler, which must forward and redirect.
  {
    const { pathToFileURL } = require("node:url");
    const path = require("node:path");
    const confirmMod = await import(pathToFileURL(path.join(process.argv[2], "functions", "api", "signup", "confirm.js")).href);
    const shown = await confirmMod.onRequestGet({ request: new Request(base + "/api/signup/confirm?t=tokC"), env: { UNCOST_SIGNUPS_OPEN: "on", SIGNUPS: {} } });
    const html = await shown.text();
    const headers = Object.fromEntries(shown.headers.entries());
    const p = await browser.newPage();
    await p.setRequestInterception(true);
    let posted = null;
    p.on("request", (rq) => {
      const u = new URL(rq.url());
      if (u.pathname === "/api/signup/confirm" && rq.method() === "GET") return rq.respond({ status: 200, headers, body: html });
      if (u.pathname === "/api/signup/confirm" && rq.method() === "POST") {
        posted = { headers: rq.headers(), body: rq.postData() || "" };
        return rq.respond({ status: 200, contentType: "text/plain", body: "ok" });
      }
      rq.continue();
    });
    await p.goto(base + "/api/signup/confirm?t=tokC", { waitUntil: "networkidle0" });
    await Promise.all([p.waitForNavigation({ waitUntil: "load" }).catch(() => {}), p.click('form.actions button[type="submit"]')]);
    await p.close();
    if (!posted) {
      errors.push("CONFIRM PRESS: Chromium sent no POST from the confirm page");
    } else {
      const calls = [];
      const env = { UNCOST_SIGNUPS_OPEN: "on", SIGNUPS: { fetch: async (url) => { calls.push(url); return new Response('{"result":"confirmed","kind":"pledge"}', { status: 200 }); } } };
      const h = new Headers();
      for (const k of ["origin", "sec-fetch-site", "content-type"]) if (posted.headers[k]) h.set(k, posted.headers[k]);
      const res = await confirmMod.onRequestPost({ request: new Request(base + "/api/signup/confirm", { method: "POST", headers: h, body: posted.body }), env });
      const location = res.headers.get("Location") || "";
      steps.push({ step: "confirm page: a real browser's press", referrerPolicy: headers["referrer-policy"], origin: posted.headers.origin || "(none)",
                   secFetchSite: posted.headers["sec-fetch-site"] || "(none)", location: location.replace(base, ""), forwarded: calls.length });
      if (calls.length !== 1 || !location.endsWith("/pledge/verify/")) {
        errors.push(`CONFIRM PRESS: Chromium's POST (Origin: ${posted.headers.origin || "(none)"}) went to ${location.replace(base, "")} and reached the Worker ${calls.length} times`);
      }
    }
  }

  // /join/ carries the updates form twice too.
  const { p } = await page("/join/", true, answer(202));
  const dup = await p.evaluate(() => { const ids = [...document.querySelectorAll("[id]")].map((el) => el.id); return ids.filter((id, i) => ids.indexOf(id) !== i); });
  if (dup.length) errors.push(`/join/ IDS: duplicated ${dup}`);
  await p.close();
  await browser.close();
  process.stdout.write(JSON.stringify({ errors, steps }));
})().catch((e) => { console.error(e.stack || String(e)); process.exit(2); });
"""


def unit() -> dict:
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="uncost-signup-"))
    try:
        (tmp / "functions" / "api").mkdir(parents=True)
        shutil.copytree(FUNCTIONS, tmp / "functions" / "api" / "signup")
        (tmp / "lib").mkdir()
        shutil.copy(LIB, tmp / "lib" / "signup.js")
        (tmp / "src" / "_data").mkdir(parents=True)
        shutil.copy(DATA, tmp / "src" / "_data" / "signups.json")
        (tmp / "package.json").write_text('{"type": "module"}\n', encoding="utf-8")
        (tmp / "run.mjs").write_text(UNIT_JS, encoding="utf-8")
        p = subprocess.run(["node", str(tmp / "run.mjs")], capture_output=True, text=True, timeout=120)
        if p.returncode != 0:
            return {"errors": [f"UNIT: {p.stderr[-800:]}"], "results": []}
        return json.loads(p.stdout)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def browser(built: pathlib.Path, port: int) -> dict:
    if not (built / "updates" / "check-email" / "index.html").exists():
        return {"errors": [f"BUILD: {built} has no /updates/check-email/ — build with UNCOST_FORMS_OPEN=on"], "steps": []}
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="uncost-signup-b-"))
    try:
        js = tmp / "probe.cjs"
        js.write_text(BROWSER_JS, encoding="utf-8")
        httpd = serve(built, port)
        try:
            p = subprocess.run(["node", str(js), str(WEBSITE), f"http://127.0.0.1:{port}", DATA.read_text(encoding="utf-8")],
                               capture_output=True, text=True, timeout=900)
        finally:
            httpd.shutdown()
            httpd.server_close()
        if p.returncode != 0:
            return {"errors": [f"PROBE: {p.stderr[-800:]}"], "steps": []}
        return json.loads(p.stdout)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--built", default=None, help="a build made with UNCOST_FORMS_OPEN=on")
    ap.add_argument("--port", type=int, default=8962)
    ap.add_argument("--unit-only", action="store_true")
    a = ap.parse_args()
    u = unit()
    out = {"unit_errors": u["errors"], "unit_cases": len(u["results"])}
    errors = list(u["errors"])
    if not a.unit_only:
        if not a.built:
            errors.append("BUILD: pass --built DIR (a build with UNCOST_FORMS_OPEN=on) or --unit-only")
        else:
            b = browser(pathlib.Path(a.built), a.port)
            errors += b["errors"]
            out.update({"browser_errors": b["errors"], "browser_steps": b["steps"]})
    out["ok"] = not errors
    out["unit_results"] = u["results"]
    print(json.dumps(out, indent=1))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())

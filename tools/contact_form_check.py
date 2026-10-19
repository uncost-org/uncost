#!/usr/bin/env python3
"""Contact form check — the handler, the mailer Worker and the form in a browser.

The /contact/ form (features.contactFormOpen; records/changes/CHG-005) posts to
website/functions/api/contact.js, which hands a valid message through a
Service binding to workers/contact-mailer/. Nothing here talks to Cloudflare:
the handler and the Worker run in Node against mocks, and the browser half
intercepts /api/contact. Standing rule 4: these are the results to report.

  HANDLER (Node): dark (404) unless UNCOST_CONTACT_FORM_OPEN is "on" AND the
    CONTACT_MAILER binding exists; a filled honeypot gets the success answer
    and nothing is sent; a missing email or message, an unticked (or wrongly
    valued) consent box, a malformed email, an over-long field, a cross-origin
    post or a cross-site Sec-Fetch-Site is rejected with no reason; a valid
    message reaches the mailer exactly once, carries consent and no phone, with
    CR/LF stripped from single-line fields; JSON for fetch, 303 to
    /contact/sent/ or /contact/not-sent/ for a plain post.
  WORKER (Node): sends only to CONTACT_TO, From contact@uncost.org, the
    visitor as Reply-To (never From), a subject naming the uncost.org contact
    form, a body that quotes the consent box and the 12-month retention rule
    and has no phone line; 400 without consent; 503 without its secret or
    binding; 405 for anything but POST; 502 if sending throws.
  BROWSER (puppeteer, a build with UNCOST_CONTACT_FORM_OPEN=on): with JS on,
    the form is sent with fetch (Accept: application/json) and .cnote reports
    sent / failed (with a mailto link) / network failure; an empty message or
    an unticked consent box sends nothing and native validation focuses that
    control; with JS off, the post lands on /contact/sent/; every field and the
    consent box have a label; there is no phone field; the honeypot is not
    rendered and never takes focus.

    python3 tools/contact_form_check.py --built DIR   # a switch-on build
    python3 tools/contact_form_check.py --unit-only

Exit 0 when ok, 1 on any error.
"""
from __future__ import annotations

import argparse
import http.server
import json
import pathlib
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading

ROOT = pathlib.Path(__file__).resolve().parents[1]
WEBSITE = ROOT / "website"
HANDLER = WEBSITE / "functions" / "api" / "contact.js"
WORKER = ROOT / "workers" / "contact-mailer" / "src" / "index.js"

UNIT_JS = r"""
import { onRequestPost } from "./contact.mjs";
import worker, { compose } from "./worker.mjs";
const errors = [], results = [];
const ORIGIN = "https://uncost.org";
function req(fields, { json = true, origin = ORIGIN, site = "same-origin" } = {}) {
  const fd = new FormData();
  for (const [k, v] of Object.entries(fields)) fd.append(k, v);
  const h = new Headers();
  if (json) h.set("Accept", "application/json");
  if (origin) h.set("Origin", origin);
  if (site) h.set("Sec-Fetch-Site", site);
  return new Request(ORIGIN + "/api/contact", { method: "POST", body: fd, headers: h });
}
function mailer(status = 204) {
  const calls = [];
  return { calls, fetch: async (url, init) => { calls.push(JSON.parse(init.body)); return new Response(null, { status }); } };
}
const env = (m, on = "on") => ({ UNCOST_CONTACT_FORM_OPEN: on, CONTACT_MAILER: m });
const good = { name: "Ada Lovelace", email: "ada@example.org", message: "Hello\nthere", consent: "yes", hp_url: "" };
async function run(name, request, e, want) {
  const res = await onRequestPost({ request, env: e });
  const out = { name, status: res.status, location: res.headers.get("Location") };
  if (res.status === 200) out.body = await res.json();
  results.push(out);
  for (const [k, v] of Object.entries(want)) {
    const got = k === "ok" ? out.body && out.body.ok : k === "sent" ? (e.CONTACT_MAILER ? e.CONTACT_MAILER.calls.length : 0) : out[k];
    if (JSON.stringify(got) !== JSON.stringify(v)) errors.push(`HANDLER ${name}: ${k} = ${JSON.stringify(got)}, expected ${JSON.stringify(v)}`);
  }
}
let m;
await run("switch off", req(good), env(mailer(), "off"), { status: 404 });
await run("no binding", req(good), { UNCOST_CONTACT_FORM_OPEN: "on" }, { status: 404 });
m = mailer(); await run("honeypot", req({ ...good, hp_url: "https://spam.example" }), env(m), { ok: true, sent: 0 });
m = mailer(); await run("no message", req({ ...good, message: " " }), env(m), { ok: false, sent: 0 });
m = mailer(); await run("no email", req({ ...good, email: "" }), env(m), { ok: false, sent: 0 });
m = mailer(); await run("bad email", req({ ...good, email: "ada@localhost" }), env(m), { ok: false, sent: 0 });
m = mailer(); await run("header email", req({ ...good, email: "a@b.org\r\nBcc: x@y.org" }), env(m), { ok: false, sent: 0 });
m = mailer(); await run("long message", req({ ...good, message: "x".repeat(5001) }), env(m), { ok: false, sent: 0 });
m = mailer(); await run("long name", req({ ...good, name: "x".repeat(201) }), env(m), { ok: false, sent: 0 });
m = mailer(); await run("no consent", req({ name: "Ada", email: "ada@example.org", message: "Hi", hp_url: "" }), env(m), { ok: false, sent: 0 });
m = mailer(); await run("consent wrong value", req({ ...good, consent: "on" }), env(m), { ok: false, sent: 0 });
m = mailer(); await run("cross origin", req(good, { origin: "https://evil.example" }), env(m), { ok: false, sent: 0 });
m = mailer(); await run("cross site", req(good, { site: "cross-site" }), env(m), { ok: false, sent: 0 });
m = mailer(); await run("valid", req({ ...good, name: "Ada\r\nBcc: x@y.org" }), env(m), { ok: true, sent: 1 });
if (m.calls[0] && /[\r\n]/.test(m.calls[0].name)) errors.push("HANDLER valid: CR/LF survived in the name");
if (m.calls[0] && m.calls[0].message !== "Hello\nthere") errors.push("HANDLER valid: the message's line break was not kept");
if (m.calls[0] && m.calls[0].consent !== true) errors.push("HANDLER valid: consent did not reach the mailer");
if (m.calls[0] && "phone" in m.calls[0]) errors.push("HANDLER valid: a phone field reached the mailer");
m = mailer(); await run("optional name empty", req({ email: "ada@example.org", message: "Hi", name: "", consent: "yes", hp_url: "" }), env(m), { ok: true, sent: 1 });
m = mailer(); await run("plain post sent", req(good, { json: false }), env(m), { status: 303, location: ORIGIN + "/contact/sent/", sent: 1 });
m = mailer(); await run("plain post invalid", req({ ...good, email: "nope" }, { json: false }), env(m), { status: 303, location: ORIGIN + "/contact/not-sent/", sent: 0 });
m = mailer(502); await run("mailer fails", req(good), env(m), { ok: false, sent: 1 });

// The Worker.
const sent = [];
const wenv = { CONTACT_TO: "founder@inbox.example", SEND_EMAIL: { send: async (msg) => { sent.push(msg); return { messageId: "x" }; } } };
const wreq = (body, method = "POST") => new Request("https://contact-mailer.internal/send", method === "POST" ? { method, body: JSON.stringify(body), headers: { "Content-Type": "application/json" } } : { method });
let r = await worker.fetch(wreq({ name: "Ada", email: "ada@example.org", message: "Hello", consent: true }), wenv);
if (r.status !== 204) errors.push(`WORKER send: status ${r.status}, expected 204`);
const s = sent[0] || {};
if (s.to !== "founder@inbox.example") errors.push(`WORKER: to is ${s.to}, not CONTACT_TO`);
if (s.from !== "contact@uncost.org") errors.push(`WORKER: from is ${s.from}`);
if (s.replyTo !== "ada@example.org") errors.push(`WORKER: replyTo is ${s.replyTo}, not the visitor`);
if (s.from === "ada@example.org") errors.push("WORKER: the visitor is From");
if (!/^uncost\.org contact form/.test(s.subject || "")) errors.push(`WORKER: subject is "${s.subject}"`);
if (!/Hello/.test(s.text || "")) errors.push("WORKER: the message is not in the body");
if (!/Consent: ticked/.test(s.text || "") || !/18 or older/.test(s.text || "")) errors.push("WORKER: the body does not quote the consent box");
if (!/within 12 months/.test(s.text || "")) errors.push("WORKER: the body does not state the retention rule");
if (/Phone/.test(s.text || "")) errors.push("WORKER: the body has a phone line");
results.push({ name: "worker send", to: "CONTACT_TO", from: s.from, replyTo: s.replyTo, subject: s.subject });
r = await worker.fetch(wreq({ email: "a@b.org", message: "x" }), wenv);
if (r.status !== 400) errors.push(`WORKER no consent: status ${r.status}, expected 400`);
r = await worker.fetch(wreq({ email: "a@b.org", message: "x", consent: true }), { SEND_EMAIL: wenv.SEND_EMAIL });
if (r.status !== 503) errors.push(`WORKER no CONTACT_TO: status ${r.status}, expected 503`);
r = await worker.fetch(wreq(null, "GET"), wenv);
if (r.status !== 405) errors.push(`WORKER GET: status ${r.status}, expected 405`);
r = await worker.fetch(wreq({ email: "a@b.org", message: "x", consent: true }), { CONTACT_TO: "f@x.example", SEND_EMAIL: { send: async () => { throw new Error("E_DELIVERY_FAILED"); } } });
if (r.status !== 502) errors.push(`WORKER send throws: status ${r.status}, expected 502`);
const c = compose({ name: "Ada\nBcc: x", email: "ada@example.org", message: "m" });
if (/\n/.test(c.subject)) errors.push("WORKER: a newline reached the subject");
process.stdout.write(JSON.stringify({ errors, results }));
"""

BROWSER_JS = r"""
const puppeteer = require(require.resolve("puppeteer", { paths: [process.argv[2]] }));
const base = process.argv[3];
(async () => {
  const browser = await puppeteer.launch({ args: ["--no-sandbox"] });
  const errors = [], steps = [];
  async function page(js, respond) {
    const p = await browser.newPage();
    await p.setCacheEnabled(false);
    await p.setJavaScriptEnabled(js);
    await p.setViewport({ width: 1280, height: 900 });
    const posts = [];
    await p.setRequestInterception(true);
    p.on("request", (rq) => {
      if (rq.url().endsWith("/api/contact")) {
        posts.push({ method: rq.method(), accept: rq.headers()["accept"] || "", body: rq.postData() || "" });
        return respond(rq);
      }
      rq.continue();
    });
    await p.goto(base + "/contact/", { waitUntil: "networkidle0" });
    return { p, posts };
  }
  const fill = async (p, msg = "Hello from the check", tick = true) => {
    await p.type("#c-name", "Ada"); await p.type("#c-email", "ada@example.org"); await p.type("#c-msg", msg);
    if (tick) await p.click("#c-consent");
  };
  const note = (p) => p.$eval(".cnote", (n) => ({ text: n.textContent.trim(), mailto: !!n.querySelector('a[href="mailto:contact@uncost.org"]') }));
  const settle = () => new Promise((r) => setTimeout(r, 300));

  // Labels and the honeypot (JS on).
  let { p } = await page(true, (rq) => rq.respond({ status: 200, contentType: "application/json", body: '{"ok":true}' }));
  const a11y = await p.evaluate(() => {
    const f = document.querySelector('form[data-form="contact"]');
    const fields = [...f.querySelectorAll("input, textarea")].filter((el) => el.name !== "hp_url");
    const unlabelled = fields.filter((el) => !el.id || !document.querySelector(`label[for="${el.id}"]`)).map((el) => el.name);
    const hp = f.querySelector('[name="hp_url"]');
    const consent = f.querySelector("#c-consent");
    return { forms: document.querySelectorAll("form").length, fields: fields.map((el) => el.name), unlabelled,
             phone: !!f.querySelector('[name="phone"], [type="tel"]'),
             consentChecked: !!consent && consent.checked, consentLabel: consent ? document.querySelector('label[for="c-consent"]').textContent.trim() : "",
             hpRendered: !!hp && hp.getClientRects().length > 0, required: fields.filter((el) => el.required).map((el) => el.name),
             action: f.getAttribute("action"), method: f.getAttribute("method") };
  });
  steps.push({ step: "markup", ...a11y });
  if (a11y.unlabelled.length) errors.push(`LABEL: no <label for> on ${a11y.unlabelled}`);
  if (a11y.hpRendered) errors.push("HONEYPOT: the honeypot field is rendered");
  if (JSON.stringify(a11y.required) !== JSON.stringify(["email", "message", "consent"])) errors.push(`REQUIRED: required fields are ${a11y.required}`);
  if (a11y.phone) errors.push("PHONE: the form still has a phone field");
  if (a11y.consentChecked) errors.push("CONSENT: the consent box is ticked by default");
  if (!/18 or older/.test(a11y.consentLabel) || !/only to reply to this message/.test(a11y.consentLabel)) errors.push(`CONSENT: label reads "${a11y.consentLabel}"`);
  if (a11y.action !== "/api/contact" || a11y.method !== "post") errors.push(`FORM: action ${a11y.action} method ${a11y.method}`);
  await p.focus("#c-name");
  const order = [];
  for (let i = 0; i < 6; i++) { order.push(await p.evaluate(() => document.activeElement.id || document.activeElement.textContent.trim().slice(0, 20))); await p.keyboard.press("Tab"); }
  steps.push({ step: "tab order", order });
  if (order.includes("c-hp")) errors.push("HONEYPOT: the honeypot takes keyboard focus");

  // JS on, sent.
  await fill(p);
  await p.click(".cbtn"); await settle();
  let n = await note(p);
  const reset = await p.$eval("#c-msg", (t) => t.value === "");
  steps.push({ step: "js on: sent", note: n.text, reset });
  if (!/sent/i.test(n.text) || /could not/i.test(n.text)) errors.push(`SENT: .cnote reads "${n.text}"`);
  if (!reset) errors.push("SENT: the form was not reset after sending");
  await p.close();

  // JS on, the handler says no.
  let pp = await page(true, (rq) => rq.respond({ status: 200, contentType: "application/json", body: '{"ok":false}' }));
  await fill(pp.p); await pp.p.click(".cbtn"); await settle();
  n = await note(pp.p);
  steps.push({ step: "js on: refused", note: n.text, mailto: n.mailto, accept: (pp.posts[0] || {}).accept });
  if (!/could not be sent/i.test(n.text) || !n.mailto) errors.push(`FAILED: .cnote reads "${n.text}" (mailto link: ${n.mailto})`);
  if (!/application\/json/.test((pp.posts[0] || {}).accept || "")) errors.push("FETCH: the request did not ask for JSON");
  await pp.p.close();

  // JS on, the network fails.
  pp = await page(true, (rq) => rq.abort("failed"));
  await fill(pp.p); await pp.p.click(".cbtn"); await settle();
  n = await note(pp.p);
  steps.push({ step: "js on: network error", note: n.text });
  if (!/could not be sent/i.test(n.text)) errors.push(`NETWORK: .cnote reads "${n.text}"`);
  await pp.p.close();

  // JS on, message missing: nothing is sent; focus goes to the message.
  pp = await page(true, (rq) => rq.respond({ status: 200, contentType: "application/json", body: '{"ok":true}' }));
  await pp.p.type("#c-email", "ada@example.org");
  await pp.p.click(".cbtn"); await settle();
  const focus = await pp.p.evaluate(() => document.activeElement && document.activeElement.id);
  steps.push({ step: "js on: empty message", posts: pp.posts.length, focus });
  if (pp.posts.length) errors.push("VALIDATION: an empty message was sent");
  if (focus !== "c-msg") errors.push(`VALIDATION: focus is on ${focus}, not the message field`);
  await pp.p.close();

  // JS on, consent unticked: nothing is sent; focus goes to the consent box.
  pp = await page(true, (rq) => rq.respond({ status: 200, contentType: "application/json", body: '{"ok":true}' }));
  await fill(pp.p, "Hello", false);
  await pp.p.click(".cbtn"); await settle();
  const cfocus = await pp.p.evaluate(() => document.activeElement && document.activeElement.id);
  steps.push({ step: "js on: consent unticked", posts: pp.posts.length, focus: cfocus });
  if (pp.posts.length) errors.push("CONSENT: a message was sent without the consent box");
  if (cfocus !== "c-consent") errors.push(`CONSENT: focus is on ${cfocus}, not the consent box`);
  await pp.p.close();

  // JS off: a plain post lands on /contact/sent/.
  pp = await page(false, (rq) => rq.respond({ status: 303, headers: { Location: base + "/contact/sent/" }, body: "" }));
  await fill(pp.p);
  await Promise.all([pp.p.waitForNavigation({ waitUntil: "networkidle0" }), pp.p.click(".cbtn")]);
  const landed = { url: pp.p.url(), h1: await pp.p.$eval("h1", (h) => h.textContent.trim()), method: (pp.posts[0] || {}).method,
                   body: (pp.posts[0] || {}).body.slice(0, 120) };
  steps.push({ step: "js off: plain post", ...landed });
  if (!landed.url.endsWith("/contact/sent/") || !/Message sent/.test(landed.h1)) errors.push(`NOJS: landed on ${landed.url} ("${landed.h1}")`);
  if (landed.method !== "POST" || !/email=ada%40example.org/.test(landed.body) || !/consent=yes/.test(landed.body)) errors.push("NOJS: the browser did not post the form with consent");
  await pp.p.close();

  await browser.close();
  process.stdout.write(JSON.stringify({ errors, steps }));
})().catch((e) => { console.error(e.stack || String(e)); process.exit(2); });
"""


def serve(directory: pathlib.Path, port: int):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    class Server(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True

    httpd = Server(("127.0.0.1", port), lambda *a, **kw: Quiet(*a, directory=str(directory), **kw))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def unit() -> dict:
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="uncost-contact-"))
    try:
        shutil.copy(HANDLER, tmp / "contact.mjs")
        shutil.copy(WORKER, tmp / "worker.mjs")
        (tmp / "run.mjs").write_text(UNIT_JS, encoding="utf-8")
        p = subprocess.run(["node", str(tmp / "run.mjs")], capture_output=True, text=True, timeout=120)
        if p.returncode != 0:
            return {"errors": [f"UNIT: {p.stderr[-600:]}"], "results": []}
        return json.loads(p.stdout)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def browser(built: pathlib.Path, port: int) -> dict:
    if not (built / "contact" / "sent" / "index.html").exists():
        return {"errors": [f"BUILD: {built} has no /contact/sent/ — build with UNCOST_CONTACT_FORM_OPEN=on"], "steps": []}
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="uncost-contact-b-"))
    try:
        js = tmp / "probe.cjs"
        js.write_text(BROWSER_JS, encoding="utf-8")
        httpd = serve(built, port)
        try:
            p = subprocess.run(["node", str(js), str(WEBSITE), f"http://127.0.0.1:{port}"],
                               capture_output=True, text=True, timeout=600)
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
    ap.add_argument("--built", default=None, help="a build made with UNCOST_CONTACT_FORM_OPEN=on")
    ap.add_argument("--port", type=int, default=8961)
    ap.add_argument("--unit-only", action="store_true")
    a = ap.parse_args()
    u = unit()
    out = {"unit_errors": u["errors"], "unit_cases": len(u["results"])}
    errors = list(u["errors"])
    if not a.unit_only:
        if not a.built:
            errors.append("BUILD: pass --built DIR (a switch-on build) or --unit-only")
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

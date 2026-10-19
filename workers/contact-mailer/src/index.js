// uncost-contact-mailer — emails one /contact/ message to the founder inbox.
//
// Called ONLY through the Service binding CONTACT_MAILER on the Pages project
// (website/functions/api/contact.js validates first). It has no public route:
// wrangler.toml turns off workers.dev and preview URLs.
//
// Sends with Cloudflare Email Routing's send_email binding (SEND_EMAIL) to a
// verified destination address — free on every plan, with only Email Routing
// configured. The destination is the secret CONTACT_TO, set in the dashboard
// (or with `wrangler secret put CONTACT_TO`), so no personal address is in this
// public repository. From is an address on the routing domain (Email Routing
// sends only from routing domains); the visitor's address is Reply-To, never
// From. Nothing is stored or logged.

const LIMITS = { name: 200, email: 254, phone: 40, message: 5000 };
const FROM = "contact@uncost.org";

const oneLine = (s) => String(s || "").replace(/[\u0000-\u001f\u007f]+/g, " ").replace(/\s+/g, " ").trim();

export function compose(msg) {
  const name = oneLine(msg.name).slice(0, LIMITS.name);
  const email = oneLine(msg.email).slice(0, LIMITS.email);
  const phone = oneLine(msg.phone).slice(0, LIMITS.phone);
  const message = String(msg.message || "").slice(0, LIMITS.message);
  const who = name || email;
  return {
    subject: `uncost.org contact form: message from ${who}`.slice(0, 250),
    text: [
      "Sent through the contact form on uncost.org. Reply to this email to answer the",
      "sender: Reply-To is the address they gave.",
      "",
      `Name:  ${name || "(not given)"}`,
      `Email: ${email}`,
      `Phone: ${phone || "(not given)"}`,
      "",
      message,
      "",
    ].join("\n"),
    replyTo: email,
  };
}

export default {
  async fetch(request, env) {
    if (request.method !== "POST") return new Response(null, { status: 405 });
    if (!env.SEND_EMAIL || !env.CONTACT_TO) return new Response(null, { status: 503 });
    let msg;
    try {
      msg = await request.json();
    } catch {
      return new Response(null, { status: 400 });
    }
    if (!msg || !oneLine(msg.email) || !String(msg.message || "").trim()) return new Response(null, { status: 400 });
    const mail = compose(msg);
    try {
      await env.SEND_EMAIL.send({ to: env.CONTACT_TO, from: FROM, ...mail });
      return new Response(null, { status: 204 });
    } catch {
      return new Response(null, { status: 502 });
    }
  },
};

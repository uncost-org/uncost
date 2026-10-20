#!/usr/bin/env python3
"""Keyboard and structure pass — key pages at desktop and phone width.

Serves a built site on 127.0.0.1 and drives each page in Chromium through
Playwright with the keyboard only (compliance pass, 2026-10-20). Per page and
width it checks:

  SKIP       the first Tab lands on a visible "skip" link to #main, and after
             Enter the next Tab lands inside <main>;
  FOCUS      Tab through every control until focus wraps: each stop is visible,
             shows an indicator (an outline or a box-shadow), and is not hidden
             under a fixed or sticky element (WCAG 2.4.11);
  ORDER      no positive tabindex, and each Tab moves forward in document order
             (the drawer and overlays are checked on their own);
  DRAWER     (phone width) Enter on the menu button opens the drawer and moves
             focus into it; 30 Tabs and 30 Shift+Tabs never leave it; Escape
             closes it and returns focus to the menu button;
  FORM       (a page with the live contact form) with no mouse: a send with a
             bad email and no message is blocked, focus goes to the first
             invalid field, and it carries a validation message; nothing is
             posted; filled in and with Space on the consent box, the send
             posts once, and the result is written into the role="alert" note;
  STRUCTURE  one visible h1; no heading that skips a level; one <main>, a
             banner and a contentinfo landmark; every <img> has an alt
             attribute; every link and button has an accessible name; no link
             text that means nothing on its own ("click here", "read more",
             "here", "more", "link", "learn more").

Findings are FAIL, or NOTE where a person must look (for example, one link
text used for two destinations). Playwright is not a dependency of website/
(see tools/axe_check.py). Standing rule 4: these are the results to report.

    python3 tools/keyboard_check.py --built DIR --playwright-core DIR [--chromium PATH]

Exit 0 when there is no FAIL, 1 when there is, 2 when the browser could not run.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from axe_check import PAGES, WIDTHS, default_chromium, serve  # noqa: E402

RUNNER = r"""
const { chromium } = require(process.env.PW_CORE);
const base = process.env.BASE;
const pages = JSON.parse(process.env.PAGES);
const widths = JSON.parse(process.env.WIDTHS);
const GENERIC = ["click here", "read more", "here", "more", "link", "learn more", "this", "this page"];

const describe = () => {
  const el = document.activeElement;
  if (!el || el === document.body) return null;
  const r = el.getBoundingClientRect();
  const cs = getComputedStyle(el);
  const outline = cs.outlineStyle !== "none" && parseFloat(cs.outlineWidth) > 0;
  const shadow = cs.boxShadow && cs.boxShadow !== "none";
  // Which fixed or sticky element (if any) covers each of five points: the
  // centre and four points just inside the corners. All five covered is
  // "entirely hidden" (WCAG 2.4.11 fails); some is "partly hidden" (a note).
  const cover = (x, y) => {
    if (x < 0 || y < 0 || x >= innerWidth || y >= innerHeight) return "offscreen";
    const top = document.elementFromPoint(x, y);
    if (!top || top === el || el.contains(top) || top.contains(el)) return null;
    for (let n = top; n; n = n.parentElement) {
      const p = getComputedStyle(n).position;
      if (p === "fixed" || p === "sticky") return n.className ? "." + String(n.className).split(" ")[0] : n.tagName;
    }
    return null;
  };
  const ix = Math.min(4, r.width / 4), iy = Math.min(4, r.height / 4);
  const pts = [[r.left + r.width / 2, r.top + r.height / 2], [r.left + ix, r.top + iy], [r.right - ix, r.top + iy],
               [r.left + ix, r.bottom - iy], [r.right - ix, r.bottom - iy]].map(([x, y]) => cover(x, y));
  const by = pts.filter((c) => c && c !== "offscreen");
  const obscured = by.length && pts.every((c) => c) ? by[0] : null;
  const partly = !obscured && by.length ? by[0] : null;
  const all = [...document.querySelectorAll("*")];
  return {
    idx: all.indexOf(el), tag: el.tagName.toLowerCase(),
    sel: el.tagName.toLowerCase() + (el.id ? "#" + el.id : "") + (el.className && typeof el.className === "string" ? "." + el.className.trim().split(/\s+/).slice(0, 2).join(".") : ""),
    name: (el.getAttribute("aria-label") || el.textContent || el.value || "").trim().replace(/\s+/g, " ").slice(0, 40),
    visible: r.width > 0 && r.height > 0 && cs.visibility !== "hidden" && parseFloat(cs.opacity) > 0,
    inViewport: r.bottom > 0 && r.top < innerHeight && r.right > 0 && r.left < innerWidth,
    indicator: outline || shadow, obscured, partly,
    inMain: !!el.closest("main"), inDrawer: !!el.closest(".drawer"), inOverlay: !!el.closest(".search-ov"),
    href: el.getAttribute("href"),
  };
};

const structure = (GENERIC) => {
  const vis = (el) => { const cs = getComputedStyle(el); const r = el.getBoundingClientRect();
    return cs.display !== "none" && cs.visibility !== "hidden" && (r.width > 0 || r.height > 0) && !el.closest("[hidden],[aria-hidden=true]"); };
  const out = { fail: [], note: [] };
  const h1 = [...document.querySelectorAll("h1")].filter(vis);
  if (h1.length !== 1) out.fail.push(`H1: ${h1.length} visible h1`);
  let prev = 0;
  for (const h of [...document.querySelectorAll("h1,h2,h3,h4,h5,h6")].filter(vis)) {
    const lvl = +h.tagName[1];
    if (prev && lvl > prev + 1) out.fail.push(`HEADING: h${prev} then h${lvl} "${h.textContent.trim().slice(0, 40)}"`);
    prev = lvl;
  }
  const mains = document.querySelectorAll("main");
  if (mains.length !== 1) out.fail.push(`LANDMARK: ${mains.length} <main>`);
  const banner = [...document.querySelectorAll("header")].filter((h) => !h.closest("main,article,section,aside,nav"));
  if (!banner.length) out.fail.push("LANDMARK: no banner (top-level <header>)");
  const info = [...document.querySelectorAll("footer")].filter((f) => !f.closest("main,article,section,aside,nav"));
  if (!info.length) out.fail.push("LANDMARK: no contentinfo (top-level <footer>)");
  for (const n of document.querySelectorAll("nav")) if (document.querySelectorAll("nav").length > 1 && !n.getAttribute("aria-label") && !n.getAttribute("aria-labelledby")) out.fail.push("LANDMARK: an unlabelled <nav> among several");
  for (const img of document.querySelectorAll("img")) if (!img.hasAttribute("alt")) out.fail.push(`ALT: <img src="${(img.getAttribute("src") || "").slice(0, 50)}"> has no alt`);
  const name = (el) => (el.getAttribute("aria-label") || (el.getAttribute("aria-labelledby") && document.getElementById(el.getAttribute("aria-labelledby"))?.textContent) || el.textContent || [...el.querySelectorAll("img[alt]")].map((i) => i.alt).join(" ") || el.title || "").trim().replace(/\s+/g, " ");
  const texts = new Map();
  for (const a of document.querySelectorAll("a[href]")) {
    if (!vis(a) && !a.closest(".drawer,.hd-mega,.search-ov")) continue;
    const n = name(a);
    if (!n) { out.fail.push(`LINK: no accessible name, href=${a.getAttribute("href")}`); continue; }
    if (GENERIC.includes(n.toLowerCase().replace(/[→›»]/g, "").trim())) out.fail.push(`LINK: "${n}" means nothing out of context (href=${a.getAttribute("href")})`);
    const key = n.toLowerCase();
    if (!texts.has(key)) texts.set(key, new Set());
    texts.get(key).add(a.getAttribute("href"));
  }
  for (const [t, hrefs] of texts) if (hrefs.size > 1) out.note.push(`LINK-TEXT: "${t.slice(0, 40)}" goes to ${hrefs.size} places: ${[...hrefs].slice(0, 3).join(" ")}`);
  for (const b of document.querySelectorAll("button")) if (!name(b)) out.fail.push(`BUTTON: no accessible name (${b.className})`);
  for (const t of document.querySelectorAll("[tabindex]")) if (+t.getAttribute("tabindex") > 0) out.fail.push(`ORDER: tabindex=${t.getAttribute("tabindex")} on ${t.tagName}`);
  return out;
};

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM, headless: true });
  const results = [];
  for (const w of widths) {
    const ctx = await browser.newContext({ viewport: { width: w.width, height: w.height }, isMobile: w.mobile, hasTouch: w.mobile });
    const page = await ctx.newPage();
    for (const p of pages) {
      const res = { page: p, width: w.name, fail: [], note: [], stops: 0 };
      const posts = [];
      await page.route("**/api/contact", (route) => { posts.push(route.request().postData() || ""); return route.fulfill({ status: 200, contentType: "application/json", body: process.env.NEXT_REPLY || '{"ok":false}' }); });
      await page.goto(base + p, { waitUntil: "load" });
      await page.evaluate(() => document.fonts.ready);

      // SKIP
      await page.keyboard.press("Tab");
      const first = await page.evaluate(describe);
      if (!first || !/skip/i.test(first.name) || first.href !== "#main") res.fail.push(`SKIP: first Tab is ${first ? first.sel + ' "' + first.name + '"' : "nothing"}`);
      else {
        if (!first.inViewport || !first.visible) res.fail.push("SKIP: the skip link is not visible when focused");
        await page.keyboard.press("Enter");
        await page.keyboard.press("Tab");
        const after = await page.evaluate(describe);
        if (!after || !after.inMain) res.fail.push(`SKIP: after Enter, Tab lands on ${after ? after.sel : "nothing"}, outside <main>`);
      }

      // FOCUS + ORDER: from the top, Tab until focus wraps to the skip link.
      await page.goto(base + p, { waitUntil: "load" });
      let prev = null, budget = 600;
      const seen = new Set();
      while (budget--) {
        await page.keyboard.press("Tab");
        const d = await page.evaluate(describe);
        if (!d) { if (prev) break; else continue; }
        if (prev && d.idx === prev.idx) break;
        if (seen.has(d.idx)) break;
        seen.add(d.idx);
        res.stops++;
        if (!d.visible) res.fail.push(`FOCUS: ${d.sel} "${d.name}" takes focus but is not visible`);
        else if (!d.indicator) res.fail.push(`FOCUS: ${d.sel} "${d.name}" shows no outline or box-shadow`);
        if (d.obscured) res.fail.push(`FOCUS: ${d.sel} "${d.name}" is entirely hidden under ${d.obscured}`);
        else if (d.partly) res.note.push(`FOCUS: ${d.sel} "${d.name}" is partly under ${d.partly}`);
        if (prev && d.idx < prev.idx && !d.inDrawer && !prev.inDrawer && !d.inOverlay && !prev.inOverlay) res.fail.push(`ORDER: ${prev.sel} -> ${d.sel} goes backwards`);
        if (d.inDrawer) res.fail.push(`ORDER: Tab reached the closed drawer (${d.sel})`);
        prev = d;
      }
      if (budget < 0) res.fail.push("FOCUS: focus never wrapped within 600 Tabs");

      // The same walk backwards (Shift+Tab scrolls up, under a sticky header).
      await page.goto(base + p, { waitUntil: "load" });
      const back = new Set();
      for (let i = 0; i < 600; i++) {
        await page.keyboard.press("Shift+Tab");
        const d = await page.evaluate(describe);
        if (!d) { if (back.size) break; else continue; }
        if (back.has(d.idx)) break;
        back.add(d.idx);
        if (d.obscured) res.fail.push(`FOCUS (Shift+Tab): ${d.sel} "${d.name}" is entirely hidden under ${d.obscured}`);
      }

      // MEGA (desktop): a panel opened by focus closes on Escape, focus stays
      // on its menu item, and Tab out of the header leaves no panel open.
      if (!w.mobile) {
        await page.goto(base + p, { waitUntil: "load" });
        const item = await page.$(".hd-item > a");
        if (item) {
          await item.focus();
          const opened = await page.evaluate(() => !!document.querySelector(".hd-mega.open"));
          await page.keyboard.press("Escape");
          const after = await page.evaluate(() => ({ open: !!document.querySelector(".hd-mega.open"), onItem: !!document.activeElement.closest(".hd-item") }));
          if (opened && (after.open || !after.onItem)) res.fail.push(`MEGA: Escape leaves the panel ${after.open ? "open" : "closed but focus off its item"}`);
          let stillOpen = false;
          for (let i = 0; i < 80; i++) {
            await page.keyboard.press("Tab");
            const st = await page.evaluate(() => ({ inHd: !!document.activeElement.closest(".hd"), open: !!document.querySelector(".hd-mega.open") }));
            if (!st.inHd) { stillOpen = st.open; break; }
          }
          if (stillOpen) res.fail.push("MEGA: a panel stays open after Tab leaves the header");
        }
      }

      // DRAWER (phone width)
      if (w.mobile) {
        await page.goto(base + p, { waitUntil: "load" });
        await page.focus("[data-drawer-open]");
        await page.keyboard.press("Enter");
        await page.waitForTimeout(150);
        const inside = async () => page.evaluate(() => !!document.activeElement.closest(".drawer"));
        if (!(await inside())) res.fail.push("DRAWER: opening it does not move focus inside");
        let escaped = 0;
        for (let i = 0; i < 30; i++) { await page.keyboard.press("Tab"); if (!(await inside())) escaped++; }
        for (let i = 0; i < 30; i++) { await page.keyboard.press("Shift+Tab"); if (!(await inside())) escaped++; }
        if (escaped) res.fail.push(`DRAWER: focus left the open drawer ${escaped} times in 60 Tabs`);
        await page.keyboard.press("Escape");
        await page.waitForTimeout(150);
        const back = await page.evaluate(() => ({ open: document.querySelector(".drawer").classList.contains("open"), onButton: document.activeElement.matches("[data-drawer-open]") }));
        if (back.open) res.fail.push("DRAWER: Escape does not close it");
        if (!back.onButton) res.fail.push("DRAWER: closing does not return focus to the menu button");
      }

      // FORM (the live contact form only)
      const live = await page.$('form[data-form="contact"][data-live]');
      if (live) {
        await page.goto(base + p, { waitUntil: "load" });
        const tabTo = async (id) => { for (let i = 0; i < 200; i++) { await page.keyboard.press("Tab"); if (await page.evaluate((x) => document.activeElement.id === x, id)) return true; } return false; };
        // Each field must be reached by a few Tabs from the one before, in
        // order (the "Privacy" link between message and consent is a stop).
        const order = [];
        const step = async (want) => { for (let i = 0; i < 4; i++) { await page.keyboard.press("Tab");
          const d = await page.evaluate(() => ({ id: document.activeElement.id, type: document.activeElement.type, sel: document.activeElement.tagName.toLowerCase() + (document.activeElement.className ? "." + document.activeElement.className : "") }));
          order.push(d.id || d.sel); if (want(d)) return true; } return false; };
        if (!(await tabTo("c-name"))) res.fail.push("FORM: Tab never reaches the name field");
        await page.keyboard.type("Test");
        const okOrder = (await step((d) => d.id === "c-email")) && (await page.keyboard.type("not-an-email"), true)
          && (await step((d) => d.id === "c-msg")) && (await step((d) => d.id === "c-consent")) && (await step((d) => d.type === "submit"));
        if (!okOrder) res.fail.push(`FORM: Tab order from the name field is ${order.join(" > ")}`);
        else res.note.push(`FORM: Tab order c-name > ${order.join(" > ")}`);
        await page.keyboard.press("Enter");
        await page.waitForTimeout(200);
        const inv = await page.evaluate(() => ({ id: document.activeElement.id, msg: document.activeElement.validationMessage || "" }));
        if (inv.id !== "c-email" || !inv.msg) res.fail.push(`FORM: a blocked send leaves focus on #${inv.id} (message: "${inv.msg}")`);
        if (posts.length) res.fail.push("FORM: an invalid form was posted");
        await page.fill("#c-email", "");
        await page.keyboard.type("someone@example.org");
        await step((d) => d.id === "c-msg"); await page.keyboard.type("A keyboard-only test message.");
        await step((d) => d.id === "c-consent"); await page.keyboard.press("Space");
        await step((d) => d.type === "submit"); await page.keyboard.press("Enter");
        await page.waitForTimeout(800);
        const note = await page.evaluate(() => { const n = document.querySelector(".cnote"); return { role: n && n.getAttribute("role"), text: n ? n.textContent.trim() : "" }; });
        if (posts.length !== 1) res.fail.push(`FORM: a valid send posted ${posts.length} times, not once`);
        if (note.role !== "alert" || !note.text) res.fail.push(`FORM: the result is not written into a role="alert" note (role=${note.role}, text="${note.text.slice(0, 40)}")`);
        else res.note.push(`FORM: keyboard-only send announced: "${note.text.slice(0, 60)}"`);
      }

      // STRUCTURE
      await page.goto(base + p, { waitUntil: "load" });
      const st = await page.evaluate(structure, GENERIC);
      res.fail.push(...st.fail); res.note.push(...st.note);
      await page.unroute("**/api/contact");
      results.push(res);
    }
    await ctx.close();
  }
  await browser.close();
  process.stdout.write(JSON.stringify(results));
})().catch((e) => { process.stderr.write(String(e && e.stack || e)); process.exit(2); });
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--built", default=str(pathlib.Path(__file__).resolve().parents[1] / "website" / "dist"))
    ap.add_argument("--playwright-core", required=True)
    ap.add_argument("--chromium")
    ap.add_argument("--pages", nargs="+", default=PAGES)
    a = ap.parse_args()
    built = pathlib.Path(a.built).resolve()
    pw = pathlib.Path(a.playwright_core).resolve()
    chromium = pathlib.Path(a.chromium) if a.chromium else default_chromium()
    if not (built / "index.html").exists() or not (pw / "package.json").exists() or not chromium:
        print(json.dumps({"ok": False, "errors": ["needs a built site, --playwright-core DIR and a Chromium"]}, indent=1))
        return 2
    httpd = serve(built)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            runner = pathlib.Path(tmp) / "keyboard-runner.cjs"
            runner.write_text(RUNNER, encoding="utf-8")
            env = {**os.environ, "PW_CORE": str(pw), "CHROMIUM": str(chromium),
                   "BASE": f"http://127.0.0.1:{httpd.server_address[1]}",
                   "PAGES": json.dumps(a.pages), "WIDTHS": json.dumps(WIDTHS)}
            proc = subprocess.run(["node", str(runner)], env=env, capture_output=True, text=True, timeout=1200)
    finally:
        httpd.shutdown()
    if proc.returncode != 0:
        print(json.dumps({"ok": False, "errors": [proc.stderr.strip()[-2000:]]}, indent=1))
        return 2
    runs = json.loads(proc.stdout)
    fails = [f"{r['page']} @{r['width']}: {f}" for r in runs for f in r["fail"]]
    notes = sorted({f"{r['page']}: {n}" for r in runs for n in r["note"]})
    print(json.dumps({"ok": not fails, "runs": len(runs),
                      "tab_stops": {f"{r['page']} @{r['width']}": r["stops"] for r in runs},
                      "fail": fails, "note": notes}, indent=1))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())

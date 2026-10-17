#!/usr/bin/env python3
"""Drawer check — the mobile menu, driven from the keyboard only.

The mobile menu (partials/nav-drawer.njk, ui.js) is an accordion: one section
open at a time. Since the 2026-10-17 mobile fixes each section opens straight
onto its links, the first of which is the section's own landing page — the
export's separate "Overview" link is gone. This check proves, in a real
browser at phone width, with no mouse:

  1. Tab reaches the menu button, and Enter opens the drawer;
  2. for every section in order (chrome.json nav): Tab reaches its button,
     Enter (or Space, alternately) opens it, and afterwards EXACTLY one section
     is open — that one — with aria-expanded true on its button and false on
     every other;
  3. the next Tab lands on that section's first link, which is visible and
     points at the section's own url (its landing page);
  4. pressing the open section's button again closes it (none open);
  5. no drawer link reads "Overview".

STANDING RULE (docs/DESIGN_IMPORT_RUNBOOK.md): it fails on "I don't know" —
a page that will not load, a control focus never reaches within the Tab
budget, or a drawer with no sections is an ERROR, never a skipped line.

    python3 tools/drawer_check.py                 # website/dist, route /
    python3 tools/drawer_check.py --built DIR --route /about/
    python3 tools/drawer_check.py --selftest      # adversarial fixtures

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
DIST = WEBSITE / "dist"
CHROME = WEBSITE / "src" / "_data" / "chrome.json"

PROBE_JS = r"""
const puppeteer = require(require.resolve("puppeteer", { paths: [process.argv[2]] }));
const url = process.argv[3];
const expected = JSON.parse(process.argv[4]);   // [{label, url}] in drawer order
const TAB_BUDGET = 200;

(async () => {
  const browser = await puppeteer.launch({ args: ["--no-sandbox"] });
  const page = await browser.newPage();
  await page.setCacheEnabled(false);
  await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 1 });
  const errors = [];
  const steps = [];
  const res = await page.goto(url, { waitUntil: "networkidle0", timeout: 60000 }).catch((e) => null);
  if (!res || !res.ok()) { process.stdout.write(JSON.stringify({ errors: ["LOAD " + url], steps })); await browser.close(); return; }

  const tabTo = async (pred, arg) => {
    for (let i = 0; i < TAB_BUDGET; i++) {
      await page.keyboard.press("Tab");
      if (await page.evaluate(pred, arg)) return i + 1;
    }
    return 0;
  };
  const state = () => page.evaluate(() => {
    const accs = [...document.querySelectorAll(".drawer .drawer-acc")];
    return {
      drawerOpen: !!document.querySelector(".drawer.open"),
      open: accs.map((a, i) => (a.classList.contains("open") ? i : -1)).filter((i) => i >= 0),
      expanded: accs.map((a) => a.querySelector("[data-acc]").getAttribute("aria-expanded")),
      sections: accs.length,
      overview: [...document.querySelectorAll(".drawer .drawer-acc a")].filter((a) => /^\s*overview\b/i.test(a.textContent)).length,
    };
  });

  // 1. open the drawer from the keyboard
  const toMenu = await tabTo(() => document.activeElement && document.activeElement.matches("[data-drawer-open]"));
  if (!toMenu) errors.push("FOCUS: Tab never reached the menu button [data-drawer-open]");
  else {
    await page.keyboard.press("Enter");
    await new Promise((r) => setTimeout(r, 200));
    const s = await state();
    steps.push({ step: "open drawer", tabs: toMenu, drawerOpen: s.drawerOpen, sections: s.sections });
    if (!s.drawerOpen) errors.push("OPEN: Enter on the menu button did not open the drawer");
    if (s.sections === 0) errors.push("SECTIONS: the drawer has no sections");
    if (s.sections !== expected.length) errors.push(`SECTIONS: drawer has ${s.sections}, chrome.json nav has ${expected.length}`);
    if (s.overview) errors.push(`OVERVIEW: ${s.overview} drawer link(s) still read "Overview"`);

    // 2-3. every section in order
    for (let i = 0; i < s.sections; i++) {
      const tabs = await tabTo((i) => {
        const btns = [...document.querySelectorAll(".drawer .drawer-acc [data-acc]")];
        return document.activeElement === btns[i];
      }, i);
      if (!tabs) { errors.push(`FOCUS: Tab never reached section ${i + 1}'s button`); break; }
      const key = i % 2 ? "Space" : "Enter";
      await page.keyboard.press(key);
      await new Promise((r) => setTimeout(r, 150));
      const t = await state();
      steps.push({ step: `section ${i + 1} via ${key}`, tabs, open: t.open, expanded: t.expanded });
      if (t.open.length !== 1 || t.open[0] !== i) {
        errors.push(`ONE-OPEN: after opening section ${i + 1}, open sections are [${t.open.map((x) => x + 1)}]`);
      }
      t.expanded.forEach((v, j) => {
        if ((j === i) !== (v === "true")) errors.push(`ARIA: section ${j + 1} aria-expanded="${v}" after opening section ${i + 1}`);
      });
      await page.keyboard.press("Tab");
      const link = await page.evaluate((i) => {
        const a = document.activeElement;
        const sec = [...document.querySelectorAll(".drawer .drawer-acc")][i];
        const r = a && a.getBoundingClientRect();
        return { isLink: !!a && a.tagName === "A", inSection: !!a && sec.contains(a),
                 href: a && a.getAttribute("href"), text: a && a.textContent.trim(),
                 visible: !!r && r.width > 0 && r.height > 0 };
      }, i);
      steps.push({ step: `section ${i + 1} first link`, ...link });
      const want = expected[i] && expected[i].url;
      if (!link.isLink || !link.inSection) errors.push(`FOCUS: the Tab after opening section ${i + 1} did not land on a link inside it`);
      else {
        if (link.href !== want) errors.push(`LANDING: section ${i + 1}'s first link is ${link.href}, not its own url ${want}`);
        if (!link.visible) errors.push(`VISIBLE: section ${i + 1}'s first link has focus but no rendered box`);
      }
    }
    // 4. the last open section closes when its button is pressed again
    const last = s.sections - 1;
    if (last >= 0) {
      await page.evaluate((i) => [...document.querySelectorAll(".drawer .drawer-acc [data-acc]")][i].focus(), last);
      await page.keyboard.press("Enter");
      await new Promise((r) => setTimeout(r, 150));
      const u = await state();
      steps.push({ step: "close the open section", open: u.open });
      if (u.open.length) errors.push(`TOGGLE: pressing the open section's button left [${u.open.map((x) => x + 1)}] open`);
    }
  }
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

        def handle_error(self, request, client_address):
            pass

    httpd = Server(("127.0.0.1", port), lambda *a, **kw: Quiet(*a, directory=str(directory), **kw))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def run(built: pathlib.Path, route: str, expected, port: int):
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="uncost-drawer-"))
    try:
        js = tmp / "probe.cjs"
        js.write_text(PROBE_JS, encoding="utf-8")
        httpd = serve(built, port)
        try:
            proc = subprocess.run(["node", str(js), str(WEBSITE), f"http://127.0.0.1:{port}{route}",
                                   json.dumps(expected)], capture_output=True, text=True, timeout=600)
        finally:
            httpd.shutdown()
            httpd.server_close()
        if proc.returncode != 0:
            return {"errors": [f"PROBE: {proc.stderr[-800:]}"], "steps": []}
        return json.loads(proc.stdout)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def expected_from_chrome():
    nav = json.loads(CHROME.read_text(encoding="utf-8"))["nav"]
    return [{"label": n["label"], "url": n["url"]} for n in nav]


FIXTURE = """<!doctype html><html><head><meta charset=utf-8><style>
.drawer{display:none}.drawer.open{display:block}.in{display:none}.drawer-acc.open .in{display:block}
</style></head><body><button data-drawer-open>Menu</button>
<div class="drawer">%s</div>
<script>
var d=document.querySelector('.drawer');
document.querySelector('[data-drawer-open]').onclick=function(){d.classList.add('open')};
d.querySelectorAll('[data-acc]').forEach(function(b){b.addEventListener('click',function(){
  var acc=b.parentElement, was=acc.classList.contains('open');
  %s
  if(!was){acc.classList.add('open');b.setAttribute('aria-expanded','true')}
  else{acc.classList.remove('open');b.setAttribute('aria-expanded','false')}
})});
</script></body></html>"""
CLOSE_OTHERS = ("d.querySelectorAll('.drawer-acc').forEach(function(a){if(a!==acc){a.classList.remove('open');"
                "a.querySelector('[data-acc]').setAttribute('aria-expanded','false')}});")


def section(label, links):
    a = "".join(f'<a href="{u}">{t}</a>' for u, t in links)
    return (f'<div class="drawer-acc"><button type="button" data-acc aria-expanded="false">{label}</button>'
            f'<div class="in"><div class="dd-desc">desc</div>{a}</div></div>')


def selftest(port: int) -> int:
    exp = [{"label": "One", "url": "/one/"}, {"label": "Two", "url": "/two/"}]
    good = section("One", [("/one/", "One home"), ("/x/", "X")]) + section("Two", [("/two/", "Two home")])
    cases = {
        "good.html": (FIXTURE % (good, CLOSE_OTHERS), set()),
        # Opening a second section leaves the first open, so closing the last
        # one still leaves a section open: three kinds, all real.
        "two-open.html": (FIXTURE % (good, ""), {"ONE-OPEN", "ARIA", "TOGGLE"}),
        "wrong-first.html": (FIXTURE % (section("One", [("/x/", "X"), ("/one/", "One home")]) +
                                        section("Two", [("/two/", "Two home")]), CLOSE_OTHERS), {"LANDING"}),
        "overview.html": (FIXTURE % (section("One", [("/one/", "Overview"), ("/one/", "One home")]) +
                                     section("Two", [("/two/", "Two home")]), CLOSE_OTHERS), {"OVERVIEW"}),
    }
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="uncost-drawer-st-"))
    failures = []
    try:
        for name, (html, want) in cases.items():
            (tmp / name).write_text(html, encoding="utf-8")
        for name, (_html, want) in cases.items():
            got = run(tmp, "/" + name, exp, port)
            kinds = {e.split(":")[0] for e in got["errors"]}
            if kinds != want:
                failures.append({"fixture": name, "expected": sorted(want), "got": sorted(kinds), "errors": got["errors"][:4]})
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(json.dumps({"ok": not failures, "selftest_cases": len(cases), "failures": failures}, indent=2))
    return 0 if not failures else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--built", default=str(DIST))
    ap.add_argument("--route", default="/")
    ap.add_argument("--port", type=int, default=8951)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest(a.port)
    expected = expected_from_chrome()
    got = run(pathlib.Path(a.built), a.route, expected, a.port)
    print(json.dumps({"ok": not got["errors"], "route": a.route, "sections_expected": len(expected),
                      "errors": got["errors"], "steps": got["steps"]}, indent=1))
    return 0 if not got["errors"] else 1


if __name__ == "__main__":
    sys.exit(main())

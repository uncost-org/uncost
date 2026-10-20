#!/usr/bin/env python3
"""Cookie and browser-storage check — the evidence behind /privacy/'s
"no cookies, nothing stored in your browser" (CHG-006).

Two halves, either or both:

  --built DIR   every .js file in a build, searched for the browser storage
                APIs: document.cookie, localStorage, sessionStorage,
                indexedDB, the Cache API (caches.) and service workers.
  --site URL    the pages below opened in Chromium through Playwright (a
                fresh profile; every script the page loads runs, including
                anything the host injects at the edge), then: every
                Set-Cookie response header on any request, the cookies the
                browser holds, and localStorage, sessionStorage and IndexedDB
                for every origin a frame was loaded from. Also each
                third-party script the pages loaded, searched for the same
                APIs.

    python3 tools/storage_check.py --built website/dist
    python3 tools/storage_check.py --site https://uncost.org \\
        --playwright-core DIR [--chromium PATH]

Playwright is not a dependency of website/ (see tools/axe_check.py). Standing
rule 4: these are the results to report.

Exit 0 when nothing is set or stored, 1 when something is, 2 when the
browser could not run.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from axe_check import default_chromium  # noqa: E402

PAGES = ["/", "/case/", "/sectors/", "/sectors/food/", "/receipts/", "/contact/", "/privacy/", "/search/"]
API_RE = re.compile(r"document\.cookie|localStorage|sessionStorage|indexedDB|\bcaches\.|serviceWorker|openDatabase")

RUNNER = r"""
const { chromium } = require(process.env.PW_CORE);
const base = process.env.BASE;
const pages = JSON.parse(process.env.PAGES);
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM, headless: true });
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  const setCookies = [], scripts = new Map(), origins = new Set();
  page.on("response", async (r) => {
    const h = await r.allHeaders().catch(() => ({}));
    if (h["set-cookie"]) setCookies.push({ url: r.url(), value: h["set-cookie"].split("=")[0] + "=…" });
    if (r.request().resourceType() === "script" && !scripts.has(r.url())) {
      scripts.set(r.url(), await r.text().catch(() => ""));
    }
  });
  const storage = [];
  for (const p of pages) {
    const resp = await page.goto(base + p, { waitUntil: "networkidle" });
    await page.waitForTimeout(1500);
    for (const f of page.frames()) {
      try { origins.add(new URL(f.url()).origin); } catch {}
    }
    const s = await page.evaluate(async () => ({
      local: Object.keys(localStorage), session: Object.keys(sessionStorage),
      idb: indexedDB.databases ? (await indexedDB.databases()).map((d) => d.name) : [],
      cookie: document.cookie,
    }));
    storage.push({ page: p, status: resp ? resp.status() : null, ...s });
  }
  const cookies = (await ctx.cookies()).map((c) => ({ name: c.name, domain: c.domain }));
  const state = await ctx.storageState();
  await browser.close();
  process.stdout.write(JSON.stringify({
    browser: browser.version ? undefined : undefined, setCookies, cookies,
    storageStateOrigins: state.origins.map((o) => ({ origin: o.origin, localStorage: o.localStorage.map((x) => x.name) })),
    storage, frameOrigins: [...origins],
    scripts: [...scripts].map(([url, text]) => ({ url, bytes: text.length, apis: [...new Set(text.match(new RegExp(process.env.API_RE, "g")) || [])] })),
  }));
})().catch((e) => { process.stderr.write(String(e && e.stack || e)); process.exit(2); });
"""


def scan_built(built: pathlib.Path) -> dict:
    hits = []
    files = sorted(built.rglob("*.js"))
    for f in files:
        for n, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            for m in API_RE.finditer(line):
                hits.append(f"{f.relative_to(built)}:{n} {m.group(0)}")
    return {"js_files": len(files), "storage_api_uses": hits}


def scan_site(base: str, pw: pathlib.Path, chromium: pathlib.Path, pages: list) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        runner = pathlib.Path(tmp) / "storage-runner.cjs"
        runner.write_text(RUNNER, encoding="utf-8")
        env = {**os.environ, "PW_CORE": str(pw), "CHROMIUM": str(chromium), "BASE": base.rstrip("/"),
               "PAGES": json.dumps(pages), "API_RE": API_RE.pattern}
        proc = subprocess.run(["node", str(runner)], env=env, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip()[-2000:])
    return json.loads(proc.stdout)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--built")
    ap.add_argument("--site")
    ap.add_argument("--playwright-core")
    ap.add_argument("--chromium")
    ap.add_argument("--pages", nargs="+", default=PAGES)
    a = ap.parse_args()
    if not a.built and not a.site:
        ap.error("give --built DIR and/or --site URL")
    result, problems = {}, []

    if a.built:
        b = scan_built(pathlib.Path(a.built))
        result["built"] = b
        problems += [f"BUILT: {h}" for h in b["storage_api_uses"]]

    if a.site:
        chromium = pathlib.Path(a.chromium) if a.chromium else default_chromium()
        if not a.playwright_core or not (pathlib.Path(a.playwright_core) / "package.json").exists() or not chromium:
            print(json.dumps({"ok": False, "errors": ["--site needs --playwright-core DIR and a Chromium"]}, indent=1))
            return 2
        try:
            s = scan_site(a.site, pathlib.Path(a.playwright_core).resolve(), chromium, a.pages)
        except RuntimeError as e:
            print(json.dumps({"ok": False, "errors": [str(e)]}, indent=1))
            return 2
        s.pop("browser", None)
        result["site"] = s
        problems += [f"SET-COOKIE: {c['url']} {c['value']}" for c in s["setCookies"]]
        problems += [f"COOKIE: {c['name']} on {c['domain']}" for c in s["cookies"]]
        for row in s["storage"]:
            if row["status"] != 200:
                problems.append(f"PAGE: {row['page']} HTTP {row['status']}")
            for kind in ("local", "session", "idb"):
                problems += [f"{kind.upper()}: {row['page']} {k}" for k in row[kind]]
            if row["cookie"]:
                problems.append(f"DOCUMENT.COOKIE: {row['page']}")
        for o in s["storageStateOrigins"]:
            problems += [f"LOCALSTORAGE: {o['origin']} {k}" for k in o["localStorage"]]
        problems += [f"SCRIPT-API: {sc['url']} uses {', '.join(sc['apis'])}" for sc in s["scripts"] if sc["apis"]]

    result = {"ok": not problems, "problems": problems, **result}
    print(json.dumps(result, indent=1))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())

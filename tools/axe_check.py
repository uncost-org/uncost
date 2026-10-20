#!/usr/bin/env python3
"""axe-core accessibility pass — key pages at desktop and phone width.

Serves a built site on 127.0.0.1, opens each page in Chromium through
Playwright and runs axe-core (website/node_modules/axe-core, which pa11y
brings in) with its default rule set: WCAG 2.x A and AA plus axe's
best-practice rules. Violations are reported by impact (critical, serious,
moderate, minor), each with its rule, the pages and widths it occurs on, and
up to five element selectors. Standing rule 4: these are the results to report.

Playwright is not a dependency of website/: the runner needs a playwright-core
package and a Chromium that Playwright installed, and fails (never skips)
without them.

    python3 tools/axe_check.py --built website/dist --playwright-core DIR
    python3 tools/axe_check.py ... --chromium PATH      # else the newest
        # chromium-* under PLAYWRIGHT_BROWSERS_PATH or Playwright's default
        # cache (~/Library/Caches/ms-playwright, ~/.cache/ms-playwright)
    python3 tools/axe_check.py ... --pages / /contact/  # else PAGES below

Note: the local server does not apply website/src/_headers, so the page runs
without its CSP; axe is injected as page script.

Exit 0 when no violations, 1 when there are any, 2 when the browser could not run.
"""
from __future__ import annotations

import argparse
import http.server
import json
import os
import pathlib
import socketserver
import subprocess
import sys
import tempfile
import threading

ROOT = pathlib.Path(__file__).resolve().parents[1]
AXE_JS = ROOT / "website" / "node_modules" / "axe-core" / "axe.min.js"
PAGES = ["/", "/case/", "/sectors/", "/sectors/food/", "/receipts/", "/contact/", "/privacy/"]
WIDTHS = [
    {"name": "desktop", "width": 1440, "height": 900, "mobile": False},
    {"name": "phone", "width": 390, "height": 844, "mobile": True},
]
IMPACTS = ["critical", "serious", "moderate", "minor"]

RUNNER = r"""
const { chromium } = require(process.env.PW_CORE);
const fs = require("fs");
const axeSource = fs.readFileSync(process.env.AXE_JS, "utf8");
const base = process.env.BASE;
const pages = JSON.parse(process.env.PAGES);
const widths = JSON.parse(process.env.WIDTHS);
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM, headless: true });
  const out = { axe: null, browser: browser.version(), runs: [] };
  try {
    for (const w of widths) {
      const ctx = await browser.newContext({
        viewport: { width: w.width, height: w.height }, isMobile: w.mobile, hasTouch: w.mobile,
      });
      const page = await ctx.newPage();
      for (const p of pages) {
        const resp = await page.goto(base + p, { waitUntil: "load" });
        await page.evaluate(() => document.fonts.ready);
        await page.evaluate(axeSource);
        const r = await page.evaluate(() => axe.run(document, { resultTypes: ["violations"] }));
        out.axe = r.testEngine.version;
        out.runs.push({
          page: p, width: w.name, status: resp ? resp.status() : null,
          violations: r.violations.map((v) => ({
            id: v.id, impact: v.impact, help: v.help, helpUrl: v.helpUrl,
            tags: v.tags.filter((t) => /^wcag|^best-practice$/.test(t)),
            nodes: v.nodes.map((n) => ({ target: n.target.join(" "), summary: n.failureSummary })),
          })),
        });
      }
      await ctx.close();
    }
  } finally {
    await browser.close();
  }
  process.stdout.write(JSON.stringify(out));
})().catch((e) => { process.stderr.write(String(e && e.stack || e)); process.exit(2); });
"""


def default_chromium() -> pathlib.Path | None:
    roots = [os.environ.get("PLAYWRIGHT_BROWSERS_PATH"),
             str(pathlib.Path.home() / "Library" / "Caches" / "ms-playwright"),
             str(pathlib.Path.home() / ".cache" / "ms-playwright")]
    for root in filter(None, roots):
        found = []
        for d in pathlib.Path(root).glob("chromium-*"):
            for exe in (list(d.glob("chrome-mac*/*.app/Contents/MacOS/*"))
                        + list(d.glob("chrome-linux*/chrome"))):
                found.append((int(d.name.split("-")[1]) if d.name.split("-")[1].isdigit() else 0, exe))
        if found:
            return max(found)[1]
    return None


def serve(directory: pathlib.Path):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    class Server(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True

    httpd = Server(("127.0.0.1", 0), lambda *a, **kw: Quiet(*a, directory=str(directory), **kw))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def summarise(runs: list) -> dict:
    by_impact: dict = {i: {} for i in IMPACTS}
    for run in runs:
        for v in run["violations"]:
            rule = by_impact.setdefault(v["impact"] or "unknown", {}).setdefault(v["id"], {
                "help": v["help"], "tags": v["tags"], "helpUrl": v["helpUrl"], "where": [], "targets": []})
            rule["where"].append(f'{run["page"]} @{run["width"]} ({len(v["nodes"])})')
            for n in v["nodes"]:
                if n["target"] not in rule["targets"] and len(rule["targets"]) < 5:
                    rule["targets"].append(n["target"])
    counts = {i: sum(len(r["where"]) for r in rules.values()) for i, rules in by_impact.items()}
    return {"counts_page_width_rule": counts, "by_impact": by_impact}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--built", default=str(ROOT / "website" / "dist"))
    ap.add_argument("--playwright-core", required=True, help="the playwright-core package directory")
    ap.add_argument("--chromium", help="a Chromium executable (default: Playwright's newest installed)")
    ap.add_argument("--pages", nargs="+", default=PAGES)
    a = ap.parse_args()

    built = pathlib.Path(a.built).resolve()
    pw = pathlib.Path(a.playwright_core).resolve()
    chromium = pathlib.Path(a.chromium) if a.chromium else default_chromium()
    problems = [msg for ok, msg in [
        ((built / "index.html").exists(), f"no built site at {a.built}"),
        ((pw / "package.json").exists(), f"no playwright-core package at {a.playwright_core}"),
        (chromium is not None and chromium.exists(), "no Playwright-installed Chromium found (use --chromium)"),
        (AXE_JS.exists(), "axe-core is not installed in website/node_modules (npm ci)"),
    ] if not ok]
    if problems:
        print(json.dumps({"ok": False, "errors": problems}, indent=1))
        return 2

    httpd = serve(built)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            runner = pathlib.Path(tmp) / "axe-runner.cjs"
            runner.write_text(RUNNER, encoding="utf-8")
            env = {**os.environ, "PW_CORE": str(pw), "AXE_JS": str(AXE_JS), "CHROMIUM": str(chromium),
                   "BASE": f"http://127.0.0.1:{httpd.server_address[1]}",
                   "PAGES": json.dumps(a.pages), "WIDTHS": json.dumps(WIDTHS)}
            proc = subprocess.run(["node", str(runner)], env=env, capture_output=True, text=True, timeout=600)
    finally:
        httpd.shutdown()
    if proc.returncode != 0:
        print(json.dumps({"ok": False, "errors": [proc.stderr.strip()[-2000:]]}, indent=1))
        return 2

    data = json.loads(proc.stdout)
    bad_status = [f'{r["page"]} @{r["width"]}: HTTP {r["status"]}' for r in data["runs"] if r["status"] != 200]
    summary = summarise(data["runs"])
    total = sum(summary["counts_page_width_rule"].values())
    result = {"ok": total == 0 and not bad_status, "axe": data["axe"], "browser": data["browser"],
              "pages": a.pages, "widths": [w["name"] for w in WIDTHS], "runs": len(data["runs"]),
              "errors": bad_status, **summary}
    print(json.dumps(result, indent=1))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

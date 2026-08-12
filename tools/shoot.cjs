#!/usr/bin/env node
/* Screenshot a list of routes at given widths. Used by tools/render_diff.py.
   Usage: node tools/shoot.cjs <baseUrl> <outDir> <widths csv> <route...>  */
// puppeteer comes in with pa11y under website/node_modules; resolved from
// there so this tool adds no dependency of its own.
const path = require("node:path");
const puppeteer = require(require.resolve("puppeteer", {
  paths: [path.join(__dirname, "..", "website")],
}));
const fs = require("node:fs");

(async () => {
  const [baseUrl, outDir, widthsCsv, ...routes] = process.argv.slice(2);
  const widths = widthsCsv.split(",").map(Number);
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await puppeteer.launch({ args: ["--no-sandbox", "--force-device-scale-factor=1"] });
  const page = await browser.newPage();
  // Freeze anything time-based so two runs are comparable.
  await page.emulateMediaFeatures([{ name: "prefers-reduced-motion", value: "reduce" }]);
  for (const route of routes) {
    for (const w of widths) {
      await page.setViewport({ width: w, height: 1000, deviceScaleFactor: 1 });
      const url = baseUrl + route;
      const res = await page.goto(url, { waitUntil: "networkidle0", timeout: 60000 });
      if (!res || !res.ok()) { console.error(`MISS ${url} ${res && res.status()}`); continue; }
      await page.evaluate(() => document.fonts && document.fonts.ready);
      const name = route.replace(/^\//, "").replace(/\/$/, "").replace(/[\/.]/g, "_") || "index";
      const file = path.join(outDir, `${name}@${w}.png`);
      await page.screenshot({ path: file, fullPage: true });
      console.log(`shot ${file}`);
    }
  }
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });

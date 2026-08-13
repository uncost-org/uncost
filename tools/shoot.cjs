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

// Regions permitted to differ, masked in BOTH renders before the pixel compare.
// These are the documented WCAG 2.2 AA corrections applied on adoption: the
// export puts white on brand coral (4.32:1) and coral on cream (4.04:1), which
// fail AA, so this build darkens the text. Recorded in design-system/AUTHORITY.md
// and approved by the founder as an intentional divergence from the export.
const ALLOWLIST = [
  ".hd .cta-btn",          // header CTA: white -> near-black on coral
  ".pledgebar a",          // sticky mobile CTA, same coral fill
  ".hd-mega .mg-num",      // coral -> coral-deep, small text on cream-2
  ".hd-mega .mg-go a .ar",
  ".drawer-acc > button .pm",
  ".drawer-acc .in a .ar",
];

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
      // Section boxes let the gate compare each band against its own origin, so
      // one content-driven height change does not cascade into every section
      // below it. Allowlist boxes are masked before diffing.
      const meta = await page.evaluate((allow) => {
        const box = (el) => { const r = el.getBoundingClientRect();
          return [Math.round(r.x), Math.round(r.y + window.scrollY), Math.round(r.width), Math.round(r.height)]; };
        const main = document.querySelector("main");
        return {
          // Label each section so the gate can match by identity rather than by
          // index: a page that legitimately omits an optional section (a sector
          // with no related projects) should not read as a layout break.
          sections: main ? [...main.children].map((el) => ({
            label: el.getAttribute("data-screen-label")
              || el.id
              || (el.tagName.toLowerCase() + "." + (el.className || "").toString().trim().split(/\s+/).join(".")),
            box: box(el),
          })) : [],
          masks: allow.flatMap((s) => [...document.querySelectorAll(s)].map(box)),
        };
      }, ALLOWLIST);
      fs.writeFileSync(file.replace(/\.png$/, ".json"), JSON.stringify(meta));
      console.log(`shot ${file}`);
    }
  }
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });

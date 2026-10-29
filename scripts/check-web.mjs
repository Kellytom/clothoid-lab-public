// Layout gate for the docs pages and the local app.
// Uses playwright-core with the installed Chrome: no browser download.
//
//   node scripts/check-web.mjs [--shots <dir>]
//
// Fails (exit 1) on horizontal overflow at any viewport, or if the app is down.

import { chromium } from "playwright-core";
import fs from "node:fs";
import path from "node:path";

const DOCS = "http://127.0.0.1:8002";
const APP = "http://127.0.0.1:8000";
const PAGES = ["cloud.html", "gallery.html", "transfer.html", "extremes.html", "cloud-form.html"];
const VIEWPORTS = [[900, 1200], [390, 844], [320, 844]];

const shotsAt = process.argv.indexOf("--shots");
const shotsDir = shotsAt > -1 ? process.argv[shotsAt + 1] : null;
if (shotsDir) fs.mkdirSync(shotsDir, { recursive: true });

// The gate launches its own Chrome: connectOverCDP to the persistent :9223
// instance hangs on this machine. For ad-hoc shots of that instance use
// scripts/shot.mjs, which speaks CDP directly.
const browser = await chromium.launch({ channel: "chrome", headless: true });
const context = await browser.newContext();
const results = [];
let failed = false;

async function check(label, url) {
  for (const [width, height] of VIEWPORTS) {
    const page = await context.newPage();
    await page.setViewportSize({ width, height });
    let status = null;
    let error = null;
    try {
      const response = await page.goto(url, { waitUntil: "load", timeout: 15000 });
      status = response ? response.status() : null;
      const overflow = await page.evaluate(() =>
        document.documentElement.scrollWidth - window.innerWidth);
      const ok = status === 200 && overflow <= 1;
      if (!ok) failed = true;
      results.push({ label, width, status, overflow, ok });
      if (shotsDir && width === 900) {
        await page.screenshot({
          path: path.join(shotsDir, `${label.replace(/\W+/g, "-")}.png`),
          fullPage: true,
        });
      }
    } catch (e) {
      failed = true;
      error = e.message.split("\n")[0];
      results.push({ label, width, status, error, ok: false });
    }
    await page.close();
    if (error) break;
  }
}

for (const page of PAGES) await check(page, `${DOCS}/${page}`);
await check("app", `${APP}/`);

await context.close();
await browser.close();
console.log(JSON.stringify(results, null, 1));
process.exit(failed ? 1 : 0);

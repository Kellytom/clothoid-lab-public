// Screenshot a page through the persistent headless Chrome on CDP 9223.
// No dependencies: Node 22's global WebSocket plus fetch.
//
//   node scripts/shot.mjs <url> <out.png> [width] [height] [full|viewport]

import fs from "node:fs";

const [, , url, out, w = "900", h = "1400", mode = "full"] = process.argv;
if (!url || !out) {
  console.error("usage: node scripts/shot.mjs <url> <out.png> [w] [h] [full|viewport]");
  process.exit(2);
}

const BASE = "http://127.0.0.1:9223";

const version = await fetch(`${BASE}/json/version`).catch(() => null);
if (!version || !version.ok) {
  console.error("no Chrome on 127.0.0.1:9223 — start it with:");
  console.error("  /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\");
  console.error("    --headless=old --disable-gpu --remote-debugging-port=9223 \\");
  console.error("    --user-data-dir=$TMPDIR/opencode/chrome-profile about:blank");
  process.exit(1);
}

const tab = await (await fetch(`${BASE}/json/new?${encodeURIComponent(url)}`, {
  method: "PUT",
})).json();

const ws = new WebSocket(tab.webSocketDebuggerUrl);
const pending = new Map();
let next = 0;

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  const done = pending.get(msg.id);
  if (done) {
    pending.delete(msg.id);
    done(msg);
  }
};
await new Promise((resolve) => { ws.onopen = resolve; });

const send = (method, params = {}) => new Promise((resolve) => {
  const id = ++next;
  pending.set(id, resolve);
  ws.send(JSON.stringify({ id, method, params }));
});

await send("Page.enable");
await send("Emulation.setDeviceMetricsOverride", {
  width: Number(w), height: Number(h), deviceScaleFactor: 1, mobile: false,
});
await send("Page.navigate", { url });
await new Promise((resolve) => setTimeout(resolve, 800));

const metrics = await send("Page.getLayoutMetrics");
const size = metrics.result.cssContentSize;
const clip = mode === "full"
  ? { x: 0, y: 0, width: size.width, height: size.height, scale: 1 }
  : undefined;
const shot = await send("Page.captureScreenshot", clip
  ? { format: "png", captureBeyondViewport: true, clip }
  : { format: "png" });

fs.writeFileSync(out, Buffer.from(shot.result.data, "base64"));
await fetch(`${BASE}/json/close/${tab.id}`);
ws.close();
console.log(out, `${Math.round(size.width)}x${Math.round(size.height)}`);

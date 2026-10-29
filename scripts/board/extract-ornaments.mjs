import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const DATA = process.env.BOARD_DATA || path.join(HERE, "data");
const PORT = Number(process.env.CDP_PORT || 9223);
const PAGE = `${process.env.ORNAMENTS_URL || "http://127.0.0.1:8010"}/ornaments.html`;
const version = await (await fetch(`http://127.0.0.1:${PORT}/json/version`)).json();
const ws = new WebSocket(version.webSocketDebuggerUrl);
let nextId = 0;
const pending = new Map();
ws.addEventListener("message", (ev) => {
  const msg = JSON.parse(ev.data);
  if (msg.id && pending.has(msg.id)) {
    const { resolve, reject } = pending.get(msg.id);
    pending.delete(msg.id);
    msg.error ? reject(new Error(JSON.stringify(msg.error))) : resolve(msg.result);
  }
});
await new Promise((res, rej) => { ws.addEventListener("open", res); ws.addEventListener("error", rej); });
function send(method, params = {}, sessionId) {
  const id = ++nextId;
  ws.send(JSON.stringify({ id, method, params, ...(sessionId ? { sessionId } : {}) }));
  return new Promise((resolve, reject) => pending.set(id, { resolve, reject }));
}
const { targetId } = await send("Target.createTarget", { url: "about:blank" });
const { sessionId } = await send("Target.attachToTarget", { targetId, flatten: true });
const s = (m, p) => send(m, p, sessionId);
await s("Page.enable"); await s("Runtime.enable");
await s("Emulation.setDeviceMetricsOverride", { width: 1400, height: 1200, deviceScaleFactor: 1, mobile: false });
await s("Page.navigate", { url: PAGE });
await new Promise((r) => setTimeout(r, 7000));

const expression = `(async () => {
  const sections = ['round','leaf','fleur','glyphs','stage-two-grid','stage-three-grid','stage-four-grid','stage-five-grid'];
  const out = [];
  for (const id of sections) {
    const root = document.getElementById(id);
    if (!root) continue;
    for (const c of root.querySelectorAll('.card')) {
      let svg = c.querySelector('svg')?.outerHTML || '';
      const img = c.querySelector('img');
      if (!svg && img) {
        try { svg = await (await fetch(img.src)).text(); } catch (e) { svg = ''; }
      }
      out.push({
        section: id,
        title: (c.querySelector('h3')?.textContent || '').trim(),
        note: (c.querySelector('.note')?.textContent || '').trim(),
        nums: (c.querySelector('.nums')?.innerText || '').trim(),
        prompt: (c.querySelector('pre')?.textContent || '').trim(),
        svg
      });
    }
  }
  return out;
})()`;
const { result, exceptionDetails } = await s("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
if (exceptionDetails) { console.error(JSON.stringify(exceptionDetails)); process.exit(1); }
const fs = await import("node:fs");
fs.writeFileSync(path.join(DATA, "ornaments-full.json"), JSON.stringify(result.value, null, 1));
const bySection = {};
for (const p of result.value) bySection[p.section] = (bySection[p.section] || 0) + 1;
console.log("total", result.value.length, JSON.stringify(bySection));
console.log("missing svg", result.value.filter((p) => !p.svg).length);
for (const p of result.value.slice(0, 3)) console.log(p.title, p.svg.length);
ws.close();

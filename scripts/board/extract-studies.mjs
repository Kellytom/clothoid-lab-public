import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const DATA = process.env.BOARD_DATA || path.join(HERE, "data");
const PORT = Number(process.env.CDP_PORT || 9223);
const PAGE = `${process.env.ORNAMENTS_URL || "http://127.0.0.1:8010"}/fleur-de-lis-20-tests.html`;
const version = await (await fetch(`http://127.0.0.1:${PORT}/json/version`)).json();
const ws = new WebSocket(version.webSocketDebuggerUrl);
let nextId = 0;
const pending = new Map();
const events = [];
ws.addEventListener("message", (ev) => {
  const msg = JSON.parse(ev.data);
  if (msg.id && pending.has(msg.id)) {
    const { resolve, reject } = pending.get(msg.id);
    pending.delete(msg.id);
    msg.error ? reject(new Error(JSON.stringify(msg.error))) : resolve(msg.result);
  } else events.push(msg);
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
await s("Page.enable");
await s("Runtime.enable");
await s("Emulation.setDeviceMetricsOverride", { width: 1280, height: 900, deviceScaleFactor: 1, mobile: false });
await s("Page.navigate", { url: PAGE });
await new Promise((r) => setTimeout(r, 7000));
const expression = `(() => {
  const cards = [...document.querySelectorAll('.card')];
  return {
    count: cards.length,
    cards: cards.map(c => ({
      title: (c.querySelector('h3')?.textContent || '').trim(),
      note: (c.querySelector('.note')?.textContent || '').trim(),
      nums: (c.querySelector('.nums')?.innerText || '').trim(),
      prompt: (c.querySelector('pre')?.textContent || '').trim(),
      svg: c.querySelector('svg')?.outerHTML || ''
    })),
    d3: typeof window.d3,
    ornaments: typeof window.OrnamentSet
  };
})()`;
const { result, exceptionDetails } = await s("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
if (exceptionDetails) {
  console.error(JSON.stringify(exceptionDetails));
  process.exit(1);
}
const fs = await import("node:fs");
fs.writeFileSync(path.join(DATA, "studies.json"), JSON.stringify(result.value, null, 1));
console.log("cards", result.value.count, "d3", result.value.d3, "ornaments", result.value.ornaments);
console.log(result.value.cards.slice(0, 2).map((c) => `${c.title} | ${c.note} | svg ${c.svg.length}`).join("\n"));
ws.close();

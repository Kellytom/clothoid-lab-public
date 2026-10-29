import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "../..");
const DATA = process.env.BOARD_DATA || path.join(HERE, "data");
const fleurStudies = JSON.parse(fs.readFileSync(path.join(DATA, "studies.json"), "utf8")).cards;
const catalogue = JSON.parse(fs.readFileSync(path.join(DATA, "ornaments-full.json"), "utf8"));
const template = fs.readFileSync(path.join(HERE, "board-template.html"), "utf8");

function cropSvg(text) {
  let svg = text.replace(/<sodipodi:namedview[\s\S]*?<\/sodipodi:namedview>/g, "");
  const pairs = [];
  for (const match of svg.matchAll(/\sd="([^"]+)"/g)) {
    const nums = (match[1].match(/-?\d+(?:\.\d+)?/g) || []).map(Number);
    for (let i = 0; i + 1 < nums.length; i += 2) pairs.push([nums[i], nums[i + 1]]);
  }
  if (pairs.length) {
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (const [x, y] of pairs) {
      x0 = Math.min(x0, x); y0 = Math.min(y0, y);
      x1 = Math.max(x1, x); y1 = Math.max(y1, y);
    }
    const pad = Math.max(x1 - x0, y1 - y0) * 0.05 + 1;
    const view = [x0 - pad, y0 - pad, x1 - x0 + 2 * pad, y1 - y0 + 2 * pad]
      .map((n) => n.toFixed(2)).join(" ");
    svg = svg.replace(/viewBox="[^"]*"/, `viewBox="${view}"`);
  }
  svg = svg.replace(/\swidth="[^"]*"/, "").replace(/\sheight="[^"]*"/, "");
  return svg;
}

function designFromDesc(svg) {
  const match = svg.match(/<desc id="clothoid-lab-design">([\s\S]*?)<\/desc>/);
  if (!match) return null;
  const text = match[1]
    .replace(/&quot;/g, '"').replace(/&apos;/g, "'")
    .replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&");
  try { return JSON.parse(text); } catch { return null; }
}

const icon = (body) => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 180" role="img">
  <rect width="240" height="180" fill="#fff"/>
  <g fill="none" stroke="#8C6A21" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">${body}</g>
</svg>`;

const fleurPlates = fleurStudies.map((study, index) => ({
  id: `P${String(index + 1).padStart(2, "0")}`,
  kind: "plate",
  group: "fleur-studies",
  groupLabel: "FLEUR STUDY",
  title: study.title,
  note: study.note,
  nums: study.nums,
  prompt: study.prompt,
  svg: study.svg,
}));

const sectionMap = [
  { section: "glyphs", group: "stage-1", short: "STAGE I", label: "Stage I vocabulary" },
  { section: "stage-two-grid", group: "stage-2", short: "STAGE II", label: "Stage II storeys" },
  { section: "stage-three-grid", group: "stage-3", short: "STAGE III", label: "Stage III analogies" },
  { section: "stage-four-grid", group: "stage-4", short: "STAGE IV", label: "Stage IV boteh" },
  { section: "stage-five-grid", group: "stage-5", short: "STAGE V", label: "Stage V scroll" },
  { section: "round", group: "terminals", short: "TERMINAL", label: "Terminals" },
  { section: "leaf", group: "terminals", short: "TERMINAL", label: "Terminals" },
  { section: "fleur", group: "hero", short: "HERO", label: "Hero fleur" },
];

const groupSuffix = {
  "fleur-studies": "This is one of twenty variations of the same ornament, not a finished piece. Compare it with its neighbours: does the tall centre leaf (the lance) balance the side petals, does the band sit at the right height, and does the foot look heavy enough? Write down the one change you would make next.",
  "stage-1": "This is one basic unit of the ornament language — a cross, leaf, palmette, scroll, volute or foil. Larger ornaments are made by arranging units like this one, so a unit that is unclear here will be unclear everywhere it is reused. Look for the intended sharp corners (point terminals) and smooth joins (G2: the bend does not jump). Work: redraw it with clothoid segments and compare the joins and terminals to the original.",
  "stage-2": "This is a whole ornament read from the ground up: a base that carries weight, a middle that holds the main idea, and a top that opens. The test is the silhouette, not the small detail. Build it from Stage I units rather than inventing new curves.",
  "stage-3": "This piece is a picture of an idea — an analogy — and each part is named. It has to read without a caption. Check that the named parts are legible and that the idea survives when colour is removed.",
  "stage-4": "This is the paisley family: a leaf bent inside a round drop, with a hook at the top. The back is one smooth arc; the leaves lean the same way; the hook leaves the back on its own tangent, without a kink. Small changes in the lean change the whole piece.",
  "stage-5": "This is a spiral. The hard part is the eye at the centre: the curve must tighten smoothly, and the last rail must approach the centre without a kink. This is where the choice between a clothoid and a spiro actually matters.",
  terminals: "This is a terminal study: it decides how an open stroke ends. A round end is a half-circle; an arc or leaf end is a small arc; a point is a sharp corner. The end must meet the side smoothly, and the fold radius is the tightest bend the ribbon can take before its inner edge folds over.",
  hero: "This is the assembled reference piece: the whole fleur built from the grammar, with a band, point terminals and two parallel edges. If the rebuilt grammar cannot reproduce this, the grammar is not ready.",
};

const groupBriefs = {
  all: {
    title: "The whole board — start here",
    text: "This board is for choosing what to do next. It holds 85 plates, 26 work items and 11 decisions. A plate is a drawing; a work item is a job that unlocks or supports plates; a decision is a rule that changes how the work is done. If a word is unfamiliar, open “Words used on this board” above. The DeepSeek pick sort is my recommended order: foundations first, then the ornament vocabulary, then whole pieces, then the web and operations work. Change it with priority, stage or manual order.",
  },
  "fleur-studies": {
    title: "The first hand — twenty studies",
    text: "Twenty variations of one ornament, P01–P20, all marked “Needs work”. They are a working set, not finished plates: the grammar has not yet been redrawn with clothoids, the terminal choice is still open, and the balance of the tall centre leaf (lance), side petals, band and foot still needs a human eye. Compare neighbouring pieces; whether the set reads as one hand matters more than any single number.",
  },
  "stage-1": {
    title: "Stage I — the vocabulary",
    text: "Twenty basic units: crosses, leaves, palmettes, scrolls, volutes and foils. A larger ornament is made by arranging units like these, so this is where the visual language is proved. Judge each unit as a single idea: does it read at a glance, are the intended corners sharp, are the joins smooth? If a unit fails here, it will fail in every piece that reuses it.",
  },
  "stage-2": {
    title: "Stage II — eight whole ornaments",
    text: "Monstrance, pillar, flower, crib, church, ship, crucifix, tree. Each is a small vertical world. The ground holds the piece, the middle carries the main idea, and the top opens. The test is gravity and silhouette — a heavy foot, a clear middle, an open top — not fine detail. Build them from Stage I units rather than inventing new curves.",
  },
  "stage-3": {
    title: "Stage III — the analogies",
    text: "Seven pieces that teach through an analogy: a building, a body, a vine, a harvest, a chalice, the communion of saints, an altar. Each part is named, and the piece has to read without a caption. Judge whether the named parts are legible and whether the idea survives when colour is removed.",
  },
  "stage-4": {
    title: "Stage IV — the bent leaf",
    text: "The boteh family: a leaf bent inside a round drop, then trefoil and quatrefoil fields. The grammar is lean and hook. The back is one smooth arc; the leaves grow from its inner edge and lean the same way; the hook leaves the back on its own tangent, without a kink. Small changes in the lean change the whole piece.",
  },
  "stage-5": {
    title: "Stage V — the scroll and its eye",
    text: "Two scrolls from the same brief: one built from a clothoid (Euler) spiral, one from a hyperbezier. The test is the eye at the centre — the curve must close smoothly and the last rail must approach the centre. This is the clearest place where G2 is not enough and G3 enters the decision.",
  },
  terminals: {
    title: "Terminal studies",
    text: "Four studies of how a stroke ends: round ends at two radii, leaf and arc ends at two radii. A terminal is the difference between a sketch and a finished ribbon. The end must meet the side smoothly, and the fold radius is the hard limit. Use these when choosing D02 (terminals).",
  },
  hero: {
    title: "The hero fleur",
    text: "The assembled fleur-de-lis: 24 spans, exact symmetry, a band, six point terminals and a scored parallel. It is the acceptance test for the whole grammar. If the port cannot reproduce this piece, the grammar is not ready.",
  },
  caps: {
    title: "Class I caps — rounded ribbon ends",
    text: "Twenty-seven caps from the existing clothoid set. A cap turns a ribbon through 180° and brings it back to the centre line, so the ribbon ends in a rounded end instead of a blunt cut. These are finished pieces, not sketches. Judge the fit (how close the drawing is to the exact curve) and the fold margin (how much room is left before the inner edge folds over).",
  },
  leaves: {
    title: "Class II leaves — pointed ends",
    text: "Nine pointed leaves from the existing set. A leaf is two clothoid edges that meet at a point; it has no ribbon width, and the point is the design. These are the point-terminal family. Judge the corner angle and the fit.",
  },
  presets: {
    title: "The four presets",
    text: "Bracket, ogee, petal and S-curve — the four named clothoid designs. They are the engine's sanity set and the starting points for the grammar. Bracket is the road transition; ogee is the S-shaped Gothic curve; petal closes four curves; S-curve reverses the bend. If these four are not right, nothing built above them is.",
  },
  "work-foundation": {
    title: "The foundations",
    text: "The four jobs everything else depends on: a way to hold several traces in one piece, a vocabulary for ends, the grammar port, and the twenty parameter sets. Skipping them turns every ornament into a special case. These should normally come before any plate.",
  },
  work: {
    title: "All 26 work items",
    text: "These are the jobs rather than the drawings: foundations, production batches, web and product work, and operations. Rank a job when it unblocks several plates or removes a risk; rank a plate when you want to see that piece on paper. The DeepSeek pick order puts the four foundations first, then the plates, then the supporting work.",
  },
  "work-stage": {
    title: "The production batches",
    text: "Four batch shortcuts, one per stage. They let you rank a whole stage at once instead of every plate. Use them only after the individual pieces are visible; a batch can hide the one piece that needs attention.",
  },
  "work-web": {
    title: "The web and product work",
    text: "Nine jobs that make the tool pleasant and safe to use: sliders, saving, sign-in, limits, phone use, browsing, undo, accessibility and help. They do not change the geometry, so do them after the plates they support — except saving, which is worth doing before a long tuning session.",
  },
  "work-ops": {
    title: "The operations and quality work",
    text: "Nine jobs that keep the project fast and honest: CI, deploy and rollback, monitoring, backup, regression tests, performance budgets, docs sync, the reference library and export. They are cheap early and expensive later.",
  },
};
let next = 21;
const cataloguePlates = [];
for (const spec of sectionMap) {
  for (const piece of catalogue.filter((p) => p.section === spec.section)) {
    cataloguePlates.push({
      id: `P${String(next++).padStart(2, "0")}`,
      kind: "plate",
      group: spec.group,
      groupLabel: spec.short,
      title: piece.title,
      note: piece.note,
      nums: piece.nums,
      prompt: piece.prompt,
      svg: piece.svg,
    });
  }
}

for (const plate of [...fleurPlates, ...cataloguePlates]) {
  plate.note = `${plate.note} ${groupSuffix[plate.group]}`;
}

const readme = fs.readFileSync(`${ROOT}/out/caps/README.md`, "utf8");
const capRows = new Map();
for (const line of readme.split("\n")) {
  const cells = line.split("|").slice(1, -1).map((cell) => cell.trim());
  if (cells.length >= 6 && /^`cap-(?:pt-)?\d+`$/.test(cells[0])) {
    capRows.set(cells[0].replace(/`/g, ""), cells.slice(1));
  }
}

const capNames = fs.readdirSync(`${ROOT}/out/caps`)
  .filter((name) => /^cap-\d+\.svg$/.test(name))
  .sort((a, b) => Number(a.slice(4, -4)) - Number(b.slice(4, -4)));
const leafNames = fs.readdirSync(`${ROOT}/out/caps`)
  .filter((name) => /^cap-pt-\d+\.svg$/.test(name))
  .sort((a, b) => Number(a.slice(7, -4)) - Number(b.slice(7, -4)));

const capPlates = [];
const leafPlates = [];
let capIndex = next;
for (const file of capNames) {
  const stem = file.replace(/\.svg$/, "");
  const row = capRows.get(stem) || [];
  const [segs, endY, l1, , , fit, cubics] = row;
  const raw = fs.readFileSync(`${ROOT}/out/caps/${file}`, "utf8");
  const design = JSON.parse(fs.readFileSync(`${ROOT}/out/caps/${stem}.json`, "utf8"));
  capPlates.push({
    id: `P${String(capIndex++).padStart(2, "0")}`,
    kind: "plate",
    group: "caps",
    groupLabel: "CAP I",
    title: `Cap ${stem.slice(4)}`,
    note: `A class I cap: a 10 mm ribbon turns through 180° and closes on the centre line at y = ${endY} mm. It has ${segs} clothoid segment${segs === "1" ? "" : "s"}. Fit (how far the drawing is from the exact curve) is ${fit} mm; the fold margin is the room left before the inner edge folds over. This is the round terminal made real — a ribbon ends in a rounded end instead of a blunt cut.`,
    nums: `segments ${segs} · end y ${endY} mm · L1 ${l1} · fit ${fit} · cubics ${cubics}`,
    prompt: JSON.stringify(design, null, 2),
    svg: cropSvg(raw),
  });
}

for (const file of leafNames) {
  const stem = file.replace(/\.svg$/, "");
  const row = capRows.get(stem) || [];
  const [endY, l1, corner, fit, cubics] = row;
  const raw = fs.readFileSync(`${ROOT}/out/caps/${file}`, "utf8");
  const design = JSON.parse(fs.readFileSync(`${ROOT}/out/caps/${stem}.json`, "utf8"));
  leafPlates.push({
    id: `P${String(capIndex++).padStart(2, "0")}`,
    kind: "plate",
    group: "leaves",
    groupLabel: "CAP II",
    title: `Pointed leaf ${stem.slice(7)}`,
    note: `A class II pointed leaf: two clothoid edges meet at a ${corner}° corner, and the base closes on the centre line at y = ${endY} mm. It has no ribbon width; the point is the design. Fit is ${fit} mm. This is the point terminal made real, and the corner angle is the knob.`,
    nums: `edges 2 · end y ${endY} mm · L1 ${l1} · corner ${corner}° · fit ${fit} · cubics ${cubics}`,
    prompt: JSON.stringify(design, null, 2),
    svg: cropSvg(raw),
  });
}

const presetMeta = {
  bracket: {
    title: "Bracket",
    note: "The road fillet: straight, transition in, constant arc, transition out, straight. This is the construction clothoids exist for; the joins are G2 and the arc share is the knob.",
  },
  ogee: {
    title: "Ogee",
    note: "Curvature rises, crosses zero, falls, returns to straight. The S of a Gothic ogee; each segment hands the next the curvature it ended on.",
  },
  petal: {
    title: "Petal",
    note: "Four clothoids with alternating hands, so the ends face the way they started. The closed petal unit and the clearest test of mirroring.",
  },
  "s-curve": {
    title: "S-curve",
    note: "Two clothoids of opposite hand; the bend reverses at the join. The simplest S and the clearest test of the sign convention.",
  },
};
const presetPlates = [];
let presetIndex = capIndex;
for (const [name, meta] of Object.entries(presetMeta)) {
  const raw = fs.readFileSync(`${ROOT}/out/${name}.svg`, "utf8");
  const design = designFromDesc(raw);
  const segments = design?.segments?.length ?? 0;
  const total = (design?.segments || []).reduce((sum, seg) => sum + Number(seg.length || 0), 0);
  presetPlates.push({
    id: `P${String(presetIndex++).padStart(2, "0")}`,
    kind: "plate",
    group: "presets",
    groupLabel: "PRESET",
    title: meta.title,
    note: meta.note,
    nums: `segments ${segments} · total length ${total.toFixed(1)} mm · stroke ${design?.stroke ?? "—"} · offsets ${(design?.offsets || []).length}`,
    prompt: design ? JSON.stringify(design, null, 2) : "",
    svg: cropSvg(raw),
  });
}

const clothoidPlates = [...capPlates, ...leafPlates, ...presetPlates];

const work = [
  {
    id: "W01",
    title: "Piece model",
    note: "An ornament is not one path: the half-stroke, the band, the two parallels and the mirror are separate traces that must stay registered. The engine renders one chain today, so every piece would become a special case. Build a Piece model with named traces, layers and a mirror first; W03 and W04 depend on it.",
    icon: icon(`
      <path d="M28 120 C 70 60, 100 150, 140 88 S 198 52, 214 92" stroke="#3A2E1A"/>
      <path d="M28 132 C 70 72, 100 162, 140 100 S 198 64, 214 104" opacity=".55"/>
      <path d="M28 108 C 70 48, 100 138, 140 76 S 198 40, 214 80" opacity=".55" stroke-dasharray="5 5"/>`),
  },
  {
    id: "W02",
    title: "Terminal vocabulary",
    note: "Terminals decide how a stroke finishes: a point (G0), a small arc, a round cap or a taper. The old grammar uses point and arc; the SPEC asks for round and taper. Implement all four behind one small vocabulary, report the terminal like a join, and keep the blunt butt join as the baseline.",
    icon: icon(`
      <path d="M34 74 H 140 A 16 16 0 0 1 140 106 H 34" stroke="#3A2E1A"/>
      <path d="M34 74 L 18 90 L 34 106" stroke="#B23A2B"/>
      <path d="M158 74 L 214 90 L 158 106" stroke="#3A2E1A"/>
      <circle cx="158" cy="90" r="2.6" fill="#B23A2B" stroke="none"/>`),
  },
  {
    id: "W03",
    title: "Fleur grammar",
    note: "Port the old half-stroke grammar — foot, tail, band, petal, lance — from ornament_set.js. The Euler spans map to clothoids, arcs become constant curvature, lines become zero curvature; the spiro/hyperbezier tails are the one place clothoid-only needs a decision. The first target is P01.",
    icon: icon(`
      <path d="M120 154 C 96 132, 60 120, 62 88 C 64 58, 92 50, 108 70 C 122 88, 116 108, 120 116 C 124 108, 118 88, 132 70 C 148 50, 176 58, 178 88 C 180 120, 144 132, 120 154 Z" stroke="#3A2E1A"/>
      <path d="M120 154 V 96" stroke="#B23A2B" stroke-dasharray="4 4"/>`),
  },
  {
    id: "W04",
    title: "Twenty parameter sets",
    note: "Once the grammar exists, the twenty parameter sets are data, not code. Generate P01–P20 with their prompts and measured error, and a contact sheet that reads as one hand. This is the first milestone where the studies can be judged as a set rather than one at a time.",
    icon: icon(`
      ${[0, 1, 2].map((r) => [0, 1, 2].map((c) => `<rect x="${62 + c * 40}" y="${38 + r * 40}" width="26" height="26" rx="3" stroke="#3A2E1A"/>`).join("")).join("")}`),
  },
  {
    id: "W05",
    title: "Stage II batch",
    note: "Batch shortcut for P41–P48. If you rank the batch, you are choosing all eight storeys; if one piece matters more, rank its plate instead. The pieces share the Stage I units and the three-storey test.",
    icon: icon(`
      <circle cx="120" cy="60" r="24" stroke="#3A2E1A"/>
      <path d="M120 84 V 128 M 96 150 H 144 M 104 140 H 136" stroke="#3A2E1A"/>
      <path d="M120 30 V 42 M 96 60 H 108 M 132 60 H 144" stroke="#8C6A21"/>`),
  },
  {
    id: "W06",
    title: "Stage III batch",
    note: "Batch shortcut for P49–P55. The analogies are the teaching set; the risk is a piece that reads only with its caption. Batch them only after the named parts are stable.",
    icon: icon(`
      <path d="M52 142 V 86 A 68 46 0 0 1 188 86 V 142" stroke="#3A2E1A"/>
      <path d="M84 142 V 102 A 36 28 0 0 1 156 102 V 142" opacity=".6"/>
      <path d="M120 62 V 142" stroke="#B23A2B" stroke-dasharray="4 5"/>`),
  },
  {
    id: "W07",
    title: "Stage IV–V batch",
    note: "Batch shortcut for P56–P60. The boteh family and the scroll share the lean/hook grammar; the scroll adds the eye-closure decision (D05).",
    icon: icon(`
      <path d="M120 150 C 72 132, 58 92, 82 62 C 104 34, 154 34, 166 66 C 178 98, 142 112, 128 98 C 116 86, 132 70, 142 80" stroke="#3A2E1A"/>`),
  },
  {
    id: "W08",
    title: "Drapery and church decoration",
    note: "Drapery is the bridge to church decoration. The fold report is the instrument: a fold must be chosen, not discovered. No plates yet; this is the first piece of the next phase.",
    icon: icon(`
      <path d="M48 38 C 68 70, 58 110, 44 144" stroke="#3A2E1A"/>
      <path d="M86 38 C 104 74, 96 116, 82 144" stroke="#3A2E1A"/>
      <path d="M124 38 C 142 74, 134 116, 120 144" stroke="#3A2E1A"/>
      <path d="M162 38 C 180 74, 172 116, 158 144" stroke="#3A2E1A"/>
      <path d="M48 38 C 96 50, 144 50, 196 38" stroke="#8C6A21"/>`),
  },
  {
    id: "W09",
    title: "Sliders per family",
    note: "Sliders over the family parameters, not raw segments. A clothoid chain is coupled, so a per-segment slider would break joins; the useful controls are length, turn, band, lean and terminal. Keep the JSON as the source of truth.",
    icon: icon(`
      <path d="M56 58 H 188 M 56 90 H 188 M 56 122 H 188" stroke="#3A2E1A"/>
      <circle cx="94" cy="58" r="8" fill="#8C6A21" stroke="none"/>
      <circle cx="148" cy="90" r="8" fill="#8C6A21" stroke="none"/>
      <circle cx="76" cy="122" r="8" fill="#8C6A21" stroke="none"/>`),
  },
  {
    id: "W10",
    title: "Persistence and share",
    note: "Persistence is cheap and independent of the geometry: autosave to localStorage, restore on boot, and a share link that carries the design. Do it after the plates if the browser is only a viewer; do it before a long tuning session if you need to keep variants.",
    icon: icon(`
      <path d="M84 66 H 60 A 12 12 0 0 0 48 78 V 132 A 12 12 0 0 0 60 144 H 148 A 12 12 0 0 0 160 132 V 108" stroke="#3A2E1A"/>
      <path d="M112 48 H 186 V 108 H 112 Z" stroke="#3A2E1A"/>
      <path d="M112 48 L 186 108" stroke="#8C6A21" opacity=".6"/>`),
  },
  {
    id: "W11",
    title: "Auth and access",
    note: "The URL is public. Auth is the gate to sharing: Google sign-in, a shared token, or keep it private. Deferred by operator decision; do not implement until D07 is answered.",
    icon: icon(`
      <path d="M120 34 L 178 58 V 94 C 178 128 152 150 120 158 C 88 150 62 128 62 94 V 58 Z" stroke="#3A2E1A"/>
      <path d="M100 88 V 80 A 20 20 0 0 1 140 80 V 88 M 96 88 H 144 V 126 H 96 Z" stroke="#8C6A21"/>`),
  },
  {
    id: "W12",
    title: "Rate limiting and quotas",
    note: "Even with auth, a public endpoint can burn the free allowance. Keep the 1 MB body and 200-segment bounds, add a per-IP or per-token limit, and cap concurrency. A simple in-process limiter is enough before a service.",
    icon: icon(`
      <path d="M48 128 A 72 72 0 0 1 192 128" stroke="#3A2E1A"/>
      <path d="M120 128 L 164 84" stroke="#B23A2B"/>
      <circle cx="120" cy="128" r="5" fill="#B23A2B" stroke="none"/>
      <path d="M56 128 H 72 M 168 128 H 184 M 74 88 L 86 100 M 166 88 L 154 100" stroke="#8C6A21"/>`),
  },
  {
    id: "W13",
    title: "Mobile and touch",
    note: "The page is responsive but still a desktop form on a phone. Inputs at 16 px, 44 px targets, a collapsible JSON editor, a preview that can be pinched, and the report collapsed. Test on the actual Samsung in Chrome and Samsung Internet.",
    icon: icon(`
      <rect x="80" y="30" width="80" height="122" rx="10" stroke="#3A2E1A"/>
      <path d="M108 40 H 132" stroke="#8C6A21"/>
      <circle cx="120" cy="140" r="3" fill="#8C6A21" stroke="none"/>`),
  },
  {
    id: "W14",
    title: "Gallery and browse",
    note: "A catalogue grid with the 85 plates and their prompts, so a piece can be found by eye, not by ID. This is the natural home for the reference library; the board stays the ranking instrument.",
    icon: icon(`
      <rect x="44" y="40" width="68" height="46" stroke="#3A2E1A"/>
      <rect x="128" y="40" width="68" height="46" stroke="#3A2E1A"/>
      <rect x="44" y="98" width="68" height="46" stroke="#3A2E1A"/>
      <rect x="128" y="98" width="68" height="46" stroke="#3A2E1A"/>`),
  },
  {
    id: "W15",
    title: "Undo and history",
    note: "A clothoid chain is easy to break with one edit. Keep a small undo/redo stack of design JSON plus page and width, with a visible history. Snapshot on render; do not persist every keystroke.",
    icon: icon(`
      <path d="M60 96 A 54 54 0 1 1 74 130" stroke="#3A2E1A"/>
      <path d="M60 70 V 98 H 88" stroke="#B23A2B"/>`),
  },
  {
    id: "W16",
    title: "Accessibility and keyboard",
    note: "Keyboard-only use and screen readers: labelled controls, a sensible focus order, visible focus, and shortcuts that do not fight the browser. The gaps are the preview and the JSON editor, not the buttons.",
    icon: icon(`
      <rect x="44" y="58" width="62" height="64" rx="6" stroke="#3A2E1A"/>
      <path d="M54 74 H 96 M 54 90 H 96 M 54 106 H 96" stroke="#8C6A21"/>
      <path d="M136 84 L 156 104 L 196 56" stroke="#3A2E1A"/>`),
  },
  {
    id: "W17",
    title: "Onboarding and help",
    note: "A first-run panel: what the tool is, the four presets, how to change a curve, and what the report means. The JSON editor is a developer surface; a newcomer should not have to start there.",
    icon: icon(`
      <circle cx="120" cy="86" r="46" stroke="#3A2E1A"/>
      <path d="M104 72 A 18 18 0 1 1 130 98 C 122 104 120 110 120 118" stroke="#8C6A21"/>
      <circle cx="120" cy="138" r="4" fill="#8C6A21" stroke="none"/>`),
  },
  {
    id: "W18",
    title: "CI on push",
    note: "Run the unit tests and the headless layout gate on every push. GitHub Actions is the cheap default; Cloud Build is already there but is not a test runner. A red main should block deploys.",
    icon: icon(`
      <path d="M44 90 H 74 L 92 62 L 112 118 L 132 90 H 196" stroke="#3A2E1A"/>
      <path d="M158 70 L 178 90 L 158 110" stroke="#2F6F4E"/>`),
  },
  {
    id: "W19",
    title: "Deploy, rollback, cache",
    note: "One command to deploy, one to roll back, and a recorded revision. The image split makes an app deploy about 30 s; add a smoke check after routing and keep the previous revision one command away.",
    icon: icon(`
      <path d="M120 152 V 58" stroke="#3A2E1A"/>
      <path d="M94 84 L 120 58 L 146 84" stroke="#B23A2B"/>
      <path d="M70 130 C 70 112 86 104 104 108 M 170 130 C 170 112 154 104 136 108" stroke="#8C6A21"/>`),
  },
  {
    id: "W20",
    title: "Monitoring and alerts",
    note: "Know when the service is down or slow: an uptime check on the public URL, Cloud Run error and latency alerts, and a note in the handoff when a revision changes. Keep the budget alert, but add a usage view.",
    icon: icon(`
      <path d="M44 96 H 70 L 84 70 L 102 126 L 120 82 L 136 110 L 152 96 H 196" stroke="#3A2E1A"/>
      <circle cx="84" cy="70" r="4" fill="#B23A2B" stroke="none"/>`),
  },
  {
    id: "W21",
    title: "Backup and restore",
    note: "Back up what cannot be regenerated: the repo, the cap JSON and SVG, the ornament sources, and any saved designs. Git covers code; the designs and caps need a second copy in a bucket or release artifact.",
    icon: icon(`
      <ellipse cx="120" cy="58" rx="56" ry="18" stroke="#3A2E1A"/>
      <path d="M64 58 V 118 C 64 128 89 136 120 136 C 151 136 176 128 176 118 V 58" stroke="#3A2E1A"/>
      <path d="M64 88 C 64 98 89 106 120 106 C 151 106 176 98 176 88" stroke="#8C6A21"/>`),
  },
  {
    id: "W22",
    title: "Regression suite",
    note: "Go beyond unit tests: render a fixed corpus of caps, presets and ornaments and compare hashes or measured error; screenshot the page at 320, 390 and 1280. Catch a geometry or CSS change before a phone does.",
    icon: icon(`
      <rect x="42" y="48" width="66" height="86" stroke="#3A2E1A"/>
      <rect x="132" y="48" width="66" height="86" stroke="#3A2E1A"/>
      <path d="M66 92 L 82 108 L 164 58" stroke="#2F6F4E"/>`),
  },
  {
    id: "W23",
    title: "Performance budget",
    note: "Set budgets: render under 500 ms warm, interactive under 2 s, app deploy under 60 s, cold start under 3 s. Measure, do not guess; put the numbers in the handoff so a regression is visible.",
    icon: icon(`
      <circle cx="120" cy="96" r="48" stroke="#3A2E1A"/>
      <path d="M120 96 L 120 62 M 120 96 L 150 112" stroke="#B23A2B"/>
      <path d="M120 40 V 48 M 176 96 H 168 M 72 96 H 64" stroke="#8C6A21"/>`),
  },
  {
    id: "W24",
    title: "Docs sync automation",
    note: "The handoff, handover, HTML mirror, backlog and board drift. Add a small check that counts, links and command names agree, and run it before /fhandoff. Keep the board generated from one data file.",
    icon: icon(`
      <path d="M46 48 H 108 V 132 H 46 Z" stroke="#3A2E1A"/>
      <path d="M132 48 H 194 V 132 H 132 Z" stroke="#3A2E1A"/>
      <path d="M108 90 H 132" stroke="#8C6A21"/>`),
  },
  {
    id: "W25",
    title: "Reference library",
    note: "A browsable page for the 58 catalogue designs and 72 ornament SVGs, kept separate from the work board. These are the visual sources, not clothoid plates; they should be findable without polluting the order.",
    icon: icon(`
      <path d="M44 62 H 92 V 136 H 44 Z M 100 54 H 144 V 136 H 100 Z M 152 66 H 196 V 136 H 152 Z" stroke="#3A2E1A"/>
      <path d="M54 78 H 82 M 110 70 H 134 M 162 82 H 186" stroke="#8C6A21"/>`),
  },
  {
    id: "W26",
    title: "Export paths",
    note: "The working output is SVG. Add PNG for review and print, and an OTF/Glyphs path when the ornament set is stable; Inkscape remains the editor. Do not build a font pipeline before the shapes are right.",
    icon: icon(`
      <path d="M64 76 H 132 V 140 H 64 Z" stroke="#3A2E1A"/>
      <path d="M132 76 L 176 42 M 150 42 H 176 V 68" stroke="#B23A2B"/>
      <path d="M64 56 H 120" stroke="#8C6A21"/>`),
  },
];

const workMeta = {
  W01: ["work-foundation", "FOUNDATION"],
  W02: ["work-foundation", "FOUNDATION"],
  W03: ["work-foundation", "FOUNDATION"],
  W04: ["work-foundation", "FOUNDATION"],
  W05: ["work-stage", "PRODUCTION"],
  W06: ["work-stage", "PRODUCTION"],
  W07: ["work-stage", "PRODUCTION"],
  W08: ["work-stage", "PRODUCTION"],
  W09: ["work-web", "WEB"],
  W10: ["work-web", "WEB"],
  W11: ["work-web", "WEB"],
  W12: ["work-web", "WEB"],
  W13: ["work-web", "WEB"],
  W14: ["work-web", "WEB"],
  W15: ["work-web", "WEB"],
  W16: ["work-web", "WEB"],
  W17: ["work-web", "WEB"],
  W18: ["work-ops", "OPS"],
  W19: ["work-ops", "OPS"],
  W20: ["work-ops", "OPS"],
  W21: ["work-ops", "OPS"],
  W22: ["work-ops", "OPS"],
  W23: ["work-ops", "OPS"],
  W24: ["work-ops", "OPS"],
  W25: ["work-ops", "OPS"],
  W26: ["work-ops", "OPS"],
};

const definitions = [
  { term: "Plate (P…)", text: "One drawing or design. P01–P20 are the twenty fleur studies on their own page; P21–P65 are the catalogue ornaments; P66–P105 are the caps and presets we already made. The number is permanent, so you can quote it." },
  { term: "Work item (W…)", text: "A job that unlocks or supports plates — building the piece model, adding sign-in, running tests. Work items are ranked the same way as plates." },
  { term: "Decision (D…)", text: "A choice that changes how the work is done. Click one option per decision. A decision is a rule, not a task." },
  { term: "Clothoid", text: "A curve whose bend changes at a steady rate along its length. That steady change is what makes a road transition feel smooth, and what lets two curves meet without a sudden jerk. The whole project is built on this curve." },
  { term: "Curvature", text: "How tightly a curve is bending at one point. A straight line has zero curvature; a small circle has a lot." },
  { term: "Curvature rate", text: "How fast the curvature changes as you travel along the curve. A clothoid has a constant curvature rate." },
  { term: "Join — G1, G2, G3", text: "A join is where two pieces meet. G1 means they meet in the same direction with no kink. G2 means they also have the same bend, so the bend does not jump. G3 also matches how fast the bend is changing. Higher is smoother; G2 is the normal target here." },
  { term: "Corner / point terminal", text: "A deliberate sharp turn between two pieces. A leaf tip is a corner on purpose; an accidental corner is a fault." },
  { term: "Terminal", text: "How an open stroke ends: a point, a small arc, a round cap, or a taper. It is a design choice, not leftover geometry." },
  { term: "Ribbon, rail, offset", text: "A ribbon is a stroke with width. Its two edges are rails. Each rail is the centre line moved sideways by an offset — half the ribbon width on each side." },
  { term: "Fold", text: "When a ribbon is wider than the tightest bend, the inner rail turns back on itself and folds over. The fold radius and margin say when that happens. A fold is allowed only if you chose it." },
  { term: "Fit / tolerance", text: "The drawing uses cubic Bézier curves to approximate the exact clothoid. Fit is the measured worst distance between them; tolerance is the limit you accept (0.02 mm by default). Smaller is better." },
  { term: "Cap (class I)", text: "A cap turns a ribbon through 180° and brings it back to the centre line, so the ribbon ends in a rounded end instead of a blunt cut." },
  { term: "Leaf (class II)", text: "A leaf is two clothoid edges that meet at a point. It has no ribbon width; the point is the design." },
  { term: "Euler, arc, spiro", text: "An Euler curve is a clothoid: the bend changes steadily. An arc has constant bend. A spiro is a different spiral where both the bend and its rate are controlled; it is not a clothoid." },
  { term: "Lattice", text: "The old drawings used whole-number points and radii like 25, 125 and 625. A clothoid does not naturally land on those points. “Lattice-first” means fitting the curve back to them and printing the error." },
  { term: "Trace", text: "A drawing that shows the construction as well as the shape: the curve, its handles, the knots, and the two parallel edges. A trace is proof; a fill is a finish." },
  { term: "Prompt", text: "The written recipe for a piece: the prose for the eye and the span table for the arithmetic. A piece is not finished until its prompt is written." },
];

const workCopy = {
  W01: "Done 2026-10-26. A Piece now holds named traces (spine, band, rails), an optional ribbon width per trace, a piece-level mirror with per-trace override, and layers. render_piece() writes one SVG through svg.document(groups=...); the visual proof is docs/piece-model.html. Tests: tests/test_piece.py.",
  W02: "A terminal is any treatment of an open ribbon end; a cap is a subset that closes the end without turning the stroke past a limit — 120 degrees for now, a tunable choice. Seven are drawn: four caps (butt, point, arc, round) and three tapers (taper, cone, bulb, the last two on the Stage II width laws w = ½(t(3−3t+t²)+12t²(1−t)³) and w = ½(1−(1−t)³), both G2 at the join). Each end is set separately, drawn as geometry and reported with kind, reach and fold; a folded ribbon is refused. Turned terminals — hairpin, and the old wrapped bulb — are the missing category: they turn past the cap limit and are not caps. Bulb here is the width-law taper, not the wrapped bulb; the names collide, the shapes do not. Reopened 2026-10-26; 88 Stage II and 62 log-aesthetic ends recovered to docs/terminals/.",
  W03: "This is the port of the old fleur grammar: foot, tail, band, petals and centre leaf, redrawn with clothoid segments. Straight lines become zero-curvature segments; arcs stay arcs; Euler curves stay clothoids. The first target is P01, so the new grammar can be compared directly with the old drawing.",
  W04: "Once the grammar works, the twenty studies are data, not twenty programs. This job turns the parameter sets into P01–P20, each with its written recipe (prompt) and its measured error. Then the set can be judged as one hand.",
  W05: "Batch shortcut for P41–P48, the eight whole ornaments. Rank this if you want all eight; rank an individual plate if one matters more. They share the Stage I units and the same three-part test: heavy base, clear middle, open top.",
  W06: "Batch shortcut for P49–P55, the seven teaching pieces. Each is an analogy with named parts, and must read without a caption. Batch them only after the named parts are stable.",
  W07: "Batch shortcut for P56–P60: the boteh family and the scroll. They share the lean-and-hook grammar; the scroll adds the eye-closure question and the G3 decision.",
  W08: "Drapery is the bridge to church decoration. The fold report is the instrument: a fold must be chosen, not discovered. There are no plates yet; this starts the next phase.",
  W09: "Sliders over the family parameters — length, turn, band, lean, terminal — not over raw segment numbers. A clothoid chain is coupled, so a per-segment slider would break the joins. The JSON stays the source of truth.",
  W10: "This saves a design in the browser and puts it in a link. It is independent of the geometry and cheap. Do it before a long tuning session so variants are not lost.",
  W11: "Done 2026-10-26. Every route except /health now requires a shared token over HTTP Basic; the token lives in Secret Manager as clothoid-token. Accounts, named users and roles are still absent.",
  W12: "Done 2026-10-26. POST /api/render is limited to 60 requests per minute with a burst of 20 per client address; excess returns 429 with Retry-After. The limiter is in-process, so it resets on a cold start.",
  W13: "The page works on a phone but still feels like a desktop form. This job makes inputs large enough to tap, stops the browser zooming when a field is focused, collapses the JSON editor, and makes the preview easy to inspect. Test it on the actual Samsung in Chrome and Samsung Internet.",
  W14: "A browsable gallery of all 85 plates, with their written recipes. The board is for ordering; the gallery is for finding a piece by eye. It is also the natural home for the reference library.",
  W15: "One edit can break a chain. This adds undo and redo for the design, page and ribbon width, with a short visible history. Snapshot on render; do not store every keystroke.",
  W16: "This makes the page usable without a mouse and with a screen reader: labels, focus order, visible focus, and shortcuts that do not fight the browser. The weak spots are the preview and the JSON editor, not the buttons.",
  W17: "A first-run guide: what the tool does, the four presets, how to change a curve, and what the report means. The JSON editor is a developer surface; a beginner should not have to start there.",
  W18: "CI runs the tests automatically when code changes. This job adds a GitHub Actions check for the unit tests and the headless layout gate. A red main branch should block a deploy.",
  W19: "One command to deploy, one to roll back, and a record of which revision is live. The split image already makes an app deploy about 30 seconds; this adds a smoke check and keeps the previous revision one command away.",
  W20: "This tells you when the site is down or slow: an uptime check on the public URL, Cloud Run error and latency alerts, and a note in the handoff when a revision changes. The budget alert stays, with a usage view beside it.",
  W21: "Back up what cannot be regenerated: the repository, the cap files, the ornament sources, and any saved designs. Git covers the code; the drawings and caps need a second copy in a bucket or release.",
  W22: "A regression suite renders a fixed set of caps, presets and ornaments and compares the result, and screenshots the page at 320, 390 and 1280 pixels. It catches a geometry or CSS change before a phone does.",
  W23: "Set and measure budgets: render under 500 ms warm, page usable under 2 s, app deploy under 60 s, cold start under 3 s. Put the numbers in the handoff so a regression is visible.",
  W24: "The handoff, handover, HTML mirror, backlog and board drift apart. This adds a small check that counts, links and command names agree, run before /fhandoff. The board should be generated from one data file.",
  W25: "A browsable page for the 58 catalogue designs and 72 ornament SVGs, kept separate from the work board. These are visual sources, not clothoid plates, so they should not pollute the order.",
  W26: "The working output is SVG. This adds PNG for review and print, and an OTF/Glyphs path when the ornament set is stable. Inkscape remains the editor; do not build a font pipeline before the shapes are right.",
};
for (const item of work) {
  if (workCopy[item.id]) item.note = workCopy[item.id];
}

const taggedWork = work.map((item) => {
  const [group, groupLabel] = workMeta[item.id];
  return { kind: "work", group, groupLabel, ...item };
});

const decisions = [
  {
    id: "D01",
    title: "Scope",
    note: "The board has 85 plates (45 catalogue ornaments, 27 caps, 9 leaves, 4 presets) plus the 20 fleur studies on their own page. Catalogue-first gets finished ornaments on paper. Studies-first fixes the shared grammar before it is copied twenty times. Recommendation: fix the fleur grammar and the twenty studies first, then the catalogue.",
    default: "fleur",
    options: [
      { value: "fleur", label: "The twenty fleur studies first" },
      { value: "catalogue", label: "The catalogue plates first" },
      { value: "all", label: "Everything, ranked together" },
    ],
  },
  {
    id: "D02",
    title: "Terminals",
    note: "A terminal is how an open stroke ends. Point and arc are the old grammar's ends; round and taper are the ribbon caps. Point + arc unblocks the ornament plates; round + taper completes the ribbon tool. Recommendation: point + arc first, then round + taper.",
    default: "point-arc",
    options: [
      { value: "point-arc", label: "Point + arc — unblocks the ornaments" },
      { value: "round-taper", label: "Round + taper — completes the ribbon" },
      { value: "both", label: "Both" },
    ],
  },
  {
    id: "D03",
    title: "Lattice",
    note: "Smooth-first accepts a small measured error and drops the claim that every knot is a whole-number point. Lattice-first keeps the old whole-point discipline but forces a fit after every clothoid chain. Recommendation: smooth-first for the ornament pass, with the error printed on every piece.",
    default: "smooth",
    options: [
      { value: "smooth", label: "Smooth first — measured error" },
      { value: "lattice", label: "Lattice first — force whole points" },
    ],
  },
  {
    id: "D04",
    title: "Output",
    note: "A trace shows the construction — curves, knots, handles, parallel edges — and is the proof of a piece. A clean black path is the working file for Inkscape. Recommendation: both from one source; if only one, the trace, because it shows how the piece was built.",
    default: "both",
    options: [
      { value: "trace", label: "Trace — colour, knots, parallels" },
      { value: "clean", label: "Clean black path for Inkscape" },
      { value: "both", label: "Both from one source" },
    ],
    default: "both",
    options: [
      { value: "trace", label: "Trace · colour, knots, parallels" },
      { value: "clean", label: "Clean black path" },
      { value: "both", label: "Both from one source" },
    ],
  },
  {
    id: "D05",
    title: "Joins",
    note: "A clothoid-to-arc join is G2: the bend matches, but the rate of bend steps. A hyperbezier can be G3 at one end and contains arcs and clothoids exactly; a spiro can hold the rate of bend at both ends but is a second family. Recommendation: clothoid-only first; add hyperbezier only where a scroll's eye visibly needs G3.",
    default: "g2",
    options: [
      { value: "g2", label: "Clothoid only — G2 at best" },
      { value: "hyper", label: "Add hyperbezier — G3 at one end" },
      { value: "spiro", label: "Add spiro — G3 at both ends" },
    ],
  },
  {
    id: "D06",
    title: "Mirroring",
    note: "Mirror one half and the piece is guaranteed to be symmetrical; it also halves the work. Build both halves independently only when a piece is meant to be asymmetrical. Recommendation: mirror, unless the design says otherwise.",
    default: "mirror",
    options: [
      { value: "mirror", label: "Mirror one half" },
      { value: "independent", label: "Build both halves independently" },
    ],
  },
  {
    id: "D07",
    title: "Access",
    note: "Chosen 2026-10-26 and implemented: a shared token over HTTP Basic. Private means no sharing; Google sign-in names each user; public + rate limit lets anyone in with caps. The token is in Secret Manager; accounts and roles are still a later job.",
    default: "token",
    options: [
      { value: "private", label: "Private — no sign-in yet" },
      { value: "token", label: "Shared token — one password" },
      { value: "google", label: "Google sign-in — named users" },
      { value: "open", label: "Public + rate limit" },
    ],
  },
  {
    id: "D08",
    title: "Data",
    note: "localStorage keeps a design in this browser; a share link carries it to someone else. Export-only is stateless — nothing is kept between visits. Cloud saves add accounts, a database and cost. Recommendation: localStorage + link now; cloud only when several people work together.",
    default: "local",
    options: [
      { value: "local", label: "localStorage + share link" },
      { value: "export", label: "Stateless — export only" },
      { value: "cloud", label: "Cloud saves" },
    ],
  },
  {
    id: "D09",
    title: "CI",
    note: "CI means the tests run automatically when code changes, so a broken change is caught before a deploy. GitHub Actions is free for this repository; Cloud Build builds deploys, it is not a test runner. Recommendation: GitHub Actions.",
    default: "actions",
    options: [
      { value: "actions", label: "GitHub Actions" },
      { value: "cloudbuild", label: "Cloud Build only" },
      { value: "manual", label: "Manual — run the tests yourself" },
    ],
  },
  {
    id: "D10",
    title: "Export",
    note: "SVG is the working file for Inkscape; PNG is for review and print; OTF/Glyphs is for the type and ornament pipeline. Recommendation: SVG + PNG now, OTF only when the shapes are stable.",
    default: "svg",
    options: [
      { value: "svg", label: "SVG + PNG" },
      { value: "otf", label: "OTF / Glyphs" },
      { value: "both", label: "All three" },
    ],
  },
  {
    id: "D11",
    title: "Monitoring",
    note: "Logs only is free but blind: you see a problem only if you go looking. Uptime + Cloud Run alerts tell you when the site is down or slow. An error service adds stack traces and grouping. Recommendation: uptime + alerts.",
    default: "uptime",
    options: [
      { value: "logs", label: "Logs only" },
      { value: "uptime", label: "Uptime + alerts" },
      { value: "service", label: "Error service" },
    ],
  },
];

const boardGroups = [
  { value: "all", label: "All (111)" },
  { value: "plates", label: "All plates (85)" },
  { value: "stage-1", label: "Stage I vocabulary (20)" },
  { value: "stage-2", label: "Stage II storeys (8)" },
  { value: "stage-3", label: "Stage III analogies (7)" },
  { value: "stage-4", label: "Stage IV boteh (3)" },
  { value: "stage-5", label: "Stage V scroll (2)" },
  { value: "terminals", label: "Terminal studies (4)" },
  { value: "hero", label: "Hero fleur (1)" },
  { value: "caps", label: "Class I caps (27)" },
  { value: "leaves", label: "Class II leaves (9)" },
  { value: "presets", label: "Presets (4)" },
  { value: "work", label: "All work items (26)" },
  { value: "work-foundation", label: "Foundations (4)" },
  { value: "work-stage", label: "Productions (4)" },
  { value: "work-web", label: "Web / product (9)" },
  { value: "work-ops", label: "Ops / quality (9)" },
];

const boardOrder = [
  ...taggedWork.filter((w) => ["W01", "W02", "W03", "W04"].includes(w.id)),
  ...cataloguePlates.filter((p) => p.group === "stage-1"),
  ...cataloguePlates.filter((p) => p.group === "stage-2"),
  ...cataloguePlates.filter((p) => p.group === "stage-3"),
  ...cataloguePlates.filter((p) => p.group === "stage-4"),
  ...cataloguePlates.filter((p) => p.group === "stage-5"),
  ...cataloguePlates.filter((p) => p.group === "terminals"),
  ...cataloguePlates.filter((p) => p.group === "hero"),
  ...capPlates,
  ...leafPlates,
  ...presetPlates,
  ...taggedWork.filter((w) => ["W05", "W06", "W07", "W08"].includes(w.id)),
  ...taggedWork.filter((w) => w.group === "work-web"),
  ...taggedWork.filter((w) => w.group === "work-ops"),
];

const workPicks = {
  W01: 10, W02: 11, W03: 12, W04: 13,
  W05: 90, W06: 91, W07: 92, W08: 93,
  W09: 100, W10: 101, W11: 102, W12: 103, W13: 104,
  W14: 105, W15: 106, W16: 107, W17: 108,
  W18: 120, W19: 121, W20: 122, W21: 123, W22: 124,
  W23: 125, W24: 126, W25: 127, W26: 128,
};
const plateBase = {
  "fleur-studies": 20,
  "stage-1": 30,
  "stage-2": 40,
  "stage-3": 50,
  "stage-4": 60,
  "stage-5": 61,
  terminals: 70,
  hero: 71,
  caps: 80,
  leaves: 81,
  presets: 82,
};
const pickCount = {};
for (const item of boardOrder) {
  if (item.kind === "work") {
    item.pick = workPicks[item.id] ?? 999;
  } else {
    const base = plateBase[item.group] ?? 999;
    const index = (pickCount[item.group] = (pickCount[item.group] ?? -1) + 1);
    item.pick = base + index * 0.1;
  }
}
for (const item of fleurPlates) {
  item.pick = 20 + fleurPlates.indexOf(item) * 0.1;
}

const boardData = {
  mode: "board",
  version: 6,
  storageKey: "clothoid-ornament-board-v1",
  exportName: "ornament-board.json",
  title: "clothoid ornament board — what to do next",
  lead: "A visual to-do board for the clothoid ornament project. Every plate, job and decision has a permanent label. Read the definitions, open a card, rank it, then copy the order back into the session.",
  legend: "<b>P</b> = plate (a drawing). <b>W</b> = work item (a job). <b>D</b> = decision (a rule). Priority <b>1</b> = do next, <b>5</b> = someday. Stage = foundational / sketch / finished. <b>DeepSeek pick</b> is my recommended order. Saved in this browser; use Export JSON to keep a copy. P01–P20 are on the fleur-studies page.",
  subpage: {
    href: "fleur-studies.html",
    label: "Open the twenty fleur studies (P01–P20) — a working set that needs work →",
  },
  back: null,
  groups: boardGroups,
  groupBriefs,
  decisions,
  definitions,
  items: boardOrder,
};

const fleurData = {
  mode: "fleur",
  version: 2,
  storageKey: "clothoid-fleur-studies-v1",
  exportName: "fleur-studies.json",
  title: "fleur studies — the first hand",
  lead: "Twenty drawings that are variations of one ornament. They are a working set, not finished plates: compare them, rank them, and write the one change each needs before it can be called Ready.",
  legend: "<b>P01–P20</b> · priority <b>1</b> = do next · <b>Needs work</b> = not ready; <b>Ready</b> = can join the catalogue. Saved in this browser; use Export JSON to keep a copy.",
  subpage: null,
  back: { href: "ornament-board.html", label: "← back to the ornament board" },
  groups: [{ value: "fleur-studies", label: "Fleur studies (20)" }],
  groupBriefs: { "fleur-studies": groupBriefs["fleur-studies"] },
  decisions: [],
  definitions,
  items: fleurPlates,
};

function render(data, path) {
  const json = JSON.stringify(data)
    .replace(/<\/script/gi, "<\\/script")
    .replace(/\u2028/g, "\\u2028")
    .replace(/\u2029/g, "\\u2029");
  const html = template.replace("__DATA__", json);
  fs.writeFileSync(path, html);
  return { path, bytes: html.length, items: data.items.length };
}

const a = render(boardData, path.join(ROOT, "docs/ornament-board.html"));
const b = render(fleurData, path.join(ROOT, "docs/fleur-studies.html"));
console.log(a);
console.log(b);

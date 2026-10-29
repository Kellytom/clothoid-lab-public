const els = {
  preset: document.querySelector("#preset"),
  cap: document.querySelector("#cap"),
  width: document.querySelector("#width"),
  pagew: document.querySelector("#pagew"),
  pageh: document.querySelector("#pageh"),
  design: document.querySelector("#design"),
  render: document.querySelector("#render"),
  preview: document.querySelector("#preview"),
  report: document.querySelector("#report"),
  status: document.querySelector("#status"),
  downloadSvg: document.querySelector("#downloadSvg"),
  downloadJson: document.querySelector("#downloadJson"),
  loadFile: document.querySelector("#loadFile"),
  file: document.querySelector("#file"),
  toggleReport: document.querySelector("#toggleReport"),
};

let lastSvg = null;
let debounce = 0;
let lastName = "design";

function setStatus(text, kind = "") {
  els.status.textContent = text;
  els.status.className = "status" + (kind ? " " + kind : "");
}

function showError(message) {
  setStatus("error", "bad");
  els.report.textContent = String(message);
  els.report.classList.add("error");
  els.report.hidden = false;
  els.toggleReport.textContent = "hide";
}

function clearError() {
  els.report.classList.remove("error");
}

async function api(path, options) {
  const response = await fetch(path, options);
  let body;
  try {
    body = await response.json();
  } catch {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  if (!response.ok) throw new Error(body.error || `${response.status} ${response.statusText}`);
  return body;
}

function setDesign(design) {
  els.design.value = JSON.stringify(design, null, 2);
  if (design.name) {
    lastName = design.name.replace(/[^a-z0-9._-]+/gi, "-").replace(/^-+|-+$/g, "") || "design";
  }
}

function fillSelect(select, names) {
  for (const name of names) {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = name;
    select.append(option);
  }
}

function page() {
  return [Number(els.pagew.value), Number(els.pageh.value)];
}

async function loadPreset(name) {
  if (!name) return;
  els.cap.value = "";
  els.width.value = "10";
  setStatus("loading…");
  try {
    const body = await api("/api/preset?name=" + encodeURIComponent(name));
    setDesign(body.design);
    await render();
  } catch (error) {
    showError(error.message);
  }
}

async function loadCap(name) {
  if (!name) return;
  els.preset.value = "";
  // Class II leaves are two clothoid edges meeting at a point; a constant
  // width rail would put a diamond at that point. Draw the edges only.
  els.width.value = name.startsWith("cap-pt-") ? "" : "10";
  setStatus("loading…");
  try {
    const body = await api("/api/cap?name=" + encodeURIComponent(name));
    setDesign(body.design);
    await render();
  } catch (error) {
    showError(error.message);
  }
}

async function render() {
  clearTimeout(debounce);
  let design;
  try {
    design = JSON.parse(els.design.value);
  } catch (error) {
    showError("design.json: " + error.message);
    return;
  }

  const width = els.width.value.trim() === "" ? null : Number(els.width.value);
  const sheet = page();
  if (width !== null && !(width > 0)) {
    showError("ribbon width must be greater than zero");
    return;
  }
  if (!(sheet[0] > 0) || !(sheet[1] > 0)) {
    showError("sheet sides must be greater than zero");
    return;
  }

  clearError();
  setStatus("rendering…");
  const started = performance.now();
  try {
    const body = await api("/api/render", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ design, width, page: sheet, tol: 0.02, split: 2 }),
    });
    lastSvg = body.svg;
    els.preview.innerHTML = body.svg;
    els.report.textContent = body.report;
    els.report.classList.remove("error");
    els.report.hidden = els.toggleReport.textContent === "show";

    const info = body.info;
    const chain = info.chain;
    const ms = body.elapsed_ms ?? (performance.now() - started);
    const joins = info.g1 ? "G1" : chain.join_g2 ? "G2" : "check joins";
    const verdict = info.ok ? joins : "check report";
    const corners = chain.corner_count ? ` · ${chain.corner_count} corner${chain.corner_count === 1 ? "" : "s"}` : "";
    setStatus(
      `${ms.toFixed(0)} ms · ${chain.segments} segment${chain.segments === 1 ? "" : "s"} · ` +
      `${info.fit.spans} cubics · ${verdict}${corners}`,
      info.ok ? "ok" : "warn",
    );
  } catch (error) {
    showError(error.message);
  }
}

function download(blob, name) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = name;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

async function init() {
  els.preview.innerHTML = '<div class="empty">loading the geometry engine…</div>';
  try {
    const [presetBody, capBody] = await Promise.all([api("/api/presets"), api("/api/caps")]);
    fillSelect(els.preset, presetBody.presets);
    fillSelect(els.cap, capBody.caps);
  } catch (error) {
    showError(error.message);
    return;
  }

  els.preset.addEventListener("change", () => loadPreset(els.preset.value));
  els.cap.addEventListener("change", () => loadCap(els.cap.value));
  els.render.addEventListener("click", render);
  els.width.addEventListener("change", render);
  els.pagew.addEventListener("change", render);
  els.pageh.addEventListener("change", render);
  els.design.addEventListener("input", () => {
    clearTimeout(debounce);
    debounce = setTimeout(render, 450);
  });
  els.design.addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
      event.preventDefault();
      render();
    }
  });
  els.loadFile.addEventListener("click", () => els.file.click());
  els.file.addEventListener("change", async () => {
    const file = els.file.files?.[0];
    if (!file) return;
    try {
      const text = await file.text();
      JSON.parse(text);
      els.design.value = text;
      await render();
    } catch (error) {
      showError(file.name + ": " + error.message);
    } finally {
      els.file.value = "";
    }
  });
  els.downloadSvg.addEventListener("click", async () => {
    if (!lastSvg) await render();
    if (!lastSvg) return;
    download(new Blob([lastSvg], { type: "image/svg+xml" }), lastName + ".svg");
  });
  els.downloadJson.addEventListener("click", () => {
    try {
      const data = JSON.parse(els.design.value);
      const text = JSON.stringify(data, null, 2);
      download(new Blob([text], { type: "application/json" }), lastName + ".json");
    } catch (error) {
      showError("design.json: " + error.message);
    }
  });
  els.toggleReport.addEventListener("click", () => {
    els.report.hidden = !els.report.hidden;
    els.toggleReport.textContent = els.report.hidden ? "show" : "hide";
  });

  els.cap.value = "cap-14";
  await loadCap("cap-14");
}

init();

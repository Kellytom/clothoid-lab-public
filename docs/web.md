# Web / PWA architecture

A static, local-first PWA with a TypeScript UI and the C++ Clothoids engine
compiled to WebAssembly. No server, no database, no Python in production.

## Shape

```
Browser
  HTML/CSS/TS (UI)
    └── Web Worker
          └── TypeScript core (model, fit, rails, SVG)
                └── WASM wrapper
                      └── C++17 Clothoids + C ABI
```

The Python package stays in the repository as the reference implementation and
the test oracle. The web app is a separate port of the same policy, not a
wrapper around a Python server.

## Directory structure

```
clothoid-web/
├── package.json
├── pnpm-lock.yaml
├── tsconfig.json
├── vite.config.ts
├── index.html
├── public/
│   ├── manifest.webmanifest
│   ├── icons/                    192, 512, maskable
│   ├── offline.html
│   └── robots.txt
├── src/
│   ├── main.ts                   mounts the app, registers the PWA
│   ├── app/
│   │   ├── App.svelte            or App.ts, if vanilla
│   │   ├── controls/             numbers, presets, caps, sheets
│   │   ├── preview/              inline SVG, pan/zoom (no transform in file)
│   │   ├── report/               fit, folds, corners, scale
│   │   └── dialogs/              import, export, about
│   ├── core/
│   │   ├── model.ts              design, segments, JSON, validation, corner
│   │   ├── engine.ts             place chain, joins, corners, arc length
│   │   ├── wasm.ts               module loader, memory, typed calls, errors
│   │   ├── bezier.ts             arm rule, subdivision, measured error
│   │   ├── offsets.ts            rails, folds, corner handling
│   │   ├── svg.ts                paths, annotations, y-up flip, page/frame
│   │   ├── render.ts             pure renderDesign(design, opts) -> svg, report
│   │   ├── presets.ts            s-curve, ogee, bracket, petal
│   │   ├── interpolate.ts        G1/G2 through points
│   │   ├── compose.ts            trim, reverse, connect, join
│   │   ├── solve.ts              bounded least squares for exercises
│   │   └── caps.ts               class I and class II cap builders
│   ├── state/
│   │   ├── store.ts              current design, dirty flag
│   │   ├── history.ts            undo/redo command stack
│   │   └── persist.ts            IndexedDB, File System Access, autosave
│   ├── workers/
│   │   └── render.worker.ts      render off the main thread
│   ├── pwa/
│   │   ├── register.ts           service worker registration, updates
│   │   └── install.ts            beforeinstallprompt, iOS hints
│   ├── styles/
│   └── wasm/                     generated, not edited
│       ├── clothoid.js           Emscripten ES module
│       ├── clothoid.wasm
│       └── clothoid.d.ts         hand-written or --emit-tsd
├── cpp/
│   ├── clothoid_api.cpp          same 26-function C surface
│   └── build-wasm.sh             em++ invocation
├── vendor/Clothoids/             pinned, BSD-2 + MPL-2 Eigen
├── scripts/
│   ├── build-wasm.sh
│   ├── check-goldens.ts          TS output against Python SVGs
│   └── make-icons.ts
├── tests/
│   ├── unit/                     Vitest
│   ├── goldens/                  SVG fixtures from the Python suite
│   └── e2e/                      Playwright
├── deploy/
│   ├── netlify.toml
│   ├── _headers
│   ├── _redirects
│   └── cloudflare/_headers
└── .github/workflows/ci.yml
```

## Components and responsibilities

| Component | Language | Responsibility | Depends on |
|---|---|---|---|
| `cpp/clothoid_api.cpp` | C++17 | plain C ABI over the vendor engine | Clothoids, Eigen |
| `clothoid.wasm` | WASM | compiled engine | Emscripten |
| `core/wasm.ts` | TS | load, memory, arrays, error codes, typed `g1_fit`, `g2_spline`, `trim`, etc. | wasm module |
| `core/model.ts` | TS | design types, JSON schema, units, corners | — |
| `core/engine.ts` | TS | resolve curvature, tangent, corners; global arc length | model, wasm |
| `core/bezier.ts` | TS | arm rule, split, error along arc length | engine |
| `core/offsets.ts` | TS | exact rails, folds, corner joins | engine |
| `core/svg.ts` | TS | absolute `M`/`C`, no transforms, +y up, annotations | model |
| `core/render.ts` | TS | one pure function: design → SVG + report | all core |
| UI (`app/`) | TS + HTML/CSS | controls, preview, report, import/export | render, state |
| `state/` | TS | undo, autosave, IndexedDB, file access | model |
| `workers/render.worker.ts` | TS | keeps fitting off the UI thread | render |
| PWA (`pwa/`, manifest) | TS/JSON | install, offline cache, updates | Vite PWA |
| Tests | TS | unit, goldens, e2e | all |

## Dependencies

### Toolchain, not npm

- **Node.js 20 or 22 LTS**, **pnpm** (or npm).
- **Emscripten SDK (`emsdk`)**, pinned; provides `emcc`, `em++`, `wasm-ld`.
- **Binaryen** (`wasm-opt`) for size/speed after linking.
- **wabt** (`wasm2wat`) optional, for debugging.
- **CMake is optional.** A `build-wasm.sh` with `em++` is enough; add a modern
  `CMakeLists.txt` only if native and WASM builds should share one file.

### Runtime dependencies (bundle)

- **`idb`** — small IndexedDB wrapper for designs and settings.
- **`workbox-window`** — update/install lifecycle messages (optional; the
  service worker itself is generated).
- **`zod`** — optional; JSON validation can be hand-written instead.
- **UI framework, optional:** Svelte 5 (recommended: small, no virtual DOM) or
  vanilla TS. React works but is heavier for one screen.
- **No geometry runtime dependency.** The engine is the `.wasm` file.

### Dev dependencies

`typescript`, `vite`, `svelte` + `@sveltejs/vite-plugin-svelte` (or none),
`svelte-check`, `vitest`, `@vitest/coverage-v8`, `@playwright/test`,
`eslint` + `typescript-eslint`, `prettier`, `vite-plugin-pwa`,
`@types/node`, `@types/emscripten` (if using the runtime API types).

## WASM build

```sh
em++ -std=c++17 -O3 -flto -fexceptions \
  -Ivendor/Clothoids/src \
  -Ivendor/Clothoids/submodules/UtilsLite/src \
  -Ivendor/Clothoids/submodules/UtilsLite/ThirdParties/Eigen \
  -Ivendor/Clothoids/submodules/GenericContainer/include \
  -Ivendor/Clothoids/submodules/quarticRootsFlocke/src \
  csrc/clothoid_api.cpp vendor/Clothoids/src/*.cc ... \
  -sMODULARIZE=1 -sEXPORT_ES6=1 -sEXPORT_NAME=createClothoid \
  -sENVIRONMENT=web,worker -sALLOW_MEMORY_GROWTH=1 \
  -sFILESYSTEM=0 -sDISABLE_EXCEPTION_CATCHING=0 \
  -sEXPORTED_FUNCTIONS='["_malloc","_free","_cl_new",...]' \
  -sEXPORTED_RUNTIME_METHODS='["ccall","cwrap","HEAPF64"]' \
  -o src/wasm/clothoid.js
```

- Keep the **26 `cl_*` functions**; export `_malloc` and `_free`.
- `-sEXPORT_ES6` gives a module the worker can import.
- Keep **single-threaded**; no pthreads, so no COOP/COEP headers, and GitHub
  Pages stays viable.
- `-fexceptions` and exception catching are required because the vendor throws.
- `wasm-opt -O3` afterwards; strip debug for production.
- Emit TS declarations (`--emit-tsd`) or write `clothoid.d.ts` by hand.
- ABI version: add `cl_abi_version()` before shipping; the JS wrapper refuses
  a mismatch.

## PWA

- `manifest.webmanifest`: name, short_name, start_url, scope, display
  `standalone`, theme/background, 192/512/maskable icons.
- Service worker (generated by `vite-plugin-pwa`): precache app shell, JS,
  CSS, WASM; cache-first for hashed assets; navigation fallback to
  `index.html`; offline page.
- Update flow: `workbox-window` message, “new version — reload”.
- Install prompt: `beforeinstallprompt`, plus iOS `apple-mobile-web-app-*`.
- Offline storage: IndexedDB for designs/settings; File System Access API for
  open/save where available, Blob download/upload otherwise.
- No server; designs never leave the device unless exported.

## The Linux `.so`

The Linux library is not committed. `.github/workflows/native.yml` builds it on
every push and pull request:

- artifact: **`libclothoidlab-linux-x86_64`**, containing
  `build/libclothoidlab.so`
- download from the Actions run, or `gh run download <run-id> -n
  libclothoidlab-linux-x86_64`
- the same job runs the 92 tests against the `.so`

`scripts/build-native.sh` builds `libclothoidlab.dylib` on macOS and
`libclothoidlab.so` on Linux, with separate object directories. The Python
backend selects the suffix from the platform, and `CLOTHOID_LIB` overrides the
path.

For a server, the clean option is still a multi-stage Dockerfile that runs the
script during the image build; then there is no artifact to copy around.

## Deploy targets

| Target | Config | Notes |
|---|---|---|
| Local | `pnpm dev` / `pnpm preview`; `python3 -m http.server dist` | WASM needs HTTP, not `file://` |
| Cloudflare Pages | build `pnpm build`, output `dist`, `_headers`, `_redirects` | static; no Worker needed |
| Netlify | `netlify.toml`, `_headers`, `_redirects` | static; functions not used |
| GitHub Pages | `base` for repo path, `404.html` | no custom headers; keep single-threaded |
| celld | only if a backend is added | self-hosted Workers; WASM + Durable Objects |

## Testing and CI

- **Vitest** for core: model, corners, fit, rails, SVG rules.
- **Golden SVGs** generated by the Python implementation; compare structure and
  geometry within the stated precision.
- **Playwright** for load, render, export, offline reload, install.
- **WASM smoke test**: load, `cl_abi_version`, one fit, one eval.
- **Fuzz** design JSON: NaN, huge n, zero length, duplicate points, bad page.
- CI: emsdk cache, `pnpm install --frozen-lockfile`, build wasm, unit, e2e,
  build web, upload artifact.

## Sizes and performance

- Wasm engine: roughly 1–3 MB before Brotli, depending on what is linked;
  keep the C surface narrow and let the linker drop unused code.
- App JS/CSS: ~100–300 KB.
- Startup target: under one second on a laptop, under three on a tablet.
- Render: keep the Python lesson — batch evaluation. Do not make hundreds of
  thousands of JS↔WASM calls in the arc-length search; move the search or the
  sampling into Wasm, or use the library’s projection.
- Run fitting in a Web Worker; post the design, receive SVG + report.

## Security and licensing

- CSP: `default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; img-src 'self' data:`.
- Validate input: finite numbers, positive lengths, segment/page caps, JSON
  size limit; timeout the worker.
- Vendor licences: Clothoids BSD-2-Clause, Eigen MPL-2.0, our code MIT. Ship a
  `NOTICE`/`ATTRIBUTION` file with the build.
- No telemetry, no uploads by default.

## Milestones

1. **WASM spike** — compile, export, call one function, load in a Worker (1–2 days).
2. **Core TS port** — model, engine, fit, rails, SVG; goldens against Python (1–2 weeks).
3. **UI + worker** — controls, preview, report, import/export (3–5 days).
4. **PWA + storage** — manifest, service worker, IndexedDB, file access (2–3 days).
5. **Deploy + CI** — Cloudflare Pages/Netlify, headers, e2e (1–2 days).

Total: **3–5 focused weeks**, with the TypeScript core as the real work.

# Project overview

`clothoid-lab` turns numerical clothoids into plain, editable SVG. A design is
a chain of clothoid segments — curvature rising linearly with arc length —
placed in the plane, fitted to cubic Béziers to a measured tolerance, offset
into rails, and written in millimetres with no transform, so Inkscape opens it
as ordinary nodes. The loop is meant for a human: edit a design, the watcher
rebuilds, Inkscape reloads, look, repeat.

It is a small tool with a real engine under it. The geometry is Bertolazzi and
Frego's Clothoids (BSD-2), compiled from the vendored source; everything above
the C surface is MIT and written here.

## Pipeline

```
design JSON ──┐
              ├─ engine.build ── fit to cubics ── rails ── SVG + design in <desc>
points file ──┘        │                          │
                       │                          └─ folds, margins, error report
                       └─ Clothoids: place, evaluate, exact offset
                                              │
watcher ── file stamp ── atomic write ─────────┘── Inkscape reload (Cmd+Opt+R)
```

Three properties the code takes seriously:

1. **Measured, not assumed.** Fit error is found by searching arc length; joins
   report their curvature jump; rails report folds and margins.
2. **The file is the interface.** Absolute `M`/`C`, millimetres, no transform,
   no exponent notation, and the design rides along in the SVG for round trip.
3. **A bad edit never destroys the last good drawing.** The watcher writes
   atomically and keeps the old file when the new one does not parse.

## Structure

```
.
├── clothoid_lab/              Python 3, the package (MIT)
│   ├── model.py               design, segments, JSON, validation
│   ├── engine.py              place the chain, arc-length addressing, joins
│   ├── bezier.py              arm rule, adaptive split, error metric
│   ├── offsets.py             exact rails, fold ranges, ribbon
│   ├── svg.py                 path writer/reader, view carry-over, framing
│   ├── presets.py             s-curve, ogee, bracket, petal
│   ├── interpolate.py         G1/G2 fit and spline through points
│   ├── compose.py             trim, reverse, connect, join
│   ├── solve.py               bounded least squares for exercises
│   ├── cli.py                 report, flags, exit status
│   ├── watch.py               two-window loop, atomic rebuild
│   └── backend/               ctypes surface + pyclothoids adapter
├── csrc/clothoid_api.cpp      C++17, the C surface over Clothoids (MIT)
├── scripts/
│   ├── build-native.sh        compile the vendored engine (Bash)
│   ├── grid_3125.py           reverse-curve grid generator (Python)
│   ├── bind_shortcut.py       Cmd+Opt+R = Revert (Python)
│   ├── fit_view.py            compute the saved Inkscape fit view (Python)
│   ├── twin.py                self-contained HTML twin of a drawing (Python)
│   ├── set_window_geometry.py Inkscape window frame and chrome (Python)
│   └── place-window.sh        window helper (Bash)
├── tests/                     Python, unittest, 92 checks
├── vendor/Clothoids/          C++17 engine and submodules (BSD-2 and friends)
├── build/libclothoidlab.dylib the compiled engine + C surface
├── out/                       drawings, designs, grid tables (scratch)
│   └── caps/                  cap family, fold and index
├── docs/                      TODO, this overview, the 3125 grid note
├── README.md  SPEC.md  ATTRIBUTION.md  LICENSE
```

### Languages and size

| Layer | Language | Lines |
|---|---|---|
| Package, tests, scripts | Python 3 | ~3,100 |
| C surface | C++17 | ~340 |
| Build and window helpers | Bash | ~130 |
| Vendored Clothoids and submodules | C++17 | ~103,000 |
| Design and output | JSON, SVG/XML | data |
| Docs | Markdown | ~1,000 |

No Rust, no JavaScript, no Node. The one place a second language earns its keep
is the compiled C++ engine; everything else is Python because it is glue and
math, and glue in Rust would only add a build step.

## Who wrote what

| What | Where | Language | Author | Licence |
|---|---|---|---|---|
| Geometry engine: evaluation, exact offsets, G1/G2 fitting, trim, projection, intersections | `vendor/Clothoids` | C++ | Enrico Bertolazzi, Marco Frego | BSD-2 |
| Linear algebra | `vendor/.../Eigen` | C++ headers | Eigen authors | MPL-2.0 |
| UtilsLite, GenericContainer, quarticRootsFlocke | `vendor/.../submodules` | C++ | Enrico Bertolazzi | permissive |
| Chain model, cubic fit, rails, SVG, presets, CLI, watcher, C surface | `clothoid_lab/`, `csrc/` | Python, C++ | Kellytom (project author); this session's additions by Kellytom with an OpenCode agent | MIT |
| Tests and scripts | `tests/`, `scripts/` | Python, Bash | same | MIT |
| Prebuilt wheel, second opinion only | optional dependency | Python/C++ | Phillip Dix (`pyclothoids`) | MIT |
| Editor and reload target | external app | C++ | Inkscape team | GPL-2.0+ |

The cubic arm rule follows Raph Levien's 2021 work on parallel curves with Euler
spirals. The idea is used; no code from it is.

The reverse-curve construction in `docs/clothoid-grid-3125.md` follows the
standard odd symmetry of the Euler spiral. The brief that prompted it is the
author's; its arithmetic was checked and corrected here.

## Effort and time

The repository began on 23 October 2026. In two days it went from nothing to
a working engine, fitter, SVG writer, watcher, and G1/G2 fitting with splicing.
Rough shape of the work:

| Phase | State | Focused effort |
|---|---|---|
| Engine, fit, rails, SVG, loop | done | ~3 days |
| G1 fitting through points | done | ~0.5 day |
| Reverse-curve maths and 3125 table | done | ~0.5 day |
| G2, smoothing, trim, connectors, queries | done | ~1 day |
| Terminals and closed outline | planned | 2–4 days |
| Splicing and parts library | connectors done; parts library planned | 1–2 days |
| Sheet in the design, check pass | planned | 1–1.5 days |
| Inkscape extension | planned | 1–2 days |
| PySide6 parameter window | planned | 2–4 days |
| Re-import / inverse fit | planned | 2–3 days |
| Packaging and CI | planned | 0.5–1 day |

Total remaining: roughly **10–18 focused days**, so two to four working weeks
including review and looks. The uncertainty is concentrated in terminals and in
the parameter window; the curve geometry is mostly binding work because the
library already implements it.

## Running it

```sh
bash scripts/build-native.sh                 # compile the engine, ~1 minute
python3 -m venv .venv                        # no runtime dependencies
.venv/bin/python -m clothoid_lab.cli --preset ogee --width 6 --out out/ogee.svg

# the two-window loop
.venv/bin/python -m clothoid_lab.cli --watch --design out/play.json \
    --width 4 --frame 200x250 --out out/play.svg
```

Inkscape: `Cmd+Opt+R` reverts after a rebuild; `5` fits the page. The window is
placed by `scripts/set_window_geometry.py`.

```sh
.venv/bin/python -m unittest discover tests   # 92 checks
.venv/bin/python scripts/grid_3125.py         # reverse-curve table
```

## Environment

- macOS 12.7.6, Intel
- Xcode 13.2.1 at `/Applications/Xcode.app`, selected with `xcode-select`
- `/usr/bin/python3` 3.8.9; project venv Python 3.12.4
- Inkscape 1.4.4, used as the viewer and node editor
- Apple clang 13.0.0, C++17, no CMake (the vendored tree is CMake 3.x era)
- Target machine is small: the design goal is to run beside Inkscape on 8 GB

## Documents

- `README.md` — how to use it, and the decisions behind the output.
- `SPEC.md` — what it promises, with the acceptance numbers.
- `docs/TODO.md` — what is done, planned, and what is broken.
- `docs/clothoid-grid-3125.md` — reverse curves, odd symmetry, the exact 4% table.
- `docs/caps.md` — the closed two-clothoid cap family and its fold.
- `ATTRIBUTION.md` — licences and provenance.

# To do

Status as of **2026-10-24**. Two states only:

- **done** — in the tree, tested, working.
- **planned** — not written.

Effort is focused working time, not calendar time.

## Done

- **Engine.** Clothoid chains compiled from the vendored C++ (BSD-2), placed by
  arc length, continuity measured rather than assumed.
- **Cubic fit with a measured error.** Adaptive split, error found by searching
  arc length, not by distance to samples.
- **Offset rails and ribbons**, with folds drawn and their arc-length ranges and
  margins reported.
- **SVG writer.** Absolute `M`/`C`, millimetres, no transform, no exponent
  notation, design JSON carried in the file.
- **Design model.** Anchor, segments, explicit or inherited curvature, JSON
  round trip, `g1` flag for fits whose curvature jumps are intended.
- **G1 fitting.** Two-point `buildClothoid` and a spline through points, as a
  design; CLI `--points`, watchable with `--watch --points`. Every point hit to
  ~1e-14 mm in tests.
- **Two-window loop.** Poll-based watcher, atomic writes, a bad edit never
  blanks the drawing, Inkscape's zoom and pan carried across rebuilds.
- **Fixed frame and fit-on-open view.** `--frame WxH`, view centred and scaled
  for the portrait sheet.
- **Desktop convenience.** `Cmd+Option+R` = File → Revert, installed by
  `scripts/bind_shortcut.py`; window placement and chrome via
  `scripts/set_window_geometry.py`.
- **Environment.** Xcode 13.2.1 selected, `/usr/bin/python3` works again,
  project venv on Python 3.12.4.
- **Reverse-curve maths and the 3125 grid.** The S-pair as one clothoid with
  zero curvature at the inflection, verified G2 and symmetric to `1.7e-11 mm`;
  a generator and 4% table in `scripts/grid_3125.py` and
  `docs/clothoid-grid-3125.md`.
- **G2 and splicing.** G2 splines through points (open or closed), quasi-G2
  smoothing, trim, reverse, projection, intersections, ISO measurements, and
  G2 connectors with `join`. 92 tests, all passing.
- **Twin and view helpers.** `scripts/twin.py` writes a self-contained HTML twin;
  `scripts/fit_view.py` computes the Inkscape saved view (zoom is a factor, not
  pixels per millimetre).
- **Cap family and fold.** The two-clothoid caps from `closed-cl-1` were
  continued from y=10 to y=162.2817, where `kd2` reaches zero; documented in
  `docs/caps.md` with the full table in `out/caps/README.md`.
- **Class II pointed leaves.** Both clothoids left-turning, one tangent corner;
  `cap-pt-1`…`cap-pt-9` from Y=20 to Y=180, the point closing at Y=199.239.

## Planned, in priority order

### 1b. Reverse curves and the 3125 grid — 1–2 days

The brief is received and checked in `docs/clothoid-grid-3125.md`. The maths is
settled; the choices are not.

- [ ] Treat `3125` as the module, not a sheet: no sheet is required, and a
      sheet is never a limit. Only `--page` (refuses a page too small) and
      `--frame` (scales) introduce one, both optional.
- [x] Working sheet set to `200 × 250 mm` for now; 25 divisions are
      `8 × 10 mm`. The sheet remains optional and is not a limit.
- [ ] Suggested starting sheets, not constraints: one full S is
      `2.7647A x 1.5536A` at 90 degree halves, so `6A` holds `2.17` S. Cell
      `3A x 2A`, three across `30625 x 7500` with `625` gaps, is a suggestion
      (245 x 60 steps of 125); the sheet may also grow automatically.
- [ ] Decide the grid: integer rounding is honest, 125 snapping is not (up to
      58 units off). If 125 is required, adopt canvas 5250 with `A = 3121.0`.
- [ ] Add a reverse-curve design: one clothoid crossing zero curvature, half
      turn and `A` in the design JSON.
- [ ] CLI entry (`--reverse A --half-turn DEG`) and a preset.
- [ ] Tests: `kappa = 0` at the inflection, G2, symmetry error < 1e-9, endpoints.
- [ ] A renderer path that consumes `out/grid-3125.json` without hand arithmetic.
- [ ] Reconcile with the millimetre design model: the grid is a scale, not a
      unit system, so state how it maps onto the sheet.

Acceptance: a reverse curve is generated from parameters, passes through the
inflection with zero curvature, is G2, and a renderer reproduces the table to
integers.

### 2. Terminals and a closed ribbon outline — 2–4 days

The one layer no repository has. `Clothoids` offsets at a constant distance; a
tapered or looped end needs a width envelope.

- [ ] Half-width as a function of arc length, `w(s)`, and rails offset by it.
- [ ] Terminal kinds made from clothoids: round, tapered to a point, looped.
- [ ] Outline builder: rail + terminal + rail + terminal, one closed path.
- [ ] Keep the three-line mode. The spine is already a separate path, so the
      paint can change without touching the geometry.
- [ ] Add a filled ribbon mode and an `inlay` style: filled outline, spine drawn
      last as an accent line. The accent must stay a separate path so it remains
      editable.
- [ ] Decide what "white" means: white ink printed on top of the fill, or a
      knockout that lets the paper through. They are different SVGs and print
      differently; the accent path alone cannot express a knockout.
- [ ] Terminals close the rails; the centreline may stop at the terminal or run
      to the tip.
- [ ] Styles named `lines` (current), `ribbon` (closed outline), `inlay`
      (filled ribbon plus a centreline accent).
- [ ] Report terminal length, taper, and any self-intersection.
- [ ] Tests: square end, taper to zero width, round end, no crossing, and the
      three-line output unchanged.

Acceptance: a ribbon closes with a chosen terminal at both ends and its outline
is a single path with no self-crossing for the test designs. The existing
three-line drawing remains the default; a filled ribbon can carry the spine as a
centreline accent, with the accent's ink semantics stated rather than assumed.

### 3. Splicing and a parts library — 1–2 days

- [ ] `join(a, b, method)` using the G2 connectors, with both designs
      materialised to explicit curvature first.
- [ ] A part: a named design with its own local frame and a start/end pose.
- [ ] Resolve a list of parts into one chain; check each seam.
- [ ] A small library of parts (ogee, bracket, scroll, terminal).
- [ ] Tests: two parts joined, curvature continuous at the seam, round trip.

### 4. The design file owns the sheet — 0.5 day

- [ ] Move `page`, `frame`, `width`, `stroke`, `offsets` into the design JSON.
- [ ] CLI falls back to the file, flags still override.
- [ ] One command for every design; the watcher command stops depending on the
      drawing.

### 5. A real check pass — 1 day (can merge into 2)

- [ ] Use `intersect` for crossings instead of the sampling script.
- [ ] Clearance between non-neighbour parts, fold margins, aspect, fill.
- [ ] `--check` prints a verdict and sets the exit status.
- [ ] Tests: crossing pair caught, clear pair passed.

### 6. Inkscape extension — 1–2 days

- [ ] `.inx` menu entry and a Python entry point calling this package.
- [ ] "Rebuild from design" without leaving Inkscape.
- [ ] Keeps the current two-window loop working; does not replace it.

### 7. Parameter window (PySide6) — 2–4 days

- [ ] Open/save design JSON, sliders per segment, width and sheet.
- [ ] Live rebuild through the same render path; no second geometry engine.
- [ ] Packaged separately so the CLI stays dependency-free.

### 8. Re-import and inverse fitting — 2–3 days

- [ ] Read a path, split it, fit clothoids, report the approximation error.
- [ ] Replace a section of an existing design with a fitted piece.
- [ ] No claim of an exact inverse; the error is the deliverable.

### 9. Packaging and CI — 0.5–1 day

- [ ] CI on macOS and Linux: build the dylib, run 68+ tests.
- [ ] Build cache keyed by file content, not absolute path (see Known issues).
- [ ] sdist/wheel that actually contains `clothoid_lab.backend` (fixed in
      `pyproject.toml`, untested as a build).

## Known issues

- `scripts/build-native.sh` names object files by absolute path, so its cache
  misses if the checkout moves. Correct but noisy.
- The script forces `DEVELOPER_DIR=/Library/Developer/CommandLineTools`. That
  tree is half-removed on this machine; `xcode-select` now points at Xcode.
  Builds still work, but the default should follow `xcode-select -p`.
- Fit-on-open relies on a `sodipodi:namedview` computed for the current window
  size. Resizing the window or changing the sheet needs `scripts/fit_view.py`
  again. `inkscape:zoom` is a factor (1.0 = 100%), not pixels per millimetre.
- The `g1` flag means "curvature jumps are intended". It does not distinguish a
  G1 point spline from a smoothed chain; a `kind` field would.
- The watcher is a foreground process started by hand; nothing restarts it.
- Stroke width scales with `--frame`, so a small drawing gets a heavy pen unless
  the design lowers `stroke`. Ribbon width does not scale independently.
- The `pyclothoids` backend has no G1/G2 fitting, projection or intersections;
  those features are compiled-backend only and say so.
- `out/play.svg`, `out/play-template.svg` and `out/play.json` are scratch files,
  not examples; the template was saved by hand in Inkscape.
- No CI, no linter, no coverage measurement.

## Out of scope, deliberately

`Dubins`, `Dubins3p`, `NURBS` conversion, AABB trees, Ipopt/Pipal and the
`GenericContainer` serializers are compiled but unused. They solve motion
planning, export and optimisation problems this tool does not have. Binding them
would add surface without adding a design capability.

## Incoming

The reverse-curve / `3125` brief arrived 2026-10-24 and is classified in
`docs/clothoid-grid-3125.md`. Its core construction is right and is now proved;
four of its numeric claims are wrong and one decision (what `3125` denotes) is
still open. Nothing from it is wired into the CLI yet.

# clothoid-lab handoff

**Updated:** 2026-10-29  
**Use `/fhandon` to resume, `/fhandoff` to refresh this file.** The commands are
project-scoped: open OpenCode in this repository to use them. They are not
global and do not appear in `grid-8` or `ornaments`.

## Objective

Turn clothoid-lab into a usable design tool with exact clothoid geometry, a
200 × 250 mm sheet, +y up, and class I/II cap families. A local MVP and a public
remote MVP now exist.

## Current state

- **Local:** `http://127.0.0.1:8000/` — Python stdlib server plus the macOS
  `.dylib`. Start with `.venv/bin/python web/server.py`. HTTP 200 at
  2026-10-29 (probe). Auth is unset locally, so the loopback server stays
  open; the public deployment requires the token.
- **Remote:** `https://<your-service>.run.app` — Cloud Run,
  project `<your-gcp-project>`, region `us-central1`, service
  `clothoid-web`, revision `clothoid-web-00006-zrx` (carried). HTTP **401
  without the token** at 2026-10-29 (probe); a thin app deploy takes
  ~30 s.
- **Access:** HTTP Basic with a shared token; every route except `/health`.
  Token in Secret Manager `clothoid-token`, local copy
  `~/.config/<app>/token` (outside the repo). `/api/render` is limited to
  60/min, burst 20, per client address; excess is 429 with `Retry-After`.
- **Remote limits:** min `0`, max `1`, 1 vCPU, 512 MiB, concurrency `2`,
  60 s timeout. The Cloud Run IAM policy still allows unauthenticated ingress;
  the application token is the gate.
- **Build split (done):** engine base `clothoid-engine:2026-10-26` built in
  6m43s and pushed; the thin app deploy took 30 s (revision
  `clothoid-web-00004-nwx`, commit `eb67f4c`). App deploys now upload ~100
  files and skip the C++ compiler.
- **Budget:** `$1/month` alert (`clothoid-lab guardrail`) at 50/90/100%; alerts
  do not stop spend. Re-confirmed against billing account
  `<your-billing-account>` at 2026-10-25 23:45 UTC (carried).
- **Parity:** carried — all seven comparisons passed at 2026-10-26 00:02 UTC
  (not re-run in the handoff).
- **Local tests:** 215 pass — **carried** from 2026-10-27; the tree is clean
  under `web/`, `clothoid_lab/`, `csrc/` and `tests/` at the 2026-10-29 probe.
- **Git:** HEAD `d2b49e3`; the handoff commit sits on top. The code tree is
  clean. `reference/` has only untracked images (`reference/1/`,
  `reference/hard/`, an `IMG_*` dump) and no tracked change at the 2026-10-29
  probe. `out/play-template.svg` is untracked.
- **Untracked user file:** `out/play-template.svg`; leave it alone.
- **Docs:** `docs/HANDOVER.md` is the durable reference;
  `docs/HANDOVER.html` is its browser mirror.

## What changed this session

- Added `web/` MVP: stdlib HTTP server, static page, JSON editor, SVG preview,
  report, presets/caps, SVG/JSON download.
- Added `Dockerfile` with Debian C++ build and `python:3.12-slim` runtime.
- Added `.dockerignore`, `.gcloudignore`, `tests/test_web.py`, `web/README.md`.
- Deployed the container to Cloud Run via Cloud Build.
- Set min 0 / max 1, concurrency 2, 1 vCPU / 512 MiB, 60 s timeout.
- Created the $1 budget alert.
- Added project-scoped, focused `/fhandoff` and `/fhandon` commands, modelled
  on the existing `handoff`/`handon` pattern in `grid-8` and `ornaments`.
- Added `scripts/check-parity.py`, which compares the local and remote served
  assets, presets/caps, SVG and report. It passes.
- Opened the local and remote apps in Chrome tabs as the shared starting base.
- Added a **global** `/focus` command (`~/.config/opencode/commands/focus.md`)
  that moves any session into this repo and surfaces `next-fhandoff.md` without
  starting work, so `/fhandon` is reachable after a restart from any directory.
  `/fhandon` and `/fhandoff` stay project-scoped on purpose: they are hard-wired
  to this repo and should not appear in `grid-8` or `ornaments`.
- Made `/fhandon` faster to follow: it now opens with one sentence naming the
  focused action, and it uses headless Chrome/CDP for browser checks instead of
  looking for the desktop Review pane or Safari.
- Hardened the phone layout in `web/static/style.css`: zero-minimum grid
  tracks, `min-width: 0` on selects/inputs/status, wrapping action buttons, and
  tighter 430px padding. Headless Chrome at 390 × 844 and 320 × 844 shows no
  overflow in any state (cap-14, `cap-pt-9`, all four presets, width error,
  report shown). The original clipping did **not** reproduce in Chromium, so
  the hardening targets intrinsic-width/Safari cases; confirm on a real phone.
- Deployed the CSS fix: revision `clothoid-web-00003-r4m`; remote measures
  390/390 at 390 × 844 with the same control geometry as local; parity passes.
- Phone check on the Samsung: right edge confirmed clean, 2026-10-26. The
  temporary tunnel was closed after the check.
- Split the image: added `engine/Dockerfile` (C++ build + runtime base),
  `cloudbuild.engine.yaml`, a thin app `Dockerfile` (FROM the engine base), and
  `.gcloudignore.engine`; app `.gcloudignore` now drops `vendor/`, `csrc/`, and
  `scripts/`. Engine base built in 6m43s; first thin deploy took 30 s
  (revision `clothoid-web-00004-nwx`); parity passed.
- Added shared-token access and quotas: HTTP Basic on every route except
  `/health`, token in Secret Manager `clothoid-token`, and a per-address
  render limit (60/min, burst 20). Deployed as revision
  `clothoid-web-00006-zrx`; 401 without the token, 200 with it. Added
  `tests/test_auth.py`.
- **W01 done:** added `clothoid_lab/piece.py` (`Piece`, `Trace`,
  `render_piece`), extended `svg.document(..., groups=...)` for several named
  traces, and added `tests/test_piece.py`. The visual proof is
  `docs/piece-model.html`, generated by `scripts/piece_sandbox.py`: one ribbon
  half, its two rails, its mirror, and an unmirrored guide.
- **W02 taxonomy.** Terminal is the umbrella; **cap** is a subset that closes
  the end without turning the stroke past **120°** (a tunable project choice,
  not a law). Caps: `butt`, `point`, `arc`, `round`. Tapers: `taper`, `cone`,
  `bulb`. A hairpin and the old wrapped bulb turn past the limit: *turned
  terminals*, not caps, and not built yet. `bulb` in the code is the Stage II
  width-law taper, not the wrapped ornament bulb.
- **W02 reopened.** Seven terminals now: `butt`, `point`, `arc` (5 mm dome),
  `round` (half-width dome), `taper` (four half-widths), plus `bulb` and `cone`
  on the two width laws recovered from the ornaments `stage-two` page
  (`w = ½(t(3−3t+t²)+12t²(1−t)³)` and `w = ½(1−(1−t)³)`, both G2 at the join).
  The old five are still cap geometry at either end of a ribbon. `Trace.terminals = (start, end)`
  takes a kind, a pair or a dict and round-trips through JSON; `render_piece`
  writes one named path per cap, reports each end with kind, reach and fold, and
  rejects a terminal on a folded ribbon or a trace without a width. `butt` adds
  no geometry, so W01 output is unchanged. `svg.document(..., linecap=...)` lets
  the piece ink use `butt` caps while the single-design default stays `round`.
  `docs/piece-model.html` gained the labelled terminal strip (seven rows).
- **Junction object:** `clothoid_lab/junction.py` — `Junction(corner,
  branch_end, trunk_end, radius, widths)`, `.build()` returns a `Piece`, a
  declared `Contact` and a report (angle, trim, arc length, G1 join, 1/r step),
  `.check()` returns the clearance report with the merge already declared.
  Tests: `tests/test_junction.py`.
- **Contacts are model data:** `Piece.contacts` round-trips through JSON and
  `piece_clearance()` uses it by default. `Contact` moved to
  `clothoid_lab/contact.py` to keep the import graph acyclic.
- **Junctions started:** `clothoid_lab/fillet.py` gives the tangent-arc fillet
  at a corner (`corner_fillet`), plus `fillet_span()` to trim two straight
  spans and insert the arc. It refuses a radius that does not fit, collinear
  edges and doubled-back edges. This is G1 by construction: curvature still
  jumps at the touch points, so a trunk needs the clothoid blend next.
  `arc_segment()` turns the fillet into a circular-arc `Segment` + anchor, so a
  filleted run can be a normal `Design`. Docs: `docs/JUNCTION.md`; tests:
  `tests/test_fillet.py`.
- **Principle cards:** `reference/principles.json` holds eight cards — four
  primals, four archetypes — each with a gesture paragraph, exactly three
  numbers and a "not this" list. `scripts/principles.py` rebuilds
  `docs/principles.html`; images attach by subject from `reference/manifest.json`
  (never hard-coded), so links cannot rot. `tests/test_principles.py` validates
  the cards, the corpus and the rendered page. Each primal card also carries a
  `check` block, and the tests assert the rendered grammar against it: segment
  count, maximum segment turn, maximum corner and end terminal. The board header
  links the page.
- **Primal first slice:** `clothoid_lab/primal.py` has one canonical grammar per
  element — earth (terraces with corners, taper), water (sweep and reversal,
  round), air (billowing arcs, round), fire (Euler tongue with a point). Render:
  `scripts/primal.py` → `docs/primal.html`; tests: `tests/test_primal.py`.
  These are ahead of the gate on purpose and are sketches, not the four studies.
- **Section and Bundle:** `clothoid_lab/section.py` gives the read model —
  `Section(s, spine, tangent, width, left, right)` sampled by arc length, with
  left = `(-t.y, t.x)`. `clothoid_lab/bundle.py` gives the design box: a named
  set of full lines with an internal clearance and a footprint (sheaf, fasces,
  capital, acanthus leaves, fleur halves). `Bundle.check()` measures members
  only; the box is for placement, not clipping.
- **W03 first slice:** `clothoid_lab/grammar.py` ports study 01 from
  `ornament_set.js` as clothoid segments — straight runs, circle arcs and the
  petal's Euler span exact — with `Segment.corner` carrying the tangent jumps the
  old chain allows. All 12 nodes match the original within **0.030 units** (its
  3125-lattice snap). `scripts/study_01.py` writes `docs/fleur-study-01.html`
  with the drawing and the node table. Not done: per-stroke terminals, the
  declared centre-seam contact, and studies 02–20.
- **Spiral parity:** `scripts/check-spirals.py` fits one clothoid per recovered
  cubic span (endpoints + tangents) and measures the worst distance to the drawn
  curve. All 586 Stage II spans fit. Median error per chord: `line` 0.00%,
  `euler` 0.01% (worst 0.12%), `arc` 0.02%, `logaesthetic` 0.01% (worst 0.16%),
  `member` 0.03%, `reflected` 0.03%. `hyperbezier` diverges as it must: 35.8%
  median, worst 78× chord. Writes `docs/spirals/parity.json`.
- **Spike exponent dial (2026-10-28):** `pythagorean-spiral` now takes
  `power` in `design.spiral/lobe/curl` — turns run `k**p`, the clothoid at
  p = 1 (frozen digest test proves the old curl bit for bit), and every
  integer p closes exactly because the reversal cancels the same integers.
  `--power` on the CLI. **Join/fork landed too:** `Spiral.knots()`, `fork()`
  (angle as triangle steps or quarter turns, never degrees) and `joined()`
  asserting exact point and vector equality; the explainer's branch figure is
  now drawn by them. **Rails landed too:** `ribbon.py` offsets a chain exactly
  (miter of rational lines) with a rational taper, and `docs/GALLERY.md` +
  `docs/gallery.html` put six studies on it -- catenary, drapery, Corinthian
  volute, violin scroll, acanthus, fleur-de-lis -- each a filled ribbon. The
  float hybrid landed (`hybrid.py`): exact plan, double ink, 20,000 chords in
  0.03 s, closure still exact; `docs/EXTREMES.md` tests a 90-degree leaf corner
  (exact cusp) and the angles the lattice can hit. **Placement started:**
  `place.py` rotates inside the rational group, fits a 200 x 250 page and emits
  integers; `docs/TRANSFER.md` carries the 36 caps onto the new curve (median
  0.44% gap) and reports that the 150 terminal ends have no frame stored. The
  cloud study is `pythagorean-spiral/docs/CLOUD.md` + `cloud.html`: a toned
  photograph and a toned fresco under four layers of exact ellipse billows;
  the edge filter is optical, the geometry is rational. The veil strength is
  solved from the artwork area (`solve_veil`): only the bottom layer covers the
  works, to 5 per cent total, and the upper layers keep their body and stay off
  the work. Settings in `pythagorean-spiral/docs/veil-settings.json`. The solve
  is analytic, so a rendered-contrast check is still wanted. 127 tests there. This is the exact **spine
  layer**, central to the curve work, not a spike — it is just not yet
  imported by `clothoid_lab` (promotion gate in
  `pythagorean-spiral/docs/HANDOVER.md`).
- **Span bridge:** `interpolate.design_from_spans(spans)` turns a recovered or
  grammar-produced cubic chain into a `Design`, one clothoid segment per span,
  marked G1. This is the entry point a W03 port consumes.
- **Spirals recovered:** `scripts/extract-spirals.py` pulls every `spine` path
  from the Stage II and LAC pages, keeps the page's own cubics and its
  `data-span` tag (`line`, `arc`, `euler`, `logaesthetic`, `reflected`,
  `hyperbezier`, `member`), and writes `docs/spirals/stage-two.json` (20 plates,
  90 spines) and `docs/spirals/lac.json` (31 plates, 31 spines) plus a gallery.
  Coordinates are page units with y down, recorded as found. Shared reading
  helpers now live in `scripts/recover.py`.
- **Clearance built:** `clothoid_lab/clearance.py` measures the minimum
  edge-to-edge gap between ink instances and lists crossings, allowing one only
  where a declared `Contact` covers it. Measurements carry a `2·tol` band, so
  the report says *violation*, *warning* or *pass* instead of pretending the
  last tenth of a millimetre is known. `render_piece()` was split into
  `build_piece()` + writer so drawing and measuring share one geometry build.
  Docs: `docs/CLEARANCE.md`; tests: `tests/test_clearance.py`.
- **Terminals recovered:** `scripts/extract-terminals.py` cuts the outline ends
  out of the two ornaments pages at their `L`/`Z` seams and writes
  `docs/terminals/stage-two.json` (20 plates, 88 ends),
  `docs/terminals/lac.json` (31 plates, 62 ends) and a gallery
  `docs/terminals/index.html`. The taper fraction is measured by nearest
  distance between the rails, not assumed: the medians are 17 per cent on
  Stage II and 18 on the LAC page.
- Added `docs/ornament-board.html`: **85 plates** (45 catalogue ornaments
  P21–P65, 27 class I caps P66–P92, 9 class II leaves P93–P101, 4 presets
  P102–P105), **26 work items** W01–W26 and **11 decisions** D01–D11. The
  twenty fleur studies (P01–P20) are the subpage `docs/fleur-studies.html`,
  defaulted to “Needs work”. The board has a beginner glossary, plain-language
  briefs, editable text per card, DeepSeek-pick sorting, priority/stage,
  drag/↑↓, notes, localStorage and JSON/order export.

## Risks / open decisions

1. **Accounts and roles are still absent.** The shared token (W11) and the
   per-address render limit (W12) protect the URL, but there are no named users,
   saved designs or audit trail. Rotate the Secret Manager version if the token
   leaks.
2. **Cold starts** at min 0 are roughly 1–3 s. Do not pay for min 1 unless a
   demo needs it; set it back to 0.
3. **Free-tier usage.** Stay within the monthly Cloud Run/Cloud Build/Artifact
   Registry allowances; the budget alert is only a warning.
4. **Large deploys (fixed).** App deploys are thin and skip the C++ compiler;
   the engine base must be rebuilt only when `vendor/`, `csrc/`, or
   `scripts/build-native.sh` changes. The base tag is pinned to `2026-10-26`.
   The Debian build is deliberate: the Ubuntu 24.04 artifact needs glibc 2.38
   and will not run on Debian bookworm.
5. **Caps are baked in.** New `out/caps/*.json` files need an app deploy (thin),
   not an engine rebuild.
6. **No persistence/accounts.** Designs live in the browser and are not saved.
7. **Reference tree is dirty and growing.** Untriaged images sit at `reference/`
   root, `reference/1/` and `reference/hard/`; the last hash/dedupe pass was
   2026-10-27. Nothing there is committed except the measured references and
   READMEs.

## Veil rebuilt on turn chains (2026-10-29, this session)

- **Two versions, both live on `docs/cloud.html`.** *v1* is the original veil:
  the same ellipse composition, now with the veil factor on every layer (the
  drawing used to give it to `bank` alone while the report gave it to all, so
  the top went opaque while the numbers said 5 per cent). *v2* replaces each
  ellipse with a turn-chain ribbon. The page carries both figures, both strips
  and the numbers side by side.
- **v1 is restored faithfully, including its under-shading.** The cloud read by
  shading, not by outline: every billow and crown had a darker under-lobe and a
  cream top. Those strokes were outside the opacity model; they are now a
  `shade` / `light` layer like any other, so the measurement counts them.
  v1's measured flaw is the original one: top row mean **0.54**, worst 0.72.
- **v2 is turn chains.** `design.lobe` (turns `k**p`, then the same integers
  reversed) through `ribbon.outline` with a rational taper: a closed rational
  polygon with pointed ends. Power dial = layer: haze p1, bank p2, billow p2,
  crown p3. 90 lobes from 30 puffs. Top row mean **0.07**, worst 0.28.
- **One model.** `pythagorean_spiral/veil.py` owns the geometry and the
  composite; `scripts/cloud.py` draws exactly those polygons.
- **2b: four standard patterns,** two on top (where the cloud meets the image)
  and two below, sampled and gated in `tests/test_veil.py`. v2 passes, v1 fails
  — that difference is the finding, not a bug.
- **2c: the slider.** One uniform layer of one cloud colour over the same four
  patterns, with `?veil=0.42` to set it from the URL. The number the operator
  picks there is the target the veil should be solved to; the model is not the
  authority on a design number.
- **The operator's number is 80 per cent opacity** (chosen on the 2c slider,
  now ranged 0-100 and sitting at 80). Both versions are solved to that peak,
  so the comparison is about *where* the density lands, not how strong it is.
  v1: top row mean 0.43, worst 0.61 — over the image. v2: top row mean 0.09,
  worst 0.47 — the peak is in the sky above the works. Same transparency,
  different geometry.
- **The gate reads the row mean** (how much of the image is covered), with a
  looser allowance for a single bad corner: top mean ≤ 0.25 (worst ≤ 0.50),
  bottom mean ≤ 0.12 (worst ≤ 0.30). v2 passes, v1 fails on the top mean.
- 139 tests pass. `scripts/veil_test.py` writes both versions' numbers to
  `docs/veil-test.json`.

- **Pixel truth is now measured, and it agrees with the model.** The analytic
  model was predicting the browser's compositing a second time; that duplication
  is what let the report and the picture drift apart. `scripts/veil_measure.py`
  now renders the veil over a black field and a white field in headless Chrome
  and recovers alpha exactly, per channel, from `a = 1 - (Rw - Rb)/255` --
  independent of the composite colour, edges and overlaps included. ~26 s.
  Measured vs model at the same factors: v1 top mean 0.461 / 0.428, v2 top mean
  0.120 / 0.131, peaks 0.84-0.85 / 0.80. Agreement is within ~8 per cent, so the
  original failure was the drawing/model split, not the arithmetic.
- **Still half-wired:** `docs/veil-measured.json` exists and is correct, but
  §2b's table and `tests/test_veil.py` still read the model numbers. The one
  remaining step is to make the measured block the reported truth and keep the
  model as the design aid (the operator asked for both, not one).

## Next move

**Wire the measured numbers in.** §2b's table gains a measured column beside the
model one, and the gate reads the measured values. The model stays in
`pythagorean_spiral/veil.py` as the design aid — it is fast and now provably
close — but nothing ships a number the pixels have not confirmed.

**v2 is still sparse where it counts.** Its measured peak is 0.85 but its canvas
mean is 0.04: the lobes are separate streaks, not a mass. More overlap (more
lobes per puff, or a larger `SCALE`), not a larger factor: the operator has
fixed the number at 80 per cent.

**Give the terminals a frame.** In `scripts/extract-terminals.py`, record the
seam's point and tangent beside each terminal's cubic spans (`anchor`,
`heading`), the way `out/caps` already carries an anchor. Then the 150 ends can
be attached with one affine call (`place.place`) and the transfer is complete.
No new curve work: the geometry exists; the missing datum is the frame.

**Deferred, not dropped: the canonical fleur.** Build `fleur_canonical()` from the measured fleur
reference (`reference/fleur/png/metrics.json`: aspect 1.43, fill 0.17,
symmetry 0.83), with exact clothoid segments, the band as a `Bundle`, terminals
per stroke, the centre seam declared, and a silhouette render beside the
numbers. Old study 01 stays as history; do not conform the other nineteen
until the silhouette is approved.

**Superseded, kept for context: the junction object, then W03.** The fillet exists; what is missing is the
junction itself — a small object carrying the corner, the clearance that must
survive through the crotch, the fillet or clothoid blend, the taper, and the
declared contacts, with a report that gives the join grades and the gore. The
recovered spirals (`docs/spirals/`) are its first test data: the S joints are
real joins that must come out G2 or be explained.

**Clearance and junction work**: a measured minimum gap between
strokes (the 5 mm local clearance), a crossing report that allows a crossing
only at a declared terminal, and a blend where a leaf meets a branch and a
branch meets the trunk.

**After W03/W04: the primal studies.** Fire, water, earth and air are a category
of their own (`docs/PRIMAL.md`), gated on a finished framework: twenty fleur
studies with node parity, turned terminals, junctions with measured gores,
`Section` as a first-class model, and a web route. Order within it is earth →
water → air → fire, because fire needs the turned terminals. The archetypes
(fleur, acanthus, palmette) follow the primals.

**W03 — fleur grammar.** Port the old half-stroke grammar from
`ornaments/assets/ornament_set.js` (foot, tail, band, petal, lance, with its
lines, 5ⁿ arcs and Euler spans) onto `Piece`/`Trace` from W01 and the terminals
from W02. First target **P01**, study 01, at its old parameter values; keep the
report (spans, joins, copy error, fold) and no fill. Then W04 the twenty sets.

## Tooling notes

- `--headless=new` hangs Chrome on this machine; `--headless=old` captures
  screenshots fine. Prefer DevTools Protocol over CLI flags for emulation and
  measurement.

## Important paths and commands

| Path | Purpose |
|---|---|
| `web/server.py` | stdlib server and `/api/render` |
| `web/static/` | MVP page, JS, CSS |
| `clothoid_lab/piece.py` | `Piece`/`Trace` multi-trace model and renderer |
| `clothoid_lab/terminals.py` | `butt`, `point`, `arc`, `round`, `taper` cap geometry |
| `tests/test_piece.py` | piece model, mirror, round-trip tests |
| `tests/test_terminals.py` | each terminal, extension, fold and width rejection |
| `scripts/piece_sandbox.py` | builds `docs/piece-model.html` |
| `docs/REVIEW.md` | senior review: page model, PDF, outline, ids, CI |
| `docs/PHILOSOPHY.md` | what a glyph is: parts, full lines, sections, joints |
| `docs/PRIMAL.md` | primal ornaments: the four elements, their gate and order |
| `docs/piece-model.html` | W01/W02 visual proof: traces, rails, mirror, terminal strip |
| `Dockerfile` | thin app image; starts FROM the engine base |
| `engine/Dockerfile` | engine base: C++ build + Python runtime + `.so` |
| `cloudbuild.engine.yaml` | build and push the engine base |
| `.gcloudignore` | small app-only Cloud Build upload |
| `.gcloudignore.engine` | engine-base build context |
| `scripts/check-parity.py` | local/remote parity smoke test |
| `tests/test_web.py` | web API tests |
| `tests/test_auth.py` | token auth and rate-limit tests |
| `docs/HANDOVER.md` | durable handover |
| `docs/HANDOVER.html` | HTML mirror |
| `docs/BACKLOG.md` | execution detail for W01–W26 |
| `docs/ornament-board.html` | visual board: 85 plates, 26 work, 11 decisions |
| `docs/fleur-studies.html` | subpage: the twenty fleur studies, P01–P20 |
| `scripts/board/` | board generator, template, extractors and README |
| `next-fhandoff.md` | two-line focused pointer |
| `.opencode/commands/fhandoff.md` | write the focused handoff |
| `.opencode/commands/fhandon.md` | resume from it |
| `~/.config/opencode/commands/focus.md` | global: move session here, show focus |

```sh
cd /Users/thomaskelly/developer/clothoid-lab
.venv/bin/python -m unittest discover tests
.venv/bin/python web/server.py
# with the local server up and the remote reachable:
.venv/bin/python scripts/check-parity.py
```

```sh
# engine base: only when vendor/, csrc/, or scripts/build-native.sh changes
gcloud builds submit --config cloudbuild.engine.yaml \
  --ignore-file=.gcloudignore.engine .

# app: every UI/Python change (thin upload, no C++ compile)
gcloud run deploy clothoid-web --source . --region us-central1 \
  --allow-unauthenticated --memory 512Mi --cpu 1 --concurrency 2 \
  --min-instances 0 --max-instances 1 --timeout 60 --port 8080 \
  --set-env-vars HOST=0.0.0.0 --quiet
```

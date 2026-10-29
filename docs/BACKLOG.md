# Backlog — the ornament pass

The **order** is chosen on the visual board: [`docs/ornament-board.html`](ornament-board.html).
The twenty fleur studies are a **subpage** — [`docs/fleur-studies.html`](fleur-studies.html) —
because they are a working set, not finished plates. The board carries **85
plates** (45 catalogue ornaments, 27 caps, 9 leaves, 4 presets), **26 work
items** W01–W26, and **11 decisions** D01–D11.

Labels are stable: **P01–P20** fleur studies (subpage), **P21–P65** catalogue
plates, **P66–P92** class I caps, **P93–P101** class II leaves, **P102–P105**
presets, **W01–W26** work items, **D01–D11** decisions. The board is the
authority on order; this file keeps the execution detail.

Open the board, rank, tag, then copy the order back into the session.

## Rules

- One item at a time; one verify; one commit. Do not bundle.
- Keep the public URL private; auth/rate limiting stays deferred.
- Never touch `out/play-template.svg`.
- Do not change `vendor/` or the cap JSON.
- If an item needs a taste or product decision, put the question under it and
  stop; do not invent. Record the answer on the board under D01–D06.
- If a verify fails twice for the same reason, stop and write the reason.
- Deploy only where marked; app deploys are thin now (about 30 s).
- Tests must stay green: `.venv/bin/python -m unittest discover tests` (96 now).

## Done

- **M0 — image split.** Engine base `clothoid-engine:2026-10-26` plus a thin app
  image. First app-only deploy took 30 s; revision `clothoid-web-00004-nwx`;
  parity passed. Commit `eb67f4c`.

## W01 — Piece model — done 2026-10-26

A piece is several named traces: the half-stroke, the band, the two parallels,
then the mirror. Implemented in `clothoid_lab/piece.py`:

- `Piece` and `Trace`: named chains, layer, optional width, piece mirror with
  per-trace override.
- `render_piece()` builds every trace and writes one SVG through
  `svg.document(..., groups=...)`.
- Tests: `tests/test_piece.py`; visual proof: `docs/piece-model.html`
  (`scripts/piece_sandbox.py`).
- The single-design CLI path is unchanged.

**Verify:** 110 tests pass; the sandbox SVG opens.
**Commit:** `feat: add a piece model for several traces`

## W02 — Terminal vocabulary

- Point (corner), arc (small 5ⁿ radius), round (half-width), taper (converging
  rails). Apply to open trace ends; report the terminal like a join.
- Keep the current blunt join as `butt` so nothing regresses.
- Tests: each terminal on a straight ribbon; a fold/negative-width rejection.

**Verify:** tests + a one-page terminal strip.
**Commit:** `feat: add point, arc, round and taper terminals`

## W03 — Fleur grammar

- Port the old half-stroke grammar from `ornaments/assets/ornament_set.js`:
  foot, tail, band, petal, lance, with its lines, 5ⁿ arcs and Euler spans.
- Use W01 for the piece, W02 for the ends. The mirror is W01's.
- First target: **P01**, study 01, at its old parameter values.
- Keep the report: spans, joins, copy error, fold. No fill.

**Verify:** `P01` renders; its joins are the old grades or better; tests.
**Commit:** `feat: port the fleur grammar to clothoid spans`

## W04 — Twenty parameter sets

- Port all twenty option sets from `ornament_set.js`; generate **P01–P20**.
- CLI: one piece by id, plus a contact sheet.
- Each piece carries its prompt and its measured error.
- This is the first “all the ornaments” milestone.

**Verify:** 20 SVGs, 20 prompts, no failed joins; contact sheet reviewed.
**Commit:** `feat: generate the twenty fleur studies`

## W05 — Stage II: eight storeys

Monstrance, pillar, flower, crib, church, ship, crucifix, tree. Reuse the part
library; no new curve grammar unless a piece demands it.

**Verify:** 8 pieces, one contact sheet, joins reported.
**Commit:** `feat: add the eight Stage II storeys`

## W06 — Stage III: six analogies

Building, body, plant, eucharist, communion of saints, altar. Each piece is one
analogy; every part named.

**Verify:** 6 pieces, one contact sheet, joins reported.
**Commit:** `feat: add the six Stage III analogies`

## W07 — Stage IV–V: boteh and scroll

The bent leaf on the round back, then the scroll and the volute. The paisley
grammar and the spiral units.

**Verify:** the boteh family and the scroll/volute set render; fold reported.
**Commit:** `feat: add the boteh and scroll families`

## W08 — Drapery and church decoration

Hanging cloth, folds, the curtain and the corridor. The fold report is the
design instrument; a fold must be chosen, not discovered.

**Verify:** one drapery study at a stated width, fold ranges printed.
**Commit:** `feat: add the drapery studies`

## W09 — Sliders per family

Tune the chosen grammar's parameters in the browser. The JSON stays the source
of truth; the sliders are a layer over the family parameters, not raw segments.

- Depends on W03/W04.
- Extend the headless layout gate to the new controls.

**Verify:** headless Chrome at 390 px; a slider changes the SVG; tests.
**Commit:** `feat(web): add sliders for the ornament families`

## W10 — Persistence and share

Remember a design across reloads and put it in a link. Later than the geometry,
but cheap. Depends on nothing.

**Verify:** reload restores; a `#d=` link restores; tests.
**Commit:** `feat(web): remember and share designs`

## W11–W26 — the supporting work

Each label is on the board with its full plain-language brief. The short form:

- **W11 Auth and access — done 2026-10-26.** Every route except `/health`
  requires HTTP Basic with a shared token; token in Secret Manager
  `clothoid-token`. Accounts and roles remain later.
- **W12 Rate limiting and quotas — done 2026-10-26.** `POST /api/render` is
  limited to 60/min, burst 20, per client address; 429 with `Retry-After`.
  In-process, resets on a cold start.
- **W13 Mobile and touch.** 16 px fields, 44 px targets, collapsible JSON,
  pinchable preview, report collapsed. Test the Samsung in two browsers.
- **W14 Gallery and browse.** Find a plate by eye, not by ID; home of the
  reference library.
- **W15 Undo and history.** Snapshot the design on render; undo/redo the design,
  page and width.
- **W16 Accessibility and keyboard.** Labels, focus order, visible focus, safe
  shortcuts. The preview and JSON editor are the gaps.
- **W17 Onboarding and help.** A first-run guide that does not start in JSON.
- **W18 CI on push.** GitHub Actions: unit tests + headless layout gate.
- **W19 Deploy, rollback, cache.** One deploy, one rollback, a smoke check, the
  previous revision one command away.
- **W20 Monitoring and alerts.** Uptime, error/latency alerts, revision note in
  the handoff, usage beside the budget alert.
- **W21 Backup and restore.** Repo, caps, ornament sources and saved designs in
  a second copy.
- **W22 Regression suite.** Fixed cap/preset/ornament corpus + screenshots at
  320/390/1280.
- **W23 Performance budget.** Render, page, deploy and cold-start numbers
  measured and recorded.
- **W24 Docs sync automation.** Counts, links and command names checked before
  `/fhandoff`; board generated from one data file.
- **W25 Reference library.** The 58 designs and 72 ornament SVGs, browsable but
  separate from the work board.
- **W26 Export paths.** SVG + PNG now; OTF/Glyphs when the shapes are stable.



## Blocked

- **Accounts and roles.** The shared token (W11) and render limit (W12) are in
  place; named users, saved designs and audit remain a later decision.
- **Parametric caps.** Needs a product decision about which cap family is worth
  parameterising; do not invent one.

# Spec

What this tool is for, what it refuses to do, and the numbers that decide
whether it has done the job. The original brief is preserved in the lineage of
this file; what follows is the version the code is held to.

## Purpose

Generate clothoid chains with numerical control, offset them into ribbons, and
write SVG that Inkscape opens as ordinary cubic Bézier nodes for a human to
edit.

## Goals

- Chains of clothoids with stated start curvature, curvature rate and arc
  length, joined G2 unless the design says otherwise.
- Parallel rails at signed distances, for ribbons and thickness.
- A G1 clothoid spline through a list of points, for when the shape starts as a
  sketch rather than a curvature list.
- A G2 clothoid spline through points, with prescribed end tangent and
  curvature, and optional closure.
- Trim, reverse and G2-connect existing chains, so pieces can be spliced without
  refitting them.
- A measured fit. Every cubic says how far it sits from the true curve.
- Plain absolute-cubic SVG, millimetre units, **positive y up**, no transform,
  no exponent notation, four decimals by default.
- A JSON design that survives the round trip, carried inside the SVG.
- Light enough to run on an eight gigabyte machine beside Inkscape.

## Non-goals

- Replacing Inkscape as the path editor.
- Real-time freehand drawing.
- A Bézier handle editor of our own.
- A polished multi-platform package, for now.

## Decisions taken

1. **Engine: Bertolazzi's Clothoids, compiled from the vendored source.** It
   carries the exact parallel curve, the G1 fitter and the trimming that would
   otherwise be ours to write and get wrong. Its licence is BSD-2-Clause, so our
   code is MIT and can move between projects.
2. **The wheel is a cross-check, not the engine.** `pyclothoids` carries the same
   source, so it cannot vouch for the mathematics; it does catch what actually
   breaks in a ctypes wrapper. It is optional and off the default path.
3. **Offsets are emitted, not clipped.** Where a rail folds, `|d * kappa| >= 1`,
   the fold is drawn and its arc-length range and margin are printed. A fold is
   often the point of the shape; an unannounced one never is.
4. **No path library.** `M` and `C` are string formatting. A library here earns
   nothing and costs a dependency.
5. **No GUI yet.** The engine, the fit and the writer come first. The parameter
   window is the last piece, not the first.
6. **The tolerance decides the node count.** Not an angle rule, not a fixed
   count. `--split` sets how many pieces a span is redivided into.
7. **G1 fitting is the library's, surfaced as a design.** The two-point fit and
   the spline through points come from Clothoids (`build_G1`), not a second
   implementation. A fitted spline is written out as ordinary segments with
   explicit curvature, marked `g1`, so its curvature jumps are reported as the
   fit rather than failed as a defect.
8. **Splicing uses the library's cut and connectors.** Trimming and reversing
   are the library's own operations, so a cut piece is the same arcs, not a
   refit. Joining uses `G2solve2arc`, `G2solve3arc` or `G2solveCLC` at the seam.

## Acceptance numbers

These are the promises, and each has a test.

- **Accuracy.** The fit error is measured as the distance from the cubic to the
  curve, minimised along arc length. It is reported per run and must not exceed
  `--tol`, default 0.02 design units (millimetres at 1:1; a frame scales it with
  the drawing). On failure the exit status is 1.
- **Continuity.** A join is G2 when the curvature jump is below 1e-9 per unit
  and the tangent corner is zero. Any jump or corner is printed. Presets must
  be G2.
- **Engine fidelity.** The engine matches an independent Simpson integration of
  the clothoid's defining integral to 1e-9 mm.
- **Rails.** A rail is the library's exact parallel curve, refitted, and reports
  its worst deviation. A zero-distance rail reproduces the spine inside tolerance.
- **Backend agreement.** The compiled library and the wheel must agree on
  position, tangent, curvature and offset to 1e-9 over 41 points on every preset.
  That is the test the ctypes wrapper earns.
- **Path data.** No exponent notation, no transform, **positive y up** (the
  writer flips SVG's y-down at output), no coordinate more precise than the
  stated decimals, and no non-finite number.
- **Round trip.** The design JSON recovered from a written SVG equals the design
  it was written from.
- **The 45 degree rule is not assumed.** Measured: two spans over a 90 degree
  turn on a 40 mm segment deviates 0.024 mm, over the default tolerance. Three
  spans give 0.0036 mm; four give 0.0009 mm. The fitter measures rather than
  counts degrees.
- **G1 interpolation.** A fitted spline passes through every supplied point
  within 1e-9 mm, and its direction at each point matches the fitted or supplied
  direction within 1e-9 rad. A two-point fit meets both prescribed directions
  within 1e-9 rad.
- **G2 interpolation.** A G2 spline passes through every point within 1e-9 mm,
  every join is G2, and a closed spline returns to its start within 1e-9 mm in
  position and direction.
- **Splicing.** A trimmed design is the original between the two arc lengths,
  within 1e-9 mm; a reversed design starts where the original ended. A G2
  connector reaches both poses within 1e-9, and a joined design is G2 at the
  seams and lands on the second design's end.
- **G1 is reported, not disguised.** A spline design is marked `g1`; its
  curvature jumps are printed and the run succeeds when the fit is inside
  tolerance. A jump from a hand-set `kappa0` without the flag still fails.

## The model

A design is an anchor `{x, y, angle}` and a list of segments.

```json
{"kd": 0.0019635, "length": 40.0, "kappa0": null}
```

`kd` is curvature rate in 1/design-unit², `length` is arc length in design
units, and `kappa0` is the curvature the segment starts from, with `null`
meaning "continue from the previous end" and therefore G2. One design unit is
one millimetre at 1:1 (`--page`, or an automatic sheet); `--frame` multiplies
the design by a scale to fill the sheet. A number is honoured as given and the
mismatch against the previous end is printed.

A segment may also carry `"corner"` in radians, a tangent jump at its start.
Curvature can remain continuous across a corner; the report counts corners
separately from curvature jumps.

Rails are `offsets`, a list of signed distances in design units, or `--width`,
which adds two at half width. The frame scales them with the drawing.

A design fitted through points carries `"g1": true`. It marks the curvature
jumps at the joins as the fit, so the report prints them without failing the
run. A hand-set `kappa0` without that flag is still a defect.

## Roadmap

1. Cut the span count from the turn as a seed, then refine by error. Measured
   today, bisection already reaches tolerance in three spans per segment on a
   quarter turn, so this is a tidy-up rather than a saving.
2. Terminals: tapered and round ends. The ribbon outline still closes with a
   straight join.
3. The Inkscape extension: an `.inx` menu entry and a Python entry point calling
   this module, so the tool is integrated rather than exported to.
4. The PySide6 parameter window with JSON open and save, per the original brief.
5. Re-import: read a path back, replace a section with a fitted clothoid, and
   report the approximation error rather than implying a perfect inverse.

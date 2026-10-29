# Offsetting and stroke outlines

Two related jobs: **offset a curve** by a distance (a rail), and **turn a
stroke into an outline** (a closed shape that can be filled). We do the first
with exact clothoid offsets and approximate them with cubics; the second we do
not do at all yet.

## The core difficulty

The exact offset of a cubic Bézier is not a Bézier of any fixed degree. Its
arc-length-parameterised form involves the offset of both coordinates, and its
degree grows. Every implementation therefore chooses an approximation and an
error measure.

## How the sources handle it

- **`repos/linebender/kurbo/kurbo/src/offset.rs`** — offsetting a path by a
  distance, in the same spirit as ours: offset the source, fit, refine where the
  error is large.
- **`kurbo/kurbo/src/stroke.rs`** — stroke expansion: rails plus joins (miter,
  round, bevel) plus caps, producing a fillable outline. This is the reference
  for anything that needs filled plates rather than stroked ribbons.
- **`kurbo/kurbo/src/mindist.rs`** — minimum distance between a point and a
  curve; the building block of clearance (`04-clearance-and-crossings.md`).
- **`kurbo/kurbo/src/simplify.rs`, `fit.rs`** — curve simplification and fitting;
  useful when the sampled offset has too many points.
- **`kurbo/polycool/src/yuksel.rs`** — Yuksel's polynomial root finding, the
  accurate way to intersect two cubics.
- **`repos/paperjs-offset/src/offset_core.ts`** — the practical recipe: offset
  each segment, insert join geometry, split at high-curvature points, then
  remove the loops where the offset outruns the curvature radius.
- **`repos/cubic-bezier-offsetter`** — the smallest readable cubic offset; good
  for checking a normal calculation.
- **`repos/simoncozens/curve-offsetting`** — no licence file, so read the idea
  only: offset by **minimising the error between the desired distance and the
  actual distance** over the curve, using the Tunni simplification (a cubic with
  straight handles). It also covers variable thickness, which is our terminal
  width law.

## What we already do

`clothoid_lab/offsets.py` samples the exact offset through the engine, splits
where the fit is worst, and fits cubics until each rail is inside tolerance. The
control-point arm is bounded at four times the chord (Levien's rule, adapted);
a clamped span is counted in the report. A rail that folds is reported, not
hidden, because a fold means the offset exceeded the local radius of curvature.

## What the sources add

1. **Join construction.** At a corner in a stroke, the outline needs a join:
   round, miter (with a limit), or bevel. Our terminals are the *end* analogue;
   joins are the *middle* analogue and we have no vocabulary for them yet.
2. **Loop removal.** Offsetting a concave corner produces a self-intersecting
   loop; the outline must cut it at the cusp. Our fold report detects the region
   but does not excise it.
3. **Error measures.** Kurbo measures offset error by sampling the distance from
   the candidate to the true offset; that is stricter than fitting the sampled
   points and is the measure to copy if a rewrite happens.
4. **Variable width.** A width law `w(t)` along the spine, with the outline
   rails at ±w, is how `bulb` and `cone` are already expressed. The Stage II
   note is the specification: `w` and its first two derivatives vanish at the
   join, so no step is visible.

## Verdict

Highest-value file in the whole library: `kurbo/kurbo/src/stroke.rs`. Read it
before writing any fillable outline or join vocabulary.

# Clearance and crossings

The rule we want, stated so it can be tested:

> Two strokes keep at least **clearance** `c` between their edges, everywhere,
> and cross nowhere except at a **declared terminal**.

This note is about measuring both halves of that sentence.

## Words

- **Clearance** — edge-to-edge gap. The enforced number (5 mm local).
- **Spacing** — centreline-to-centreline distance. `spacing = clearance + (w₁ + w₂)/2`
  for two ribbons of width `w₁`, `w₂`.
- **Counter** — the white shape the clearance creates. The bulb beside a
  terminal is a counter.
- **Contact** — a crossing or touch that a terminal declares legal.

## Measuring clearance

Distance between two curves is the minimum over segment pairs of the distance
between two cubic segments. Two ways:

1. **Exact-ish.** Minimise the distance between two parametric cubics. Kurbo's
   `mindist.rs` does point-to-curve; curve-to-curve is the same minimisation with
   the other curve's parameter as a second unknown, solved by Newton from a set
   of seeds. Robust, more code.
2. **Sampled, with a margin.** Flatten both rails to polylines at tolerance `ε`,
   then take the minimum segment-to-segment distance:

       d(P₁P₂, Q₁Q₂) = min over segment pairs

   and require `measured ≥ c + ε_a + ε_b`. The margin is the point: a polyline is
   never further from its curve than `ε`, so the sampled minimum can understate
   the true minimum by at most the two flattening errors. Reporting the sampled
   number without that correction is how clearance bugs get shipped.

For a piece this is `n²` over segments, which is tens of thousands of pairs —
fine. Above a few hundred spans, put the segments in an AABB tree (the engine
already has one internally for intersections) and query near pairs only.

**Shortcut for a pass/fail check:** buffer one ribbon's outline by `c` and test
overlap with the other (`Clipper2`, `clipper.offset.h`). That is conservative and
cheap, but it answers yes/no, not "by how much, and where". We want where.

## Measuring crossings

A crossing is an intersection point of two rails (or two spines) that is not a
declared contact. Two levels:

1. **Polyline level.** Segment-segment intersection after flattening. O(n²) or a
   sweep. Gives the point, and is enough for a report.
2. **Curve level.** Cubic-cubic intersection via `kurbo/polycool` (Yuksel's
   method), or clothoid-clothoid intersections via the engine's `cl_intersect`,
   which already accepts iso-offsets and is tested in `tests/test_curves.py`.

Deduplicate: a crossing usually appears in several adjacent segment pairs, and
a tangency can appear as zero or two intersections depending on rounding.

## Declaring a contact

A terminal contact is legal when the two curves meet **at** an endpoint that is
declared, within tolerance. Model it as a set of declared contact points, each
with a radius:

    contact = (piece, trace, end, point, radius)

Then the rule is: every intersection must lie within some contact radius, and
the number of intersections at that contact must be explicable (one for a
T-joint, two for a crossing through a bulb, none for a gap). Anything else is a
violation with a location.

## What is already in the tree

- `cl_intersect` — clothoid pairs, iso-offsets, max-hit cap, error codes.
- `Curve.project(x, y)` — point distance, for "is this crossing near an end".
- `bbox_iso` — bounding box of an offset chain, for cheap rejection.
- `rail` reports `folds` and `margin = min_radius − |offset|`, which is a
  *self*-clearance statement: a rail folds exactly when the ribbon is wider than
  the local radius of curvature.

## Failure modes to test

- Two parallel rails 4.9 mm apart (fail) and 5.1 mm (pass).
- A taper that closes to a point: clearance at the tip is zero by design, so the
  tip must be a declared contact, not a violation.
- A bulb that swells into a neighbouring stroke: clearance decreases *inside*
  the bulb, so sampling only the joins misses it.
- Tangency: exactly `c`, and near-tangency with flattening error on both sides.
- A ribbon whose own two rails cross (fold) — caught today by the fold report.

## Verdict

No library does the whole rule. Take the distance maths from `kurbo`
(`mindist.rs`, `polycool`), the conservative buffer trick from `Clipper2`, and
the intersection list from the engine we already call. The declared-contact
model is ours.

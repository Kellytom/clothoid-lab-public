# Clearance and crossings

`clothoid_lab/clearance.py` answers one question about a drawing:

> Does the ink keep at least **5 mm** between strokes, and does it cross
> anywhere it was not allowed to?

It is a measurement, not a constraint solver. Nothing moves to satisfy it; the
report tells you where the drawing fails and by how much.

## Vocabulary

| Word | Meaning here |
|---|---|
| **clearance** | the minimum edge-to-edge distance the design must keep |
| **spacing** | centreline distance; `clearance + (w₁ + w₂)/2` for two ribbons |
| **counter** | the white shape the clearance creates (the bulb beside a terminal) |
| **contact** | a declared place where two strokes may touch or cross |
| **instance** | one trace, or the mirror of one; ink that belongs together |
| **ink** | rails and terminal caps. Spines are construction lines and are excluded by default |

## Quick start

```python
from clothoid_lab.clearance import Contact, piece_clearance

result = piece_clearance(piece, clearance=5.0, tol=0.05)

if not result["ok"]:
    for bad in result["violations"]:
        print(f"{bad['a']} / {bad['b']}: {bad['distance']:.2f} mm "
              f"({bad['shortfall']:.2f} mm short) at {bad['at']}")
```

Allowing a legal junction where a leaf meets a branch:

```python
result = piece_clearance(
    piece, clearance=5.0,
    contacts=[Contact((12.0, 0.0), radius=2.5,
                      a="ink/leaf", b="ink/branch")],
)
```

`result` is a plain dict: `ok`, `min`, `violations`, `warnings`, `crossings`,
`disallowed`, `clearance`, `tolerance`, `margin`, plus `piece` and `fit_ok` when
called through `piece_clearance()`.

## How the decision is made

Flattening introduces a known error: a polyline is within `tol` of its curve, so
the measured minimum can be up to `2·tol` below the true one. The report keeps
that honest instead of rounding it away:

| Measured distance | Verdict |
|---|---|
| `< clearance − 2·tol` | **violation** — definitely too close |
| `clearance − 2·tol … clearance + 2·tol` | **warning** — inside the uncertainty band |
| `> clearance + 2·tol` | pass |

At `clearance = 5`, `tol = 0.05`: violation below 4.9, warning from 4.9 to 5.1.
The warning band is not noise — it is the only responsible answer when the
measurement cannot resolve the last tenth of a millimetre.

## Junctions waive clearance inside their footprint

A junction is not a violation; it is a merge. A `Contact` therefore carries
`waives_clearance=True` by default: a pair closer than the rule is accepted when
**both strokes pass within the contact's radius**, and the pair is listed under
`merged` rather than dropped. Testing the footprint rather than one sampled
closest point matters: the minimum between two parallel rails is a whole line,
and the first point found is arbitrary. The gore — the narrowing gap just outside
the footprint — is still measured normally, which is the point: the waiver has
an edge, and the edge is where the drawing must start respecting the rule again.

Pass `waives_clearance=False` for a contact that only permits a crossing while
still demanding the gap.

## Why instances matter

A 6 mm ribbon has two rails 6 mm apart and a cap that meets both at the tips.
Measuring those as separate strokes would call every piece a violation. Groups
are therefore compared only **between** instances (`Group.instance`), never
within one. The mirror is its own instance, so the gap between a trace and its
reflection is measured, which is what a fleur half demands.

`piece_clearance(..., roles=("rail", "cap"))` is the default. Spines are
excluded because they are construction geometry and usually closer together
than the ink; pass `roles=("spine", "rail", "cap")` to include them.

## API

| Function | Purpose |
|---|---|
| `piece_clearance(piece, ...)` | build the piece once, measure the ink, return the report |
| `measure(groups, ...)` | the same judgement on groups you built yourself |
| `Contact(point, radius, a=None, b=None)` | declare a legal touch, optionally for one pair of instances |
| `flatten(spans, tol)` | polyline for a span chain, within `tol` |
| `segment_distance(p1, q1, p2, q2)` | closest points of two segments (Ericson §5.1.9) |

## Algorithm

1. **Build once.** `build_piece()` returns `Group` objects — spine, rail or cap,
   tagged with their instance — and `render_piece()` writes SVG from the same
   list. Measurement and drawing cannot drift apart.
2. **Flatten.** Each cubic is split by de Casteljau until its control points are
   within `tol` of the chord (or a depth cap of 18 is hit). The bound is
   conservative; it never reports a polyline further from the curve than `tol`.
3. **Compare instances.** For each pair, minimum segment-to-segment distance.
   The bounding boxes are used only to skip the crossing scan when the boxes are
   disjoint; the distance is always computed so `min` is the true minimum.
4. **Find crossings.** Segment intersections, including collinear overlap.
   Touching endpoints count as crossings: that is how an undeclared contact
   looks. Each is allowed only if a `Contact` covers it.
5. **Classify.** Violations, warnings, allowed and disallowed crossings.

Complexity is `O(n·m)` in flattened segments per instance pair. A piece with a
few hundred spans measures in milliseconds; a whole catalogue would want an
AABB index, and the engine already has one internally.

## Limits and non-goals

- **No self-intersection test within an instance.** A ribbon's own rails are
  checked elsewhere: `build_rail()` reports `folds` and a `margin`, and a
  terminal refuses a folded ribbon.
- **No curvature or tangent check.** Gaps are distance only. Smoothness is the
  job of `engine`'s join report.
- **Contacts are declared, never inferred.** A drawing that happens to touch is
  a violation until someone says it is a junction.
- **Clearance is per pair of instances.** Three-way crowding is reported as the
  three pairwise minima, which is sufficient for the rule.
- **Polyline geometry only.** Curvature extrema between sample points can hide a
  sub-tolerance dip; choose `tol` below the smallest feature you care about.

## Tests

`tests/test_clearance.py` — 26 cases: segment distances (parallel, crossing,
collinear, endpoint, degenerate), flattening bound, pass/warn/fail bands, the
same-instance exclusion, mirror gap, disallowed crossing, declared contact,
named contacts, argument validation, report shape, clearance waivers inside and outside a contact.

## Where this goes next

A junction object (leaf → branch → trunk) will declare its contacts through
this module, and the gore is read directly from the warning band: the set of
points where two strokes come within `clearance` of each other.

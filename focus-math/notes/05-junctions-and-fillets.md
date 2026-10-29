# Junctions and fillets

A junction is where one stroke meets another: leaf to branch, branch to trunk.
The eye reads it as smooth when the meeting curve is tangent to both sides, and
as intentional when there is a small nick instead. The provenance is mixed:
botany calls the swelling a **branch collar**, architecture calls the thickening
a **haunch**, roads call the triangular white between diverging carriageways a
**gore**.

## The simple fillet

Between two straight edges meeting at an interior angle `θ`, a circular fillet
of radius `r` touches each edge at distance

    T = r / tan(θ/2)

from the corner, and the arc subtends `π − θ`. This is the whole of the classic
2D fillet. For a line and a circle, or two circles, the touch points come from
offsetting each primitive by `r` and intersecting the offsets; that construction
is the one every CAD sketcher uses (SolveSpace, FreeCAD Sketcher — read, do not
copy; both are GPL/LGPL).

A circular fillet is **G1**: tangent continuous, curvature jumps from 0 to `1/r`
at each touch point. That jump is visible at large scale, which is why road and
type design both prefer a transition curve.

## The clothoid junction (G2)

A clothoid between two elements can match tangent **and** curvature at each end.
With curvature continuity at both ends the problem is a three-parameter fit; the
engine already implements several constructions (`cl_g2_connect`, with a method
selector, and `build_G2` in the vendored source). This is the right tool when a
branch leaves a trunk and the joins must not show a curvature step.

## Spiro

`repos/raphlinus/spiro` is Levien's interpolating spline built from spiral
segments: control points say *through this point, this tangent, this curvature*,
and the solver produces a G2 chain. It is the closest public prior art to
"draw a leaf, a branch and a trunk as one smooth skeleton", and it is what
FontForge uses for exactly this kind of stroke work. Licence Apache-2.0, so the
algorithms are readable without contamination.

The trade-off: Spiro solves a global system, so a local change moves the whole
curve. Our `Piece` model is local — each trace is its own clothoid chain. A
junction model should keep locality: a fillet span inserted between two existing
traces, not a global re-solve.

## What the junction needs from the clearance model

The gore is a *shape of the gap*, so it cannot be designed before clearance can
be measured. Given two strokes and a minimum clearance `c`, the gore is bounded
by the offsets at `c` from each stroke. The bulb at a terminal is the same idea
in the other direction: a width law that swells when the two sides separate.

Practical parameters for a junction object:

| Parameter | Meaning |
|---|---|
| `angle` | interior angle between the two strokes at the meeting point |
| `clearance` | minimum gap between the two ribbons through the junction |
| `fillet` | radius of a circular fillet, or `None` for a clothoid blend |
| `taper` | length over which the branch narrows into the trunk |
| `bulb` | width law at the terminal, `none` / `cone` / `bulb` (W02) |

Report: the two join grades (G0/G1/G2), the minimum clearance through the gore,
the bulb's maximum width, and any crossing that is not a declared contact.

## What to read, in order

1. `kurbo/kurbo/src/stroke.rs` — how joins are constructed in general.
2. `spiro/` — the G2 interpolating approach and its price (globality).
3. `vendor/Clothoids` `cl_g2_connect` — the local G2 blend we can call today.
4. SolveSpace's sketcher fillet (reference only) for the geometry of touch
   points when one side is an arc.

## Verdict

Nothing to vendor. The circular fillet is twenty lines; the clothoid blend is
already callable; the parts that are ours are the junction object, the declared
contact and the clearance it must respect.

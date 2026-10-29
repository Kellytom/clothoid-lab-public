# Junctions

A junction is where one stroke meets another: leaf to branch, branch to trunk.
The vocabulary is borrowed, because the problem is older than this project:

| Word | Source | Meaning |
|---|---|---|
| **fillet** | engineering | the blend arc at a corner |
| **crotch** | botany | the white wedge where a branch leaves a stem |
| **gore** | road design | the triangular white between diverging carriageways |
| **haunch** | architecture | the thickening where a member meets its support |
| **bulb** | this project | a width law at a terminal, swelling into the gap |
| **cap** | drafting / SVG | a *subset* of terminal: closes the end without turning the stroke past the cap limit |
| **turned terminal** | this project | a terminal that turns past the limit (hairpin, wrapped bulb) — not a cap |

The cap limit is currently **120°**, chosen for this project and free to move;
it is a threshold, not a theorem. Under it: `butt`, `point`, `arc` and `round`
are caps; `taper`, `cone` and `bulb` are tapers; a hairpin is a turned terminal.

## What exists now

`clothoid_lab/fillet.py` — the circular fillet, and nothing more.

```python
from clothoid_lab.fillet import corner_fillet

f = corner_fillet(a=(10, 0), corner=(0, 0), c=(0, 10), radius=2.0)
f["start"], f["end"]     # (2, 0), (0, 2) — the touch points
f["centre"]              # (2, 2)
f["trim"]                # how much of each edge the arc consumes
f["spans"]               # cubic spans, start → end
```

`fillet_span(spans, index, radius)` does the same in place: it trims two
straight spans at their shared corner and inserts the arc, so the result is one
continuous chain.

`arc_segment(f)` turns the fillet into a circular-arc `Segment` and anchor, so
it can enter a `Design` chain and be rendered by the same writer as everything
else:

```python
from clothoid_lab.fillet import arc_segment
from clothoid_lab.model import Design, Segment

spec = arc_segment(f)
design = Design(anchor=..., segments=[Segment(kd=0, length=8, kappa0=0),
                                      Segment(**spec["segment"]),
                                      Segment(kd=0, length=8, kappa0=0)])
```

The two joins come out G1 with a curvature step of `1/r` — exactly what a
circular fillet is, and the reason a trunk eventually wants the clothoid
blend.

The maths is the standard construction: for interior angle `θ`, the touch
distance is `T = r / tan(θ/2)`, the centre sits on the bisector at
`r / sin(θ/2)`, and the arc turns through `π − θ`. It refuses a radius that does
not fit the shorter edge, collinear edges, and edges that double back.

## What it is not

- **It is G1, not G2.** Curvature jumps from 0 to `1/r` at each touch point.
  That is honest for a foot or a nick, and visible on a trunk. The clothoid
  blend (`cl_g2_connect` in the engine) is the next step, not this one.
- **Straight edges only.** `fillet_span` rejects curved spans instead of
  pretending a tangent point lies on the chord.
- **No clearance check.** A fillet can still crowd a neighbouring stroke. Run
  `piece_clearance()` on the result; the fillet does not police itself. At the
  junction itself, declare a `Contact` with `waives_clearance=True` so the merge
  is accepted and reported under `merged`, while the gore outside the footprint
  is still measured.

## The junction object

`clothoid_lab/junction.py` now has it:

```python
from clothoid_lab.junction import Junction

j = Junction(corner=(0, 0), branch_end=(30, 0), trunk_end=(0, 40), radius=6)
built = j.build()          # {"piece", "contact", "report"}
report = built["report"]   # angle, tangent, arc length, trim, join "G1", 1/r
result = j.check()         # the clearance report, merge declared
```

The branch is a straight run, the fillet arc, and the merge; the trunk is a
straight ribbon. The contact at the merge carries `waives_clearance=True`, so
the overlap is accepted and reported under `merged` — while anything crowding
the junction from outside still fails. The reported join is **G1**: that is the
circular fillet, stated rather than dressed up.

## What comes after this object

```text
Junction
  point        where the two centre lines would meet
  angle        interior angle between the strokes
  clearance    minimum gap that must survive through the crotch
  fillet       radius, or None for a clothoid blend
  taper        length over which the branch narrows into the trunk
  bulb         none | cone | bulb, from the W02 terminal laws
  contacts     declared Contact objects passed to the clearance report
```

Its report should carry the join grades (G0/G1/G2), the minimum clearance
through the gore, the bulb's maximum width, and any crossing not covered by a
declared contact. That is the point where "leaf joins branch" stops being a
drawing and becomes something the tests can hold.

## Prior art, without copying

- `focus-math/repos/kurbo/kurbo/src/stroke.rs` — how joins are built in general.
- `focus-math/repos/spiro/` — G2 interpolating spirals; the global alternative.
- `focus-math/notes/05-junctions-and-fillets.md` — the full reading list.
- SolveSpace / FreeCAD sketchers (GPL/LGPL) — reference for arc-tangent
  constructions only.

## Tests

`tests/test_fillet.py` — 19 cases: right angle and 60°, arc on the circle,
continuity, clearance from the corner, radius fit, collinear and doubled-back
rejection, trimming two spans, keeping the outer ends, curved-span rejection, arc-segment endpoints and curvature, and the G1 join
report.

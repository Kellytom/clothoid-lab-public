# Design philosophy

The question this answers: when we say "a fleur", what is the object, in what
order is it built, and what are its parts called?

## The glyph is a graph, not a walk

There is no single curve to walk from 1 to 2 to 3. A glyph is:

    glyph   = parts + joints + symmetry + measurement
    part    = a full line (stroke body) with two terminals
    joint   = a declared contact between two parts
    symmetry= mirror, applied to the whole glyph
    measure = clearance, crossings, folds

Order of drawing is **layer order**, not connectivity. Order of building is
**part by part**, each part walked once along its spine. A fleur is not "trace
the outline"; it is "a lance, two petals, a band, a foot, two tails, mirrored,
with declared joints between them".

## The full line

The three lines together — centre and both rails — are a **full line**.

- **spine** — the centre line, the curve the engine computes.
- **rail** — either edge. `rail +` is on the left of travel, `rail −` on the
  right, with left = `(-t.y, t.x)` for tangent `t` (y up).
- **full line** — spine + both rails + the width law that relates them. This is
  the unit of design, measurement and naming ("the petal's full line").
- **stroke** is reserved for what SVG means: the drawn mark. Using it for the
  body would collide with `stroke-width` and `stroke-linecap` in every file.

**Direction is part of a full line.** A stroke is walked from its *start*
terminal to its *end* terminal, and the rails are named by that direction.
Mirroring reverses handedness: the mirror's left rail is the original's right.
A terminal is therefore never just "the end"; it is the start or the end.

## Sections, not independent walks

At one station `s` along the spine, the three lines are one cross-section:

    section(s) = (left, spine, right, tangent, curvature, width)

This is the "design box" idea, and it is how the model should *think*: width,
terminal width laws, clearance and folds are all properties of a section or a
pair of sections. The rails are **derived at the same stations**, never walked
separately and never independently re-timed.

Rendering is allowed to disagree in representation, not in meaning: each rail is
fitted to cubics for SVG, so the output is three paths that no longer share a
parameter. That is fine — the authoring model is section-locked, the output is
path-locked. Measurements take the fitted paths and carry their error bound.

## Terminals

- A **terminal** is any treatment of a full line's end.
- A **cap** is the subset that closes the cross-section without turning past the
  cap limit (120° for now, tunable).
- A **taper** closes by narrowing: `taper`, `cone`, `bulb` (the width-law bulb).
- A **turned terminal** goes past the limit: hairpin, wrapped bulb. Not caps.

Terminals belong to ends, not to traces: `(start, end)` is part of the model.

## Joints

A **joint** is where two full lines meet: leaf into branch, branch into trunk.
It is declared, never inferred from proximity. Declaring it does two things:

1. it permits the crossing or merge inside its footprint;
2. it waives clearance *inside* that footprint, and only there.

The **gore** is the part of the gap just outside the footprint; it is measured
normally, which is what keeps a junction from hiding crowding. The **counter**
is the white shape the gap makes — the bulb beside a terminal is a counter.

## Mirror

The mirror is a symmetry of the glyph, not a second drawing. It duplicates
every part whose rule says it is mirrored, and swaps the handedness of terminals
and rails. The centre seam is a joint like any other: if the two halves touch,
that contact is declared.

## What this rules out

- **No global walk.** No 1,2,3 around the outline; no imposed starting point.
- **No implicit joins.** Two strokes that happen to touch are a violation until
  declared.
- **No rail-first design.** A rail is always a section of a full line, never an
  independent curve that the spine is inferred from.
- **No style in geometry.** Width is geometry (a law), not a stroke attribute.

## Where the code stands

| Idea | In code |
|---|---|
| glyph = parts + joints + mirror | `Piece` (traces, contacts, mirror) |
| full line | `Trace` + width; rails built as `Group`s |
| section | `section.py`: `Section`, sampled by arc length |
| terminal (cap / taper / turned) | `terminals.py`; turned not built |
| joint | `Contact`, `Junction` |
| measurement | `clearance.py` |
| grammar | `grammar.py` (study 01) |

The read model is `Section`; the grouping object is `Bundle`. It is what a terminal width law, a
junction gore and a clearance sample all want to read, and today each of them
reconstructs it from the fitted paths.

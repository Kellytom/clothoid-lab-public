# clothoid-lab

Numerical clothoid chains, out as plain editable SVG.

A clothoid, or Euler spiral, is the curve whose curvature rises linearly with
arc length. It is the transition every road and railway uses, and the shape
under a French curve. This tool builds chains of them to stated tolerance,
offsets them into ribbons, and writes SVG that Inkscape opens as ordinary cubic
Bézier nodes.

The engine is Bertolazzi's Clothoids, compiled from the vendored source and
called through a small C surface. Everything around it is here: the chain
model, the cubic fit, the rails, and the writer.

## Install and run

```sh
bash scripts/build-native.sh          # compiles the engine, about a minute
python3 -m venv .venv                 # nothing to install: no runtime deps
.venv/bin/python -m clothoid_lab.cli --preset s-curve --width 6 --out out/s-curve.svg
```

The build needs a C++ compiler and nothing else. If the compiler is unavailable,
install the wheel and ask for it: `pip install -r requirements-dev.txt`, then add
`--backend pyclothoids` or `export CLOTHOID_BACKEND=pyclothoids`. The wheel carries
the same engine, which is why it works as a cross-check and not as the default.

```
scale         1 unit = 1.0000 mm
segments      2   length 80.000 units
joins         G2   worst curvature jump 0.000e+00 1/unit
tightest      radius 12.732 units at s=40.00
cubics        6  per segment [3, 3]
fit           0.0032 units worst, 0.0032 units spacing  (tol 0.02 units)
rail +3.000  clear  7 cubics  error 0.0167 units  margin 9.732 units
rail -3.000  clear  7 cubics  error 0.0136 units  margin 9.732 units
verdict       inside tolerance
wrote         out/s-curve.svg
```

Presets: `s-curve`, `ogee`, `bracket`, `petal`. Options: `--tol` in design
units (millimetres at 1:1), `--width` for a two-rail ribbon in design units,
`--page WxH` to fix the page in mm, `--prec` for
decimals in the path data, `--split` for how many pieces a span is cut into,
`--backend` to choose the engine, `--design` to read a JSON design, `--points` to
fit a spline through a points file, `--g2` and `--closed` for that spline,
`--smooth N`, `--trim S0,S1` and `--reverse` on any design, `--json` to write
one, `--watch` to rebuild on save, `--quiet`.

`--page` matters in the two-window loop: with an automatic page every parameter
change resizes the document and the viewer re-fits, so the zoom moves under your
hand. A fixed page keeps the viewBox constant and the drawing moves inside it.

`--page` keeps one design unit equal to one millimetre. `--frame` instead scales
the drawing to fill the sheet, so a design unit becomes the reported scale in
millimetres; the report prints `1 unit = ... mm` on every run so the two cannot
be confused silently.

A rail that folds reverses inside a span, where the parabola arm runs away and
would place a control point tens of metres out. The arm is bounded at four times
the chord, and each clamped span is counted in the report rather than hidden.

## Clearance

A piece can be measured as well as drawn. `piece_clearance()` reports the
minimum edge-to-edge gap between strokes, the pairs that fall below it, and
every crossing that no declared contact covers:

```python
from clothoid_lab.clearance import Contact, piece_clearance

result = piece_clearance(piece, clearance=5.0)
print(result["ok"], result["min"])

# a junction is a declared contact, not an accident
piece_clearance(piece, clearance=5.0,
                contacts=[Contact((12.0, 0.0), 2.5, "ink/leaf", "ink/branch")])
```

Measurements carry their error: a pair is only called a violation when it is
below `clearance - 2·tol`, and the band in between is reported as a warning.
See `docs/CLEARANCE.md` for the rule, the algorithm and its limits.

Exit status is 0 when the fit is inside tolerance and every join is G2, 1 when
it is not. A fold in a rail is reported and does not fail the run.

## Two windows

Start the watcher, keep Inkscape open on the drawing, edit the design on the
other side, and save.

```sh
.venv/bin/python -m clothoid_lab.cli --watch \
    --design out/play.json --seed ogee --width 6 --out out/play.svg
```

```
seeded out/play.json from preset ogee
built     8 cubics  0.0050 mm  bertolazzi  ok
watching out/play.json -> out/play.svg   (ctrl-c to stop)
rebuilt   8 cubics  0.0031 mm  bertolazzi  ok
```

Inkscape notices the file changed and offers to reload. The write is atomic, so
it never opens a half-written file, and a design that does not parse leaves the
last good drawing untouched, because typing a number passes through states that
are not valid JSON.

If the drawing opens zoomed into a corner, the saved view is wrong. Inkscape
stores `inkscape:zoom` as a factor, not as pixels per millimetre, so
`scripts/fit_view.py out/play.svg` recomputes it from the page and the window
and centres the view.

This is generate-and-look, not a round trip: a rebuild replaces the file, so node
edits made in Inkscape are lost on the next save. The extension is what closes
that loop.

## A browser twin

`scripts/twin.py` writes a self-contained HTML page: the SVG inline, the chain
report and the design JSON beside it.

```sh
.venv/bin/python scripts/twin.py --svg out/play.svg --design out/play.json \
    --out out/twin.html
```

It needs no server and no external assets, so it can be sent on as one file.
`--refresh 2` reloads it on a timer while the watcher rebuilds.

## A design is data

```json
{
  "name": "s-curve 90 deg",
  "anchor": {"x": 0.0, "y": 0.0, "angle": 0.0},
  "segments": [
    {"kd": 0.0019635, "length": 40.0, "kappa0": null},
    {"kd": -0.0019635, "length": 40.0, "kappa0": null}
  ],
  "offsets": [],
  "stroke": 0.8
}
```

`kd` is curvature rate in 1/unit², `length` is arc length in design units, and
`kappa0` is the curvature the segment starts from. At output, one design unit is
one millimetre for a page or an automatic sheet; with `--frame`, the writer
scales the design to the sheet, so one unit becomes that much larger or smaller.
`null` means "continue from the previous segment's end", which is what makes the
join G2. Set a number and the jump against the previous end is measured and
printed.

## Through points

When the shape starts as a sketch rather than a curvature list, give the tool
the points and let it fit them:

```sh
.venv/bin/python -m clothoid_lab.cli --points out/route.txt \
    --width 4 --frame 200x250 --out out/route.svg
```

`out/route.txt` is one point per line, in millimetres:

```
0, 0
12, 6
24, 2
36, 10
```

This is Bertolazzi and Frego's G1 fitting. Each pair of points gets one clothoid
that passes through both with the directions at its ends, and the directions are
estimated so neighbours share a tangent. The fit is G1, not G2: curvature is
free to jump at a point, and the report prints the jump rather than hiding it.
Every fitted segment is written into the design in full, so a spline is still a
design — editable, offsettable, and reproducible without the points file.

For control, JSON may carry the directions and a name:

```json
{"name": "ridge", "points": [[0, 0], [12, 6], [24, 2]],
 "thetas": [0.0, 0.4, 0.9]}
```

A supplied direction is honoured; with no `thetas`, they are estimated.
`--watch --points out/route.txt` watches the points file and refits on save,
the same loop as a design file.

Two points give one clothoid. The fit is available directly too, as
`interpolate.fit(p0, t0, p1, t1)`, returning `(kappa0, kd, length)`.

```
segments      4   length 55.461 units
joins         G1   curvature jumps are intended by construction
fit           0.0100 units worst  (tol 0.02 units)
verdict       inside tolerance, joins G1 by construction
```

`--g2` fits with continuous curvature instead: the end directions default to
the first and last chord, the end curvatures to zero, and `--closed` closes the
ring. It costs more segments, and it removes the jumps — measured, not assumed.

## Splicing and trimming

The chain can be cut and reversed without refitting, so the pieces stay the
same clothoid arcs. Two designs can be joined with a G2 connector at the seam:

```python
from clothoid_lab import compose

short = compose.trim(design, 20.0, 120.0)   # arc-length range, mm
back = compose.reverse(design)
joined = compose.join(first, second, method="3arc")
```

`compose.join` places the second design where its anchor says and bridges the
gap with one of the library's G2 connectors: `2arc`, `3arc` or `clc`. The seam
is curvature-continuous; the result is an ordinary design, not a new type.

From the command line, `--trim 20,120` and `--reverse` apply to any design, and
`--smooth N` moves the shared tangents to reduce curvature jumps (quasi-G2).

## How the drawing is made

1. **Place the chain.** Each segment starts where the last ended, facing the
   direction the last ended in. Position, tangent and curvature carry across,
   so continuity is structural rather than hoped for.
2. **Cut it into cubics.** Each span takes the parabola rule's arm along its end
   tangents, chord over three cosine-squared halves. A span that misses the
   tolerance is redivided `--split` ways, two by default.
3. **Measure, never assume.** The error is the distance from the cubic to the
   curve, found by searching arc length, not the distance to sampled points. A
   sampled metric cannot report zero, so a straight line would look bent.
4. **Offset.** Rails are the library's exact parallel curve (`X_ISO`, `Y_ISO`),
   refitted to cubics. A rail folds where the offset reaches the centre of
   curvature, `|d * kappa| >= 1`; the fold is drawn and its arc-length range and
   margin are printed.
5. **Write.** Absolute `M` and `C` only, fixed-point numbers with no exponent,
   one user unit to one millimetre, `width` and `height` in mm with a matching
   viewBox, no transform. Positive y is up: SVG's y is down, so the writer flips
   at output (`y' = page_height - y`) and nowhere else, leaving the design JSON
   y-up. The design rides along in a `<desc>` so a round trip has something to
   recover.

## What is settled

- **The engine is compiled from source, BSD-2-Clause.** No wheel in the critical
  path, no copyleft: our code is MIT and can move between projects. The wheel is
  kept as a second opinion on the wrapper.
- **The fold is drawn, not clipped.** A fold is often the point of a ribbon. What
  must not happen is an unannounced one, so every rail carries its fold range in
  the report.
- **The 45 degree rule fails 0.02 mm.** Two spans over a 90 degree turn on a 40 mm
  segment is 0.024 mm off, by measurement, here. The tolerance decides, not the
  angle.
- **No path library.** Writing `M` and `C` is a formatting job, not a dependency.
- **The split factor is a dial, not a saving.** Measured on a 90 degree turn at
  0.02 mm: two-way splitting reaches tolerance in three spans per segment, a
  four-way split needs four. The default stays two.

## Files

- `clothoid_lab/model.py` holds the design, its JSON, and its validation.
- `clothoid_lab/engine.py` places the chain and addresses it by arc length.
- `clothoid_lab/interpolate.py` fits a G1 or G2 spline through points and turns it into a design.
- `clothoid_lab/compose.py` trims, reverses, connects and joins designs.
- `clothoid_lab/bezier.py` holds the arm rule, the subdivision, and the error metric.
- `clothoid_lab/offsets.py` builds the rails, the fold ranges and the ribbon.
- `clothoid_lab/svg.py` writes the path data and reads the design back.
- `clothoid_lab/presets.py` holds the named starting designs, numbers derived.
- `clothoid_lab/backend/` holds the ctypes surface and the wheel adapter.
- `clothoid_lab/cli.py` runs one command and prints the report.
- `clothoid_lab/watch.py` holds the two-window loop and its safety rules.

## Tests

```sh
.venv/bin/python -m unittest discover tests
```

92 checks. The engine is held against an independent Simpson integral of the
Fresnel form, every preset against G2, both spline methods against the points
they were given, the G2 spline and the joined designs against their own
curvature continuity, the fitter against its own tolerance, and the writer
against the things that break Inkscape: exponent notation, transforms, and
coordinates that never touch the curve. The two backends are held against each
other, and the watcher is held against a broken edit, which must not blank the
drawing.

## Known roughness

- A rebuild replaces the whole file, so node edits made in Inkscape are lost.
- `--reopen` asks the macOS open handler for the file, which can hand Inkscape a
  second window and break a tiled layout. It is off unless you ask for it.
- The error is measured from the cubic to the curve, not the curve to the cubic,
  so a span that skipped a piece of curve would report small.

## Licence

MIT for this project. The vendored engine is BSD-2-Clause, Eigen is MPL-2.0, and
the optional wheel is MIT. See `LICENSE` and `ATTRIBUTION.md`.

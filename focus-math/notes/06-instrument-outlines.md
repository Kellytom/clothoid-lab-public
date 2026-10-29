# Instrument outlines

`repos/Violin_Boundary` (MIT) is the one public, licensed, mathematically
serious outline dataset found: the NURBS boundary of a symmetric violin **with
its f-holes**, from Arf and Reichle's isogeometric work.

## What is in it

- 8 corpus NURBS (`BoundaryCorpus_01..08`) plus one straight segment, degree ≤ 3.
- 12 f-hole NURBS (`BoundaryFhole_01..12`), also degree ≤ 3, normalised knots.
- `OrigCurve.m` builds them with `nrbmak` from **GeoPDEs** and plots them;
  `Viola_Boundary.3dm` is the same data as a Rhino file.
- Coordinates are in the authors' own units, not millimetres. Any comparison
  with our sheet needs scaling by a measured dimension, not by assumption.

## Why it matters to this project

1. **Purfling is a clearance constraint.** The double line around the plate is a
   fixed offset — roughly 4–5 mm on a full-size violin — held around every
   corner and every bout. That is the 5 mm rule with a historical precedent and a
   name: purfling, and the white between the lines is a counter.
2. **Corners are terminals.** The C-bout corners are point ends with a defined
   overhang. They give `point` a real reference instead of an invented one.
3. **The C-bout is a concave junction.** A leaf leaving a branch is the same
   geometry with the sign flipped, so the fillet and gore vocabulary
   (`05-junctions-and-fillets.md`) can be tested on both.
4. **The f-hole is two point terminals and a taper**, i.e. W02's vocabulary in
   one shape, with a bulb at the eye.
5. **The outline is a closed, mirrored piece.** `Piece` already mirrors; closure
   and a closed-chain renderer are the missing parts.

## Use it as a fixture, not as a design source

The value is in the *numbers*: a real outline whose clearance must stay constant
under a fixed offset. Two checks worth building once the clearance report exists:

- Offset the corpus by the purfling gap and confirm the measured clearance never
  falls below it, including at the corners.
- Intersect the f-hole with the plate edge and confirm no unintended crossings.

If those two hold, the clearance machinery is trustworthy on our own pieces.

## Out of scope

Arching, graduation, thickness mapping and acoustics are 3D and a different
product. The sheet is 2D; keep instrument work to outline, purfling, corners and
f-holes.

## Verdict

No code to take. One MIT fixture worth porting far enough to produce a polyline
(the MATLAB depends on GeoPDEs; a small NURBS evaluator is enough for a test).

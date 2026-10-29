# Ornament grammar: what prior art exists

Searched GitHub for fleur-de-lis, ornament generators, calligraphic strokes,
ribbon/stroke grammars and pen-lettering engines. The result is thin:

- `redocebiv/oyu-pattern` (1★) and `Byambaa0325/khee` (0★) — rule-based Kazakh
  and Mongolian ornaments. Motif-specific, no general stroke model.
- Signature and brush-calligraphy demos — animation of single-stroke fonts, not
  geometry.
- Font tooling (`fonttools`, Spiro, libspiro) — the closest serious work on
  variable-width strokes, but aimed at glyphs, not ornament.

Nothing carries: named terminals, a minimum clearance between strokes,
crossings permitted only at declared terminals, or leaf → branch → trunk blends.
The nearest neighbours are type design (Spiro, `curve-offsetting`) and road
design (clothoid transitions, gores), and both stop short of the grammar.

## Consequence

The grammar is ours to write, and the honest description of it is: a small
stroke model (already in `Piece`/`Trace`), a terminal vocabulary (W02, done), a
clearance and crossing report (not built), and junctions (not built). The prior
art supplies algorithms for each; none supplies the structure.

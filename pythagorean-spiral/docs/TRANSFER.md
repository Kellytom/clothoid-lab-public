# Placement and transfer

A curve is useful only when it can be put somewhere. This asks two questions of the spine layer: can a finished figure be rotated and scaled onto the integer lattice, and can the caps and terminals be re-expressed on the new curve?

> Placement is exact exactly when the rotation comes from the chain's group. Quarter turns and triangle powers stay rational; 30 and 45 degrees do not, and belong to the float path.


## 1. The lattice rule

A chain's points are rational. Rotating by a triangle power or a quarter turn, scaling by a rational and translating by a rational keeps them rational, so they can be written as integers over one denominator (`place.lattice`) -- or snapped to a page grid in thousandths (`place.quantize`). `place.fit` takes the largest uniform scale that puts the figure inside a 200 x 250 box with a margin, then rounds to the grid.

```text
rotation      triangle power + quarter turn, exact
scale         rational (or an integer multiple of the lattice)
offset        rational
output        integers over one denominator, or grid units
outside group float only; quantized, not exact
```

| quantity | value |
| --- | --- |
| page | 200 x 250, +y up |
| rotation | triangle power 5 of 39-760-761 |
| scale | 26.417 |
| output | integers, thousandths of a unit |
| margin | 8 units |

![The fleur from the gallery, rotated inside the group, fitted to the page and rounded to thousandths.](fig/transfer-page.svg)

*The fleur from the gallery, rotated inside the group, fitted to the page and rounded to thousandths.*

The point of the exercise is not the picture: it is that every vertex is an integer on a declared grid, so a design can be stored, tiled, compared and cut without a float deciding where a corner is. A rotation outside the group would break that, which is why the placement API asks for a `Dir` rather than degrees.


## 2. Caps: clothoid segments into a chain

All 36 caps in `out/caps` are clothoid segments in a local frame at the origin with angle zero -- they were made to be placed. Each segment is `(kappa0, kd, length)`, so the cap is a curve with curvature linear in arc length. The new curve is an Euler polygon of exactly that kind of curve, so a cap transfers by quantising each chord's turn to the triangle lattice.

```text
kappa(s)      kappa0 + kd*s
turn/chord    kappa(s_mid) * chord
lattice turn  round(turn / alpha) * alpha
error         measured against a fine integration of kappa
frame         anchor (0,0), heading east, angle 0 in every cap
```

| caps | 36 |
| --- | --- |
| segments | 77 |
| chords at 2 units | 7,490 |
| median gap | 0.44% of length |
| worst gap | 10.06% (cap-2.json) |

![A cap transferred to the lattice: the clothoid in faint, the quantised chain in ink.](fig/transfer-cap.svg)

*A cap transferred to the lattice: the clothoid in faint, the quantised chain in ink.*

The residual is the lattice, not the arithmetic: each chord's turn is rounded to a whole triangle angle, so the gap grows with alpha and with curvature. At 0.05 degrees the median is under half a percent of the cap's length; the worst cases are the caps whose curvature changes fastest, and they want a finer alpha or shorter chords, both of which the float hybrid can now afford.


## 3. Terminals: geometry without a frame

The terminals are `150` ends across two extractors, stored as cubic spans in page units. They transfer as *geometry* -- a rotation, scale and offset turn them into placed cubics -- but they carry no anchor and no heading, because they were cut out of a finished outline at a seam. The frame has to be recovered from the seam, or recorded when the terminal is extracted.

```text
terminals      cubic spans, page units
anchor         absent
heading        absent
transfer       one affine call once a frame exists
missing datum  the seam's point and direction
```

That is the next change in the main package, not here: the extractor should write `anchor` and `heading` beside each terminal, exactly as the caps already do. With that, attachment is the same operation as `fork`: read a frame, rotate by its exact direction, scale, translate.


## 4. What is ready

| operation | status |
| --- | --- |
| rotate inside the group | exact, tested |
| scale by a rational | exact, tested |
| fit to a 200 x 250 page | integer grid, tested |
| caps to the new curve | 36 cap files, median gap 0.44% |
| terminals with a frame | blocked: no frame stored |
| arbitrary angles | float only; quantized |

Placement is the piece that had to exist first: caps, terminals, mirrors and branches all reduce to it. The caps are close to ready; the terminals need one field added where they are cut.


## Reproduce

```text
cd pythagorean-spiral
../.venv/bin/python scripts/transfer.py
../.venv/bin/python -m unittest tests.test_place
```

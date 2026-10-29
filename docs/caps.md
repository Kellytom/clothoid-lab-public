# Closed two-clothoid caps

This is the account of the cap exercise: a hairpin that starts at the origin
heading east, changes from a left clothoid to a right clothoid at an inflection,
and ends with a horizontal centreline. Two families came out of it, and a fold.

## The model

```
start        (0, 0), heading east
first        kappa0 = 0, kd1 > 0, length L1      left clothoid
inflection   kappa  = 0                          the hand-off
second       kappa0 = 0, kd2 < 0, length L2      right clothoid
end          (?, ?), heading west
```

Two ways of reaching the y-axis were built on that:

1. **Direct**: the clothoids end at `(0, Y)` heading west. That is
   `cap-11` … `cap-27`.
2. **Straight return**: the clothoids end at `(X, X)` heading west, then a
   straight segment of length `X` returns to `(0, X)`. That is
   `cap-5` … `cap-10`.

A third, separate form is the single clothoid turning exactly −180°:
`cap-1` (30 mm) and `cap-2` (10 mm). It has no inflection and no joint.

## The fixed numbers

```
kd1      6.08097981987e-5 1/mm²      A = 1/sqrt(kd1) = 128.236961 mm
width    10 mm                        rails at ±5 mm
stroke   0.5 mm
page     200 × 250 mm                 1 design unit = 1 mm
```

The scale was held fixed across the whole family. The page is 1:1, so the run
report says `1 unit = 1.0000 mm`; there is no frame factor.

## The solve

For a direct cap at height `Y`, solve three equations in `(L1, kd2, L2)`:

```
x_end            = 0
y_end            = Y
wrap(theta_end - pi) = 0
```

with `L1 > 0`, `L2 > 0`, `kd2 < 0`. The solver is the bounded
Levenberg–Marquardt in `clothoid_lab/solve.py`; each solution seeds the next
height, so the branch is a continuation rather than a fresh search.

For the straight-return family the first two residuals are `x_end - X` and
`y_end - X`, and the third segment is a straight line of length `X` back to the
y-axis.

## The result

The direct family solves from **Y = 10** to **Y = 162.2817** with the second
clothoid right-leaning. The fold is at:

```
Y     162.2817
L1    321.442393
kd2   0                 the second clothoid is now a straight line
L2    120.213937
```

`cap-26` at `Y = 160` is the last strictly right-leaning one, with
`kd2 = −4.047451e-6`. `cap-27` is the fold itself.

Past the fold, if `kd2 > 0` is allowed, the same equations continue to solve.
`kd2` turns over near **Y ≈ 235** (maximum ≈ `4.4e-5`) and the branch still
solves at **Y = 500**. So this is not a numerical failure of the solver; it is
where the *right-leaning* constraint ends.

Every committed cap fits under the 0.02 mm tolerance; the worst are `cap-17`
and `cap-22` at about 0.0196 mm. The rest are between 0.004 and 0.015 mm.

## Class II: the pointed leaf

A second family uses the same two clothoids as the **two edges of a leaf**, not
as a centreline with rails. The edges meet at a **tangent corner**, the point.
The y-axis closes the base.

Both halves turn left. The second is the mirror of the *reversed* first half, so
its curvature is not reversed:

```
first    kappa0 = 0,       kd1 = +KD, length L1
second   kappa0 = +KD*L1,  kd2 = -KD, length L1, corner = pi - 2*theta1
```

`theta1 = 0.5*KD*L1^2` is the tangent at the hand-off. The corner is the only
discontinuity; curvature is continuous across it, and the second half still
turns left while its curvature falls to zero at the y-axis. The end is
`(0, 2*y(L1))`, heading west, by symmetry.

The point closes when `corner = 0`, at `L1 = 227.30`, giving `Y = 199.239`.
The series `cap-pt-1` … `cap-pt-9` runs from `Y = 20` to `Y = 180`, with the
corner falling from 145° to 15°.

This required a real model change: `Segment.corner` is a tangent jump at the
start of a segment, carried through JSON and the engine, and reported as
`corners`. Class II uses no rails; the two clothoid edges themselves are the
drawing, closed by the y-axis. A cornered ribbon is still possible, and its rail
fit stops a fraction of a millimetre short of the break so the offset search
never sits exactly on the discontinuity.

## What the exercise established

- The family is a genuine one-parameter continuation: fixed curvature scale,
  fixed ribbon, only the endpoint height changes.
- The straight return and the direct end are different families. In
  `cap-5`…`cap-10` the clothoids stop at `(X, X)`; in `cap-11`…`cap-27` they
  stop on the y-axis itself.
- The fold is where `kd2` reaches zero, not where the equations lose a solution.
- A positive endpoint x at the same height needs the second clothoid to
  over-rotate; that is why `cap-3` loops and was superseded.

## Files

- `out/caps/README.md` — the full table of cap numbers, endpoint heights,
  parameters and fit errors.
- `out/caps/cap-N.svg` and `.json` — the drawings and their designs.
- `out/closed-cl-1.svg` — the closed hairpin the caps were derived from.
- `clothoid_lab/solve.py` — the bounded solver used for every solve.

All cap SVGs are y-up, 200 × 250 mm, scale 1.0000, with a fitted view and an
opaque white page.

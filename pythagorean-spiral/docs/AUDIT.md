# Audit — the Pythagorean "Euler curve", claim by claim

The source is a chat transcript proposing a clothoid built from Pythagorean
triangles. This is what checks out, what does not, and what the code does
instead. Every number here is reproduced by `tests/` or by
`scripts/compare_bertolazzi.py`.

## 1. What is right

| Claim | Check |
|---|---|
| Every primitive triple is `(m²−n², 2mn, m²+n²)` | `tests/test_triples.py` |
| A triple's rotation is the rational matrix `((bx−ay)/c, (ax+by)/c)` | `exact.Dir`, exact for every power |
| The 3-4-5 star at radius 3125 hits `(2500,1875), (875,3000), (−1100,2925), (−2635,1680), (−3116,−237), (−2350.6,−2059.2)` | reproduced exactly |
| The 7-24-25 chain nodes `(24,7), (40.4736,25.8048), (37.1840,50.5874), (13.3277,58.0626), (2.3304,35.6113)` (L = 25) | reproduced exactly |
| 79-3120-3121 is the thinnest primitive triple with `c ≤ 3125` | `thinnest(3125)`; it is `(m,n) = (40,39)` |
| Its double-angle twin is `(492960, 9728159, 9740641)` | `Triple.double_angle()` |
| `alpha = 1.4504486°`, the linear correction is `−alpha/2 = −0.0126576` | exact |
| Headings follow triangular numbers, so the sum is a quadratic in arc length | `Spiral`, and the oracle |
| `T(15) = 120` and `8·T(5) = 120`: ×8 closes on 15/5 | `closure_pairs(8)` |
| 32 segments reach `T(31)·alpha = 719.42°`, i.e. two laps | exact |

## 2. What is wrong

**"An exact, quantized execution of the continuous clothoid differential
equations."** No. The heading is piecewise *constant*: curvature is zero inside
a chord and impulsive at a node. The chain is an explicit **Euler polygon** of
the clothoid, first order in the step, not the clothoid. Measured against
Bertolazzi with `kappa0 = alpha/(2L)`, `kd = alpha/L²`, `L = 3121`:

```
worst heading error at a node   1.0e-13 deg
worst position error            3131.05 = 1.0032 chords
```

So the headings *are* the clothoid's, and the vertices are a polygon around it.
The two statements are different, and the difference is a whole chord.

**"The continuous curve passes precisely through every node."** Impossible. A
curve with those headings is the clothoid, and it misses the nodes by up to
`1.0032` chords. Only the piecewise-constant heading polygon passes through
them. Matching headings at the nodes buys tangents, not positions.

**"A² = 139.5050."** Their own derivation gives `A² = 1/alpha`. With
`alpha = 0.0253151 rad`, that is **39.5021**, not 139.5.

**"The unit-step 3-4-5 chain converges to a central limit point (0.62, 0.62)."**
It does not converge at all. With a fixed chord length the terms never decay;
once `alpha·k` passes a radian the sampled chirp aliases and the partial sums
wander like a random walk. Measured: `|S| = 134.1` at N = 10⁴, `198.6` at
4·10⁴, `403.1` at 1.6·10⁵ — growth like `sqrt(N)`. The Fresnel integral it should
have approximated gives `1.1048(1+i)`, modulus `1.5625`.

**"15 inward, 8 outward at ×2 ends at exactly 0°."** `T(15) − 2·T(8) = 120 − 72
= 48`, which is 69.6°, not 0. The transcript contradicts itself two sections
later. Exact ×2 pairs are `(3,2)` and `(20,14)`. For ×3, `(9,4)` is also wrong:
`T(9) − 3·T(4) = 45 − 30 = 15`. The true set is `(2,1), (9,5), (35,20)`. For
×15, `(15,3)` gives `120 − 90 = 30`; the true pairs are `(5,1), (9,2),
(44,11), (75,19)`.

**"Every node lands on exact integers."** Only the first one. The displacement
of chord `k` has denominator `c^T(k-1)`, with `T` triangular, so with `L = c`
the nodes are rational from chord 3 on. Integers need `L = c^T(max)`: for seven
chords that is `3121^21 ≈ 10^73`. `integer_form()` gets exact integers by
scaling the finished design once, which is honest and costs nothing — but it is
a scale choice, not a property of the chain.

**The leaf tables.** Their node 2 is `(6240, 79)`; exact is `(6241, 79)`. Node 3
is `(9351, 315)`; exact is `(9357.001, 315.949)`. Node 4 is `(12443, 786)`;
exact `(12448.025, 788.937)`. The claimed 20-triangle apex `(35518, 19864)`
does not belong to the stated 15-in construction, whose heading there is
`174.05°` and whose coordinates are a 300-digit rational.

**`x₆ = −11753/3125`.** The numerator is right; the denominator is 625× too
large. At radius 3125 the point is `(−11753/5, −10296/5)`.

**"Drift begins after n steps, so raise the exponent."** With `Fraction` there is
no drift at any step, so the whole grid-scaling apparatus is unnecessary. The
star's denominators grow as `c^k`; the spiral's as `c^T(k)`. Neither is a
rendering problem.

## 3. The theorem the notes guessed at

The transcript says the heading "only hits 0 or 90 if the multiplier is zero"
and treats it as an observation. It is a theorem, and it decides the design:

> With a single triangle, a chain ends on an axis **iff** its total turn
> coefficient is zero.

`q·alpha = k·π/2` makes `alpha` a rational multiple of `π`, so `tan alpha` would
be the tangent of a rational multiple of `π`; the only such rational tangents
are `0, ±1`. But `tan alpha = a/b` with `0 < a < b`, so it is neither. Hence
`q = 0`.

Consequences, all implemented:

- A **smooth** join (curvature continuous) can still close exactly, but only on
  `j(j+1) = 2n(n-1)`: `n = 3, 15, 85, …` (`design.g2_lobe`).
- A **sharp** join costs nothing extra: the sign flip at the apsis is free, and
  closure is the same arithmetic (`design.lobe`).
- Reaching **90°** is impossible by accumulated turning. It needs an explicit
  right-angle cusp at the apsis (`Spiral.cusp`) or a quarter turn of the
  finished design. There is no `n` that makes it come out otherwise, so
  "change the number of triangles until it lands on 90" has no solution.

## 4. Unnecessary constrictions

The method is more general than the notes allow, and narrower than they claim.

| Constriction | Verdict |
|---|---|
| "Every chord must be the hypotenuse length" | Unnecessary. Any length works; only `L = c^T` keeps integers. |
| "Integer coordinates" | Unnecessary, and it is what produced the wrong scaling rules. `Fraction` is exact and cheap. |
| "One triangle only" | Unnecessary. Products of powers of different triples stay rational. Closure bookkeeping wants one `alpha`. |
| "Use the thinnest triangle" | Not for exactness. It is a *resolution* constraint: chords resolve the curve while `alpha·k < ~1`, so `k ≲ 39` here. |
| "One cubic per 45-60°" | Not a global rule, and the wrong variable. A cubic's error follows the turn it carries, so the budget is a turn budget, and it must break at a curvature reversal or it cannot fit the apsis at all. With 6° chords the measured deviation is the chain's own sagitta. |
| "3125 grid, 31 250 panel" | Unnecessary. Page size is a render concern, and the writer scales. |
| Equal chord lengths | The one real constraint: integer turn coefficients plus linear curvature force a quadratic arc-length schedule. |

## 5. Integration verdict

The idea integrates; the artifacts mostly do not.

- **Fits:** the span layer. `spans.spans()` returns exactly
  `{"s0","s1","p0","c1","c2","p3"}`, and `clothoid_lab.svg.path_d` consumes it
  today with no change (`tests/test_render.py::TestIntegration`). That is the
  seam the `piece`/`groups` machinery already uses.
- **Does not fit:** `Design`/`Segment`. Those describe continuous clothoids
  evaluated by a backend; a chord polygon is neither.
- **Should not be a backend.** The protocol is `Curve` with `offset_point`,
  `project`, `intersections`, `length_iso`, `bbox_iso`, plus `g1_fit`,
  `g2_spline`, `trim`, `smooth`. A polygon can answer some of that and would be
  wrong about the rest, and registering it in `BACKENDS` would claim it is an
  interchangeable oracle for the same geometry. It is a different curve with a
  1-chord position error.
- **Gap to close before replacing anything:** `clearance`, `fillet`, `junction`
  and `offsets` all take a `Chain`. A replacement needs offsets of a polygon
  (fine, Minkowski) and *crossing* tests (fine), but the G1/G2 fitting would have
  to be re-derived against the chain's own curvature, which is impulsive.

Recommendation: keep this as a study at the span layer, and do not touch
`clothoid_lab/` until the closure and resolution results above are accepted.

## 6. Reproduce

```sh
cd pythagorean-spiral
../.venv/bin/python -m unittest discover -s tests -t .     # 36 tests
../.venv/bin/python -m pythagorean_spiral.cli --list-closures
cd .. && .venv/bin/python pythagorean-spiral/scripts/compare_bertolazzi.py
```

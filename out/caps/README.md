# Caps

Every cap is on a **200 × 250 mm** page, **1 design unit = 1 mm**, stroke
**0.5 mm**, y-up, with a fitted view. Class I caps use the **10 mm ribbon**
(5 mm each side); class II leaves draw only the two clothoid edges.

Columns: segments, end y (mm), first length, second curvature rate, second
length, fit error (mm), cubics.

| file | segs | end y | L1 | k2 | L2 | fit | cubics |
|---|---|---|---|---|---|---|---|
| `cap-1` | 1 | -30.000 | 59.423 | +0.0000e+00 | 0.000 | 0.01227 | 4 |
| `cap-2` | 1 | -10.000 | 19.808 | +0.0000e+00 | 0.000 | 0.01297 | 3 |
| `cap-3` | 3 | 10.000 | 1.890 | -6.6805e-03 | 38.409 | 0.01628 | 8 |
| `cap-4` | 2 | -0.000 | 391.516 | -1.2541e-04 | 155.642 | 0.01109 | 10 |
| `cap-5` | 3 | 10.000 | 392.823 | -1.5871e-04 | 139.769 | 0.01059 | 11 |
| `cap-6` | 3 | 20.000 | 394.383 | -2.0739e-04 | 123.731 | 0.01008 | 11 |
| `cap-7` | 3 | 30.000 | 396.280 | -2.8276e-04 | 107.476 | 0.01008 | 11 |
| `cap-8` | 3 | 40.000 | 398.635 | -4.0888e-04 | 90.921 | 0.01056 | 11 |
| `cap-9` | 3 | 50.000 | 401.643 | -6.4512e-04 | 73.935 | 0.01120 | 11 |
| `cap-10` | 3 | 60.000 | 405.627 | -1.1744e-03 | 56.296 | 0.01211 | 11 |
| `cap-11` | 2 | 10.000 | 389.540 | -1.3579e-04 | 147.250 | 0.00955 | 10 |
| `cap-12` | 2 | 20.000 | 387.349 | -1.4633e-04 | 139.330 | 0.00844 | 10 |
| `cap-13` | 2 | 30.000 | 384.916 | -1.5660e-04 | 131.945 | 0.00804 | 10 |
| `cap-14` | 2 | 40.000 | 382.211 | -1.6597e-04 | 125.168 | 0.00762 | 10 |
| `cap-15` | 2 | 50.000 | 379.203 | -1.7356e-04 | 119.077 | 0.00717 | 10 |
| `cap-16` | 2 | 60.000 | 375.862 | -1.7831e-04 | 113.759 | 0.00669 | 10 |
| `cap-17` | 2 | 70.000 | 372.157 | -1.7905e-04 | 109.302 | 0.01959 | 9 |
| `cap-18` | 2 | 80.000 | 368.066 | -1.7465e-04 | 105.797 | 0.01435 | 9 |
| `cap-19` | 2 | 90.000 | 363.572 | -1.6436e-04 | 103.331 | 0.01006 | 9 |
| `cap-20` | 2 | 100.000 | 358.674 | -1.4806e-04 | 101.981 | 0.00665 | 9 |
| `cap-21` | 2 | 110.000 | 353.386 | -1.2648e-04 | 101.804 | 0.00419 | 9 |
| `cap-22` | 2 | 120.000 | 347.742 | -1.0120e-04 | 102.838 | 0.01952 | 8 |
| `cap-23` | 2 | 130.000 | 341.795 | -7.4328e-05 | 105.089 | 0.01895 | 7 |
| `cap-24` | 2 | 140.000 | 335.617 | -4.8077e-05 | 108.535 | 0.01515 | 7 |
| `cap-25` | 2 | 150.000 | 329.289 | -2.4263e-05 | 113.124 | 0.01323 | 7 |
| `cap-26` | 2 | 160.000 | 322.900 | -4.0475e-06 | 118.782 | 0.01150 | 7 |
| `cap-27` | 2 | 162.282 | 321.442 | +0.0000e+00 | 120.214 | 0.01114 | 7 |

## Families

- **cap-1, cap-2** — one clothoid turning exactly −180°, 30 mm and 10 mm caps.
- **cap-3** — two clothoids plus a straight return; the first branch tried, which
  loops. Superseded.
- **cap-4** — a copy of `closed-cl-1`; the model.
- **cap-5 … cap-10** — two clothoids ending at `(X, X)` with a straight `X` back
  to the y-axis, X = 10…60.
- **cap-11 … cap-26** — two clothoids ending directly on the y-axis at
  `(0, Y)`, Y = 10…160. The second clothoid is right-leaning.
- **cap-27** — the fold: Y = 162.2817 and `k2 = 0`, so the second clothoid has
  become a straight line. The strictly right-leaning family ends here.

Past the fold, with `k2 > 0` allowed, the same equations continue to solve; `k2`
turns over near Y ≈ 235 (max ≈ 4.4e-5) and the branch still solves at Y = 500.

## Class II: pointed leaves

Both clothoids turn left. They are the **two edges of the leaf**, not a
centreline with rails. The second half is the mirror of the reversed first half,
so its curvature stays positive: `kappa0 = +kd1*L1`, `kd2 = -kd1`, and only the
tangent breaks at the point. The edges end at `(0, 0)` and `(0, Y)`, both
horizontal; the y-axis closes the base. `Y = 2*y(L1)`, so the leaves are ordered by their
first half length.

| file | end y | L1 | corner | fit | cubics |
|---|---|---|---|---|---|
| `cap-pt-1` | 20.0 | 99.772 | 145.32 | 0.01864 | 15 |
| `cap-pt-2` | 40.0 | 126.132 | 124.57 | 0.01863 | 15 |
| `cap-pt-3` | 60.0 | 144.987 | 106.76 | 0.01407 | 15 |
| `cap-pt-4` | 80.0 | 160.355 | 90.41 | 0.01165 | 15 |
| `cap-pt-5` | 100.0 | 173.691 | 74.89 | 0.01937 | 14 |
| `cap-pt-6` | 120.0 | 185.723 | 59.82 | 0.01541 | 15 |
| `cap-pt-7` | 140.0 | 196.878 | 44.95 | 0.01175 | 15 |
| `cap-pt-8` | 160.0 | 207.448 | 30.06 | 0.01607 | 14 |
| `cap-pt-9` | 180.0 | 217.653 | 14.95 | 0.01648 | 13 |

The point closes when the corner reaches zero: `L1 = 227.30`, `Y = 199.239`;
past that the two halves meet smoothly and the leaf is no longer pointed.

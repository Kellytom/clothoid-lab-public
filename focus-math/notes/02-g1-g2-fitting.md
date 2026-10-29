# G1 and G2 fitting with clothoids

## The G1 problem (`buildClothoid`)

Given two points and a direction at each, find the clothoid that passes through
both with those directions. Unknowns: `(κ0, κ', L)`. Three equations: the
integrated endpoint must land on the target point and match the target tangent.

    ∫₀ᴸ cos(½κ'τ² + κ0τ + θ0) dτ = Δx
    ∫₀ᴸ sin(½κ'τ² + κ0τ + θ0) dτ = Δy
    θ0 + κ0L + ½κ'L² = θ1   (mod 2π)

The system is nonlinear and, without a restriction, has more than one solution.
The standard restriction — the tangent turns by less than `2π` — makes it unique.
This is Bertolazzi & Frego, *G1 fitting with clothoids* (2015).

**Where:** `repos/G1fitting/src/Clothoid.cc` (the solver),
`repos/G1fitting/src_mex/mex_buildClothoid.cc` (the call shape: `tol` is the
Newton stop, typically `1e-10`), and `repos/pyclothoids` for the Python surface.

**What to take:**
- Initial guesses matter. The implementation uses a cheap geometric estimate
  before Newton; a naive start fails on long, strongly turned inputs.
- Failures are reported, not thrown away: a non-finite or non-positive `L` must
  be rejected by the caller.
- `tol` is on the residual, not on the parameter step. Two runs at `1e-10` and
  `1e-12` should agree; if they do not, the problem is near-degenerate.

## The G2 problem

Given two points, tangent **and** curvature at each, fit a clothoid. The extra
curvature conditions make the system stiffer; Bertolazzi & Frego (2018) give the
construction, and `vendor/Clothoids` implements it (`build_G2`, cyclic variants,
a smoothing pass). Our CLI already exposes `--g2`, `--smooth`.

## Chained fitting

A spline through a list of points with a shared tangent at each join is a chain
of G1 fits. Curvature is free to jump at each join — the result is G1, not G2,
and the report must say so. `clothoid_lab/interpolate.py` does exactly this and
marks the design `g1` so the report does not fail it.

## The junction question this raises

Chained fitting is one answer to "join a leaf to a branch": put a point with a
direction at the junction and fit a clothoid through it. It gives G1, which may
be enough at a branch foot where a small corner is intended, but not at a
trunk where the eye expects G2. The alternative is a fillet or a spiral spline
(`05-junctions-and-fillets.md`). Keep both in view; do not assume the fitter is
the only way to join two strokes.

## Verdict

Already covered by the engine and by `interpolate.py`. Read `G1fitting` for the
initial-guess strategy and the uniqueness rule; that is the part a rewrite would
get wrong.

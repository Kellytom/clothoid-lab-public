# Clothoids and Fresnel integrals

A clothoid is the curve whose curvature is linear in arc length:
`κ(s) = κ0 + κ' s`. Its position is the Fresnel-type integral

    x(s) = ∫₀ˢ cos(½κ'τ² + κ0τ + θ0) dτ
    y(s) = ∫₀ˢ sin(½κ'τ² + κ0τ + θ0) dτ

There is no closed form in elementary functions. Every implementation is a
choice about how to evaluate these two integrals accurately and quickly.

## How the implementations do it

- **`vendor/Clothoids/src/Fresnel.cc`** — the engine we already build.
  `FresnelCS(y, C, S)` uses a power series for small arguments and an asymptotic
  expansion for large ones, with an explicit convergence failure message. The
  generalised form `GeneralizedFresnelCS` takes the three coefficients
  (κ' s², κ0 s, θ0) and returns cos/sin components, which is how `Clothoid::eval`
  gets position and tangent in one pass.
- **`repos/G1fitting/src/Clothoid.cc`** — the paper's own implementation, same
  two-regime strategy, smaller and easier to read. This is the one to consult
  when checking a sign convention.
- **`repos/euler_spiral`** — a compact C++ Euler spiral; useful as a third
  opinion on the series coefficients.

## What matters to us

1. **Sign conventions.** `κ'` is per unit length squared; a positive `κ'` turns
   left with increasing `s`. The project is y-up. A mismatch here shows up as a
   mirrored curve, not as a numerical error.
2. **Regime switch.** The series loses accuracy as the argument grows; the
   asymptotic expansion loses accuracy near the switch. Any reimplementation
   should be checked against `Clothoids` at the switch point, not only in the
   middle of each regime.
3. **Degenerate cases.** `κ' = 0` is a circle arc; `κ' = κ0 = 0` is a straight
   line. Both must be exact, not approached by the general formula.
4. **Length parameter.** For a fixed endpoint problem, `L` is an unknown, so
   the integrals are evaluated at trial lengths inside a solver — see
   `02-g1-g2-fitting.md`. Speed matters more than in plain evaluation.

## Verdict

We already have the best public implementation, built and tested. Nothing to
port. Read `G1fitting` only when a convention is in doubt.

"""Cubic Bezier fitting for a clothoid span, and the error that the fit costs.

The arm rule is the house's parabola rule, already settled and tested elsewhere:
a cubic spanning one arc-length interval puts its handle along the end tangent
with length |chord| / (3 cos^2(theta/2)), where theta is the angle between that
tangent and the chord. For a span whose curvature is linear in arc length, that
is the right shape, so a span needs only to be short enough for the rule to
hold, not short enough for a different family to hide the error.

Subdivision is adaptive and measured: a span is bisected at its arclength
midpoint while its measured deviation from the true curve exceeds the tolerance.
Nothing is split to a fixed count, and the count is reported afterward.

The point and tangent functions are passed in, so the same fitter serves the
spine and each parallel rail.
"""

from __future__ import annotations

import math


def fit_span(s0: float, s1: float, point, tangent,
             max_arm: float = 4.0) -> dict:
    """One cubic from s0 to s1, on the parabola rule.

    The arm is bounded at `max_arm` times the chord, and a span that hits the
    bound is flagged. The rule divides by the square of the cosine of half the
    angle between the tangent and the chord, so where a curve reverses inside a
    span, which is what a folded rail does, the arm runs away and the control
    point leaves the drawing. A bound turns a 50 metre control point into a
    clamped one and a counted one, which is a fact the report can carry.
    """
    p0 = point(s0)
    p3 = point(s1)
    cx, cy = p3[0] - p0[0], p3[1] - p0[1]
    chord = math.hypot(cx, cy)
    if chord < 1e-12:
        return {"s0": s0, "s1": s1, "p0": p0, "c1": p0, "c2": p3, "p3": p3,
                "clamped": False}

    limit = max_arm * chord
    clamped = False

    def arm(s):
        nonlocal clamped
        ux, uy = math.cos(tangent(s)), math.sin(tangent(s))
        cos = (cx * ux + cy * uy) / chord
        cos = max(-1.0, min(1.0, cos))
        half = (1.0 + cos) / 2.0
        want = chord / (3.0 * half) if half > 1e-9 else limit
        if want > limit:
            clamped = True
            return limit
        return want

    a0, a1 = arm(s0), arm(s1)
    t0, t1 = tangent(s0), tangent(s1)
    return {
        "s0": s0, "s1": s1,
        "p0": p0, "p3": p3,
        "c1": (p0[0] + a0 * math.cos(t0), p0[1] + a0 * math.sin(t0)),
        "c2": (p3[0] - a1 * math.cos(t1), p3[1] - a1 * math.sin(t1)),
        "clamped": clamped,
    }


def cubic_at(span: dict, t: float) -> tuple[float, float]:
    u = 1.0 - t
    a, b, c, d = u * u * u, 3 * u * u * t, 3 * u * t * t, t * t * t
    (x0, y0), (x1, y1) = span["p0"], span["c1"]
    (x2, y2), (x3, y3) = span["c2"], span["p3"]
    return (a * x0 + b * x1 + c * x2 + d * x3, a * y0 + b * y1 + c * y2 + d * y3)


def distance_to_curve(x: float, y: float, s0: float, s1: float, point,
                     coarse: int = 9, refine: int = 40) -> float:
    """Distance from a point to the curve over [s0, s1], minimised on arclength.

    A sampled minimum is not a distance: a straight span would report half the
    sample spacing no matter how well it was fitted. So the coarse scan only
    brackets the nearest arclength, and a golden-section search closes on it.
    """
    span = s1 - s0
    best_s, best_d = s0, float("inf")
    for i in range(coarse):
        s = s0 + span * i / (coarse - 1)
        px, py = point(s)
        d = (x - px) ** 2 + (y - py) ** 2
        if d < best_d:
            best_s, best_d = s, d

    step = span / (coarse - 1)
    lo = max(s0, best_s - step)
    hi = min(s1, best_s + step)
    g = 0.6180339887498949
    m1 = hi - g * (hi - lo)
    m2 = lo + g * (hi - lo)
    px, py = point(m1)
    d1 = (x - px) ** 2 + (y - py) ** 2
    px, py = point(m2)
    d2 = (x - px) ** 2 + (y - py) ** 2
    for _ in range(refine):
        if d1 < d2:
            hi, m2, d2 = m2, m1, d1
            m1 = hi - g * (hi - lo)
            px, py = point(m1)
            d1 = (x - px) ** 2 + (y - py) ** 2
        else:
            lo, m1, d1 = m1, m2, d2
            m2 = lo + g * (hi - lo)
            px, py = point(m2)
            d2 = (x - px) ** 2 + (y - py) ** 2
    return math.sqrt(min(d1, d2))


def span_error(span: dict, point, samples: int = 17) -> float:
    """Worst distance from points on the cubic to the true curve under the span."""
    s0, s1 = span["s0"], span["s1"]
    worst = 0.0
    for i in range(samples):
        x, y = cubic_at(span, i / (samples - 1))
        worst = max(worst, distance_to_curve(x, y, s0, s1, point))
    return worst


def fit_interval(s0: float, s1: float, point, tangent,
                 tol: float = 0.02, max_spans: int = 64,
                 split: int = 2) -> list[dict]:
    """Adaptive fit of [s0, s1], redividing the worst span until it is under tolerance.

    `split` is how many pieces a span that misses the tolerance is cut into.
    Measured on a ninety degree turn at 0.02 mm: bisection reaches the tolerance
    in three spans per segment, a four-way split needs four, and a three-way
    split lands on three with more room to spare. So the factor is a dial on
    evenness and headroom rather than a saving, and two stays the default.
    """
    if split < 2:
        raise ValueError(f"split factor must be at least 2, got {split}")

    spans = [fit_span(s0, s1, point, tangent)]
    errors = [span_error(spans[0], point)]

    while max(errors) > tol and len(spans) < max_spans:
        i = errors.index(max(errors))
        bad = spans.pop(i)
        errors.pop(i)
        cuts = [bad["s0"] + (bad["s1"] - bad["s0"]) * k / split
                for k in range(split + 1)]
        pieces = [fit_span(cuts[k], cuts[k + 1], point, tangent) for k in range(split)]
        pieces = [p for p in pieces if p["s1"] > p["s0"]]
        if not pieces:
            break
        spans[i:i] = pieces
        errors[i:i] = [span_error(p, point) for p in pieces]

    return spans


def fit_chain(chain, tol: float = 0.02, max_spans_per_segment: int = 64,
              split: int = 2) -> tuple[list[dict], dict]:
    """Fit every segment of a chain, and report the numbers behind the drawing."""
    spans: list[dict] = []
    per_segment: list[int] = []
    for placed in chain.segments:
        fitted = fit_interval(placed.s_base, placed.s_base + placed.length,
                              chain.point, chain.tangent,
                              tol=tol, max_spans=max_spans_per_segment, split=split)
        spans.extend(fitted)
        per_segment.append(len(fitted))
    errors = [span_error(s, chain.point) for s in spans]
    return spans, {
        "spans": len(spans),
        "tol": tol,
        "split": split,
        "error_max": max(errors) if errors else 0.0,
        "spans_per_segment": per_segment,
    }


def path_deviation(spans: list[dict], point, samples_per_span: int = 9) -> float:
    """Spacing between the fitted path and the true curve, over a whole chain."""
    worst = 0.0
    for span in spans:
        s0, s1 = span["s0"], span["s1"]
        for i in range(samples_per_span):
            x, y = cubic_at(span, i / (samples_per_span - 1))
            worst = max(worst, distance_to_curve(x, y, s0, s1, point))
    return worst

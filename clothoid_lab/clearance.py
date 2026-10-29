"""Clearance and crossings: does the ink keep its distance?

The rule this module measures is deliberately simple to state:

    two strokes keep at least `clearance` between their edges, and cross
    nowhere except at a contact the caller declares.

Everything here is geometry on the spans a piece already builds. There is no
new dependency and no second source of truth: `piece_clearance()` takes the
same `Group`s that `build_piece()` gives the SVG writer.

Two engineering decisions are worth knowing before reading the numbers.

**Flattening has a bound.** A cubic is replaced by a polyline whose distance
from the curve is at most `tol`. That error is not incidental: the measured
minimum can be smaller than the true minimum by up to twice `tol` (once for
each curve). A gap within that band is therefore reported as a *warning*, not
as a pass or a failure, and a failure is only claimed when the measurement is
below `clearance - 2*tol`.

**Instances own their ink.** A ribbon's two rails are 6 mm apart by design, and
its cap meets its own rails at the tips. Measuring those as if they were two
strokes would report every piece as a violation. So groups are grouped by
`Group.instance`: a trace, or the mirror of one. Only different instances are
compared, which also means the gap between a trace and its mirror is measured,
as it should be.
"""

from __future__ import annotations

import math

from .contact import Contact
from .piece import Group, Piece, build_piece

Point = tuple[float, float]
_EPS = 1e-12


# --------------------------------------------------------------------------
# flattening


def _split(span: dict) -> tuple[dict, dict]:
    """De Casteljau split at t = 0.5, returning the two halves as spans."""
    p0, c1, c2, p3 = span["p0"], span["c1"], span["c2"], span["p3"]
    m01 = ((p0[0] + c1[0]) / 2.0, (p0[1] + c1[1]) / 2.0)
    m12 = ((c1[0] + c2[0]) / 2.0, (c1[1] + c2[1]) / 2.0)
    m23 = ((c2[0] + p3[0]) / 2.0, (c2[1] + p3[1]) / 2.0)
    a = ((m01[0] + m12[0]) / 2.0, (m01[1] + m12[1]) / 2.0)
    b = ((m12[0] + m23[0]) / 2.0, (m12[1] + m23[1]) / 2.0)
    mid = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
    left = {"p0": p0, "c1": m01, "c2": a, "p3": mid}
    right = {"p0": mid, "c1": b, "c2": m23, "p3": p3}
    return left, right


def _flatness(span: dict) -> float:
    """How far the control points stray from the chord: a conservative bound."""
    p0, c1, c2, p3 = span["p0"], span["c1"], span["c2"], span["p3"]
    dx, dy = p3[0] - p0[0], p3[1] - p0[1]
    chord = math.hypot(dx, dy)
    if chord <= _EPS:
        return max(math.dist(p0, c1), math.dist(p0, c2), math.dist(p0, p3))
    worst = 0.0
    for point in (c1, c2):
        # perpendicular distance, no division by a possibly tiny chord
        cross = abs(dx * (point[1] - p0[1]) - dy * (point[0] - p0[0]))
        worst = max(worst, cross / chord)
    return worst


def flatten(spans: list[dict], tol: float = 0.05, max_depth: int = 18) -> list[Point]:
    """A polyline within `tol` of the curve, as points in design space."""
    if tol <= 0:
        raise ValueError("flattening tolerance must be positive")
    if not spans:
        return []
    points: list[Point] = [tuple(spans[0]["p0"])]  # type: ignore[list-item]
    stack = [(span, 0) for span in reversed(spans)]
    while stack:
        span, depth = stack.pop()
        if depth >= max_depth or _flatness(span) <= tol:
            points.append(tuple(span["p3"]))  # type: ignore[arg-type]
        else:
            left, right = _split(span)
            stack.append((right, depth + 1))
            stack.append((left, depth + 1))
    return points


# --------------------------------------------------------------------------
# primitive distances


def _dot(ax, ay, bx, by):
    return ax * bx + ay * by


def segment_distance(p1: Point, q1: Point, p2: Point, q2: Point):
    """Closest points between two segments, as `(distance, point_a, point_b)`.

    The standard clamped-solve of Ericson, *Real-Time Collision Detection* §5.1.9.
    Parallel and degenerate segments are handled explicitly instead of dividing
    by a near-zero denominator.
    """
    d1x, d1y = q1[0] - p1[0], q1[1] - p1[1]
    d2x, d2y = q2[0] - p2[0], q2[1] - p2[1]
    rx, ry = p1[0] - p2[0], p1[1] - p2[1]
    a = _dot(d1x, d1y, d1x, d1y)
    e = _dot(d2x, d2y, d2x, d2y)
    f = _dot(d2x, d2y, rx, ry)

    if a <= _EPS and e <= _EPS:
        s = t = 0.0
    elif a <= _EPS:
        s = 0.0
        t = min(1.0, max(0.0, f / e))
    else:
        c = _dot(d1x, d1y, rx, ry)
        if e <= _EPS:
            t = 0.0
            s = min(1.0, max(0.0, -c / a))
        else:
            b = _dot(d1x, d1y, d2x, d2y)
            denom = a * e - b * b
            s = 0.0 if denom <= _EPS else min(1.0, max(0.0, (b * f - c * e) / denom))
            t = (b * s + f) / e
            if t < 0.0:
                t = 0.0
                s = min(1.0, max(0.0, -c / a))
            elif t > 1.0:
                t = 1.0
                s = min(1.0, max(0.0, (b - c) / a))

    pa = (p1[0] + d1x * s, p1[1] + d1y * s)
    pb = (p2[0] + d2x * t, p2[1] + d2y * t)
    return math.dist(pa, pb), pa, pb


def _segment_hit(p1: Point, q1: Point, p2: Point, q2: Point, eps: float = 1e-9):
    """The intersection point of two segments, or None."""
    r = (q1[0] - p1[0], q1[1] - p1[1])
    s = (q2[0] - p2[0], q2[1] - p2[1])
    denom = r[0] * s[1] - r[1] * s[0]
    qp = (p2[0] - p1[0], p2[1] - p1[1])
    if abs(denom) <= eps:
        # parallel: only a collinear overlap counts, and it is a crossing
        if abs(qp[0] * r[1] - qp[1] * r[0]) > eps:
            return None
        rr = _dot(r[0], r[1], r[0], r[1])
        if rr <= eps:
            return None
        t0 = _dot(qp[0], qp[1], r[0], r[1]) / rr
        t1 = t0 + _dot(s[0], s[1], r[0], r[1]) / rr
        lo, hi = max(0.0, min(t0, t1)), min(1.0, max(t0, t1))
        if hi < lo - eps:
            return None
        t = (lo + hi) / 2.0
        return (p1[0] + r[0] * t, p1[1] + r[1] * t)
    t = (qp[0] * s[1] - qp[1] * s[0]) / denom
    u = (qp[0] * r[1] - qp[1] * r[0]) / denom
    if -eps <= t <= 1 + eps and -eps <= u <= 1 + eps:
        return (p1[0] + r[0] * t, p1[1] + r[1] * t)
    return None


# --------------------------------------------------------------------------
# per-instance geometry


class _Ink:
    """The flattened segments of one instance, plus the names they came from."""

    __slots__ = ("instance", "segments", "points")

    def __init__(self, instance: str):
        self.instance = instance
        self.segments: list[tuple[Point, Point, str]] = []
        self.points: list[Point] = []

    def add(self, group: Group, tol: float) -> None:
        points = flatten(group.spans, tol)
        self.points.extend(points)
        for start, end in zip(points, points[1:]):
            if math.dist(start, end) > _EPS:
                self.segments.append((start, end, group.name))

    @property
    def bbox(self):
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        return min(xs), min(ys), max(xs), max(ys)

    def gap(self, other: "_Ink"):
        """Nearest approach, as `(distance, point_here, point_there, name)`."""
        best = (math.inf, (0.0, 0.0), (0.0, 0.0), "")
        for a0, a1, name in self.segments:
            for b0, b1, _ in other.segments:
                distance, pa, pb = segment_distance(a0, a1, b0, b1)
                if distance < best[0]:
                    best = (distance, pa, pb, name)
        return best

    def near(self, point: Point, radius: float) -> bool:
        """Is any part of this ink within `radius` of `point`?"""
        for a0, a1, _ in self.segments:
            distance, _, _ = segment_distance(a0, a1, point, point)
            if distance <= radius:
                return True
        return False

    def crossings(self, other: "_Ink"):
        hits = []
        for a0, a1, name in self.segments:
            for b0, b1, _ in other.segments:
                hit = _segment_hit(a0, a1, b0, b1)
                if hit is not None:
                    hits.append((hit, name))
        return hits


def _instances(groups: list[Group], tol: float,
               roles=("rail", "cap")) -> dict[str, _Ink]:
    ink: dict[str, _Ink] = {}
    for group in groups:
        if group.role not in roles:
            continue
        instance = ink.setdefault(group.instance, _Ink(group.instance))
        instance.add(group, tol)
    return {name: item for name, item in ink.items() if item.segments}


def _bbox_gap(a, b) -> float:
    """Lower bound on the gap between two boxes, for cheap rejection."""
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(0.0, bx0 - ax1, ax0 - bx1)
    dy = max(0.0, by0 - ay1, ay0 - by1)
    return math.hypot(dx, dy)


def measure(groups: list[Group], clearance: float = 5.0, tol: float = 0.05,
            contacts: list[Contact] | tuple = (),
            roles: tuple[str, ...] = ("rail", "cap")) -> dict:
    """Measure every pair of ink instances and judge the clearance rule.

    Returns a plain dict, so it can be printed, serialised, or asserted on:

    - `ok` — no violation and no disallowed crossing
    - `min` — the closest pair seen, with its location
    - `violations` — pairs below `clearance - 2*tol`
    - `warnings` — pairs inside the flattening band around `clearance`
    - `crossings` — each intersection, allowed only if a `Contact` covers it
    - `merged` — pairs inside a contact footprint whose clearance is waived by
      declaration, reported rather than hidden
    """
    if clearance <= 0:
        raise ValueError("clearance must be positive")
    if tol <= 0:
        raise ValueError("tolerance must be positive")

    ink = _instances(groups, tol, roles)
    names = list(ink)
    margin = 2.0 * tol
    violations, warnings, crossings, merged = [], [], [], []
    best = None
    for i, a_name in enumerate(names):
        a = ink[a_name]
        for b_name in names[i + 1:]:
            b = ink[b_name]
            distance, pa, pb, group = a.gap(b)
            if best is None or distance < best["distance"]:
                best = {
                    "distance": distance,
                    "a": a_name,
                    "b": b_name,
                    "group": group,
                    "at": ((pa[0] + pb[0]) / 2.0, (pa[1] + pb[1]) / 2.0),
                }
            entry = {
                "distance": distance,
                "a": a_name,
                "b": b_name,
                "group": group,
                "at": ((pa[0] + pb[0]) / 2.0, (pa[1] + pb[1]) / 2.0),
            }
            if distance < clearance - margin:
                if any(c.waives_clearance
                       and c.allows(c.point, a_name, b_name)
                       and a.near(c.point, c.radius)
                       and b.near(c.point, c.radius)
                       for c in contacts):
                    entry["merged"] = True
                    merged.append(entry)
                else:
                    entry["shortfall"] = clearance - margin - distance
                    violations.append(entry)
            elif distance < clearance + margin:
                warnings.append(entry)
            # Two shapes whose boxes do not touch cannot cross; skip the
            # segment-pair scan but still report the gap.
            if _bbox_gap(a.bbox, b.bbox) > 1e-9:
                continue
            for point, name in a.crossings(b):
                allowed = any(c.allows(point, a_name, b_name) for c in contacts)
                crossings.append({
                    "at": point,
                    "a": a_name,
                    "b": b_name,
                    "group": name,
                    "allowed": allowed,
                })

    disallowed = [c for c in crossings if not c["allowed"]]
    return {
        "ok": not violations and not disallowed,
        "clearance": clearance,
        "tolerance": tol,
        "margin": margin,
        "min": best,
        "violations": violations,
        "warnings": warnings,
        "crossings": crossings,
        "disallowed": disallowed,
        "merged": merged,
    }


def piece_clearance(piece: Piece, clearance: float = 5.0, tol: float = 0.05,
                    contacts: list[Contact] | tuple | None = None,
                    roles=("rail", "cap"), **build) -> dict:
    """`measure()` over a piece's ink, built the same way the SVG is built.

    Spines are excluded by default: they are construction lines, not ink, and
    a spine is usually closer to its neighbour than the rails are. Pass
    `roles=("spine", "rail", "cap")` to include them.
    """
    if contacts is None:
        contacts = piece.contacts
    groups, info = build_piece(piece, **build)
    result = measure(groups, clearance=clearance, tol=tol, contacts=contacts)
    result["piece"] = info["piece"]
    result["fit_ok"] = info["fit_ok"]
    return result

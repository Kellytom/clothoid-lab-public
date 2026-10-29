"""Junctions, starting with the circular fillet.

A junction is where one stroke meets another: leaf to branch, branch to trunk.
The first primitive is the classic one: a circular arc that is tangent to two
straight edges at a corner. It is G1 — tangent continuous, curvature jumping to
`1/r` at each touch point — which is enough for a foot or a nick, and not enough
for a trunk. The clothoid blend that fixes that is a separate step; this module
is deliberately only the part that can be proved with a ruler.

The construction is the one every CAD sketcher uses. For an interior angle `θ`
at the corner, the arc touches each edge at distance

    T = r / tan(θ/2)

from the corner, its centre sits on the bisector at `r / sin(θ/2)`, and the arc
turns through `π − θ`. The caller gets the two touch points, the centre, the
cubics, the arc length and the trim each edge must give up.

Coordinates are the project's own: design units, y up.
"""

from __future__ import annotations

import math

Point = tuple[float, float]
_EPS = 1e-9


class FilletError(ValueError):
    """The corner cannot take the requested fillet."""


def _unit(dx: float, dy: float) -> Point:
    length = math.hypot(dx, dy)
    if length <= _EPS:
        raise FilletError("corner has a zero-length edge")
    return dx / length, dy / length


def corner_fillet(a: Point, corner: Point, c: Point, radius: float,
                  segments: int = 2) -> dict:
    """A tangent arc at `corner` between the edges `corner → a` and `corner → c`.

    Returns a dict:

    - `start`, `end` — the touch points on the two edges
    - `centre` — the arc centre
    - `angle` — the interior angle at the corner, radians
    - `tangent` — `T`, the distance from the corner to each touch point
    - `trim` — `(T, T)`: how much of each edge the fillet consumes
    - `spans` — cubic spans for the arc, from `start` to `end`
    - `length` — the arc length, `r·(π − θ)`

    Raises `FilletError` when the radius does not fit the shorter edge, when the
    edges are collinear, or when they double back on each other.
    """
    if radius <= 0:
        raise FilletError("fillet radius must be positive")
    if segments < 1:
        raise FilletError("a fillet needs at least one span")

    corner = (float(corner[0]), float(corner[1]))
    ax, ay = a[0] - corner[0], a[1] - corner[1]
    cx, cy = c[0] - corner[0], c[1] - corner[1]
    length_a, length_c = math.hypot(ax, ay), math.hypot(cx, cy)
    ux, uy = _unit(ax, ay)
    vx, vy = _unit(cx, cy)

    cosine = max(-1.0, min(1.0, ux * vx + uy * vy))
    angle = math.acos(cosine)
    if angle <= 1e-6:
        raise FilletError("the edges are collinear; there is no corner to fillet")
    if angle >= math.pi - 1e-6:
        raise FilletError("the edges double back; a fillet needs an interior angle")

    tangent = radius / math.tan(angle / 2.0)
    if tangent > min(length_a, length_c):
        raise FilletError(
            f"radius {radius:g} needs {tangent:.3g} along each edge, "
            f"but the shorter edge is {min(length_a, length_c):.3g}"
        )

    start = (corner[0] + ux * tangent, corner[1] + uy * tangent)
    end = (corner[0] + vx * tangent, corner[1] + vy * tangent)
    bx, by = ux + vx, uy + vy
    if math.hypot(bx, by) <= _EPS:
        raise FilletError("the bisector is undefined for these edges")
    bx, by = _unit(bx, by)
    offset = radius / math.sin(angle / 2.0)
    centre = (corner[0] + bx * offset, corner[1] + by * offset)

    first = math.atan2(start[1] - centre[1], start[0] - centre[0])
    last = math.atan2(end[1] - centre[1], end[0] - centre[0])
    sweep = last - first
    while sweep > math.pi:
        sweep -= 2.0 * math.pi
    while sweep < -math.pi:
        sweep += 2.0 * math.pi
    expected = math.pi - angle
    if abs(abs(sweep) - expected) > 1e-6:
        # Mirror image corners sweep the other way; take the arc that matches.
        sweep = -sweep

    step = sweep / segments
    spans = []
    for index in range(segments):
        t0 = first + step * index
        t1 = t0 + step
        p0 = (centre[0] + radius * math.cos(t0), centre[1] + radius * math.sin(t0))
        p3 = (centre[0] + radius * math.cos(t1), centre[1] + radius * math.sin(t1))
        pull = 4.0 / 3.0 * math.tan(step / 4.0) * radius
        c1 = (p0[0] - pull * math.sin(t0), p0[1] + pull * math.cos(t0))
        c2 = (p3[0] + pull * math.sin(t1), p3[1] - pull * math.cos(t1))
        spans.append({"p0": p0, "c1": c1, "c2": c2, "p3": p3})
    spans[0]["p0"] = start
    spans[-1]["p3"] = end

    return {
        "start": start,
        "end": end,
        "centre": centre,
        "radius": radius,
        "angle": angle,
        "tangent": tangent,
        "trim": (tangent, tangent),
        "spans": spans,
        "sweep": sweep,
        "length": radius * expected,
    }


def arc_segment(fillet: dict) -> dict:
    """The fillet as a circular-arc clothoid segment, ready for a `Design`.

    A circular arc is a clothoid with `kd = 0`, curvature `±1/r` and length
    `r·|sweep|`. The anchor is the arc's start point and its tangent, so the
    segment can follow a straight run in a chain. The join at each end is G1,
    not G2: curvature steps from 0 to `1/r`. That is the fillet, stated plainly.
    """
    radius = fillet["radius"]
    sweep = fillet["sweep"]
    if radius <= 0 or abs(sweep) <= 0:
        raise FilletError("not a fillet")
    start = fillet["start"]
    centre = fillet["centre"]
    # tangent at the start, in the direction of motion
    dx, dy = start[0] - centre[0], start[1] - centre[1]
    sign = 1.0 if sweep > 0 else -1.0
    tx, ty = -dy * sign, dx * sign
    return {
        "anchor": {"x": start[0], "y": start[1],
                   "angle": math.atan2(ty, tx)},
        "segment": {"kd": 0.0, "length": radius * abs(sweep),
                    "kappa0": sign / radius},
    }


def fillet_span(spans: list[dict], index: int, radius: float) -> list[dict]:
    """Replace the corner between spans `index` and `index + 1` with a fillet.

    Only straight spans are handled: the corner is where one span ends, and the
    trim is measured back along each span's own chord. Anything curved raises
    `FilletError` rather than pretending the tangent point is on the chord.
    """
    if index < 0 or index + 1 >= len(spans):
        raise FilletError("no corner at that index")
    left, right = spans[index], spans[index + 1]
    for span in (left, right):
        if not _straight(span):
            raise FilletError("fillet_span only handles straight spans")
    corner = (left["p3"][0], left["p3"][1])
    fillet = corner_fillet(left["p0"], corner, right["p3"], radius)
    trim_a, trim_b = fillet["trim"]

    def cut(span: dict, keep: float, from_end: bool) -> dict:
        p0, p3 = span["p0"], span["p3"]
        length = math.dist(p0, p3)
        if keep >= length:
            raise FilletError("the fillet consumes the whole span")
        if from_end:
            ratio = (length - keep) / length
            point = (p0[0] + (p3[0] - p0[0]) * ratio,
                     p0[1] + (p3[1] - p0[1]) * ratio)
            return {"p0": p0, "c1": p0, "c2": point, "p3": point}
        ratio = keep / length
        point = (p0[0] + (p3[0] - p0[0]) * ratio,
                 p0[1] + (p3[1] - p0[1]) * ratio)
        return {"p0": point, "c1": point, "c2": p3, "p3": p3}

    return [cut(left, trim_a, True), *fillet["spans"], cut(right, trim_b, False)]


def _straight(span: dict, tol: float = 1e-6) -> bool:
    p0, p3 = span["p0"], span["p3"]
    chord = math.dist(p0, p3)
    if chord <= _EPS:
        return False
    return all(_line_distance(p0, p3, span[key]) <= tol for key in ("c1", "c2"))


def _line_distance(p: Point, q: Point, x: Point) -> float:
    dx, dy = q[0] - p[0], q[1] - p[1]
    length = math.hypot(dx, dy)
    return abs(dx * (x[1] - p[1]) - dy * (x[0] - p[0])) / length

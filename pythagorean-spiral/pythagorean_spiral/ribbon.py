"""Rails and ribbons: a width around an exact chain.

The spine is a chain of rational points, so a rail is exact too. The normal of
a chord is its heading turned a quarter turn -- a swap of two rationals -- and
the meeting of two offset chord lines is the intersection of two rational
lines, which is rational. Nothing is normalized, so nothing becomes a square
root.

A rail is a **miter** offset: each chord is shifted by half the width and
adjacent shifted lines are intersected. That keeps the station count and makes
the rail corner land exactly where the spine's corner is. The limitation is the
usual one: at a width larger than the inside radius the rail folds through
itself, and this module does not repair that -- it reports nothing and lets the
drawing show it.

`taper` is a count of chords. The width ramps from zero at each end to full
over that many chords, which is what makes a leaf tip rather than a cut end.
"""

from __future__ import annotations

import math
from fractions import Fraction

from .exact import Dir


def _points(points):
    return [(Fraction(x), Fraction(y)) for x, y in points]


def _length(dx: Fraction, dy: Fraction) -> Fraction:
    """The chord length, or a refusal: a rail needs an exact direction."""
    sq = dx * dx + dy * dy
    n, d = sq.numerator, sq.denominator
    rn, rd = math.isqrt(n), math.isqrt(d)
    if rn * rn != n or rd * rd != d:
        raise ValueError("chord length is not rational; not a chain of this kind")
    return Fraction(rn, rd)


def directions(points) -> list[Dir]:
    """The exact heading of every chord, recovered from the points alone.

    The length of a chain chord is rational by construction, so dividing the
    difference by it stays in the rationals. Composite chains -- arcs of
    different lengths joined at nodes -- work without carrying a Spiral object.
    """
    pts = _points(points)
    if len(pts) < 2:
        raise ValueError("a rail needs at least one chord")
    out = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        dx, dy = x1 - x0, y1 - y0
        length = _length(dx, dy)
        if length == 0:
            raise ValueError("a zero-length chord has no direction")
        out.append(Dir(dx / length, dy / length))
    return out


def _meet(p, u: Dir, q, v: Dir):
    """Intersect p + t*u and q + s*v exactly; None when they are parallel."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    det = v.re * u.im - u.re * v.im
    if det == 0:
        return None
    t = (dy * v.re - dx * v.im) / det
    return (p[0] + t * u.re, p[1] + t * u.im)


def _shift(p, distance, normal: Dir):
    """Move a point along a rational unit direction by a rational distance."""
    return (p[0] + distance * normal.re, p[1] + distance * normal.im)


def _widths(n: int, width, taper: int):
    w = Fraction(width)
    if w < 0:
        raise ValueError(f"width must be zero or more, got {width}")
    if taper < 0:
        raise ValueError(f"taper must be zero or more chords, got {taper}")
    out = []
    for k in range(n + 1):
        f = 1 if not taper else min(Fraction(1), Fraction(k, taper),
                                    Fraction(n - k, taper))
        out.append(w * f)
    return out


def rail(points, width, side: int = 1, taper: int = 0):
    """One rail: the miter offset of the chain at `side` (+1 left, -1 right)."""
    pts = _points(points)
    heads = directions(pts)
    n = len(heads)
    w = _widths(n, width, taper)
    if side not in (1, -1):
        raise ValueError(f"side must be +1 or -1, got {side}")

    base = [_shift(pts[i], side * (w[i] + w[i + 1]) / 2,
                   heads[i].quarter(1)) for i in range(n)]
    out = [_shift(pts[0], side * w[0], heads[0].quarter(1))]
    for k in range(1, n):
        hit = _meet(base[k - 1], heads[k - 1], base[k], heads[k])
        # a straight run has parallel offset lines; the node is already on both
        out.append(hit if hit is not None
                   else _shift(pts[k], side * w[k], heads[k].quarter(1)))
    out.append(_shift(pts[n], side * w[n], heads[n - 1].quarter(1)))
    return out


def rails(points, width, taper: int = 0):
    """Both rails, left first. Each has one point per node, exactly."""
    return (rail(points, width, +1, taper), rail(points, width, -1, taper))


# -- the float twin -----------------------------------------------------
def _float_points(points):
    return [(float(x), float(y)) for x, y in points]


def _unit_float(points):
    out = []
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy)
        if length == 0:
            raise ValueError("a zero-length chord has no direction")
        out.append((dx / length, dy / length))
    return out


def _meet_float(p, u, q, v):
    det = v[0] * u[1] - u[0] * v[1]
    if det == 0:
        return None
    dx, dy = q[0] - p[0], q[1] - p[1]
    t = (dy * v[0] - dx * v[1]) / det
    return (p[0] + t * u[0], p[1] + t * u[1])


def rail_float(points, width, side: int = 1, taper: int = 0):
    """The same miter offset in doubles, for chains too long to afford exact.

    Nothing here is exact: the headings are normalized with `hypot`, so the
    rail is right to about 1e-15 rather than exact. Use `rail` when the chain
    is small and the exactness matters.
    """
    pts = _float_points(points)
    heads = _unit_float(pts)
    n = len(heads)
    w = [float(v) for v in _widths(n, width, taper)]
    if side not in (1, -1):
        raise ValueError(f"side must be +1 or -1, got {side}")

    def shift(p, d, h):
        # left normal of (hx, hy) is (-hy, hx); `d` already carries the side
        return (p[0] - d * h[1], p[1] + d * h[0])

    base = [shift(pts[i], side * (w[i] + w[i + 1]) / 2, heads[i])
            for i in range(n)]
    out = [shift(pts[0], side * w[0], heads[0])]
    for k in range(1, n):
        hit = _meet_float(base[k - 1], heads[k - 1], base[k], heads[k])
        out.append(hit if hit is not None
                   else shift(pts[k], side * w[k], heads[k]))
    out.append(shift(pts[n], side * w[n], heads[n - 1]))
    return out


def rails_float(points, width, taper: int = 0):
    return (rail_float(points, width, +1, taper),
            rail_float(points, width, -1, taper))


def outline_float(points, width, taper: int = 0):
    left, right = rails_float(points, width, taper)
    return left + list(reversed(right))


def outline(points, width, taper: int = 0):
    """The closed ribbon: left rail out, right rail back.

    The start and end are not repeated; an SVG fill closes the path, and the
    two ends are a square cut unless `taper` brings the rails together.
    """
    left, right = rails(points, width, taper)
    return left + list(reversed(right))

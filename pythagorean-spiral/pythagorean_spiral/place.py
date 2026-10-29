"""Placement on the integer lattice: rotate, scale, fit, quantize.

A chain's points are rational, and its rotation group is rational too: the
triangle's direction, its powers, and quarter turns. So a placement that uses
only those rotations, a rational scale and a rational offset keeps every point
rational and can be written as integers over a common denominator.

Any other angle -- 30 degrees, 45, a decorative tilt -- leaves the group. It is
still available, but only in floats, and it must be quantized to the lattice
like any other float drawing. That is the line this module draws.
"""

from __future__ import annotations

import math
from fractions import Fraction

from .exact import Dir


def rotation(triangle, turns: int = 0, quarter: int = 0) -> Dir:
    """A rotation from the chain's own group, exactly."""
    return (triangle.direction ** int(turns)).quarter(int(quarter))


def rotate(p, d: Dir):
    """Rotate a point (rational or float) by an exact rational direction."""
    x, y = p
    return (x * d.re - y * d.im, x * d.im + y * d.re)


def place(points, rotation: Dir | None = None, scale=1, offset=(0, 0)):
    """Rotate, scale and translate rational points, exactly."""
    d = rotation or Dir.east()
    s = Fraction(scale)
    ox, oy = Fraction(offset[0]), Fraction(offset[1])
    out = []
    for p in points:
        x, y = Fraction(p[0]), Fraction(p[1])
        rx, ry = x * d.re - y * d.im, x * d.im + y * d.re
        out.append((rx * s + ox, ry * s + oy))
    return out


def bounds(points):
    xs = [float(p[0]) for p in points]
    ys = [float(p[1]) for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def lattice(points):
    """The same points as integers over one common denominator."""
    den = 1
    for x, y in points:
        den = math.lcm(den, Fraction(x).denominator, Fraction(y).denominator)
    return [(int(Fraction(x) * den), int(Fraction(y) * den))
            for x, y in points], den


def quantize(points, units_per_unit: int = 1000, offset=(0, 0)):
    """Snap float points to an integer grid, in grid units.

    `units_per_unit` is the lattice resolution: 1000 means thousandths of the
    drawings's own unit. This is the float path's lattice; the exact path uses
    `lattice()` and needs no rounding.
    """
    if not isinstance(units_per_unit, int) or units_per_unit < 1:
        raise ValueError("units_per_unit must be a positive integer")
    ox, oy = offset
    return [(int(round((float(x) - ox) * units_per_unit)),
             int(round((float(y) - oy) * units_per_unit)))
            for x, y in points]


def fit(points, box=(200, 250), margin=2, units_per_unit: int = 1000,
        rotation: Dir | None = None):
    """Largest uniform scale that puts the points in the box, then lattice it.

    Returns `(int_points, scale)` with every point an integer in grid units,
    inset by `margin` on all four sides. The rotation must come from the
    group (`rotation()`); anything else belongs to `quantize()`.
    """
    if margin < 0:
        raise ValueError("margin must be zero or more")
    w, h = box
    if w <= 2 * margin or h <= 2 * margin:
        raise ValueError("the box is smaller than its margin")
    placed = place(points, rotation=rotation)
    x0, y0, x1, y1 = bounds(placed)
    sx, sy = x1 - x0, y1 - y0
    if sx <= 0 and sy <= 0:
        raise ValueError("a single point has no scale to fit")
    s = min((w - 2 * margin) / sx if sx > 0 else math.inf,
            (h - 2 * margin) / sy if sy > 0 else math.inf)
    out = []
    for x, y in placed:
        gx = margin * units_per_unit + (float(x) - x0) * s * units_per_unit
        gy = margin * units_per_unit + (float(y) - y0) * s * units_per_unit
        out.append((int(round(gx)), int(round(gy))))
    return out, s

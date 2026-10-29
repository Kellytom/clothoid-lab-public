"""The veil as geometry, in versions.

v1 -- the original cloud.  One exact ellipse per entry, in the composition the
      operator approved ("good in principle, just needed more transparency").
      Its only fault was opacity: the drawing gave the base layer the veil
      factor and left every other layer at full body, while the report gave
      every layer the veil factor.  The report said five per cent; the picture
      was opaque.  Here every layer carries the veil factor, so the model and
      the drawing agree and the cloud is simply more transparent.

v2 -- turn-chain billows.  A billow is a ribbon along a lobe, and the lobe is
      the p-triple chain: turns k**p out, then the same integers back, so the
      exit is exactly parallel to the entry.  `ribbon.outline` offsets it with
      a rational taper, giving one closed rational polygon with pointed ends --
      a brush mark rather than a disc.  The power dial is the layer.

Both versions expose the same three functions -- `polygons`, `weights_at`,
`alpha` -- so one measurement serves both, and a strip cannot pass on paper
while the drawing covers it.

Construction is exact: circle points are rational, rails are rational, taper is
rational.  Placement -- scaling to a box, tilting -- is float, because the cloud
is a composition, not a lattice drawing.
"""

from __future__ import annotations

import math
from fractions import Fraction
from functools import lru_cache

from . import design, place, ribbon
from .exact import Dir
from .spiral import Spiral
from .triples import for_angle

VERSIONS = ("v1", "v2")

# ---------------------------------------------------------------- v1 -----
# the original composition: one ellipse per entry
ELLIPSES = [
    # haze: the outer breath
    (24, 39, 6, 4, -4, "haze"), (90, 40, 5, 4, 3, "haze"),
    (30, 36, 5, 3.5, 5, "haze"),
    (40, 71, 4, 3.5, 5, "haze"), (70, 68, 4, 3.5, -5, "haze"),
    # base: the flat underside
    (38, 34, 9, 4.5, 2, "bank"), (52, 38, 11, 4.5, -1, "bank"),
    (66, 36, 9, 4.5, 3, "bank"), (79, 41, 7, 4, -3, "bank"),
    # the veil down over the works
    (24, 20, 9, 6, -3, "bank"), (42, 18, 11, 6, 3, "bank"),
    (60, 19, 11, 6, -2, "bank"), (78, 21, 9, 6, 4, "bank"),
    (32, 27, 10, 8, -5, "billow"), (50, 29, 11, 9, 4, "billow"),
    (68, 28, 10, 9, -3, "billow"), (84, 30, 8, 7, 5, "billow"),
    # the veil reaches the bottom of the pictures, not just their tops
    (24, 12, 11, 5, -2, "bank"), (44, 11, 13, 5, 3, "bank"),
    (64, 12, 12, 5, -3, "bank"), (84, 14, 9, 4.5, 4, "bank"),
    (36, 6, 10, 4.5, -2, "bank"), (56, 5, 11, 4.5, 3, "bank"),
    (76, 6, 10, 4.5, -3, "bank"),
    # lower lobes
    (36, 42, 10, 8, -5, "billow"), (50, 44, 12, 9, 3, "billow"),
    (65, 43, 10, 8, -4, "billow"), (79, 41, 7, 6, 5, "billow"),
    # middle
    (42, 52, 8, 7, 4, "billow"), (56, 55, 9, 8, -3, "billow"),
    (70, 52, 7, 7, 5, "billow"),
    # upper and crown
    (48, 62, 6, 6, -4, "crown"), (60, 63, 6, 6, 3, "crown"),
    (54, 69, 5, 4.5, -3, "crown"),
]
# As it was: the bodies the operator approved, shading included.
V1_LAYER = {"haze": 0.14, "bank": 0.34, "billow": 0.46, "crown": 0.60,
            "shade": 0.12, "light": 0.16}

# The old cloud read by shading, not by outline: every billow and crown carried
# a darker under-lobe and a cream top.  Those strokes used to sit outside the
# opacity model; here they are billows like any other, so the measurement
# counts them.
SHADING = ((1.8, -3.4, 1.02, 0.92, "shade"),
           (-1.4, 2.6, 0.84, 0.78, "light"))


# One puff becomes several smaller ellipses.  Drawn at full size they were a
# fog: a handful of washes with no edge inside them.  The same composition at
# a third of the radius, repeated, has structure -- and the lobes still overlap.
CLUSTER = ((-0.45, -0.30, 0.42, 0), (0.42, -0.25, 0.38, 1),
           (-0.05, 0.38, 0.44, -1), (0.10, -0.02, 0.30, 2))


def _v1_ellipses():
    out = []
    for cx, cy, rx, ry, tilt, layer in ELLIPSES:
        for dx, dy, k, step in CLUSTER:
            ex, ey = cx + dx * rx * 2.2, cy + dy * ry * 2.2
            er, es = rx * k * 2.2, ry * k * 2.2
            out.append((ex, ey, er, es, tilt + step, layer))
            if layer in ("billow", "crown"):
                for sx, sy, kx, ky, under in SHADING:
                    out.append((ex + sx * er, ey + sy * es, er * kx,
                                es * ky, tilt + step, under))
    return out

# ---------------------------------------------------------------- v2 -----
V2_LAYER = {"haze": 0.10, "bank": 0.09, "billow": 0.30, "crown": 0.42,
            "shade": 0.14, "light": 0.18}

# shape per layer for v2: (power, steps, width, taper) -- the dial is the layer
SHAPE = {
    "haze":   (1, 9, 1.10, 4),
    "bank":   (2, 7, 1.30, 3),
    "billow": (2, 9, 1.50, 3),
    "crown":  (3, 7, 1.40, 2),
}

CHORD = 6.0  # degrees per chord: the resolution budget, not a look

PUFTS = [
    # haze: the outer breath
    (24, 39, 6, 4, -4, "haze"), (90, 40, 5, 4, 3, "haze"),
    (30, 36, 5, 3.5, 5, "haze"),
    (40, 71, 4, 3.5, 5, "haze"), (70, 68, 4, 3.5, -5, "haze"),
    # base: the flat underside
    (38, 34, 9, 4.5, 2, "bank"), (52, 38, 11, 4.5, -1, "bank"),
    (66, 36, 9, 4.5, 3, "bank"), (79, 41, 7, 4, -3, "bank"),
    # the veil down over the works: haze only, because the images are there
    (24, 20, 9, 6, -3, "haze"), (42, 18, 11, 6, 3, "haze"),
    (60, 19, 11, 6, -2, "haze"), (78, 21, 9, 6, 4, "haze"),
    (32, 27, 10, 8, -5, "haze"), (50, 29, 11, 9, 4, "haze"),
    (68, 28, 10, 9, -3, "haze"), (84, 30, 8, 7, 5, "haze"),
    # the veil reaches the bottom of the pictures, not just their tops
    (24, 12, 11, 5, -2, "bank"), (44, 11, 13, 5, 3, "bank"),
    (64, 12, 12, 5, -3, "bank"), (84, 14, 9, 4.5, 4, "bank"),
    (36, 6, 10, 4.5, -2, "bank"), (56, 5, 11, 4.5, 3, "bank"),
    (76, 6, 10, 4.5, -3, "bank"),
    # lower lobes
    (36, 46, 9, 6, -5, "billow"), (50, 48, 11, 7, 3, "billow"),
    (65, 47, 9, 6, -4, "billow"), (79, 45, 7, 5, 5, "billow"),
    # middle
    (42, 52, 8, 7, 4, "billow"), (56, 55, 9, 8, -3, "billow"),
    (70, 52, 7, 7, 5, "billow"),
    # upper and crown
    (48, 62, 6, 6, -4, "crown"), (60, 63, 6, 6, 3, "crown"),
    (54, 69, 5, 4.5, -3, "crown"),
]

# each puff gets three lobes: offsets as fractions of its radii, a size, a
# quarter-turn and a power step off the layer's own.  Deterministic on purpose.
SPREAD = ((-0.30, -0.22, 0.92, 0, 0),
          (0.28, 0.20, 0.78, 1, 1),
          (0.02, 0.30, 0.62, -1, -1))

CANVAS = (0.0, 0.0, 120.0, 80.0)  # corners x0, y0, x1, y1

# A lens fills about half its box, so v2's billows are drawn at this multiple
# of the placement box to make the mass read as a cloud.
SCALE = 1.55

# compatibility: the v2 tables under their old names
BILLOWS = None  # set below
LAYER = V2_LAYER


def layers(version="v2"):
    return V1_LAYER if version == "v1" else V2_LAYER


def _spread():
    """Puffs into lobes, each with its own shaped under-lobe and top."""
    out = []
    for cx, cy, rx, ry, tilt, layer in PUFTS:
        power, steps, width, taper = SHAPE[layer]
        for dx, dy, size, quarter, dstep in SPREAD:
            p = max(1, power + dstep)
            base = (cx + dx * rx, cy + dy * ry, rx * size, ry * size,
                    tilt + quarter)
            out.append(base + (layer, p, layer))
            for sx, sy, kx, ky, under in SHADING:
                out.append((base[0] + sx * size, base[1] + sy * size,
                            base[2] * kx, base[3] * ky, base[4],
                            under, p, layer))
    return out


BILLOWS = _spread()


@lru_cache(maxsize=None)
def _circle():
    """The turn-chain circle, **normalised to radius 1**.

    The polygon's own radius is 1/(2 sin(alpha/2)) -- about 9.5 at a 6-degree
    chord -- so every billow used to be drawn at 9.5 times the radius it asked
    for, and a handful of them blanketed the whole image.  The circumradius is
    irrational, so this is the one place exactness stops being rational: the
    shape is still the exact polygon, its scale is a float.
    """
    tri = for_angle(2.0)
    n = round(360 / tri.degrees)
    path = Spiral(tri, 1, heading=Dir.east())
    path.extend([0] + [1] * (n - 1))
    nodes = [(float(x), float(y)) for x, y in path.nodes]
    # the chain closes through the origin, so the circle's centre is the mean
    cx = sum(x for x, _ in nodes[:-1]) / (len(nodes) - 1)
    cy = sum(y for _, y in nodes[:-1]) / (len(nodes) - 1)
    r = max(math.hypot(x - cx, y - cy) for x, y in nodes)
    return tuple(((x - cx) / r, (y - cy) / r) for x, y in nodes), tri


def _ellipse(cx, cy, rx, ry, tilt):
    pts, tri = _circle()
    d = place.rotation(tri, int(tilt))
    out = []
    for x, y in pts:
        q = place.rotate((Fraction(rx) * Fraction(x).limit_denominator(10 ** 9),
                          Fraction(ry) * Fraction(y).limit_denominator(10 ** 9)), d)
        out.append((float(q[0]) + cx, float(q[1]) + cy))
    return tuple(out)


@lru_cache(maxsize=None)
def _unit_outline(layer: str, power: int):
    """One v2 billow at chord length 1, exact, centred on its own box."""
    _p, steps, width, taper = SHAPE[layer]
    lobe = design.lobe(for_angle(CHORD), steps, 1, power=power)
    pts = ribbon.outline(lobe.nodes, width, taper)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    cx = (min(xs) + max(xs)) / 2
    cy = (min(ys) + max(ys)) / 2
    hw = max(Fraction(1, 10 ** 6), (max(xs) - min(xs)) / 2)
    hh = max(Fraction(1, 10 ** 6), (max(ys) - min(ys)) / 2)
    return tuple(((x - cx) / hw, (y - cy) / hh) for x, y in pts)


@lru_cache(maxsize=None)
def polygons(version="v2"):
    """Every billow as a closed float polygon in canvas coordinates."""
    out = []
    if version == "v1":
        for cx, cy, rx, ry, tilt, layer in _v1_ellipses():
            out.append((layer, _ellipse(cx, cy, rx, ry, tilt)))
        return tuple(out)
    for cx, cy, rx, ry, tilt, layer, power, shape in BILLOWS:
        a = math.radians(tilt * for_angle(CHORD).degrees)
        ca, sa = math.cos(a), math.sin(a)
        pts = []
        for x, y in _unit_outline(shape, power):
            u, v = float(x) * rx * SCALE, float(y) * ry * SCALE
            pts.append((cx + u * ca - v * sa, cy + u * sa + v * ca))
        out.append((layer, tuple(pts)))
    return tuple(out)


def _inside(poly, x, y):
    hit = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            if x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                hit = not hit
    return hit


def weights_at(x, y, version="v2"):
    """The bodies covering a point, one per billow.  No veil factor yet."""
    w = layers(version)
    return tuple(w[layer] for layer, poly in polygons(version)
                 if _inside(poly, x, y))


def alpha_of(weights, veil):
    """Composite alpha of the given bodies at one veil factor."""
    a = 0.0
    for w in weights:
        a = a + (1 - a) * w * veil
    return a


def alpha(x, y, veil, version="v2"):
    return alpha_of(weights_at(x, y, version), veil)


def grid(x0, y0, x1, y1, nx, ny):
    return [(x0 + (x1 - x0) * i / (nx - 1), y0 + (y1 - y0) * j / (ny - 1))
            for j in range(ny) for i in range(nx)]


# the two test rows as corners (x0, y0, x1, y1), y up: where the four standard
# patterns sit.  `row_box` turns a row into the (x, y, w, h) that `panel` wants.
TOP_ROW = (14.0, 32.0, 106.0, 48.0)
BOTTOM_ROW = (14.0, 8.0, 106.0, 24.0)


@lru_cache(maxsize=None)
def field(box=None, step: float = 2.0, version="v2"):
    """Coverage weights on a fixed grid, so a solve is arithmetic, not geometry."""
    x0, y0, x1, y1 = CANVAS if box is None else box
    nx = max(2, int(round((x1 - x0) / step)) + 1)
    ny = max(2, int(round((y1 - y0) / step)) + 1)
    return tuple((x, y, weights_at(x, y, version))
                 for x, y in grid(x0, y0, x1, y1, nx, ny))


def worst(veil, box=None, step: float = 2.0, version="v2"):
    return max(alpha_of(w, veil) for _, _, w in field(box, step, version))


def panel(box, veil, nx=17, ny=13, version="v2"):
    """Mean, 95th percentile and worst alpha over one box (x, y, w, h)."""
    x0, y0, w, h = box
    values = sorted(alpha(x, y, veil, version)
                    for x, y in grid(x0, y0, x0 + w, y0 + h, nx, ny))
    n = len(values)
    return {"mean": sum(values) / n, "p95": values[min(n - 1, int(0.95 * n))],
            "max": values[-1]}


def row_box(row):
    """(x, y, w, h) for a row name, from TOP_ROW / BOTTOM_ROW."""
    x0, y0, x1, y1 = TOP_ROW if row == "top" else BOTTOM_ROW
    return (x0, y0, x1 - x0, y1 - y0)


def solve(target, box=None, step: float = 2.0, version="v2",
          lo=0.0, hi=1.0):
    """The largest veil factor whose worst point in `box` stays under target."""
    samples = field(box, step, version)
    def check(v):
        return max(alpha_of(w, v) for _, _, w in samples)
    if check(hi) <= target:
        return hi
    for _ in range(30):
        mid = (lo + hi) / 2
        if check(mid) > target:
            hi = mid
        else:
            lo = mid
    return lo

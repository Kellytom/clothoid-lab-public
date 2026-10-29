"""Engine: place a chain of clothoid segments in the plane and read it back.

The geometry itself comes from a backend: either the compiled Clothoids
library or the wheel, both the same source reached two ways. This module owns
the parts that are ours whatever the backend: resolving each segment's starting
curvature, carrying position and direction across joins, measuring the
continuity that results, and exposing one global arc length.

Continuity is structural and measured. A join inherits position, tangent and,
when `kappa0` is null, curvature. A curvature set by hand is honoured and the
jump against the previous end is reported, never smoothed.
"""

from __future__ import annotations

import math

from . import backend as backends
from .model import Design


class Placed:
    """Segment metadata: where it starts on the chain and what it starts from.

    No geometry lives here. That is the point: the backend holds the curve, so
    the numbers cannot drift between a Python copy and the library's own.
    """

    __slots__ = ("index", "s_base", "length", "k0", "kd", "t0")

    def __init__(self, index, s_base, length, k0, kd, t0):
        self.index = index
        self.s_base = s_base
        self.length = length
        self.k0 = k0
        self.kd = kd
        self.t0 = t0

    def tangent(self, s_local: float) -> float:
        return self.t0 + self.k0 * s_local + 0.5 * self.kd * s_local * s_local

    def kappa(self, s_local: float) -> float:
        return self.k0 + self.kd * s_local

    def turn(self) -> float:
        """Total turning over the segment, in radians."""
        return self.k0 * self.length + 0.5 * self.kd * self.length ** 2


class Chain:
    """The placed chain, addressed by one global arc length."""

    def __init__(self, curve, placed: list[Placed], design: Design, joins: list[dict],
                 backend_name: str):
        self.curve = curve
        self.segments = placed
        self.design = design
        self.joins = joins
        self.backend = backend_name
        self.length = curve.length

    # -- geometry, straight from the backend ------------------------------

    def point(self, s: float) -> tuple[float, float]:
        return self.curve.point(s)

    def tangent(self, s: float) -> float:
        return self.curve.tangent(s)

    def kappa(self, s: float) -> float:
        return self.curve.kappa(s)

    def offset_point(self, s: float, distance: float) -> tuple[float, float]:
        return self.curve.offset_point(s, distance)

    def normal(self, s: float) -> tuple[float, float]:
        a = self.tangent(s)
        return (-math.sin(a), math.cos(a))

    # -- readings ---------------------------------------------------------

    def locate(self, s: float) -> tuple[Placed, float]:
        s = min(max(s, 0.0), self.length)
        for p in self.segments:
            if s <= p.s_base + p.length + 1e-12:
                return p, min(s - p.s_base, p.length)
        last = self.segments[-1]
        return last, last.length

    def sample(self, n: int) -> list[tuple[float, float, float]]:
        if n < 2:
            raise ValueError("need at least two sample points")
        out = []
        for i in range(n):
            s = self.length * i / (n - 1)
            x, y = self.point(s)
            out.append((x, y, s))
        return out

    def min_radius(self) -> tuple[float, float]:
        """Smallest radius of curvature on the chain, as (radius, s)."""
        best, best_s = float("inf"), 0.0
        n = max(64, len(self.segments) * 64)
        for i in range(n + 1):
            s = self.length * i / n
            k = abs(self.kappa(s))
            if k > 1e-12 and 1.0 / k < best:
                best, best_s = 1.0 / k, s
        return best, best_s

    def bounds(self) -> tuple[float, float, float, float]:
        return self.curve.bounds()

    @property
    def g2(self) -> bool:
        return all(abs(j["d_kappa"]) < 1e-9 and abs(j.get("corner", 0.0)) < 1e-12
                   for j in self.joins)

    @property
    def max_join_kappa_error(self) -> float:
        return max((abs(j["d_kappa"]) for j in self.joins), default=0.0)

    @property
    def max_corner(self) -> float:
        return max((abs(j.get("corner", 0.0)) for j in self.joins), default=0.0)

    @property
    def corner_count(self) -> int:
        return sum(1 for j in self.joins if abs(j.get("corner", 0.0)) >= 1e-12)

    def close(self):
        close = getattr(self.curve, "close", None)
        if close:
            close()


def build(design: Design, backend: str | None = None) -> Chain:
    """Resolve the design, then hand the geometry to the backend."""
    module = backends.load(backend)

    x = float(design.anchor.get("x", 0.0))
    y = float(design.anchor.get("y", 0.0))
    t_anchor = float(design.anchor.get("angle", 0.0))
    t = t_anchor

    k = 0.0
    s_base = 0.0
    resolved: list[dict] = []
    placed: list[Placed] = []
    joins: list[dict] = []

    for i, seg in enumerate(design.segments):
        corner = float(seg.corner) if i > 0 else 0.0
        t += corner
        k0 = k if seg.kappa0 is None else float(seg.kappa0)
        if i > 0:
            joins.append({
                "at": s_base,
                "between": (i - 1, i),
                "d_kappa": k0 - k,
                "corner": corner,
                "inherited": seg.kappa0 is None,
            })
        entry = {"k0": k0, "kd": seg.kd, "length": seg.length, "corner": corner}
        resolved.append(entry)
        piece = Placed(i, s_base, seg.length, k0, seg.kd, t)
        placed.append(piece)
        k = k0 + seg.kd * seg.length
        t = piece.tangent(seg.length)
        s_base += seg.length

    curve = module.build_curve(resolved, {"x": x, "y": y, "angle": t_anchor})
    return Chain(curve, placed, design, joins, module.NAME)


def report(chain: Chain) -> dict:
    """The numbers that decide whether the drawing is what the design asked for."""
    r_min, r_at = chain.min_radius()
    x0, y0, x1, y1 = chain.bounds()
    return {
        "segments": len(chain.segments),
        "length": chain.length,
        "join_g2": chain.g2,
        "join_kappa_error_max": chain.max_join_kappa_error,
        "corner_count": chain.corner_count,
        "corner_max": chain.max_corner,
        "min_radius": r_min,
        "min_radius_at": r_at,
        "bounds": (x0, y0, x1, y1),
        "backend": chain.backend,
    }

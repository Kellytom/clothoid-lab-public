"""Sections: one station across a full line.

A section is the authoring view of a stroke: the spine, its tangent, the width
law's value there, and the two rails derived from them. Rendering fits the rails
to cubics; measurement flattens those cubics. Both are approximations of this,
the thing the design actually means.

Left is ``(-t.y, t.x)`` for tangent ``t`` in a y-up plane, so the left rail is on
the left of travel. Mirroring swaps the two.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from . import engine
from .piece import Trace

Point = tuple[float, float]


@dataclass(frozen=True)
class Section:
    """The full line at one arc length."""

    s: float
    spine: Point
    tangent: Point
    width: float
    left: Point
    right: Point

    @property
    def half_width(self) -> float:
        return self.width / 2.0


def sections(trace: Trace, samples: int = 32,
             backend: str | None = None) -> list[Section]:
    """Sample a trace from end to end, both ends included.

    Samples are by arc length, not by span parameter, so a section is a real
    station on the stroke. `samples` is the number of intervals: the result has
    `samples + 1` sections.
    """
    if samples < 1:
        raise ValueError("a section sample needs at least one interval")
    chain = engine.build(trace.design, backend=backend)
    length = chain.length
    limit = length * (1.0 - 1e-12)
    half = (trace.width or 0.0) / 2.0
    out = []
    for index in range(samples + 1):
        s = min(length * index / samples, limit)
        x, y = chain.point(s)
        angle = chain.tangent(s)
        tx, ty = math.cos(angle), math.sin(angle)
        nx, ny = -ty, tx
        left = (x + nx * half, y + ny * half)
        right = (x - nx * half, y - ny * half)
        out.append(Section(s, (x, y), (tx, ty), trace.width or 0.0,
                           left, right))
    return out

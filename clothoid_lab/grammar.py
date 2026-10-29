"""The fleur grammar: study 01, ported from the ornaments `ornament_set.js`.

The old generator draws each study from named spans: a straight foot, a tail
arc, a band, a petal built from an Euler span and an arc, a waist bow, and a
central lance. This module rebuilds those spans as clothoid **segments**.

The port is exact where the original approximates. `ornament_set.js` turns every
arc and Euler span into 45° cubics and snaps nodes to a 3125 lattice; here an arc
is `κ = 1/R`, an Euler span is `κ` running linearly from `k0` to `k1`, and the
only difference expected is the lattice snap — up to half a unit per node.

A detail that matters: the old spans are allowed to meet at a **corner**, and
this package's chain is tangent-continuous unless told otherwise. Each span
therefore carries `Segment.corner`, the tangent jump at its start, worked out
from the span's own geometry. Without it the foot would bend into the tail base
and every later node would be wrong.

`study_01()` returns a `Piece`: the right half mirrored, plus the band. The
parameter block is the old `study-01` object, unchanged.
"""

from __future__ import annotations

import math

from . import engine
from .model import Design, Segment
from .piece import Piece, Trace

D = math.pi / 180.0

# The old study-01 parameters, verbatim from ornaments/assets/ornament_set.js
STUDY_01 = {
    "petalH": 1000, "petalSweep": 25, "tailT0": -15, "tailSweep": -35,
    "lanceH": 1180, "bandHalf": 250, "waist": 160, "innerBow": 3125,
    "footY": -330, "footBase": 65, "tailBase": 120, "petalT0": 55,
    "lanceBase": 110,
}


def _wrap(angle: float) -> float:
    """An angle in (-π, π], so a corner is the smallest turn that explains it."""
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle <= -math.pi:
        angle += 2.0 * math.pi
    return angle


def _arc(radius: float, sweep_deg: float, start_dir: float):
    if radius <= 0:
        raise ValueError("arc radius must be positive")
    sweep = sweep_deg * D
    kappa = (1.0 if sweep >= 0 else -1.0) / radius
    return (Segment(kd=0.0, length=radius * abs(sweep), kappa0=kappa), start_dir)


def _line(a, b):
    length = math.hypot(b[0] - a[0], b[1] - a[1])
    if length <= 0:
        raise ValueError("a straight span needs two distinct points")
    return (Segment(kd=0.0, length=length, kappa0=0.0),
            math.atan2(b[1] - a[1], b[0] - a[0]))


def _euler(k0: float, k1: float, turn_deg: float, start_dir: float):
    turn = turn_deg * D
    total = k0 + k1
    if abs(total) <= 1e-12:
        raise ValueError("an Euler span needs a non-zero curvature sum")
    length = 2.0 * turn / total
    if length <= 0:
        raise ValueError("an Euler span needs a positive length")
    return (Segment(kd=(k1 - k0) / length, length=length, kappa0=k0), start_dir)


def _arc_from(point, tdeg: float, radius: float, sweep: float):
    return _arc(radius, sweep, tdeg * D)


def _arc_between(a, b, radius: float, side: int):
    chord = math.hypot(b[0] - a[0], b[1] - a[1])
    h = math.sqrt(max(0.0, radius * radius - chord * chord / 4.0))
    ux, uy = (b[0] - a[0]) / chord, (b[1] - a[1]) / chord
    centre = ((a[0] + b[0]) / 2.0 + side * -uy * h,
              (a[1] + b[1]) / 2.0 + side * ux * h)
    a0 = math.atan2(a[1] - centre[1], a[0] - centre[0])
    a1 = math.atan2(b[1] - centre[1], b[0] - centre[0])
    sweep = _wrap(a1 - a0)
    # tangent at the start, following the sweep's hand
    sign = 1.0 if sweep >= 0 else -1.0
    rx, ry = a[0] - centre[0], a[1] - centre[1]
    start_dir = math.atan2(sign * rx, -sign * ry)
    return _arc(radius, math.degrees(sweep), start_dir)


class _Walk:
    """Walk spans from a start point, recording corners and node positions."""

    def __init__(self, point, direction: float):
        self.point = (float(point[0]), float(point[1]))
        self.direction = direction
        self.spans: list[Segment] = []
        self.nodes = [(self.point[0], self.point[1])]

    def add(self, built) -> None:
        segment, start_dir = built
        segment.corner = _wrap(start_dir - self.direction)
        design = Design(name="span", segments=[segment],
                        anchor={"x": self.point[0], "y": self.point[1],
                                "angle": start_dir})
        chain = engine.build(design)
        self.point = chain.point(chain.length)
        self.direction = chain.tangent(chain.length)
        self.spans.append(segment)
        self.nodes.append(self.point)


def fleur_right(o: dict) -> dict:
    """The right half from the foot to the lance tip, as segments and nodes."""
    start = (0.0, o["footY"])
    walk = _Walk(start, math.atan2(-25.0 - o["footY"], o["footBase"]))
    walk.add(_line(start, (o["footBase"], -25.0)))
    walk.add(_line((o["footBase"], -25.0), (o["tailBase"], -25.0)))
    walk.add(_arc_from((o["tailBase"], -25.0), o["tailT0"], 625.0,
                       o["tailSweep"]))
    walk.add(_arc_between(walk.point, (o["bandHalf"], -25.0), 625.0, 1))
    walk.add(_line((o["bandHalf"], -25.0), (o["bandHalf"], 25.0)))
    walk.add(_euler(0.0, 1.0 / 625.0, 10.0, o["petalT0"] * D))
    walk.add(_arc(625.0, o["petalSweep"], walk.direction))
    tip = (round(walk.point[0]), o["petalH"])
    walk.add(_line(walk.point, tip))
    walk.add(_arc_between(tip, (o["waist"], 25.0), o["innerBow"], 1))
    walk.add(_line((o["waist"], 25.0), (o["lanceBase"], 25.0)))
    walk.add(_line((o["lanceBase"], 25.0), (0.0, o["lanceH"])))
    return {"spans": walk.spans, "start": start,
            "angle": math.atan2(-25.0 - o["footY"], o["footBase"]),
            "nodes": walk.nodes}


def band(o: dict) -> dict:
    half = o["bandHalf"]
    walk = _Walk((-half, -25.0), 0.0)
    walk.add(_line((-half, -25.0), (half, -25.0)))
    walk.add(_arc(25.0, 180.0, 0.0))
    walk.add(_line((half, 25.0), (-half, 25.0)))
    walk.add(_arc(25.0, 180.0, math.pi))
    return {"spans": walk.spans, "start": (-half, -25.0), "angle": 0.0,
            "nodes": walk.nodes}


def study_01() -> Piece:
    o = STUDY_01
    right = fleur_right(o)
    ring = band(o)
    return Piece(
        name="Fleur study 01",
        mirror=True,
        stroke=0.6,
        traces=[
            Trace("half", Design(name="fleur right", segments=right["spans"],
                                 anchor={"x": right["start"][0],
                                         "y": right["start"][1],
                                         "angle": right["angle"]},
                                 g1=True),
                  width=25.0),
            Trace("band", Design(name="band", segments=ring["spans"],
                                 anchor={"x": ring["start"][0],
                                         "y": ring["start"][1],
                                         "angle": ring["angle"]},
                                 g1=True),
                  mirror=False),
        ],
    )

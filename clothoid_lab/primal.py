"""The four primal ornaments: earth, water, air, fire.

Each is one grammar, not a drawing: built from clothoid segments so it inherits
exact arcs, Euler spans and real corners. Parameter sets are deliberately small;
these are the canonical studies, the ones later sets vary.
"""

from __future__ import annotations

import math

from .model import Design, Segment
from .piece import Piece, Trace


def _arc(radius: float, sweep_deg: float, corner: float = 0.0) -> Segment:
    sweep = math.radians(sweep_deg)
    return Segment(kd=0.0, length=radius * abs(sweep),
                   kappa0=(1.0 if sweep >= 0 else -1.0) / radius,
                   corner=corner)


def _line(length: float, corner: float = 0.0) -> Segment:
    return Segment(kd=0.0, length=length, kappa0=0.0, corner=corner)


def _euler(k0: float, k1: float, turn_deg: float, corner: float = 0.0) -> Segment:
    turn = math.radians(turn_deg)
    length = 2.0 * turn / (k0 + k1)
    return Segment(kd=(k1 - k0) / length, length=length, kappa0=k0, corner=corner)


def _piece(name: str, segments, width: float, terminals, mirror=False) -> Piece:
    design = Design(name=name, segments=segments,
                    anchor={"x": 0.0, "y": 0.0, "angle": 0.0}, g1=True)
    return Piece(name=name, mirror=mirror, stroke=0.6,
                 traces=[Trace(name, design, width=width, terminals=terminals)])


def earth() -> Piece:
    """Strata: terraces that step down, heavy at the foot, drawn to a point."""
    return _piece("earth", [
        _line(44.0),
        _line(30.0, corner=-0.55),
        _line(20.0, corner=-0.55),
        _line(12.0, corner=-0.55),
    ], width=9.0, terminals=("butt", "taper"))


def water() -> Piece:
    """A wave: one long sweep, one reversal, both ends rounded."""
    return _piece("water", [
        _arc(42.0, 90.0),
        _arc(42.0, -90.0),
        _arc(30.0, 60.0),
    ], width=6.0, terminals=("round", "round"))


def air() -> Piece:
    """A cloud: billows of falling radius, closed by round ends."""
    return _piece("air", [
        _arc(18.0, 180.0),
        _arc(12.0, -180.0),
        _arc(8.0, 180.0),
    ], width=4.0, terminals=("round", "round"))


def fire() -> Piece:
    """A tongue: rising curvature, then a fall to a point."""
    return _piece("fire", [
        _euler(0.0, 0.018, 95.0),
        _euler(0.018, 0.0, 55.0, corner=0.15),
    ], width=5.0, terminals=("butt", "point"))


PRIMAL = {"earth": earth, "water": water, "air": air, "fire": fire}

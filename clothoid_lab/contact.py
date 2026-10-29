"""A declared place where two strokes may touch, cross or merge.

Kept in its own module because both the drawing model (`Piece.contacts`) and the
measurement (`clearance`) need it; putting it in either would make the other
import in a circle.
"""

from __future__ import annotations

import math

Point = tuple[float, float]


class Contact:
    """A spot where two strokes are allowed to touch or cross.

    `radius` is in design units (millimetres at 1:1). Contacts are declared by
    the caller, never inferred: a terminal is a contact because the drawing says
    so, not because the geometry happens to meet.
    """

    __slots__ = ("point", "radius", "a", "b", "waives_clearance")

    def __init__(self, point: Point, radius: float = 1.0,
                 a: str | None = None, b: str | None = None,
                 waives_clearance: bool = True):
        if radius <= 0:
            raise ValueError("contact radius must be positive")
        self.point = (float(point[0]), float(point[1]))
        self.radius = float(radius)
        self.a = a
        self.b = b
        # Inside its footprint a contact is a merge: the strokes are joined, so
        # the clearance rule does not apply there. Outside it, it very much does.
        self.waives_clearance = bool(waives_clearance)

    def allows(self, point: Point, a: str, b: str) -> bool:
        if self.a is not None and self.b is not None:
            if {self.a, self.b} != {a, b}:
                return False
        elif self.a is not None and self.a not in (a, b):
            return False
        elif self.b is not None and self.b not in (a, b):
            return False
        return math.dist(point, self.point) <= self.radius

    def __repr__(self) -> str:
        return f"Contact({self.point}, r={self.radius})"

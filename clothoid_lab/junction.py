"""A junction: where a branch meets a trunk.

This is the smallest object that earns the name. It holds the corner the two
centre lines would make, the fillet radius, the two ribbon widths, and the names
the clearance report should use. `build()` returns three things together:

- a `Piece` with the branch and the trunk,
- a `Contact` declaring the merge, with `waives_clearance=True`,
- a report with the join grade, the arc length and the trim.

The geometry is deliberately conservative: a straight branch, a circular fillet,
then the trunk. That is G1 — curvature steps to `1/r` at the touch point — and
the report says so instead of pretending otherwise. A clothoid blend and a taper
into the trunk are the next increments, not hidden options here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .contact import Contact
from .fillet import FilletError, arc_segment, corner_fillet
from .model import Design, Segment
from .piece import Piece, Trace

Point = tuple[float, float]


@dataclass(frozen=True)
class Junction:
    """A branch leaving a trunk, with the merge declared."""

    corner: Point
    branch_end: Point
    trunk_end: Point
    radius: float = 6.0
    branch_width: float = 6.0
    trunk_width: float = 12.0
    branch_name: str = "ink/branch"
    trunk_name: str = "ink/trunk"
    trunk_length: float = 80.0
    branch_terminal: str = "cone"

    def __post_init__(self):
        if self.radius <= 0:
            raise ValueError("junction radius must be positive")
        if self.branch_width <= 0 or self.trunk_width <= 0:
            raise ValueError("ribbon widths must be positive")
        if self.branch_end == self.corner or self.trunk_end == self.corner:
            raise ValueError("a junction needs two edges away from the corner")

    def build(self) -> dict:
        """Return `{"piece", "contact", "report"}` for this junction."""
        fillet = corner_fillet(self.branch_end, self.corner,
                               self.trunk_end, self.radius)
        branch_length = (math.dist(self.branch_end, self.corner)
                         - fillet["trim"][0])
        if branch_length <= 0:
            raise FilletError("the fillet consumes the whole branch")

        anchor_angle = math.atan2(self.corner[1] - self.branch_end[1],
                                  self.corner[0] - self.branch_end[0])
        arc = arc_segment(fillet)
        branch = Design(
            name="branch",
            anchor={"x": self.branch_end[0], "y": self.branch_end[1],
                    "angle": anchor_angle},
            segments=[
                Segment(kd=0.0, length=branch_length, kappa0=0.0),
                Segment(**arc["segment"]),
            ],
        )

        trunk_angle = math.atan2(self.trunk_end[1] - self.corner[1],
                                 self.trunk_end[0] - self.corner[0])
        back = self.trunk_length / 2.0
        trunk = Design(
            name="trunk",
            anchor={
                "x": self.corner[0] - math.cos(trunk_angle) * back,
                "y": self.corner[1] - math.sin(trunk_angle) * back,
                "angle": trunk_angle,
            },
            segments=[Segment(kd=0.0, length=self.trunk_length, kappa0=0.0)],
        )

        piece = Piece(
            name="junction",
            stroke=0.6,
            traces=[
                Trace("branch", branch, width=self.branch_width,
                      terminals=(self.branch_terminal, "butt")),
                Trace("trunk", trunk, width=self.trunk_width,
                      terminals=("butt", "butt")),
            ],
            contacts=[self.contact()],
        )

        report = {
            "angle": fillet["angle"],
            "tangent": fillet["tangent"],
            "arc_length": fillet["length"],
            "trim": list(fillet["trim"]),
            "merge": fillet["end"],
            "branch_length": branch_length,
            "join": "G1",
            "curvature_step": 1.0 / self.radius,
        }
        return {"piece": piece, "contact": self.contact(), "report": report}

    def contact(self) -> Contact:
        """The merge, as a declared contact wide enough to cover the branch."""
        return Contact(
            self.merge_point,
            radius=self.radius + self.branch_width,
            a=self.branch_name,
            b=self.trunk_name,
        )

    @property
    def merge_point(self) -> Point:
        fillet = corner_fillet(self.branch_end, self.corner,
                               self.trunk_end, self.radius)
        return fillet["end"]

    def check(self, clearance: float = 5.0, tol: float = 0.05) -> dict:
        """Build and measure: one call for the report a review needs."""
        from .clearance import piece_clearance

        built = self.build()
        return piece_clearance(built["piece"], clearance=clearance, tol=tol)

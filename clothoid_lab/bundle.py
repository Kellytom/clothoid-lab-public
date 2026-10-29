"""Bundles: full lines grouped together without touching.

A bundle is the design box: a named set of strokes that belong together and must
keep clearance *inside* the set. A sheaf of wheat, a fasces, a capital, the
leaves of an acanthus, the halves of a fleur-de-lis.

It is deliberately not a `Piece`. A piece is the drawing; a bundle is a part of a
drawing with its own rule. `Bundle.piece()` gives a piece for rendering or
checking, and `Bundle.check()` measures only the members against each other, so
a bundle can sit next to another bundle without inheriting its contacts.

The footprint is the box: the bounding rectangle of everything the bundle draws,
including the mirror. It is for placement and for saying "this is one object".
It is not a clip and it does not enforce anything by itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .clearance import Contact, piece_clearance
from .piece import Piece, Trace, build_piece

Box = tuple[float, float, float, float]


@dataclass
class Bundle:
    """A named group of full lines with an internal clearance rule."""

    name: str
    traces: list[Trace]
    mirror: bool = False
    clearance: float = 5.0
    contacts: list[Contact] = field(default_factory=list)

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("a bundle needs a name")
        if not self.traces:
            raise ValueError("a bundle needs at least one full line")
        if self.clearance <= 0:
            raise ValueError("bundle clearance must be positive")

    def piece(self) -> Piece:
        """The bundle as a piece, for rendering or measuring."""
        return Piece(name=self.name, mirror=self.mirror, stroke=0.6,
                     traces=list(self.traces), contacts=list(self.contacts))

    def footprint(self, tol: float = 0.05) -> Box:
        """The design box: the bounds of the ink, mirror included."""
        groups, _ = build_piece(self.piece(), tol=tol)
        xs = [p[0] for group in groups for span in group.spans
              for p in (span["p0"], span["c1"], span["c2"], span["p3"])]
        ys = [p[1] for group in groups for span in group.spans
              for p in (span["p0"], span["c1"], span["c2"], span["p3"])]
        return min(xs), min(ys), max(xs), max(ys)

    def check(self, tol: float = 0.05) -> dict:
        """Clearance among the members only, with no junctions assumed."""
        return piece_clearance(self.piece(), clearance=self.clearance,
                               tol=tol, contacts=list(self.contacts))

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "mirror": self.mirror,
            "clearance": self.clearance,
            "contacts": [{"point": list(c.point), "radius": c.radius, "a": c.a,
                          "b": c.b, "waives_clearance": c.waives_clearance}
                         for c in self.contacts],
            "traces": [t.to_dict() for t in self.traces],
        }

"""The design model: a chain of clothoid segments, anchored in the plane.

A design is plain data, so it round-trips through JSON and can be written into
the SVG metadata for later recovery.

Lengths are in design units. At output one design unit maps to millimetres:
1:1 for `--page` or an automatic sheet, and multiplied by the frame scale when
`--frame` is used. Curvature is 1/design-unit, curvature rate is
1/design-unit^2. A segment is a clothoid: its curvature runs linearly with arc length,
kappa(s) = kappa0 + kd * s, over an arc length `length`.

`kappa0: null` means "continue from the previous segment's end curvature",
which is what makes a chain G2 at that join.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field


@dataclass
class Segment:
    """One clothoid: curvature rate, arc length, and where it starts curving from."""

    kd: float
    length: float
    kappa0: float | None = None
    # A tangent jump at the start of this segment. Zero means continuous; a
    # nonzero value makes a corner, as at the point of a leaf.
    corner: float = 0.0

    def __post_init__(self):
        if self.length <= 0:
            raise ValueError(f"segment length must be positive, got {self.length}")
        if self.kappa0 is not None and not _finite(self.kappa0):
            raise ValueError("segment kappa0 must be a finite number or null")
        if not _finite(self.corner):
            raise ValueError("segment corner must be a finite angle")

    def kappa_end(self, k0: float) -> float:
        return k0 + self.kd * self.length

    def to_dict(self) -> dict:
        out = {"kd": self.kd, "length": self.length, "kappa0": self.kappa0}
        if self.corner:
            out["corner"] = self.corner
        return out


@dataclass
class Design:
    """An anchored chain, plus the offset distances and stroke it is drawn with."""

    segments: list[Segment]
    anchor: dict = field(default_factory=lambda: {"x": 0.0, "y": 0.0, "angle": 0.0})
    offsets: list[float] = field(default_factory=list)
    stroke: float = 1.0
    name: str = "untitled"
    # A G1 spline through points is G1 by construction: curvature jumps at the
    # joins are the fit, not a mistake, so the report must not fail the run.
    g1: bool = False

    def __post_init__(self):
        if not self.segments:
            raise ValueError("a design needs at least one segment")
        for key in ("x", "y", "angle"):
            self.anchor.setdefault(key, 0.0)
        if self.stroke <= 0:
            raise ValueError("stroke width must be positive")

    @classmethod
    def from_pieces(cls, pieces, anchor=None, name: str = "untitled",
                    stroke: float = 1.0, g1: bool = False) -> "Design":
        """A design from backend pieces: start point, direction, curvature, rate, length."""
        if not pieces:
            raise ValueError("a design needs at least one piece")
        if anchor is None:
            first = pieces[0]
            anchor = {"x": float(first["x0"]), "y": float(first["y0"]),
                      "angle": float(first["theta0"])}
        segments = [
            Segment(kd=float(p["kd"]), length=float(p["length"]),
                    kappa0=float(p["kappa0"] if "kappa0" in p else p["k0"]),
                    corner=float(p.get("corner", 0.0)))
            for p in pieces
        ]
        return cls(segments=segments, anchor=dict(anchor), stroke=float(stroke),
                   name=name, g1=g1)

    def to_dict(self) -> dict:
        out = {
            "name": self.name,
            "anchor": dict(self.anchor),
            "segments": [s.to_dict() for s in self.segments],
            "offsets": list(self.offsets),
            "stroke": self.stroke,
        }
        if self.g1:
            out["g1"] = True
        return out

    @classmethod
    def from_dict(cls, data: dict) -> "Design":
        segs = [
            Segment(kd=float(s["kd"]), length=float(s["length"]),
                    kappa0=None if s.get("kappa0") is None else float(s["kappa0"]),
                    corner=float(s.get("corner", 0.0)))
            for s in data.get("segments", [])
        ]
        return cls(
            segments=segs,
            anchor=dict(data.get("anchor", {})),
            offsets=[float(d) for d in data.get("offsets", [])],
            stroke=float(data.get("stroke", 1.0)),
            name=str(data.get("name", "untitled")),
            g1=bool(data.get("g1", False)),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=False)

    @classmethod
    def from_json(cls, text: str) -> "Design":
        return cls.from_dict(json.loads(text))

    def save(self, path) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.to_json() + "\n")

    @classmethod
    def load(cls, path) -> "Design":
        with open(path, "r", encoding="utf-8") as fh:
            return cls.from_json(fh.read())


def _finite(value: float) -> bool:
    value = float(value)
    return value == value and abs(value) != float("inf")

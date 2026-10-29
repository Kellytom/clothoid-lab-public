"""The float hybrid: an exact plan, drawn in doubles.

The closure result is integer arithmetic: which turns, which sums cancel, where
the apsis is. None of that needs a coordinate. Coordinates need about fifteen
digits, because that is all the page can hold. So the plan stays exact and the
ink becomes floating point, which lifts the practical ceiling from a few
hundred chords to tens of thousands.

What survives in floats, exactly:

- the turn schedule and the total coefficient (Python ints, untouched);
- a quarter-turn cusp, because it is a component swap, not a trig call;
- a mirror through an axis, because `-x` is exact in IEEE floats;
- a shared node, because a branch stores the float pair it reads.

What does not: the heading drifts by about one ulp per turn, and the position
by the sum of those. Both are measured in `tests/test_hybrid.py` rather than
asserted.

Do not call this exact geometry. It is the same plan, drawn to about 1e-12.
"""

from __future__ import annotations

import math
from fractions import Fraction

from .exact import Dir
from .spiral import Spiral, triangular
from .triples import Triple


class FloatChain:
    """A chain whose plan is exact and whose points are doubles."""

    def __init__(self, triangle: Triple, length=1, heading: Dir | None = None,
                 start=(0.0, 0.0)):
        self.triangle = triangle
        self.length = float(length)
        self.length_exact = Fraction(length) if not isinstance(length, float) \
            else Fraction(length).limit_denominator()
        self.alpha = triangle.radians
        cos_a = float(triangle.direction.re)
        sin_a = float(triangle.direction.im)
        self._cos, self._sin = cos_a, sin_a
        h = heading or Dir.east()
        self.heading0 = h
        self.start0 = start
        self.hx, self.hy = float(h.re), float(h.im)
        self.x, self.y = float(start[0]), float(start[1])
        self.nodes: list[tuple[float, float]] = [(self.x, self.y)]
        self.turns: list[int] = []
        self.headings: list[tuple[float, float]] = []
        self.coeff = 0
        self.cusps: list[int] = []

    def _rotate(self, k: int) -> None:
        """Rotate the heading by k triangle angles, in doubles."""
        if k == 0:
            return
        if k == 1:
            c, s = self._cos, self._sin
        elif k == -1:
            c, s = self._cos, -self._sin
        else:
            ang = k * self.alpha
            c, s = math.cos(ang), math.sin(ang)
        hx, hy = self.hx, self.hy
        self.hx = hx * c - hy * s
        self.hy = hx * s + hy * c

    def turn(self, k: int):
        self._rotate(int(k))
        self.coeff += int(k)
        return self

    def cusp(self, quarter_turns: int):
        """A quarter turn is a swap: exact even here."""
        q = int(quarter_turns) % 4
        hx, hy = self.hx, self.hy
        if q == 0:
            pass
        elif q == 1:
            self.hx, self.hy = -hy, hx
        elif q == 2:
            self.hx, self.hy = -hx, -hy
        else:
            self.hx, self.hy = hy, -hx
        self.cusps.append(q)
        return self

    def walk(self, turn: int = 0):
        if turn:
            self.turn(turn)
        self.turns.append(int(turn))
        self.headings.append((self.hx, self.hy))
        self.x += self.length * self.hx
        self.y += self.length * self.hy
        self.nodes.append((self.x, self.y))
        return self

    def extend(self, turns):
        for k in turns:
            self.walk(k)
        return self

    # -- plan readings, still exact ------------------------------------
    def cumulative(self) -> list[int]:
        out, total = [], 0
        for t in self.turns:
            total += t
            out.append(total)
        return out

    @property
    def peak_degrees(self) -> float:
        return max(self.cumulative(), default=0) * self.triangle.degrees

    @property
    def final(self):
        return self.nodes[-1]

    def heading_degrees(self) -> float:
        return math.degrees(math.atan2(self.hy, self.hx))

    def drift(self) -> float:
        """How far the float heading has left the exact unit circle, in ulps."""
        return abs(math.hypot(self.hx, self.hy) - 1.0)

    def exact(self) -> Spiral:
        """The same plan, exactly: only for chains small enough to afford it."""
        path = Spiral(self.triangle, self.length_exact,
                      heading=self.heading0, start=self.start0)
        path.extend(self.turns)
        return path


def build(triangle: Triple, turns, length=1, heading: Dir | None = None,
          start=(0.0, 0.0), cusps=()) -> FloatChain:
    """A float chain from a turn schedule, with any cusps at given indices."""
    chain = FloatChain(triangle, length, heading, start)
    at = {int(k): int(q) for k, q in cusps}
    for i, t in enumerate(turns):
        if i in at:
            chain.cusp(at.pop(i))
        chain.walk(t)
    if len(turns) in at:
        chain.cusp(at.pop(len(turns)))
    if at:
        raise ValueError(f"cusp at {sorted(at)} is past the last chord")
    return chain

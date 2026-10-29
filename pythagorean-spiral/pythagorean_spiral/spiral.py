"""The discrete Euler spiral: a chain of equal chords, turned by k*alpha.

Convention
----------
Segment 1 runs along `heading` (east by default).  Segment `k` has heading
`alpha * T(k-1)` with `T(j) = j(j+1)/2`, so the heading *after* the node at the
start of segment k is `alpha * T(k)`.  Turns are applied at nodes, never inside
a segment.

That is the defining law of a clothoid read as a difference equation: the
heading is quadratic in the step index, so the curvature is linear in arc
length.  What the chain is *not* is the clothoid itself.  Each chord leaves
along the tangent at its own start node, which makes the chain an explicit
Euler integration of the clothoid ODE with step `length`; the exact arithmetic
is exact about the polygon, not about the curve it imitates.

Every node is a rational point.  `integer_form` rescales exactly to integers.
"""

from __future__ import annotations

import math
from fractions import Fraction

from .exact import Dir
from .triples import Triple


def triangular(k: int) -> int:
    """T(k) = 1 + 2 + ... + k."""
    return k * (k + 1) // 2


class Spiral:
    """An exact chord chain.  Mutating calls return `self`, so calls chain."""

    def __init__(self, triangle: Triple, length=1, heading: Dir | None = None,
                 start=(0, 0)):
        self.triangle = triangle
        self.length = Fraction(length)
        self.heading = heading or Dir.east()
        self.x = Fraction(start[0])
        self.y = Fraction(start[1])
        self.nodes: list[tuple[Fraction, Fraction]] = [(self.x, self.y)]
        self.headings: list[Dir] = []   # one per chord, in order
        self.turns: list[int] = []
        self.coeff = 0          # total turn, in whole multiples of alpha
        self.cusps: list[int] = []

    # -- the two primitives -------------------------------------------
    def turn(self, k: int):
        """Rotate by k triangle angles, exactly."""
        self.heading = self.heading * (self.triangle.direction ** k)
        self.coeff += k
        return self

    def cusp(self, quarter_turns: int):
        """An exact right-angle corner: a swap, no triangle involved."""
        self.heading = self.heading.quarter(quarter_turns)
        self.cusps.append(quarter_turns)
        return self

    def walk(self, turn: int = 0):
        """Apply `turn` triangle angles at this node, then lay one chord."""
        if turn:
            self.turn(turn)
        self.turns.append(turn)
        self.headings.append(self.heading)      # the chord's own direction
        self.x += self.length * self.heading.re
        self.y += self.length * self.heading.im
        self.nodes.append((self.x, self.y))
        return self

    def extend(self, turns):
        for k in turns:
            self.walk(k)
        return self

    # -- readings ------------------------------------------------------
    def cumulative(self) -> list[int]:
        """The turn coefficient at each node, unwrapped.

        The heading is stored as a vector, so `Dir.degrees` folds past 180.
        This is the heading as a count of triangle angles, which is what a
        report wants: a curl whose apsis is 198 degrees says 198, not -162.
        """
        out, total = [], 0
        for turn in self.turns:
            total += turn
            out.append(total)
        return out

    @property
    def peak_degrees(self) -> float:
        """The largest unwrapped heading the chain reaches."""
        return max(self.cumulative()) * self.triangle.degrees

    @property
    def final(self) -> tuple[Fraction, Fraction]:
        return self.nodes[-1]

    def knots(self) -> list[tuple[tuple[Fraction, Fraction], Dir]]:
        """Every node with the exact heading of the path at it.

        The heading at a node is the direction of the chord that leaves it; at
        the final node no chord leaves, so the last chord's heading carries
        forward.  These are the attachment points for a branch: a branch reads
        one of these pairs, so both sides share the same rational point and the
        same exact direction -- no measurement, no tolerance.
        """
        return list(zip(self.nodes, list(self.headings) + [self.heading]))

    @property
    def arc_length(self) -> Fraction:
        return self.length * len(self.turns)

    def is_closed_in_direction(self) -> bool:
        """True when the chain ends exactly on an axis."""
        return self.heading.is_axis_aligned()

    def equivalent_clothoid(self) -> dict:
        """The clothoid whose node *headings* the chain reproduces exactly.

        NOT the curve. Do not use this to obtain a clothoid: evaluating it
        gives a different curve, a full chord away in position, and the chain
        itself has piecewise-constant curvature. For a real clothoid use
        `clothoid_lab` / pyclothoids. This is here so the two can be compared.

        With h(s) the chain's heading at arc length s = j*L,

            h(s) = alpha*s^2/(2L^2) + alpha*s/(2L)

        so this is a clothoid with initial curvature kappa0 = alpha/(2L) and
        rate kd = alpha/L^2.  Exact at the nodes, but only the nodes: the chain
        is the Euler polygon of that curve, not the curve.
        """
        alpha = self.triangle.radians
        L = float(self.length)
        return {
            "alpha": alpha,
            "kappa0": alpha / (2 * L),
            "kd": alpha / (L * L),
            "A2": L * L / alpha,
            "step": L,
            "steps": len(self.turns),
            "length": L * len(self.turns),
        }

    def chord_angle(self) -> float:
        """The largest turn any one chord gets, in radians.

        The chain stops reading as a curve once this approaches a radian: the
        chords are too coarse to resolve the local radius.
        """
        biggest = max((abs(k) for k in self.turns), default=0)
        return self.triangle.radians * biggest

    def usable_steps(self) -> int:
        """Largest step index whose chord still subtends under a right angle."""
        return max(1, int(1.0 / self.triangle.radians))

    # -- exact output --------------------------------------------------
    def integer_form(self) -> tuple[list[tuple[int, int]], int]:
        """Every node as an integer pair, plus the exact scale factor used."""
        den = 1
        for x, y in self.nodes:
            den = math.lcm(den, x.denominator, y.denominator)
        return [(int(x * den), int(y * den)) for x, y in self.nodes], den

    def floats(self) -> list[tuple[float, float]]:
        return [(float(x), float(y)) for x, y in self.nodes]

    def mirrored(self, axis: Dir, through=(0, 0)):
        """The chain reflected exactly through a rational line."""
        cx, cy = Fraction(through[0]), Fraction(through[1])
        u, v = axis.re, axis.im
        r00, r01 = 2 * u * u - 1, 2 * u * v
        r11 = 2 * v * v - 1
        out = []
        for x, y in self.nodes:
            dx, dy = x - cx, y - cy
            out.append((cx + r00 * dx + r01 * dy, cy + r01 * dx + r11 * dy))
        return out

    def __repr__(self):
        x, y = self.final
        return (f"Spiral({self.triangle}, steps={len(self.turns)}, "
                f"final=({float(x):.6f}, {float(y):.6f}), "
                f"heading={self.heading.degrees:.3f}deg)")

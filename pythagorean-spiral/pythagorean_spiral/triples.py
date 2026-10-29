"""Primitive Pythagorean triples and the exact turn each one contributes.

Every primitive triple comes from one pair of Euclid generators (m > n,
coprime, opposite parity):

    a = m^2 - n^2,  b = 2mn,  c = m^2 + n^2,  a^2 + b^2 = c^2

and the rotation by its acute angle is the rational matrix

    (x, y) -> ((b*x - a*y)/c, (a*x + b*y)/c)

Nothing here is trigonometric.  The angle never appears in the geometry; it is
only reported, for a human reading the output.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction

from .exact import Dir


@dataclass(frozen=True)
class Triple:
    """A right triangle with integer sides; `a` is the short leg."""

    a: int
    b: int
    c: int
    m: int = 0
    n: int = 0

    def __post_init__(self):
        if self.a * self.a + self.b * self.b != self.c * self.c:
            raise ValueError(f"{self.a}, {self.b}, {self.c} is not a right triangle")
        if self.a <= 0 or self.b <= 0 or self.a > self.b:
            raise ValueError("need 0 < a <= b")

    # -- what it contributes to a chain -------------------------------
    @property
    def direction(self) -> Dir:
        return Dir.from_triple(self.a, self.b, self.c)

    @property
    def slope(self) -> Fraction:
        """The exact tangent of the acute angle: a/b."""
        return Fraction(self.a, self.b)

    @property
    def radians(self) -> float:
        return math.atan2(self.a, self.b)

    @property
    def degrees(self) -> float:
        return math.degrees(self.radians)

    # -- derived triangles -------------------------------------------
    def scaled(self, k: int) -> "Triple":
        return Triple(self.a * k, self.b * k, self.c * k, self.m, self.n)

    def double_angle(self) -> "Triple":
        """The triangle whose angle is exactly twice this one's.

        Sides (2ab, |b^2 - a^2|, c^2).  Its hypotenuse is c^2, so scaling this
        triangle by c makes the two the *same* side length.
        """
        p, q = 2 * self.a * self.b, abs(self.b * self.b - self.a * self.a)
        lo, hi = min(p, q), max(p, q)
        return Triple(lo, hi, self.c * self.c)

    def at_length(self, length: int) -> "Triple":
        """This triangle scaled so that its hypotenuse is `length`."""
        if length % self.c:
            raise ValueError(f"{self.c} does not divide {length}")
        return self.scaled(length // self.c)

    def is_primitive(self) -> bool:
        return math.gcd(math.gcd(self.a, self.b), self.c) == 1

    def __str__(self):
        return f"{self.a}-{self.b}-{self.c}"


def primitive(limit: int | None = None) -> list[Triple]:
    """Every primitive triple, ordered by hypotenuse (then by thinness)."""
    out = []
    m = 2
    while True:
        # for a fixed m the smallest hypotenuse is at n = 1: c = m*m + 1
        if limit is not None and m * m + 1 > limit:
            break
        if limit is None and m > 64:
            break
        for n in range(1, m):
            if (m - n) % 2 == 0 or math.gcd(m, n) != 1:
                continue
            a, b = m * m - n * n, 2 * m * n
            c = m * m + n * n
            if limit is not None and c > limit:
                continue
            lo, hi = min(a, b), max(a, b)
            out.append(Triple(lo, hi, c, m, n))
        m += 1
    out.sort(key=lambda t: (t.c, Fraction(t.a, t.b)))
    return out


def thinnest(limit: int) -> Triple:
    """The smallest acute angle available on a hypotenuse of at most `limit`.

    Thin triangles are the ones that let a chain look like a curve rather than
    a staircase, so this is the triangle a spiral wants.
    """
    best = None
    m = 2
    while m * m + 1 <= limit:
        for n in range(1, m):
            if (m - n) % 2 == 0 or math.gcd(m, n) != 1:
                continue
            c = m * m + n * n
            if c > limit:
                continue
            a, b = m * m - n * n, 2 * m * n
            lo, hi = min(a, b), max(a, b)
            if best is None or lo * best.b < best.a * hi:
                best = Triple(lo, hi, c, m, n)
        m += 1
    if best is None:
        raise ValueError(f"no primitive triple with c <= {limit}")
    return best


def thinnest_consecutive(limit: int) -> Triple | None:
    """The (2n+1, 2n(n+1), 2n^2+2n+1) family member under `limit`.

    Consecutive Euclid generators give the thinnest primitive triple for a
    given hypotenuse, which is why 79-3120-3121 sits just under 3125.
    """
    n = 1
    best = None
    while True:
        t = Triple(2 * n + 1, 2 * n * (n + 1), 2 * n * n + 2 * n + 1, n + 1, n)
        if t.c > limit:
            return best
        best = t
        n += 1


def for_angle(degrees: float) -> Triple:
    """The thinnest primitive triple whose acute angle is at most `degrees`.

    The `(m, m-1)` family -- `2m-1, 2m(m-1), m^2+(m-1)^2` -- is the thinnest
    family at any given size, so the first member under the target is the
    thinnest triangle available at that resolution.  A chain's widest chord
    turn sets its resolution, and that turn *is* this angle, so choosing the
    triangle is really choosing how smooth the curve can be.
    """
    if not 0 < degrees < 45:
        raise ValueError(f"want 0 < degrees < 45, got {degrees}")
    m = 2
    while True:
        t = Triple(2 * m - 1, 2 * m * (m - 1), m * m + (m - 1) ** 2, m, m - 1)
        if t.degrees <= degrees:
            return t
        m += 1

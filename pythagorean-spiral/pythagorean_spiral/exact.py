"""Exact unit directions.

The whole claim of the method is that a heading built from whole triangle
angles can be carried as a rational pair, so nothing drifts.  A direction is
`(re, im)` with `re*re + im*im == 1`, both `Fraction`.  Multiplication is
closed under that, so a chain of turns never leaves the rationals.  Angles
exist only for printing.
"""

from __future__ import annotations

import math
from fractions import Fraction


class Dir:
    """An exact unit direction."""

    __slots__ = ("re", "im")

    def __init__(self, re, im):
        self.re = Fraction(re)
        self.im = Fraction(im)
        if self.re * self.re + self.im * self.im != 1:
            raise ValueError(f"not a unit direction: {self.re}, {self.im}")

    # -- construction -------------------------------------------------
    @classmethod
    def east(cls):
        return cls(1, 0)

    @classmethod
    def north(cls):
        return cls(0, 1)

    @classmethod
    def from_triple(cls, a: int, b: int, c: int):
        """The direction of the hypotenuse of legs (a, b): cos = b/c, sin = a/c."""
        if b * b + a * a != c * c:
            raise ValueError(f"{a}, {b}, {c} is not a right triangle")
        return cls(Fraction(b, c), Fraction(a, c))

    # -- algebra ------------------------------------------------------
    def __mul__(self, other: "Dir") -> "Dir":
        return Dir(self.re * other.re - self.im * other.im,
                   self.re * other.im + self.im * other.re)

    def __pow__(self, k: int) -> "Dir":
        """k is exact and may be negative: a negative turn rotates back."""
        if k < 0:
            return (self.conj()) ** (-k)
        out, base, k = Dir(1, 0), self, int(k)
        while k:
            if k & 1:
                out = out * base
            base = base * base
            k >>= 1
        return out

    def conj(self) -> "Dir":
        return Dir(self.re, -self.im)

    def quarter(self, n: int) -> "Dir":
        """Turn by n exact right angles; exact because it is a swap."""
        n %= 4
        if n == 0:
            return self
        if n == 1:
            return Dir(-self.im, self.re)
        if n == 2:
            return Dir(-self.re, -self.im)
        return Dir(self.im, -self.re)

    def mirror(self, axis: "Dir") -> "Dir":
        """Reflect through the line with direction `axis`."""
        d = 2 * (self.re * axis.re + self.im * axis.im)
        return Dir(d * axis.re - self.re, d * axis.im - self.im)

    # -- reading ------------------------------------------------------
    @property
    def angle(self) -> float:
        return math.atan2(float(self.im), float(self.re))

    @property
    def degrees(self) -> float:
        return math.degrees(self.angle)

    def is_axis_aligned(self) -> bool:
        """True when the direction is exactly east, north, west or south."""
        return self.re == 0 or self.im == 0

    def axis_name(self) -> str | None:
        named = {(1, 0): "east", (0, 1): "north", (-1, 0): "west", (0, -1): "south"}
        if not self.is_axis_aligned():
            return None
        return named[(int(self.re), int(self.im))]

    def __eq__(self, other):
        return isinstance(other, Dir) and (self.re, self.im) == (other.re, other.im)

    def __hash__(self):
        return hash((self.re, self.im))

    def __repr__(self):
        return f"Dir({self.re}, {self.im})"

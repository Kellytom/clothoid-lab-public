"""Triangles and exact directions."""

import math
import unittest
from fractions import Fraction

from pythagorean_spiral.exact import Dir
from pythagorean_spiral.triples import Triple, primitive, thinnest, thinnest_consecutive


class TestDir(unittest.TestCase):
    def test_unit_and_exact(self):
        d = Dir.from_triple(3, 4, 5)
        self.assertEqual(d.re, Fraction(4, 5))
        self.assertEqual(d.im, Fraction(3, 5))
        self.assertEqual(d.re * d.re + d.im * d.im, 1)

    def test_powers_stay_rational(self):
        d = Dir.from_triple(79, 3120, 3121)
        for k in range(-4, 9):
            p = d ** k
            self.assertEqual(p.re ** 2 + p.im ** 2, 1)
            self.assertEqual(p.denominator if hasattr(p, "denominator") else 1, 1)

    def test_negative_power_is_the_conjugate(self):
        d = Dir.from_triple(3, 4, 5)
        self.assertEqual(d ** -1, d.conj())
        self.assertEqual(d ** -3, (d ** 3).conj())

    def test_quarter_turns_are_exact_swaps(self):
        d = Dir.from_triple(3, 4, 5)
        self.assertEqual(d.quarter(4), d)
        self.assertEqual(d.quarter(2), Dir(-d.re, -d.im))
        self.assertEqual(d.quarter(1), Dir(-d.im, d.re))

    def test_mirror_preserves_length(self):
        d = Dir.from_triple(7, 24, 25)
        axis = Dir.from_triple(20, 21, 29)
        m = d.mirror(axis)
        self.assertEqual(m.re ** 2 + m.im ** 2, 1)
        self.assertEqual(axis.mirror(axis), axis)


class TestTriples(unittest.TestCase):
    def test_primitive_list_is_exact(self):
        got = {str(t) for t in primitive(100)}
        for want in ("3-4-5", "5-12-13", "8-15-17", "7-24-25", "20-21-29"):
            self.assertIn(want, got)

    def test_thinnest_under_3125_is_79_3120_3121(self):
        t = thinnest(3125)
        self.assertEqual((t.a, t.b, t.c), (79, 3120, 3121))
        self.assertAlmostEqual(t.degrees, 1.450448, places=5)

    def test_consecutive_generators_agree(self):
        self.assertEqual(thinnest_consecutive(3125), thinnest(3125))

    def test_double_angle_of_the_thin_triangle(self):
        t = thinnest(3125).double_angle()
        self.assertEqual((t.a, t.b, t.c), (492960, 9728159, 9740641))
        self.assertAlmostEqual(t.degrees, 2 * thinnest(3125).degrees, places=9)

    def test_slope_is_the_tangent(self):
        t = thinnest(3125)
        self.assertEqual(float(t.slope), math.tan(t.radians))
        self.assertEqual(t.slope, Fraction(79, 3120))

    def test_rejects_a_non_triangle(self):
        with self.assertRaises(ValueError):
            Triple(1, 2, 4)


if __name__ == "__main__":
    unittest.main()

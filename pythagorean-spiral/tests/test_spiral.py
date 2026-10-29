"""The exact chain, and the three named constructions."""

import math
import unittest
from fractions import Fraction

from pythagorean_spiral import design
from pythagorean_spiral.spiral import Spiral, triangular
from pythagorean_spiral.triples import thinnest

THIN = thinnest(3125)


class TestSpiral(unittest.TestCase):
    def test_first_two_nodes_are_exact_integers(self):
        p = Spiral(THIN, 3121)
        p.walk(0).walk(1)
        self.assertEqual(p.nodes[0], (Fraction(0), Fraction(0)))
        self.assertEqual(p.nodes[1], (Fraction(3121), Fraction(0)))
        # 3121 along east, then 3120+79i: the second node is the first leg
        self.assertEqual(p.nodes[2], (Fraction(6241), Fraction(79)))

    def test_heading_of_chord_k_is_the_kth_triangular_number(self):
        p = design.spiral(THIN, 6, 1)
        for k, h in enumerate(p.headings):
            self.assertEqual(p.turns[k], k)
            self.assertAlmostEqual(h.degrees, triangular(k) * THIN.degrees,
                                   places=9)

    def test_nodes_stay_rational(self):
        p = design.spiral(THIN, 5, 1)
        for x, y in p.nodes:
            self.assertIsInstance(x, Fraction)
            self.assertIsInstance(y, Fraction)

    def test_integer_form_is_exact(self):
        p = design.lobe(THIN, 7, 3121)
        ints, scale = p.integer_form()
        self.assertEqual(len(ints), len(p.nodes))
        for (ix, iy), (x, y) in zip(ints, p.nodes):
            self.assertEqual(Fraction(ix, scale), x)
            self.assertEqual(Fraction(iy, scale), y)

    def test_the_equivalent_clothoid(self):
        p = design.spiral(THIN, 8, 2)
        c = p.equivalent_clothoid()
        self.assertAlmostEqual(c["kappa0"], THIN.radians / (2 * 2), places=12)
        self.assertAlmostEqual(c["kd"], THIN.radians / 4, places=12)
        # headings agree with s^2/(2A^2) + kappa0*s at every node
        A2 = c["A2"]
        for k in range(8):
            s = k * 2
            self.assertAlmostEqual(
                s * s / (2 * A2) + c["kappa0"] * s,
                p.headings[k].angle, places=9)

    def test_usable_steps_is_where_the_chord_stops_resolving(self):
        self.assertEqual(design.spiral(THIN, 5, 1).usable_steps(), 39)


class TestConstructions(unittest.TestCase):
    def test_lobe_closes_exactly_parallel(self):
        p = design.lobe(THIN, 7, 3121)
        self.assertEqual(p.coeff, 0)
        self.assertEqual(p.heading.axis_name(), "east")
        self.assertGreater(float(p.final[1]), 0)
        self.assertEqual(len(p.turns), 14)

    def test_lobe_is_symmetric_in_turning(self):
        p = design.lobe(THIN, 5, 1)
        self.assertEqual(p.turns, [0, 1, 2, 3, 4, -4, -3, -2, -1, 0])
        peak = max(abs(t) for t in p.turns)
        self.assertEqual(peak, 4)

    def test_hook_closes_on_the_first_exact_pair(self):
        p = design.hook(THIN, 8, None, 3121)
        self.assertEqual(p.coeff, 0)
        self.assertEqual(p.heading.axis_name(), "east")
        self.assertEqual(len(p.turns), 16 + 5)

    def test_g2_lobe_closes_and_needs_a_real_solution(self):
        p = design.g2_lobe(THIN, 3, 1)
        self.assertEqual(p.coeff, 0)
        self.assertEqual(p.turns, [0, 1, 2, 2, 1, 0, -1, -2, -3])
        with self.assertRaises(ValueError):
            design.g2_lobe(THIN, 4, 1)

    def test_no_accumulated_turn_ever_lands_on_an_axis(self):
        """The Niven argument, spot-checked: only coefficient zero lands."""
        d = THIN.direction
        for k in range(1, 200):
            self.assertFalse((d ** k).is_axis_aligned(), f"k={k} landed on an axis")


if __name__ == "__main__":
    unittest.main()

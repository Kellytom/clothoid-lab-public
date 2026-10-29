"""Rails: width around an exact chain, and the exactness of the offset."""

import unittest
from fractions import Fraction

from pythagorean_spiral import design, ribbon
from pythagorean_spiral.spiral import Spiral
from pythagorean_spiral.triples import thinnest

THIN = thinnest(3125)


def straight(n=4, length=1):
    p = Spiral(THIN, length)
    p.extend([0] * n)
    return p


class TestDirections(unittest.TestCase):
    def test_a_chain_gives_exact_unit_directions(self):
        path = design.lobe(THIN, 5)
        for h in ribbon.directions(path.nodes):
            self.assertEqual(h.re * h.re + h.im * h.im, 1)

    def test_a_composite_chain_needs_no_spiral_object(self):
        """Arcs of different lengths joined at nodes still have rational steps."""
        pts = [(Fraction(0), Fraction(0)), (Fraction(3, 5), Fraction(4, 5)),
               (Fraction(3, 5) + Fraction(3, 5), Fraction(4, 5) + Fraction(4, 5))]
        heads = ribbon.directions(pts)
        self.assertEqual(len(heads), 2)
        self.assertEqual(heads[0], heads[1])

    def test_rejects_a_step_that_is_not_rational(self):
        with self.assertRaises(ValueError):
            ribbon.directions([(0, 0), (1, 1)])


class TestRail(unittest.TestCase):
    def test_a_straight_rail_is_the_node_shifted_by_the_width(self):
        path = straight()
        width = Fraction(1, 10)
        left = ribbon.rail(path.nodes, width, +1)
        for node, q in zip(path.nodes, left):
            self.assertEqual(q[0], node[0])
            self.assertEqual(q[1] - node[1], width)

    def test_both_rails_are_one_width_apart_on_a_straight_run(self):
        path = straight()
        left, right = ribbon.rails(path.nodes, Fraction(1, 5))
        for a, b in zip(left, right):
            self.assertEqual(a[1] - b[1], Fraction(2, 5))

    def test_a_miter_lies_on_both_offset_lines(self):
        """The rail corner is the intersection of the two shifted chords."""
        path = design.lobe(THIN, 5)
        width = Fraction(1, 8)
        left = ribbon.rail(path.nodes, width, +1)
        heads = ribbon.directions(path.nodes)
        for k in range(1, len(path.turns)):
            for i in (k - 1, k):
                normal = heads[i].quarter(1)
                d = (left[k][0] - path.nodes[i][0], left[k][1] - path.nodes[i][1])
                self.assertEqual(d[0] * normal.re + d[1] * normal.im, width)

    def test_every_rail_point_stays_rational(self):
        for q in ribbon.outline(design.lobe(THIN, 6).nodes, Fraction(1, 9)):
            self.assertIsInstance(q[0], Fraction)
            self.assertIsInstance(q[1], Fraction)

    def test_taper_brings_the_rails_together_at_both_ends(self):
        path = straight(6)
        left, right = ribbon.rails(path.nodes, Fraction(1, 5), taper=3)
        self.assertEqual(left[0], path.nodes[0])
        self.assertEqual(right[0], path.nodes[0])
        self.assertEqual(left[-1], path.nodes[-1])
        self.assertEqual(right[-1], path.nodes[-1])

    def test_the_outline_is_both_rails(self):
        path = straight(3)
        poly = ribbon.outline(path.nodes, Fraction(1, 10))
        self.assertEqual(len(poly), 2 * (len(path.turns) + 1))

    def test_width_and_side_are_checked(self):
        path = straight(2)
        with self.assertRaises(ValueError):
            ribbon.rail(path.nodes, Fraction(-1, 10))
        with self.assertRaises(ValueError):
            ribbon.rail(path.nodes, Fraction(1, 10), side=0)
        with self.assertRaises(ValueError):
            ribbon.rail(path.nodes, Fraction(1, 10), taper=-1)


class TestFloatRail(unittest.TestCase):
    def test_the_same_offset_in_doubles(self):
        pts = [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0)]
        left, right = ribbon.rails_float(pts, 0.1)
        for a, b in zip(left, right):
            self.assertAlmostEqual(a[1], 0.1, places=12)
            self.assertAlmostEqual(b[1], -0.1, places=12)

    def test_taper_still_lands_on_the_end_nodes(self):
        pts = [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (3.0, 0.0)]
        left, right = ribbon.rails_float(pts, 0.1, taper=2)
        self.assertEqual(left[0], pts[0])
        self.assertEqual(right[-1], pts[-1])

    def test_a_long_float_chain_offsets_without_raising(self):
        from pythagorean_spiral import hybrid
        from pythagorean_spiral.triples import thinnest
        chain = hybrid.build(thinnest(3125), range(2000))
        poly = ribbon.outline_float(chain.nodes, 0.01, taper=4)
        self.assertEqual(len(poly), 2 * len(chain.nodes))
        self.assertTrue(all(x == x and y == y for x, y in poly))


if __name__ == "__main__":
    unittest.main()

"""Joins and forks: the shared node is proved, not measured."""

import unittest
from fractions import Fraction

from pythagorean_spiral import design
from pythagorean_spiral.spiral import Spiral
from pythagorean_spiral.triples import thinnest

THIN = thinnest(3125)


class TestKnots(unittest.TestCase):
    def setUp(self):
        self.path = design.lobe(THIN, 6)

    def test_one_knot_per_node(self):
        self.assertEqual(len(self.path.knots()), len(self.path.turns) + 1)

    def test_knot_is_the_stored_node_and_its_exit_heading(self):
        knots = self.path.knots()
        self.assertEqual([p for p, _ in knots], self.path.nodes)
        self.assertEqual([h for _, h in knots[:-1]], self.path.headings)
        self.assertEqual(knots[-1][1], self.path.heading)

    def test_a_knot_stays_exact(self):
        point, heading = self.path.knots()[3]
        self.assertIsInstance(point[0], Fraction)
        self.assertIsInstance(point[1], Fraction)
        self.assertEqual(heading.re * heading.re + heading.im * heading.im, 1)


class TestFork(unittest.TestCase):
    def setUp(self):
        self.path = design.lobe(THIN, 6)

    def test_branch_starts_on_the_node_exactly(self):
        anchor, branch = design.fork(self.path, 5, steps=5)
        self.assertEqual(anchor, self.path.knots()[5])
        self.assertEqual(branch.nodes[0], self.path.nodes[5])
        self.assertEqual(branch.headings[0], self.path.knots()[5][1])

    def test_branch_parts_with_opposite_curvature(self):
        _, branch = design.fork(self.path, 5, steps=5)
        self.assertEqual(branch.turns[:5], [0, -1, -2, -3, -4])
        self.assertLess(branch.cumulative()[-1], 0)

    def test_the_fork_angle_is_a_triangle_power(self):
        node_heading = self.path.knots()[4][1]
        anchor, branch = design.fork(self.path, 4, steps=3, turn=3)
        self.assertEqual(anchor[1],
                         node_heading * (self.path.triangle.direction ** 3))
        self.assertEqual(branch.headings[0], anchor[1])
        self.assertNotEqual(anchor[1], node_heading)

    def test_the_fork_angle_is_an_exact_quarter_turn(self):
        node_heading = self.path.knots()[4][1]
        anchor, branch = design.fork(self.path, 4, steps=3, quarter=1)
        self.assertEqual(anchor[1], node_heading.quarter(1))
        self.assertEqual(branch.headings[0], anchor[1])
        self.assertNotEqual(anchor[1], node_heading)

    def test_no_degrees_are_involved(self):
        """A fork angle is a group element; a float angle cannot express it."""
        with self.assertRaises(ValueError):
            design.fork(self.path, 4, steps=3, quarter=22.5)


class TestJoined(unittest.TestCase):
    def setUp(self):
        self.path = design.lobe(THIN, 6)

    def test_a_fork_at_the_same_node_passes(self):
        _, branch = design.fork(self.path, 5, steps=4)
        self.assertIs(design.joined(self.path, branch, 5), branch)

    def test_the_attachment_does_not_care_which_triangle_built_the_branch(self):
        point, heading = self.path.knots()[5]
        other = Spiral(thinnest(65), heading=heading, start=point)
        other.extend([0, -1, -2])
        design.joined(self.path, other, 5)

    def test_a_branch_moved_off_the_node_fails(self):
        _, branch = design.fork(self.path, 5, steps=4)
        moved = Spiral(THIN, heading=branch.headings[0],
                       start=branch.nodes[1])
        with self.assertRaises(AssertionError) as caught:
            design.joined(self.path, moved, 5)
        self.assertIn("starts at", str(caught.exception))

    def test_a_corner_fails_the_g1_proof(self):
        _, corner = design.fork(self.path, 5, steps=4, quarter=1)
        with self.assertRaises(AssertionError) as caught:
            design.joined(self.path, corner, 5)
        self.assertIn("heads", str(caught.exception))

    def test_a_branch_at_the_exit_continues_the_line(self):
        end = len(self.path.turns)
        _, branch = design.fork(self.path, end, steps=4, sign=1)
        design.joined(self.path, branch, end)


if __name__ == "__main__":
    unittest.main()

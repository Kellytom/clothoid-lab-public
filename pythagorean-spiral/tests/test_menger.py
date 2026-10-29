"""Menger curvature: what "the curvature at a node" means, and how to hit it."""

import math
import unittest

from pythagorean_spiral import design, spans, quality
from pythagorean_spiral.triples import thinnest

THIN = thinnest(3125)


class TestMenger(unittest.TestCase):
    def test_three_points_on_a_circle(self):
        R = 5.0
        for start in (0.0, 0.7, 2.1):
            pts = [(R * math.cos(start + t), R * math.sin(start + t))
                   for t in (0.0, 0.4, 0.9)]
            self.assertAlmostEqual(quality.menger_of(*pts), 1.0 / R, places=6)

    def test_a_straight_run_of_points_has_no_curvature(self):
        self.assertAlmostEqual(
            quality.menger_of((0, 0), (1, 0), (2, 0)), 0.0, places=12)

    def test_a_reversal_keeps_the_magnitude_and_flips_the_sign(self):
        p = design.curl(200, 6, 1.0)
        prof = quality.menger_profile(p)
        node = next(iter(quality.reversal_nodes(p)))
        self.assertGreater(prof[node - 1], 0)
        self.assertLess(prof[node], 0)
        self.assertAlmostEqual(abs(prof[node - 1]), abs(prof[node]), places=9)

    def test_the_heading_peaks_one_node_before_the_reversal(self):
        p = design.curl(200, 6, 1.0)
        apex = max(range(len(p.turns)), key=lambda k: p.cumulative()[k])
        self.assertEqual(apex + 1, next(iter(quality.reversal_nodes(p))))

    def test_menger_tracks_the_chord_rule_on_a_fine_chain(self):
        p = design.curl(200, 6, 1.0)
        self.assertTrue(quality.menger_agrees_with_chord(p, tol=1e-3))

    def test_reversals_are_found(self):
        p = design.curl(200, 6, 1.0)
        self.assertEqual(len(quality.reversal_nodes(p)), 1)
        self.assertEqual(quality.reversal_nodes(design.spiral(THIN, 6)), set())


class TestTargets(unittest.TestCase):
    def test_a_corner_gets_two_targets(self):
        p = design.curl(200, 6, 1.0)
        targets = quality.curvature_targets(p)
        node = next(iter(quality.reversal_nodes(p)))
        arriving, leaving = targets[node]
        self.assertGreater(arriving, 0)
        self.assertLess(leaving, 0)
        self.assertAlmostEqual(abs(arriving), abs(leaving), places=9)

    def test_elsewhere_arriving_equals_leaving(self):
        p = design.curl(200, 6, 1.0)
        rev = quality.reversal_nodes(p)
        for k, (a, b) in enumerate(quality.curvature_targets(p)):
            if k not in rev:
                self.assertEqual(a, b)


class TestArms(unittest.TestCase):
    def test_menger_arms_land_on_their_targets(self):
        p = design.curl(200, 6, 1.0)
        curves = spans.spans(p, math.radians(20), arms="menger")
        worst, node, corner = quality.menger_agrees(curves, p)
        self.assertLess(worst, 0.05, f"worst {worst:.3f} at node {node}")
        # each span carries its own side of the corner, so both sides land
        self.assertLess(corner, 0.05)

    def test_menger_beats_the_arc_rule_at_the_knots(self):
        p = design.lobe(THIN, 7, 1.0)
        arc = quality.menger_agrees(spans.spans(p, math.radians(20), arms="arc"), p)[0]
        men = quality.menger_agrees(spans.spans(p, math.radians(20), arms="menger"), p)[0]
        self.assertLess(men, arc / 5)

    def test_arc_rule_stays_the_default(self):
        p = design.curl(200, 6, 1.0)
        default = spans.spans(p, math.radians(20))
        arc = spans.spans(p, math.radians(20), arms="arc")
        self.assertEqual([c["c1"] for c in default], [c["c1"] for c in arc])


if __name__ == "__main__":
    unittest.main()

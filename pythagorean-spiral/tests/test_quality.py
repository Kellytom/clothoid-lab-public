"""Acceleration as a design input: magnitude, not signed curvature."""

import math
import unittest

from pythagorean_spiral import design, quality
from pythagorean_spiral.triples import thinnest

THIN = thinnest(3125)


class TestMagnitude(unittest.TestCase):
    def test_peak_is_turn_over_chord(self):
        p = design.curl(200, 6, 1.0)
        expected = max(abs(t) for t in p.turns) * p.triangle.radians / float(p.length)
        self.assertAlmostEqual(quality.peak(p), expected, places=12)

    def test_the_apsis_is_continuous_in_bending(self):
        """The curl reverses curvature at its peak.  Signed, that is a jump of
        twice the peak; in magnitude it is one ordinary ramp step."""
        p = design.curl(200, 6, 1.0)
        r = quality.report(p)
        self.assertTrue(r["pinned_apsis"])
        self.assertGreater(r["signed_jump"], 1.5 * r["peak_acceleration"])
        self.assertAlmostEqual(r["jump_in_steps"], 1.0, places=9)

    def test_the_g2_closure_has_no_reversal(self):
        p = design.g2_lobe(THIN, 15, 1.0)
        r = quality.report(p)
        self.assertFalse(r["pinned_apsis"])
        self.assertAlmostEqual(r["jump_in_steps"], 1.0, places=9)

    def test_a_verdict_names_the_design(self):
        self.assertIn("designed apsis", quality.verdict(design.curl(200, 6, 1.0)))
        self.assertIn("does not reverse", quality.verdict(design.g2_lobe(THIN, 15)))

    def test_jerk_scales_with_the_chord(self):
        fine = quality.jerk(design.curl(200, 6, 2.0))
        coarse = quality.jerk(design.curl(200, 6, 1.0))
        self.assertLess(fine, coarse)


class TestAccelerationAsInput(unittest.TestCase):
    def test_chord_length_is_solved_from_the_target(self):
        target = 0.02
        p = design.curl(200, 6, accel=target)
        self.assertAlmostEqual(quality.peak(p), target, places=12)

    def test_a_softer_stroke_is_a_longer_chord(self):
        soft = design.curl(200, 6, accel=0.02)
        hard = design.curl(200, 6, accel=0.20)
        self.assertGreater(float(soft.length), float(hard.length))
        self.assertAlmostEqual(quality.peak(hard), 0.20, places=12)

    def test_the_shape_does_not_change_with_the_target(self):
        a = design.curl(200, 6, accel=0.02)
        b = design.curl(200, 6, accel=0.20)
        self.assertEqual(a.turns, b.turns)
        self.assertEqual(a.triangle, b.triangle)

    def test_rejects_a_target_that_makes_no_sense(self):
        with self.assertRaises(ValueError):
            design.chord_for_acceleration(THIN, [0, 0, 0], 1.0)
        with self.assertRaises(ValueError):
            design.chord_for_acceleration(THIN, [1, 2, 3], 0.0)


if __name__ == "__main__":
    unittest.main()

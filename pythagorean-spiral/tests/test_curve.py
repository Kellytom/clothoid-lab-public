"""The curl: resolution-driven shape, and a fit that is at the chain's floor."""

import hashlib
import math
import unittest

from pythagorean_spiral import design, spans as spanmod
from pythagorean_spiral.triples import for_angle, thinnest

THIN = thinnest(3125)


class TestForAngle(unittest.TestCase):
    def test_returns_the_thinnest_triangle_under_the_target(self):
        t = for_angle(6.0)
        self.assertLessEqual(t.degrees, 6.0)
        self.assertGreater(for_angle(6.1).degrees, t.degrees - 1e-12)

    def test_smaller_target_means_a_longer_hypotenuse(self):
        self.assertLess(for_angle(0.5).c, for_angle(0.1).c)
        self.assertLess(for_angle(0.5).degrees, for_angle(5.0).degrees)

    def test_rejects_impossible_budgets(self):
        for bad in (0, -1, 45, 90):
            with self.assertRaises(ValueError):
                for_angle(bad)


class TestCostGuard(unittest.TestCase):
    def test_refuses_a_budget_that_would_need_astronomical_integers(self):
        with self.assertRaises(ValueError) as caught:
            design.curl(200.0, 1.0, 1.0)
        self.assertIn("chord budget", str(caught.exception))


class TestCurl(unittest.TestCase):
    def setUp(self):
        self.path = design.curl(200.0, 6.0, 1.0)

    def test_peak_is_what_was_asked_for(self):
        """Within one chord turn: the triangle quantises the angle, so the
        peak can only land on a multiple of it."""
        widest = max(abs(k) for k in self.path.turns) * self.path.triangle.degrees
        self.assertAlmostEqual(self.path.peak_degrees, 200.0, delta=widest)

    def test_peak_reads_past_180(self):
        """A curl over the top says 200, not -160: the heading is unwrapped."""
        self.assertGreater(self.path.peak_degrees, 180.0)

    def test_chord_budget_is_respected(self):
        widest = max(abs(k) for k in self.path.turns) * self.path.triangle.degrees
        self.assertLessEqual(widest, 6.0)

    def test_ends_exactly_east_and_higher_than_it_started(self):
        self.assertEqual(self.path.coeff, 0)
        self.assertEqual(self.path.heading.axis_name(), "east")
        self.assertGreater(float(self.path.final[1]), 0.0)

    def test_is_still_a_lobe(self):
        n = len(self.path.turns) // 2
        self.assertEqual(len(self.path.turns), 2 * n)
        self.assertEqual(self.path.turns[0], 0)
        self.assertEqual(self.path.turns[-1], 0)
        self.assertEqual(max(self.path.turns), n - 1)

    def test_a_finer_budget_is_a_thinner_triangle(self):
        coarse = design.curl(200.0, 12.0, 1.0)
        fine = design.curl(200.0, 8.0, 1.0)
        self.assertLess(fine.triangle.degrees, coarse.triangle.degrees)
        self.assertGreater(len(fine.turns), len(coarse.turns))


class TestExponentDial(unittest.TestCase):
    def test_power_one_reproduces_the_curl_bit_for_bit(self):
        """Frozen at a8653ba: the chain was k before the dial, and is k**1."""
        p = design.curl(200.0, 6.0, 1.0)
        digest = hashlib.sha256()
        for x, y in p.nodes:
            for v in (x.numerator, x.denominator, y.numerator, y.denominator):
                raw = abs(v).to_bytes(max(1, (abs(v).bit_length() + 7) // 8),
                                      "big")
                digest.update(b"-" if v < 0 else b"+")
                digest.update(len(raw).to_bytes(4, "big"))
                digest.update(raw)
        digest.update(",".join(map(str, p.turns)).encode())
        self.assertEqual(len(p.turns), 134)
        self.assertEqual(
            digest.hexdigest(),
            "81cbac4e127dd71f9fa5e9981ba58d8493677d0ab3c5f070a1e52b72acaca49d")

    def test_every_integer_power_still_closes_exactly(self):
        """The reversal cancels the same integers, so closure is inherited."""
        for power in (0, 2, 3):
            p = design.curl(30.0, 6.0, 1.0, power=power)
            n = len(p.turns) // 2
            self.assertEqual(p.coeff, 0)
            self.assertEqual(p.heading.axis_name(), "east")
            self.assertEqual(p.turns[:n], [k ** power for k in range(n)])
            self.assertEqual(p.turns[n:],
                             [-(k ** power) for k in range(n - 1, -1, -1)])

    def test_power_must_be_a_whole_number(self):
        with self.assertRaises(ValueError):
            design.curl(200.0, 6.0, 1.0, power=1.5)
        with self.assertRaises(ValueError):
            design.lobe(THIN, 5, power=-1)

    def test_the_dial_moves_the_turning_to_the_last_chords(self):
        straight = design.curl(200.0, 6.0, 1.0, power=1)
        late = design.curl(200.0, 6.0, 1.0, power=2)
        self.assertLess(len(late.turns), len(straight.turns))
        self.assertGreater(max(late.turns), max(straight.turns))
        widest = max(late.turns) * late.triangle.degrees
        self.assertAlmostEqual(late.peak_degrees, 200.0, delta=widest)
        self.assertGreaterEqual(late.peak_degrees, 200.0)


class TestFittedCurve(unittest.TestCase):
    def setUp(self):
        self.path = design.curl(200.0, 6.0, 1.0)
        self.curves = spanmod.spans(self.path, math.radians(20))

    def test_the_only_corner_is_the_apsis_and_it_is_exact(self):
        """The chain reverses curvature at the apsis, so the drawn curve must
        corner there -- by exactly the chain's own turn at that node."""
        corner = max(abs(t) for t in self.path.turns) * self.path.triangle.radians
        self.assertAlmostEqual(spanmod.join_kink(self.curves), corner, places=9)

    def test_the_apsis_is_a_choice_and_both_modes_do_what_they_say(self):
        corner = max(abs(t) for t in self.path.turns) * self.path.triangle.radians
        sharp = spanmod.spans(self.path, math.radians(20), apsis="sharp")
        smooth = spanmod.spans(self.path, math.radians(20), apsis="smooth")
        self.assertAlmostEqual(spanmod.join_kink(sharp), corner, places=9)
        self.assertLess(spanmod.join_kink(smooth), 1e-9)
        self.assertGreater(spanmod.max_curvature(smooth),
                           2.0 * spanmod.max_curvature(sharp))

    def test_the_cubics_never_overshoot_the_chain_curvature(self):
        peak = max(abs(t) for t in self.path.turns) * self.path.triangle.radians
        self.assertLess(spanmod.max_curvature(self.curves), 1.3 * peak)

    def test_the_fit_sits_on_the_chains_own_floor(self):
        nodes = self.path.floats()
        worst = max(spanmod.deviation(c, nodes, samples=81) for c in self.curves)
        floor = spanmod.sagitta(self.path)
        self.assertLess(worst, 2.5 * floor)

    def test_no_span_swallows_the_apsis(self):
        """The reversal must fall on a span boundary, not inside a cubic."""
        apex = max(range(len(self.path.turns)), key=lambda k: self.path.cumulative()[k])
        bounds = {int(c["s0"]) for c in self.curves} | {int(c["s1"]) for c in self.curves}
        self.assertIn(apex, bounds)


if __name__ == "__main__":
    unittest.main()

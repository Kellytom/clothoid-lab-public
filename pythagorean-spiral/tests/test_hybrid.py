"""The float hybrid: the plan stays exact, the ink is measured, not asserted."""

import math
import time
import unittest

from pythagorean_spiral import hybrid
from pythagorean_spiral.triples import for_angle, thinnest

THIN = thinnest(3125)


def lobe_turns(steps: int):
    return list(range(steps)) + list(range(-(steps - 1), 1))


class TestAgainstExact(unittest.TestCase):
    def test_float_matches_exact_where_exact_is_affordable(self):
        turns = list(range(40))
        f = hybrid.build(THIN, turns)
        e = f.exact()
        gap = max(math.hypot(ax - float(bx), ay - float(by))
                  for (ax, ay), (bx, by) in zip(f.nodes, e.nodes))
        self.assertLess(gap, 1e-12)

    def test_the_plan_is_the_same_object(self):
        f = hybrid.build(THIN, lobe_turns(60))
        self.assertEqual(f.coeff, 0)
        self.assertEqual(f.cumulative()[-1], 0)
        self.assertEqual(f.peak_degrees, 59 * 60 * THIN.degrees / 2)

    def test_a_closed_lobe_closes_to_the_plan_not_to_the_drawing(self):
        f = hybrid.build(THIN, lobe_turns(500))
        self.assertEqual(f.coeff, 0)                    # exact integer plan
        self.assertLess(abs(f.heading_degrees()), 1e-10)  # float ink
        self.assertLess(f.drift(), 1e-12)


class TestExactnessInFloats(unittest.TestCase):
    def test_a_quarter_turn_is_a_swap_bit_for_bit(self):
        f = hybrid.build(THIN, [0, 0, 0])
        before = (f.hx, f.hy)
        f.cusp(1)
        self.assertEqual((f.hx, f.hy), (-before[1], before[0]))
        f.cusp(-1)
        self.assertEqual((f.hx, f.hy), before)

    def test_a_shared_node_is_the_same_float(self):
        first = hybrid.build(THIN, [0, 1, 2, 3])
        node = first.nodes[2]
        second = hybrid.build(THIN, [0, 1], start=node)
        self.assertEqual(second.nodes[0], node)

    def test_a_cusp_can_sit_on_the_final_node(self):
        f = hybrid.build(THIN, [0, 1, 2], cusps=[(3, 1)])
        self.assertEqual(f.cusps, [1])
        self.assertEqual(len(f.turns), 3)

    def test_a_cusp_past_the_end_is_refused(self):
        with self.assertRaises(ValueError):
            hybrid.build(THIN, [0, 1], cusps=[(9, 1)])


class TestScale(unittest.TestCase):
    def test_twenty_thousand_chords(self):
        start = time.perf_counter()
        f = hybrid.build(THIN, range(20000))
        elapsed = time.perf_counter() - start
        self.assertEqual(len(f.nodes), 20001)
        self.assertLess(f.drift(), 1e-12)
        self.assertLess(elapsed, 10.0)

    def test_the_rest_of_the_package_still_works(self):
        """The hybrid is an addition: the exact path is not replaced."""
        from pythagorean_spiral import design
        path = design.curl(200.0, 6.0, 1.0)
        self.assertEqual(path.coeff, 0)
        self.assertEqual(path.heading.axis_name(), "east")


class TestAngles(unittest.TestCase):
    def test_a_thirty_and_a_forty_five_degree_peak_are_exact_sums(self):
        tri = for_angle(3.0)                 # alpha just under three degrees
        for degrees in (30, 45):
            steps = round(degrees / tri.degrees) + 1
            f = hybrid.build(tri, [0] + [1] * (steps - 1))
            self.assertAlmostEqual(f.peak_degrees, degrees,
                                   delta=tri.degrees)

    def test_ninety_degrees_by_accumulation_is_a_sum_not_a_ramp(self):
        """A triangular ramp cannot land on 90; a flat schedule can."""
        tri = for_angle(3.0)
        steps = round(90 / tri.degrees) + 1
        flat = hybrid.build(tri, [0] + [1] * (steps - 1))
        self.assertAlmostEqual(flat.peak_degrees, 90, delta=tri.degrees)
        ramp = hybrid.build(tri, list(range(steps)))
        self.assertNotAlmostEqual(ramp.peak_degrees, 90,
                                  delta=tri.degrees)

    def test_the_cusp_hits_ninety_with_no_angle_at_all(self):
        f = hybrid.build(THIN, [0], cusps=[(1, 1)])
        self.assertAlmostEqual(f.heading_degrees(), 90.0, places=9)


if __name__ == "__main__":
    unittest.main()

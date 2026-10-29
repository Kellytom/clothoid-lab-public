"""G2 interpolation, splicing, projection, intersections and the CLI flags."""

import math
import os
import tempfile
import unittest

from clothoid_lab import cli, compose, engine, interpolate
from clothoid_lab.model import Design, Segment

POINTS = [(0.0, 0.0), (10.0, 5.0), (20.0, 0.0), (30.0, 8.0), (40.0, 2.0)]


class TestG2Spline(unittest.TestCase):
    def test_interpolates_and_is_g2(self):
        design = interpolate.from_points(POINTS, method="g2")
        chain = engine.build(design)
        self.assertTrue(chain.g2)
        self.assertFalse(design.g1)
        for point in POINTS:
            self.assertLess(chain.curve.project(*point)["distance"], 1e-9,
                            msg=f"point {point}")

    def test_closed_spline_closes(self):
        points = [(0.0, 0.0), (20.0, 10.0), (40.0, 0.0), (20.0, -10.0)]
        design = interpolate.from_points(points, method="g2", cyclic=True)
        chain = engine.build(design)
        self.assertTrue(chain.g2)
        gap = chain.curve.closure_gap()
        for value in gap:
            self.assertLess(abs(value), 1e-9, msg=f"closure gap {gap}")
        for point in points:
            self.assertLess(chain.curve.project(*point)["distance"], 1e-9)

    def test_per_point_directions_are_refused_for_g2(self):
        with self.assertRaises(interpolate.InterpolationError):
            interpolate.from_points(POINTS, [0.0] * len(POINTS), method="g2")

    def test_g1_still_works(self):
        design = interpolate.from_points(POINTS)
        self.assertTrue(design.g1)
        self.assertFalse(engine.build(design).g2)


class TestSmoothing(unittest.TestCase):
    def test_jump_falls(self):
        design = Design(segments=[
            Segment(kappa0=0.0, kd=1e-3, length=20.0),
            Segment(kappa0=0.05, kd=-1e-3, length=20.0),
        ])
        before = engine.build(design).max_join_kappa_error
        after_design = interpolate.smooth(design, iterations=100, epsi=1e-9)
        after = engine.build(after_design).max_join_kappa_error
        self.assertLess(after, before * 1e-6)
        self.assertTrue(after_design.g1)


class TestReverseCurve(unittest.TestCase):
    def test_s_pair_is_one_clothoid_with_zero_curvature(self):
        # A = 3125, half to the 90 degree hook; curvature crosses zero at L.
        a = 3125.0
        kd = 1.0 / (a * a)
        half = a * math.sqrt(math.pi)
        design = Design(segments=[Segment(kappa0=-kd * half, kd=kd,
                                          length=2.0 * half)])
        chain = engine.build(design)
        self.assertAlmostEqual(chain.kappa(half), 0.0, places=12)
        self.assertTrue(chain.g2)
        centre = chain.point(half)
        worst = 0.0
        for i in range(41):
            t = half * i / 40
            before = chain.point(half - t)
            after = chain.point(half + t)
            reflected = (-(after[0] - centre[0]), -(after[1] - centre[1]))
            worst = max(worst, math.dist(
                (before[0] - centre[0], before[1] - centre[1]), reflected))
        self.assertLess(worst, 1e-9)


class TestCompose(unittest.TestCase):
    def setUp(self):
        self.a = Design(segments=[Segment(kappa0=0.0, kd=1e-3, length=20.0)],
                        anchor={"x": 0.0, "y": 0.0, "angle": 0.0})
        self.b = Design(segments=[Segment(kappa0=0.0, kd=-1e-3, length=20.0)],
                        anchor={"x": 30.0, "y": 20.0, "angle": 0.5})

    def test_trim_keeps_the_range(self):
        trimmed = compose.trim(self.a, 5.0, 15.0)
        chain = engine.build(trimmed)
        self.assertAlmostEqual(chain.length, 10.0, places=9)
        origin = engine.build(self.a)
        start = chain.point(0.0)
        want = origin.point(5.0)
        self.assertAlmostEqual(start[0], want[0], places=9)
        self.assertAlmostEqual(start[1], want[1], places=9)

    def test_reverse_swaps_the_ends(self):
        reversed_design = compose.reverse(self.a)
        chain = engine.build(reversed_design)
        origin = engine.build(self.a)
        self.assertAlmostEqual(chain.length, origin.length, places=9)
        start = chain.point(0.0)
        end = origin.point(origin.length)
        self.assertAlmostEqual(start[0], end[0], places=9)
        self.assertAlmostEqual(start[1], end[1], places=9)

    def test_connect_reaches_both_poses(self):
        pose0 = (0.0, 0.0, 0.0, 0.0)
        pose1 = (10.0, 10.0, math.pi / 2, 0.0)
        connector = compose.connect(pose0, pose1, method="3arc")
        chain = engine.build(connector)
        end = chain.point(chain.length)
        self.assertAlmostEqual(end[0], 10.0, places=9)
        self.assertAlmostEqual(end[1], 10.0, places=9)
        self.assertAlmostEqual(chain.tangent(chain.length), math.pi / 2, places=9)
        self.assertAlmostEqual(chain.kappa(chain.length), 0.0, places=9)

    def test_join_is_g2_and_lands_on_second(self):
        joined = compose.join(self.a, self.b)
        chain = engine.build(joined)
        self.assertTrue(chain.g2)
        second = engine.build(self.b)
        end = chain.point(chain.length)
        want = second.point(second.length)
        self.assertAlmostEqual(end[0], want[0], places=9)
        self.assertAlmostEqual(end[1], want[1], places=9)


class TestQueries(unittest.TestCase):
    def setUp(self):
        self.horizontal = Design(
            segments=[Segment(kappa0=0.0, kd=0.0, length=20.0)],
            anchor={"x": -10.0, "y": 0.0, "angle": 0.0})
        self.vertical = Design(
            segments=[Segment(kappa0=0.0, kd=0.0, length=20.0)],
            anchor={"x": 0.0, "y": -10.0, "angle": math.pi / 2})
        self.chain_h = engine.build(self.horizontal)
        self.chain_v = engine.build(self.vertical)

    def test_projection(self):
        on = self.chain_h.curve.project(0.0, 0.0)
        self.assertLess(abs(on["distance"]), 1e-12)
        self.assertAlmostEqual(on["s"], 10.0, places=9)
        off = self.chain_h.curve.project(0.0, 3.0)
        self.assertAlmostEqual(off["distance"], 3.0, places=9)

    def test_intersection(self):
        hits = self.chain_h.curve.intersections(self.chain_v.curve)
        self.assertEqual(len(hits), 1)
        self.assertAlmostEqual(hits[0][0], 10.0, places=9)
        self.assertAlmostEqual(hits[0][1], 10.0, places=9)

    def test_iso_measurements(self):
        self.assertAlmostEqual(self.chain_h.curve.length_iso(2.0), 20.0, places=9)
        x0, y0, x1, y1 = self.chain_h.curve.bbox_iso(2.0)
        self.assertAlmostEqual(x0, -10.0, places=9)
        self.assertAlmostEqual(x1, 10.0, places=9)
        self.assertAlmostEqual(y0, 2.0, places=9)
        self.assertAlmostEqual(y1, 2.0, places=9)
        _, low, _, high = self.chain_h.curve.bbox_iso(-2.0)
        self.assertAlmostEqual(low, -2.0, places=9)
        self.assertAlmostEqual(high, -2.0, places=9)


class TestCliFlags(unittest.TestCase):
    def run_cli(self, args):
        return cli.main(args + ["--quiet"])

    def test_g2_points(self):
        with tempfile.TemporaryDirectory() as tmp:
            points = os.path.join(tmp, "p.txt")
            out = os.path.join(tmp, "g2.svg")
            with open(points, "w", encoding="utf-8") as fh:
                fh.write("0, 0\n10, 5\n20, 0\n30, 8\n")
            self.assertEqual(self.run_cli(["--points", points, "--g2", "--out", out]), 0)
            self.assertTrue(os.path.exists(out))

    def test_closed_g2_points(self):
        with tempfile.TemporaryDirectory() as tmp:
            points = os.path.join(tmp, "p.txt")
            out = os.path.join(tmp, "c.svg")
            with open(points, "w", encoding="utf-8") as fh:
                fh.write("0, 0\n20, 10\n40, 0\n20, -10\n")
            self.assertEqual(
                self.run_cli(["--points", points, "--g2", "--closed", "--out", out]), 0)

    def test_trim_and_reverse_on_a_design(self):
        with tempfile.TemporaryDirectory() as tmp:
            design = os.path.join(tmp, "d.json")
            out = os.path.join(tmp, "t.svg")
            Design(segments=[Segment(kappa0=0.0, kd=1e-3, length=20.0)]).save(design)
            self.assertEqual(
                self.run_cli(["--design", design, "--trim", "5,15", "--reverse",
                              "--out", out]), 0)
            self.assertTrue(os.path.exists(out))

    def test_flags_without_points_are_refused(self):
        with self.assertRaises(SystemExit):
            cli.main(["--preset", "ogee", "--g2", "--quiet"])


if __name__ == "__main__":
    unittest.main()

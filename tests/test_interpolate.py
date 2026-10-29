"""G1 fitting: one clothoid through two points, a spline through many."""

import math
import os
import tempfile
import unittest

from clothoid_lab import cli, engine, interpolate
from clothoid_lab.model import Design, Segment

POINTS = [(0.0, 0.0), (10.0, 5.0), (20.0, 0.0), (30.0, 8.0), (40.0, 2.0)]


def angle_error(a, b):
    """Difference between two directions, allowing for a full turn."""
    return abs(math.atan2(math.sin(a - b), math.cos(a - b)))


class TestTwoPointFit(unittest.TestCase):
    def test_hits_both_points_and_both_directions(self):
        k, dk, length = interpolate.fit((0.0, 0.0), 0.2, (10.0, 6.0), 0.9)
        design = Design(segments=[Segment(kd=dk, length=length, kappa0=k)],
                        anchor={"x": 0.0, "y": 0.0, "angle": 0.2})
        chain = engine.build(design)
        self.assertAlmostEqual(chain.point(length)[0], 10.0, delta=1e-9)
        self.assertAlmostEqual(chain.point(length)[1], 6.0, delta=1e-9)
        self.assertLess(angle_error(chain.tangent(0.0), 0.2), 1e-9)
        self.assertLess(angle_error(chain.tangent(length), 0.9), 1e-9)

    def test_same_point_is_refused(self):
        with self.assertRaises(interpolate.InterpolationError):
            interpolate.fit((1.0, 2.0), 0.0, (1.0, 2.0), 0.0)


class TestSpline(unittest.TestCase):
    def test_passes_through_every_point(self):
        design = interpolate.from_points(POINTS)
        self.assertTrue(design.g1)
        chain = engine.build(design)
        s = 0.0
        for index, point in enumerate(POINTS):
            x, y = chain.point(s)
            self.assertAlmostEqual(x, point[0], delta=1e-9, msg=f"point {index} x")
            self.assertAlmostEqual(y, point[1], delta=1e-9, msg=f"point {index} y")
            if index < len(design.segments):
                s += design.segments[index].length

    def test_every_join_is_g1_not_g2(self):
        design = interpolate.from_points(POINTS)
        chain = engine.build(design)
        self.assertFalse(chain.g2, "a fitted spline should show its curvature jumps")
        for placed in chain.segments[:-1]:
            s = placed.s_base + placed.length
            before = chain.tangent(s - 1e-7)
            after = chain.tangent(s + 1e-7)
            self.assertLess(angle_error(before, after), 1e-5)

    def test_supplied_directions_are_honoured(self):
        points = [(0.0, 0.0), (10.0, 1.0), (20.0, 0.0)]
        thetas = [0.0, 0.1, 0.0]
        design = interpolate.from_points(points, thetas)
        chain = engine.build(design)
        s = 0.0
        for index, theta in enumerate(thetas):
            self.assertLess(angle_error(chain.tangent(s), theta), 1e-9,
                            msg=f"direction at point {index}")
            if index < len(design.segments):
                s += design.segments[index].length

    def test_two_points_give_one_segment(self):
        design = interpolate.from_points([(0.0, 0.0), (10.0, 0.0)])
        self.assertEqual(len(design.segments), 1)

    def test_design_round_trip_keeps_the_flag(self):
        design = interpolate.from_points(POINTS, name="round trip")
        again = Design.from_json(design.to_json())
        self.assertTrue(again.g1)
        self.assertEqual(again.to_dict(), design.to_dict())

    def test_bad_input_is_refused(self):
        with self.assertRaises(interpolate.InterpolationError):
            interpolate.from_points([(0.0, 0.0)])
        with self.assertRaises(interpolate.InterpolationError):
            interpolate.from_points([(0.0, 0.0), (0.0, 0.0)])
        with self.assertRaises(interpolate.InterpolationError):
            interpolate.from_points(POINTS, [0.0, 0.0])
        with self.assertRaises(interpolate.InterpolationError):
            interpolate.from_points([(0.0, 0.0), (float("nan"), 1.0)])


class TestParsing(unittest.TestCase):
    def test_plain_lines_with_comments(self):
        data = interpolate.parse("# start\n0, 0\n10 5  # second\n\n20,0\n")
        self.assertEqual(data["points"], [(0.0, 0.0), (10.0, 5.0), (20.0, 0.0)])
        self.assertIsNone(data["thetas"])

    def test_json_object(self):
        data = interpolate.parse('{"points": [[0,0],[1,1]], "thetas": [0, 1], "name": "x"}')
        self.assertEqual(data["points"], [[0, 0], [1, 1]])
        self.assertEqual(data["thetas"], [0, 1])
        self.assertEqual(data["name"], "x")

    def test_bare_json_list(self):
        data = interpolate.parse("[[0,0],[1,1]]")
        self.assertEqual(data["points"], [[0, 0], [1, 1]])


class TestCli(unittest.TestCase):
    def test_points_file_writes_an_svg_and_succeeds(self):
        with tempfile.TemporaryDirectory() as tmp:
            points = os.path.join(tmp, "points.txt")
            out = os.path.join(tmp, "spline.svg")
            with open(points, "w", encoding="utf-8") as fh:
                fh.write("0, 0\n10, 5\n20, 0\n")
            code = cli.main(["--points", points, "--out", out, "--quiet"])
            self.assertEqual(code, 0)
            with open(out, "r", encoding="utf-8") as fh:
                text = fh.read()
            self.assertIn('id="spine"', text)
            self.assertIn("&quot;g1&quot;: true", text)


class TestDesignFromSpans(unittest.TestCase):
    def straight(self, p0, p3):
        dx, dy = p3[0] - p0[0], p3[1] - p0[1]
        return {"p0": p0, "c1": (p0[0] + dx / 3, p0[1] + dy / 3),
                "c2": (p0[0] + 2 * dx / 3, p0[1] + 2 * dy / 3), "p3": p3}

    def test_straight_spans_become_straight_segments(self):
        spans = [self.straight((0.0, 0.0), (10.0, 0.0)),
                 self.straight((10.0, 0.0), (25.0, 0.0))]
        design = interpolate.design_from_spans(spans, name="two")
        self.assertEqual(len(design.segments), 2)
        self.assertTrue(design.g1)
        for segment in design.segments:
            self.assertAlmostEqual(segment.kappa0, 0.0, places=9)
        self.assertAlmostEqual(sum(s.length for s in design.segments), 25.0, places=6)
        chain = engine.build(design)
        end = chain.point(chain.length)
        self.assertAlmostEqual(end[0], 25.0, places=4)
        self.assertAlmostEqual(end[1], 0.0, places=4)

    def test_quarter_circle_comes_back_with_its_curvature(self):
        k = 0.5522847498307936
        span = {"p0": (1.0, 0.0), "c1": (1.0, k), "c2": (k, 1.0), "p3": (0.0, 1.0)}
        design = interpolate.design_from_spans([span], name="quarter")
        self.assertAlmostEqual(design.segments[0].kappa0, 1.0, delta=2e-3)
        self.assertAlmostEqual(design.segments[0].length, math.pi / 2, delta=2e-3)
        chain = engine.build(design)
        start = chain.point(0.0)
        end = chain.point(chain.length)
        self.assertAlmostEqual(start[0], 1.0, places=5)
        self.assertAlmostEqual(end[1], 1.0, places=5)

    def test_rejects_empty(self):
        with self.assertRaises(interpolate.InterpolationError):
            interpolate.design_from_spans([])

    def test_rejects_a_span_with_no_length(self):
        span = {"p0": (1.0, 1.0), "c1": (1.0, 1.0),
                "c2": (1.0, 1.0), "p3": (1.0, 1.0)}
        with self.assertRaises(interpolate.InterpolationError):
            interpolate.design_from_spans([span])


if __name__ == "__main__":
    unittest.main()

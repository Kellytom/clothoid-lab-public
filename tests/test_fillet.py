import math
import unittest

from clothoid_lab import engine
from clothoid_lab.fillet import (
    FilletError, arc_segment, corner_fillet, fillet_span,
)
from clothoid_lab.model import Design, Segment


def cubic(span, t):
    u = 1 - t
    return tuple(
        u ** 3 * span["p0"][i] + 3 * u * u * t * span["c1"][i]
        + 3 * u * t * t * span["c2"][i] + t ** 3 * span["p3"][i]
        for i in (0, 1)
    )


def assert_points(test, a, b, places=12):
    test.assertAlmostEqual(a[0], b[0], places=places)
    test.assertAlmostEqual(a[1], b[1], places=places)


def straight(p0, p3):
    dx, dy = p3[0] - p0[0], p3[1] - p0[1]
    return {"p0": p0, "c1": (p0[0] + dx / 3, p0[1] + dy / 3),
            "c2": (p0[0] + 2 * dx / 3, p0[1] + 2 * dy / 3), "p3": p3}


class TestCornerFillet(unittest.TestCase):
    def test_right_angle(self):
        f = corner_fillet((10, 0), (0, 0), (0, 10), 2.0)
        self.assertAlmostEqual(f["angle"], math.pi / 2, places=12)
        self.assertAlmostEqual(f["tangent"], 2.0, places=12)
        assert_points(self, f["start"], (2.0, 0.0))
        assert_points(self, f["end"], (0.0, 2.0))
        assert_points(self, f["centre"], (2.0, 2.0))
        self.assertAlmostEqual(f["length"], math.pi, places=12)
        self.assertAlmostEqual(f["trim"][0], 2.0, places=12)
        self.assertAlmostEqual(f["trim"][1], 2.0, places=12)

    def test_arc_stays_on_the_circle(self):
        f = corner_fillet((10, 0), (0, 0), (0, 10), 2.0, segments=4)
        self.assertEqual(len(f["spans"]), 4)
        for span in f["spans"]:
            self.assertAlmostEqual(
                math.dist(span["p0"], f["centre"]), 2.0, places=9)
            self.assertAlmostEqual(
                math.dist(span["p3"], f["centre"]), 2.0, places=9)
            self.assertAlmostEqual(
                math.dist(cubic(span, 0.5), f["centre"]), 2.0, delta=1e-3)

    def test_spans_are_continuous(self):
        f = corner_fillet((10, 0), (0, 0), (0, 10), 2.0, segments=3)
        for left, right in zip(f["spans"], f["spans"][1:]):
            assert_points(self, left["p3"], right["p0"])
        assert_points(self, f["spans"][0]["p0"], f["start"])
        assert_points(self, f["spans"][-1]["p3"], f["end"])

    def test_arc_clears_the_corner_by_the_expected_distance(self):
        radius = 2.0
        f = corner_fillet((10, 0), (0, 0), (0, 10), radius)
        # closest point on the arc to the corner is along the bisector
        ux, uy = f["centre"]
        n = math.hypot(ux, uy)
        nearest = (ux - radius * ux / n, uy - radius * uy / n)
        self.assertAlmostEqual(math.hypot(*nearest),
                               radius / math.sin(math.pi / 4) - radius, places=9)

    def test_sixty_degrees(self):
        radius, angle = 1.0, math.radians(60)
        f = corner_fillet((10, 0), (0, 0),
                          (10 * math.cos(angle), 10 * math.sin(angle)), radius)
        self.assertAlmostEqual(f["angle"], angle, places=12)
        self.assertAlmostEqual(f["tangent"], radius / math.tan(angle / 2), places=12)
        self.assertAlmostEqual(f["length"], radius * (math.pi - angle), places=12)

    def test_centre_is_on_the_bisector(self):
        f = corner_fillet((8, 0), (0, 0), (0, 8), 1.5)
        cx, cy = f["centre"]
        self.assertAlmostEqual(cx, cy, places=12)
        self.assertAlmostEqual(math.hypot(cx, cy), 1.5 / math.sin(math.pi / 4), places=12)

    def test_rejects_radius_that_does_not_fit(self):
        with self.assertRaises(FilletError):
            corner_fillet((1, 0), (0, 0), (0, 1), 2.0)

    def test_rejects_collinear_edges(self):
        with self.assertRaises(FilletError):
            corner_fillet((-5, 0), (0, 0), (5, 0), 1.0)

    def test_rejects_doubled_back_edges(self):
        with self.assertRaises(FilletError):
            corner_fillet((5, 0), (0, 0), (2, 0), 1.0)

    def test_rejects_zero_length_edge(self):
        with self.assertRaises(FilletError):
            corner_fillet((0, 0), (0, 0), (0, 5), 1.0)

    def test_rejects_bad_radius_and_segments(self):
        with self.assertRaises(FilletError):
            corner_fillet((5, 0), (0, 0), (0, 5), 0.0)
        with self.assertRaises(FilletError):
            corner_fillet((5, 0), (0, 0), (0, 5), 1.0, segments=0)


class TestFilletSpan(unittest.TestCase):
    def setUp(self):
        self.left = straight((0, 0), (10, 0))
        self.right = straight((10, 0), (10, 10))

    def test_trims_both_edges_and_inserts_the_arc(self):
        spans = fillet_span([self.left, self.right], 0, 2.0)
        self.assertEqual(len(spans), 4)
        assert_points(self, spans[0]["p3"], (8.0, 0.0))
        assert_points(self, spans[1]["p0"], (8.0, 0.0))
        assert_points(self, spans[-2]["p3"], (10.0, 2.0))
        assert_points(self, spans[-1]["p0"], (10.0, 2.0))
        for left, right in zip(spans, spans[1:]):
            assert_points(self, left["p3"], right["p0"])

    def test_keeps_the_outer_ends(self):
        spans = fillet_span([self.left, self.right], 0, 2.0)
        assert_points(self, spans[0]["p0"], (0.0, 0.0))
        assert_points(self, spans[-1]["p3"], (10.0, 10.0))

    def test_rejects_a_curve(self):
        curved = {"p0": (0, 0), "c1": (5, 5), "c2": (5, 5), "p3": (10, 0)}
        with self.assertRaises(FilletError):
            fillet_span([curved, self.right], 0, 1.0)

    def test_rejects_a_missing_corner(self):
        with self.assertRaises(FilletError):
            fillet_span([self.left], 0, 1.0)
        with self.assertRaises(FilletError):
            fillet_span([self.left, self.right], 5, 1.0)

    def test_rejects_a_fillet_that_eats_a_span(self):
        short = straight((0, 0), (1, 0))
        right = straight((1, 0), (1, 10))
        with self.assertRaises(FilletError):
            fillet_span([short, right], 0, 3.0)


class TestArcSegment(unittest.TestCase):
    def test_arc_matches_the_fillet(self):
        f = corner_fillet((10, 0), (0, 0), (0, 10), 2.0)
        spec = arc_segment(f)
        segment = Segment(**spec["segment"])
        chain = engine.build(Design(name="arc", segments=[segment],
                                    anchor=spec["anchor"]))
        start = chain.point(0.0)
        end = chain.point(segment.length)
        assert_points(self, start, f["start"], places=6)
        assert_points(self, end, f["end"], places=6)
        self.assertAlmostEqual(chain.kappa(0.0), -0.5, places=9)
        self.assertAlmostEqual(chain.kappa(segment.length), -0.5, places=9)

    def test_mirrored_corner_has_the_other_hand(self):
        f = corner_fillet((10, 0), (0, 0), (0, -10), 2.0)
        spec = arc_segment(f)
        self.assertAlmostEqual(spec["segment"]["kappa0"], 0.5, places=12)

    def test_joins_are_g1_not_g2(self):
        f = corner_fillet((10, 0), (0, 0), (0, 10), 2.0)
        spec = arc_segment(f)
        arc = spec["segment"]
        design = Design(
            name="filleted run",
            anchor={"x": f["start"][0] - 8.0, "y": 0.0, "angle": 0.0},
            segments=[
                Segment(kd=0.0, length=8.0, kappa0=0.0),
                Segment(**arc),
                Segment(kd=0.0, length=8.0, kappa0=0.0),
            ],
        )
        chain = engine.build(design)
        self.assertEqual(len(chain.joins), 2)
        for join in chain.joins:
            self.assertAlmostEqual(abs(join["d_kappa"]), 0.5, places=9)
        self.assertFalse(chain.g2)


if __name__ == "__main__":
    unittest.main()

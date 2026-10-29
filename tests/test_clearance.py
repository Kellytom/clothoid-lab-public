import math
import unittest

from clothoid_lab import clearance as cl
from clothoid_lab.model import Design, Segment
from clothoid_lab.piece import Piece, Trace, build_piece


def ribbon(x: float = 0.0, y: float = 0.0, length: float = 60.0,
           angle: float = 0.0, width: float = 2.0) -> Design:
    return Design(
        name="ribbon",
        segments=[Segment(kd=0.0, length=length, kappa0=0.0)],
        anchor={"x": x, "y": y, "angle": angle},
    )


def two(y: float, gap: float, width: float = 2.0) -> Piece:
    """Two parallel ribbons with edges `gap` apart."""
    offset = gap + width
    return Piece(
        name="pair",
        stroke=0.6,
        traces=[
            Trace("a", ribbon(0.0, 0.0, width=width), width=width),
            Trace("b", ribbon(0.0, offset, width=width), width=width),
        ],
    )


class TestSegmentDistance(unittest.TestCase):
    def test_parallel(self):
        distance, pa, pb = cl.segment_distance((0, 0), (10, 0), (0, 3), (10, 3))
        self.assertAlmostEqual(distance, 3.0, places=12)
        self.assertAlmostEqual(pa[1], 0.0)
        self.assertAlmostEqual(pb[1], 3.0)

    def test_crossing_zero(self):
        distance, _, _ = cl.segment_distance((0, 0), (10, 0), (5, -5), (5, 5))
        self.assertAlmostEqual(distance, 0.0, places=12)

    def test_collinear_overlap_is_zero(self):
        distance, _, _ = cl.segment_distance((0, 0), (10, 0), (4, 0), (14, 0))
        self.assertAlmostEqual(distance, 0.0, places=12)

    def test_endpoint_to_endpoint(self):
        distance, pa, pb = cl.segment_distance((0, 0), (1, 0), (4, 3), (4, 3))
        self.assertAlmostEqual(distance, math.hypot(3.0, 3.0), places=12)
        self.assertAlmostEqual(pa[0], 1.0)
        self.assertAlmostEqual(pb[0], 4.0)

    def test_degenerate_segment(self):
        distance, _, _ = cl.segment_distance((2, 2), (2, 2), (0, 0), (4, 0))
        self.assertAlmostEqual(distance, 2.0, places=12)

    def test_parallel_offset_segments(self):
        distance, _, _ = cl.segment_distance((0, 0), (10, 0), (3, 2), (9, 2))
        self.assertAlmostEqual(distance, 2.0, places=12)


class TestFlatten(unittest.TestCase):
    def span(self, p0, c1, c2, p3):
        return {"p0": p0, "c1": c1, "c2": c2, "p3": p3}

    def test_straight_span_keeps_both_ends(self):
        points = cl.flatten([self.span((0, 0), (1, 0), (2, 0), (3, 0))], tol=0.1)
        self.assertEqual(points, [(0, 0), (3, 0)])

    def test_curve_stays_within_tolerance(self):
        # A quarter circle as a cubic: the polyline must hug it within tol.
        span = self.span((1, 0), (1, 0.5522847498), (0.5522847498, 1), (0, 1))
        tol = 0.005
        points = cl.flatten([span], tol=tol)
        self.assertGreater(len(points), 3)
        for x, y in points:
            self.assertAlmostEqual(math.hypot(x, y), 1.0, delta=0.01)
        # The chord midpoint of the first two points must not sag past tol.
        for (x0, y0), (x1, y1) in zip(points, points[1:]):
            mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
            self.assertLess(1.0 - math.hypot(mx, my), 2 * tol + 1e-9)

    def test_rejects_bad_tolerance(self):
        with self.assertRaises(ValueError):
            cl.flatten([], tol=0.0)

    def test_empty(self):
        self.assertEqual(cl.flatten([]), [])


class TestMeasure(unittest.TestCase):
    def test_clearance_met(self):
        result = cl.piece_clearance(two(0.0, 5.1), clearance=5.0, tol=0.05)
        self.assertTrue(result["ok"])
        self.assertEqual(result["violations"], [])
        self.assertGreaterEqual(result["min"]["distance"], 5.0)

    def test_clearance_broken(self):
        result = cl.piece_clearance(two(0.0, 4.8), clearance=5.0, tol=0.05)
        self.assertFalse(result["ok"])
        self.assertEqual(len(result["violations"]), 1)
        self.assertAlmostEqual(result["min"]["distance"], 4.8, delta=1e-6)
        self.assertIn("shortfall", result["violations"][0])

    def test_inside_the_flattening_band_is_a_warning(self):
        # 4.95 is below 5 by less than 2*tol, so it must not be a failure.
        result = cl.piece_clearance(two(0.0, 4.95), clearance=5.0, tol=0.05)
        self.assertTrue(result["ok"])
        self.assertEqual(result["violations"], [])
        self.assertEqual(len(result["warnings"]), 1)

    def test_one_ribbon_is_not_compared_with_itself(self):
        piece = Piece(name="single", traces=[Trace("a", ribbon(width=2.0), width=2.0)])
        result = cl.piece_clearance(piece, clearance=5.0)
        self.assertTrue(result["ok"])
        self.assertIsNone(result["min"])

    def test_mirror_gap_is_measured(self):
        piece = Piece(
            name="mirror",
            mirror=True,
            traces=[Trace("a", ribbon(x=10.0, length=50.0, width=2.0), width=2.0)],
        )
        result = cl.piece_clearance(piece, clearance=5.0)
        # The band runs x = 10..60; its mirror runs x = -60..-10.
        self.assertAlmostEqual(result["min"]["distance"], 20.0, places=6)
        self.assertTrue(result["ok"])

    def test_crossing_is_disallowed_without_a_contact(self):
        piece = Piece(
            name="cross",
            traces=[
                Trace("in", ribbon(0.0, 0.0, 60.0, width=2.0), width=2.0),
                Trace("cut", ribbon(30.0, -30.0, 60.0, angle=math.pi / 2, width=2.0),
                      width=2.0),
            ],
        )
        result = cl.piece_clearance(piece, clearance=5.0)
        self.assertFalse(result["ok"])
        self.assertGreaterEqual(len(result["disallowed"]), 1)
        self.assertAlmostEqual(result["min"]["distance"], 0.0, places=6)

    def test_crossing_allowed_by_a_declared_contact(self):
        piece = Piece(
            name="cross",
            traces=[
                Trace("in", ribbon(0.0, 0.0, 60.0, width=2.0), width=2.0),
                Trace("cut", ribbon(30.0, -30.0, 60.0, angle=math.pi / 2, width=2.0),
                      width=2.0),
            ],
        )
        contact = cl.Contact((30.0, 0.0), radius=3.0)
        result = cl.piece_clearance(piece, clearance=5.0, contacts=[contact])
        self.assertEqual(result["disallowed"], [])
        self.assertTrue(all(c["allowed"] for c in result["crossings"]))

    def test_spines_are_not_ink_by_default(self):
        piece = two(0.0, 5.1)
        groups, _ = build_piece(piece)
        rails = cl.measure(groups, clearance=5.0, roles=("rail", "cap"))
        every = cl.measure(groups, clearance=5.0, roles=("spine", "rail", "cap"))
        # Rails are 5.1 apart; the spines are 7.1, so the minima differ.
        self.assertAlmostEqual(rails["min"]["distance"], 5.1, places=6)
        self.assertAlmostEqual(every["min"]["distance"], 5.1, places=6)
        self.assertEqual(len(cl._instances(groups, 0.05, roles=("spine",))), 2)

    def test_rejects_bad_arguments(self):
        groups, _ = build_piece(two(0.0, 5.0))
        with self.assertRaises(ValueError):
            cl.measure(groups, clearance=0.0)
        with self.assertRaises(ValueError):
            cl.measure(groups, tol=0.0)

    def test_contact_waives_clearance_inside_its_footprint(self):
        # Edges at y = 1 and y = 2: 1 mm apart, so a merge.
        piece = two(0.0, 1.0)
        contact = cl.Contact((30.0, 1.5), radius=5.0,
                             a="ink/a", b="ink/b")
        result = cl.piece_clearance(piece, clearance=5.0, contacts=[contact])
        self.assertTrue(result["ok"])
        self.assertEqual(result["violations"], [])
        self.assertEqual(len(result["merged"]), 1)

    def test_contact_far_away_does_not_waive(self):
        piece = two(0.0, 1.0)
        contact = cl.Contact((30.0, 200.0), radius=2.0, a="ink/a", b="ink/b")
        result = cl.piece_clearance(piece, clearance=5.0, contacts=[contact])
        self.assertFalse(result["ok"])
        self.assertEqual(len(result["violations"]), 1)
        self.assertEqual(result["merged"], [])

    def test_contact_can_be_declared_without_waiving(self):
        piece = two(0.0, 1.0)
        contact = cl.Contact((30.0, 1.5), radius=5.0,
                             a="ink/a", b="ink/b", waives_clearance=False)
        result = cl.piece_clearance(piece, clearance=5.0, contacts=[contact])
        self.assertFalse(result["ok"])
        self.assertEqual(len(result["violations"]), 1)

    def test_piece_contacts_are_used_by_default(self):
        piece = two(0.0, 1.0)
        piece.contacts = [cl.Contact((30.0, 1.5), 5.0, "ink/a", "ink/b")]
        result = cl.piece_clearance(piece, clearance=5.0)
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["merged"]), 1)

    def test_merged_pairs_appear_in_the_report(self):
        result = cl.piece_clearance(two(0.0, 1.0), clearance=5.0,
                                    contacts=[cl.Contact((30.0, 1.5), 5.0)])
        self.assertIn("merged", result)
        self.assertEqual(result["merged"][0]["a"], "ink/a")

    def test_named_contact_only_covers_its_pair(self):
        contact = cl.Contact((0.0, 0.0), radius=10.0, a="ink/in", b="ink/other")
        self.assertTrue(contact.allows((1.0, 0.0), "ink/other", "ink/in"))
        self.assertFalse(contact.allows((1.0, 0.0), "ink/in", "ink/cut"))

    def test_contact_rejects_bad_radius(self):
        with self.assertRaises(ValueError):
            cl.Contact((0, 0), radius=0.0)

    def test_report_shape(self):
        result = cl.piece_clearance(two(0.0, 5.1))
        for key in ("ok", "min", "violations", "warnings", "crossings",
                    "piece", "fit_ok", "margin"):
            self.assertIn(key, result)


if __name__ == "__main__":
    unittest.main()

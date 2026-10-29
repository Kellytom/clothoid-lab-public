"""The cubic fit and the rails: tolerance is a promise, so it gets measured."""

import math
import unittest

from clothoid_lab import bezier, engine, presets
from clothoid_lab.model import Design, Segment
from clothoid_lab.offsets import build_rail, build_rails, cusp_ranges, rail_deviation


class TestFit(unittest.TestCase):
    def test_the_fit_lands_inside_its_tolerance(self):
        for name in presets.PRESETS:
            chain = engine.build(presets.get(name))
            for tol in (0.5, 0.05, 0.02):
                spans, info = bezier.fit_chain(chain, tol=tol)
                self.assertLessEqual(info["error_max"], tol,
                                     f"{name} at tol {tol}: {info['error_max']}")
                self.assertEqual(info["spans"], len(spans))

    def test_a_tighter_tolerance_never_uses_fewer_cubics(self):
        chain = engine.build(presets.get("ogee"))
        counts = []
        for tol in (1.0, 0.1, 0.02, 0.005):
            spans, _ = bezier.fit_chain(chain, tol=tol)
            counts.append(len(spans))
        self.assertEqual(counts, sorted(counts), counts)

    def test_the_split_factor_is_a_dial_on_evenness(self):
        chain = engine.build(presets.get("s-curve"))
        for split in (2, 3, 4, 8):
            spans, info = bezier.fit_chain(chain, tol=0.02, split=split)
            self.assertLessEqual(info["error_max"], 0.02, f"split {split}")
            self.assertEqual(info["split"], split)
            self.assertEqual(len(spans), info["spans"])
            for span in spans:
                self.assertLess(span["s0"], span["s1"])

    def test_a_split_of_one_is_refused(self):
        chain = engine.build(presets.get("ogee"))
        with self.assertRaises(ValueError):
            bezier.fit_interval(0.0, 10.0, chain.point, chain.tangent, split=1)

    def test_a_straight_span_is_one_cubic(self):
        chain = engine.build(Design(segments=[Segment(kappa0=0.0, kd=0.0, length=30.0)]))
        spans, info = bezier.fit_chain(chain, tol=1e-6)
        self.assertEqual(info["spans"], 1)
        self.assertLess(info["error_max"], 1e-6)

    def test_span_endpoints_sit_on_the_curve(self):
        chain = engine.build(presets.get("bracket"))
        spans, _ = bezier.fit_chain(chain, tol=0.05)
        for span in spans:
            self.assertLess(math.dist(span["p0"], chain.point(span["s0"])), 1e-12)
            self.assertLess(math.dist(span["p3"], chain.point(span["s1"])), 1e-12)
            self.assertLess(span["s0"], span["s1"])

    def test_the_cubic_leaves_along_the_tangent(self):
        chain = engine.build(presets.get("s-curve"))
        spans, _ = bezier.fit_chain(chain, tol=0.05)
        for span in spans:
            want = chain.tangent(span["s0"])
            dx = span["c1"][0] - span["p0"][0]
            dy = span["c1"][1] - span["p0"][1]
            self.assertAlmostEqual(math.atan2(dy, dx), want, places=9)


class TestRails(unittest.TestCase):
    def test_a_zero_offset_rail_is_the_spine(self):
        chain = engine.build(presets.get("ogee"))
        rail = build_rail(chain, 0.0, tol=0.02)
        self.assertLess(rail_deviation(rail, chain), 0.02)
        self.assertEqual(rail["folds"], [])

    def test_distance_is_held_along_the_rail(self):
        chain = engine.build(presets.get("bracket"))
        rail = build_rail(chain, 5.0, tol=0.05)
        for span in rail["spans"]:
            for t in (0.0, 0.5, 1.0):
                p = bezier.cubic_at(span, t)
                d = min(math.dist(p, chain.point(chain.length * i / 2000))
                        for i in range(2001))
                self.assertAlmostEqual(d, 5.0, delta=0.12)

    def test_a_fold_is_reported_where_the_offset_outruns_the_radius(self):
        chain = engine.build(presets.get("bracket"))
        r_min, _ = chain.min_radius()
        self.assertEqual(cusp_ranges(chain, r_min * 0.5), [])
        folds = cusp_ranges(chain, r_min * 1.2)
        self.assertTrue(folds, "an offset past the centre of curvature must fold")
        self.assertGreater(folds[0][1], folds[0][0])

    def test_the_margin_is_the_room_left_before_a_fold(self):
        chain = engine.build(presets.get("bracket"))
        rail = build_rail(chain, 4.0, tol=0.05)
        self.assertAlmostEqual(rail["margin"], rail["min_radius"] - 4.0, places=9)
        self.assertGreater(rail["margin"], 0)

    def test_a_folded_rail_is_clamped_and_counted(self):
        # A fold reverses the rail inside a span, so the parabola arm runs away.
        # It must be bounded and reported, not left to place a control point
        # fifty metres from the drawing.
        chain = engine.build(presets.get("bracket"))
        r_min, _ = chain.min_radius()
        rail = build_rail(chain, r_min * 1.5, tol=0.02)
        self.assertTrue(rail["folds"])
        self.assertGreater(rail["clamped"], 0)
        reach = max(abs(v) for span in rail["spans"]
                    for p in (span["p0"], span["c1"], span["c2"], span["p3"])
                    for v in p)
        self.assertLess(reach, 1e3, "a clamped rail must stay near the drawing")

    def test_a_clean_rail_has_nothing_clamped(self):
        chain = engine.build(presets.get("ogee"))
        rail = build_rail(chain, 2.0, tol=0.02)
        self.assertEqual(rail["clamped"], 0)

    def test_both_rails_and_both_signs(self):
        chain = engine.build(presets.get("petal"))
        rails = build_rails(chain, [3.0, -3.0], tol=0.05)
        self.assertEqual([r["distance"] for r in rails], [3.0, -3.0])
        self.assertNotEqual(rails[0]["spans"][0]["p0"], rails[1]["spans"][0]["p0"])


if __name__ == "__main__":
    unittest.main()

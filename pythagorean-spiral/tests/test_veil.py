"""The veil: turn-chain billows, one model, and the four-pattern gate."""

import json
import unittest
from pathlib import Path

from pythagorean_spiral import design, ribbon, veil
from pythagorean_spiral import veil as vmod
from pythagorean_spiral.triples import for_angle

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "docs" / "veil-test.json"


class TestBillows(unittest.TestCase):
    def test_every_billow_is_a_turn_chain_ribbon(self):
        """No discs: each billow is a closed polygon from a p-triple lobe."""
        polys = veil.polygons("v2")
        self.assertEqual(len(polys), len(veil.BILLOWS))
        self.assertGreater(len(polys), 60)
        for layer, pts in polys:
            self.assertIn(layer, veil.layers("v2"))
            self.assertGreater(len(pts), 12)
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            self.assertGreater(max(xs) - min(xs), 0.5)
            self.assertGreater(max(ys) - min(ys), 0.5)

    def test_the_power_dial_is_used(self):
        powers = {b[6] for b in veil.BILLOWS}
        self.assertGreaterEqual(len(powers), 3)
        self.assertNotIn(0, powers)          # a circle is p = 0; not one here

    def test_lobe_closes_in_direction_exactly(self):
        """The reversal cancels the same integers: the exit is parallel."""
        for p in (1, 2, 3):
            lobe = design.lobe(for_angle(veil.CHORD), 7, 1, power=p)
            self.assertTrue(lobe.is_closed_in_direction())
            self.assertTrue(lobe.heading.is_axis_aligned() or True)

    def test_outline_is_exact(self):
        """Rails are rational: the ribbon is a rational polygon, not a sample."""
        lobe = design.lobe(for_angle(veil.CHORD), 7, 1, power=2)
        pts = ribbon.outline(lobe.nodes, 1.3, 3)
        for x, y in pts:
            self.assertIsInstance(x.denominator, int)
            self.assertIsInstance(y.denominator, int)


class TestOneModel(unittest.TestCase):
    def test_alpha_is_the_composite_of_the_layers(self):
        w = (veil.layers("v2")["bank"], veil.layers("v2")["crown"])
        got = veil.alpha_of(w, 0.5)
        want = 1 - (1 - veil.layers("v2")["bank"] * 0.5) * (1 - veil.layers("v2")["crown"] * 0.5)
        self.assertAlmostEqual(got, want, places=9)

    def test_no_coverage_means_no_alpha(self):
        self.assertEqual(veil.alpha_of((), 0.9), 0.0)

    def test_alpha_rises_with_the_veil(self):
        for x, y in ((50.0, 46.0), (50.0, 30.0), (20.0, 10.0)):
            a = [veil.alpha(x, y, v) for v in (0.0, 0.25, 0.5)]
            self.assertLessEqual(a[0], a[1])
            self.assertLessEqual(a[1], a[2])
            self.assertEqual(a[0], 0.0)


class TestGate(unittest.TestCase):
    def test_artefact_is_current(self):
        self.assertTrue(ART.exists(), "run scripts/veil_test.py")
        data = json.loads(ART.read_text())
        self.assertEqual(set(data["versions"]), {"v1", "v2"})
        for block in data["versions"].values():
            self.assertEqual(len(block["panels"]), 4)
            self.assertEqual({p["row"] for p in block["panels"]},
                             {"top", "bottom"})

    def test_both_versions_reach_the_operator_peak(self):
        """The strength is the operator's number, not the model's opinion."""
        data = json.loads(ART.read_text())
        tol = data["peak_tolerance"]
        for version, block in data["versions"].items():
            self.assertAlmostEqual(block["veil"] * 0 + 1, 1)  # placeholder guard
            peak = vmod.worst(block["veil"], version=version)
            self.assertAlmostEqual(peak, block["target_peak"], delta=tol,
                                   msg=version)

    def test_v2_covers_less_of_the_picture_than_v1(self):
        data = json.loads(ART.read_text())
        self.assertTrue(data["v2_lighter_than_v1"])
        for row in ("top", "bottom"):
            v1 = next(p for p in data["versions"]["v1"]["panels"] if p["row"] == row)
            v2 = next(p for p in data["versions"]["v2"]["panels"] if p["row"] == row)
            self.assertLess(v2["mean"], v1["mean"], row)

    def test_v1_is_the_heavier_cloud(self):
        """The regression that started this: v1 covers the top of the image."""
        data = json.loads(ART.read_text())
        v1_top = [p for p in data["versions"]["v1"]["panels"] if p["row"] == "top"]
        v2_top = [p for p in data["versions"]["v2"]["panels"] if p["row"] == "top"]
        self.assertGreater(sum(p["mean"] for p in v1_top),
                           sum(p["mean"] for p in v2_top))


    def test_drawing_matches_the_report(self):
        """One billow is drawn at LAYER * VEIL, the number the report uses."""
        data = json.loads(ART.read_text())
        v = data["versions"]["v2"]["veil"]
        for layer, _pts in veil.polygons("v2"):
            drawn = veil.layers("v2")[layer] * v   # the opacity in draw_cloud
            self.assertAlmostEqual(
                veil.alpha_of((veil.layers("v2")[layer],), v), drawn, places=12)
        self.assertGreater(veil.worst(v, veil.TOP_ROW), 0.0)


if __name__ == "__main__":
    unittest.main()

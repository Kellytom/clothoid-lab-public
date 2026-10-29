"""Cubics, SVG, and the seam into the existing writer."""

import math
import sys
import unittest
from pathlib import Path

from pythagorean_spiral import design, spans as spanmod, svg
from pythagorean_spiral.triples import thinnest

THIN = thinnest(3125)
REPO = Path(__file__).resolve().parents[2]


class TestCubics(unittest.TestCase):
    def test_unsmoothed_one_chord_span_is_that_chord(self):
        p = design.spiral(THIN, 4, 3121)
        curves = spanmod.spans(p, math.radians(0.1), sharp=0.0)
        first = curves[0]
        self.assertAlmostEqual(first["c1"][1], first["p0"][1], places=9)
        self.assertAlmostEqual(
            math.dist(first["p0"], first["c1"]),
            math.dist(first["p0"], first["p3"]) / 3.0, places=6)

    def test_smoothing_leaves_no_kink_away_from_a_reversal(self):
        p = design.spiral(THIN, 4, 3121)          # no curvature reversal
        smooth = spanmod.spans(p, math.radians(20))
        self.assertLess(spanmod.join_kink(smooth), 1e-9)
        sharp = spanmod.spans(p, math.radians(0.1), sharp=0.0)
        self.assertGreater(spanmod.join_kink(sharp), math.radians(1))

    def test_a_curvature_reversal_is_left_sharp(self):
        p = design.lobe(THIN, 7, 3121)
        corner = max(abs(t) for t in p.turns) * p.triangle.radians
        self.assertAlmostEqual(spanmod.join_kink(spanmod.spans(p, math.radians(20))),
                               corner, places=9)

    def test_fit_reaches_the_chain_resolution(self):
        p = design.lobe(THIN, 7, 3121)
        nodes = p.floats()
        curves = spanmod.spans(p, math.radians(20))
        worst = max(spanmod.deviation(c, nodes) for c in curves)
        floor = spanmod.sagitta(p)
        self.assertLess(worst, 3 * floor)
        self.assertLess(worst, 0.10 * float(p.length))

    def test_sagitta_grows_with_the_turn(self):
        slow = design.spiral(THIN, 3, 1)
        fast = design.spiral(THIN, 30, 1)
        self.assertGreater(spanmod.sagitta(fast), spanmod.sagitta(slow))

    def test_every_cubic_starts_at_a_node(self):
        p = design.hook(THIN, 8, None, 3121)
        nodes = p.floats()
        for c in spanmod.spans(p, math.radians(20)):
            self.assertIn(c["p0"], nodes)
            self.assertIn(c["p3"], nodes)


class TestSvg(unittest.TestCase):
    def test_document_is_well_formed_and_flipped(self):
        p = design.lobe(THIN, 5, 3121)
        curves = spanmod.spans(p, math.radians(20))
        text = svg.document(p, curves, page=(100, 100))
        self.assertIn("<svg", text)
        self.assertIn("</svg>", text)
        self.assertIn("<path", text)
        ys = [pt[1] for pt in p.floats()]
        self.assertGreater(max(ys), min(ys))
        # y flips at output: the highest design point is nearest the top
        circles = [ln for ln in text.splitlines() if "<circle" in ln]
        top = min(float(ln.split('cy="')[1].split('"')[0]) for ln in circles[:len(p.nodes)])
        self.assertLess(top, 100)


class TestIntegration(unittest.TestCase):
    """The polygon must be drawable by clothoid-lab's writer, untouched."""

    def test_spans_feed_the_existing_path_writer(self):
        if not (REPO / "clothoid_lab" / "svg.py").exists():
            self.skipTest("clothoid_lab not on this checkout")
        sys.path.insert(0, str(REPO))
        try:
            from clothoid_lab import svg as lab_svg
        finally:
            sys.path.pop(0)
        p = design.lobe(THIN, 5, 3121)
        curves = spanmod.spans(p, math.radians(20))
        d = lab_svg.path_d(curves)
        self.assertTrue(d.startswith("M "))
        self.assertEqual(d.count("C "), len(curves))


if __name__ == "__main__":
    unittest.main()

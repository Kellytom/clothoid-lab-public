import math
import unittest

from clothoid_lab import engine
from clothoid_lab.grammar import STUDY_01, band, fleur_right, study_01
from clothoid_lab.piece import render_piece

# Nodes produced by the original generator (ornament_set.js, study-01), with
# its 3125-lattice snap. Our exact segments should agree within that snap.
REFERENCE = [
    (0.0, -330.0), (65.0, -25.0), (120.0, -25.0), (436.992, -226.944),
    (249.984, -25.024), (250.0, 25.0), (364.352, 210.432), (422.912, 474.56),
    (423.0, 1000.0), (160.0, 25.024), (110.0, 25.0), (0.0, 1180.0),
]


class TestFleurRight(unittest.TestCase):
    def test_span_count_matches_the_original(self):
        self.assertEqual(len(fleur_right(STUDY_01)["spans"]), 11)

    def test_every_node_matches_the_original(self):
        nodes = fleur_right(STUDY_01)["nodes"]
        self.assertEqual(len(nodes), len(REFERENCE))
        for index, (ours, reference) in enumerate(zip(nodes, REFERENCE)):
            self.assertAlmostEqual(ours[0], reference[0], delta=0.1,
                                   msg=f"node {index} x")
            self.assertAlmostEqual(ours[1], reference[1], delta=0.1,
                                   msg=f"node {index} y")

    def test_corners_are_recorded_where_the_old_chain_turns(self):
        spans = fleur_right(STUDY_01)["spans"]
        corners = [s.corner for s in spans]
        self.assertEqual(corners[0], 0.0)
        self.assertGreater(abs(corners[1]), 1e-6,
                           "the tail base should be a corner, not a smooth turn")
        self.assertTrue(all(abs(c) <= math.pi for c in corners))

    def test_arcs_and_euler_are_exact_families(self):
        spans = fleur_right(STUDY_01)["spans"]
        families = ["arc" if s.kd == 0.0 and s.kappa0 != 0.0
                    else ("euler" if s.kd != 0.0 else "line") for s in spans]
        self.assertEqual(families.count("arc"), 4)
        self.assertEqual(families.count("euler"), 1)
        self.assertEqual(families.count("line"), 6)


class TestBand(unittest.TestCase):
    def test_band_is_closed(self):
        ring = band(STUDY_01)
        self.assertEqual(len(ring["spans"]), 4)
        design = study_01().traces[1].design
        chain = engine.build(design)
        end = chain.point(chain.length)
        self.assertAlmostEqual(end[0], -STUDY_01["bandHalf"], delta=0.1)
        self.assertAlmostEqual(end[1], -25.0, delta=0.1)


class TestStudy(unittest.TestCase):
    def test_piece_shape(self):
        piece = study_01()
        self.assertTrue(piece.mirror)
        self.assertEqual([t.name for t in piece.traces], ["half", "band"])
        self.assertEqual(piece.traces[0].width, 25.0)
        self.assertFalse(piece.traces[1].mirror)

    def test_renders(self):
        text, info = render_piece(study_01(), tol=0.05, margin=10)
        self.assertIn('id="ink-half"', text)
        self.assertIn('id="ink-half-mirrored"', text)
        self.assertIn('id="ink-band"', text)
        self.assertTrue(info["fit_ok"])


if __name__ == "__main__":
    unittest.main()

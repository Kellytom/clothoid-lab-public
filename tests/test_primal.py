import unittest

from clothoid_lab import primal
from clothoid_lab.piece import render_piece


class TestPrimal(unittest.TestCase):
    def test_each_element_builds_and_renders(self):
        for name, build in primal.PRIMAL.items():
            with self.subTest(element=name):
                piece = build()
                text, info = render_piece(piece, tol=0.05)
                self.assertIn(f'id="ink-{name}"', text)
                self.assertTrue(info["fit_ok"])

    def test_terminals_are_legal_for_each(self):
        expected = {"earth": "taper", "water": "round",
                    "air": "round", "fire": "point"}
        for name, build in primal.PRIMAL.items():
            trace = build().traces[0]
            self.assertEqual(trace.terminals[1], expected[name])

    def test_earth_uses_real_corners(self):
        corners = [s.corner for s in primal.earth().traces[0].design.segments]
        self.assertGreater(abs(corners[1]), 0.4)


if __name__ == "__main__":
    unittest.main()

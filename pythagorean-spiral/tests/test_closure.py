"""Exact closures, and the pairs the source notes got wrong."""

import unittest

from pythagorean_spiral.closure import (
    closure_pairs, g2_pairs, inverse_triangular, triangular,
)


class TestTriangular(unittest.TestCase):
    def test_round_trip(self):
        for k in range(0, 80):
            self.assertEqual(inverse_triangular(triangular(k)), k)

    def test_nonsquare_has_no_answer(self):
        self.assertIsNone(inverse_triangular(2))
        self.assertIsNone(inverse_triangular(5))


class TestClosures(unittest.TestCase):
    def test_multiplier_two(self):
        self.assertEqual(closure_pairs(2, 40), [(3, 2), (20, 14)])

    def test_multiplier_three(self):
        self.assertIn((9, 5), closure_pairs(3, 40))
        self.assertNotIn((9, 4), closure_pairs(3, 40))

    def test_multiplier_eight(self):
        self.assertIn((15, 5), closure_pairs(8, 40))
        self.assertIn((32, 11), closure_pairs(8, 40))

    def test_multiplier_four_has_no_exact_pair(self):
        self.assertEqual(closure_pairs(4, 120), [])

    def test_the_claimed_15_in_8_out_does_not_close(self):
        self.assertNotIn((15, 8), closure_pairs(2, 40))
        self.assertNotEqual(2 * triangular(8), triangular(15))

    def test_g2_pairs(self):
        self.assertEqual(g2_pairs(120), [(2, 3), (14, 20), (84, 119)])


if __name__ == "__main__":
    unittest.main()

"""The bounded solver used by the exercises."""

import math
import unittest

from clothoid_lab.solve import least_squares


class TestLeastSquares(unittest.TestCase):
    def test_solves_a_linear_system(self):
        result = least_squares(lambda v: [v[0] - 3.0, v[1] + 2.0], [0.0, 0.0])
        self.assertTrue(result.converged)
        self.assertAlmostEqual(result.x[0], 3.0, places=9)
        self.assertAlmostEqual(result.x[1], -2.0, places=9)

    def test_solves_a_nonlinear_system(self):
        # x^2 + y^2 = 25, x = y
        def residual(v):
            return [v[0] * v[0] + v[1] * v[1] - 25.0, v[0] - v[1]]
        result = least_squares(residual, [2.0, 2.0])
        self.assertTrue(result.converged)
        self.assertAlmostEqual(result.x[0], math.sqrt(12.5), places=8)
        self.assertAlmostEqual(result.x[1], math.sqrt(12.5), places=8)

    def test_bounds_hold(self):
        result = least_squares(lambda v: [v[0], v[1] - 5.0], [0.0, 0.0],
                               lower=[1.0, -math.inf], upper=[math.inf, 10.0])
        self.assertAlmostEqual(result.x[0], 1.0, places=9)
        self.assertAlmostEqual(result.x[1], 5.0, places=9)


if __name__ == "__main__":
    unittest.main()

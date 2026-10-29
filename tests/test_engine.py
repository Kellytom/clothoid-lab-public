"""The engine against an independent integral, and the joins it promises."""

import math
import unittest

from clothoid_lab import engine, presets
from clothoid_lab.model import Design, Segment


def simpson(f, a, b, n=20000):
    h = (b - a) / n
    total = f(a) + f(b)
    for i in range(1, n):
        total += (4 if i % 2 else 2) * f(a + i * h)
    return total * h / 3.0


class TestAgainstTheIntegral(unittest.TestCase):
    """A clothoid is defined by an integral, so the library must match one."""

    def test_half_turn_reference(self):
        # theta = s^2 / 2, the pole-free pace with w = 1.
        chain = engine.build(Design(segments=[Segment(kappa0=0.0, kd=1.0, length=2.0)]))
        for s in (0.5, 1.0, 2.0):
            x, y = chain.point(s)
            rx = simpson(lambda u: math.cos(u * u / 2.0), 0.0, s)
            ry = simpson(lambda u: math.sin(u * u / 2.0), 0.0, s)
            self.assertAlmostEqual(x, rx, delta=1e-9, msg=f"x at s={s}")
            self.assertAlmostEqual(y, ry, delta=1e-9, msg=f"y at s={s}")

    def test_curvature_is_linear_in_arc_length(self):
        chain = engine.build(Design(segments=[Segment(kappa0=0.004, kd=0.002, length=25.0)]))
        for s in (0.0, 6.0, 25.0):
            self.assertAlmostEqual(chain.kappa(s), 0.004 + 0.002 * s, places=12)
        self.assertAlmostEqual(chain.tangent(25.0), 0.004 * 25 + 0.002 * 625 / 2, places=12)

    def test_straight_is_exact(self):
        design = Design(segments=[Segment(kappa0=0.0, kd=0.0, length=10.0)],
                        anchor={"x": 2.0, "y": 3.0, "angle": math.pi / 2})
        chain = engine.build(design)
        x, y = chain.point(10.0)
        self.assertAlmostEqual(x, 2.0, places=12)
        self.assertAlmostEqual(y, 13.0, places=12)


class TestCorners(unittest.TestCase):
    def test_a_tangent_corner_is_kept(self):
        design = Design(segments=[
            Segment(kd=0.0, length=10.0, kappa0=0.0),
            Segment(kd=0.0, length=10.0, kappa0=0.0, corner=math.pi / 2),
        ])
        chain = engine.build(design)
        x, y = chain.point(20.0)
        self.assertAlmostEqual(x, 10.0, places=12)
        self.assertAlmostEqual(y, 10.0, places=12)
        self.assertAlmostEqual(chain.tangent(20.0), math.pi / 2, places=12)
        self.assertEqual(chain.corner_count, 1)
        self.assertFalse(chain.g2)

    def test_the_corner_survives_json(self):
        design = Design(segments=[
            Segment(kd=0.0, length=10.0, kappa0=0.0,
                    corner=math.radians(30)),
        ])
        again = Design.from_json(design.to_json())
        self.assertAlmostEqual(again.segments[0].corner, math.radians(30), places=12)


class TestJoins(unittest.TestCase):
    """Where two segments meet, position, direction and curvature must agree."""

    def test_every_preset_is_g2(self):
        for name in presets.PRESETS:
            chain = engine.build(presets.get(name))
            self.assertTrue(chain.g2, f"{name} is not G2")
            self.assertEqual(chain.max_join_kappa_error, 0.0, name)

    def test_an_explicit_mismatch_is_reported_not_hidden(self):
        design = Design(segments=[
            Segment(kappa0=0.0, kd=0.01, length=10.0),     # ends at 0.1
            Segment(kappa0=0.0, kd=0.0, length=5.0),       # restarts at 0: G1 only
        ])
        chain = engine.build(design)
        self.assertFalse(chain.g2)
        self.assertAlmostEqual(chain.max_join_kappa_error, 0.1, places=12)

    def test_the_chain_is_continuous_in_position(self):
        chain = engine.build(presets.get("bracket"))
        for join in chain.joins:
            s = join["at"]
            before = chain.point(s - 1e-7)
            after = chain.point(s + 1e-7)
            self.assertLess(math.dist(before, after), 1e-5)


class TestRadius(unittest.TestCase):
    def test_min_radius_is_the_largest_curvature(self):
        chain = engine.build(Design(segments=[Segment(kappa0=0.0, kd=0.01, length=20.0)]))
        r, s = chain.min_radius()
        self.assertAlmostEqual(r, 1.0 / 0.2, places=6)
        self.assertAlmostEqual(s, 20.0, places=6)

    def test_a_straight_chain_has_no_radius(self):
        chain = engine.build(Design(segments=[Segment(kappa0=0.0, kd=0.0, length=8.0)]))
        self.assertEqual(chain.min_radius()[0], float("inf"))


if __name__ == "__main__":
    unittest.main()

"""The compiled library against the wheel: the same source, two ways in.

This is not an independent check of the mathematics. Both backends are
Bertolazzi's code, so a wrong formula is wrong in both. What it does check is
the thing that actually breaks in a ctypes wrapper: a swapped argument, a wrong
restype, a handle freed under a live curve, a chain built at the wrong anchor.
"""

import math
import unittest

from clothoid_lab import backend, engine, presets


class TestBackendAgreement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.status = backend.available()
        if not cls.status.get("bertolazzi", "").startswith("ok"):
            raise unittest.SkipTest(f"compiled library unavailable: {cls.status.get('bertolazzi')}")
        if not cls.status.get("pyclothoids", "").startswith("ok"):
            raise unittest.SkipTest("wheel unavailable")

    def test_the_two_backends_draw_the_same_chain(self):
        for name in presets.PRESETS:
            design = presets.get(name)
            compiled = engine.build(design, backend="bertolazzi")
            wheel = engine.build(design, backend="pyclothoids")
            self.assertAlmostEqual(compiled.length, wheel.length, places=9, msg=name)
            for i in range(41):
                s = compiled.length * i / 40
                ax, ay = compiled.point(s)
                bx, by = wheel.point(s)
                self.assertLess(math.hypot(ax - bx, ay - by), 1e-9,
                                f"{name}: positions diverge at s={s}")
                self.assertAlmostEqual(compiled.tangent(s), wheel.tangent(s), places=9)
                self.assertAlmostEqual(compiled.kappa(s), wheel.kappa(s), places=9)

    def test_the_exact_offset_agrees_with_the_normal_step(self):
        # X_ISO is the library's exact parallel curve; the wheel builds the same
        # point by stepping along the normal. On a clothoid the two must agree.
        design = presets.get("ogee")
        compiled = engine.build(design, backend="bertolazzi")
        wheel = engine.build(design, backend="pyclothoids")
        for i in range(21):
            s = compiled.length * i / 20
            ax, ay = compiled.offset_point(s, 3.0)
            bx, by = wheel.offset_point(s, 3.0)
            self.assertLess(math.hypot(ax - bx, ay - by), 1e-9, f"offset diverges at s={s}")

    def test_the_anchor_is_honoured(self):
        design = presets.get("bracket")
        design.anchor = {"x": 17.0, "y": -4.0, "angle": 0.7}
        compiled = engine.build(design, backend="bertolazzi")
        x, y = compiled.point(0.0)
        self.assertAlmostEqual(x, 17.0, places=12)
        self.assertAlmostEqual(y, -4.0, places=12)
        self.assertAlmostEqual(compiled.tangent(0.0), 0.7, places=12)

    def test_an_unknown_backend_is_refused(self):
        with self.assertRaises(KeyError):
            engine.build(presets.get("ogee"), backend="spiro")

    def test_the_report_names_the_backend(self):
        chain = engine.build(presets.get("petal"), backend="pyclothoids")
        self.assertEqual(engine.report(chain)["backend"], "pyclothoids")


if __name__ == "__main__":
    unittest.main()

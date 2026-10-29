import math
import unittest

from clothoid_lab.bundle import Bundle
from clothoid_lab.model import Design, Segment
from clothoid_lab.piece import Trace
from clothoid_lab.section import sections


def ribbon(y=0.0, width=6.0):
    return Design(name="r", segments=[Segment(kd=0.0, length=20.0, kappa0=0.0)],
                  anchor={"x": 0.0, "y": y, "angle": 0.0})


class TestSections(unittest.TestCase):
    def test_straight_ribbon_sections(self):
        got = sections(Trace("r", ribbon(), width=6.0), samples=4)
        self.assertEqual(len(got), 5)
        for section in got:
            self.assertAlmostEqual(section.left[1], 3.0, places=6)
            self.assertAlmostEqual(section.right[1], -3.0, places=6)
            self.assertAlmostEqual(section.tangent[0], 1.0, places=9)
        self.assertAlmostEqual(got[0].spine[0], 0.0, places=6)
        self.assertAlmostEqual(got[-1].spine[0], 20.0, delta=1e-6)

    def test_widthless_stroke_has_coincident_rails(self):
        got = sections(Trace("r", ribbon(), width=None), samples=2)
        for section in got:
            self.assertEqual(section.left, section.right)
            self.assertEqual(section.left, section.spine)

    def test_rejects_bad_sample_count(self):
        with self.assertRaises(ValueError):
            sections(Trace("r", ribbon(), width=6.0), samples=0)


class TestBundle(unittest.TestCase):
    def test_check_fails_when_members_crowd(self):
        bundle = Bundle("sheaf", [
            Trace("a", ribbon(0.0), width=2.0),
            Trace("b", ribbon(3.0), width=2.0),
        ], clearance=5.0)
        self.assertFalse(bundle.check()["ok"])

    def test_check_passes_when_members_keep_clear(self):
        bundle = Bundle("sheaf", [
            Trace("a", ribbon(0.0), width=2.0),
            Trace("b", ribbon(8.0), width=2.0),
        ], clearance=5.0)
        self.assertTrue(bundle.check()["ok"])

    def test_footprint_is_the_design_box(self):
        bundle = Bundle("box", [Trace("a", ribbon(0.0), width=2.0)])
        x0, y0, x1, y1 = bundle.footprint()
        self.assertAlmostEqual(x0, 0.0, places=3)
        self.assertAlmostEqual(x1, 20.0, places=3)
        self.assertAlmostEqual(y0, -1.0, places=3)
        self.assertAlmostEqual(y1, 1.0, places=3)

    def test_needs_a_name_and_a_member(self):
        with self.assertRaises(ValueError):
            Bundle("", [Trace("a", ribbon(), width=2.0)])
        with self.assertRaises(ValueError):
            Bundle("empty", [])


if __name__ == "__main__":
    unittest.main()

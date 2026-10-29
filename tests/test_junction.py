import math
import unittest

from clothoid_lab import engine
from clothoid_lab.clearance import piece_clearance
from clothoid_lab.fillet import FilletError
from clothoid_lab.junction import Junction


def sample(**overrides) -> Junction:
    values = dict(corner=(0.0, 0.0), branch_end=(30.0, 0.0),
                  trunk_end=(0.0, 40.0))
    values.update(overrides)
    return Junction(**values)


class TestJunctionBuild(unittest.TestCase):
    def test_piece_has_branch_trunk_and_contact(self):
        built = sample().build()
        piece = built["piece"]
        self.assertEqual([t.name for t in piece.traces], ["branch", "trunk"])
        self.assertEqual(len(piece.contacts), 1)
        contact = piece.contacts[0]
        self.assertEqual({contact.a, contact.b}, {"ink/branch", "ink/trunk"})
        self.assertTrue(contact.waives_clearance)

    def test_report_records_the_fillet(self):
        report = sample(radius=6.0).build()["report"]
        self.assertAlmostEqual(report["angle"], math.pi / 2, places=12)
        self.assertAlmostEqual(report["tangent"], 6.0, places=9)
        self.assertAlmostEqual(report["arc_length"], 3 * math.pi, places=9)
        self.assertAlmostEqual(report["curvature_step"], 1.0 / 6.0, places=12)
        self.assertEqual(report["join"], "G1")

    def test_branch_ends_on_the_trunk_with_its_tangent(self):
        built = sample().build()
        branch = built["piece"].traces[0]
        chain = engine.build(branch.design)
        end = chain.point(chain.length)
        self.assertAlmostEqual(end[0], 0.0, places=6)
        self.assertAlmostEqual(end[1], 6.0, places=6)
        angle = chain.tangent(chain.length)  # radians, not a vector
        self.assertAlmostEqual(abs(math.cos(angle)), 0.0, places=6)
        self.assertAlmostEqual(abs(math.sin(angle)), 1.0, places=6)

    def test_branch_join_is_g1(self):
        branch = sample().build()["piece"].traces[0]
        chain = engine.build(branch.design)
        self.assertEqual(len(chain.joins), 1)
        self.assertAlmostEqual(abs(chain.joins[0]["d_kappa"]), 1.0 / 6.0, places=9)
        self.assertFalse(chain.g2)

    def test_branch_terminal_is_a_taper(self):
        branch = sample().build()["piece"].traces[0]
        self.assertEqual(branch.terminals, ("cone", "butt"))

    def test_rejects_a_radius_that_does_not_fit(self):
        with self.assertRaises(FilletError):
            sample(radius=40.0).build()

    def test_rejects_bad_widths(self):
        with self.assertRaises(ValueError):
            sample(branch_width=0.0)


class TestJunctionClearance(unittest.TestCase):
    def test_merge_is_declared_and_accepted(self):
        built = sample().build()
        result = piece_clearance(built["piece"], clearance=5.0)
        self.assertTrue(result["ok"])
        self.assertEqual(result["violations"], [])
        self.assertEqual(len(result["merged"]), 1)

    def test_without_the_contact_the_merge_is_a_violation(self):
        piece = sample().build()["piece"]
        piece.contacts = []
        result = piece_clearance(piece, clearance=5.0)
        self.assertFalse(result["ok"])
        self.assertGreaterEqual(len(result["violations"]), 1)
        self.assertEqual(result["merged"], [])

    def test_check_returns_the_report(self):
        result = sample().check(clearance=5.0)
        self.assertIn("piece", result)
        self.assertTrue(result["ok"])

    def test_clearance_outside_the_footprint_still_applies(self):
        # A junction does not license a second branch crowding the first.
        built = sample().build()
        piece = built["piece"]
        piece.contacts = []
        result = piece_clearance(piece, clearance=5.0)
        self.assertFalse(result["ok"])


if __name__ == "__main__":
    unittest.main()

import unittest

from clothoid_lab.model import Design, Segment
from clothoid_lab.contact import Contact
from clothoid_lab.piece import Piece, Trace, render_piece
from clothoid_lab.presets import s_curve


def band() -> Design:
    return Design(
        name="band",
        segments=[Segment(kd=0.0, length=80.0, kappa0=0.0)],
        anchor={"x": -40.0, "y": 50.0, "angle": 0.0},
    )


class TestPiece(unittest.TestCase):
    def test_renders_named_groups_and_mirror(self):
        piece = Piece(
            name="test piece",
            mirror=True,
            stroke=0.6,
            traces=[
                Trace("right", s_curve(), width=6.0),
                Trace("band", band(), mirror=False),
            ],
        )
        text, info = render_piece(piece, tol=0.05, frame=(200, 250), margin=10)
        self.assertIn('id="ink-right"', text)
        self.assertIn('id="ink-right-rail-3"', text)
        self.assertIn('id="ink-right-mirrored"', text)
        self.assertIn('id="ink-band"', text)
        self.assertNotIn('id="ink-band-mirrored"', text)
        self.assertIn('&quot;mirror&quot;: true', text)
        self.assertEqual(len(info["traces"]), 2)
        self.assertEqual(info["traces"][1]["mirrored"], False)
        self.assertTrue(info["fit_ok"])

    def test_mirror_adds_paths(self):
        piece = Piece(
            name="mirror check",
            mirror=True,
            traces=[Trace("right", s_curve(), width=4.0)],
        )
        text, _ = render_piece(piece, tol=0.05, frame=(200, 250))
        mirrored = text.count("-mirrored")
        self.assertGreaterEqual(mirrored, 2)  # spine plus at least one rail

    def test_round_trip(self):
        piece = Piece(
            name="round trip",
            mirror=True,
            traces=[Trace("right", s_curve(), width=6.0, layer="ink")],
        )
        restored = Piece.from_dict(piece.to_dict())
        self.assertEqual(restored.to_dict(), piece.to_dict())

    def test_rejects_empty_piece(self):
        with self.assertRaises(ValueError):
            Piece(name="empty", traces=[])

    def test_rejects_bad_width(self):
        with self.assertRaises(ValueError):
            Trace("bad", s_curve(), width=0.0)

    def test_contacts_are_part_of_the_piece(self):
        piece = Piece(
            name="junction",
            traces=[Trace("a", s_curve(), width=6.0)],
            contacts=[Contact((0.0, 3.0), 2.5, "ink/a", "ink/b")],
        )
        restored = Piece.from_dict(piece.to_dict())
        self.assertEqual(restored.to_dict(), piece.to_dict())
        self.assertEqual(len(restored.contacts), 1)
        self.assertAlmostEqual(restored.contacts[0].radius, 2.5)

    def test_rejects_a_contact_that_is_not_one(self):
        with self.assertRaises(ValueError):
            Piece(name="bad", traces=[Trace("a", s_curve(), width=6.0)],
                  contacts=[("not", "a", "contact")])


if __name__ == "__main__":
    unittest.main()

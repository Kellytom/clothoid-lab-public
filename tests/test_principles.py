import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARDS = json.loads((ROOT / "reference" / "principles.json").read_text())
MANIFEST = json.loads((ROOT / "reference" / "manifest.json").read_text())


class TestCards(unittest.TestCase):
    def test_every_card_is_complete(self):
        self.assertEqual(len(CARDS), 8)
        ids = [c["id"] for c in CARDS]
        self.assertEqual(len(ids), len(set(ids)))
        for card in CARDS:
            self.assertIn(card["class"], {"primal", "archetype"})
            self.assertGreater(len(card["gesture"].split()), 20, card["id"])
            self.assertEqual(len(card["numbers"]), 3, card["id"])
            self.assertGreaterEqual(len(card["not_this"]), 2, card["id"])

    def test_primal_ids_are_the_four(self):
        primal = {c["id"] for c in CARDS if c["class"] == "primal"}
        self.assertEqual(primal, {"earth", "water", "air", "fire"})

    def test_manifest_points_at_real_files(self):
        """No phantom rows: every file the manifest names is on disk.

        This is the integrity half of the rule, and it is never allowed to slip.
        A row that outlives its image turns the manifest into a claim about a
        file nobody has.
        """
        for row in MANIFEST:
            path = ROOT / "reference" / row["file"]
            self.assertTrue(path.is_file(), row["file"])
            self.assertGreater(path.stat().st_size, 1000, row["file"])

    def test_every_card_has_a_reference(self):
        """The coverage half, which reports rather than blocks.

        A card without an image is a gap in the reference set, not a broken
        build: `docs/principles.html` already renders "no references" for one.
        It is skipped loudly instead of failing, so the gap stays visible in a
        verbose run without holding the suite red until the images are chosen.
        """
        subjects = {row["subject"] for row in MANIFEST}
        missing = sorted(c["id"] for c in CARDS if c["id"] not in subjects)
        if missing:
            self.skipTest("cards with no reference image yet: " + ", ".join(missing))

    def test_page_matches_the_cards(self):
        page = (ROOT / "docs" / "principles.html").read_text()
        for card in CARDS:
            self.assertIn(card["name"], page)
            self.assertIn(card["gesture"], page)


if __name__ == "__main__":
    unittest.main()


class TestCardGeometry(unittest.TestCase):
    """The cards' numbers are assertions about the rendered grammar."""

    def stats(self, piece):
        import math
        segments = piece.traces[0].design.segments
        turns = [abs(math.degrees(s.kappa0 * s.length + 0.5 * s.kd * s.length ** 2))
                 for s in segments]
        corners = [abs(math.degrees(s.corner)) for s in segments]
        return {"segments": len(segments),
                "max_segment_turn_deg": max(turns),
                "max_corner_deg": max(corners),
                "terminal": piece.traces[0].terminals[1]}

    def test_primal_cards_match_their_geometry(self):
        from clothoid_lab import primal
        for card in CARDS:
            if card["class"] != "primal":
                continue
            got = self.stats(primal.PRIMAL[card["id"]]())
            check = card["check"]
            with self.subTest(element=card["id"]):
                self.assertEqual(got["segments"], check["segments"])
                self.assertLessEqual(
                    got["max_segment_turn_deg"],
                    check["max_segment_turn_deg"] + 1e-6)
                self.assertLessEqual(
                    got["max_corner_deg"], check.get("max_corner_deg", 0.0) + 1e-6)
                self.assertEqual(got["terminal"], check["terminal"])

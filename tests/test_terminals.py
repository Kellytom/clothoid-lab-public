import math
import unittest

from clothoid_lab import engine
from clothoid_lab.model import Design, Segment
from clothoid_lab.offsets import build_rail
from clothoid_lab.piece import Piece, Trace, render_piece
from clothoid_lab.terminals import (
    TERMINALS, ARC_RADIUS, TAPER_FACTOR, terminal_extension, terminal_spans,
    width_law,
)


def ribbon(length: float = 60.0, y: float = 0.0) -> Design:
    """A straight ribbon: the simplest case where every end is measurable."""
    return Design(
        name="ribbon",
        segments=[Segment(kd=0.0, length=length, kappa0=0.0)],
        anchor={"x": 0.0, "y": y, "angle": 0.0},
    )


def rails(width: float = 8.0, length: float = 60.0):
    chain = engine.build(ribbon(length))
    half = width / 2.0
    return build_rail(chain, half), build_rail(chain, -half)


class TestTerminalSpans(unittest.TestCase):
    def test_butt_adds_nothing(self):
        pos, neg = rails()
        self.assertEqual(terminal_spans(pos, neg, "butt"), [])

    def test_point_meets_at_a_tip_one_half_width_out(self):
        width = 8.0
        pos, neg = rails(width)
        spans = terminal_spans(pos, neg, "point")
        self.assertEqual(len(spans), 2)
        tip = spans[0]["p3"]
        self.assertAlmostEqual(tip[0], 60.0 + width / 2.0, places=6)
        self.assertAlmostEqual(tip[1], 0.0, places=6)
        # Straight sides: each control point sits on the chord, a third of the way.
        for span in spans:
            p0, p3 = span["p0"], span["p3"]
            self.assertAlmostEqual(span["c1"][0], p0[0] + (p3[0] - p0[0]) / 3.0, places=6)
            self.assertAlmostEqual(span["c1"][1], p0[1] + (p3[1] - p0[1]) / 3.0, places=6)

    def test_round_is_a_half_width_semicircle(self):
        width = 8.0
        pos, neg = rails(width)
        spans = terminal_spans(pos, neg, "round")
        self.assertEqual(len(spans), 1)
        span = spans[0]
        self.assertAlmostEqual(span["p0"][1], width / 2.0, places=6)
        self.assertAlmostEqual(span["p3"][1], -width / 2.0, places=6)
        # Midpoint of the cubic sits one half-width past the rail ends.
        x = (span["p0"][0] + 3 * span["c1"][0] + 3 * span["c2"][0] + span["p3"][0]) / 8.0
        self.assertAlmostEqual(x, 60.0 + width / 2.0, places=6)

    def test_arc_is_shallower_than_round(self):
        width = 8.0
        pos, neg = rails(width)
        arc = terminal_spans(pos, neg, "arc")[0]
        x = (arc["p0"][0] + 3 * arc["c1"][0] + 3 * arc["c2"][0] + arc["p3"][0]) / 8.0
        half = width / 2.0
        sagitta = ARC_RADIUS - math.sqrt(ARC_RADIUS ** 2 - half ** 2)
        self.assertAlmostEqual(x, 60.0 + sagitta, places=6)
        self.assertLess(sagitta, half)

    def test_taper_converges_further_out_than_point(self):
        width = 8.0
        pos, neg = rails(width)
        spans = terminal_spans(pos, neg, "taper")
        self.assertEqual(len(spans), 2)
        tip = spans[0]["p3"]
        self.assertAlmostEqual(tip[0], 60.0 + TAPER_FACTOR * width / 2.0, places=6)
        self.assertGreater(TAPER_FACTOR * width / 2.0, width / 2.0)

    def test_start_end_mirror_each_other(self):
        pos, neg = rails()
        start = terminal_spans(pos, neg, "round", end="start")
        end = terminal_spans(pos, neg, "round", end="end")
        self.assertAlmostEqual(start[0]["p0"][0], 0.0, places=6)
        self.assertAlmostEqual(end[0]["p3"][0], 60.0, places=6)

    def test_width_laws_meet_the_stroke_at_g2(self):
        # Recovered from the ornaments stage-two page: w(1) = 1/2 and both
        # derivatives vanish, so the taper starts without a step.
        for kind in ("bulb", "cone"):
            law = width_law(kind)
            self.assertAlmostEqual(law(0.0), 0.0, places=12)
            self.assertAlmostEqual(law(1.0), 0.5, places=12)
            h = 1e-4
            slope = (law(1.0) - law(1.0 - h)) / h
            self.assertLess(abs(slope), 1e-3, msg=f"{kind} slope at the join")
            curvature = (law(1.0) - 2 * law(1.0 - h) + law(1.0 - 2 * h)) / (h * h)
            self.assertLess(abs(curvature), 1e-2, msg=f"{kind} curvature at the join")

    def test_bulb_swells_wider_than_cone(self):
        bulb, cone = width_law("bulb"), width_law("cone")
        self.assertGreater(bulb(0.5), cone(0.5) * 1.3)

    def test_law_tapers_end_at_the_centreline_tip(self):
        width = 8.0
        pos, neg = rails(width)
        for kind in ("bulb", "cone"):
            spans = terminal_spans(pos, neg, kind)
            tip = spans[len(spans) // 2 - 1]["p3"]  # plus side ends at the tip
            self.assertAlmostEqual(tip[0], 60.0 + TAPER_FACTOR * width / 2.0, places=3)
            self.assertAlmostEqual(tip[1], 0.0, places=3)
            self.assertAlmostEqual(
                terminal_extension(kind, width), TAPER_FACTOR * width / 2.0)

    def test_extension_matches_geometry(self):
        width = 8.0
        self.assertEqual(terminal_extension("butt", width), 0.0)
        self.assertEqual(terminal_extension("point", width), width / 2.0)
        self.assertEqual(terminal_extension("round", width), width / 2.0)
        self.assertAlmostEqual(
            terminal_extension("arc", width),
            ARC_RADIUS - math.sqrt(ARC_RADIUS ** 2 - (width / 2.0) ** 2),
            places=9,
        )
        self.assertEqual(terminal_extension("taper", width), TAPER_FACTOR * width / 2.0)


class TestPieceTerminals(unittest.TestCase):
    def test_each_terminal_renders_a_named_cap_at_both_ends(self):
        for kind in TERMINALS:
            with self.subTest(kind=kind):
                piece = Piece(
                    name=f"{kind} strip",
                    stroke=0.6,
                    traces=[Trace("ribbon", ribbon(), width=8.0,
                                   terminals=(kind, kind))],
                )
                text, info = render_piece(piece, tol=0.05, margin=5)
                if kind == "butt":
                    self.assertNotIn("-end-butt", text)
                    self.assertNotIn("-start-butt", text)
                else:
                    self.assertIn(f'id="ink-ribbon-start-{kind}"', text)
                    self.assertIn(f'id="ink-ribbon-end-{kind}"', text)
                for terminal in info["traces"][0]["terminals"]:
                    self.assertEqual(terminal["kind"], kind)
                    self.assertFalse(terminal["fold"])
                    self.assertGreaterEqual(terminal["extension"], 0.0)

    def test_butt_is_the_baseline_and_draws_no_cap(self):
        butt = Piece(name="butt", traces=[Trace("r", ribbon(), width=8.0)])
        point = Piece(
            name="point",
            traces=[Trace("r", ribbon(), width=8.0, terminals=("point", "point"))],
        )
        text_butt, info_butt = render_piece(butt, tol=0.05)
        text_point, _ = render_piece(point, tol=0.05)
        # One cap path per end; each cap path holds both sides of the tip.
        self.assertEqual(text_butt.count("<path"), text_point.count("<path") - 2)
        cap = [line for line in text_point.splitlines() if 'id="ink-r-end-point"' in line][0]
        self.assertEqual(cap.count(" C "), 2)
        self.assertTrue(all(t["kind"] == "butt" for t in info_butt["traces"][0]["terminals"]))

    def test_caps_mirror_with_the_piece(self):
        piece = Piece(
            name="mirror terminals",
            mirror=True,
            traces=[Trace("r", ribbon(), width=8.0, terminals=("butt", "round"))],
        )
        text, _ = render_piece(piece, tol=0.05)
        self.assertIn('id="ink-r-mirrored-end-round"', text)

    def test_single_name_sets_both_ends(self):
        trace = Trace("r", ribbon(), width=8.0, terminals="taper")
        self.assertEqual(trace.terminals, ("taper", "taper"))

    def test_round_trip_keeps_terminals(self):
        piece = Piece(
            name="round trip",
            mirror=True,
            traces=[Trace("r", ribbon(), width=8.0, terminals=("arc", "taper"))],
        )
        restored = Piece.from_dict(piece.to_dict())
        self.assertEqual(restored.to_dict(), piece.to_dict())

    def test_rejects_unknown_terminal(self):
        with self.assertRaises(ValueError):
            Trace("r", ribbon(), width=8.0, terminals=("butt", "chamfer"))

    def test_rejects_negative_width(self):
        with self.assertRaises(ValueError):
            Trace("r", ribbon(), width=-2.0)

    def test_rejects_terminal_without_a_ribbon(self):
        with self.assertRaises(ValueError):
            Trace("r", ribbon(), terminals=("butt", "round"))

    def test_rejects_a_folded_ribbon(self):
        tight = Design(
            name="tight circle",
            segments=[Segment(kd=0.0, length=40.0, kappa0=0.5)],
            anchor={"x": 0.0, "y": 0.0, "angle": 0.0},
        )
        piece = Piece(
            name="fold",
            traces=[Trace("curl", tight, width=8.0, terminals=("butt", "round"))],
        )
        with self.assertRaises(ValueError) as caught:
            render_piece(piece, tol=0.05)
        self.assertIn("fold", str(caught.exception))

    def test_butt_still_draws_a_folded_ribbon(self):
        # The fold guard belongs to the terminals; a butt end must not start
        # rejecting drawings W01 accepted.
        tight = Design(
            name="tight circle",
            segments=[Segment(kd=0.0, length=40.0, kappa0=0.5)],
            anchor={"x": 0.0, "y": 0.0, "angle": 0.0},
        )
        piece = Piece(name="fold", traces=[Trace("curl", tight, width=8.0)])
        text, info = render_piece(piece, tol=0.05)
        self.assertIn("<svg", text)
        self.assertFalse(info["traces"][0]["terminals"][1]["fold"])


if __name__ == "__main__":
    unittest.main()

"""The SVG layer: what Inkscape will actually be handed."""

import os
import re
import unittest

from clothoid_lab import bezier, cli, engine, presets, svg
from clothoid_lab.model import Design, Segment


def build(name="s-curve", width=6.0, prec=4):
    design = presets.get(name)
    text, info = cli.render(design, tol=0.02, width=width, prec=prec)
    return design, text, info


class TestNumbers(unittest.TestCase):
    def test_no_exponent_notation_ever_reaches_the_path(self):
        for name in presets.PRESETS:
            _, text, _ = build(name)
            d = re.search(r' d="([^"]*)"', text).group(1)
            self.assertNotIn("e", d.lower(), name)
            self.assertNotIn("E", d, name)

    def test_precision_is_respected(self):
        _, text, _ = build(prec=3)
        for d in re.findall(r' d="([^"]*)"', text):
            for number in re.findall(r"-?\d+\.(\d+)", d):
                self.assertLessEqual(len(number), 3, d[:80])

    def test_tiny_numbers_becomes_zero_not_dust(self):
        self.assertEqual(svg.num(1e-9, 4), "0")
        self.assertEqual(svg.num(-1e-9, 4), "0")
        self.assertEqual(svg.num(-0.0, 4), "0")
        self.assertEqual(svg.num(12.5, 4), "12.5")
        self.assertEqual(svg.num(-3.14159, 3), "-3.142")

    def test_a_non_finite_coordinate_is_refused(self):
        with self.assertRaises(ValueError):
            svg.num(float("nan"))


class TestDocument(unittest.TestCase):
    def test_millimetre_units_and_no_transform(self):
        design, text, _ = build()
        self.assertIn('width="', text)
        self.assertIn("mm", text)
        self.assertIn("viewBox=", text)
        self.assertNotIn("transform=", text)
        self.assertNotIn("matrix(", text)

    def test_a_fixed_page_does_not_move_with_the_drawing(self):
        design = presets.get("ogee")
        wide, _ = cli.render(design, tol=0.02, width=6.0, page=(210.0, 148.0))
        narrow, _ = cli.render(presets.get("bracket"), tol=0.02, width=6.0,
                               page=(210.0, 148.0))
        for text in (wide, narrow):
            self.assertIn('width="210mm"', text)
            self.assertIn('height="148mm"', text)
            self.assertIn('viewBox="0 0 210 148"', text)

    def test_a_frame_keeps_the_sheet_and_fills_it(self):
        for name in ("ogee", "bracket", "petal"):
            text, _ = cli.render(presets.get(name), width=6.0, frame=(200.0, 120.0))
            self.assertIn('viewBox="0 0 200 120"', text, name)
            pts = []
            for d in re.findall(r' d="([^"]*)"', text):
                for _, vals in svg.parse_d(d):
                    pts += list(zip(vals[0::2], vals[1::2]))
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            self.assertGreaterEqual(min(ys), 4.99, name)
            self.assertLessEqual(max(ys), 115.01, name)
            self.assertLess(abs((max(xs) + min(xs)) / 2 - 100.0), 0.01, name)

    def test_a_frame_smaller_than_its_margin_is_refused(self):
        with self.assertRaises(ValueError):
            cli.render(presets.get("ogee"), frame=(8.0, 8.0), margin=5.0)

    def test_a_page_smaller_than_the_drawing_is_refused(self):
        with self.assertRaises(ValueError):
            cli.render(presets.get("ogee"), tol=0.02, width=6.0, page=(10.0, 10.0))

    def test_one_path_per_rail(self):
        _, text, info = build(width=6.0)
        self.assertEqual(len(re.findall(r"<path ", text)), 1 + len(info["rails"]))
        self.assertIn('id="spine"', text)

    def test_the_path_starts_with_a_move_then_only_curves(self):
        _, text, _ = build()
        d = re.search(r'id="spine" d="([^"]*)"', text).group(1)
        tokens = svg.parse_d(d)
        self.assertEqual(tokens[0][0], "M")
        self.assertEqual({cmd for cmd, _ in tokens}, {"M", "C"})
        self.assertEqual(sum(1 for cmd, _ in tokens if cmd == "C"), len(tokens) - 1)

    def test_the_design_survives_the_round_trip(self):
        design, text, _ = build()
        recovered = Design.from_dict(svg.metadata_design(text))
        self.assertEqual(recovered.to_dict(), design.to_dict())

    def test_the_writer_refuses_an_empty_path(self):
        with self.assertRaises(ValueError):
            svg.path_d([])


class TestInkscapeView(unittest.TestCase):
    """The zoom is Inkscape's, in the file. A rebuild must not throw it away."""

    def setUp(self):
        import tempfile
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, "drawing.svg")

    def tearDown(self):
        self.dir.cleanup()

    def _save_as_inkscape_would(self, zoom="2.5", cx="105", cy="74"):
        """Write the file, then add what Inkscape writes when a human saves."""
        text, _ = cli.render(presets.get("ogee"), width=6.0, page=(210.0, 148.0))
        view = (f'<sodipodi:namedview id="namedview1" pagecolor="#ffffff" '
                f'bordercolor="#666666" borderopacity="1.0" '
                f'inkscape:document-units="mm" inkscape:zoom="{zoom}" '
                f'inkscape:cx="{cx}" inkscape:cy="{cy}" '
                f'inkscape:current-layer="clothoid"/>')
        text = text.replace(
            '<svg xmlns="http://www.w3.org/2000/svg"',
            '<svg xmlns="http://www.w3.org/2000/svg"\n'
            '     xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"\n'
            '     xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"', 1)
        text = text.replace("<title>", "  " + view + "\n  <title>", 1)
        svg.write(self.path, text)

    def test_a_file_without_a_view_reports_none(self):
        text, _ = cli.render(presets.get("ogee"), width=6.0)
        svg.write(self.path, text)
        self.assertIsNone(svg.read_view(self.path))

    def test_the_zoom_and_pan_survive_a_rebuild(self):
        self._save_as_inkscape_would(zoom="2.5", cx="105", cy="74")
        view = svg.read_view(self.path)
        self.assertIsNotNone(view)
        text, _ = cli.render(presets.get("bracket"), width=6.0,
                             page=(210.0, 148.0), view=view)
        self.assertIn('inkscape:zoom="2.5"', text)
        self.assertIn('inkscape:cx="105"', text)
        self.assertIn('inkscape:cy="74"', text)
        self.assertIn('xmlns:sodipodi=', text)
        self.assertIn('xmlns:inkscape=', text)
        # the view comes before the drawing, as Inkscape expects
        self.assertLess(text.index("namedview"), text.index("<g id="))

    def test_the_view_is_read_back_from_what_we_wrote(self):
        self._save_as_inkscape_would(zoom="0.8")
        view = svg.read_view(self.path)
        text, _ = cli.render(presets.get("ogee"), width=6.0,
                             page=(210.0, 148.0), view=view)
        svg.write(self.path, text)
        again = svg.read_view(self.path)
        self.assertIn('inkscape:zoom="0.8"', again)


class TestCommandLine(unittest.TestCase):
    def test_a_fold_does_not_fail_the_run_but_a_bad_fit_does(self):
        design = presets.get("bracket")
        chain = engine.build(design)
        r_min, _ = chain.min_radius()
        _, info = cli.render(design, tol=0.02, width=2.0 * r_min * 1.2)
        self.assertTrue(info["rails"][0]["folds"] or info["rails"][1]["folds"])
        self.assertTrue(info["ok"], "a fold is a reported shape, not a failure")

    def test_an_impossible_tolerance_reports_over_tolerance(self):
        design = presets.get("bracket")
        _, info = cli.render(design, tol=1e-9, max_spans=2)
        self.assertFalse(info["ok"])

    def test_the_verdict_names_a_broken_join(self):
        from clothoid_lab.model import Design, Segment
        from clothoid_lab import cli
        design = Design(segments=[Segment(kappa0=0.0, kd=0.01, length=10.0),
                                  Segment(kappa0=0.0, kd=0.0, length=10.0)])
        _, info = cli.render(design, tol=0.02)
        text = cli.format_report(info, 0.02)
        self.assertIn("G1 not G2", text)
        self.assertIn("kappa0 to null", text)
        self.assertFalse(info["ok"])
        self.assertTrue(info["fit_ok"], "the fit is fine; the join is not")

    def test_report_states_the_numbers(self):
        design = presets.get("ogee")
        _, info = cli.render(design, tol=0.02, width=6.0)
        text = cli.format_report(info, 0.02)
        self.assertIn("joins", text)
        self.assertIn("G2", text)
        self.assertIn("mm", text)


class TestAnnotations(unittest.TestCase):
    def test_marks_are_standard_svg(self):
        design = presets.get("s-curve")
        marks = [
            {"kind": "line", "x1": 0.0, "y1": 0.0, "x2": 10.0, "y2": 0.0,
             "width": 0.25},
            {"kind": "circle", "x": 5.0, "y": 5.0, "r": 1.0, "front": True},
            {"kind": "text", "x": 5.0, "y": 5.0, "text": "a & b", "size": 4.0,
             "front": True},
        ]
        text, _ = cli.render(design, width=6.0, annotations=marks)
        self.assertIn('<g id="annotation-lines">', text)
        self.assertIn('<g id="annotations">', text)
        self.assertIn("<line ", text)
        self.assertIn("<circle ", text)
        self.assertIn("a &amp; b</text>", text)
        self.assertIn('font-size="4"', text)
        self.assertNotIn("transform=", text)

    def test_output_is_y_up(self):
        design = presets.get("s-curve")
        chain = engine.build(design)
        x0, y0, x1, y1 = chain.bounds()
        marks = [
            {"kind": "circle", "x": x0, "y": y0, "r": 1.0, "front": True},
            {"kind": "circle", "x": x0, "y": y1, "r": 1.0, "front": True},
        ]
        text, _ = cli.render(design, width=6.0, annotations=marks)
        ys = [float(v) for v in re.findall(r'<circle cx="[^"]*" cy="([^"]*)"', text)]
        self.assertEqual(len(ys), 2)
        self.assertLess(ys[1], ys[0], "the larger design y must sit higher on the page")


class TestModel(unittest.TestCase):
    def test_json_round_trip(self):
        design = presets.get("petal")
        again = Design.from_json(design.to_json())
        self.assertEqual(again.to_dict(), design.to_dict())

    def test_a_zero_length_segment_is_refused(self):
        with self.assertRaises(ValueError):
            Segment(kd=0.0, length=0.0)

    def test_a_design_needs_a_segment(self):
        with self.assertRaises(ValueError):
            Design(segments=[])

    def test_null_kappa_means_continue(self):
        design = Design(segments=[Segment(kd=0.01, length=10.0),
                                  Segment(kd=-0.01, length=10.0)])
        chain = engine.build(design)
        self.assertTrue(chain.g2)
        self.assertTrue(chain.joins[0]["inherited"])


if __name__ == "__main__":
    unittest.main()

"""The two-window loop: seed, rebuild, and refuse to clobber on a bad edit."""

import json
import os
import tempfile
import unittest

from clothoid_lab import cli, watch
from clothoid_lab.model import Design


class TestWatch(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.design = os.path.join(self.dir.name, "design.json")
        self.out = os.path.join(self.dir.name, "drawing.svg")

    def tearDown(self):
        self.dir.cleanup()

    def test_a_missing_design_is_seeded_from_a_preset(self):
        design = watch.seed(self.design, "ogee")
        self.assertTrue(os.path.exists(self.design))
        self.assertEqual(Design.load(self.design).to_dict(), design.to_dict())

    def test_a_save_is_drawn(self):
        watch.seed(self.design, "s-curve")
        ok, message = watch.rebuild(self.design, self.out, cli.render, width=6.0)
        self.assertTrue(ok, message)
        self.assertIn("cubics", message)
        self.assertTrue(os.path.exists(self.out))
        self.assertFalse(os.path.exists(self.out + ".tmp"), "the temp file must be renamed away")

    def test_a_broken_design_leaves_the_last_drawing_alone(self):
        watch.seed(self.design, "s-curve")
        watch.rebuild(self.design, self.out, cli.render, width=6.0)
        good = open(self.out, "rb").read()

        with open(self.design, "w", encoding="utf-8") as fh:
            fh.write('{"segments": [{"kd": 0.00')          # mid-typing
        ok, message = watch.rebuild(self.design, self.out, cli.render, width=6.0)
        self.assertFalse(ok)
        self.assertIn("JSON", message)
        self.assertEqual(open(self.out, "rb").read(), good)

    def test_a_design_that_cannot_build_leaves_the_drawing_alone(self):
        watch.seed(self.design, "s-curve")
        watch.rebuild(self.design, self.out, cli.render, width=6.0)
        good = open(self.out, "rb").read()

        data = json.loads(open(self.design, encoding="utf-8").read())
        data["segments"][0]["length"] = 0.0                # refused by the model
        with open(self.design, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        ok, message = watch.rebuild(self.design, self.out, cli.render, width=6.0)
        self.assertFalse(ok)
        self.assertIn("length", message)
        self.assertEqual(open(self.out, "rb").read(), good)

    def test_a_change_stamp_moves_with_the_file(self):
        watch.seed(self.design, "ogee")
        first = watch._stamp(self.design)
        with open(self.design, "a", encoding="utf-8") as fh:
            fh.write("\n")
        self.assertNotEqual(first, watch._stamp(self.design))
        self.assertEqual(watch._stamp(os.path.join(self.dir.name, "absent")), (0, 0))


if __name__ == "__main__":
    unittest.main()

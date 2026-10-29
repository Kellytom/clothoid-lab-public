import math
import unittest

from clothoid_lab import presets
from web.server import render_payload


class TestWebRender(unittest.TestCase):
    def test_render_preset(self):
        body = render_payload({
            "design": presets.ogee().to_dict(),
            "width": 10,
            "page": [200, 250],
        })
        self.assertTrue(body["svg"].startswith("<?xml") or body["svg"].startswith("<svg"))
        self.assertEqual(body["info"]["chain"]["segments"], 3)
        self.assertTrue(body["info"]["rails"])
        self.assertTrue(math.isfinite(body["elapsed_ms"]))
        self.assertIn("verdict", body["report"])

    def test_render_centerline_only(self):
        body = render_payload({
            "design": presets.s_curve().to_dict(),
            "width": None,
            "page": [200, 250],
        })
        self.assertEqual(body["info"]["rails"], [])

    def test_rejects_malformed_design(self):
        with self.assertRaises(ValueError):
            render_payload({"design": {"segments": [{"kd": 0.001}]}})

    def test_rejects_bad_page(self):
        with self.assertRaises(ValueError):
            render_payload({
                "design": presets.ogee().to_dict(),
                "page": [200, -1],
            })


if __name__ == "__main__":
    unittest.main()

import base64
import unittest

from web.server import RateLimiter, authorized, parse_basic


def basic(user: str, password: str) -> str:
    raw = base64.b64encode(f"{user}:{password}".encode("utf-8")).decode("ascii")
    return f"Basic {raw}"


class TestAuth(unittest.TestCase):
    def test_open_when_no_token(self):
        self.assertTrue(authorized(None, ""))

    def test_token_as_password(self):
        self.assertTrue(authorized(basic("clothoid", "s3cret"), "s3cret"))

    def test_token_as_user(self):
        self.assertTrue(authorized(basic("s3cret", "anything"), "s3cret"))

    def test_wrong_token(self):
        self.assertFalse(authorized(basic("clothoid", "nope"), "s3cret"))

    def test_missing_or_malformed_header(self):
        self.assertFalse(authorized(None, "s3cret"))
        self.assertFalse(authorized("Bearer abc", "s3cret"))
        self.assertFalse(authorized("Basic !!!", "s3cret"))
        self.assertFalse(authorized("Basic " + base64.b64encode(b"no-colon").decode(), "s3cret"))

    def test_parse_basic(self):
        self.assertEqual(parse_basic(basic("a", "b")), ("a", "b"))
        self.assertIsNone(parse_basic(""))
        self.assertIsNone(parse_basic("Basic"))


class TestRateLimiter(unittest.TestCase):
    def test_burst_then_refill(self):
        now = [0.0]
        limiter = RateLimiter(per_min=60, burst=2, clock=lambda: now[0])
        self.assertTrue(limiter.allow("ip"))
        self.assertTrue(limiter.allow("ip"))
        self.assertFalse(limiter.allow("ip"))
        now[0] = 1.0
        self.assertTrue(limiter.allow("ip"))
        self.assertFalse(limiter.allow("ip"))

    def test_separate_keys(self):
        limiter = RateLimiter(per_min=60, burst=1, clock=lambda: 0.0)
        self.assertTrue(limiter.allow("a"))
        self.assertFalse(limiter.allow("a"))
        self.assertTrue(limiter.allow("b"))

    def test_zero_rate_is_unlimited(self):
        limiter = RateLimiter(per_min=0, burst=1, clock=lambda: 0.0)
        for _ in range(10):
            self.assertTrue(limiter.allow("ip"))


if __name__ == "__main__":
    unittest.main()

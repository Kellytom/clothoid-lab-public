"""A zero-dependency web MVP for clothoid-lab.

Serves a small HTML/JS page and one JSON render endpoint:

    POST /api/render   {design, width, page, tol, split} -> {svg, report, info}

Run from the repository root after building the native library:

    .venv/bin/python web/server.py
    open http://127.0.0.1:8000/
"""

from __future__ import annotations

import base64
import hmac
import json
import math
import mimetypes
import os
import re
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
STATIC = Path(__file__).resolve().parent / "static"
CAPS = ROOT / "out" / "caps"
sys.path.insert(0, str(ROOT))

from clothoid_lab import cli, presets  # noqa: E402
from clothoid_lab.model import Design  # noqa: E402


def _safe(value):
    """JSON cannot carry inf or nan; report them as null."""
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {k: _safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe(v) for v in value]
    return value


def render_payload(payload: dict) -> dict:
    """Validate one request and render it. Raises ValueError on bad input."""
    if not isinstance(payload, dict):
        raise ValueError("the request must be a JSON object")
    data = payload.get("design")
    if not isinstance(data, dict):
        raise ValueError("design must be an object")
    try:
        design = Design.from_dict(data)
    except (KeyError, TypeError) as exc:
        raise ValueError(f"design is malformed: {exc}") from exc
    if not 1 <= len(design.segments) <= 200:
        raise ValueError("design must have between 1 and 200 segments")

    width = payload.get("width", None)
    if width is not None:
        width = float(width)
        if not 0 < width <= 100:
            raise ValueError("width must be greater than 0 and at most 100")
    page = payload.get("page", [200, 250])
    if page is not None:
        if not isinstance(page, (list, tuple)) or len(page) != 2:
            raise ValueError("page must be [width, height] in mm")
        page = (float(page[0]), float(page[1]))
        if page[0] <= 0 or page[1] <= 0:
            raise ValueError("page sides must be positive")
    tol = float(payload.get("tol", 0.02))
    if not 0 < tol <= 1:
        raise ValueError("tol must be in (0, 1]")
    split = int(payload.get("split", 2))
    if not 2 <= split <= 8:
        raise ValueError("split must be between 2 and 8")

    started = time.perf_counter()
    text, info = cli.render(design, width=width, page=page, tol=tol, split=split)
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    return {
        "svg": text,
        "report": cli.format_report(info, tol),
        "info": _safe(info),
        "design": design.to_dict(),
        "elapsed_ms": elapsed_ms,
    }


CAP_NAME = re.compile(r"^cap-(?:pt-)?\d+$")


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


# A shared token gates every route except /healthz. Empty means open, which is
# the local default; the public deployment always sets it.
AUTH_TOKEN = os.environ.get("CLOTHOID_TOKEN", "").strip()
RATE_PER_MIN = _env_float("CLOTHOID_RATE_PER_MIN", 60.0)
RATE_BURST = _env_float("CLOTHOID_RATE_BURST", 20.0)


def parse_basic(header: str | None) -> tuple[str, str] | None:
    """Return (user, password) from a Basic header, or None."""
    if not header:
        return None
    scheme, _, value = header.partition(" ")
    if scheme.lower() != "basic" or not value:
        return None
    try:
        raw = base64.b64decode(value.strip(), validate=True).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return None
    user, sep, password = raw.partition(":")
    if not sep:
        return None
    return user, password


def authorized(header: str | None, token: str) -> bool:
    """True when the request may proceed. No token means local/open mode."""
    if not token:
        return True
    credentials = parse_basic(header)
    if credentials is None:
        return False
    user, password = credentials
    # Accept the token in either field so a person can type it as the username
    # in a client that handles passwords awkwardly.
    return hmac.compare_digest(password, token) or hmac.compare_digest(user, token)


def client_ip(handler) -> str:
    forwarded = handler.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return handler.client_address[0]


class RateLimiter:
    """A small token bucket per key. In-process is enough for one Cloud Run instance."""

    def __init__(self, per_min: float, burst: float, clock=time.monotonic):
        self.rate = max(per_min, 0.0) / 60.0
        self.burst = max(burst, 1.0)
        self.clock = clock
        self._buckets: dict[str, tuple[float, float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        if self.rate <= 0:
            return True
        now = self.clock()
        with self._lock:
            tokens, last = self._buckets.get(key, (self.burst, now))
            tokens = min(self.burst, tokens + (now - last) * self.rate)
            if tokens < 1.0:
                self._buckets[key] = (tokens, now)
                return False
            self._buckets[key] = (tokens - 1.0, now)
            if len(self._buckets) > 4096:
                self._buckets = {
                    k: v for k, v in self._buckets.items() if now - v[1] < 300.0
                }
            return True


LIMITER = RateLimiter(RATE_PER_MIN, RATE_BURST)


def cap_names() -> list[str]:
    if not CAPS.exists():
        return []
    names = []
    for path in CAPS.glob("cap-*.json"):
        if CAP_NAME.match(path.stem):
            names.append(path.stem)
    return sorted(names, key=lambda n: (n.startswith("cap-pt"), n))


def cap_design(name: str) -> dict:
    if not CAP_NAME.match(name):
        raise ValueError("not a known cap name")
    path = CAPS / f"{name}.json"
    if not path.exists():
        raise ValueError("no such cap")
    return Design.load(path).to_dict()


class Handler(BaseHTTPRequestHandler):
    server_version = "clothoid-lab-web/0.1"

    def log_message(self, fmt, *args):
        sys.stderr.write(f"{self.address_string()} {fmt % args}\n")

    def _json(self, status: int, payload: dict):
        body = json.dumps(payload, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self) -> bool:
        return authorized(self.headers.get("Authorization"), AUTH_TOKEN)

    def _unauthorized(self):
        body = b"authentication required\n"
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="clothoid-lab"')
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _rate_limited(self) -> bool:
        if LIMITER.allow(client_ip(self)):
            return False
        body = json.dumps(
            {"error": "rate limit exceeded; try again shortly"}
        ).encode("utf-8")
        self.send_response(429)
        self.send_header("Retry-After", "5")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        return True

    def _file(self, name: str):
        path = (STATIC / name).resolve()
        if STATIC.resolve() not in path.parents or not path.is_file():
            self.send_error(404)
            return
        body = path.read_bytes()
        ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        query = parse_qs(url.query)
        if url.path == "/health":
            self._json(200, {"ok": True})
            return
        if not self._authorized():
            self._unauthorized()
            return
        try:
            if url.path in ("/", "/index.html"):
                self._file("index.html")
            elif url.path in ("/app.js", "/style.css"):
                self._file(url.path.lstrip("/"))
            elif url.path == "/api/presets":
                self._json(200, {"presets": sorted(presets.PRESETS)})
            elif url.path == "/api/preset":
                name = (query.get("name") or [""])[0]
                if name not in presets.PRESETS:
                    raise ValueError("no such preset")
                self._json(200, {"design": presets.get(name).to_dict()})
            elif url.path == "/api/caps":
                self._json(200, {"caps": cap_names()})
            elif url.path == "/api/cap":
                name = (query.get("name") or [""])[0]
                self._json(200, {"design": cap_design(name)})
            else:
                self.send_error(404)
        except ValueError as exc:
            self._json(400, {"error": str(exc)})
        except Exception as exc:  # noqa: BLE001
            self._json(500, {"error": str(exc)})

    def do_POST(self):
        url = urlparse(self.path)
        if not self._authorized():
            self._unauthorized()
            return
        if url.path != "/api/render":
            self.send_error(404)
            return
        if self._rate_limited():
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0 or length > 1_000_000:
            self._json(413, {"error": "request body must be under 1 MB"})
            return
        try:
            payload = json.loads(self.rfile.read(length))
            self._json(200, render_payload(payload))
        except ValueError as exc:
            self._json(400, {"error": str(exc)})
        except json.JSONDecodeError as exc:
            self._json(400, {"error": f"bad JSON: {exc}"})
        except Exception as exc:  # noqa: BLE001
            self._json(500, {"error": str(exc)})


def main() -> int:
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"clothoid-lab web: http://{host}:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

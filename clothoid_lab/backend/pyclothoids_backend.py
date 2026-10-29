"""The pyclothoids wheel, kept as a second opinion on the wrapper.

It carries the same Clothoids source, so it cannot confirm the mathematics;
it confirms that the ctypes surface returns the same numbers as a binding
someone else wrote. That is the failure this project can actually have: a wrong
argument order, a mangled signature, a handle freed twice.

Its offset is computed here, by stepping along the normal, because the wheel
does not expose X_ISO. Rails therefore differ slightly between backends, which
is itself worth a test.
"""

from __future__ import annotations

import math

NAME = "pyclothoids"


def probe() -> str:
    try:
        import pyclothoids  # noqa: F401

        return "ok: pyclothoids wheel"
    except Exception as exc:
        return str(exc)


def load():
    import pyclothoids

    return pyclothoids


class Curve:
    """The same chain interface, built from one Clothoid object per segment."""

    __slots__ = ("placed", "_len", "segments")

    def __init__(self, segments, anchor):
        import pyclothoids as pc

        x = float(anchor.get("x", 0.0))
        y = float(anchor.get("y", 0.0))
        t = float(anchor.get("angle", 0.0))
        placed = []
        for i, seg in enumerate(segments):
            if i > 0 and seg.get("corner"):
                t += float(seg["corner"])
            cloth = pc.Clothoid.StandardParams(x, y, t, seg["k0"], seg["kd"], seg["length"])
            placed.append({
                "clothoid": cloth,
                "x0": x, "y0": y, "t0": t,
                "k0": seg["k0"], "kd": seg["kd"], "length": seg["length"],
            })
            x, y = cloth.X(seg["length"]), cloth.Y(seg["length"])
            t = self._theta(placed[-1], seg["length"])
        self.placed = placed
        self.segments = segments
        self._len = sum(p["length"] for p in placed)

    @staticmethod
    def _theta(placed, s):
        return placed["t0"] + placed["k0"] * s + 0.5 * placed["kd"] * s * s

    @property
    def length(self):
        return self._len

    def _locate(self, s):
        s = min(max(float(s), 0.0), self._len)
        base = 0.0
        for p in self.placed:
            if s <= base + p["length"] + 1e-12:
                return p, min(s - base, p["length"])
            base += p["length"]
        p = self.placed[-1]
        return p, p["length"]

    def point(self, s):
        p, u = self._locate(s)
        return (p["clothoid"].X(u), p["clothoid"].Y(u))

    def tangent(self, s):
        p, u = self._locate(s)
        return self._theta(p, u)

    def kappa(self, s):
        p, u = self._locate(s)
        return p["k0"] + p["kd"] * u

    def offset_point(self, s, distance):
        x, y = self.point(s)
        a = self.tangent(s)
        return (x - distance * math.sin(a), y + distance * math.cos(a))

    def bounds(self):
        n = max(64, 64 * len(self.placed))
        xs, ys = [], []
        for i in range(n + 1):
            x, y = self.point(self._len * i / n)
            xs.append(x)
            ys.append(y)
        return (min(xs), min(ys), max(xs), max(ys))

    def close(self):
        return None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return None


def build_curve(segments, anchor):
    return Curve(segments, anchor)


def describe() -> str:
    return f"{NAME} (wheel)"

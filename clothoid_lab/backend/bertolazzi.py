"""The compiled Clothoids library through ctypes.

The dylib is built by `scripts/build-native.sh` from `vendor/Clothoids`. This
module is the only place that knows the C names, the argument types, or the
error codes, and it converts every call into either a value or a Python
exception. Nothing above it sees ctypes.

Positions, angles and curvature come from the library itself, so this backend
can offer the exact parallel curve (`X_ISO`, `Y_ISO`) rather than offsetting a
sample by a rotated tangent.
"""

from __future__ import annotations

import ctypes
import os
from pathlib import Path

import math
import sys

NAME = "bertolazzi"
_ROOT = Path(__file__).resolve().parents[2]
_SUFFIX = ".dylib" if sys.platform == "darwin" else ".so"
LIB_PATH = Path(os.environ.get("CLOTHOID_LIB", _ROOT / "build" / f"libclothoidlab{_SUFFIX}"))

_lib = None


class BackendError(RuntimeError):
    pass


def _bind():
    """Load the library and declare every signature once."""
    global _lib
    if _lib is not None:
        return _lib
    if not LIB_PATH.exists():
        raise BackendError(
            f"{LIB_PATH} is missing; run scripts/build-native.sh, or set "
            "CLOTHOID_BACKEND=pyclothoids to use the wheel"
        )
    lib = ctypes.CDLL(str(LIB_PATH))

    lib.cl_version.restype = ctypes.c_char_p
    lib.cl_new.restype = ctypes.c_void_p
    lib.cl_free.argtypes = [ctypes.c_void_p]

    lib.cl_push.argtypes = [ctypes.c_void_p] + [ctypes.c_double] * 3
    lib.cl_push.restype = ctypes.c_int
    lib.cl_push_at.argtypes = [ctypes.c_void_p] + [ctypes.c_double] * 6
    lib.cl_push_at.restype = ctypes.c_int
    lib.cl_push_G1.argtypes = [ctypes.c_void_p] + [ctypes.c_double] * 3
    lib.cl_push_G1.restype = ctypes.c_int

    lib.cl_g1_fit.argtypes = [ctypes.c_double] * 6 + [ctypes.c_double,
                                                     ctypes.POINTER(ctypes.c_double)]
    lib.cl_g1_fit.restype = ctypes.c_int
    lib.cl_build_g1.argtypes = [ctypes.c_void_p, ctypes.c_int,
                                ctypes.POINTER(ctypes.c_double),
                                ctypes.POINTER(ctypes.c_double),
                                ctypes.POINTER(ctypes.c_double)]
    lib.cl_build_g1.restype = ctypes.c_int
    lib.cl_segment.argtypes = [ctypes.c_void_p, ctypes.c_int,
                               ctypes.POINTER(ctypes.c_double)]
    lib.cl_segment.restype = ctypes.c_int

    lib.cl_build_g2.argtypes = [ctypes.c_void_p, ctypes.c_int,
                                ctypes.POINTER(ctypes.c_double),
                                ctypes.POINTER(ctypes.c_double)] + [ctypes.c_double] * 4
    lib.cl_build_g2.restype = ctypes.c_int
    lib.cl_build_g2_cyclic.argtypes = [ctypes.c_void_p, ctypes.c_int,
                                       ctypes.POINTER(ctypes.c_double),
                                       ctypes.POINTER(ctypes.c_double)]
    lib.cl_build_g2_cyclic.restype = ctypes.c_int
    lib.cl_smooth_g2.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_double,
                                 ctypes.POINTER(ctypes.c_double)]
    lib.cl_smooth_g2.restype = ctypes.c_int
    lib.cl_trim.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double]
    lib.cl_trim.restype = ctypes.c_int
    lib.cl_reverse.argtypes = [ctypes.c_void_p]
    lib.cl_reverse.restype = ctypes.c_int
    lib.cl_g2_connect.argtypes = [ctypes.c_void_p, ctypes.c_int,
                                  ctypes.POINTER(ctypes.c_double)]
    lib.cl_g2_connect.restype = ctypes.c_int
    lib.cl_project.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double,
                               ctypes.POINTER(ctypes.c_double)]
    lib.cl_project.restype = ctypes.c_int
    lib.cl_project_iso.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double,
                                   ctypes.c_double, ctypes.POINTER(ctypes.c_double)]
    lib.cl_project_iso.restype = ctypes.c_int
    lib.cl_intersect.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_double,
                                 ctypes.c_double, ctypes.POINTER(ctypes.c_double),
                                 ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
    lib.cl_intersect.restype = ctypes.c_int
    lib.cl_length_iso.argtypes = [ctypes.c_void_p, ctypes.c_double]
    lib.cl_length_iso.restype = ctypes.c_double
    lib.cl_bbox_iso.argtypes = [ctypes.c_void_p, ctypes.c_double,
                                ctypes.POINTER(ctypes.c_double)]
    lib.cl_bbox_iso.restype = ctypes.c_int
    lib.cl_closure_gap.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_double)]
    lib.cl_closure_gap.restype = ctypes.c_int

    lib.cl_length.argtypes = [ctypes.c_void_p]
    lib.cl_length.restype = ctypes.c_double
    lib.cl_nseg.argtypes = [ctypes.c_void_p]
    lib.cl_nseg.restype = ctypes.c_int

    lib.cl_eval.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.POINTER(ctypes.c_double)]
    lib.cl_eval.restype = ctypes.c_int
    lib.cl_eval_offset.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double,
                                   ctypes.POINTER(ctypes.c_double)]
    lib.cl_eval_offset.restype = ctypes.c_int
    lib.cl_bbox.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_double)]
    lib.cl_bbox.restype = ctypes.c_int

    _lib = lib
    return lib


def probe() -> str:
    """Whether this backend can load, as a short sentence either way."""
    try:
        lib = _bind()
        return f"ok: {lib.cl_version().decode()}"
    except Exception as exc:
        return str(exc)


def load():
    return _bind()


_FOUR = ctypes.c_double * 4


def _make_handle(lib, segments, anchor) -> int:
    """A ClothoidList from resolved segments, anchored in the plane."""
    handle = lib.cl_new()
    if not handle:
        raise BackendError("the library could not allocate a chain")
    x = float(anchor.get("x", 0.0))
    y = float(anchor.get("y", 0.0))
    t = float(anchor.get("angle", 0.0))
    try:
        for i, seg in enumerate(segments):
            if i == 0:
                rc = lib.cl_push_at(handle, x, y, t, seg["k0"], seg["kd"], seg["length"])
            elif seg.get("corner"):
                end = _FOUR()
                rc = lib.cl_eval(handle, lib.cl_length(handle), end)
                if rc != 0:
                    raise BackendError(f"could not read the join before segment {i} (code {rc})")
                rc = lib.cl_push_at(handle, end[0], end[1],
                                    end[2] + seg["corner"],
                                    seg["k0"], seg["kd"], seg["length"])
            else:
                rc = lib.cl_push(handle, seg["k0"], seg["kd"], seg["length"])
            if rc != 0:
                raise BackendError(f"the library refused segment {i} (code {rc})")
        return handle
    except Exception:
        lib.cl_free(handle)
        raise


def _read_segments(lib, handle) -> list[dict]:
    """Read every piece back as start point, direction, curvature, rate, length."""
    out = []
    for i in range(int(lib.cl_nseg(handle))):
        seg = (ctypes.c_double * 6)()
        rc = lib.cl_segment(handle, i, seg)
        if rc != 0:
            raise BackendError(f"could not read segment {i} ({_reason(rc)})")
        out.append({
            "x0": seg[0], "y0": seg[1], "theta0": seg[2],
            "kappa0": seg[3], "kd": seg[4], "length": seg[5],
        })
    return out


class Curve:
    """One chain, held as a ClothoidList, addressed by arc length."""

    __slots__ = ("_h", "_len", "segments")

    def __init__(self, segments, anchor):
        lib = _bind()
        self._h = _make_handle(lib, segments, anchor)
        self.segments = segments
        self._len = float(lib.cl_length(self._h))

    def close(self):
        if getattr(self, "_h", None):
            _bind().cl_free(self._h)
            self._h = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    @property
    def length(self):
        return self._len

    def _eval(self, s):
        out = _FOUR()
        rc = _bind().cl_eval(self._h, float(s), out)
        if rc != 0:
            raise BackendError(f"eval failed at s={s} (code {rc})")
        return out[0], out[1], out[2], out[3]

    def point(self, s):
        x, y, _, _ = self._eval(s)
        return (x, y)

    def tangent(self, s):
        return self._eval(s)[2]

    def kappa(self, s):
        return self._eval(s)[3]

    def offset_point(self, s, distance):
        out = (ctypes.c_double * 2)()
        rc = _bind().cl_eval_offset(self._h, float(s), float(distance), out)
        if rc != 0:
            raise BackendError(f"offset eval failed at s={s} (code {rc})")
        return (out[0], out[1])

    def bounds(self):
        out = _FOUR()
        rc = _bind().cl_bbox(self._h, out)
        if rc != 0:
            raise BackendError(f"bounds failed (code {rc})")
        return (out[0], out[1], out[2], out[3])

    def project(self, x, y, offset=None):
        """Closest point on the chain (or its offset): s, t, point, distance."""
        out = (ctypes.c_double * 5)()
        lib = _bind()
        if offset is None:
            rc = lib.cl_project(self._h, float(x), float(y), out)
        else:
            rc = lib.cl_project_iso(self._h, float(x), float(y), float(offset), out)
        if rc != 0:
            raise BackendError(f"projection failed ({_reason(rc)})")
        return {"s": out[0], "t": out[1], "x": out[2], "y": out[3],
                "distance": out[4]}

    def length_iso(self, distance):
        return float(_bind().cl_length_iso(self._h, float(distance)))

    def bbox_iso(self, distance):
        out = _FOUR()
        rc = _bind().cl_bbox_iso(self._h, float(distance), out)
        if rc != 0:
            raise BackendError(f"offset bounds failed ({_reason(rc)})")
        return (out[0], out[1], out[2], out[3])

    def closure_gap(self):
        out = _FOUR()
        rc = _bind().cl_closure_gap(self._h, out)
        if rc != 0:
            raise BackendError(f"closure check failed ({_reason(rc)})")
        return (out[0], out[1], out[2], out[3])

    def intersections(self, other, iso_self=0.0, iso_other=0.0, max_hits=256):
        """Crossings between two chains, as (s on self, s on other) pairs."""
        out = (ctypes.c_double * (2 * max_hits))()
        count = ctypes.c_int(0)
        rc = _bind().cl_intersect(self._h, other._h, float(iso_self),
                                  float(iso_other), out, max_hits,
                                  ctypes.byref(count))
        if rc not in (0, 6):
            raise BackendError(f"intersection failed ({_reason(rc)})")
        return [(out[2 * i], out[2 * i + 1]) for i in range(count.value)]


def build_curve(segments, anchor):
    return Curve(segments, anchor)


def g1_fit(p0, t0, p1, t1, tol: float = 1e-12) -> tuple[float, float, float]:
    """The two-point G1 problem: starting curvature, rate and length.

    This is Bertolazzi and Frego's `buildClothoid`: one clothoid that passes
    through both points with the prescribed directions.
    """
    out = (ctypes.c_double * 3)()
    rc = _bind().cl_g1_fit(float(p0[0]), float(p0[1]), float(t0),
                           float(p1[0]), float(p1[1]), float(t1), float(tol), out)
    if rc != 0:
        raise BackendError(f"the G1 fit failed ({_reason(rc)})")
    return out[0], out[1], out[2]


def g1_spline(points, thetas=None) -> list[dict]:
    """A chain of clothoids through the points, G1 at every join.

    Directions are estimated when `thetas` is None, and honoured as given
    otherwise. Each returned segment carries its own start point, direction,
    curvature, curvature rate and length, so it can be fed straight into the
    design model.
    """
    points = [(float(x), float(y)) for x, y in points]
    if len(points) < 2:
        raise BackendError("a G1 spline needs at least two points")
    if thetas is not None and len(thetas) != len(points):
        raise BackendError("give one direction per point, or none at all")

    lib = _bind()
    n = len(points)
    xs = (ctypes.c_double * n)(*[p[0] for p in points])
    ys = (ctypes.c_double * n)(*[p[1] for p in points])
    ts = None if thetas is None else (ctypes.c_double * n)(*[float(t) for t in thetas])

    handle = lib.cl_new()
    if not handle:
        raise BackendError("the library could not allocate a chain")
    try:
        rc = lib.cl_build_g1(handle, n, xs, ys, ts)
        if rc != 0:
            raise BackendError(f"the G1 spline failed ({_reason(rc)})")
        return _read_segments(lib, handle)
    finally:
        lib.cl_free(handle)


def g2_spline(points, theta0=None, kappa0=0.0, theta1=None, kappa1=0.0) -> list[dict]:
    """A G2 spline through the points, with end tangent and curvature.

    The end directions default to the first and last chord; the end curvatures
    default to zero, which is what a road or a ribbon wants.
    """
    points = [(float(x), float(y)) for x, y in points]
    if len(points) < 2:
        raise BackendError("a G2 spline needs at least two points")
    if theta0 is None:
        theta0 = math.atan2(points[1][1] - points[0][1],
                            points[1][0] - points[0][0])
    if theta1 is None:
        theta1 = math.atan2(points[-1][1] - points[-2][1],
                            points[-1][0] - points[-2][0])

    lib = _bind()
    n = len(points)
    xs = (ctypes.c_double * n)(*[p[0] for p in points])
    ys = (ctypes.c_double * n)(*[p[1] for p in points])
    handle = lib.cl_new()
    if not handle:
        raise BackendError("the library could not allocate a chain")
    try:
        rc = lib.cl_build_g2(handle, n, xs, ys, float(theta0), float(kappa0),
                             float(theta1), float(kappa1))
        if rc != 0:
            raise BackendError(f"the G2 spline failed ({_reason(rc)})")
        return _read_segments(lib, handle)
    finally:
        lib.cl_free(handle)


def g2_cyclic(points) -> list[dict]:
    """A closed G2 spline through the points.

    The vendor routine expects the closing point to be given explicitly, so the
    first point is repeated when it is not already there.
    """
    points = [(float(x), float(y)) for x, y in points]
    if len(points) < 3:
        raise BackendError("a closed G2 spline needs at least three points")
    if math.dist(points[0], points[-1]) > 1e-12:
        points = points + [points[0]]
    lib = _bind()
    n = len(points)
    xs = (ctypes.c_double * n)(*[p[0] for p in points])
    ys = (ctypes.c_double * n)(*[p[1] for p in points])
    handle = lib.cl_new()
    if not handle:
        raise BackendError("the library could not allocate a chain")
    try:
        rc = lib.cl_build_g2_cyclic(handle, n, xs, ys)
        if rc != 0:
            raise BackendError(f"the closed G2 spline failed ({_reason(rc)})")
        return _read_segments(lib, handle)
    finally:
        lib.cl_free(handle)


def _transform(segments, anchor, action):
    """Build a chain, mutate it, and read the pieces back."""
    lib = _bind()
    handle = _make_handle(lib, segments, anchor)
    try:
        rc = action(lib, handle)
        if rc != 0:
            raise BackendError(f"the library refused the transform ({_reason(rc)})")
        return _read_segments(lib, handle)
    finally:
        lib.cl_free(handle)


def trim_segments(segments, anchor, s0, s1) -> list[dict]:
    return _transform(segments, anchor,
                      lambda lib, h: lib.cl_trim(h, float(s0), float(s1)))


def reverse_segments(segments, anchor) -> list[dict]:
    return _transform(segments, anchor, lambda lib, h: lib.cl_reverse(h))


def smooth_segments(segments, anchor, max_iter=100, epsi=1e-6):
    """Reduce curvature jumps; returns (pieces, largest remaining jump)."""
    lib = _bind()
    handle = _make_handle(lib, segments, anchor)
    jump = ctypes.c_double(0.0)
    try:
        rc = lib.cl_smooth_g2(handle, int(max_iter), float(epsi),
                              ctypes.byref(jump))
        # A residual jump above epsi is a result, not a failure: the pieces are
        # still a valid quasi-G2 chain and the caller reports the jump.
        if rc not in (0, 5):
            raise BackendError(f"the smoothing failed ({_reason(rc)})")
        return _read_segments(lib, handle), float(jump.value)
    finally:
        lib.cl_free(handle)


def connect_segments(pose0, pose1, method="3arc") -> list[dict]:
    """A G2 connector between two end states (x, y, theta, kappa)."""
    codes = {"clc": 0, "2arc": 2, "3arc": 3}
    if method not in codes:
        raise BackendError(f"no connector {method!r}; use clc, 2arc or 3arc")
    if len(pose0) != 4 or len(pose1) != 4:
        raise BackendError("a pose is (x, y, theta, kappa)")
    values = (ctypes.c_double * 8)(*[float(v) for v in pose0],
                                   *[float(v) for v in pose1])
    lib = _bind()
    handle = lib.cl_new()
    if not handle:
        raise BackendError("the library could not allocate a chain")
    try:
        rc = lib.cl_g2_connect(handle, codes[method], values)
        if rc != 0:
            raise BackendError(f"the G2 connector failed ({_reason(rc)})")
        return _read_segments(lib, handle)
    finally:
        lib.cl_free(handle)


def _reason(code: int) -> str:
    return {
        1: "bad argument",
        2: "the library rejected the fit",
        3: "no such segment",
        5: "no solution converged",
    }.get(code, f"code {code}")


def describe() -> str:
    return f"{NAME} ({LIB_PATH.name})"

"""A chain of clothoids through target points, G1 at every join.

This is Bertolazzi and Frego's G1 fitting, the `buildClothoid` problem: given
two points and a direction at each, one clothoid passes through both with those
directions. Chained over a list of points it gives a spline that interpolates
every point, with a shared tangent at each join.

The fit is G1, not G2: curvature is free to jump at a join, and it usually does.
That is the price of passing through points, and the report says so instead of
pretending the chain is smooth in curvature.

The result is an ordinary `Design`: each fitted clothoid becomes a segment with
its curvature written out, so the drawing, the SVG writer, the rails and the
round trip all keep working without a second kind of geometry.
"""

from __future__ import annotations

import json
import math
import os

from . import backend as backends
from .model import Design, Segment


class InterpolationError(ValueError):
    """The points or the directions cannot be fitted."""


def design_from_spans(spans: list[dict], name: str = "from spans") -> Design:
    """One clothoid segment per cubic span, G1 at every join.

    The bridge from recovered drawings and grammar output into our model: each
    cubic contributes its two endpoints and their tangents, which is exactly the
    G1 problem. An `euler`, `arc` or `line` span comes back exact (to floating
    point); a `logaesthetic` or `hyperbezier` span comes back as the closest
    clothoid, which is the honest answer rather than a claim of equality.

    Spans are the dicts the rest of the package uses: `p0`, `c1`, `c2`, `p3`.
    The design is marked `g1`, because curvature is free to jump at the joins.
    """
    if not spans:
        raise InterpolationError("no spans to convert")
    segments = []
    for index, span in enumerate(spans):
        p0, p3 = span["p0"], span["p3"]
        chord = math.dist(p0, p3)
        if chord <= 1e-12:
            raise InterpolationError(f"span {index} has no length")
        c1, c2 = span["c1"], span["c2"]
        t0 = math.atan2(c1[1] - p0[1], c1[0] - p0[0])
        t1 = math.atan2(p3[1] - c2[1], p3[0] - c2[0])
        kappa, kd, length = fit(p0, t0, p3, t1)
        segments.append(Segment(kd=kd, length=length, kappa0=kappa))
    first = spans[0]
    t0 = math.atan2(first["c1"][1] - first["p0"][1],
                    first["c1"][0] - first["p0"][0])
    return Design(
        name=name,
        anchor={"x": first["p0"][0], "y": first["p0"][1], "angle": t0},
        segments=segments,
        g1=True,
    )


def fit(p0, theta0, p1, theta1, tol: float = 1e-12, backend: str | None = None):
    """One clothoid through two points with prescribed directions.

    Returns `(kappa0, kd, length)`, the same three numbers a segment needs.
    """
    module = _backend(backend)
    x0, y0 = _point(p0, 0)
    x1, y1 = _point(p1, 1)
    if (x0, y0) == (x1, y1):
        raise InterpolationError("the two points are the same")
    k, dk, length = module.g1_fit((x0, y0), theta0, (x1, y1), theta1, tol=tol)
    if not (math.isfinite(k) and math.isfinite(dk) and length > 0):
        raise InterpolationError("the G1 fit returned a non-finite clothoid")
    return k, dk, length


def from_points(points, thetas=None, name: str | None = None,
                stroke: float = 1.0, backend: str | None = None,
                method: str = "g1", cyclic: bool = False,
                theta0=None, kappa0: float = 0.0,
                theta1=None, kappa1: float = 0.0) -> Design:
    """Fit a spline through `points` and return it as a design.

    `method="g1"` (default) is Bertolazzi and Frego's two-point fit chained with
    estimated or supplied directions; curvature jumps at the points. `"g2"`
    interpolates with continuous curvature, using the end tangent and curvature
    given (the tangents default to the first and last chord, the curvatures to
    zero). `cyclic=True` closes the curve, repeating the first point for G1.
    """
    if method not in ("g1", "g2"):
        raise InterpolationError(f"no spline method {method!r}; use g1 or g2")
    pts = _points(points)
    angles = _thetas(thetas, len(pts))
    module = _backend(backend)

    if method == "g1":
        if cyclic and pts[0] != pts[-1]:
            pts = pts + [pts[0]]
            if angles is not None:
                angles = angles + [angles[0]]
        pieces = module.g1_spline(pts, angles)
        flag = True
    else:
        if angles is not None:
            raise InterpolationError("a G2 spline takes end directions, not one per point")
        pieces = (module.g2_cyclic(pts) if cyclic
                  else module.g2_spline(pts, theta0=theta0, kappa0=kappa0,
                                        theta1=theta1, kappa1=kappa1))
        flag = False

    if not pieces:
        raise InterpolationError("the spline came back empty")
    return Design.from_pieces(
        pieces,
        name=name or f"spline {len(points)} points",
        stroke=float(stroke),
        g1=flag,
    )


def smooth(design: Design, iterations: int = 100, epsi: float = 1e-9,
           backend: str | None = None) -> Design:
    """Move the shared tangents to reduce curvature jumps, keeping the ends.

    The result is quasi-G2: the residual jump is small, not zero, so the design
    keeps the `g1` flag and the report prints the jump instead of failing.
    """
    from . import engine

    module = _backend(backend)
    chain = engine.build(design, backend=backend)
    pieces = [{"k0": p.k0, "kd": p.kd, "length": p.length} for p in chain.segments]
    smoothed, _jump = module.smooth_segments(pieces, dict(design.anchor),
                                             max_iter=iterations, epsi=epsi)
    return Design.from_pieces(
        smoothed,
        name=f"{design.name} smoothed",
        stroke=design.stroke,
        g1=True,
    )


def parse(text: str) -> dict:
    """Read points from JSON, or from plain `x, y` lines, with directions optional.

    JSON may be a bare list of pairs, or an object with `points`, `thetas` and
    `name`. The plain form is one point per line, commas or spaces, `#` comments.
    """
    stripped = text.strip()
    if stripped.startswith(("[", "{")):
        data = json.loads(stripped)
        if isinstance(data, dict):
            method = data.get("method") or ("g2" if data.get("g2") else "g1")
            return {
                "points": data.get("points", []),
                "thetas": data.get("thetas"),
                "name": data.get("name"),
                "method": str(method),
                "cyclic": bool(data.get("cyclic", False)),
                "theta0": data.get("theta0"),
                "kappa0": float(data.get("kappa0", 0.0)),
                "theta1": data.get("theta1"),
                "kappa1": float(data.get("kappa1", 0.0)),
            }
        return {"points": data, "thetas": None, "name": None,
                "method": "g1", "cyclic": False,
                "theta0": None, "kappa0": 0.0, "theta1": None, "kappa1": 0.0}

    points = []
    for number, line in enumerate(stripped.splitlines(), start=1):
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.replace(",", " ").split()
        if len(parts) != 2:
            raise InterpolationError(
                f"line {number} is not a point: {line!r}; write 'x, y'")
        try:
            points.append((float(parts[0]), float(parts[1])))
        except ValueError:
            raise InterpolationError(f"line {number} is not numeric: {line!r}") from None
    return {"points": points, "thetas": None, "name": None,
            "method": "g1", "cyclic": False,
            "theta0": None, "kappa0": 0.0, "theta1": None, "kappa1": 0.0}


def load(path, method: str | None = None, cyclic: bool | None = None) -> Design:
    """Read a points file and return the fitted design.

    `method` and `cyclic` override what the file says, which is how the command
    line flags win over the file.
    """
    with open(path, "r", encoding="utf-8") as fh:
        data = parse(fh.read())
    name = data["name"] or f"spline {os.path.basename(path)}"
    return from_points(
        data["points"], data["thetas"], name=name,
        method=method or data.get("method", "g1"),
        cyclic=data.get("cyclic", False) if cyclic is None else cyclic,
        theta0=data.get("theta0"), kappa0=data.get("kappa0", 0.0),
        theta1=data.get("theta1"), kappa1=data.get("kappa1", 0.0),
    )


def _backend(name: str | None = None):
    module = backends.load(name)
    if not (hasattr(module, "g1_spline") and hasattr(module, "g1_fit")):
        raise InterpolationError(
            "the G1 fitter is only in the compiled backend; build it with "
            "scripts/build-native.sh or unset CLOTHOID_BACKEND")
    return module


def _point(p, index: int) -> tuple[float, float]:
    try:
        x, y = (float(v) for v in p)
    except (TypeError, ValueError):
        raise InterpolationError(f"point {index} is not a pair of numbers: {p!r}") from None
    if not (math.isfinite(x) and math.isfinite(y)):
        raise InterpolationError(f"point {index} is not finite: {p!r}")
    return x, y


def _points(points) -> list[tuple[float, float]]:
    pts = [_point(p, i) for i, p in enumerate(points)]
    if len(pts) < 2:
        raise InterpolationError("a G1 spline needs at least two points")
    for i in range(1, len(pts)):
        if pts[i] == pts[i - 1]:
            raise InterpolationError(
                f"points {i} and {i + 1} are the same; a clothoid needs distance")
    return pts


def _thetas(thetas, count: int) -> list[float] | None:
    if thetas is None:
        return None
    angles = [float(t) for t in thetas]
    if len(angles) != count:
        raise InterpolationError(
            f"give one direction per point: {len(angles)} directions for {count} points")
    if not all(math.isfinite(t) for t in angles):
        raise InterpolationError("every direction must be finite")
    return angles

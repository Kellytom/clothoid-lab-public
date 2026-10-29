"""Chords to cubics, in the span format the existing writer already takes.

`clothoid_lab.svg.path_d` and `clothoid_lab.piece` speak one span shape:

    {"s0", "s1", "p0", "c1", "c2", "p3"}

so a polygon from this package can be drawn by the existing SVG writer without
a backend, a `Design`, or a `Chain`.  That is the integration seam, and it is
deliberately the *only* one.

The cubic between two nodes uses the parabola rule, which is exact for a
circular arc: the control arm is `chord / (3 cos^2(delta/2))` where `delta` is
the angle between the chord and the end tangent.  A group is closed once its
turns add up to `max_turn`, so no single cubic has to carry a large heading
change -- the "45 to 60 degrees" rule, applied to the fit rather than the curve.
"""

from __future__ import annotations

import math

from .spiral import Spiral


def node_tangents(path: Spiral, sharp: float = math.radians(12.0),
                  apsis: str = "sharp"):
    """Two tangents per node: the one arriving, and the one leaving.

    A node whose turn is under `sharp` is smoothed onto the bisector, so
    consecutive cubics meet G1 and the polygon stops reading like a polygon.
    A node whose turn is bigger keeps both chord directions, so a deliberate
    corner stays a corner.  This is the whole difference between a faceted
    chain and a curve, and it costs one line of arithmetic.
    """
    heads = [h.angle for h in path.headings]
    # one entry per node (chords + 1), not per chord
    arrive = [heads[0]] + list(heads)
    leave = list(heads) + [heads[-1]]
    turns = [path.triangle.radians * t for t in path.turns]
    for k in range(1, len(heads)):
        if abs(turns[k]) > sharp:
            continue
        # A curvature reversal is not a small turn, it is a different thing:
        # smoothing it hands the two spans a tangent that does not lie on
        # their own chords, and a single short chord forced to bow between
        # them overshoots the chain's curvature by 3x. Keep the corner.
        if apsis == "sharp" and 0 < k < len(turns) and turns[k] \
                and turns[k - 1] and (turns[k] > 0) != (turns[k - 1] > 0):
            continue
        a, b = heads[k - 1], heads[k]
        vx, vy = math.cos(a) + math.cos(b), math.sin(a) + math.sin(b)
        if math.hypot(vx, vy) > 1e-12:
            mid = math.atan2(vy, vx)
            arrive[k] = leave[k] = mid
    return leave, arrive


def _cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def arms_for_curvature(p0, p3, t0, t1, k0, k1, iters=60):
    """Two arm lengths that put the cubic's end curvatures on `k0` and `k1`.

    For a cubic with `P1 = P0 + a u` and `P2 = P3 - b v`,

        k(0) = (2/3) (cross(u, D) - b cross(u, v)) / a^2
        k(1) = (2/3) (cross(v, D) + a cross(u, v)) / b^2

    which is two coupled quadratics.  Fixed point on (a, b), starting from the
    arc arms; returns None when the target cannot be met.
    """
    D = (p3[0] - p0[0], p3[1] - p0[1])
    u = (math.cos(t0), math.sin(t0))
    v = (math.cos(t1), math.sin(t1))
    chord = math.hypot(*D)
    if chord < 1e-12:
        return None
    Z = _cross(u, v)
    X0 = _cross(u, D)
    X1 = _cross(v, D)
    a = b = chord / 3.0
    for _ in range(iters):
        if k0 > 1e-12:
            num = (2.0 / 3.0) * (X0 - b * Z)
            if num <= 0:
                return None
            a = math.sqrt(num / k0)
        if k1 > 1e-12:
            num = (2.0 / 3.0) * (X1 + a * Z)
            if num <= 0:
                return None
            b = math.sqrt(num / k1)
        if a > 100 * chord or b > 100 * chord:
            return None
    return a, b


def spans(path: Spiral, max_turn: float = math.radians(50.0),
          sharp: float = math.radians(12.0), apsis: str = "sharp",
          arms: str = "arc") -> list[dict]:
    """Group the chords of `path` into cubics, each within `max_turn`."""
    nodes = path.floats()
    if len(nodes) < 2:
        return []
    leave, arrive = node_tangents(path, sharp, apsis)
    heads = [h.angle for h in path.headings]

    alpha = path.triangle.radians
    groups: list[tuple[int, int]] = []
    i = 0
    while i < len(nodes) - 1:
        j, turn = i + 1, 0.0
        # the curvature sign entering the span: the turn that produced its
        # first chord.  Without it a span can start just after an apsis and
        # swallow the reversal, which is exactly where a cubic fails worst.
        sign = (turns_sign := (path.turns[i] > 0) - (path.turns[i] < 0))
        while j < len(nodes) - 1:
            step = alpha * path.turns[j]
            # a curvature reversal means the cubic has to change its bulge
            # sense inside the span, which no single cubic does well
            if step and sign and (step > 0) != (sign > 0):
                break
            if abs(turn + step) > max_turn:
                break
            turn += step
            if step:
                sign = 1 if step > 0 else -1
            j += 1
        groups.append((i, j))
        i = j

    from .quality import curvature_targets

    targets = curvature_targets(path) if arms == "menger" else None

    out = []
    for i, j in groups:
        if arms == "menger":
            k0 = abs(targets[i][1])
            k1 = abs(targets[j][0])
            solved = arms_for_curvature(nodes[i], nodes[j], leave[i], arrive[j],
                                        k0, k1)
            if solved is not None:
                # verify: a converged solve must actually land on the targets
                probe = {"s0": float(i), "s1": float(j), "p0": nodes[i],
                         "c1": (nodes[i][0] + solved[0] * math.cos(leave[i]),
                                nodes[i][1] + solved[0] * math.sin(leave[i])),
                         "c2": (nodes[j][0] - solved[1] * math.cos(arrive[j]),
                                nodes[j][1] - solved[1] * math.sin(arrive[j])),
                         "p3": nodes[j]}
                got0, got1 = abs(curvature(probe, 0.0)), abs(curvature(probe, 1.0))
                if k0 > 1e-9 and abs(got0 - k0) > 0.05 * k0:
                    solved = None
                elif k1 > 1e-9 and abs(got1 - k1) > 0.05 * k1:
                    solved = None
            if solved is not None:
                a, b = solved
                out.append({"s0": float(i), "s1": float(j), "p0": nodes[i],
                            "c1": (nodes[i][0] + a * math.cos(leave[i]),
                                   nodes[i][1] + a * math.sin(leave[i])),
                            "c2": (nodes[j][0] - b * math.cos(arrive[j]),
                                   nodes[j][1] - b * math.sin(arrive[j])),
                            "p3": nodes[j]})
                continue
        if j - i == 1 and apsis == "sharp" and arms != "menger":
            # one chord: draw the chord.  Smoothing one end of a single short
            # span asks the cubic to bend 3 degrees over one chord, which
            # overshoots the chain's curvature by 2x.  The straight chord is
            # both exact and the thing the polygon actually says.
            out.append(_cubic(nodes[i], nodes[j], heads[i], heads[i],
                              s0=float(i), s1=float(j)))
        else:
            out.append(_cubic(nodes[i], nodes[j], leave[i], arrive[j],
                              s0=float(i), s1=float(j)))
    return out


def join_kink(curves: list[dict]) -> float:
    """The largest tangent jump between one cubic and the next, in radians.

    Zero means the path is G1 as drawn.  A nonzero value is a corner that was
    left in on purpose, by `node_tangents` keeping a big turn sharp.
    """
    worst = 0.0
    for a, b in zip(curves, curves[1:]):
        ta = math.atan2(a["p3"][1] - a["c2"][1], a["p3"][0] - a["c2"][0])
        tb = math.atan2(b["c1"][1] - b["p0"][1], b["c1"][0] - b["p0"][0])
        d = abs((ta - tb + math.pi) % (2 * math.pi) - math.pi)
        worst = max(worst, d)
    return worst


def sagitta(path: Spiral) -> float:
    """The resolution floor: how far the smooth curve sits from the chords.

    A chord of length L subtending a turn `d` belongs to a circle of radius
    `L / (2 sin(d/2))`; the curve bulges away from the chord by its sagitta.
    No cubic fit can beat this, so a deviation near it means the fit is done
    and the *chain* is the limit.
    """
    worst = 0.0
    for turn in path.turns:
        d = abs(path.triangle.radians * turn)
        if d <= 0 or d >= math.pi:
            continue
        R = float(path.length) / (2 * math.sin(d / 2))
        worst = max(worst, R * (1 - math.cos(d / 2)))
    return worst


def _cubic(p0, p3, t0, t1, s0=0.0, s1=1.0) -> dict:
    cx, cy = p3[0] - p0[0], p3[1] - p0[1]
    chord = math.hypot(cx, cy)
    if chord < 1e-12:
        return {"s0": s0, "s1": s1, "p0": p0, "c1": p0, "c2": p3, "p3": p3}

    def arm(theta):
        cos = (cx * math.cos(theta) + cy * math.sin(theta)) / chord
        half = (1.0 + max(-1.0, min(1.0, cos))) / 2.0
        return chord / (3.0 * half) if half > 1e-9 else chord

    a0, a1 = arm(t0), arm(t1)
    return {
        "s0": s0, "s1": s1, "p0": p0,
        "c1": (p0[0] + a0 * math.cos(t0), p0[1] + a0 * math.sin(t0)),
        "c2": (p3[0] - a1 * math.cos(t1), p3[1] - a1 * math.sin(t1)),
        "p3": p3,
    }


def cubic_at(span: dict, t: float) -> tuple[float, float]:
    u = 1.0 - t
    b = (u * u * u, 3 * u * u * t, 3 * u * t * t, t * t * t)
    px = (span["p0"][0], span["c1"][0], span["c2"][0], span["p3"][0])
    py = (span["p0"][1], span["c1"][1], span["c2"][1], span["p3"][1])
    return (sum(w * v for w, v in zip(b, px)), sum(w * v for w, v in zip(b, py)))


def _segment_distance(p, a, b) -> float:
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    den = dx * dx + dy * dy
    if den < 1e-18:
        return math.hypot(p[0] - ax, p[1] - ay)
    t = ((p[0] - ax) * dx + (p[1] - ay) * dy) / den
    t = max(0.0, min(1.0, t))
    return math.hypot(p[0] - (ax + t * dx), p[1] - (ay + t * dy))


def curvature(span: dict, t: float) -> float:
    """Signed curvature of the cubic at `t`, from its first two derivatives."""
    px = (span["p0"], span["c1"], span["c2"], span["p3"])
    u = 1.0 - t
    x1 = 3 * u * u * (px[1][0] - px[0][0]) + 6 * u * t * (px[2][0] - px[1][0]) \
        + 3 * t * t * (px[3][0] - px[2][0])
    y1 = 3 * u * u * (px[1][1] - px[0][1]) + 6 * u * t * (px[2][1] - px[1][1]) \
        + 3 * t * t * (px[3][1] - px[2][1])
    x2 = 6 * u * (px[2][0] - 2 * px[1][0] + px[0][0]) \
        + 6 * t * (px[3][0] - 2 * px[2][0] + px[1][0])
    y2 = 6 * u * (px[2][1] - 2 * px[1][1] + px[0][1]) \
        + 6 * t * (px[3][1] - 2 * px[2][1] + px[1][1])
    speed = math.hypot(x1, y1)
    return (x1 * y2 - y1 * x2) / speed ** 3 if speed > 1e-12 else 0.0


def max_curvature(curves: list[dict], samples: int = 48) -> float:
    """Largest |curvature| anywhere on the drawn curve."""
    worst = 0.0
    for c in curves:
        for i in range(samples + 1):
            worst = max(worst, abs(curvature(c, i / samples)))
    return worst


def deviation(span: dict, nodes: list[tuple[float, float]], samples: int = 33) -> float:
    """Worst distance from the cubic to the polyline it replaces."""
    lo, hi = int(span["s0"]), int(span["s1"])
    worst = 0.0
    for k in range(samples):
        p = cubic_at(span, k / (samples - 1))
        best = min(_segment_distance(p, nodes[i], nodes[i + 1])
                   for i in range(lo, hi))
        worst = max(worst, best)
    return worst

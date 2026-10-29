"""Acceleration, and what "smooth" should mean for a drawn stroke.

A point travelling at unit speed has acceleration `a = kappa * v^2`, so the
*magnitude* of its acceleration is the magnitude of the curvature.  That is the
number a pen, a cutter or a plotter actually feels, and it is the number the eye
reads as "how hard is this line bending".

It also settles the apsis.  A leaf tip is the place where the curvature
reverses **at its peak**: the signed curvature jumps by twice its value, and the
magnitude does not move at all.  Both numbers are reported here, and only one of
them is a defect.
"""

from __future__ import annotations

import math

from .spiral import Spiral


def signed(path: Spiral) -> list[float]:
    """Signed curvature per chord: turn per chord, divided by the chord length."""
    return [t * path.triangle.radians / float(path.length) for t in path.turns]


def magnitude(path: Spiral) -> list[float]:
    """|curvature| per chord -- the acceleration at unit speed."""
    return [abs(v) for v in signed(path)]


def peak(path: Spiral) -> float:
    return max(magnitude(path))


def signed_jump(path: Spiral) -> float:
    """The largest change of signed curvature between neighbouring chords.

    At a design apsis this is twice the peak: the reversal itself.
    """
    values = signed(path)
    return max((abs(b - a) for a, b in zip(values, values[1:])), default=0.0)


def magnitude_jump(path: Spiral) -> float:
    """The largest change of |curvature|.  This is the one that is a defect."""
    values = magnitude(path)
    return max((abs(b - a) for a, b in zip(values, values[1:])), default=0.0)


def jerk(path: Spiral) -> float:
    """Largest |d|kappa|/ds| -- how fast the pen force changes, per unit length."""
    values = magnitude(path)
    L = float(path.length)
    return max((abs(b - a) / L for a, b in zip(values, values[1:])), default=0.0)


def expected_step(path: Spiral) -> float:
    """The curvature change one chord is *supposed* to make.

    Every chord turns one more increment than the last, so |kappa| rises by
    `alpha / L` per chord.  That is the clothoid law, not a jump, and it is the
    yardstick every other change has to be measured against.
    """
    return path.triangle.radians / float(path.length)


def apsis_is_pinned(path: Spiral) -> bool:
    """True when the signed curvature reverses exactly at its peak.

    That is a leaf tip: `|kappa|` is continuous there, by construction.
    """
    values = signed(path)
    pk = peak(path)
    for a, b in zip(values, values[1:]):
        if a * b < 0 and abs(a) > 0.9 * pk and abs(b) > 0.9 * pk:
            return True
    return False


def report(path: Spiral) -> dict:
    """Everything that can be said about the stroke's acceleration."""
    return {
        "peak_acceleration": peak(path),
        "signed_jump": signed_jump(path),
        "magnitude_jump": magnitude_jump(path),
        "jerk": jerk(path),
        "pinned_apsis": apsis_is_pinned(path),
        "chord": float(path.length),
        "ramp": expected_step(path),
        "jump_in_steps": magnitude_jump(path) / expected_step(path),
    }


def verdict(path: Spiral, slack: float = 1.5) -> str:
    """One line: is the stroke's bending continuous, and is that on purpose?

    A jump is only a defect when it exceeds the ramp every chord is entitled
    to, `alpha/L`, by more than `slack`.
    """
    r = report(path)
    step = expected_step(path)
    if r["magnitude_jump"] > slack * step:
        return (f"bending jumps {r['magnitude_jump'] / step:.1f} steps of the ramp "
                f"({100 * r['magnitude_jump'] / max(r['peak_acceleration'], 1e-12):.0f}% "
                f"of peak): an unfinished step")
    if r["pinned_apsis"]:
        return ("bending is continuous; the signed curvature reverses at peak, "
                "so this is a designed apsis")
    return "bending is continuous and the curvature does not reverse"


# -- Menger: curvature from three nodes, which is what a join means --------
def menger_of(a, b, c) -> float:
    """Curvature of the circle through three points: 2h / (|ab| |bc|)."""
    ax, ay = float(a[0]) - float(b[0]), float(a[1]) - float(b[1])
    cx, cy = float(c[0]) - float(b[0]), float(c[1]) - float(b[1])
    ac = math.hypot(float(c[0]) - float(a[0]), float(c[1]) - float(a[1]))
    if ac == 0:
        return 0.0
    h = abs(ax * cy - ay * cx) / ac
    return 2.0 * h / (math.hypot(ax, ay) * math.hypot(cx, cy))


def menger(path: Spiral, k: int, signed: bool = True) -> float:
    """Curvature of the circle through nodes k-1, k, k+1.

    `2h / (|ab| |bc|)` with h the perpendicular from b onto ac -- the discrete
    curvature of three points, and the only definition of "the curvature at a
    node" that does not have to choose a side.  Signed by the turn at k, so a
    reversal shows as a sign flip with the magnitude unchanged.
    """
    n = len(path.nodes) - 1
    if not 0 <= k <= n:
        raise IndexError(f"node {k} outside 0..{n}")
    if k == 0 or k == n:
        # an end node has only one chord, so fall back to the chord rule
        turn = path.turns[k if k == 0 else k - 1]
        value = abs(turn) * path.triangle.radians / float(path.length)
    else:
        value = menger_of(path.nodes[k - 1], path.nodes[k], path.nodes[k + 1])
    if signed and k < len(path.turns) and path.turns[k] < 0:
        return -value
    return value


def menger_profile(path: Spiral) -> list[float]:
    return [menger(path, k) for k in range(len(path.nodes))]


def menger_agrees_with_chord(path: Spiral, tol: float = 1e-3) -> bool:
    """Menger and the chord rule are within `tol` relative, as they should be."""
    for k, value in enumerate(menger_profile(path)):
        chord = abs(path.turns[k] if k < len(path.turns) else 0) * \
            path.triangle.radians / float(path.length)
        if chord > 0 and abs(abs(value) - chord) > tol * chord:
            return False
    return True


def reversal_nodes(path: Spiral) -> set[int]:
    """Nodes where the turn changes sign: the corners, where curvature is
    one-sided and there is no single value to match."""
    out = set()
    for k in range(1, len(path.turns)):
        if path.turns[k] and path.turns[k - 1] and \
                (path.turns[k] > 0) != (path.turns[k - 1] > 0):
            out.add(k)
    return out


def curvature_targets(path: Spiral) -> list[tuple[float, float]]:
    """The curvature a drawn curve should have at each node, (arriving, leaving).

    Away from a reversal the Menger value is the answer, and arriving equals
    leaving.  At a reversal there is no single value -- the corner has one on
    each side -- so each side gets its own chord's curvature, signed.  The two
    differ only in sign, which is the leaf tip: same bending, opposite sense.
    """
    rev = reversal_nodes(path)
    al = path.triangle.radians
    L = float(path.length)
    out = []
    for k in range(len(path.nodes)):
        if k in rev:
            # signed: at a corner the two sides differ by sign, not by size
            left = path.turns[k - 1] if k > 0 else 0
            right = path.turns[k] if k < len(path.turns) else 0
            out.append((left * al / L, right * al / L))
        else:
            m = menger(path, k)
            out.append((m, m))
    return out


def menger_agrees(curves, path: Spiral, tol: float = 0.05):
    """Compare the drawn cubics' knot curvature with the Menger intent.

    Returns `(worst relative error away from corners, worst node, corner
    error)`.  Corners are reported separately because a corner is a design
    decision, not a fit failure.
    """
    from .spans import curvature as drawn_curvature

    targets = curvature_targets(path)
    rev = reversal_nodes(path)
    worst = (0.0, None)
    corner = 0.0
    for c in curves:
        i, j = int(c["s0"]), int(c["s1"])
        for node, got, want in ((i, abs(drawn_curvature(c, 0.0)), targets[i][1]),
                                (j, abs(drawn_curvature(c, 1.0)), targets[j][0])):
            if want < 1e-9:
                continue
            err = abs(got - want) / want
            if node in rev:
                corner = max(corner, err)
            elif err > worst[0]:
                worst = (err, node)
    return worst[0], worst[1], corner

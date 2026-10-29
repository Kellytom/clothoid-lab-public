"""Named chains, each ending exactly on an axis.

All three use the same convention as `Spiral`: the first chord lies on the
starting heading, so the turn applied at node k is `k*alpha` for the spiral and
the coefficient bookkeeping is offset by one from the "first chord already
turned" convention used in the notes this was checked against.

Every builder asserts the turn coefficient is exactly zero.  That is not
decoration: `closure.py` proves no other exact axis landing exists.
"""

from __future__ import annotations

import math

from .closure import closure_pairs, g2_pairs, inverse_triangular, triangular
from .spiral import Spiral, triangular
from .triples import Triple, for_angle


def _exponent(power: int) -> int:
    """Validate the exponent dial: a whole number, zero or more."""
    if int(power) != power or power < 0:
        raise ValueError(f"power must be a non-negative integer, got {power!r}")
    return int(power)


def _whole(value: int, name: str) -> int:
    """Validate a group index: turns and quarter turns are never floats."""
    if int(value) != value:
        raise ValueError(f"{name} must be a whole number, got {value!r}")
    return int(value)


def power_sum(n: int, power: int) -> int:
    """0**p + 1**p + ... + (n-1)**p, the heading coefficient after n chords."""
    return sum(k ** power for k in range(n))


def _out_turns(steps: int, power: int) -> list[int]:
    """The growing half of the schedule: k**p for k = 0 .. steps-1."""
    return [k ** power for k in range(steps)]


def spiral(triangle: Triple, steps: int, length=1, power: int = 1) -> Spiral:
    """A plain Euler spiral: turns k**p, the clothoid at power 1."""
    path = Spiral(triangle, length)
    path.extend(_out_turns(steps, _exponent(power)))
    return path


def lobe(triangle: Triple, steps: int, length=1, power: int = 1) -> Spiral:
    """Out with growing curvature, back with it reversed.  Sharp apsis.

    Turns k**p for k = 0..n-1, then the same integers negated.  The heading
    peaks at `power_sum(n, p)*alpha`, the curvature flips sign there, and the
    sum is zero, so the exit is exactly parallel to the entry for every p.
    """
    out = _out_turns(steps, _exponent(power))
    path = Spiral(triangle, length)
    path.extend(out)
    path.extend(-t for t in reversed(out))
    _assert_closed(path)
    return path


def hook(triangle: Triple, multiplier: int, n_out: int | None = None,
         length=1) -> Spiral:
    """Spiral in on 1, 2, 3..., unwind on -m, -2m, ...  Sharp apsis.

    The unwind is `multiplier` times faster than the wind, which is what makes
    a teardrop rather than a symmetric lobe.  Only pairs where the turn sums
    cancel exist; `n_out` defaults to the first one found.
    """
    pairs = closure_pairs(multiplier)
    if not pairs:
        raise ValueError(f"no exact closure for multiplier {multiplier}")
    if n_out is None:
        n_in, n_out = pairs[0]
    else:
        match = [p for p in pairs if p[1] == n_out]
        if not match:
            raise ValueError(
                f"multiplier {multiplier} does not close with {n_out} out-steps; "
                f"try {[p[1] for p in pairs]}")
        n_in, n_out = match[0]
    path = Spiral(triangle, length)
    path.extend(range(0, n_in + 1))          # n_in + 1 chords, sum T(n_in)
    path.extend(-multiplier * k for k in range(1, n_out + 1))
    _assert_closed(path)
    return path


def g2_lobe(triangle: Triple, steps: int, length=1) -> Spiral:
    """The same lobe with the curvature continuous at the apsis.

    Turns 0..n-1, then n-1, n-2, ..., 0, -1, ..., -j, where j(j+1) = 2n(n-1).
    The exit opens at exactly the entry's final curvature, so the join is G2.
    Solutions are sparse: n = 3, 15, 85, ...
    """
    m = steps - 1
    j = inverse_triangular(2 * triangular(m))
    if j is None:
        raise ValueError(
            f"no G2 closure for {steps} steps; try "
            f"{[m + 1 for m, _ in g2_pairs(60)]}")
    path = Spiral(triangle, length)
    path.extend(range(0, steps))
    path.extend(range(m, -1, -1))
    path.extend(-k for k in range(1, j + 1))
    _assert_closed(path)
    return path


def fork(path: Spiral, node: int, steps: int = 9, length=1, power: int = 1,
         turn: int = 0, quarter: int = 0, sign: int = -1):
    """A branch off an exact node, with its angle from the rotation group.

    The branch starts on the node itself: the same rational point and the same
    exact heading, so `joined` can prove the attachment with equality instead
    of measuring it.  `turn` counts triangle angles and `quarter` counts right
    angles -- both integers, never degrees.  Leave both at zero for a G1 join,
    or set one for an exact corner.  The branch turns opposite the part it
    leaves (`sign=-1`), so it parts company rather than shadowing the trunk.

    Returns the anchor `(point, heading)` and the branch.
    """
    point, heading = path.knots()[node]
    heading = heading * (path.triangle.direction ** _whole(turn, "turn"))
    heading = heading.quarter(_whole(quarter, "quarter"))
    branch = Spiral(path.triangle, length, heading=heading, start=point)
    branch.extend(sign * t for t in _out_turns(steps, _exponent(power)))
    return (point, heading), branch


def joined(a: Spiral, b: Spiral, node: int) -> Spiral:
    """Prove `b` leaves `a`'s `node` exactly; return `b`.

    Equality is vector equality: the same rational point and the same exact
    direction, not a tolerance.  A branch from `fork` at that node passes with
    no arithmetic at all; a branch merely drawn near it fails, which is the
    point -- position error in this method is a whole chord, never a rounding.
    """
    point, heading = a.knots()[node]
    leaves = b.headings[0] if b.headings else b.heading
    if b.nodes[0] != point:
        raise AssertionError(
            f"branch starts at {b.nodes[0]}, node {node} is at {point}")
    if leaves != heading:
        raise AssertionError(
            f"branch leaves at {leaves}, node {node} heads {heading}")
    return b


def _assert_closed(path: Spiral) -> None:
    if path.coeff != 0:
        raise AssertionError(f"chain does not close: coefficient {path.coeff}")
    if not path.heading.is_axis_aligned():
        raise AssertionError(f"chain does not end on an axis: {path.heading}")


def chord_for_acceleration(triangle: Triple, turns, acceleration: float):
    """The chord length that puts the peak |curvature| at `acceleration`.

    Curvature is turn-per-chord over chord length, so it scales as 1/L: ask for
    a softer stroke and the whole chain grows.  This is the constructor that
    treats acceleration as a design input rather than a symptom.
    """
    if acceleration <= 0:
        raise ValueError(f"acceleration must be positive, got {acceleration}")
    peak_turn = max(abs(t) for t in turns)
    if peak_turn == 0:
        raise ValueError("a straight chain has no curvature to bound")
    return peak_turn * triangle.radians / acceleration


def curl(peak: float = 200.0, chord: float = 6.0, length=None,
         accel: float | None = None, power: int = 1) -> Spiral:
    """A volute whose smoothness you ask for in degrees.

    `peak` is the heading at the apsis; `chord` is the widest turn any single
    chord may take, which fixes the triangle -- the thinner the triangle, the
    smoother the drawn curve, at the cost of a longer hypotenuse.  The step
    count follows from the two: power_sum(n, p)*alpha = peak.

    `power` is the exponent dial: turns run k**p instead of k.  p = 1 is the
    clothoid; p = 0 is a circle; p > 1 holds the turning back to the last
    chords, so the run opens long and tightens at the apsis.  Exactness does
    not care: every integer p closes because the reversal cancels the same
    integers, so the cost is still only digits.

    Two numbers instead of three, and neither is a hairiness knob you have to
    tune by eye: the chord budget *is* the resolution.
    """
    power = _exponent(power)
    if not 0 < chord < 45:
        raise ValueError(f"chord budget must be in (0, 45) degrees, got {chord}")
    if not 0 < peak < 720:
        raise ValueError(f"peak must be in (0, 720) degrees, got {peak}")

    rough = max(3, math.ceil(2 * peak / chord) + 1)
    triangle = for_angle(chord / (rough - 1))
    alpha = triangle.degrees
    if power == 1:
        # p = 1 keeps the original closed form, bit for bit
        steps = max(2, int(round((-1 + math.sqrt(1 + 8 * peak / alpha)) / 2)) + 1)
    else:
        # power_sum(n, p) grows like n**(p+1)/(p+1); land on the first n at
        # or above the requested peak, so the peak stays a floor.
        steps = max(2, int(round((peak / alpha * (power + 1))
                                 ** (1 / (power + 1)))))
        while power_sum(steps, power) * alpha < peak:
            steps += 1
        while steps > 2 and power_sum(steps - 1, power) * alpha >= peak:
            steps -= 1
    if accel is not None:
        # the stroke's softness is the input; the chord length follows from it
        length = chord_for_acceleration(triangle, _out_turns(steps, power),
                                        accel)
    elif length is None:
        length = 1
    # exactness is carried by integers over a power of the hypotenuse, so the
    # cost is set by c^power_sum(steps, p). Guard it rather than hang.
    digits = power_sum(steps, power) * math.log10(triangle.c)
    if digits > 25_000:
        raise ValueError(
            f"chord {chord} deg needs about {digits:.0f}-digit integers at "
            f"c={triangle.c}; the exact chain stops being practical here, "
            f"use a chord budget of 4 deg or more")
    return lobe(triangle, steps, 1 if length is None else length, power)

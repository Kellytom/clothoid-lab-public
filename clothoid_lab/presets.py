"""Named starting designs, with their numbers derived rather than typed.

A quarter turn over an arc length L needs a curvature rate of 2 * theta / L^2,
because the turn of a clothoid is theta = kd * L^2 / 2. Every preset is written
that way, so changing a length keeps the turn the preset is named for.
"""

from __future__ import annotations

import math

from .model import Design, Segment


def rate_for_turn(length: float, degrees: float) -> float:
    """The curvature rate that turns `degrees` over an arc length of `length`."""
    return 2.0 * math.radians(degrees) / (length * length)


def s_curve(length: float = 40.0, degrees: float = 90.0) -> Design:
    """Two clothoids of opposite hand: the bend reverses at the join, so it is an S.

    The first segment turns by `degrees`, so its end curvature is kappa = kd*L.
    The second halves the rate and turns it negative, running from +kappa to
    -kappa, which is a real reversal rather than a bend back to straight.
    """
    kd = rate_for_turn(length, degrees)
    return Design(
        name=f"s-curve {degrees:g} deg",
        segments=[Segment(kd=kd, length=length), Segment(kd=-1.5 * kd, length=length)],
        anchor={"x": 0.0, "y": 0.0, "angle": 0.0},
        stroke=0.8,
    )


def ogee(length: float = 30.0, degrees: float = 60.0) -> Design:
    """The ogee: curvature rises, crosses zero, falls, and returns to straight.

    Each stage hands the next the curvature it ended on, so every join is G2.
    The middle stage turns by twice the first and in the opposite direction,
    which makes the whole shape return parallel to where it started.
    """
    kd = rate_for_turn(length, degrees)
    return Design(
        name="ogee",
        segments=[
            Segment(kappa0=0.0, kd=kd, length=length),
            Segment(kappa0=kd * length, kd=-kd, length=2 * length),
            Segment(kappa0=-kd * length, kd=kd, length=length),
        ],
        anchor={"x": 0.0, "y": 0.0, "angle": 0.0},
        stroke=0.8,
    )


def bracket(length: float = 30.0, degrees: float = 90.0,
            straight: float = 12.0, arc_share: float = 0.5) -> Design:
    """A road fillet: straight, transition in, constant arc, transition out, straight.

    This is the construction clothoids exist for. The transitions each turn
    `degrees` * (1 - arc_share) / 2, and the circular middle turns the rest, so
    the tangent is continuous in direction and the curvature is continuous at
    every join.
    """
    turn = math.radians(degrees)
    each = turn * (1.0 - arc_share) / 2.0
    kd = 2.0 * each / (length * length)
    kappa = kd * length
    return Design(
        name=f"bracket {degrees:g} deg",
        segments=[
            Segment(kappa0=0.0, kd=0.0, length=straight),
            Segment(kappa0=0.0, kd=kd, length=length),
            Segment(kappa0=kappa, kd=0.0, length=turn * arc_share / kappa),
            Segment(kappa0=kappa, kd=-kd, length=length),
            Segment(kappa0=0.0, kd=0.0, length=straight),
        ],
        anchor={"x": 0.0, "y": 0.0, "angle": 0.0},
        stroke=0.8,
    )


def petal(length: float = 26.0, degrees: float = 100.0) -> Design:
    """Four clothoids, hand alternating, so the ends face the same way they started."""
    kd = rate_for_turn(length, degrees)
    return Design(
        name="petal",
        segments=[
            Segment(kappa0=0.0, kd=kd, length=length),
            Segment(kappa0=kd * length, kd=-2 * kd, length=length),
            Segment(kappa0=-kd * length, kd=2 * kd, length=length),
            Segment(kappa0=kd * length, kd=-kd, length=length),
        ],
        anchor={"x": 0.0, "y": 0.0, "angle": 0.0},
        stroke=0.8,
    )


PRESETS = {
    "s-curve": s_curve,
    "ogee": ogee,
    "bracket": bracket,
    "petal": petal,
}


def get(name: str) -> Design:
    if name not in PRESETS:
        raise KeyError(f"no preset named {name!r}; try one of {', '.join(PRESETS)}")
    return PRESETS[name]()

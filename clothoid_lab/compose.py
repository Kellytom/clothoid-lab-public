"""Cut, reverse, connect and join designs.

These are the splice operations. Trimming and reversing are the library's own,
so a cut piece is still made of the same clothoid arcs, not a refitted copy.
The G2 connectors (`2arc`, `3arc`, `clc`) exist for joining two finished pieces
with curvature continuity; `join` uses one at the seam.

Everything returns an ordinary `Design`, with curvature written out per segment,
so the result draws, offsets and round-trips like any other design.
"""

from __future__ import annotations

from . import backend as backends, engine
from .model import Design


class ComposeError(ValueError):
    """The pieces cannot be cut or joined as asked."""


def _module(backend: str | None = None):
    module = backends.load(backend)
    if not hasattr(module, "trim_segments"):
        raise ComposeError(
            "curve operations are only in the compiled backend; build it with "
            "scripts/build-native.sh or unset CLOTHOID_BACKEND")
    return module


def _materialize(design: Design, backend: str | None = None):
    chain = engine.build(design, backend=backend)
    pieces = [{"k0": p.k0, "kd": p.kd, "length": p.length} for p in chain.segments]
    return chain, pieces


def start_pose(design: Design, backend: str | None = None) -> tuple:
    chain, _ = _materialize(design, backend)
    x, y = chain.point(0.0)
    return x, y, chain.tangent(0.0), chain.kappa(0.0)


def end_pose(design: Design, backend: str | None = None) -> tuple:
    chain, _ = _materialize(design, backend)
    length = chain.length
    x, y = chain.point(length)
    return x, y, chain.tangent(length), chain.kappa(length)


def trim(design: Design, s0: float, s1: float,
         backend: str | None = None) -> Design:
    """Keep the arc-length range [s0, s1]; the ends move, nothing is refitted."""
    module = _module(backend)
    chain, pieces = _materialize(design, backend)
    if not (0.0 <= s0 < s1 <= chain.length):
        raise ComposeError(
            f"trim range {s0:g}..{s1:g} is outside 0..{chain.length:.6g}")
    out = module.trim_segments(pieces, dict(design.anchor), s0, s1)
    return Design.from_pieces(
        out, name=f"{design.name} trim {s0:g}-{s1:g}",
        stroke=design.stroke, g1=design.g1)


def reverse(design: Design, backend: str | None = None) -> Design:
    """Traverse the same chain the other way."""
    module = _module(backend)
    _, pieces = _materialize(design, backend)
    out = module.reverse_segments(pieces, dict(design.anchor))
    return Design.from_pieces(
        out, name=f"{design.name} reversed",
        stroke=design.stroke, g1=design.g1)


def connect(pose0, pose1, method: str = "3arc",
            backend: str | None = None) -> Design:
    """A G2 connector between two poses: (x, y, theta, kappa)."""
    module = _module(backend)
    out = module.connect_segments(pose0, pose1, method=method)
    return Design.from_pieces(
        out, name=f"connector {method}", stroke=1.0)


def join(first: Design, second: Design, method: str = "3arc",
         backend: str | None = None) -> Design:
    """Place `second` where it is anchored and bridge the two with a G2 connector.

    The pieces' curvature is written out first, so the second design's inherited
    curvature cannot silently re-inherit from the connector.
    """
    module = _module(backend)
    _, pieces_first = _materialize(first, backend)
    _, pieces_second = _materialize(second, backend)
    connector = module.connect_segments(
        end_pose(first, backend), start_pose(second, backend), method=method)
    return Design.from_pieces(
        pieces_first + connector + pieces_second,
        anchor=dict(first.anchor),
        name=f"{first.name} + {second.name}",
        stroke=first.stroke,
        g1=bool(first.g1 or second.g1),
    )

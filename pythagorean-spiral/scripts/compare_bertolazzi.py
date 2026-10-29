"""Check the chain against the real clothoid engine already in this repo.

The claim under test: the Pythagorean chain is the Euler polygon of the
clothoid with `kappa0 = alpha/(2L)` and `kd = alpha/L^2`.  If that is true, the
node *headings* must agree with the engine's tangent at `s = k*L` to rounding,
and the node *positions* must sit within one chord of the engine's curve.

Run from the repository root:  .venv/bin/python pythagorean-spiral/scripts/compare_bertolazzi.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "pythagorean-spiral"))

from clothoid_lab import engine                      # noqa: E402
from clothoid_lab.model import Design, Segment       # noqa: E402
from pythagorean_spiral import design as tdesign        # noqa: E402
from pythagorean_spiral.triples import thinnest         # noqa: E402


def main() -> int:
    tri = thinnest(3125)
    L = 3121
    path = tdesign.spiral(tri, 32, L)
    eq = path.equivalent_clothoid()

    design_ = Design(
        segments=[Segment(kd=eq["kd"], length=eq["length"], kappa0=eq["kappa0"])],
        anchor={"x": 0.0, "y": 0.0, "angle": 0.0},
        name="oracle",
    )
    chain = engine.build(design_)

    print(f"triangle {tri}   alpha {tri.degrees:.6f} deg   L {L}")
    print(f"clothoid kappa0 {eq['kappa0']:.6g}  kd {eq['kd']:.6g}  A^2 {eq['A2']:.6g}")
    print(f"{'k':>3} {'heading err (deg)':>18} {'position err':>14} {'err/L':>8}")
    worst_h = worst_p = 0.0
    for k in range(0, len(path.turns)):
        s = k * L
        x, y = chain.point(s)
        theta = chain.tangent(s)
        nx, ny = path.nodes[k]
        h = path.headings[min(k, len(path.headings) - 1)].angle
        dh = abs((theta - h + math.pi) % (2 * math.pi) - math.pi)
        dp = math.hypot(float(nx) - x, float(ny) - y)
        worst_h = max(worst_h, dh)
        worst_p = max(worst_p, dp)
        if k % 4 == 0 or k == len(path.turns) - 1:
            print(f"{k:3d} {math.degrees(dh):18.9f} {dp:14.4f} {dp / L:8.4f}")
    s_end = (len(path.turns) - 1) * L
    tail = abs((chain.tangent(s_end) - path.heading.angle + math.pi)
               % (2 * math.pi) - math.pi)
    print(f"heading at the last node vs the chain's final direction: "
          f"{math.degrees(tail):.3e} deg")
    print(f"worst heading error at a node {math.degrees(worst_h):.3e} deg")
    print(f"worst position error {worst_p:.4f} = {worst_p / L:.4f} chords")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

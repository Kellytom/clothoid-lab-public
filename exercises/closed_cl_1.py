"""Exercise 1: a closed two-clothoid hairpin.

Prompt: start at (0, 0) heading east; a left-turning clothoid; go as far as you
can; change to a right-turning clothoid and return to (0, 0).

The hand-off is an inflection: curvature is zero there, so the first clothoid
ends with curvature to spare and the second starts from zero. That is a G1
join, not G2, and the design says so.

Three conditions fix the shape:

  position closes at (0, 0), and the end heading is west (180 degrees),
  a hairpin reversal rather than a loop.

With the first curvature rate fixed at 1 (a scale choice), the unknowns are
L1, k2, L2. The solved shape has L1 = 3.053068, k2 = -2.062369, L2 = 1.213706,
so the hand-off is at 71.6% of the total arc length: past the midpoint, as the
prompt warned.

The prompt's line check also holds. The ray from the origin at the hand-off's
bearing (58.62 degrees) meets the first clothoid twice, at r = 1.4178 and
r = 1.0938; the nearer one is the hand-off.

    python exercises/closed_cl_1.py
"""

from __future__ import annotations

import argparse
import math
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from clothoid_lab import cli, engine  # noqa: E402
from clothoid_lab.model import Design, Segment  # noqa: E402
from clothoid_lab.solve import least_squares  # noqa: E402

TARGET_HEADING = math.pi


def state(v):
    """The chain for (L1, k2, L2); first rate 1, hand-off curvature 0."""
    L1, k2, L2 = v
    return engine.build(Design(segments=[
        Segment(kappa0=0.0, kd=1.0, length=L1),
        Segment(kappa0=0.0, kd=k2, length=L2),
    ], anchor={"x": 0.0, "y": 0.0, "angle": 0.0}))


def residual(v):
    chain = state(v)
    x, y = chain.point(chain.length)
    heading = chain.tangent(chain.length) - TARGET_HEADING
    return [x, y, math.atan2(math.sin(heading), math.cos(heading))]


def solve():
    seeds = [
        (3.053, -2.062, 1.214),
        (2.5, -2.0, 1.5),
        (3.5, -2.5, 1.2),
        (4.0, -2.0, 1.5),
        (2.0, -1.0, 2.0),
    ]
    for seed in seeds:
        result = least_squares(residual, seed,
                               lower=[1e-6, -math.inf, 1e-6],
                               upper=[math.inf, -1e-9, math.inf],
                               max_iter=300, tol=1e-13)
        if result.converged and result.x[0] > result.x[2] > 0:
            return result
    raise SystemExit("no converging hairpin from the given seeds")


def ray_hits(chain, L1, bearing):
    """Where the ray at `bearing` meets the first clothoid, excluding the start."""
    sin_b, cos_b = math.sin(bearing), math.cos(bearing)

    def cross(s):
        x, y = chain.point(s)
        return x * sin_b - y * cos_b

    hits = []
    previous_s, previous = 0.0, cross(0.0)
    samples = 4000
    for i in range(1, samples + 1):
        s = L1 * i / samples
        value = cross(s)
        if previous * value <= 0 and s > 0:
            x, y = chain.point(s)
            if x * cos_b + y * sin_b > 0:
                lo, hi = previous_s, s
                for _ in range(60):
                    mid = (lo + hi) / 2.0
                    if cross(lo) * cross(mid) <= 0:
                        hi = mid
                    else:
                        lo = mid
                s_hit = (lo + hi) / 2.0
                hits.append(s_hit)
        previous_s, previous = s, value
    out = []
    for s in hits:
        radius = math.hypot(*chain.point(s))
        if radius > 1e-9:
            out.append((s, radius))
    # The hand-off itself lies on the ray by construction; the scan above only
    # sees sign changes, and the curve can end on the ray without crossing it.
    if all(abs(s - L1) > 1e-6 for s, _ in out):
        out.append((L1, math.hypot(*chain.point(L1))))
    return sorted(out)


def annotations(chain, switch_s):
    """Discreet axes through the origin and a label at the inflection."""
    x0, y0, x1, y1 = chain.bounds()
    px, py = chain.point(switch_s)
    width, height = x1 - x0, y1 - y0
    label = (px + 12.0, py + 12.0)
    return [
        {"kind": "line", "x1": x0, "y1": 0.0, "x2": x1, "y2": 0.0,
         "stroke": "#bdbdbd", "width": 0.25},
        {"kind": "line", "x1": 0.0, "y1": y0, "x2": 0.0, "y2": y1,
         "stroke": "#bdbdbd", "width": 0.25},
        {"kind": "text", "x": x1, "y": 0.0, "dx": 1.6, "dy": -1.4,
         "text": "x", "size": 3.5, "fill": "#7a7a7a", "front": True},
        {"kind": "text", "x": 0.0, "y": y1, "dx": 1.8, "dy": -2.6,
         "text": "y", "size": 3.5, "fill": "#7a7a7a", "front": True},
        {"kind": "text", "x": 0.0, "y": 0.0, "dx": -1.6, "dy": -1.4,
         "text": "0", "size": 3.5, "fill": "#7a7a7a", "front": True,
         "anchor": "end"},
        {"kind": "line", "x1": px, "y1": py, "x2": label[0], "y2": label[1],
         "stroke": "#9a9a9a", "width": 0.2, "dash": "1.2 1.2", "front": True},
        {"kind": "circle", "x": px, "y": py, "r": 1.2, "fill": "#333333",
         "front": True},
        {"kind": "text", "x": label[0], "y": label[1], "dx": 1.6, "dy": -1.0,
         "text": "inflection", "size": 4.0, "fill": "#333333", "front": True},
    ]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--page", default="200x250", help="sheet WxH in mm, 1 unit = 1 mm")
    ap.add_argument("--margin", type=float, default=6.0, help="page margin in mm")
    ap.add_argument("--width", type=float, default=10.0, help="rail to rail, mm")
    ap.add_argument("--stroke", type=float, default=0.5, help="line width, mm")
    ap.add_argument("--out", default=str(ROOT / "out" / "closed-cl-1.svg"))
    args = ap.parse_args(argv)

    result = solve()
    L1, k2, L2 = result.x
    unit = state(result.x)
    bearing = math.atan2(*reversed(unit.point(L1)))
    hits = ray_hits(unit, L1, bearing)
    ratio = L1 / unit.length

    page_w, page_h = (float(v) for v in args.page.lower().split("x"))
    ux0, uy0, ux1, uy1 = unit.bounds()
    spine_w, spine_h = ux1 - ux0, uy1 - uy0
    ink = args.width + args.stroke          # rails plus half the stroke each side
    scale = min((page_w - 2 * args.margin - ink) / spine_w,
                (page_h - 2 * args.margin - ink) / spine_h)

    design = Design(segments=[
        Segment(kappa0=0.0, kd=1.0 / (scale * scale), length=L1 * scale),
        Segment(kappa0=0.0, kd=k2 / (scale * scale), length=L2 * scale),
    ], anchor={"x": 0.0, "y": 0.0, "angle": 0.0},
        stroke=args.stroke, name="closed-cl-1", g1=True)
    chain = engine.build(design)

    text, info = cli.render(design, width=args.width, page=(page_w, page_h),
                            annotations=annotations(chain, L1 * scale))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(text, encoding="utf-8")
    design.save(Path(args.out).with_suffix(".json"))

    print(f"solved      L1={L1:.9f}  k2={k2:.9f}  L2={L2:.9f}")
    print(f"closure     {result.residual:.2e}   end heading "
          f"{math.degrees(chain.tangent(chain.length)):.6f} deg")
    print(f"hand-off    s={L1 * scale:.3f} mm  {100*ratio:.3f}% of the total arc length")
    print(f"ray hits    " + ", ".join(f"r={r:.4f} at s={s:.4f}" for s, r in hits))
    if len(hits) >= 2:
        nearer = min(hits, key=lambda hit: hit[1])
        print(f"            nearer r={nearer[1]:.4f} is the hand-off: "
              f"{'yes' if abs(nearer[0] - L1) < 1e-3 else 'no'}")
    print(f"scale       1 unit = 1.0000 mm   (page {page_w:g} x {page_h:g})")
    print(f"ribbon      rail to rail {args.width:g} mm, stroke {args.stroke:g} mm, "
          f"clear gap {args.width - args.stroke:g} mm")
    print(f"fit         {info['spine_error']:.5f} mm, {info['fit']['spans']} cubics, "
          f"min radius {info['chain']['min_radius']:.2f} mm")
    print(f"wrote       {args.out} and {Path(args.out).with_suffix('.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

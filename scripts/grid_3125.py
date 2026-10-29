"""The 3125 grid: exact clothoid coordinates at 4% steps of the envelope.

The curve is the standard Euler spiral with parameter A = 3125:

    theta(s) = s^2 / (2 A^2)          tangent angle, radians
    x(u) = A sqrt(pi) C(u)            C = Fresnel cosine integral
    y(u) = A sqrt(pi) S(u)            S = Fresnel sine integral
    u = s / (A sqrt(pi))              theta = pi u^2 / 2

The 4% steps are radial fractions of the largest distance from the inflection,
solved on the rising branch. They are not multiples of 125; see
docs/clothoid-grid-3125.md for what the residuals are.

    python scripts/grid_3125.py
    python scripts/grid_3125.py --steps 25 --json out/grid-3125.json
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from clothoid_lab import engine  # noqa: E402
from clothoid_lab.model import Design, Segment  # noqa: E402

SCALE = 3125.0
U_SPAN = 2.2


class Grid:
    """One long clothoid, addressed by the dimensionless u."""

    def __init__(self, scale: float = SCALE):
        self.scale = float(scale)
        self.k = 1.0 / (self.scale * self.scale)
        self.unit = self.scale * math.sqrt(math.pi)
        self.chain = engine.build(Design(
            segments=[Segment(kappa0=0.0, kd=self.k, length=self.unit * U_SPAN)]))

    def point(self, u: float) -> tuple[float, float]:
        return self.chain.point(self.unit * u)

    def radius(self, u: float) -> float:
        x, y = self.point(u)
        return math.hypot(x, y)

    def theta(self, u: float) -> float:
        return math.pi * u * u / 2.0

    def envelope(self) -> tuple[float, float]:
        """(u, radius) of the largest distance from the inflection."""
        best_u, best_r = 0.0, 0.0
        n = 8800
        for i in range(n + 1):
            u = U_SPAN * i / n
            r = self.radius(u)
            if r > best_r:
                best_u, best_r = u, r
        lo, hi = max(0.0, best_u - U_SPAN / n), min(U_SPAN, best_u + U_SPAN / n)
        for _ in range(60):
            a = lo + (hi - lo) / 3.0
            b = hi - (hi - lo) / 3.0
            if self.radius(a) < self.radius(b):
                lo = a
            else:
                hi = b
        u = (lo + hi) / 2.0
        return u, self.radius(u)

    def solve_fraction(self, fraction: float, u_max: float) -> float:
        """u where the radius first reaches `fraction` of the envelope."""
        if fraction <= 0.0:
            return 0.0
        lo, hi = 0.0, u_max
        for _ in range(80):
            mid = (lo + hi) / 2.0
            if self.radius(mid) < fraction * self.radius(u_max):
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2.0

    def half_bbox(self, u_stop: float, n: int = 2000) -> tuple[float, float]:
        """Width and height of the half-curve from the inflection."""
        x_max = y_max = 0.0
        for i in range(n + 1):
            x, y = self.point(u_stop * i / n)
            x_max = max(x_max, x)
            y_max = max(y_max, y)
        return x_max, y_max

    def rows(self, steps: int = 25) -> list[dict]:
        u_max, r_max = self.envelope()
        out = []
        for n in range(steps + 1):
            fraction = n / steps
            u = self.solve_fraction(fraction, u_max)
            x, y = self.point(u)
            out.append({
                "step": n,
                "fraction": fraction,
                "u": u,
                "theta_deg": math.degrees(self.theta(u)),
                "s": self.unit * u,
                "x": x,
                "y": y,
                "radius": math.hypot(x, y),
                "x_int": round(x),
                "y_int": round(y),
                "x125": round(x / 125.0) * 125,
                "y125": round(y / 125.0) * 125,
                "dx125": x - round(x / 125.0) * 125.0,
                "dy125": y - round(y / 125.0) * 125.0,
            })
        return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scale", type=float, default=SCALE, help="clothoid parameter A")
    ap.add_argument("--steps", type=int, default=25, help="subdivisions of the envelope")
    ap.add_argument("--json", default=None, help="write the table as JSON")
    ap.add_argument("--csv", default=None, help="write the table as CSV")
    ap.add_argument("--layout", type=int, default=0,
                    help="suggest a starting sheet for this many curves in a row")
    ap.add_argument("--gap", type=float, default=None,
                    help="gap and margin in units (default scale/5)")
    args = ap.parse_args(argv)

    grid = Grid(args.scale)
    u_max, r_max = grid.envelope()
    rows = grid.rows(args.steps)
    hook = grid.point(1.0)
    hook_r = math.hypot(*hook)

    print(f"A = {grid.scale:g}")
    print(f"hook  u=1.00000  theta=90.000 deg  x={hook[0]:.4f} y={hook[1]:.4f} "
          f"r={hook_r:.4f}  ({100*hook_r/r_max:.4f}% of max)")
    print(f"max   u={u_max:.5f}  theta={math.degrees(grid.theta(u_max)):.3f} deg  "
          f"r={r_max:.4f}  (x={grid.point(u_max)[0]:.4f} y={grid.point(u_max)[1]:.4f})")
    print(f"envelope: {r_max:.2f} from the inflection. No sheet is required; "
          f"a fixed --page must contain this, and --frame scales instead")
    half_hook = grid.half_bbox(1.0)
    half_max = grid.half_bbox(u_max)
    print()
    print(f"one half  @90 deg:   {half_hook[0]:9.2f} x {half_hook[1]:9.2f}  "
          f"({half_hook[0]/grid.scale:.4f}A x {half_hook[1]/grid.scale:.4f}A)")
    print(f"one half  @envelope: {half_max[0]:9.2f} x {half_max[1]:9.2f}  "
          f"({half_max[0]/grid.scale:.4f}A x {half_max[1]/grid.scale:.4f}A)")
    print(f"one S     @90 deg:   {2*half_hook[0]:9.2f} x {2*half_hook[1]:9.2f}  "
          f"({2*half_hook[0]/grid.scale:.4f}A x {2*half_hook[1]/grid.scale:.4f}A)")
    print(f"one S     @envelope: {2*half_max[0]:9.2f} x {2*half_max[1]:9.2f}  "
          f"({2*half_max[0]/grid.scale:.4f}A x {2*half_max[1]/grid.scale:.4f}A)")
    if args.layout:
        gap = args.gap if args.gap is not None else grid.scale / 5.0
        cell_w, cell_h = 3 * grid.scale, 2 * grid.scale
        total_w = args.layout * cell_w + (args.layout + 1) * gap
        total_h = cell_h + 2 * gap
        print()
        print(f"suggested sheet for {args.layout} in a row, cell 3A x 2A = "
              f"{cell_w:.0f} x {cell_h:.0f}, gap {gap:.0f}")
        print(f"sheet: {total_w:.0f} x {total_h:.0f}  "
              f"({total_w/125:.0f} x {total_h/125:.0f} steps of 125)")
        print(f"6A = {6*grid.scale:.0f} holds {6*grid.scale/(2*half_hook[0]):.2f} "
              f"full S across, or {6*grid.scale/half_hook[0]:.2f} halves")
    print()
    print(" n  %    u        theta     x          y          r        x125    y125    dx125   dy125")
    for r in rows:
        if r["step"] % max(1, args.steps // 5) == 0 or r["step"] == args.steps:
            print(f"{r['step']:2d} {100*r['fraction']:4.0f} {r['u']:8.5f} "
                  f"{r['theta_deg']:8.3f} {r['x']:10.3f} {r['y']:10.3f} {r['radius']:8.3f} "
                  f"{r['x125']:7d} {r['y125']:7d} {r['dx125']:7.2f} {r['dy125']:7.2f}")

    if args.json:
        os.makedirs(os.path.dirname(args.json) or ".", exist_ok=True)
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump({
                "scale": grid.scale,
                "rule": "radial fraction of the maximum distance from the inflection",
                "u_max": u_max,
                "theta_max_deg": math.degrees(grid.theta(u_max)),
                "radius_max": r_max,
                "hook": {"u": 1.0, "x": hook[0], "y": hook[1], "radius": hook_r},
                "steps": rows,
            }, fh, indent=2)
            fh.write("\n")
        print(f"\nwrote {args.json}")

    if args.csv:
        with open(args.csv, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        print(f"wrote {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

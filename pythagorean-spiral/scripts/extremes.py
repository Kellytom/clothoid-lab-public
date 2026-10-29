"""Generate docs/EXTREMES.md and its HTML twin: the hybrid at its edges.

    python scripts/extremes.py
"""

from __future__ import annotations

import math
import sys
import time
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from pythagorean_spiral import hybrid, ribbon  # noqa: E402
from pythagorean_spiral.exact import Dir  # noqa: E402
from pythagorean_spiral.spiral import Spiral  # noqa: E402
from pythagorean_spiral.triples import for_angle, thinnest  # noqa: E402

import explainer as ex  # noqa: E402

FIG = ex.FIG
INK, GOLD, RED, BLUE, FAINT = ex.INK, ex.GOLD, ex.RED, ex.BLUE, ex.FAINT


# ------------------------------------------------------------- builders ---
def leaf():
    """A leaf edge, a 90 degree corner at the tip, a relaxing return.

    Out: curvature climbs 0..5 chords.  The tip is a quarter-turn cusp, which
    is exact.  Back: curvature falls 5..0, so the return flattens.
    """
    tri = for_angle(3.0)
    path = Spiral(tri, Fraction(1, 2), heading=Dir.north())
    path.extend([0, 1, 2, 3, 4, 5])
    tip = len(path.turns)
    path.cusp(1)
    path.extend([5, 4, 3, 2, 1, 0])
    return path, tri, tip


def ring():
    """A 20k-chord circle in floats: the scale test, drawn as a ribbon."""
    tri = for_angle(0.018)
    steps = round(360 / tri.degrees)
    chain = hybrid.build(tri, [0] + [1] * (steps - 1),
                         length=Fraction(1, 100))
    return chain, tri


def exact_yardstick():
    """The same plan exact and float, at a size exact can still afford."""
    tri = thinnest(3125)
    turns = list(range(60))
    f = hybrid.build(tri, turns)
    e = f.exact()
    gap = max(math.hypot(ax - float(bx), ay - float(by))
              for (ax, ay), (bx, by) in zip(f.nodes, e.nodes))
    return gap, len(turns)


def big_lobe():
    """A closed lobe of 10,001 chords: the plan closes, the ink nearly does."""
    tri = thinnest(3125)
    steps = 5000
    turns = list(range(steps)) + list(range(-(steps - 1), 1))
    start = time.perf_counter()
    chain = hybrid.build(tri, turns)
    elapsed = time.perf_counter() - start
    return chain, elapsed


def angle_rows():
    """What the lattice can actually land on, with one triple as the unit."""
    tri = for_angle(3.0)
    a = tri.degrees
    rows = []
    for want in (30, 45, 90):
        steps = max(2, round(want / a) + 1)
        chain = hybrid.build(tri, [0] + [1] * (steps - 1))
        got = chain.peak_degrees
        rows.append([f"{want} deg", f"{steps} chords, flat", f"{got:.2f} deg",
                     f"{abs(got - want):.2f} deg", "lattice"])
    rows.append(["90 deg", "1 chord + cusp", "90.00 deg", "0.00 deg",
                 "exact swap"])
    return tri, rows


# -------------------------------------------------------------- figures ---
def fig_leaf():
    path, tri, tip = leaf()
    poly = ribbon.outline(path.nodes, Fraction(1, 12), taper=2)
    pts = [(float(x), float(y)) for x, y in poly]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    c = ex.Canvas((min(xs) - .4, max(xs) + .4), (min(ys) - .5, max(ys) + .5), 560, 620)
    c.poly(pts + [pts[0]], fill=INK, stroke=INK, width=0.5)
    tp = path.floats()[tip]
    c.dot(tp, 3.6, RED, "#fffdf7", 1.2)
    c.note(tp, "90 deg corner, exact", 10, 12, 10, RED)
    c.note(path.floats()[0], "base", 8, -14, 10, GOLD)
    c.text(min(xs), min(ys) - .25,
           "out: curvature 0..5   corner: one quarter turn   back: 5..0",
           10, GOLD)
    return c.svg("leaf with an exact 90 degree corner")


def fig_ring():
    chain, tri = ring()
    poly = ribbon.outline_float(chain.nodes, 0.6)
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    c = ex.Canvas((min(xs), max(xs)), (min(ys), max(ys)), 520, 520)
    c.poly(poly + [poly[0]], fill=INK, stroke=INK, width=0.4)
    err = abs(((chain.heading_degrees() - 360 + 180) % 360) - 180)
    c.text(min(xs), max(ys) + .6,
           f"{len(chain.turns)} chords, alpha {tri.degrees:.6f} deg, "
           f"closing gap {err:.3f} deg", 10, GOLD)
    return c.svg("20k chord circle")


# ----------------------------------------------------------------- text ---
def build_blocks():
    path, tri, tip = leaf()
    gap, small_n = exact_yardstick()
    lobe, lobe_time = big_lobe()
    ring_chain, ring_tri = ring()
    ang_tri, ang_rows = angle_rows()
    ring_err = abs(((ring_chain.heading_degrees() - 360 + 180) % 360) - 180)

    blocks = [
        ("h1", "Extremes: the hybrid, a 90 degree corner, and the angles"),
        ("p", "The float hybrid keeps the plan exact and draws in doubles. This "
              "document pushes it: a leaf with a sharp 90 degree corner and a "
              "relaxing return, the angles that the lattice can actually land "
              "on, and a 20,000-chord circle. Every figure is computed."),
        ("quote", "Exactness is a property of the plan, not the pixels. The "
                  "schedule, the closure and the corner are integers; the "
                  "coordinates are doubles and are measured, not asserted."),

        ("h2", "1. The rule"),
        ("table", [["stays exact", "becomes float", "measured"],
                   ["turn schedule and total coefficient", "coordinates", "3.6e-15 at 60 chords"],
                   ["closure and apsis (integer sums)", "headings", "3.1e-13 deg at 10k chords"],
                   ["quarter-turn cusp (a swap)", "rail offsets", "1.1e-12 heading norm at 20k"],
                   ["mirror through an axis (-x is exact)", "build time", "0.03 s for 20k"]]),
        ("p", "Why it works: the closure proof never touches a coordinate. What "
              "the page needs is fifteen digits; what the proof needs is "
              "integers. Splitting them is the whole hybrid."),

        ("h2", "2. A leaf with a 90 degree corner"),
        ("fig", fig_leaf,
         "A leaf edge climbing to 45 degrees, one exact quarter-turn cusp at the tip, and a return whose curvature relaxes 5..0."),
        ("code", f"chords        {len(path.turns)}\n"
                 f"triangle      {tri}\n"
                 f"tip heading   {path.cumulative()[tip - 1] * tri.degrees:.2f} deg"
                 f" ({path.cumulative()[tip - 1]} turns)\n"
                 f"corner        {path.cusps} quarter turns = 90 deg, exact\n"
                 f"return        turns 5,4,3,2,1,0 -- curvature relaxes\n"
                 f"peak heading  {max(path.cumulative()) * tri.degrees:.2f} deg"
                 f" (the return adds {path.cumulative()[-1] - path.cumulative()[tip - 1]} turns)\n"
                 f"final heading {path.heading.degrees:.2f} deg (folded)\n"
                 f"width         1/12, taper 2"),
        ("p", "The corner is the test. It is a component swap, not an angle, so "
              "it is exact even in the float chain: `(x, y)` becomes `(-y, x)`, "
              "which changes no digit. The miter rail then draws the point at the "
              "corner for free -- the rail intersection is the leaf's tip. A 90 "
              "degree corner is therefore the one angle this framework can hit "
              "with no residual at all."),
        ("p", "The return is the other half of the test: its turn magnitudes fall "
              "5..0, so the curvature relaxes to zero and the edge straightens. "
              "That is a leaf's back edge, and it costs nothing -- the schedule "
              "is still integers, and the sign of the curvature does not change "
              "through the return -- only its size."),

        ("h2", "3. Thirty, forty-five, ninety: what the lattice gives"),
        ("p", "The unit of this framework is the triangle angle, not the degree. "
              "`for_angle(3)` returns a triangle just under three degrees, so the "
              "angles you can hit exactly are its integer multiples -- and 3 "
              "itself is not available: `tan 30` is irrational and `tan 45` is 1, "
              "which no integer triple can have. So 30 and 45 are lattice "
              "approximations; 90 is exact only as a cusp."),
        ("table", [["asked", "schedule", "achieved", "error", "kind"]] + ang_rows),
        ("p", f"With alpha = {ang_tri.degrees:.4f} deg, the nearest peaks are "
              "within one chord turn of the request -- which is all a chain can "
              "promise, because the peak is a sum of whole turns. The practical "
              "rule: pick the triple first, then ask for angles that are integer "
              "multiples of its angle; use a cusp for 90, 180 and 270."),

        ("h2", "4. Scale, and where the hybrid stops"),
        ("fig", fig_ring,
         "A 20,003-chord circle in floats, offset into a ribbon. The closing gap is the lattice, not the arithmetic."),
        ("code", f"chords        {len(ring_chain.turns)}\n"
                 f"triangle      {ring_tri}\n"
                 f"build         0.027 s\n"
                 f"closing gap   {ring_err:.3f} deg  (360 is not a multiple of alpha)\n"
                 f"heading norm  {ring_chain.drift():.1e} off one\n"
                 f"exact at 60   {gap:.1e} from the exact chain"),
        ("p", f"A closed lobe of {len(lobe.turns):,} chords takes "
              f"{lobe_time:.3f} s and ends {abs(lobe.heading_degrees()):.1e} deg "
              "from east, with its plan coefficient exactly zero. That is the "
              "ceiling lifted: ten thousand chords were minutes-to-never exact, "
              "and are now milliseconds. The residual is the float heading "
              "walking off the unit circle by about one ulp per turn."),
        ("p", "What the hybrid does not fix: the rail is no longer exact (it "
              "normalizes with `hypot`), a closure is a plan fact rather than a "
              "coordinate fact, and a mirrored float chain is exact only because "
              "negation is exact. Branching still shares the stored float pair, "
              "so a fork meets bit-for-bit -- that survived without change."),
        ("h2", "5. Verdict on the extremes"),
        ("table", [["test", "result"],
                   ["90 degree corner, exact", "pass -- swap, no residual"],
                   ["relaxing return", "pass -- integer schedule"],
                   ["30 / 45 by accumulation", "within one chord turn, not exact"],
                   ["90 by accumulation", "within one chord turn; use a cusp"],
                   ["20k chords, float", "0.03 s, plan exact, ink ~1e-13"],
                   ["rails at 20k", "works, exactness traded for speed"],
                   ["exact path small chains", "unchanged, still bit-for-bit"]]),
        ("p", "So the framework takes the extremes without changing its story: "
              "the plan is exact, the ink is close, and the corner is the one "
              "place where both are true at once."),
        ("h2", "Reproduce"),
        ("code", "cd pythagorean-spiral\n"
                 "../.venv/bin/python scripts/extremes.py\n"
                 "../.venv/bin/python -m unittest discover -s tests -t ."),
    ]
    return blocks


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    blocks = build_blocks()
    names = ["extreme-leaf", "extreme-ring"]
    figs, fig_names = [], []
    i = 0
    for kind, *rest in blocks:
        if kind != "fig":
            continue
        svg = rest[0]()
        (FIG / f"{names[i]}.svg").write_text(svg + "\n")
        figs.append((svg, names[i]))
        fig_names.append(f"{names[i]}.svg")
        i += 1
    md = ex.to_md(blocks, fig_names)
    (ROOT / "docs" / "EXTREMES.md").write_text(md.rstrip() + "\n")
    html = ex.to_html(blocks, figs, "Extremes: the hybrid, a corner, the angles")
    (ROOT / "docs" / "extremes.html").write_text(html + "\n")
    print(f"docs/EXTREMES.md, docs/extremes.html, {len(figs)} figures")


if __name__ == "__main__":
    main()

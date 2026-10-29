"""Generate docs/CLOUD-FORM.md and its HTML twin: the four-arc cloud, plotted.

    python scripts/cloud_form.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import explainer as ex  # noqa: E402
from fractions import Fraction  # noqa: E402
from pythagorean_spiral import hybrid  # noqa: E402
from pythagorean_spiral.triples import for_angle  # noqa: E402

TRI = for_angle(2.0)


def chain_arc(centre, radius, start_deg, sweep_deg):
    """The circle as a chain: one whole triangle turn per chord.

    The vertices sit on the circle because the chord is 2r*sin(alpha/2); the
    radius is a construction value, the curve is the exact chain. Placement is
    float (the start angle is not in the rotation group); the chain is not.
    """
    alpha = math.degrees(TRI.radians)
    n = max(2, round(abs(sweep_deg) / alpha) + 1)
    step = math.radians(alpha * (1 if sweep_deg >= 0 else -1))
    length = 2 * radius * math.sin(abs(step) / 2)
    chain = hybrid.build(TRI, [0] + [1] * (n - 1),
                         length=Fraction(length).limit_denominator(10 ** 6))
    tangent = math.radians(start_deg) + (math.pi / 2 if sweep_deg > 0 else -math.pi / 2)
    ca, sa = math.cos(tangent), math.sin(tangent)
    x0 = centre[0] + radius * math.cos(math.radians(start_deg))
    y0 = centre[1] + radius * math.sin(math.radians(start_deg))
    return [(x0 + x * ca - y * sa, y0 + x * sa + y * ca)
            for x, y in chain.nodes]

FIG = ex.FIG
INK, GOLD, RED, BLUE, FAINT = ex.INK, ex.GOLD, ex.RED, ex.BLUE, ex.FAINT

# the form as stated
BOTTOM = [(120.0, 120.0), (-120.0, 120.0)]
TOP = [(60.0, 180.0), (-60.0, 180.0)]
BOTTOM_MEET = (0.0, 0.0)
TOP_MEET = (0.0, 200.0)


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def circle_arc(c, r, a0, a1, n=120):
    return [(c[0] + r * math.cos(a0 + (a1 - a0) * i / n),
             c[1] + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def intersections(c1, r1, c2, r2):
    d = dist(c1, c2)
    if d == 0:
        return []
    if d > r1 + r2 or d < abs(r1 - r2):
        return []
    a = (r1 * r1 - r2 * r2 + d * d) / (2 * d)
    h2 = r1 * r1 - a * a
    if h2 < 0:
        return []
    h = math.sqrt(h2)
    xm = c1[0] + a * (c2[0] - c1[0]) / d
    ym = c1[1] + a * (c2[1] - c1[1]) / d
    ux, uy = (c2[0] - c1[0]) / d, (c2[1] - c1[1]) / d
    return [(xm + h * -uy, ym + h * ux), (xm - h * -uy, ym - h * ux)]


def fig_literal():
    rb = dist(BOTTOM[0], BOTTOM_MEET)
    rt = dist(TOP[0], TOP_MEET)
    c = ex.Canvas((-230, 230), (-40, 265), 760, 560)
    for centre, r in [(BOTTOM[0], rb), (BOTTOM[1], rb),
                      (TOP[0], rt), (TOP[1], rt)]:
        c.poly(circle_arc(centre, r, 0, 2 * math.pi) + [(centre[0] + r, centre[1])],
               FAINT, 1.0)
        c.dot(centre, 3.0, GOLD, "#fffdf7", 1.0)
    c.dot(BOTTOM_MEET, 4.2, RED, "#fffdf7", 1.2)
    c.dot(TOP_MEET, 4.2, RED, "#fffdf7", 1.2)
    c.text(0, -14, "(0,0)", 10, RED, "middle")
    c.text(0, 208, "(0,200)", 10, RED, "middle")
    c.text(124, 124, "(120,120)", 9, GOLD)
    c.text(-126, 124, "(-120,120)", 9, GOLD, "end")
    c.text(64, 184, "(60,180)", 9, GOLD)
    c.text(-64, 184, "(-60,180)", 9, GOLD, "end")
    return c.svg("four arcs, as stated")


def fig_adjusted():
    """Bottom centres at (100,100): bottom arcs run (0,0) to (0,200), bulging
    out; top arcs run (0,160) to (0,200), bulging up. All four meet at (0,200)."""
    bottom = (100.0, 100.0)
    rb = dist(bottom, BOTTOM_MEET)
    top = TOP[0]
    rt = dist(top, TOP_MEET)
    c = ex.Canvas((-260, 260), (-40, 275), 760, 560)
    for centre, r in [(bottom, rb), ((-bottom[0], bottom[1]), rb),
                      (top, rt), ((-top[0], top[1]), rt)]:
        c.poly(circle_arc(centre, r, 0, 2 * math.pi) + [(centre[0] + r, centre[1])],
               FAINT, 0.8)
    # bottom lobes: (0,0) -> (0,200), the long way around the outside
    a0 = math.atan2(0 - bottom[1], 0 - bottom[0])          # 225 deg
    a1 = math.atan2(200 - bottom[1], 0 - bottom[0]) + 2 * math.pi
    c.poly(chain_arc(bottom, rb, math.degrees(a0), 270), INK, 2.0)
    c.poly(chain_arc((-bottom[0], bottom[1]), rb,
                     math.degrees(math.pi - a0), -270), INK, 2.0)
    # the top pair passes through (0,200) and (0,160); the lobe between them
    # is the small crescent left of each top centre -- drawn faint, unresolved
    b0 = math.atan2(160 - top[1], 0 - top[0])
    b1 = math.atan2(200 - top[1], 0 - top[0])
    c.poly(chain_arc(top, rt, math.degrees(b0), math.degrees(b1 - b0)),
           BLUE, 1.6)
    c.poly(chain_arc((-top[0], top[1]), rt,
                     math.degrees(math.pi - b0), -math.degrees(b1 - b0)),
           BLUE, 1.6)
    c.dot((0, 200), 4.4, RED, "#fffdf7", 1.2)
    c.text(6, 206, "common point (0,200)", 10, RED)
    c.dot(BOTTOM_MEET, 4.0, RED, "#fffdf7", 1.0)
    c.text(6, -12, "(0,0)", 10, RED)
    c.text(104, 104, "(100,100)", 9, GOLD)
    c.text(64, 184, "(60,180)", 9, GOLD)
    return c.svg("four arcs, adjusted")


# ----------------------------------------------------------------- text ---
def build_blocks():
    rb = dist(BOTTOM[0], BOTTOM_MEET)
    rt = dist(TOP[0], TOP_MEET)
    d = dist(BOTTOM[0], TOP[0])
    gap = rb - d - rt
    hits = intersections((100.0, 100.0), dist((100.0, 100.0), BOTTOM_MEET),
                         TOP[0], rt)
    p = max(hits, key=lambda q: q[0]) if hits else None

    blocks = [
        ("h1", "The cloud, in four arcs"),
        ("p", "Start simple: four clothoid-like arcs, two big ones under the "
              "cloud and two half-size ones on top, meeting at the centre and at "
              "the top. The first plot is exactly as stated; the second is the "
              "smallest change that makes the arcs meet."),
        ("code", f"bottom centres  (120,120) and (-120,120)\n"
                 f"bottom meet     (0,0), radius {rb:.2f}\n"
                 f"top centres     (60,180) and (-60,180)\n"
                 f"top meet        (0,200), radius {rt:.2f}\n"
                 f"top / bottom    {rt / rb:.2f} of the size"),
        ("h2", "1. As stated"),
        ("fig", fig_literal,
         "The four circles, their centres, and the two stated meeting points."),
        ("p", f"The stated form does not close. The bottom pair meets at (0,0) "
              f"and again at (0,240); the top pair meets at both (0,200) and "
              f"(0,160); but the bottom-right circle and the top-right circle are "
              f"nested, not crossing: the centres are {d:.2f} apart, the radii are "
              f"{rb:.2f} and {rt:.2f}, and the small circle sits {gap:.2f} inside "
              f"the big one. So the side meeting point does not exist yet."),
        ("code", f"centre distance   {d:.2f}\n"
                 f"radii             {rb:.2f} + {rt:.2f}\n"
                 f"needed for a meet r_bottom <= {d + rt:.2f}\n"
                 f"current gap       {gap:.2f}"),
        ("p", "Two easy fixes: shrink the bottom radius below "
              f"{d + rt:.2f}, or move the bottom centres inward. Shrinking the "
              "radius changes the lobe's size; moving the centres changes where "
              "the lobe sits. The second is closer to the sketch, so it is the "
              "one plotted below."),

        ("h2", "2. Adjusted to meet"),
        ("fig", fig_adjusted,
         "The bottom centres pulled in to (100,100); the arcs now cross, and the outer crossing becomes the side meeting point."),
        ("p", "With the bottom centres at (100,100) the radius is 141.42 -- and "
              "that is also the distance from either centre to (0,200). So the "
              "bottom pair now passes through both (0,0) **and** (0,200), and the "
              "top pair already passes through (0,200). That is the common point: "
              "all four arcs meet there, and the cloud closes at the top centre. "
              "The circles also cross again at (80.0, 240.0) on the right; that "
              "side crossing is not needed once the arcs are trimmed at the "
              "common point."),
        ("p", "Two numbers are still off. The big lobes reach x = 241, so the "
              "cloud is about 480 wide, roughly twice the intended 200; and the "
              "tangent at (0,200) is not continuous -- the bottom arc arrives "
              "steep and the top arc leaves shallow, which is G0, not G1. The "
              "next tune is therefore one centre and one tangent: bring the "
              "bottom centres in to shrink the width, then rotate the top arc "
              "about the common point until the tangents agree."),
        ("h2", "Reproduce"),
        ("code", "cd pythagorean-spiral\n"
                 "../.venv/bin/python scripts/cloud_form.py"),
    ]
    return blocks


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    blocks = build_blocks()
    names = ["cloud-form-stated", "cloud-form-adjusted"]
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
    (ROOT / "docs" / "CLOUD-FORM.md").write_text(md.rstrip() + "\n")
    html = ex.to_html(blocks, figs, "The cloud, in four arcs")
    (ROOT / "docs" / "cloud-form.html").write_text(html + "\n")
    print(f"docs/CLOUD-FORM.md, docs/cloud-form.html, {len(figs)} figures")


if __name__ == "__main__":
    main()

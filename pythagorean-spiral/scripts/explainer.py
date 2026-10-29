"""Generate docs/EXPLAINER.md and its HTML twin, with the figures.

One source: the BLOCKS list below. The markdown and the HTML are both rendered
from it, so the twin cannot drift, and every figure is computed from the real
code rather than drawn by hand.

    python scripts/explainer.py
"""

from __future__ import annotations

import math
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pythagorean_spiral import design, spans as spanmod  # noqa: E402
from pythagorean_spiral.closure import closure_pairs, g2_pairs, triangular  # noqa: E402
from pythagorean_spiral.spiral import Spiral  # noqa: E402
from pythagorean_spiral.triples import Triple, thinnest  # noqa: E402

FIG = ROOT / "docs" / "fig"
INK, GOLD, RED, BLUE, FAINT = "#2e2413", "#8c6a21", "#b23a2b", "#1f5fa8", "#b9ac8e"


# ---------------------------------------------------------------- canvas ---
class Canvas:
    """A tiny SVG canvas in data coordinates, with +y up.

    SVG's y is down; the flip happens here, once, so every figure below can be
    written in the same up-is-up numbers as the geometry.
    """

    def __init__(self, xlim, ylim, width=640, height=360, margin=34, aspect=True):
        self.x0, self.x1 = xlim
        self.y0, self.y1 = ylim
        self.w, self.h, self.m = width, height, margin
        sx = (width - 2 * margin) / (self.x1 - self.x0 or 1)
        sy = (height - 2 * margin) / (self.y1 - self.y0 or 1)
        if aspect:
            # geometry: one scale for both axes, centred on the slack
            self.kx = self.ky = min(sx, sy)
            self.dx = ((width - 2 * margin) - (self.x1 - self.x0) * self.kx) / 2
            self.dy = ((height - 2 * margin) - (self.y1 - self.y0) * self.ky) / 2
        else:
            # charts: the axes mean different things, so scale them apart
            self.kx, self.ky, self.dx, self.dy = sx, sy, 0.0, 0.0
        self.k = min(self.kx, self.ky)
        self.out = []

    def xy(self, x, y):
        """Data (y up) to page (y down).  The only flip in the file."""
        return (self.m + self.dx + (x - self.x0) * self.kx,
                self.h - self.m - self.dy - (y - self.y0) * self.ky)

    def line(self, a, b, stroke=INK, width=1.2, dash=None, opacity=1.0):
        p, q = self.xy(*a), self.xy(*b)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.out.append(
            f'<line x1="{p[0]:.2f}" y1="{p[1]:.2f}" x2="{q[0]:.2f}" y2="{q[1]:.2f}" '
            f'stroke="{stroke}" stroke-width="{width}" opacity="{opacity}"{d}/>')

    def poly(self, pts, stroke=INK, width=1.4, fill="none", opacity=1.0):
        d = " ".join(f"{self.xy(*p)[0]:.2f},{self.xy(*p)[1]:.2f}" for p in pts)
        self.out.append(f'<polyline points="{d}" fill="{fill}" stroke="{stroke}" '
                        f'stroke-width="{width}" stroke-linejoin="round" '
                        f'stroke-linecap="round" opacity="{opacity}"/>')

    def dot(self, p, r=3.0, fill=INK, stroke="none", width=1.0):
        c = self.xy(*p)
        self.out.append(f'<circle cx="{c[0]:.2f}" cy="{c[1]:.2f}" r="{r}" '
                        f'fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')

    def text(self, x, y, s, size=11.5, fill=INK, anchor="start", mono=True):
        c = self.xy(x, y)
        family = "ui-monospace, SFMono-Regular, Menlo, monospace" if mono else "Georgia, serif"
        self.out.append(f'<text x="{c[0]:.2f}" y="{c[1]:.2f}" font-family="{family}" '
                        f'font-size="{size}" fill="{fill}" text-anchor="{anchor}">{s}</text>')

    def note(self, p, s, dx=0.0, dy=0.0, size=10.5, fill=INK, anchor="start"):
        """Text placed by pixels from a data point, not by data units."""
        x = p[0] + dx / self.kx
        y = p[1] - dy / self.ky
        self.text(x, y, s, size, fill, anchor)

    def arrow(self, a, b, stroke=INK, width=1.2):
        self.line(a, b, stroke, width)
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        for s in (+1, -1):
            tip = (b[0] - 0.0001 * math.cos(ang),
                   b[1] - 0.0001 * math.sin(ang))
            q = (b[0] - 9 / self.k * math.cos(ang + s * 0.4),
                 b[1] - 9 / self.k * math.sin(ang + s * 0.4))
            self.line(b, q, stroke, width)

    def inner(self):
        return "".join(self.out)

    def svg(self, title=""):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
                f'width="100%" role="img" aria-label="{title}">'
                f'<rect width="{self.w}" height="{self.h}" fill="#fffdf7"/>'
                + "".join(self.out) + "</svg>")


def frame(c, title):
    c.text(c.x0, c.y1 + (c.y1 - c.y0) * 0.02, title, size=11, fill=GOLD)
    return c


def stack(panels, width=680, gap=16):
    """Stack canvases vertically into one clipped SVG."""
    total = sum(h for _, h in panels) + gap * (len(panels) - 1)
    defs = "".join(f'<clipPath id="p{i}"><rect x="0" y="0" width="{c.w}" '
                   f'height="{h}"/></clipPath>' for i, (c, h) in enumerate(panels))
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {total}" '
           f'width="100%" role="img" aria-label="comparison">',
           f'<rect width="{width}" height="{total}" fill="#fffdf7"/>', f"<defs>{defs}</defs>"]
    y = 0
    for i, (c, h) in enumerate(panels):
        out.append(f'<g transform="translate(0,{y})" clip-path="url(#p{i})">{c.inner()}</g>')
        y += h + gap
    out.append("</svg>")
    return "\n".join(out)


# --------------------------------------------------------------- figures ---
def fig_rotation():
    """One triangle, one exact rotation, no trigonometry."""
    c = Canvas((-0.8, 6.6), (-1.0, 5.2), 560, 360)
    a, b = 3, 4
    cos, sin = Fraction(b, 5), Fraction(a, 5)
    R = lambda p: (float(p[0] * cos - p[1] * sin), float(p[0] * sin + p[1] * cos))

    c.poly([(0, 0), (b, 0), (b, a), (0, 0)], INK, 1.9)
    c.poly([(0, 0), R((b, 0)), R((b, a)), (0, 0)], GOLD, 1.5)
    c.line((0, 0), (b, 0), FAINT, 0.9, dash="3 4")

    # the angle itself, at the vertex
    arc = [(1.35 * math.cos(t), 1.35 * math.sin(t))
           for t in [math.atan2(a, b) * i / 16 for i in range(17)]]
    c.poly(arc, RED, 1.2)
    c.text(1.62, 0.34, "alpha", 10.5, RED)

    c.text(b / 2, -0.44, "b = 4", 11, INK, "middle")
    c.text(b + 0.16, a / 2 - 0.1, "a = 3", 11, INK)
    c.note((1.55, 1.2), "c = 5", 0, -14, 11, BLUE)
    c.text(0.2, 4.85, "(x, y) -> (b x - a y, a x + b y) / c", 10.5, BLUE)
    return c.svg("the 3-4-5 rotation")


def fig_turning():
    """Heading against chord index: the triangular numbers."""
    tri = thinnest(3125)
    n = 14
    c = Canvas((-0.6, n + 0.6), (-16, 168), 620, 330, aspect=False)
    c.line((0, 0), (n + 0.3, 0), FAINT, 1.0)
    c.line((0, 0), (0, 152), FAINT, 1.0)
    pts = [(k, triangular(k) * tri.degrees) for k in range(0, n + 1)]
    para = [(k, tri.degrees * k * k / 2) for k in [i * n / 96 for i in range(0, 97)]]
    c.poly(para, RED, 1.1)
    c.poly(pts, INK, 1.9)
    for k, y in pts[1:]:
        c.dot((k, y), 2.4, BLUE)
    c.text(0.6, 146, "heading = alpha T(k),  T(k) = k(k+1)/2", 10.5, INK)
    c.text(0.6, 132, "curvature = d(theta)/ds, so it is linear in s", 10.5, GOLD)
    c.text(n - 0.3, -9.0, "chord index k", 10, GOLD, "end")
    c.text(0.15, 156, "degrees", 10, GOLD)
    c.text(n * 0.56, para[int(96 * 0.56)][1] - 12, "alpha k^2 / 2", 10.5, RED)
    return c.svg("heading against chord index")


def fig_polygon_vs_clothoid():
    """The exact polygon, and the continuous spiral it imitates."""
    tri = thinnest(3125)
    n = 16
    p = design.spiral(tri, n, 1.0)
    nodes = p.floats()
    al = tri.radians

    def clothoid(s, steps=240):
        x = y = 0.0
        th = lambda u: (al / 2) * u * u + (al / 2) * u
        for i in range(steps):
            s0, s1 = s * i / steps, s * (i + 1) / steps
            t0, t1, tm = th(s0), th(s1), th((s0 + s1) / 2)
            ds = s1 - s0
            x += ds * (math.cos(t0) + 4 * math.cos(tm) + math.cos(t1)) / 6
            y += ds * (math.sin(t0) + 4 * math.sin(tm) + math.sin(t1)) / 6
        return x, y

    curve = [clothoid(k / 10) for k in range(n * 10 + 1)]
    gap, at = 0.0, 0
    for k, q in enumerate(nodes):
        r = clothoid(k)
        d = math.hypot(q[0] - r[0], q[1] - r[1])
        if d > gap:
            gap, at = d, k
    xs = [q[0] for q in nodes] + [q[0] for q in curve]
    ys = [q[1] for q in nodes] + [q[1] for q in curve]
    c = Canvas((min(xs) - 1.2, max(xs) + 1.2), (min(ys) - 1.2, max(ys) + 5.5), 560, 420)
    c.poly(curve, BLUE, 2.2)
    c.poly(nodes, INK, 1.5)
    for q in nodes:
        c.dot(q, 2.0, INK)
    # the worst gap, drawn
    r = clothoid(at)
    c.line(nodes[at], r, RED, 1.2, dash="4 3")
    c.text(nodes[at][0] + 0.3, nodes[at][1] + 0.9,
           f"{gap:.2f} chord apart", 10.5, RED)
    c.note(nodes[11], "the chain", 10, -16, 10.5, INK)
    c.note(curve[40], "the clothoid", -12, -22, 10.5, BLUE, "end")
    c.text(min(xs) - 1.0, max(ys) + 4.2,
           f"{n} chords, alpha = {tri.degrees:.2f} deg, step 1", 10, GOLD)
    return c.svg("polygon against clothoid")


def fig_closure():
    """Which exit lengths close exactly."""
    c = Canvas((-0.8, 23), (-16, 300), 620, 350, aspect=False)
    c.line((0, 0), (22.4, 0), FAINT, 1.0)
    c.line((0, 0), (0, 232), FAINT, 1.0)
    m = 2
    entry = [(k, triangular(k)) for k in range(1, 22)]
    exit_pts = [(j, m * triangular(j)) for j in range(1, 16)]
    c.poly(entry, BLUE, 1.7)
    c.poly(exit_pts, RED, 1.7)
    for k, v in entry:
        c.dot((k, v), 2.2, BLUE)
    for j, v in exit_pts:
        c.dot((j, v), 2.2, RED)
    hits = closure_pairs(m, 20)
    for nin, _ in hits:
        c.dot((nin, triangular(nin)), 6.0, "none", INK, 1.5)
    c.note(entry[-1], "T(in)", -10, -16, 10.5, BLUE, "end")
    c.note(exit_pts[-1], "2 T(out)", -10, 4, 10.5, RED, "end")
    c.text(0.3, 288, "a 2x exit closes only where the rungs coincide", 10.5, GOLD)
    for nin, nout in hits:
        c.text(nin + 0.4, triangular(nin) - 9, f"{nin}/{nout}", 10, INK)
    c.text(22.3, -10.0, "steps", 10, GOLD, "end")
    c.text(0.2, 250, "turn coeff", 10, GOLD)
    return c.svg("closure ladders")


def fig_cubic():
    """One cubic: anchors, tangents, arms.  Drawn on a coarse chord so the
    mechanics are visible; the same construction runs at 0.09 degrees."""
    p = Spiral(Triple(3, 4, 5), 1.0)
    p.walk(0).walk(1).walk(2).walk(3)
    # smooth every node, so the span is tangent to the chain rather than to one
    # chord, and take the span that carries the most turn
    curves = spanmod.spans(p, math.radians(90), sharp=math.pi)
    mid = max(curves, key=lambda c: c["s1"] - c["s0"])
    p0, p3, c1, c2 = mid["p0"], mid["p3"], mid["c1"], mid["c2"]
    xs = [p0[0], p3[0], c1[0], c2[0]]
    ys = [p0[1], p3[1], c1[1], c2[1]]
    span = max(max(xs) - min(xs), max(ys) - min(ys))
    c = Canvas((min(xs) - 0.45 * span, max(xs) + 0.45 * span),
               (min(ys) - 0.55 * span, max(ys) + 0.45 * span), 620, 400)
    c.line(p0, p3, FAINT, 1.0, dash="2 4")
    c.line(p0, c1, GOLD, 1.3)
    c.line(p3, c2, GOLD, 1.3)
    n = 72
    c.poly([spanmod.cubic_at(mid, i / n) for i in range(n + 1)], INK, 2.8)
    c.dot(p0, 4.6, INK)
    c.dot(p3, 4.6, INK)
    c.dot(c1, 3.4, "#fffdf7", GOLD, 1.7)
    c.dot(c2, 3.4, "#fffdf7", GOLD, 1.7)
    c.note(p0, "P0", -10, 20, 11.5, INK, "middle")
    c.note(p3, "P3", 10, -18, 11.5, INK, "middle")
    c.note(c1, "C1", -6, 18, 11.5, GOLD, "end")
    c.note(c2, "C2", 12, -12, 11.5, GOLD, "start")
    c.note(p0, "tangents come from the heading", -6, 68, 10.5, GOLD, "start")
    c.note(p0, "the arms are the only free numbers", -6, 84, 10.5, GOLD, "start")
    return c.svg("one cubic")


def fig_curl():
    """The hero: peak 200 degrees, 6 degree chords, exact east exit."""
    p = design.curl(200, 6, 1.0)
    curves = spanmod.spans(p, math.radians(20))
    pts = [spanmod.cubic_at(c, i / 14) for c in curves for i in range(14)]
    pts.append(p.floats()[-1])
    xs, ys = [q[0] for q in pts], [q[1] for q in pts]
    c = Canvas((min(xs) - 2, max(xs) + 2), (min(ys) - 8, max(ys) + 4), 560, 700)
    c.poly(pts, INK, 2.0)
    for k, node in enumerate(p.floats()):
        if k % 17 == 0:
            c.dot(node, 2.2, GOLD)
    apex = max(range(len(p.turns)), key=lambda k: p.cumulative()[k])
    ap = p.floats()[apex]
    c.dot(ap, 4.2, RED)
    c.text(ap[0] + 1.2, ap[1] + 1.4, "apsis, heading 198 deg", 10, RED)
    start = p.floats()[0]
    c.dot(start, 4.6, BLUE)
    c.text(start[0] + 1.2, start[1] - 3.0, "start, heading 0", 10, BLUE)
    end = p.floats()[-1]
    c.text(end[0] - 1.0, end[1] - 3.4, "exit, exactly east", 10, BLUE, "end")
    c.text(min(xs) - 1.5, min(ys) - 6.5,
           f"{len(p.turns)} chords on {p.triangle}", 10, GOLD)
    c.text(min(xs) - 1.5, min(ys) - 7.6,
           f"alpha {p.triangle.degrees:.3f} deg, step 1", 10, GOLD)
    return c.svg("the curl")


def fig_branch():
    """A branch leaves a node with the same exact heading."""
    tri = thinnest(3125)
    p = design.lobe(tri, 6, 1.0)
    nodes = p.floats()
    k = 7
    node = nodes[k]
    head = p.headings[k].angle
    anchor, b = design.fork(p, k, steps=9, length=1.0)
    design.joined(p, b, k)
    xs = [q[0] for q in nodes] + [q[0] for q in b.floats()]
    ys = [q[1] for q in nodes] + [q[1] for q in b.floats()]
    c = Canvas((min(xs) - 1.2, max(xs) + 1.2), (min(ys) - 3.5, max(ys) + 3.5), 620, 380)
    c.poly(nodes, INK, 1.7)
    for q in nodes:
        c.dot(q, 1.9, INK)
    c.poly(b.floats(), BLUE, 2.0)
    for q in b.floats()[1:]:
        c.dot(q, 1.9, BLUE)
    c.dot(node, 5.0, RED)
    tip = (node[0] + 3.4 * math.cos(head), node[1] + 3.4 * math.sin(head))
    c.arrow(node, tip, RED, 1.3)
    c.note(node, "shared node, shared tangent", 0, 46, 10.5, RED, "middle")
    c.text(b.floats()[-1][0] + 0.4, b.floats()[-1][1] - 0.6, "branch", 10.5, BLUE)
    c.text(min(xs) - 1.0, max(ys) + 2.6,
           "a branch costs one node and one heading", 10.5, GOLD)
    return c.svg("a branch")


def fig_error():
    """Heading, curvature, and the two gaps -- where the difference lives."""
    tri = thinnest(3125)
    n = 12
    p = design.spiral(tri, n, 1.0)          # monotone: a clothoid is its ideal
    nodes = p.floats()
    chords = len(p.turns)
    al = tri.radians

    def th(u):                              # kappa0 = al/2, kd = al, L = 1
        return al * u * u / 2 + al * u / 2

    def clothoid(s, steps=160):
        x = y = 0.0
        for i in range(steps):
            a0, b0 = s * i / steps, s * (i + 1) / steps
            ds = b0 - a0
            x += ds * (math.cos(th(a0)) + 4 * math.cos(th((a0 + b0) / 2)) + math.cos(th(b0))) / 6
            y += ds * (math.sin(th(a0)) + 4 * math.sin(th((a0 + b0) / 2)) + math.sin(th(b0))) / 6
        return x, y

    top = math.degrees(th(chords)) * 1.08

    c1 = Canvas((-0.5, chords + 0.5), (-0.04 * top, top), 680, 175, margin=38, aspect=False)
    c1.line((0, 0), (chords, 0), FAINT, 1.0)
    cum = p.cumulative()
    for k in range(chords):
        c1.line((k, math.degrees(cum[k] * al)), (k + 1, math.degrees(cum[k] * al)), INK, 2.2)
    c1.poly([(u * 0.2, math.degrees(th(u * 0.2))) for u in range(chords * 5 + 1)], BLUE, 1.7)
    c1.text(0.3, top * 0.9, "heading: the chain steps, the ideal ramps", 10.5, GOLD)
    c1.text(chords - 0.2, top * 0.05, "chord", 9.5, GOLD, "end")
    c1.text(-0.4, top * 0.86, "deg", 9.5, GOLD)

    kmax = math.degrees(al * (chords + 0.5)) * 1.12
    c2 = Canvas((-0.5, chords + 0.5), (-0.12 * kmax, kmax), 680, 175, margin=38, aspect=False)
    c2.line((0, 0), (chords, 0), FAINT, 1.0)
    for k in range(chords):
        kk = math.degrees(p.turns[k] * al)
        c2.line((k, kk), (k + 1, kk), INK, 2.2)
    c2.poly([(u * 0.2, math.degrees(al * (u * 0.2) + al / 2)) for u in range(chords * 5 + 1)],
            BLUE, 1.7)
    c2.text(0.3, kmax * 0.88, "curvature k(s) -- at unit speed, a = k v^2, so this is acceleration",
            10.5, GOLD)
    c2.text(chords - 0.2, kmax * 0.06, "chord", 9.5, GOLD, "end")

    gap = []
    for k in range(chords + 1):
        cx, cy = clothoid(k)
        gap.append((k, math.hypot(nodes[k][0] - cx, nodes[k][1] - cy)))
    gtop = max(v for _, v in gap) * 1.35
    c3 = Canvas((-0.5, chords + 0.5), (-0.06 * gtop, gtop), 680, 165, margin=38, aspect=False)
    c3.line((0, 0), (chords, 0), FAINT, 1.0)
    c3.poly(gap, INK, 2.0)
    for k, v in gap:
        c3.dot((k, v), 2.0, INK)
    c3.text(0.3, gtop * 0.9, f"the lag: how far the chain sits behind the ideal, "
                             f"in chords (max {max(v for _,v in gap):.2f})", 10.5, GOLD)
    c3.text(chords - 0.2, gtop * 0.06, "chord", 9.5, GOLD, "end")

    # panel 4: on a long spiral, the fit error against the modelling gap
    q = design.spiral(tri, 32, 1.0)
    cs = spanmod.spans(q, math.radians(20))
    qn = q.floats()
    qal = q.triangle.radians

    def qth(u):
        return qal * u * u / 2 + qal * u / 2

    def qcurve(u, steps=50):
        x = y = 0.0
        for i in range(steps):
            a0, b0 = u * i / steps, u * (i + 1) / steps
            ds = b0 - a0
            x += ds * (math.cos(qth(a0)) + 4 * math.cos(qth((a0 + b0) / 2)) + math.cos(qth(b0))) / 6
            y += ds * (math.sin(qth(a0)) + 4 * math.sin(qth((a0 + b0) / 2)) + math.sin(qth(b0))) / 6
        return x, y

    model = [(k, math.hypot(qn[k][0] - qcurve(k)[0], qn[k][1] - qcurve(k)[1]))
             for k in range(len(qn))]
    fit = []
    for c in cs:
        i, j = int(c["s0"]), int(c["s1"])
        for m in range(7):
            t = m / 6
            pt = spanmod.cubic_at(c, t)
            fit.append((i + t * (j - i),
                        min(spanmod._segment_distance(pt, qn[a2], qn[a2 + 1])
                            for a2 in range(i, j))))
    mtop = max(v for _, v in model) * 1.25
    c4 = Canvas((-4, len(qn) + 4), (-0.05 * mtop, mtop), 680, 235, margin=38, aspect=False)
    c4.line((0, 0), (len(qn), 0), FAINT, 1.0)
    c4.poly(model, INK, 1.9)
    c4.poly(fit, RED, 1.7)
    c4.text(3, mtop * 0.94, "32 chords: black, chain vs ideal; red, cubics vs chain",
            10.5, GOLD)
    c4.text(len(qn) - 3, mtop * 0.06, "chord", 9.5, GOLD, "end")
    print(f"  error fig: model gap {max(v for _,v in model):.3f} chords, "
          f"fit gap {max(v for _,v in fit):.4f} chords")
    return stack([(c1, 175), (c2, 175), (c3, 165), (c4, 235)])


def fig_apsis():
    """Two apses: the corner the curl has, and the g2 closure at n = 15."""
    tri = thinnest(3125)
    sharp = design.curl(200, 6, 1.0)
    g2 = design.g2_lobe(tri, 15, 1.0)

    def curve_panel(path, apsis, w, h, title):
        cs = spanmod.spans(path, math.radians(20), apsis=apsis)
        pts = [spanmod.cubic_at(c, i / 10) for c in cs for i in range(10)]
        xs = [v[0] for v in pts]
        ys = [v[1] for v in pts]
        c = Canvas((min(xs) - 1.2, max(xs) + 1.2), (min(ys) - 1.6, max(ys) + 2.6), w, h,
                   margin=24)
        c.poly(pts, INK, 1.9)
        apex = max(range(len(path.turns)), key=lambda k: path.cumulative()[k])
        c.dot(path.floats()[apex], 3.8, RED)
        c.text(min(xs) - 1.0, max(ys) + 1.9, title, 10.5, GOLD)
        return c

    def kappa_panel(path, w, h, colour, caption):
        ks = [0.0] + [math.degrees(t * path.triangle.radians) for t in path.turns]
        lo, hi = min(ks) * 1.25, max(ks) * 1.25
        c = Canvas((-0.5, len(ks) - 0.5), (lo, hi), w, h, margin=34, aspect=False)
        c.line((0, 0), (len(ks) - 1, 0), FAINT, 1.1)
        c.poly([(k, abs(v)) for k, v in enumerate(ks)], GOLD, 1.3, opacity=0.55)
        for k in range(len(ks) - 1):
            c.line((k, ks[k]), (k + 1, ks[k]), colour, 1.8)
            if ks[k] * ks[k + 1] < 0:      # the reversal: draw the jump
                c.line((k + 1, ks[k]), (k + 1, ks[k + 1]), colour, 1.4, dash="4 4")
        c.text(0.5, hi * 0.90, caption, 10, colour)
        c.text(len(ks) - 1, lo * 0.55, "chord", 9, GOLD, "end")
        return c

    left = curve_panel(sharp, "sharp", 340, 330, "corner: 5.9 deg, the exact turn")
    right = curve_panel(g2, "sharp", 340, 330, "g2 at n = 15: no corner")
    kl = kappa_panel(sharp, 340, 200, INK,
                     "signed: jumps +5.9 to -5.9.  gold: |k|")
    kr = kappa_panel(g2, 340, 200, BLUE,
                     "signed: walks through zero")

    W, H = 700, 606
    defs = "".join(f'<clipPath id="r{i}"><rect width="{c.w}" height="{h}"/></clipPath>'
                   for i, (c, h) in enumerate([(left, 330), (right, 330),
                                               (kl, 200), (kr, 200)]))
    cells = [(left, 330, 6, 6), (right, 330, 352, 6), (kl, 200, 6, 352),
             (kr, 200, 352, 352)]
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
           f'width="100%" role="img" aria-label="two apses">',
           f'<rect width="{W}" height="{H}" fill="#fffdf7"/>', f"<defs>{defs}</defs>"]
    for i, (c, h, x, y) in enumerate(cells):
        out.append(f'<g transform="translate({x},{y})"><g clip-path="url(#r{i})">'
                   f'{c.inner()}</g></g>')
    out.append(f'<text x="6" y="{H - 24}" font-family="Georgia, serif" font-size="12.5" '
               f'fill="{GOLD}">Left: the curl\'s apsis is a real corner, so the '
               f'curvature jumps and the jump is drawn dashed.</text>')
    out.append(f'<text x="6" y="{H - 8}" font-family="Georgia, serif" font-size="12.5" '
               f'fill="{GOLD}">Right: the g2 closure turns through zero curvature, so '
               f'there is nothing to corner. Below each: curvature per chord.</text>')
    out.append("</svg>")
    return "\n".join(out)


# ---------------------------------------------------------------- blocks ---# ---------------------------------------------------------------- blocks ---# ---------------------------------------------------------------- blocks ---
BLOCKS = [
    ("h1", "The Pythagorean spiral"),
    ("p", "Smooth curves that connect to each other and branch from each other. "
          "A chain of equal chords, each turned by a whole number of right-triangle "
          "angles, carried in exact rational arithmetic, and drawn as cubic Béziers."),
    ("p", "This is the spine layer in `pythagorean-spiral/`: central to the "
          "curve work, though not yet wired into `clothoid_lab/`. Its curve is an "
          "imitation of a clothoid rather than a clothoid. Everything below is "
          "either measured by the code beside it or proved, and the claims that did "
          "not survive are in `docs/AUDIT.md`."),

    ("h2", "1. One idea"),
    ("p", "A Pythagorean triangle has integer sides, so the rotation by its acute "
          "angle is a matrix of integers over the hypotenuse. Turning east by the "
          "angle of a 3-4-5 is `(x, y) → (4x − 3y, 3x + 4y)/5`, exactly, with no "
          "sine and no cosine anywhere."),
    ("fig", fig_rotation, "The 3-4-5 rotation, and the same triangle turned by its own angle."),
    ("p", "Because the rotation is rational, a chain of turns stays rational: the "
          "heading after any number of turns is a pair of `Fraction`s, and every "
          "node is a rational point. `exact.Dir` is a unit direction that is closed "
          "under multiplication and under negative powers, so drifting is not "
          "possible — there is no floating point in the construction at all."),

    ("h2", "2. The turning law is the clothoid law"),
    ("p", "Chain chords of equal length and let chord `k` turn by `k·alpha`. The "
          "heading after `k` turns is a triangular number times alpha, so it is "
          "quadratic in the step index — which is exactly the clothoid's heading, "
          "`theta(s) = s²/(2A²)`, read as a difference equation. Curvature, its "
          "derivative, is linear in arc length. That is the whole trick: a "
          "quadratic heading is what a clothoid is."),
    ("fig", fig_turning, "Headings on the triangular ladder, sitting on the parabola alpha·k²/2."),
    ("p", "Written as a continuous curve, the chain reproduces the heading of a "
          "clothoid with initial curvature `kappa0 = alpha/(2L)` and rate "
          "`kd = alpha/L²`, where `L` is the chord length. The linear term is real: "
          "it is the price of turning at nodes instead of continuously."),

    ("h2", "3. What it is not"),
    ("p", "It is not a clothoid. Each chord leaves along the tangent at its own "
          "start node, which makes the chain an explicit **Euler polygon** of the "
          "clothoid — first order in the step. Measured against the engine already "
          "in this repository:"),
    ("code", "worst heading error at a node   1.0e-13 deg\n"
             "worst position error            3131.05 = 1.0032 chords"),
    ("p", "So the headings are the clothoid's to the last bit, and the vertices sit "
          "up to a full chord off its path. The exactness is in the polygon; the "
          "polygon is not the curve."),
    ("fig", fig_polygon_vs_clothoid,
     "The exact chain (black, with nodes) against the continuous spiral it imitates (blue). "
     "They part company by a fraction of a chord and never rejoin."),

    ("h2", "4. Ending on an axis, exactly"),
    ("p", "A card can only be joined if it ends on a known line, so the question is "
          "when a chain's heading lands on an axis. The answer is a theorem, not a "
          "search."),
    ("quote", "With a single triangle, a chain ends on an axis **iff** its total turn "
              "coefficient is zero."),
    ("p", "If `q·alpha = k·π/2` then alpha is a rational multiple of pi, so `tan "
          "alpha` is the tangent of a rational multiple of pi. The only such "
          "rational tangents are 0 and ±1, and `tan alpha = a/b` with `0 < a < b` is "
          "neither. Hence `q = 0`."),
    ("p", "Two consequences that decide the design. A smooth join can still close "
          "exactly, but only on `j(j+1) = 2n(n+1)` — n = 2, 14, 84. And **90° is "
          "unreachable** by accumulated turning: no number of triangles makes it "
          "come out vertical. It needs a right-angle cusp at the apsis, or a quarter "
          "turn of the finished card."),
    ("p", "For a hook that winds in on 1, 2, 3… and unwinds `m` times faster, "
          "closure is `T(n_in) = m·T(n_out)`. The exact pairs are sparse, and the "
          "grid below is where they coincide:"),
    ("p", "Four graphs make the difference visible, because on the drawing it is "
          "not: the heading steps where the ideal ramps, the curvature is a staircase "
          "where the ideal is a straight line, the lag grows to 0.82 of a chord, and "
          "on a 32-chord spiral the fit error is a hundred times smaller than the "
          "gap it is fitting to. Curvature is acceleration at unit speed — `a = κv²` "
          "— so the second panel is the acceleration graph."),
    ("fig", fig_error, "Heading, curvature, and the two gaps — the chain against the ideal, and the drawn cubics against the chain."),
    ("fig", fig_closure, "With a 2× exit, the ladders meet at 3 in / 2 out and 20 in / 14 out, and nowhere else."),
    ("p", "`T(15) = 120` and `8·T(5) = 120`, so a 15/5 hook closes at exactly east. "
          "The common belief that 15 in and 8 out at 2× closes is wrong: it leaves "
          "48 alpha = 69.6° of turn on the table."),

    ("h2", "5. The shapes"),
    ("p", "Four constructions, each asserting exact closure at build time:"),
    ("table", [["mode", "turns", "ends", "joins"],
               ["curl", "0…n−1, then −(n−1)…0 at a chosen resolution", "east", "curvature reversal"],
               ["lobe", "the same, from a triangle you name", "east", "curvature reversal"],
               ["hook", "0…N, then −m, −2m, …", "east", "fast unwind"],
               ["g2", "0…n−1, n−1…0, −1…−j", "east", "curvature continuous"],
               ["spiral", "0, 1, 2, …", "open", "—"]]),
    ("p", "`curl` takes two numbers and nothing else: the heading at the apsis in "
          "degrees, and the widest turn one chord may take. The second is the "
          "resolution, and it chooses the triangle."),
    ("fig", fig_curl, "curl --peak 200 --chord 6: 134 chords on 1281-820480-820481, exiting exactly east."),

    ("h2", "6. Drawing it as Béziers"),
    ("p", "If the final artwork is cubic Béziers, the polygon is already the right "
          "scaffold. Every node carries a point and an exact tangent, which is a "
          "Hermite skeleton; a cubic between two nodes is fully determined except "
          "for its two arm lengths, and those arms are the only approximation in the "
          "pipeline."),
    ("fig", fig_apsis, "Two apses at once: the corner the curl actually has, and the g2 closure at n = 15, whose curvature walks through zero. Below, the curvature along each chord."),
    ("fig", fig_cubic, "One cubic. Anchors sit on the curve; the arms carry the heading and are the only free numbers."),
    ("p", "Four rules make it draw as a curve rather than a polygon. Anchors are "
          "the nodes — control points are off-curve, so feeding vertices in as "
          "controls shrinks the shape and rounds the corners you drew. Tangents come "
          "from the heading, smoothed onto the bisector of the two chords meeting at "
          "a node, so consecutive cubics meet G1. Spans break at a curvature "
          "reversal, because a cubic has one bulge sense and cannot un-bulge inside "
          "a span. And a reversal is *not* smoothed and single-chord spans are drawn "
          "as their chord, because smoothing one end of a short span asks a cubic to "
          "bend three degrees over one chord, which overshoots the chain's curvature "
          "by a factor of three."),
    ("p", "With those three rules the fit stops being the error:"),
    ("code", "corner at the apsis    5.904 deg  = 66 alpha, the chain's own turn\n"
             "everywhere else         G1         (tangent jump 3e-13 deg)\n"
             "peak drawn curvature   0.121      the chain's own peak is 0.103\n"
             "worst fit error        0.0289     on a 63-unit figure\n"
             "chain sagitta          0.0129"),
    ("p", "The apsis is the one place the drawing has to choose, because the "
          "chain's curvature jumps there by twice its peak and no cubic chain "
          "follows that smoothly. `apsis=\"sharp\"` keeps the corner, which is the "
          "chain's own turn to the digit. `apsis=\"smooth\"` rounds it, which "
          "draws a curve the data does not contain — the fit has to bend harder "
          "than the chain ever does:"),
    ("table", [["apsis", "corner", "peak curvature", "fit error"],
               ["sharp (default)", "5.904 deg, exact", "1.18x the chain", "0.0289"],
               ["smooth", "none", "3.00x the chain", "0.0129"]]),
    ("p", "The alternative is a different chain, not a different fit. "
          "`design.g2_lobe(tri, 15)` is the first closure past n = 3: turns 0…14, "
          "then 14…0 so the curvature walks back through zero, then −1…−20. It is 50 "
          "chords at α = 1.450°, its widest chord turns 20.3°, it peaks at 304.6° (a "
          "full volute rather than a hook) and it still closes exactly east, at "
          "(3.82, −8.47). Its curvature is continuous at the apsis, so there is no "
          "corner to draw and nothing to choose. The price is resolution: at 20° a "
          "chord it is three times coarser than the curl, and the closing condition "
          "admits no n between 15 and 85."),
    ("p", "Measured as acceleration instead of signed curvature, the corner is "
          "not a discontinuity at all. The force a pen or cutter feels goes as "
          "`|kappa| = |a|/v²`, and at the apsis that never moves: `|kappa|` rises "
          "by exactly one ramp step per chord, through the reversal and past it. "
          "What jumps is the *sign*. So the corner is a leaf tip — peak bending "
          "held while the direction of bending flips — and that is a design "
          "decision, reported as one:"),
    ("code", "curl(200, 6)             peak |k| 0.103   |k| jump 1.00 ramp steps\n"
             "curl(200, 6, accel=0.02)  peak |k| 0.020   |k| jump 1.00 ramp steps\n"
             "                          both: a designed apsis, not a defect"),
    ("p", "That also gives the constructor a knob with a physical meaning. "
          "`accel=` sets the peak `|kappa|` and solves for the chord length, "
          "`L = peak_turn * alpha / kappa`. Ask for a gentler stroke and the whole "
          "figure grows: the triangle and the turn schedule do not change, so the "
          "shape does not change, only its size."),
    ("p", "A genuinely smooth apsis cannot come from the renderer at all: it has "
          "to come from the turn schedule, which then has to pass through zero "
          "curvature and come back. Exactly closing chains of that kind exist only "
          "at `j(j+1) = 2n(n-1)` — n = 2, 14, 84 — so at the resolution the curl "
          "needs there is no smooth, exactly closing apsis available. The corner "
          "is not a rendering defect; it is the arithmetic."),
    ("p", "The fit sits at twice the resolution of the chords it interpolates, "
          "because the apsis corner has to be cut across rather than rounded; away "
          "from the apsis it is at the floor. On a 200 mm page that gap is about "
          "0.09 mm: below what the page can show."),

    ("h2", "7. Resolution, and what exactness is for"),
    ("p", "Coordinates are integers over `c^T(steps−1)`, so finer chords cost "
          "steeply:"),
    ("table", [["chord budget", "chords", "integer size", "build"],
               ["12°", "68", "5 000 digits", "0.07 s"],
               ["6°", "134", "13 000 digits", "1.4 s"],
               ["4°", "202", "21 000 digits", "9.6 s"],
               ["3°", "268", "63 000 digits", "minutes — refused"]]),
    ("p", "That is the wrong thing to pay for. The closure result — which turns, "
          "which pairs, where the apsis is — is **integer arithmetic** and never "
          "touches a coordinate. The coordinates themselves only need to be right to "
          "about fifteen digits, because four decimals is all the page can hold. So "
          "the exactness belongs in the plan, not in the points, and a float path "
          "would make `--chord 0.01` free."),

    ("h2", "8. Connecting and branching"),
    ("p", "This is what the method is actually good for. A node is a point with an "
          "exact direction, so two chains join by sharing the point and matching the "
          "heading — G1 by construction, not to within a tolerance. A branch leaves "
          "a node along the identical tangent, which is a cleaner join than any "
          "junction fitted afterwards."),
    ("fig", fig_branch, "A branch leaves the shared node at the shared heading, with opposite curvature."),

    ("h2", "9. What is exact, and what is not"),
    ("table", [["exact", "approximate"],
               ["every triangle rotation", "the curve between nodes"],
               ["every node coordinate", "the arms of each cubic"],
               ["the final heading (east, not 0.000°)", "the drawn path's distance from the chords"],
               ["closure: which turn sums cancel", "the equivalent clothoid's A²"],
               ["the apsis and its heading", "nothing else"]]),
    ("p", "The one thing that is *not* a limitation and is often mistaken for one: "
          "the shape never needs to be tuned by eye. Peak heading, resolution and "
          "join type are the three knobs, and each has a meaning."),

    ("h2", "10. Reproduce"),
    ("code", "cd pythagorean-spiral\n"
             "../.venv/bin/python -m pythagorean_spiral.cli --mode curl --peak 200 --chord 6\n"
             "../.venv/bin/python -m pythagorean_spiral.cli --list-closures\n"
             "../.venv/bin/python -m unittest discover -s tests -t .\n"
             "cd .. && .venv/bin/python pythagorean-spiral/scripts/compare_bertolazzi.py"),
    ("p", "50 tests. `scripts/explainer.py` generated this document and every figure "
          "in it."),
]


# ---------------------------------------------------------------- render ---
def to_md(blocks, fig_names):
    out = []
    n = 0
    for kind, *rest in blocks:
        if kind == "h1":
            out.append(f"# {rest[0]}\n")
        elif kind == "h2":
            out.append(f"\n## {rest[0]}\n")
        elif kind == "p":
            out.append(f"{rest[0]}\n")
        elif kind == "quote":
            out.append(f"> {rest[0]}\n")
        elif kind == "code":
            out.append(f"```text\n{rest[0]}\n```\n")
        elif kind == "fig":
            caption = rest[1]
            out.append(f"![{caption}](fig/{fig_names[n]})\n\n*{caption}*\n")
            n += 1
        elif kind == "raw":
            out.append(rest[0])
        elif kind == "table":
            rows = rest[0]
            out.append("| " + " | ".join(rows[0]) + " |")
            out.append("|" + "|".join(" --- " for _ in rows[0]) + "|")
            for row in rows[1:]:
                out.append("| " + " | ".join(row) + " |")
            out.append("")
    return "\n".join(out)


CSS = """
body{margin:0;background:#f6f1e4;color:#2e2413;
 font:16px/1.62 Georgia,'Iowan Old Style',serif}
main{max-width:760px;margin:0 auto;padding:44px 22px 90px}
h1{font-size:31px;line-height:1.2;margin:0 0 6px;letter-spacing:-.01em}
h2{font-size:20px;margin:38px 0 8px;color:#5b4718;
 border-bottom:1px solid #ddd0b2;padding-bottom:5px}
p{margin:0 0 12px}
code,pre{font:12.5px/1.55 ui-monospace,SFMono-Regular,Menlo,monospace}
pre{background:#fffdf7;border:1px solid #ddd0b2;border-radius:4px;
 padding:11px 13px;overflow-x:auto;margin:0 0 16px}
figure{margin:22px 0 24px}
figure svg{display:block;border:1px solid #e2d7bd;border-radius:4px;background:#fffdf7}
figcaption{font:12px/1.5 ui-monospace,Menlo,monospace;color:#8c6a21;margin-top:7px}
blockquote{margin:16px 0;padding:10px 16px;border-left:3px solid #b23a2b;
 background:#fffdf7;font-size:17px}
table{width:100%;border-collapse:collapse;font:12.5px/1.5 ui-monospace,Menlo,monospace;
 margin:0 0 18px}
th,td{border-top:1px solid #ddd0b2;padding:6px 5px;text-align:left;vertical-align:top}
th{color:#8c6a21;font-weight:500}
.lead{color:#8c6a21;margin:0 0 26px}
"""


def to_html(blocks, figs, title):
    out = [f'<!doctype html><html lang="en"><head><meta charset="utf-8">',
           '<meta name="viewport" content="width=device-width, initial-scale=1">',
           f"<title>{title}</title><style>{CSS}</style></head><body><main>"]
    n = 0
    for kind, *rest in blocks:
        if kind == "h1":
            out.append(f"<h1>{rest[0]}</h1>")
        elif kind == "h2":
            out.append(f"<h2>{rest[0]}</h2>")
        elif kind == "p":
            out.append(f"<p>{rest[0]}</p>")
        elif kind == "quote":
            out.append(f"<blockquote>{rest[0]}</blockquote>")
        elif kind == "code":
            out.append(f"<pre>{rest[0]}</pre>")
        elif kind == "fig":
            out.append(f"<figure>{figs[n][0]}<figcaption>{rest[1]}</figcaption></figure>")
            n += 1
        elif kind == "raw":
            out.append(rest[0])
        elif kind == "table":
            rows = rest[0]
            out.append("<table><tr>" + "".join(f"<th>{c}</th>" for c in rows[0]) + "</tr>")
            for row in rows[1:]:
                out.append("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>")
            out.append("</table>")
    out.append("</main></body></html>")
    return "\n".join(out)


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    names = ["rotation", "turning", "polygon", "error", "closure", "curl", "apsis", "cubic", "branch"]
    figs, fig_names = [], []
    i = 0
    for kind, *rest in BLOCKS:
        if kind != "fig":
            continue
        name = names[i]
        svg = rest[0]()
        (FIG / f"{name}.svg").write_text(svg + "\n")
        figs.append((svg, name))
        fig_names.append(f"{name}.svg")
        i += 1

    md = to_md(BLOCKS, fig_names)
    (ROOT / "docs" / "EXPLAINER.md").write_text(md.rstrip() + "\n")
    html = to_html(BLOCKS, figs, "The Pythagorean spiral")
    (ROOT / "docs" / "explainer.html").write_text(html + "\n")
    print(f"docs/EXPLAINER.md, docs/explainer.html, {len(figs)} figures")


if __name__ == "__main__":
    main()

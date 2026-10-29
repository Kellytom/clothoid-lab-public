"""Generate docs/GALLERY.md and its HTML twin: six studies on the spine layer.

Each study is built from the real chain code and drawn as a filled ribbon, not
as a hairline: a rail is a miter offset of the exact chain, so the width is part
of the proof.

    python scripts/gallery.py
"""

from __future__ import annotations

import math
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from pythagorean_spiral import design, ribbon  # noqa: E402
from pythagorean_spiral.exact import Dir  # noqa: E402
from pythagorean_spiral.spiral import Spiral  # noqa: E402
from pythagorean_spiral.triples import for_angle  # noqa: E402

import explainer as ex  # noqa: E402

FIG = ex.FIG
INK, GOLD, RED, BLUE, FAINT = ex.INK, ex.GOLD, ex.RED, ex.BLUE, ex.FAINT


# ------------------------------------------------------------- builders ---
def _catenary_turns(steps: int, a: float) -> list[int]:
    """Integer turns following sech^2: curvature peaks at the low point."""
    raw = [1.0 / math.cosh((k - steps) / a) ** 2 for k in range(2 * steps + 1)]
    peak = max(raw)
    return [max(0, round(r / peak * 24)) for r in raw]


def catenary(half: float = 1.6, a: float = 1.0, steps: int = 24,
             length=Fraction(1, 10), heading=None):
    """A hanging chain from support to support, all curvature one sign.

    `half/a` is the shape; the profile is sampled six chords per unit of `a`,
    which is what keeps the turn at the low point small enough to read.
    """
    tri = for_angle(5.0)
    a_eff = 6.0
    half_eff = a_eff * half / a
    turns = _catenary_turns(steps, a_eff)
    target = 2 * math.atan(math.sinh(half_eff / a_eff))
    turns = [max(0, round(t * target / (sum(turns) * tri.radians)))
             for t in turns]
    path = Spiral(tri, length, heading=heading or Dir.east())
    path.extend(turns)
    return path, target


def reference_catenary(path: Spiral) -> tuple[float, float, float]:
    """(max gap, sag ratio, span ratio) against the true catenary, normalized."""
    pts = [(float(x), float(y)) for x, y in path.nodes]
    xs = [p[0] for p in pts]
    span = max(xs) - min(xs)
    arc = float(path.arc_length)
    ratio = span / arc
    lo, hi = 1e-6, 20.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if mid / math.sinh(mid) > ratio:
            lo = mid
        else:
            hi = mid
    u = (lo + hi) / 2
    a = (span / 2) / u
    gap = 0.0
    for x, y in pts:
        gap = max(gap, abs(abs(y) - a * (math.cosh(x / a) - 1)))
    return gap / span, (a * (math.cosh(u) - 1)) / span, ratio


def _hang(path, target):
    """Rotate a one-sign chain so its start and end are the two supports."""
    ang = -target / 2
    c, s = math.cos(ang), math.sin(ang)
    return [(float(x) * c - float(y) * s, float(x) * s + float(y) * c)
            for x, y in path.nodes]


def drape(count: int = 5, steps: int = 24, width=Fraction(1, 25)):
    """A row of catenaries, hung from one line; each returns its ribbon."""
    chains = []
    for i, half in enumerate((1.10, 1.45, 1.80, 1.55, 1.25)):
        if i >= count:
            break
        path, target = catenary(half=half, steps=steps)
        poly = ribbon.outline(path.nodes, width, taper=2)
        ang = -target / 2
        c, s = math.cos(ang), math.sin(ang)
        chains.append([(float(x) * c - float(y) * s - i * 3.4,
                        float(x) * s + float(y) * c) for x, y in poly])
    return chains


def _arc(tri, length, heading, start, steps: int):
    """A run of turning chords that leaves along `heading`, so joins stay G1."""
    a = Spiral(tri, length, heading=heading, start=start)
    a.extend([0] + [1] * (steps - 1))
    return a


def volute(per: int = 8, length=Fraction(21, 20), shrink=Fraction(13, 16),
           chord: float = 11.4, quarters: int = 8):
    """A volute: arcs of shrinking chord, joined G1 on exact nodes."""
    tri = for_angle(chord)
    path = _arc(tri, length, Dir.east(), (0, 0), per)
    points = list(path.nodes)
    for _ in range(quarters - 1):
        length *= shrink
        nxt = _arc(tri, length, path.heading, path.final, per)
        design.joined(path, nxt, len(path.turns))
        points += nxt.nodes[1:]
        path = nxt
    return points, tri


def violin_scroll():
    """The volute with a throat: two straight neck chords, a cusp, then the scroll."""
    tri = for_angle(11.4)
    neck = Spiral(tri, Fraction(6, 5), heading=Dir.north())
    neck.extend([0, 0])
    throat = Spiral(tri, Fraction(21, 20), heading=neck.heading.quarter(1),
                    start=neck.final)
    throat.extend([0] + [1] * 5)
    # the throat is a declared corner: the point is exact, the heading turns a
    # whole quarter, which is a swap and not an angle
    if throat.nodes[0] != neck.final:
        raise AssertionError("the throat does not start on the neck")
    points = list(neck.nodes) + list(throat.nodes[1:])
    path = throat
    length = Fraction(21, 20)
    for _ in range(6):
        length *= Fraction(13, 16)
        nxt = _arc(tri, length, path.heading, path.final, 6)
        design.joined(path, nxt, len(path.turns))
        points += nxt.nodes[1:]
        path = nxt
    return points, tri


def acanthus():
    """A spine with paired lobes, every lobe attached by `design.fork`."""
    tri = for_angle(4.0)
    spine = Spiral(tri, Fraction(11, 20), heading=Dir.north())
    spine.extend([3, 2, 1, 0, -1, -2, -1, 0])
    lobes = []
    for k in range(1, len(spine.turns)):
        sign = 1 if k % 2 else -1
        _, branch = design.fork(spine, k, steps=4, length=Fraction(9, 20),
                                sign=sign)
        lobes.append(branch)
    return spine, lobes, tri


def _lobe(tri, heading, steps: int, length):
    p = Spiral(tri, length, heading=heading)
    p.extend(list(range(steps)) + list(range(-(steps - 1), 1)))
    return p


def fleur():
    """A fleur-de-lis: three lobed petals and a band, half of it mirrored."""
    tri = for_angle(3.0)
    base = Spiral(tri, Fraction(1, 2), heading=Dir.north())
    # centre petal: starts half a peak west of north, apsis exactly on north
    centre = _lobe(tri, base.heading * (tri.direction ** 5), 5, Fraction(2, 3))
    # side petal: splays east of north, tip just past 45 degrees
    side = _lobe(tri, base.heading * (tri.direction ** -8), 5, Fraction(2, 3))
    band = Spiral(tri, Fraction(1, 2), heading=Dir.east())
    band.extend([0, 0, 0, 0, 0, 0])
    petals = [centre, side]
    for p in petals:
        if p.nodes[0] != base.final:
            raise AssertionError("a petal does not start on the base anchor")
    half = [p for p in petals] + [band]
    return half, base, tri


# -------------------------------------------------------------- figures ---
def _ribbon(c, poly, width, taper=0, fill=INK, stroke=None, opacity=1.0):
    """Draw one exact chain as a filled miter ribbon (offset, then closed)."""
    pts = ribbon.outline(poly, width, taper)
    pts = [(float(x), float(y)) for x, y in pts]
    c.poly(pts + [pts[0]], stroke=stroke or fill, width=0.5, fill=fill,
           opacity=opacity)
    return pts


def fig_catenary():
    path, target = catenary()
    gap, sag_ratio, span_ratio = reference_catenary(path)
    poly = ribbon.outline(path.nodes, Fraction(3, 50), taper=2)
    ang = -target / 2
    c, s = math.cos(ang), math.sin(ang)
    pts = [(float(x) * c - float(y) * s, float(x) * s + float(y) * c)
           for x, y in poly]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    c = ex.Canvas((min(xs) - .4, max(xs) + .4), (min(ys) - .6, max(ys) + .6), 660, 330)
    c.poly(pts + [pts[0]], fill=INK, stroke=INK, width=0.5)
    for q in pts[::4]:
        c.dot(q, 1.6, GOLD)
    c.text(min(xs), max(ys) + .25,
           f"{len(path.turns)} chords, {path.triangle} tri, total turn "
           f"{math.degrees(target):.1f} deg", 10, GOLD)
    c.text(min(xs), max(ys) + .1,
           f"sag/span {sag_ratio:.3f}  gap {100 * gap:.2f}% of span  "
           f"width 3/25", 10, GOLD)
    return c.svg("catenary")


def fig_drape():
    chains = drape()
    xs = [x for ch in chains for x, _ in ch]
    ys = [y for ch in chains for _, y in ch]
    c = ex.Canvas((min(xs) - .5, max(xs) + .5), (min(ys) - .5, max(ys) + 1.4), 680, 360)
    c.line((min(xs) - .4, max(ys) + .5), (max(xs) + .4, max(ys) + .5), FAINT, 1.4)
    for ch in chains:
        c.poly(ch + [ch[0]], fill=INK, stroke=INK, width=0.4)
    c.text(min(xs), max(ys) + .95, "rail, one shared line", 10, GOLD)
    c.text(max(xs), min(ys) - .1,
           f"{len(chains)} ribbons, exact offsets, no weft", 10, GOLD, "end")
    return c.svg("drapery")


def fig_volute():
    pts, tri = volute()
    poly = ribbon.outline(pts, Fraction(1, 12), taper=1)
    poly = [(float(x), float(y)) for x, y in poly]
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    c = ex.Canvas((min(xs) - .3, max(xs) + .3), (min(ys) - .3, max(ys) + .3), 520, 520)
    c.poly(poly + [poly[0]], fill=INK, stroke=INK, width=0.5)
    c.dot((float(pts[-1][0]), float(pts[-1][1])), 2.6, RED)
    c.text(min(xs), min(ys) - .1,
           f"{len(pts) - 1} chords, arcs of shrinking chord, width 1/12",
           10, GOLD)
    return c.svg("volute")


def fig_violin():
    pts, tri = violin_scroll()
    poly = ribbon.outline(pts, Fraction(1, 10), taper=1)
    poly = [(float(x), -float(y)) for x, y in poly]
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    c = ex.Canvas((min(xs) - .3, max(xs) + .3), (min(ys) - .4, max(ys) + .4), 460, 560)
    c.poly(poly + [poly[0]], fill=INK, stroke=INK, width=0.5)
    c.text(max(xs), min(ys) - .2, "throat: one exact quarter turn, width 1/10",
           10, GOLD, "end")
    return c.svg("violin scroll")


def fig_acanthus():
    spine, lobes, tri = acanthus()
    spine_poly = ribbon.outline(spine.nodes, Fraction(1, 7), taper=2)
    lobe_polys = [ribbon.outline(p.nodes, Fraction(1, 7), taper=2) for p in lobes]
    pts = spine_poly + [q for poly in lobe_polys for q in poly]
    pts = [(float(x), float(y)) for x, y in pts]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    c = ex.Canvas((min(xs) - .3, max(xs) + .3), (min(ys) - .3, max(ys) + .3), 420, 640)
    for poly in lobe_polys:
        q = [(float(x), float(y)) for x, y in poly]
        c.poly(q + [q[0]], fill=INK, stroke=INK, width=0.4)
    q = [(float(x), float(y)) for x, y in spine_poly]
    c.poly(q + [q[0]], fill=INK, stroke=INK, width=0.5)
    for lobe in lobes:
        c.dot((float(lobe.nodes[0][0]), float(lobe.nodes[0][1])), 2.0, GOLD)
    c.text(min(xs), min(ys) - .15,
           f"{len(lobes)} forks, width 1/7, tapered tips", 10, GOLD)
    return c.svg("acanthus")


def fig_fleur():
    curves, base, tri = fleur()
    half_polys = [ribbon.outline(p.nodes, Fraction(1, 7), taper=2)
                  for p in curves]
    mirror_polys = [[(float(-x), float(y)) for x, y in poly]
                    for poly in half_polys]
    half_polys = [[(float(x), float(y)) for x, y in poly] for poly in half_polys]
    pts = [q for poly in half_polys + mirror_polys for q in poly]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    c = ex.Canvas((min(xs) - .5, max(xs) + .5), (min(ys) - .6, max(ys) + .6), 460, 620)
    # the centre petal is whole and symmetric; the side petal and band mirror
    centre = half_polys[0]
    c.poly(centre + [centre[0]], fill=INK, stroke=INK, width=0.5)
    for poly in half_polys[1:]:
        c.poly(poly + [poly[0]], fill=INK, stroke=INK, width=0.4)
    for poly in mirror_polys[1:]:
        c.poly(poly + [poly[0]], fill=INK, stroke=BLUE, width=0.9)
    c.dot((0.0, 0.0), 2.6, RED)
    c.text(min(xs), min(ys) - .35,
           "centre petal whole; side petal and band exact mirrors", 10, GOLD)
    return c.svg("fleur")


# ----------------------------------------------------------------- text ---
def build_blocks():
    cat_path, target = catenary()
    gap, sag_ratio, span_ratio = reference_catenary(cat_path)
    vol_points, vol_tri = volute()
    ac_spine, ac_lobes, ac_tri = acanthus()

    blocks = [
        ("h1", "Six studies on the spine framework"),
        ("p", "How much can hang off a chain of exact Pythagorean turns? Six "
              "named objects, each drawn as a filled ribbon and each leaning on a "
              "different part of the machinery: a curvature profile, repetition, a "
              "shrinking radius, a throat, branches, and an exact mirror."),
        ("quote", "The names are targets, not claims. A catenary is a cosh, a "
                  "volute is a logarithmic spiral, and neither is rational. What "
                  "is exact is the plan: every anchor, every rail, every join, "
                  "every mirror."),
        ("table", [["study", "leans on", "verdict"],
                   ["catenary", "one curvature profile", "close, measured"],
                   ["drapery", "repetition, rails in parallel", "close, no weft"],
                   ["Corinthian volute", "arcs of shrinking chord", "shape holds, seams step"],
                   ["violin scroll", "a throat and a volute", "shape holds, no pegbox"],
                   ["acanthus", "`fork` at stored nodes", "ribbon leaf, no serration"],
                   ["fleur-de-lis", "`fork` plus exact mirror", "filled, no terminals"]]),

        ("h2", "1. Rails, and why they are exact"),
        ("p", "A rail is a miter offset. The normal of a chord is its heading "
              "turned one quarter turn, which is a swap of two rationals; each "
              "chord is shifted by half the width; adjacent shifted chord lines "
              "are intersected. The intersection of two rational lines is "
              "rational. So the rail is a rational point at an exact distance from "
              "the exact chord, and the width is part of the proof rather than a "
              "stroke chosen by eye."),
        ("code", "spine node        exact rational point\n"
                 "normal            heading turned a quarter turn (a swap)\n"
                 "rail corner       intersection of two rational lines\n"
                 "taper             width multiplied by a rational ramp\n"
                 "failure           width larger than the inside radius: the rail folds"),
        ("p", "`ribbon.rail` and `ribbon.outline` take any chain -- including a "
              "composite of arcs with different chord lengths -- and recover the "
              "exact headings from the points themselves, because every chord "
              "length in a chain is rational. `taper=n` ramps the width to zero "
              "over n chords at each end, which is what turns a cut end into a "
              "leaf tip. The limit is the obvious one: inside a turn tighter than "
              "the half-width the rail crosses itself, and the module reports "
              "nothing -- the drawing shows it."),

        ("h2", "2. A simulated catenary"),
        ("fig", fig_catenary,
         "A catenary as one chain of sech^2 turns, offset into a ribbon, rotated onto the page."),
        ("p", "The catenary's curvature is `1/(a cosh^2)`, largest at the low "
              "point. The chain cannot hold a cosh, so it holds the profile: "
              "integer turns following `sech^2`, scaled so the total turn equals "
              "the reference. That fixes the supports' angle, and leaves the sag "
              "to fall where it may."),
        ("code", f"chords        {len(cat_path.turns)}\n"
                 f"triangle      {cat_path.triangle}\n"
                 f"total turn    {math.degrees(target):.2f} deg\n"
                 f"sag/span      {sag_ratio:.3f}   (true catenary, same span)\n"
                 f"worst gap     {100 * gap:.2f}% of the span\n"
                 f"width         3/25, tapered over 2 chords"),
        ("p", "The honest sentence: it hangs like a catenary to about a percent "
              "of its span, and it is not one. The shape is a discrete curvature "
              "profile; a real catenary is a transcendental curve. On a 200 mm "
              "page the gap is under 2 mm at this aspect, the same order as the "
              "chord."),

        ("h2", "3. Drapery"),
        ("fig", fig_drape,
         "Five catenary ribbons hung from one rail; each keeps its own span, sag and node count."),
        ("p", "Repetition is free and exact: every chain is its own `Spiral`, its "
              "own offset, and the supports sit on one line. What the drawing "
              "cannot yet do is a fold, because a fold is a surface and this is a "
              "set of ribbons. It is a warp without a weft -- but the ribbons are "
              "real widths now, not hairlines, and five of them are five exact "
              "offsets."),
        ("p", "The drape also shows where a `Bundle` belongs: five ribbons that "
              "must not touch are a bundle, and `clearance.py` already measures "
              "that in the main package. The spike does not import it yet -- one "
              "of the promotion-gate items."),

        ("h2", "4. A Corinthian volute"),
        ("fig", fig_volute,
         "A volute as a ribbon: eight quarter-arcs, each chord 13/16 of the last, joined on exact nodes."),
        ("p", "This is the first study that forced a change of construction. A "
              "volute tightens: the turn per chord grows as the radius shrinks, "
              "and with one fixed chord the last turns alias into a blade. So the "
              "chord itself shrinks -- one `Spiral` per quarter turn, each "
              "starting on the previous final node with the previous heading, "
              "`design.joined` proving the attachment by equality rather than by "
              "tolerance."),
        ("code", f"arcs          8 quarter turns\n"
                 f"chords        {len(vol_points) - 1}\n"
                 f"triangle      {vol_tri}\n"
                 f"chord shrink  13/16 per quarter\n"
                 f"seams         G1 exactly, curvature steps at each seam\n"
                 f"width         1/12, tapered at the outer end"),
        ("p", "The step at a seam is the volute's own construction -- classical "
              "volutes are drawn as arcs with shifting centres -- but it is worth "
              "saying plainly: the join is G1, not G2. A smooth seam needs a chord "
              "schedule that interpolates the radius, which is a different "
              "builder."),

        ("h2", "5. A violin scroll"),
        ("fig", fig_violin,
         "The same volute machinery with a throat: two straight neck chords, one exact quarter turn, then the scroll."),
        ("p", "The scroll is the volute plus two things the framework does well: a "
              "straight run, and a right-angle cusp that is exact because a "
              "quarter turn is a swap, not an angle. The throat is where a real "
              "scroll carries the pegbox; here it is a bare corner, which is the "
              "boundary of the study -- the framework supplies the curve, not the "
              "instrument."),

        ("h2", "6. An acanthus"),
        ("fig", fig_acanthus,
         "A spine with paired lobes; every lobe is a `fork` on a stored node, drawn as a tapered ribbon."),
        ("p", "This is the study the `fork` API was built for. Each lobe leaves "
              "the spine on the identical tangent with opposite curvature, so the "
              "attachment is exact: no fitted junction, no gap to hide. The lobes "
              "alternate side by the sign of the turn, which is a property of the "
              "rotation group rather than a drawing choice. With rails they are "
              "leaves rather than veins."),
        ("code", f"spine chords  {len(ac_spine.turns)}\n"
                 f"forks         {len(ac_lobes)}\n"
                 f"triangle      {ac_tri}\n"
                 f"attachment    exact point, exact heading\n"
                 f"tips          taper 2, width 1/7"),
        ("p", "Still missing: serration depth and a central rib. Both are widths "
              "and terminals over this skeleton, not changes to it -- the leaf is "
              "now a filled shape, and its veins are exact."),

        ("h2", "7. A fleur-de-lis"),
        ("fig", fig_fleur,
         "Three lobed petals and a band; the centre petal is whole, the side petal and band are exact mirrors."),
        ("p", "The fleur is the cleanest test of exactness, because symmetry is "
              "where drawing errors show. The centre petal is a lobe whose apsis "
              "lands exactly on north, so it is symmetric without being mirrored; "
              "the side petal and the band are reflected through the vertical axis, "
              "point for point. The two halves cannot disagree: there is no fitting "
              "step to disagree in. Rails then make it a silhouette -- the apsis "
              "miter is the petal's point."),
        ("code", "petals        3 lobed ribbons\n"
                 "band          one tapered ribbon, exact mirror\n"
                 "mirror        exact, through the vertical axis\n"
                 "tips          the apsis itself, plus taper at the base\n"
                 "width         1/6, tapered at the base"),
        ("p", "What it is not is a finished fleur: the tips need real terminals "
              "(W02's taper, measured at 17-18 per cent), the band wants to be a "
              "filled member, and the whole needs a `Bundle` to declare what may "
              "touch. Those are the next layer, and they now have an exact, "
              "filled skeleton to sit on."),

        ("h2", "8. What hangs off, and what does not"),
        ("table", [["capability", "evidence here", "status"],
                   ["exact anchors", "all six figures", "proved"],
                   ["exact G1 joins", "volute, scroll, acanthus", "proved"],
                   ["exact mirror", "fleur", "proved"],
                   ["branch at a node", "acanthus, fleur", "proved"],
                   ["miter rails and width", "every figure", "proved"],
                   ["tapered terminals", "petals, lobes, ribbon ends", "proved"],
                   ["a transcendental curve", "catenary", "simulated, ~1%"],
                   ["serration and rib", "acanthus", "absent"],
                   ["curvature-continuous seams", "volute", "G1 only"],
                   ["folds and weft", "drapery", "absent"],
                   ["past ~300 chords in one chain", "any study at finer chord", "blocked by exact cost"]]),
        ("p", "That is the answer to how much can hang off it. The **plan** -- "
              "where every curve starts, turns, joins, ends, and how wide it is -- "
              "is exact and load-bearing. The **surface** -- folds, serrations, "
              "fills, texture -- is not in the framework and should not be: it "
              "belongs to `Piece`, `Bundle`, `Section` and the terminals. The one "
              "genuine architectural limit is scale: exact coordinates cost digits, "
              "and a single chain past a few hundred chords is refused. The float "
              "hybrid is the next action for that reason."),
        ("p", "Each study is about forty lines of builder in `scripts/gallery.py`, "
              "and every figure is regenerated from the code by running it. None of "
              "them is tuned by eye."),
        ("h2", "Reproduce"),
        ("code", "cd pythagorean-spiral\n"
                 "../.venv/bin/python scripts/gallery.py\n"
                 "../.venv/bin/python -m unittest discover -s tests -t ."),
    ]
    return blocks


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    blocks = build_blocks()
    names = ["gallery-catenary", "gallery-drape", "gallery-volute",
             "gallery-violin", "gallery-acanthus", "gallery-fleur"]
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
    (ROOT / "docs" / "GALLERY.md").write_text(md.rstrip() + "\n")
    html = ex.to_html(blocks, figs, "Six studies on the spine framework")
    (ROOT / "docs" / "gallery.html").write_text(html + "\n")
    print(f"docs/GALLERY.md, docs/gallery.html, {len(figs)} figures")


if __name__ == "__main__":
    main()

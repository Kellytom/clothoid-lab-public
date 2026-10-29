"""Generate docs/TRANSFER.md and its HTML twin: lattice placement and caps.

Two questions: can a finished curve be placed on the integer lattice, and can
the caps and terminals be re-expressed on the new curve?

    python scripts/transfer.py
"""

from __future__ import annotations

import json
import math
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from pythagorean_spiral import place, ribbon  # noqa: E402
from pythagorean_spiral.triples import for_angle  # noqa: E402

import explainer as ex  # noqa: E402
import gallery as gal  # noqa: E402

FIG = ex.FIG
INK, GOLD, RED, BLUE, FAINT = ex.INK, ex.GOLD, ex.RED, ex.BLUE, ex.FAINT


# ------------------------------------------------------------------ caps ---
def caps():
    out = []
    for p in sorted((REPO / "out" / "caps").glob("cap-*.json")):
        d = json.loads(p.read_text())
        d["_file"] = p.name
        out.append(d)
    return out


def cap_polyline(cap, per_unit=60.0):
    """The cap as a clothoid: integrate kappa(s) = k0 + kd*s."""
    pts = [(0.0, 0.0)]
    h = 0.0
    x = y = 0.0
    for seg in cap["segments"]:
        k0, kd, L = seg["kappa0"], seg["kd"], seg["length"]
        n = max(2, int(L * per_unit))
        ds = L / n
        for i in range(n):
            s = i * ds
            kappa = k0 + kd * s
            theta = h + 0.5 * kappa * ds      # heading at the step midpoint
            x += ds * math.cos(theta)
            y += ds * math.sin(theta)
            h += kappa * ds
            pts.append((x, y))
    return pts


def cap_chain(cap, tri, chord=2.0):
    """The same cap with each chord's turn quantised to the triangle lattice."""
    alpha = tri.radians
    pts = [(0.0, 0.0)]
    h = 0.0
    x = y = 0.0
    chords = 0
    for seg in cap["segments"]:
        k0, kd, L = seg["kappa0"], seg["kd"], seg["length"]
        n = max(1, round(L / chord))
        ds = L / n
        for i in range(n):
            s = (i + 0.5) * ds
            turn = (k0 + kd * s) * ds
            step = round(turn / alpha) * alpha
            h += step
            x += ds * math.cos(h)
            y += ds * math.sin(h)
            pts.append((x, y))
            chords += 1
    return pts, chords


def cap_gap(cap, tri, chord=2.0):
    ref = cap_polyline(cap)
    got, chords = cap_chain(cap, tri, chord)
    # compare at the chain's own stations, against the reference resampled
    n = len(got) - 1
    total = max(1, n)
    idx = [round(i * (len(ref) - 1) / total) for i in range(n + 1)]
    gap = max(math.hypot(a[0] - ref[j][0], a[1] - ref[j][1])
              for a, j in zip(got, idx))
    length = sum(math.hypot(b[0] - a[0], b[1] - a[1])
                 for a, b in zip(ref, ref[1:]))
    return gap, length, chords


# ------------------------------------------------------------- placement ---
def placed_fleur():
    curves, base, tri = gal.fleur()
    polys = [ribbon.outline(p.nodes, Fraction(1, 6), taper=2) for p in curves]
    half = [q for poly in polys for q in poly]
    mirror = [(-x, y) for x, y in half]
    points = half + mirror
    d = place.rotation(tri, 5, quarter=0)
    ints, scale = place.fit(points, box=(200, 250), margin=8,
                            units_per_unit=1000, rotation=d)
    return ints, scale, d, tri


# -------------------------------------------------------------- figures ---
def fig_page():
    ints, scale, d, tri = placed_fleur()
    pts = [(x / 1000.0, y / 1000.0) for x, y in ints]
    c = ex.Canvas((0, 200), (0, 250), 620, 720, margin=22)
    c.out.append(f'<rect x="{c.xy(0, 250)[0]:.2f}" y="{c.xy(0, 250)[1]:.2f}" '
                 f'width="{c.xy(200, 0)[0] - c.xy(0, 250)[0]:.2f}" '
                 f'height="{c.xy(0, 0)[1] - c.xy(0, 250)[1]:.2f}" '
                 f'fill="#fffdf7" stroke="{FAINT}" stroke-width="1"/>')
    c.poly(pts + [pts[0]], fill=INK, stroke=INK, width=0.5)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    c.text(4, 4, f"200 x 250 page, integers /1000   scale {scale:.3f}",
           10, GOLD)
    c.text(4, 10,
           f"bbox {min(xs):.1f}..{max(xs):.1f} x {min(ys):.1f}..{max(ys):.1f}",
           10, GOLD)
    return c.svg("the fleur placed on the page")


def fig_cap():
    caps_ = caps()
    cap = caps_[0]
    tri = for_angle(0.05)
    ref = cap_polyline(cap)
    got, _ = cap_chain(cap, tri, 2.0)
    xs = [p[0] for p in ref] + [p[0] for p in got]
    ys = [p[1] for p in ref] + [p[1] for p in got]
    c = ex.Canvas((min(xs) - 4, max(xs) + 4), (min(ys) - 4, max(ys) + 4), 620, 420)
    c.poly(ref, FAINT, 5.0)
    c.poly(got, INK, 1.6)
    gap, length, chords = cap_gap(cap, tri, 2.0)
    c.text(min(xs), min(ys) - 6,
           f"{cap['_file']}: {chords} chords, gap {100 * gap / length:.2f}% "
           f"of length", 10, GOLD)
    return c.svg("cap on the new curve")


# ----------------------------------------------------------------- text ---
def build_blocks():
    ints, scale, d, tri = placed_fleur()
    caps_ = caps()
    tri_cap = for_angle(0.05)
    gaps = []
    for cap in caps_:
        gap, length, chords = cap_gap(cap, tri_cap, 2.0)
        gaps.append((100 * gap / length, cap["_file"], chords, length))
    gaps.sort()
    worst = gaps[-1]
    median = gaps[len(gaps) // 2]
    total_chords = sum(g[2] for g in gaps)
    st = json.loads((REPO / "docs" / "terminals" / "stage-two.json").read_text())
    lac = json.loads((REPO / "docs" / "terminals" / "lac.json").read_text())
    ends = sum(len(f["terminals"]) for f in st["figures"])
    ends += sum(len(f["terminals"]) for f in lac["figures"])

    blocks = [
        ("h1", "Placement and transfer"),
        ("p", "A curve is useful only when it can be put somewhere. This asks "
              "two questions of the spine layer: can a finished figure be "
              "rotated and scaled onto the integer lattice, and can the caps "
              "and terminals be re-expressed on the new curve?"),
        ("quote", "Placement is exact exactly when the rotation comes from the "
                  "chain's group. Quarter turns and triangle powers stay "
                  "rational; 30 and 45 degrees do not, and belong to the float "
                  "path."),

        ("h2", "1. The lattice rule"),
        ("p", "A chain's points are rational. Rotating by a triangle power or a "
              "quarter turn, scaling by a rational and translating by a "
              "rational keeps them rational, so they can be written as integers "
              "over one denominator (`place.lattice`) -- or snapped to a page "
              "grid in thousandths (`place.quantize`). `place.fit` takes the "
              "largest uniform scale that puts the figure inside a 200 x 250 "
              "box with a margin, then rounds to the grid."),
        ("code", "rotation      triangle power + quarter turn, exact\n"
                 "scale         rational (or an integer multiple of the lattice)\n"
                 "offset        rational\n"
                 "output        integers over one denominator, or grid units\n"
                 "outside group float only; quantized, not exact"),
        ("table", [["quantity", "value"],
                   ["page", "200 x 250, +y up"],
                   ["rotation", f"triangle power 5 of {tri}"],
                   ["scale", f"{scale:.3f}"],
                   ["output", "integers, thousandths of a unit"],
                   ["margin", "8 units"]]),
        ("fig", fig_page,
         "The fleur from the gallery, rotated inside the group, fitted to the page and rounded to thousandths."),
        ("p", "The point of the exercise is not the picture: it is that every "
              "vertex is an integer on a declared grid, so a design can be "
              "stored, tiled, compared and cut without a float deciding where a "
              "corner is. A rotation outside the group would break that, which "
              "is why the placement API asks for a `Dir` rather than degrees."),

        ("h2", "2. Caps: clothoid segments into a chain"),
        ("p", f"All {len(caps_)} caps in `out/caps` are clothoid segments in a "
              "local frame at the origin with angle zero -- they were made to be "
              "placed. Each segment is `(kappa0, kd, length)`, so the cap is a "
              "curve with curvature linear in arc length. The new curve is an "
              "Euler polygon of exactly that kind of curve, so a cap transfers "
              "by quantising each chord's turn to the triangle lattice."),
        ("code", "kappa(s)      kappa0 + kd*s\n"
                 "turn/chord    kappa(s_mid) * chord\n"
                 "lattice turn  round(turn / alpha) * alpha\n"
                 "error         measured against a fine integration of kappa\n"
                 "frame         anchor (0,0), heading east, angle 0 in every cap"),
        ("table", [["caps", str(len(caps_))],
                   ["segments", str(sum(len(c['segments']) for c in caps_))],
                   ["chords at 2 units", f"{total_chords:,}"],
                   ["median gap", f"{median[0]:.2f}% of length"],
                   ["worst gap", f"{worst[0]:.2f}% ({worst[1]})"]]),
        ("fig", fig_cap,
         "A cap transferred to the lattice: the clothoid in faint, the quantised chain in ink."),
        ("p", "The residual is the lattice, not the arithmetic: each chord's "
              "turn is rounded to a whole triangle angle, so the gap grows with "
              "alpha and with curvature. At 0.05 degrees the median is under "
              "half a percent of the cap's length; the worst cases are the caps "
              "whose curvature changes fastest, and they want a finer alpha or "
              "shorter chords, both of which the float hybrid can now afford."),

        ("h2", "3. Terminals: geometry without a frame"),
        ("p", f"The terminals are `{ends}` ends across two extractors, stored as "
              "cubic spans in page units. They transfer as *geometry* -- a "
              "rotation, scale and offset turn them into placed cubics -- but "
              "they carry no anchor and no heading, because they were cut out "
              "of a finished outline at a seam. The frame has to be recovered "
              "from the seam, or recorded when the terminal is extracted."),
        ("code", "terminals      cubic spans, page units\n"
                 "anchor         absent\n"
                 "heading        absent\n"
                 "transfer       one affine call once a frame exists\n"
                 "missing datum  the seam's point and direction"),
        ("p", "That is the next change in the main package, not here: the "
              "extractor should write `anchor` and `heading` beside each "
              "terminal, exactly as the caps already do. With that, attachment "
              "is the same operation as `fork`: read a frame, rotate by its "
              "exact direction, scale, translate."),

        ("h2", "4. What is ready"),
        ("table", [["operation", "status"],
                   ["rotate inside the group", "exact, tested"],
                   ["scale by a rational", "exact, tested"],
                   ["fit to a 200 x 250 page", "integer grid, tested"],
                   ["caps to the new curve", "36 cap files, median gap "
                    f"{median[0]:.2f}%"],
                   ["terminals with a frame", "blocked: no frame stored"],
                   ["arbitrary angles", "float only; quantized"]]),
        ("p", "Placement is the piece that had to exist first: caps, terminals, "
              "mirrors and branches all reduce to it. The caps are close to "
              "ready; the terminals need one field added where they are cut."),
        ("h2", "Reproduce"),
        ("code", "cd pythagorean-spiral\n"
                 "../.venv/bin/python scripts/transfer.py\n"
                 "../.venv/bin/python -m unittest tests.test_place"),
    ]
    return blocks


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    blocks = build_blocks()
    names = ["transfer-page", "transfer-cap"]
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
    (ROOT / "docs" / "TRANSFER.md").write_text(md.rstrip() + "\n")
    html = ex.to_html(blocks, figs, "Placement and transfer")
    (ROOT / "docs" / "transfer.html").write_text(html + "\n")
    print(f"docs/TRANSFER.md, docs/transfer.html, {len(figs)} figures")


if __name__ == "__main__":
    main()

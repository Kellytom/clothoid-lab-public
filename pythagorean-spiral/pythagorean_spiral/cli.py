"""Command line: build one chain, report it exactly, optionally draw it."""

from __future__ import annotations

import argparse
import math
from fractions import Fraction

from . import design, quality, spans as spanmod, svg
from .closure import closure_pairs, g2_pairs
from .spiral import Spiral
from .triples import Triple, thinnest


def _triangle(text: str, limit: int) -> Triple:
    if text in ("thin", "thinnest"):
        return thinnest(limit)
    parts = text.replace("-", ",").split(",")
    if len(parts) != 3:
        raise SystemExit(f"--triangle wants a-b-c or 'thin', got {text!r}")
    a, b, c = (int(p) for p in parts)
    return Triple(min(a, b), max(a, b), c)


def _build(args, triangle: Triple) -> Spiral:
    length = Fraction(args.length)
    if args.mode == "spiral":
        return design.spiral(triangle, args.steps, length)
    if args.mode == "lobe":
        return design.lobe(triangle, args.steps, length)
    if args.mode == "curl":
        return design.curl(args.peak, args.chord,
                           None if args.accel else length, accel=args.accel,
                           power=args.power)
    if args.mode == "hook":
        return design.hook(triangle, args.multiplier, args.n_out, length)
    return design.g2_lobe(triangle, args.steps, length)


def _digits(value: Fraction) -> int:
    """Rough digit count without converting to a string."""
    return max(1, int(len(bin(abs(value.numerator))) * 0.30103) + 1)


def report(path: Spiral, exact: bool = False, brief: bool = False,
           digits: int = 6) -> str:
    x, y = path.final
    ints, scale = path.integer_form()
    ix, iy = ints[-1]
    cloth = path.equivalent_clothoid()
    head = path.heading.axis_name()
    size = max(_digits(x), _digits(y))

    lines = [
        f"triangle      {path.triangle}   alpha = {path.triangle.degrees:.6f} deg"
        f"   tan = {path.triangle.slope}",
        f"shape         {len(path.turns)} chords   step {path.length}"
        f"   widest chord {math.degrees(path.chord_angle()):.2f} deg"
        f"   peak heading {path.peak_degrees:.2f} deg",
        f"closing       turn coeff {path.coeff}   heading exactly "
        f"{head or f'{path.heading.degrees:.6f} deg'}",
        f"final         ({float(x):.{digits}f}, {float(y):.{digits}f})",
        f"clothoid      kappa0 = {cloth['kappa0']:.9g}   kd = {cloth['kd']:.9g}"
        f"   A^2 = {cloth['A2']:.6f}",
    ]
    if exact:
        lines += [f"final x       {x}", f"final y       {y}",
                  f"scaled        ({ix}, {iy})   over {_digits(Fraction(scale))} "
                  f"digits, scale {scale}"]
    elif not brief:
        lines.append(f"exactness     exact rational, {size} digits "
                     f"(pass --exact to print it)")
    r = quality.report(path)
    lines.append(
        f"acceleration  peak |k| {r['peak_acceleration']:.6g}   "
        f"|k| jump {r['jump_in_steps']:.2f} ramp steps   "
        f"({quality.verdict(path)})")
    if path.cusps:
        lines.append(f"cusps         {path.cusps} (exact quarter turns)")
    if path.chord_angle() > 0.9:
        lines.append("warning       a chord turns more than ~52 deg: the chain is "
                     "aliased here, not a curve")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="pythagorean-spiral", description=__doc__)
    p.add_argument("--triangle", default="thin",
                   help="'thin', or a primitive triple like 79-3120-3121")
    p.add_argument("--limit", type=int, default=3125,
                   help="hypotenuse bound when choosing the thin triangle")
    p.add_argument("--mode", default="lobe",
                   choices=["curl", "spiral", "lobe", "hook", "g2"])
    p.add_argument("--steps", type=int, default=15)
    p.add_argument("--peak", type=float, default=200.0,
                   help="curl: heading at the apsis, in degrees")
    p.add_argument("--accel", type=float, default=None,
                   help="curl: target peak |curvature|; the chord length follows")
    p.add_argument("--chord", type=float, default=6.0,
                   help="curl: widest turn one chord may take, in degrees")
    p.add_argument("--power", type=int, default=1,
                   help="curl: exponent dial, turns = k**power; 1 is the clothoid")
    p.add_argument("--multiplier", type=int, default=3,
                   help="hook: how much faster the exit unwinds")
    p.add_argument("--n-out", type=int, default=None,
                   help="hook: force an exit length instead of the first closure")
    p.add_argument("--length", default="1", help="chord length, integer or a/b")
    p.add_argument("--page", type=float, default=200.0)
    p.add_argument("--arms", default="arc", choices=["arc", "menger"],
                   help="arc: the parabola rule; menger: solve the arms so the "
                        "knot curvature matches the three-point circle")
    p.add_argument("--apsis", default="sharp", choices=["sharp", "smooth"],
                   help="sharp: the exact corner at a curvature reversal; "
                        "smooth: round it and overshoot the curvature")
    p.add_argument("--max-turn", type=float, default=20.0,
                   help="degrees of heading change allowed inside one cubic")
    p.add_argument("--brief", action="store_true",
                   help="keep the shape numbers, drop the arithmetic")
    p.add_argument("--exact", action="store_true",
                   help="print the exact rational coordinates in full")
    p.add_argument("--out", default=None, help="write an SVG here")
    p.add_argument("--list-closures", action="store_true",
                   help="print exact closure pairs and exit")
    args = p.parse_args(argv)
    if args.exact:
        import sys
        sys.set_int_max_str_digits(0)

    if args.list_closures:
        print("hook closures  (n_wind, n_unwind) with T(n_wind) = m*T(n_unwind)")
        for m in (2, 3, 4, 8, 15):
            print(f"  m={m:2d}  {closure_pairs(m, 60)}")
        print("g2 closures    (m, j) with j(j+1) = 2m(m+1)")
        print(f"  {g2_pairs(120)}")
        return 0

    triangle = _triangle(args.triangle, args.limit)
    path = _build(args, triangle)
    print(report(path, exact=args.exact, brief=args.brief))

    curves = spanmod.spans(path, math.radians(args.max_turn), apsis=args.apsis,
                           arms=args.arms)
    nodes = path.floats()
    worst = max((spanmod.deviation(s, nodes) for s in curves), default=0.0)
    floor = spanmod.sagitta(path)
    print(f"cubics        {len(curves)}   worst distance to the chords "
          f"{worst:.6g} ({100 * worst / max(1e-9, float(path.length)):.2f}% of a chord)")
    print(f"chord floor   {floor:.6g}   (fit is at the chain's own resolution)")
    w, node, corner = quality.menger_agrees(curves, path)
    print(f"menger        worst knot curvature error {w * 100:.2f}%"
          f"{f' at node {node}' if node is not None else ''}"
          f"   at the corner {corner * 100:.2f}%")

    if args.out:
        text = svg.document(path, curves, page=(args.page, args.page),
                            marks=False,
                            title=f"pythagorean-spiral {path.triangle}")
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"wrote         {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Command line: a preset, a design file or a list of points in, one SVG out.

The report is the point of the tool as much as the path is. It says how many
cubics were needed, how far they sit from the true clothoid, whether every join
is G2, the tightest radius on the chain, and for each rail whether it has folded
and by how much margin.

    python -m clothoid_lab.cli --preset s-curve --width 6 --out out/s-curve.svg
    python -m clothoid_lab.cli --points route.txt --width 4 --out out/route.svg

Exit status is 0 when the fit is inside tolerance and the joins are G2, or when
the design is a G1 spline through points and its jumps are the fit. It is 1
otherwise. A fold in a rail is reported and does not fail the run, because
drawing the fold is a deliberate choice.
"""

from __future__ import annotations

import argparse
import math
import os
import sys

from . import bezier, compose, engine, interpolate, presets, svg
from .model import Design
from .offsets import build_rails, rail_deviation


def render(design: Design, tol: float = 0.02, width: float | None = None,
           prec: int = 4, margin: float = 5.0,
           max_spans: int = 64, split: int = 2,
           backend: str | None = None,
           page: tuple[float, float] | None = None,
           frame: tuple[float, float] | None = None,
           view: str | None = None,
           annotations: list[dict] | None = None) -> tuple[str, dict]:
    """Build a design into SVG text, with the report that justifies it."""
    chain = engine.build(design, backend=backend)
    spine, fit = bezier.fit_chain(chain, tol=tol, max_spans_per_segment=max_spans,
                                  split=split)
    spacing = bezier.path_deviation(spine, chain.point)

    distances = list(design.offsets)
    if width is not None:
        distances.extend([width / 2.0, -width / 2.0])
    rails = build_rails(chain, distances, tol=tol, max_spans_per_segment=max_spans,
                        split=split)

    scale = 1.0
    if frame is not None:
        all_spans = list(spine) + [s for rail in rails for s in rail["spans"]]
        x0, y0, x1, y1 = svg._bbox(all_spans)
        fw, fh = float(frame[0]), float(frame[1])
        inner_w, inner_h = fw - 2 * margin, fh - 2 * margin
        if (x1 - x0) > 0 and (y1 - y0) > 0 and inner_w > 0 and inner_h > 0:
            scale = min(inner_w / (x1 - x0), inner_h / (y1 - y0))

    text = svg.document(design, chain, spine, rails, prec=prec, margin=margin,
                        page=page, frame=frame, view=view,
                        annotations=annotations)
    info = {
        "chain": engine.report(chain),
        "scale": scale,
        "fit": fit,
        "spine_error": fit["error_max"],
        "spine_deviation": spacing,
        "rails": [
            {
                "distance": r["distance"],
                "spans": r["spans_count"],
                "error_max": r["error_max"],
                "deviation": rail_deviation(r, chain),
                "folds": r["folds"],
                "clamped": r["clamped"],
                "min_radius": r["min_radius"],
                "margin": r["margin"],
            }
            for r in rails
        ],
        "fit_ok": fit["error_max"] <= tol,
        "ok": fit["error_max"] <= tol and (chain.g2 or design.g1),
        "g1": design.g1,
        "worst_join": max(chain.joins, key=lambda j: abs(j["d_kappa"]), default=None),
    }
    return text, info


def format_report(info: dict, tol: float) -> str:
    c = info["chain"]
    if info.get("g1"):
        joins = "G1   curvature jumps are intended by construction"
    else:
        joins = (f"{'G2' if c['join_g2'] else 'G1'}   "
                 f"worst curvature jump {c['join_kappa_error_max']:.3e} 1/unit")
    lines = [
        f"engine        {c['backend']}",
        f"segments      {c['segments']}   length {c['length']:.3f} units",
        f"scale         1 unit = {info.get('scale', 1.0):.4f} mm",
        f"joins         {joins}",
    ]
    if c.get("corner_count"):
        lines.append(f"corners       {c['corner_count']}  "
                     f"max {math.degrees(c['corner_max']):.2f} deg")
    lines += [
        f"tightest      radius {c['min_radius']:.3f} units at s={c['min_radius_at']:.2f}",
        f"cubics        {info['fit']['spans']}  split {info['fit']['split']}  "
        f"per segment {info['fit']['spans_per_segment']}",
        f"fit           {info['spine_error']:.4f} units worst, "
        f"{info['spine_deviation']:.4f} units spacing  (tol {tol:g} units)",
    ]
    for r in info["rails"]:
        fold = "fold" if r["folds"] else "clear"
        clamp = f"  {r['clamped']} clamped at the reversal" if r.get("clamped") else ""
        lines.append(
            f"rail {r['distance']:+.3f}  {fold}  {r['spans']} cubics  "
            f"error {r['error_max']:.4f} units  margin {r['margin']:.3f} units{clamp}"
        )
        for s0, s1 in r["folds"]:
            lines.append(f"              folds from s={s0:.2f} to s={s1:.2f}")
    lines.append(f"verdict       {_verdict(info, tol)}")
    return "\n".join(lines)


def _verdict(info: dict, tol: float) -> str:
    """Say which promise failed, because the two failures look nothing alike."""
    if info.get("ok"):
        if info.get("g1"):
            return "inside tolerance, joins G1 by construction"
        return "inside tolerance, joins G2"
    reasons = []
    if not info.get("fit_ok", True):
        reasons.append(f"fit {info['spine_error']:.4f} mm over tol {tol:g} mm")
    join = info.get("worst_join")
    if join and abs(join["d_kappa"]) >= 1e-9:
        reasons.append(
            f"join at s={join['at']:.2f} jumps {join['d_kappa']:+.3e} 1/unit, so G1 not G2 "
            f"(set kappa0 to null to inherit)")
    if info["chain"].get("corner_count"):
        reasons.append(
            f"{info['chain']['corner_count']} tangent corner(s), max "
            f"{math.degrees(info['chain']['corner_max']):.2f} deg")
    return "; ".join(reasons) if reasons else "over tolerance"


def backend_names() -> list[str]:
    from . import backend as backends
    return list(backends.BACKENDS)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="clothoid_lab", description=__doc__.splitlines()[0])
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--preset", choices=sorted(presets.PRESETS), help="a named starting design")
    src.add_argument("--design", help="a design JSON file")
    src.add_argument("--points", metavar="FILE",
                     help="fit a G1 spline through these points (JSON, or 'x, y' per line)")
    ap.add_argument("--g2", action="store_true",
                    help="fit a G2 spline through --points instead of G1")
    ap.add_argument("--closed", action="store_true",
                    help="close the spline from --points")
    ap.add_argument("--smooth", type=int, default=0, metavar="N",
                    help="reduce curvature jumps over N iterations")
    ap.add_argument("--trim", default=None, metavar="S0,S1",
                    help="keep an arc-length range in mm")
    ap.add_argument("--reverse", action="store_true",
                    help="traverse the design backwards")
    ap.add_argument("--out", default=None, help="SVG path (default out/<name>.svg)")
    ap.add_argument("--json", default=None, help="also write the design JSON here")
    ap.add_argument("--tol", type=float, default=0.02, help="fit tolerance in design units")
    ap.add_argument("--width", type=float, default=None, help="ribbon width in design units, two rails")
    ap.add_argument("--prec", type=int, default=4, help="decimal places in the path data")
    ap.add_argument("--margin", type=float, default=5.0, help="page margin in mm")
    size = ap.add_mutually_exclusive_group()
    size.add_argument("--page", default=None, metavar="WxH",
                      help="fixed page in mm, true size, drawing centred")
    size.add_argument("--frame", default=None, metavar="WxH",
                      help="fixed page in mm with the drawing scaled to fill it; "
                           "this scales design units away from millimetres")
    ap.add_argument("--split", type=int, default=2,
                    help="pieces a span is cut into when it misses the tolerance")
    ap.add_argument("--backend", choices=sorted(backend_names()), default=None,
                    help="geometry backend (default: the compiled library)")
    ap.add_argument("--watch", action="store_true",
                    help="stay running and rebuild when the design file changes")
    ap.add_argument("--seed", choices=sorted(presets.PRESETS), default=None,
                    help="preset to write when --watch starts with no design file")
    ap.add_argument("--reopen", nargs="?", const="Inkscape", default=None,
                    metavar="APP",
                    help="ask this app to reopen the drawing after each rebuild")
    ap.add_argument("--keep-view", action="store_true",
                    help="carry Inkscape's zoom and pan over from the file being replaced")
    ap.add_argument("--quiet", action="store_true", help="write the file, print nothing")
    args = ap.parse_args(argv)

    def size_of(text, flag):
        try:
            w, h = (float(v) for v in text.lower().split("x"))
        except ValueError:
            ap.error(f"{flag} takes WxH in mm, for example 210x148")
        return (w, h)

    page = size_of(args.page, "--page") if args.page else None
    frame = size_of(args.frame, "--frame") if args.frame else None

    if (args.g2 or args.closed) and not args.points:
        ap.error("--g2 and --closed apply to --points only")
    if args.smooth < 0:
        ap.error("--smooth takes a non-negative number of iterations")

    trim_range = None
    if args.trim:
        try:
            s0, s1 = (float(v) for v in args.trim.split(","))
        except ValueError:
            ap.error("--trim takes S0,S1 in mm, for example 10,120")
        if s1 <= s0:
            ap.error("--trim needs S1 greater than S0")
        trim_range = (s0, s1)

    def prepare(design: Design) -> Design:
        if args.smooth:
            design = interpolate.smooth(design, iterations=args.smooth)
        if trim_range is not None:
            design = compose.trim(design, *trim_range)
        if args.reverse:
            design = compose.reverse(design)
        return design

    def load_design(path: str) -> Design:
        if args.points:
            return prepare(interpolate.load(
                path,
                method="g2" if args.g2 else None,
                cyclic=True if args.closed else None,
            ))
        return prepare(Design.load(path))

    needs_loader = bool(args.points or args.smooth or trim_range or args.reverse)
    if args.watch:
        if not (args.design or args.points):
            ap.error("--watch needs --design or --points: there must be a file to watch")
        from . import watch as watcher
        source = args.points or args.design
        return watcher.run(
            source,
            args.out or os.path.join("out", "watched.svg"),
            render,
            interval=0.4,
            seed_preset=args.seed,
            reopen_app=args.reopen,
            load=load_design if needs_loader else None,
            tol=args.tol,
            width=args.width,
            prec=args.prec,
            margin=args.margin,
            split=args.split,
            backend=args.backend,
            page=page,
            frame=frame,
        )

    try:
        if args.points:
            design = prepare(interpolate.load(
                args.points,
                method="g2" if args.g2 else None,
                cyclic=True if args.closed else None,
            ))
        elif args.design:
            design = prepare(Design.load(args.design))
        else:
            design = prepare(presets.get(args.preset))
    except (interpolate.InterpolationError, compose.ComposeError, OSError) as exc:
        ap.error(str(exc))
    if args.width is not None:
        if args.width <= 0:
            ap.error("--width must be positive")
    if args.split < 2:
        ap.error("--split must be at least 2")
    out_path = args.out or os.path.join("out", f"{design.name.split()[0]}.svg")
    text, info = render(design, tol=args.tol, width=args.width,
                        prec=args.prec, margin=args.margin, split=args.split,
                        backend=args.backend, page=page, frame=frame,
                        view=svg.read_view(out_path) if args.keep_view else None)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    svg.write(out_path, text)

    if args.json:
        os.makedirs(os.path.dirname(args.json) or ".", exist_ok=True)
        design.save(args.json)

    if not args.quiet:
        print(format_report(info, args.tol))
        print(f"wrote         {out_path}")
    return 0 if info["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

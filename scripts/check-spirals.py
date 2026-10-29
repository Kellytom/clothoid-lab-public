"""Check our clothoid fit against the recovered ornament spines.

    .venv/bin/python scripts/check-spirals.py [docs/spirals/stage-two.json]

For every cubic span on the recovered pages, fit one clothoid through its two
endpoints and their tangents (the G1 problem), then measure how far the fitted
clothoid strays from the drawn cubic. Samples are compared by nearest distance,
not by parameter, so the two curves do not have to march in step.

Writes `docs/spirals/parity.json` beside the data and prints a summary by span
kind. This is evidence, not a gate: a cubic is not a clothoid, and a
`logaesthetic` span is not expected to be one either. What matters is whether
the ideals we care about (`line`, `arc`, `euler`) come back exact, and how far
the others drift.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from clothoid_lab import engine, interpolate  # noqa: E402
from clothoid_lab.clearance import segment_distance  # noqa: E402
from clothoid_lab.model import Design, Segment  # noqa: E402

SAMPLES = 48


def cubic(span, t):
    u = 1 - t
    return (
        u ** 3 * span["p0"][0] + 3 * u * u * t * span["c1"][0]
        + 3 * u * t * t * span["c2"][0] + t ** 3 * span["p3"][0],
        u ** 3 * span["p0"][1] + 3 * u * u * t * span["c1"][1]
        + 3 * u * t * t * span["c2"][1] + t ** 3 * span["p3"][1],
    )


def polyline(span, n: int = 32):
    points = [cubic(span, i / n) for i in range(n + 1)]
    return list(zip(points, points[1:]))


def worst_distance(points, segments) -> float:
    """The largest nearest-distance: a one-way Hausdorff measure.

    Taking the minimum over samples would always find the shared endpoints and
    report zero, which is exactly the mistake this measurement exists to avoid.
    """
    worst = 0.0
    for point in points:
        best = math.inf
        for a, b in segments:
            d, _, _ = segment_distance(point, point, a, b)
            if d < best:
                best = d
        worst = max(worst, best)
    return worst


def fit_span(span) -> dict:
    p0, p3 = span["p0"], span["p3"]
    chord = math.dist(p0, p3)
    if chord <= 1e-9:
        return {"ok": False, "reason": "zero chord"}
    t0 = math.atan2(span["c1"][1] - p0[1], span["c1"][0] - p0[0])
    t1 = math.atan2(p3[1] - span["c2"][1], p3[0] - span["c2"][0])
    try:
        kappa, kd, length = interpolate.fit(p0, t0, p3, t1)
    except (ValueError, interpolate.InterpolationError) as exc:
        return {"ok": False, "reason": str(exc)}
    if length <= 0 or not math.isfinite(length):
        return {"ok": False, "reason": "bad length"}

    design = Design(name="fit", anchor={"x": p0[0], "y": p0[1], "angle": t0},
                    segments=[Segment(kd=kd, length=length, kappa0=kappa)])
    chain = engine.build(design)
    # The engine rejects s == length in the last ulps; stay just inside.
    limit = length * (1.0 - 1e-12)
    samples = [chain.point(min(length * i / SAMPLES, limit))
               for i in range(SAMPLES + 1)]
    error = worst_distance(samples, polyline(span))
    return {"ok": True, "error": error, "chord": chord,
            "ratio": error / chord if chord else math.inf,
            "kappa0": kappa, "kd": kd, "length": length}


def main() -> int:
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs/spirals/stage-two.json"
    data = json.loads(source.read_text(encoding="utf-8"))
    rows = []
    for figure in data["figures"]:
        for spine in figure["spines"]:
            for index, span in enumerate(spine["spans"]):
                result = fit_span(span)
                result.update({
                    "figure": figure["figure"],
                    "plate": figure["plate"],
                    "spine": spine["id"],
                    "span": index,
                    "kind": spine["kind"],
                })
                rows.append(result)

    ok = [r for r in rows if r["ok"]]
    print(f"{len(rows)} spans, {len(ok)} fitted, {len(rows) - len(ok)} failed")
    kinds = sorted({r["kind"] for r in rows})
    print(f"{'kind':<14}{'spans':>6}{'ok':>5}{'median err/chord':>19}{'worst':>10}")
    for kind in kinds:
        group = [r for r in rows if r["kind"] == kind]
        good = [r for r in group if r["ok"]]
        if not good:
            print(f"{kind:<14}{len(group):>6}{0:>5}{'—':>19}{'—':>10}")
            continue
        ratios = sorted(r["ratio"] for r in good)
        print(f"{kind:<14}{len(group):>6}{len(good):>5}"
              f"{_pct(ratios[len(ratios) // 2]):>19}{_pct(ratios[-1]):>10}")

    out = source.parent / "parity.json"
    out.write_text(json.dumps({
        "source": str(source),
        "samples": SAMPLES,
        "note": "error is the max distance from the fitted clothoid to the drawn "
                "cubic, divided by the span chord",
        "spans": rows,
    }, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    return 0


def _pct(value: float) -> str:
    return f"{value * 100:.2f}%"


if __name__ == "__main__":
    raise SystemExit(main())

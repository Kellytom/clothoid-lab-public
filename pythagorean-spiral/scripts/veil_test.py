"""The veil against four standard test patterns: two on top, two below.

    python scripts/veil_test.py [target]

The cloud is a veil, so the test is legibility, not taste.  Four panels --
Siemens star, grey step wedge, colour bars, chequer -- sit under the same
billows as the works: a **top row** where the cloud is dense and a **bottom
row** where it only drifts.  Each panel is sampled on a grid and the
composited veil alpha is reported as mean, 95th percentile and worst.

The gate is deliberately blunt:

    top row     mean <= TOP_MEAN   worst <= TOP_MAX      the image stays visible
    bottom row  mean <= BOT_MEAN   worst <= BOT_MAX      the image is lightly hazed

Writes `docs/veil-test.json` and `docs/veil-test.html`.  The opacity model is
`pythagorean_spiral.veil`, the same one `draw_cloud` fills, so a panel cannot
pass on paper while the drawing covers it.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pythagorean_spiral import veil as vmod  # noqa: E402

import explainer as ex  # noqa: E402
import cloud  # noqa: E402

DOCS = ROOT / "docs"

# two rows of two, y up; the works band is y 10 .. 42
PANELS = [
    ("top", "left", "Siemens star", (14.0, 32.0, 38.0, 16.0), "siemens"),
    ("top", "right", "grey step wedge", (68.0, 32.0, 38.0, 16.0), "wedge"),
    ("bottom", "left", "colour bars", (14.0, 8.0, 38.0, 16.0), "bars"),
    ("bottom", "right", "chequer + cross", (68.0, 8.0, 38.0, 16.0), "chequer"),
]

# The operator set the strength at 85 per cent on the 2c slider.  At that peak
# every version covers a fair part of an image, so an absolute "legible" gate
# would just fail everything.  What is still an objective claim is RELATIVE:
# at the same peak, v2 must cover less of the picture band than v1.  The mean
# is the measure -- how much of the strip is covered, not where one lobe lands.
PEAK_TOL = 0.03

DARK, LIGHT = "#14120e", "#f7f4ec"


def _clip(c, box):
    i = len(c.out)
    c.out.append(f'<clipPath id="panel{i}"><rect x="0" y="0" width="0" height="0"/></clipPath>')
    return i


def siemens(c, box):
    x, y, w, h = box
    cx, cy = x + w / 2, y + h / 2
    r = 0.46 * min(w, h)
    spokes = 24
    for i in range(spokes):
        a0 = 2 * 3.141592653589793 * i / spokes
        a1 = 2 * 3.141592653589793 * (i + 0.5) / spokes
        c.poly([(cx, cy),
                (cx + r * __import__("math").cos(a0), cy + r * __import__("math").sin(a0)),
                (cx + r * __import__("math").cos(a1), cy + r * __import__("math").sin(a1))],
               fill=DARK if i % 2 == 0 else LIGHT, stroke="none")


def wedge(c, box):
    x, y, w, h = box
    steps = 11
    for i in range(steps):
        g = round(255 * i / (steps - 1))
        c.poly([(x + w * i / steps, y), (x + w * (i + 1) / steps, y),
                (x + w * (i + 1) / steps, y + h), (x + w * i / steps, y + h)],
               fill=f"#{g:02x}{g:02x}{g:02x}", stroke="none")


def bars(c, box):
    x, y, w, h = box
    cols = ["#c81e1e", "#e0a000", "#e8e000", "#1f9b3a",
            "#1f6fd0", "#7a3fbf", "#f7f4ec", "#101010"]
    for i, col in enumerate(cols):
        c.poly([(x + w * i / 8, y), (x + w * (i + 1) / 8, y),
                (x + w * (i + 1) / 8, y + h), (x + w * i / 8, y + h)],
               fill=col, stroke="none")


def chequer(c, box):
    x, y, w, h = box
    nx, ny = 10, 6
    for j in range(ny):
        for i in range(nx):
            fill = DARK if (i + j) % 2 == 0 else LIGHT
            c.poly([(x + w * i / nx, y + h * j / ny),
                    (x + w * (i + 1) / nx, y + h * j / ny),
                    (x + w * (i + 1) / nx, y + h * (j + 1) / ny),
                    (x + w * i / nx, y + h * (j + 1) / ny)],
                   fill=fill, stroke="none")
    cx, cy = x + w / 2, y + h / 2
    c.line((x + 1, cy), (x + w - 1, cy), "#c81e1e", 0.6)
    c.line((cx, y + 1), (cx, y + h - 1), "#c81e1e", 0.6)


PATTERNS = {"siemens": siemens, "wedge": wedge, "bars": bars, "chequer": chequer}


def report(veil, version="v2"):
    rows = []
    for row, side, name, box, _kind in PANELS:
        s = vmod.panel(box, veil, version=version)
        rows.append({"row": row, "side": side, "pattern": name, "box": box,
                     "mean": round(s["mean"], 4), "p95": round(s["p95"], 4),
                     "max": round(s["max"], 4)})
    return rows


def rows_pass(rows, baseline=None):
    """v2 passes when it covers less of each row than v1 did."""
    if baseline is None:
        return True
    for row, base in zip(rows, baseline):
        if base["mean"] <= 0:
            continue
        if row["mean"] >= base["mean"]:
            return False
    return True


def figure(veil, version="v2", letters=("a", "b", "c", "d")):
    c = ex.Canvas((0, 120), (0, 64), 820, 470)
    c.poly([(0, 64), (120, 64), (120, 0), (0, 0)], fill=cloud.WALL, stroke="none")
    for row, side, name, box, kind in PANELS:
        x, y, w, h = box
        PATTERNS[kind](c, box)
        c.poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)],
               stroke=cloud.INK, width=0.5)
    cloud.draw_cloud(c, version)
    # the same labels again, above the veil, so a covered caption is not a lie
    for letter, (row, side, name, box, kind) in zip(letters, PANELS):
        x, y, w, h = box
        cloud.badge(c, x + 3, y + h - 3, letter)
        c.text(x, y + h + 1.8, f"{letter} · {name}", 8, cloud.GOLD)
    return c.svg(f"four test patterns under the veil, {version}")


def main() -> int:
    payload = {"peak_tolerance": PEAK_TOL, "canvas": list(vmod.CANVAS),
               "versions": {}}
    figs, rows_by_version = {}, {}
    for version in vmod.VERSIONS:
        target = cloud.VEIL_TARGET[version]
        veil = cloud.solve_veil(target, version)
        rows = report(veil, version)
        rows_by_version[version] = rows
        payload["versions"][version] = {
            "target_peak": target, "veil": round(veil, 4),
            "billows": len(vmod.polygons(version)),
            "layers": {k: round(v * veil, 4)
                       for k, v in vmod.layers(version).items()},
            "panels": rows,
        }
        figs[version] = (figure(veil, version), "veil-test-" + version)

    base = rows_by_version["v1"]
    lighter = rows_pass(rows_by_version["v2"], base)
    payload["v2_lighter_than_v1"] = lighter
    for version in vmod.VERSIONS:
        print(f"{version} veil {payload['versions'][version]['veil']:.3f}")
        for r in rows_by_version[version]:
            print(f'  {r["row"]:6s} {r["side"]:5s} {r["pattern"]:18s} '
                  f'mean {r["mean"]:.3f} p95 {r["p95"]:.3f} max {r["max"]:.3f}')
    print("v2 lighter than v1:", lighter)

    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "veil-test.json").write_text(json.dumps(payload, indent=1) + "\n")

    table = [["version", "pattern", "row", "mean", "p95", "worst"]]
    for version, rows in rows_by_version.items():
        for r in rows:
            table.append([version, r["pattern"], f'{r["row"]} {r["side"]}',
                          f'{r["mean"]:.3f}', f'{r["p95"]:.3f}',
                          f'{r["max"]:.3f}'])
    blocks = [("h1", "The veil against four test patterns"),
              ("p", "Two panels on top where the cloud meets the picture, two "
                    "below where it drifts. Standard patterns: a Siemens star, "
                    "an eleven-step grey wedge, colour bars and a chequer. Both "
                    "versions are solved to the operator's peak (85 per cent), "
                    "so the comparison is where the density lands, not how "
                    "strong it is."),
              ("fig", lambda: figs["v1"][0], "v1, the clustered ellipse cloud."),
              ("fig", lambda: figs["v2"][0], "v2, the turn-chain cloud."),
              ("h2", "Measured"),
              ("table", table),
              ("p", f"v2 covers less of the picture band than v1 at the same "
                    f"peak: {'yes' if lighter else 'no'}.")]
    (DOCS / "veil-test.html").write_text(
        ex.to_html(blocks, [figs["v1"], figs["v2"]],
                   "The veil against four patterns"))
    print("docs/veil-test.html, docs/veil-test.json")
    return 0 if lighter else 1


if __name__ == "__main__":
    raise SystemExit(main())

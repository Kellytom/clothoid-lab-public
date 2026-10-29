"""Measure the veil from the rendered pixels, not from a model of them.

The analytic model in `pythagorean_spiral.veil` predicts what the browser will
composite.  Predicting it twice is how the report and the picture drifted apart
in the first place, so this module does not predict: it renders the veil over a
black field and over a white field, and reads the alpha back.

For one pixel with effective composite alpha `a` and composite colour `C`:

    black backdrop   Rb = a*C
    white backdrop   Rw = a*C + 255*(1-a)

so, per channel, `a = 1 - (Rw - Rb)/255` -- independent of `C`.  Averaging the
three channels gives the alpha the eye is actually responding to, edges and
overlaps included, with no geometry model in the loop.

    python scripts/veil_measure.py [peak]

Writes `docs/veil-measured.json`.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PIL import Image  # noqa: E402

from pythagorean_spiral import veil as vmod  # noqa: E402

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
DOCS = ROOT / "docs"

UNIT = 5                       # pixels per canvas unit (600x400 render)
CANVAS_W, CANVAS_H = 120, 80   # canvas units
W, H = CANVAS_W * UNIT, CANVAS_H * UNIT

PALETTE = {
    "haze": "#ded8cf", "bank": "#cfc9bf", "billow": "#ddd0bb",
    "crown": "#f2ead9", "shade": "#9b8a70", "light": "#fbf6ea",
}


def page(version: str, factor: float, backdrop: str) -> str:
    """One calibration page: the veil at `factor` over a flat backdrop."""
    table = vmod.layers(version)
    shapes = []
    for layer, pts in vmod.polygons(version):
        d = " ".join(f"{x:.3f},{y:.3f}" for x, y in pts)
        shapes.append(
            f'<polygon points="{d}" fill="{PALETTE[layer]}" '
            f'opacity="{table[layer] * factor:.6f}" '
            f'stroke="{PALETTE[layer]}" stroke-width="0.8" '
            f'stroke-opacity="{table[layer] * factor:.6f}"/>')
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;padding:0;background:{backdrop};overflow:hidden}}
svg{{display:block}}
</style></head><body>
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"
     viewBox="0 0 {CANVAS_W} {CANVAS_H}" preserveAspectRatio="none">
  <rect width="{CANVAS_W}" height="{CANVAS_H}" fill="{backdrop}"/>
  <g transform="translate(0,{CANVAS_H}) scale(1,-1)">{''.join(shapes)}</g>
</svg></body></html>'''


def shoot(html: str, out: Path) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(html)
        src = Path(f.name)
    subprocess.run([CHROME, "--headless=old", "--disable-gpu",
                    "--hide-scrollbars", "--force-device-scale-factor=1",
                    f"--window-size={W},{H}", "--virtual-time-budget=1500",
                    f"--screenshot={out}", f"file://{src}"],
                   check=True, capture_output=True)
    src.unlink(missing_ok=True)


def alpha_map(version: str, factor: float, tmp: Path):
    """Per-pixel alpha, recovered from two renders of the same geometry."""
    black = tmp / f"{version}-black.png"
    white = tmp / f"{version}-white.png"
    shoot(page(version, factor, "#000000"), black)
    shoot(page(version, factor, "#ffffff"), white)
    a = Image.open(black).convert("RGB")
    b = Image.open(white).convert("RGB")
    if a.size != b.size:
        raise RuntimeError(f"render size mismatch: {a.size} vs {b.size}")
    pa, pb = a.load(), b.load()
    out = [[0.0] * a.size[0] for _ in range(a.size[1])]
    for y in range(a.size[1]):
        row = out[y]
        for x in range(a.size[0]):
            ra, rb = pa[x, y], pb[x, y]
            row[x] = max(0.0, min(1.0, sum(
                1.0 - (rb[i] - ra[i]) / 255.0 for i in range(3)) / 3.0))
    return out


def panel(alpha, box, nx=17, ny=13):
    """Mean, 95th percentile and worst alpha over a box (x, y, w, h), y up."""
    x0, y0, w, h = box
    vals = []
    for j in range(ny):
        for i in range(nx):
            x = x0 + w * i / (nx - 1)
            y = y0 + h * j / (ny - 1)
            px = min(W - 1, max(0, int(x * UNIT)))
            py = min(H - 1, max(0, int((CANVAS_H - y) * UNIT)))
            vals.append(alpha[py][px])
    vals.sort()
    return {"mean": sum(vals) / len(vals), "p95": vals[int(0.95 * len(vals))],
            "max": vals[-1]}


def measure(version: str, factor: float, tmp: Path) -> dict:
    alpha = alpha_map(version, factor, tmp)
    rows = {}
    for row, box in (("top", vmod.row_box("top")), ("bottom", vmod.row_box("bottom"))):
        rows[row] = panel(alpha, box)
    peak = max(max(r) for r in alpha)
    return {"veil": round(factor, 4), "rows": rows, "peak": round(peak, 4)}


def main() -> int:
    peak_target = float(sys.argv[1]) if len(sys.argv) > 1 else 0.80
    import cloud
    payload = {"target_peak": peak_target, "unit_px": UNIT, "versions": {}}
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for version in vmod.VERSIONS:
            factor = cloud.solve_veil(cloud.VEIL_TARGET[version], version)
            got = measure(version, factor, tmp)
            payload["versions"][version] = got
            print(f"{version} veil {factor:.3f}: measured peak {got['peak']:.3f}  "
                  f"top mean {got['rows']['top']['mean']:.3f} "
                  f"worst {got['rows']['top']['max']:.3f}  |  "
                  f"bottom mean {got['rows']['bottom']['mean']:.3f} "
                  f"worst {got['rows']['bottom']['max']:.3f}")
    (DOCS / "veil-measured.json").write_text(json.dumps(payload, indent=1) + "\n")
    print("docs/veil-measured.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

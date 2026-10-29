"""SVG -> PNG -> silhouette metrics, for inside and outside references.

    .venv/bin/python scripts/silhouette.py reference/fleur/svg/*.svg

Rasterises with Inkscape (already required by this project), then measures the
ink silhouette: bounding box, H/W, ink fill, and vertical symmetry. This is the
measurement a principle card cites; it is never used to trace a shape.
"""
import json, subprocess, sys, tempfile
from pathlib import Path

INKSCAPE = "/Applications/Inkscape.app/Contents/MacOS/inkscape"
WIDTH = 900


def rasterise(svg: Path, png: Path) -> None:
    subprocess.run([INKSCAPE, str(svg), "--export-type=png",
                    f"--export-filename={png}", f"--export-width={WIDTH}",
                    "--export-background=white", "--export-background-opacity=1"],
                   check=True, capture_output=True)


def measure(png: Path) -> dict:
    from PIL import Image
    im = Image.open(png).convert("L")
    w, h = im.size
    px = im.load()
    mask = [[px[x, y] < 200 for x in range(w)] for y in range(h)]
    xs = [x for y in range(h) for x in range(w) if mask[y][x]]
    ys = [y for y in range(h) for x in range(w) if mask[y][x]]
    if not xs:
        return {"ink": 0.0}
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    bw, bh = x1 - x0 + 1, y1 - y0 + 1
    filled = sum(1 for y in range(y0, y1 + 1) for x in range(x0, x1 + 1) if mask[y][x])
    agree = total = 0
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            mx = x1 - (x - x0)
            if mask[y][x] or mask[y][mx]:
                total += 1
                agree += mask[y][x] == mask[y][mx]
    return {"size": [w, h], "bbox": [bw, bh], "aspect": round(bh / bw, 3),
            "fill": round(filled / (bw * bh), 3),
            "symmetry": round(agree / max(total, 1), 3)}


def main() -> int:
    paths = [Path(a) for a in sys.argv[1:]] or sorted(Path("reference/fleur/svg").glob("*.svg"))
    out = Path("reference/fleur/png"); out.mkdir(parents=True, exist_ok=True)
    rows = []
    for svg in paths:
        png = out / (svg.stem + ".png")
        rasterise(svg, png)
        row = {"svg": str(svg), "png": str(png), **measure(png)}
        rows.append(row)
        print(f"{svg.name}: aspect {row['aspect']}, fill {row['fill']}, "
              f"symmetry {row['symmetry']}, bbox {row['bbox']}")
    (out / "metrics.json").write_text(json.dumps(rows, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

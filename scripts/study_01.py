"""Build the P01 page: the ported fleur, its nodes, and the parity table.

    .venv/bin/python scripts/study_01.py

Writes `docs/fleur-study-01.html`. The reference nodes come from running the
original `ornaments/assets/ornament_set.js` under node; they are embedded in
the page so the comparison travels with the drawing.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from clothoid_lab import engine  # noqa: E402
from clothoid_lab.grammar import STUDY_01, fleur_right, study_01  # noqa: E402
from clothoid_lab.piece import render_piece  # noqa: E402

REFERENCE = [
    (0.0, -330.0), (65.0, -25.0), (120.0, -25.0), (436.992, -226.944),
    (249.984, -25.024), (250.0, 25.0), (364.352, 210.432), (422.912, 474.56),
    (423.0, 1000.0), (160.0, 25.024), (110.0, 25.0), (0.0, 1180.0),
]
FAMILIES = ["line", "line", "arc", "arc", "line", "euler",
            "arc", "line", "arc", "line", "line"]


def main() -> int:
    piece = study_01()
    svg, info = render_piece(piece, tol=0.05, margin=20)
    right = fleur_right(STUDY_01)
    worst = 0.0
    rows = []
    for index, (ours, ref, family) in enumerate(
            zip(right["nodes"], REFERENCE, ["start"] + FAMILIES)):
        delta = math.dist(ours, ref)
        worst = max(worst, delta)
        rows.append(
            f"<tr><td>{index:02d}</td><td>{family}</td>"
            f"<td>({ref[0]:.3f}, {ref[1]:.3f})</td>"
            f"<td>({ours[0]:.3f}, {ours[1]:.3f})</td>"
            f"<td>{delta:.3f}</td></tr>")

    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Fleur study 01 — ported</title>
<style>
:root {{ color-scheme: light; --paper:#f6f1e4; --card:#fffdf7; --ink:#2e2413;
  --muted:#7b6c4e; --line:#d8ccae; --gold:#8c6a21;
  --mono: ui-monospace,"SF Mono",Menlo,monospace; --serif:"EB Garamond",Georgia,serif; }}
* {{ box-sizing: border-box; }}
body {{ margin:0; background:var(--paper); color:var(--ink); font:16px/1.55 var(--serif); }}
main {{ max-width:900px; margin:0 auto; padding:34px 22px 70px; }}
h1 {{ font-size:28px; margin:0 0 4px; }}
p.lead {{ color:var(--gold); margin:0 0 18px; }}
h2 {{ font:600 11px/1.2 var(--mono); letter-spacing:.12em; text-transform:uppercase;
  color:var(--muted); margin:26px 0 8px; }}
.panel {{ background:var(--card); border:1px solid var(--line); border-radius:6px; padding:14px; }}
.art svg {{ display:block; width:100%; height:auto; background:#fff; }}
table {{ border-collapse:collapse; width:100%; font:12px/1.5 var(--mono); }}
th,td {{ border-bottom:1px solid var(--line); padding:5px 4px; text-align:left; }}
th {{ color:var(--muted); font-weight:500; }}
code {{ font:12px var(--mono); background:#fbf8ee; border:1px solid var(--line);
  border-radius:3px; padding:1px 3px; }}
a {{ color:var(--gold); }}
.back {{ font:12px var(--mono); margin-bottom:16px; }}
p {{ margin:0 0 10px; }}
</style></head><body><main>
<p class="back"><a href="ornament-board.html">← back to the ornament board</a></p>
<h1>Fleur study 01 — ported</h1>
<p class="lead">The old grammar, rebuilt from clothoid segments. Every node within
{worst:.3f} units of the original.</p>

<h2>The drawing</h2>
<div class="panel art">{svg}</div>

<h2>The nodes</h2>
<div class="panel">
  <table>
    <tr><th>node</th><th>family</th><th>original</th><th>ported</th><th>Δ</th></tr>
    {''.join(rows)}
  </table>
</div>

<h2>What is exact, what is not</h2>
<div class="panel">
<p>Each span is now a clothoid segment: a straight run is <code>κ = 0</code>, a
circle is <code>κ = 1/R</code>, and the petal's Euler span runs
<code>κ</code> linearly from 0 to <code>1/625</code> over ten degrees. The
original converted those to 45° cubics and rounded every node to the 3125
lattice; the residual above is that rounding, not a geometry difference.</p>
<p>Corners are explicit: the old chain permits a tangent jump between spans, and
each segment here carries <code>Segment.corner</code>. Without that the foot
would bend into the tail base and every later node would drift.</p>
<p>Not done yet: the terminal choice per stroke and the 12.5 mm parallels are
taken from the old set, not decided here; and the centre seam where the half
meets its mirror is a real contact that must be declared before the clearance
report can be believed.</p>
</div>
</main></body></html>
"""
    path = ROOT / "docs" / "fleur-study-01.html"
    path.write_text(page, encoding="utf-8")
    print(path)
    print(f"spans={len(right['spans'])} nodes={len(right['nodes'])} worst={worst:.3f}")
    print(f"fit_ok={info['fit_ok']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

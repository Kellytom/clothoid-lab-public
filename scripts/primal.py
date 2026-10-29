"""Build docs/primal.html: earth, water, air and fire, one page."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from clothoid_lab import primal
from clothoid_lab.piece import render_piece

NOTES = {
    "earth": "Strata: four terraces, real corners, heavy at the foot, drawn to a taper.",
    "water": "Flow: a long sweep, a reversal, a shorter return; both ends rounded.",
    "air": "Cloud: billows of falling radius, round ends, nothing sharp.",
    "fire": "Tongue: curvature rising then falling, a corner in the middle, a point at the tip.",
}

panels = []
for name, build in primal.PRIMAL.items():
    piece = build()
    svg, info = render_piece(piece, tol=0.05, margin=10, annotations=[
        {"kind": "text", "x": 0.0, "y": -12.0, "text": name, "size": 6.0,
         "fill": "#8c6a21"}])
    panels.append(f'<section><h2>{name}</h2><p>{NOTES[name]}</p>'
                  f'<div class="art">{svg}</div></section>')

page = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Primal ornaments</title>
<style>
body{margin:0;background:#f6f1e4;color:#2e2413;font:16px/1.55 Georgia,serif}
main{max-width:1100px;margin:0 auto;padding:34px 22px 70px}
h1{font-size:28px;margin:0 0 4px}.lead{color:#8c6a21;margin:0 0 20px}
section{display:inline-block;width:48%;vertical-align:top;margin:0 2% 22px 0}
h2{font:600 11px/1.2 ui-monospace,Menlo,monospace;letter-spacing:.12em;
text-transform:uppercase;color:#7b6c4e;margin:0 0 4px}
p{font-size:14px;margin:0 0 8px}.art{background:#fffdf7;border:1px solid #d8ccae;padding:10px}
svg{display:block;width:100%;height:auto}
@media(max-width:760px){section{width:100%;margin-right:0}}
</style></head><body><main>
<h1>Primal ornaments</h1>
<p class="lead">Earth, water, air, fire — one grammar each, no fills.</p>
""" + "".join(panels) + """
</main></body></html>
"""
path = ROOT / "docs" / "primal.html"
path.write_text(page, encoding="utf-8")
print(path)
for name in primal.PRIMAL:
    print(" ", name)

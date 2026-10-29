"""Build the W01/W02 sandbox: a piece, a mirror, and the terminal strip.

Run from the repo root:

    .venv/bin/python scripts/piece_sandbox.py
    open docs/piece-model.html
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from clothoid_lab.model import Design, Segment
from clothoid_lab.piece import Piece, Trace, render_piece
from clothoid_lab.presets import s_curve
from clothoid_lab.terminals import TERMINALS, terminal_extension


def band() -> Design:
    return Design(
        name="band",
        segments=[Segment(kd=0.0, length=90.0, kappa0=0.0)],
        anchor={"x": -45.0, "y": 58.0, "angle": 0.0},
    )


def ribbon(y: float, length: float = 45.0) -> Design:
    return Design(
        name="ribbon",
        segments=[Segment(kd=0.0, length=length, kappa0=0.0)],
        anchor={"x": 0.0, "y": y, "angle": 0.0},
    )


def terminal_strip() -> tuple[str, dict]:
    """One straight ribbon per terminal, stacked, labelled to the left."""
    piece = Piece(
        name="W02 terminal strip",
        stroke=0.6,
        traces=[
            Trace(kind, ribbon(96.0 - 16.0 * index), width=8.0,
                  mirror=False, terminals=(kind, kind))
            for index, kind in enumerate(TERMINALS)
        ],
    )
    annotations = [
        {"kind": "text", "x": -22.0, "y": 96.0 - 16.0 * index + 1.2,
         "text": kind, "size": 4.0, "anchor": "end", "fill": "#7b6c4e"}
        for index, kind in enumerate(TERMINALS)
    ]
    return render_piece(piece, tol=0.05, margin=34, annotations=annotations)


def main() -> int:
    piece = Piece(
        name="W01 sandbox",
        mirror=True,
        stroke=0.6,
        traces=[
            Trace("half", s_curve(), width=6.0, layer="ink"),
            Trace("band", band(), mirror=False, layer="guide"),
        ],
    )
    svg, info = render_piece(piece, tol=0.05, margin=8)
    strip, strip_info = terminal_strip()

    terminal_rows = "\n".join(
        f"<tr><td><code>{kind}</code></td>"
        f"<td>{terminal_extension(kind, 8.0):.2f} mm</td>"
        f"<td>{'the rails simply stop (baseline)' if kind == 'butt' else 'closes the ribbon end'}</td></tr>"
        for kind in TERMINALS
    )

    rows = "\n".join(
        f"<tr><td><code>{trace['layer']}/{trace['name']}</code></td>"
        f"<td>{trace['fit_error']:.4f} mm</td>"
        f"<td>{trace['rails']}</td>"
        f"<td>{'yes' if trace['mirrored'] else 'no'}</td></tr>"
        for trace in info["traces"]
    )

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>W01–W02 — the piece model and terminals</title>
<style>
  :root {{
    color-scheme: light;
    --paper: #f6f1e4; --card: #fffdf7; --ink: #2e2413;
    --muted: #7b6c4e; --gold: #8c6a21; --line: #d8ccae;
    --mono: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
    --serif: "EB Garamond", Georgia, "Palatino Linotype", Palatino, serif;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; color: var(--ink);
    background: radial-gradient(900px 440px at 12% -8%, #fcf9ef 0, transparent 60%), var(--paper);
    font: 16px/1.55 var(--serif);
  }}
  main {{ max-width: 900px; margin: 0 auto; padding: 34px 22px 70px; }}
  h1 {{ font-size: 28px; margin: 0 0 4px; }}
  .lead {{ color: var(--gold); margin: 0 0 18px; }}
  h2 {{ font: 600 11px/1.2 var(--mono); letter-spacing: .12em;
        text-transform: uppercase; color: var(--muted); margin: 26px 0 8px; }}
  .panel {{ background: var(--card); border: 1px solid var(--line);
            border-radius: 6px; padding: 14px; }}
  .art svg {{ display: block; width: 100%; height: auto; background: #fff; }}
  p {{ margin: 0 0 10px; }}
  ul {{ margin: 0 0 10px 20px; padding: 0; }}
  li {{ margin: 4px 0; }}
  code {{ font: 12px/1 var(--mono); background: #fbf8ee;
          border: 1px solid var(--line); border-radius: 3px; padding: 2px 4px; }}
  table {{ border-collapse: collapse; width: 100%; font: 12px/1.5 var(--mono); }}
  th, td {{ border-bottom: 1px solid var(--line); padding: 6px 4px; text-align: left; }}
  th {{ color: var(--muted); font-weight: 500; }}
  a {{ color: var(--gold); }}
  .back {{ font: 12px var(--mono); margin-bottom: 16px; }}
  @media (max-width: 560px) {{ main {{ padding: 22px 14px 60px; }} h1 {{ font-size: 23px; }} }}
</style>
</head>
<body>
<main>
  <p class="back"><a href="ornament-board.html">← back to the ornament board</a></p>
  <h1>W01–W02 — the piece model and terminals</h1>
  <p class="lead">One drawing, several traces, one mirror — and a vocabulary for how each ribbon ends.</p>

  <h2>What you are looking at</h2>
  <div class="panel">
    <ul>
      <li><code>ink/half</code> — one clothoid chain, drawn as the centre line of a ribbon.</li>
      <li><code>ink/half rail ±3</code> — the two edges, each offset 3 mm from the centre line; together they make a 6 mm ribbon.</li>
      <li><code>ink/half mirrored</code> — the same three paths reflected across x = 0. The mirror is one setting on the piece, not a second drawing.</li>
      <li><code>guide/band</code> — a straight guide, explicitly <em>not</em> mirrored, so it does not draw twice.</li>
    </ul>
  </div>

  <h2>The piece</h2>
  <div class="panel art">
    {svg}
  </div>

  <h2>The report</h2>
  <div class="panel">
    <table>
      <tr><th>trace</th><th>fit</th><th>rails</th><th>mirrored</th></tr>
      {rows}
    </table>
  </div>

  <h2>The terminal strip — W02</h2>
  <div class="panel art" id="terminal-strip">
    {strip}
  </div>
  <div class="panel" style="margin-top:12px">
    <table>
      <tr><th>terminal</th><th>reach past the rails</th><th>shape</th></tr>
      {terminal_rows}
    </table>
  </div>

  <h2>What this proves</h2>
  <div class="panel">
    <p>The engine still draws one chain at a time. A <code>Piece</code> holds named traces, each with its own <code>Design</code>, optional ribbon width and mirror rule. <code>render_piece()</code> builds every trace, mirrors the groups that ask for it, and writes one SVG with one page, one frame and one y-flip. The path ids are the trace names, so a later grammar can address a band or a petal directly.</p>
    <p>The terminal strip is the W02 vocabulary, eight millimetres wide, the same on both ends: <code>butt</code> stops the rails where they are; <code>point</code> brings them to a sharp tip; <code>arc</code> is a shallow five-millimetre dome; <code>round</code> is a semicircle of half the width; <code>taper</code> converges over four half-widths; <code>bulb</code> and <code>cone</code> are the two width laws recovered from the ornaments stage-two page, <code>w = ½(t(3−3t+t²)+12t²(1−t)³)</code> and <code>w = ½(1−(1−t)³)</code>. Both meet the full stroke at the join with zero slope and zero curvature. Each end is set on the trace and reported per end with its kind and reach, and a terminal refuses a ribbon that folds.</p>
    <p>The next step is W03, the fleur grammar on top of this structure.</p>
  </div>
</main>
</body>
</html>
"""
    path = Path(__file__).resolve().parents[1] / "docs" / "piece-model.html"
    path.write_text(html, encoding="utf-8")
    print(path)
    print(f"traces={len(info['traces'])} fit_ok={info['fit_ok']}")
    for trace in info["traces"]:
        print(f"  {trace['layer']}/{trace['name']}: fit {trace['fit_error']:.4f} mm, "
              f"rails {trace['rails']}, mirrored {trace['mirrored']}")
    print(f"terminal strip: {len(strip_info['traces'])} ribbons, "
          f"{', '.join(t['terminals'][0]['kind'] for t in strip_info['traces'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

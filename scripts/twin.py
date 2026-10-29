"""Write a self-contained HTML twin of a drawing and its design.

The SVG is inlined, so the page works from the filesystem and survives being
sent on. The design JSON, the chain report and the page size are beside it.

    python scripts/twin.py --svg out/play.svg --design out/play.json
    python scripts/twin.py --svg out/play.svg --out out/twin.html --refresh 2
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from clothoid_lab import engine  # noqa: E402
from clothoid_lab.model import Design  # noqa: E402


def embedded_design(svg: str) -> dict | None:
    match = re.search(r'<desc id="clothoid-lab-design">(.*?)</desc>', svg, re.S)
    if not match:
        return None
    try:
        return json.loads(html.unescape(match.group(1)))
    except ValueError:
        return None


def svg_inline(svg: str) -> str:
    body = svg
    body = re.sub(r'^<\?xml[^>]*\?>\s*', "", body)
    body = re.sub(r'<!DOCTYPE[^>]*>\s*', "", body, flags=re.I)
    return body


def page_size(svg: str) -> tuple[str, str]:
    width = re.search(r'width="([^"]+)"', svg)
    height = re.search(r'height="([^"]+)"', svg)
    return (width.group(1) if width else "?", height.group(1) if height else "?")


def build_html(args) -> str:
    svg = Path(args.svg).read_text(encoding="utf-8")
    data = embedded_design(svg)
    if args.design:
        data = Design.load(args.design).to_dict()
    design = Design.from_dict(data) if data else None

    width, height = page_size(svg)
    title = html.escape(design.name if design else Path(args.svg).stem)

    chain = engine.build(design) if design else None
    report = engine.report(chain) if chain else None

    rows = []
    if design:
        for index, segment in enumerate(design.segments):
            rows.append(
                "<tr>"
                f"<td>{index}</td>"
                f"<td>{segment.kd:.8g}</td>"
                f"<td>{segment.length:.4f}</td>"
                f"<td>{'inherit' if segment.kappa0 is None else f'{segment.kappa0:.8g}'}</td>"
                "</tr>"
            )

    stats = []
    if report:
        stats = [
            ("page", f"{width} x {height}"),
            ("segments", str(report["segments"])),
            ("length", f"{report['length']:.2f} mm"),
            ("tightest radius", f"{report['min_radius']:.2f} mm"),
            ("joins", "G2" if report["join_g2"] else
                      f"G1, jump {report['join_kappa_error_max']:.2e} 1/mm"),
            ("backend", report["backend"]),
        ]

    refresh = (f'<meta http-equiv="refresh" content="{args.refresh}">'
               if args.refresh else "")
    generated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    design_json = html.escape(json.dumps(data, indent=2)) if data else "no design found"

    stat_html = "\n".join(
        f"<div class='stat'><span>{html.escape(k)}</span><b>{html.escape(v)}</b></div>"
        for k, v in stats
    )
    row_html = "\n".join(rows)

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title} - clothoid-lab twin</title>
{refresh}
<style>
  :root {{ color-scheme: light dark; --ink:#111; --paper:#fff; --muted:#666; --line:#d8d8d8; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; font:14px/1.45 -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
         background:#f2f1ee; color:var(--ink); }}
  header {{ padding:18px 24px 8px; }}
  h1 {{ margin:0 0 2px; font-size:20px; letter-spacing:.01em; }}
  .sub {{ color:var(--muted); font-size:12px; }}
  main {{ display:grid; grid-template-columns:minmax(0,1fr) 360px; gap:20px; padding:16px 24px 32px; }}
  @media (max-width: 900px) {{ main {{ grid-template-columns:1fr; }} }}
  .sheet {{ background:var(--paper); border:1px solid var(--line); border-radius:6px;
            padding:18px; display:flex; align-items:center; justify-content:center; min-height:60vh; }}
  .sheet svg {{ width:100%; height:auto; max-height:78vh; }}
  aside {{ display:flex; flex-direction:column; gap:14px; }}
  .stats {{ display:grid; grid-template-columns:1fr 1fr; gap:8px; }}
  .stat {{ border:1px solid var(--line); border-radius:4px; padding:8px 10px; background:var(--paper); }}
  .stat span {{ display:block; color:var(--muted); font-size:11px; text-transform:uppercase;
                letter-spacing:.06em; }}
  .stat b {{ font-size:14px; font-weight:600; }}
  h2 {{ font-size:12px; text-transform:uppercase; letter-spacing:.08em; color:var(--muted);
        margin:6px 0 0; }}
  pre {{ margin:0; background:var(--paper); border:1px solid var(--line); border-radius:4px;
         padding:10px; overflow:auto; max-height:34vh; font-size:12px; }}
  table {{ width:100%; border-collapse:collapse; background:var(--paper); font-size:12px;
           border:1px solid var(--line); border-radius:4px; overflow:hidden; }}
  th, td {{ text-align:right; padding:5px 8px; border-bottom:1px solid var(--line); }}
  th:first-child, td:first-child {{ text-align:left; }}
  th {{ color:var(--muted); font-weight:500; font-size:11px; }}
  tr:last-child td {{ border-bottom:0; }}
  a {{ color:inherit; }}
  footer {{ padding:0 24px 24px; color:var(--muted); font-size:11px; }}
</style>
</head>
<body>
<header>
  <h1>{title}</h1>
  <div class="sub">page {html.escape(width)} x {html.escape(height)} &nbsp;|&nbsp;
    generated {generated} &nbsp;|&nbsp; <a href="{html.escape(Path(args.svg).name)}">svg</a></div>
</header>
<main>
  <section class="sheet">
    {svg_inline(svg)}
  </section>
  <aside>
    <div class="stats">{stat_html}</div>
    <h2>Segments</h2>
    <table>
      <thead><tr><th>#</th><th>kd</th><th>length</th><th>kappa0</th></tr></thead>
      <tbody>{row_html}</tbody>
    </table>
    <h2>Design</h2>
    <pre>{design_json}</pre>
  </aside>
</main>
<footer>clothoid-lab twin. The SVG above is inline; the page has no external assets.</footer>
</body>
</html>
"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--svg", default="out/play.svg")
    ap.add_argument("--design", default=None, help="design JSON; default: the SVG's own")
    ap.add_argument("--out", default=None, help="default: alongside the SVG, .html")
    ap.add_argument("--refresh", type=int, default=0,
                    help="reload the page every N seconds (0 = never)")
    args = ap.parse_args(argv)

    out = args.out or str(Path(args.svg).with_suffix(".html"))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(build_html(args), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

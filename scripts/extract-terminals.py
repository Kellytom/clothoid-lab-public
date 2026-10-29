"""Recover the terminals from the ornaments pages.

Run with the ornaments repository served locally (or pass URLs as arguments):

    python3 -m http.server 8001 --bind 127.0.0.1     # in ../ornaments
    .venv/bin/python scripts/extract-terminals.py

Writes `docs/terminals/stage-two.json`, `docs/terminals/lac.json` and
`docs/terminals/index.html`.

Every plate on those pages is static SVG with an `outline` layer, and every
band is one closed path:

    M <tip A> C ... C <tip B> L <tip B> C ... C <tip A> Z

The zero-length `L` is the far tip and the `Z` seam is the near tip, so the two
ends can be cut apart exactly. Where a taper *begins* is measured, not assumed:
the width between the rails is sampled along the band, and the terminal is the
run from each tip back to the last station that still has full width. The
measured fraction is written into the JSON, so the page's claim (14 per cent on
Stage II, 33 on the LAC page) can be checked against the drawing rather than
believed.
"""

from __future__ import annotations

import html
import json
import math
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from recover import cards, fetch, label as card_label, parse_d  # noqa: E402

SOURCES = [
    ("stage-two", "Stage II", "http://127.0.0.1:8001/stage-two.html"),
    ("lac", "Log-aesthetic family", "http://127.0.0.1:8001/LAC-log-asth-curve.html"),
]
PER_SPAN = 8
STATIONS = 96
FULL = 0.99  # a station counts as full width at 99 per cent of the band's max

OUTLINE_RE = re.compile(
    r'<g[^>]*inkscape:label="outline"[^>]*>(.*?)</g>', re.DOTALL)
PATH_RE = re.compile(r"<path[^>]*\sid=\"([^\"]+)\"[^>]*\sd=\"([^\"]+)\"[^>]*/>")


def as_span(values) -> dict:
    return {"p0": None,
            "c1": (values[0], values[1]), "c2": (values[2], values[3]),
            "p3": (values[4], values[5])}


def chain(spans: list[dict], start=None) -> list[dict]:
    start = spans[0]["c1"] if start is None else start
    out = []
    for span in spans:
        out.append({"p0": start, "c1": span["c1"], "c2": span["c2"],
                    "p3": span["p3"]})
        start = span["p3"]
    return out


def reverse(spans: list[dict]) -> list[dict]:
    return [{"p0": s["p3"], "c1": s["c2"], "c2": s["c1"], "p3": s["p0"]}
            for s in reversed(spans)]


def split_band(tokens):
    """Two rails plus the two tips of one closed band outline."""
    start = None
    spans = []
    tip_b = None
    seam = None
    for cmd, values in tokens:
        if cmd == "M":
            start = (values[0], values[1])
        elif cmd == "C":
            spans.append(as_span(values))
        elif cmd == "L":
            point = (values[0], values[1])
            if tip_b is None:
                tip_b, seam = point, len(spans)
            elif point != tip_b:
                raise ValueError("unexpected second straight seam")
        elif cmd == "Z":
            break
    if start is None or tip_b is None or not seam:
        raise ValueError("outline is not the expected two-rail band")
    spans = chain(spans, start)
    return spans[:seam], spans[seam:], start, tip_b


def cubic(span, t):
    u = 1 - t
    x = (u ** 3 * span["p0"][0] + 3 * u * u * t * span["c1"][0]
         + 3 * u * t * t * span["c2"][0] + t ** 3 * span["p3"][0])
    y = (u ** 3 * span["p0"][1] + 3 * u * u * t * span["c1"][1]
         + 3 * u * t * t * span["c2"][1] + t ** 3 * span["p3"][1])
    return (x, y)


def samples(spans: list[dict], per: int = PER_SPAN):
    """Points and cumulative arc length along a rail, tip to tip."""
    points = [spans[0]["p0"]]
    length = [0.0]
    for span in spans:
        previous = span["p0"]
        for i in range(1, per + 1):
            point = cubic(span, i / per)
            length.append(length[-1] + math.dist(previous, point))
            points.append(point)
            previous = point
    return points, length


def at(points, length, s):
    """The point at arc length s, by linear search; rails are short."""
    if s <= 0:
        return points[0]
    if s >= length[-1]:
        return points[-1]
    lo, hi = 0, len(length) - 1
    while lo < hi - 1:
        mid = (lo + hi) // 2
        if length[mid] <= s:
            lo = mid
        else:
            hi = mid
    span = length[hi] - length[lo]
    f = 0 if span <= 0 else (s - length[lo]) / span
    return (points[lo][0] + (points[hi][0] - points[lo][0]) * f,
            points[lo][1] + (points[hi][1] - points[lo][1]) * f)


def width_profile(rail_a, rail_b, n: int = STATIONS):
    """Width along one rail, as the nearest distance to the other rail.

    Station-by-station pairing is wrong here: a cap or a curved rail shifts the
    correspondence by several per cent of the run and invents a taper. Nearest
    distance needs no correspondence and gives the same answer on a straight
    band with square ends.
    """
    pa, la = samples(rail_a)
    pb, _ = samples(rail_b)
    widths = []
    for i in range(n + 1):
        u = i / n
        widths.append(min(math.dist(at(pa, la, u * la[-1]), q) for q in pb))
    return widths, la[-1]


def plateau(widths, total):
    """The two taper fractions, measured from the full-width run between them.

    Width is zero at each tip and peaks between them, so the plateau between
    the first and last full-width station is the part of the band that is not
    a terminal. Each fraction is a share of the whole run.
    """
    peak = max(widths)
    idx = [i for i, w in enumerate(widths) if w >= FULL * peak]
    n = len(widths) - 1
    near = total * min(idx) / n
    far = total - total * max(idx) / n
    return near / total, far / total, peak


def tail(spans: list[dict], length: float) -> list[dict]:
    """The spans nearest the tip that together cover about `length`."""
    out = []
    covered = 0.0
    for span in reversed(spans):
        out.append(span)
        covered += span_len(span)
        if covered >= length:
            break
    return list(reversed(out))


def span_len(span, n: int = 8) -> float:
    total = 0.0
    previous = span["p0"]
    for i in range(1, n + 1):
        point = cubic(span, i / n)
        total += math.dist(previous, point)
        previous = point
    return total


def cut_terminal(inbound, outbound, fraction: float) -> dict:
    """Join -> tip -> join across one band end, `fraction` of each rail long."""
    keep_a = min(0.5 * sum(span_len(s) for s in inbound),
                 max(1.0, 1.06 * fraction * sum(span_len(s) for s in inbound)))
    keep_b = min(0.5 * sum(span_len(s) for s in outbound),
                 max(1.0, 1.06 * fraction * sum(span_len(s) for s in outbound)))
    side = tail(inbound, keep_a)
    back = reverse(tail(outbound, keep_b))
    spans = chain(side + back)
    return {"spans": spans, "length": sum(span_len(s) for s in spans),
            "cut": round(keep_a, 1)}


def d_for(spans: list[dict]) -> str:
    parts = [f"M {spans[0]['p0'][0]:.1f} {spans[0]['p0'][1]:.1f}"]
    for span in spans:
        parts.append("C {:.1f} {:.1f} {:.1f} {:.1f} {:.1f} {:.1f}".format(
            *span["c1"], *span["c2"], *span["p3"]))
    parts.append("Z")
    return " ".join(parts)


def read_page(name: str, label: str, source: str) -> dict:
    page = fetch(source)
    figures = []
    for card in cards(page):
        figure_label, title, meta = card_label(card)
        outline = OUTLINE_RE.search(card)
        if not (figure_label and outline):
            continue
        ends = []
        for path_id, d in PATH_RE.findall(outline.group(1)):
            rail_a, rail_b, tip_a, tip_b = split_band(parse_d(d))
            widths, total = width_profile(rail_a, rail_b)
            near_fraction, far_fraction, peak = plateau(widths, total)
            for end, inbound, outbound, tip, fraction in (
                ("far", rail_a, reverse(rail_b), tip_b, far_fraction),
                ("near", rail_b, reverse(rail_a), tip_a, near_fraction),
            ):
                piece = cut_terminal(inbound, outbound, fraction)
                piece.update({
                    "end": end, "tip": list(tip), "plate": path_id,
                    "figure": figure_label,
                    "taper_fraction": round(fraction, 4),
                    "full_width": round(peak, 1),
                    "d": d_for(piece["spans"]),
                })
                ends.append(piece)
        figures.append({
            "figure": figure_label,
            "title": title,
            "family": meta.get("family", ""),
            "plate": meta.get("plate", ""),
            "k0": meta.get("k0", ""),
            "k1": meta.get("k1", ""),
            "terminals": ends,
        })
    return {
        "name": name, "label": label, "source": source,
        "note": "Outline ends cut at the L and Z seams, join to tip to join, "
                "in page units. taper_fraction is measured, not assumed.",
        "figures": figures,
    }


def gallery(data: list[dict]) -> str:
    blocks = []
    for page in data:
        rows = []
        for figure in page["figures"]:
            cells = []
            for terminal in figure["terminals"]:
                spans = terminal["spans"]
                xs = [p[0] for s in spans for p in (s["p0"], s["c1"], s["c2"], s["p3"])]
                ys = [p[1] for s in spans for p in (s["p0"], s["c1"], s["c2"], s["p3"])]
                pad = max(6.0, 0.06 * max(max(xs) - min(xs), max(ys) - min(ys)))
                x0, y0 = min(xs) - pad, min(ys) - pad
                w = max(xs) - min(xs) + 2 * pad
                h = max(ys) - min(ys) + 2 * pad
                cells.append(
                    f'<figure><svg viewBox="{x0:.1f} {y0:.1f} {w:.1f} {h:.1f}" '
                    f'role="img" aria-label="{figure["figure"]} {terminal["end"]}">'
                    f'<path d="{terminal["d"]}" fill="#2E2413" fill-opacity="0.14" '
                    f'stroke="#2E2413" stroke-width="{max(w, h) / 90:.2f}" '
                    f'stroke-linejoin="round"/></svg>'
                    f'<figcaption>{terminal["end"][0].upper()} · '
                    f'{terminal["taper_fraction"] * 100:.0f}%</figcaption></figure>')
            rows.append(
                f'<tr><th><b>{figure["figure"]}</b><span>{html.escape(figure["title"])}</span>'
                f'<em>{figure["family"]} · {figure["plate"]}</em></th>'
                f'<td class="ends">{"".join(cells)}</td></tr>')
        blocks.append(
            f'<section><h2>{html.escape(page["label"])}</h2>'
            f'<p class="meta">{html.escape(page["source"])} · '
            f'{sum(len(f["terminals"]) for f in page["figures"])} terminals</p>'
            f'<table>{"".join(rows)}</table></section>')
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Recovered terminals</title>
<style>
:root {{ color-scheme: light; --paper:#f6f1e4; --card:#fffdf7; --ink:#2e2413;
  --muted:#7b6c4e; --line:#d8ccae; --gold:#8c6a21;
  --mono: ui-monospace,"SF Mono",Menlo,monospace; --serif:"EB Garamond",Georgia,serif; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--paper); color:var(--ink); font:16px/1.55 var(--serif); }}
main {{ max-width:1000px; margin:0 auto; padding:34px 22px 70px; }}
h1 {{ font-size:28px; margin:0 0 4px; }}
p.lead {{ color:var(--gold); margin:0 0 18px; }}
h2 {{ font:600 11px/1.2 var(--mono); letter-spacing:.12em; text-transform:uppercase;
  color:var(--muted); margin:28px 0 8px; }}
meta {{ color:var(--muted); }}
p.meta {{ font:12px var(--mono); color:var(--muted); margin:0 0 10px; }}
table {{ border-collapse:collapse; width:100%; }}
th,td {{ border-top:1px solid var(--line); padding:8px 6px; text-align:left; vertical-align:top; }}
th {{ width:190px; font-weight:400; }}
th b {{ display:block; font:600 12px var(--mono); }}
th span {{ display:block; font-size:13px; }}
th em {{ display:block; font:11px var(--mono); color:var(--muted); }}
td.ends {{ display:flex; flex-wrap:wrap; gap:10px; }}
figure {{ margin:0; width:120px; }}
figure svg {{ display:block; width:120px; height:64px; background:#fff; border:1px solid var(--line); }}
figcaption {{ font:10px var(--mono); color:var(--muted); margin-top:2px; }}
code {{ font:12px var(--mono); }}
</style></head><body><main>
<h1>Recovered terminals</h1>
<p class="lead">The ends of the old outline bands, cut at their seams, before anything is redrawn.</p>
<p>Each cell is one end of one band: join on the left, tip in the middle, join back on the right.
The percentage is the measured taper fraction — how much of the band the taper occupies — not the value the source page claims.</p>
{"".join(blocks)}
</main></body></html>
"""


def main() -> int:
    sources = SOURCES if len(sys.argv) == 1 else [
        (Path(arg).stem.lower(), Path(arg).stem, arg) for arg in sys.argv[1:]
    ]
    out_dir = ROOT / "docs" / "terminals"
    out_dir.mkdir(parents=True, exist_ok=True)
    data = []
    for name, label, source in sources:
        page = read_page(name, label, source)
        data.append(page)
        (out_dir / f"{name}.json").write_text(
            json.dumps(page, indent=1) + "\n", encoding="utf-8")
        total = sum(len(f["terminals"]) for f in page["figures"])
        print(f"{label}: {len(page['figures'])} plates, {total} terminals -> "
              f"{out_dir / (name + '.json')}")
        fractions = [t["taper_fraction"] for f in page["figures"] for t in f["terminals"]]
        if fractions:
            print(f"  measured taper fraction {min(fractions) * 100:.0f}-"
                  f"{max(fractions) * 100:.0f}%")
    (out_dir / "index.html").write_text(gallery(data), encoding="utf-8")
    print(f"gallery -> {out_dir / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

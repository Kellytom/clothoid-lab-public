"""Recover the Stage II and LAC spirals from the ornaments pages.

    python3 -m http.server 8001 --bind 127.0.0.1     # in ../ornaments
    .venv/bin/python scripts/extract-spirals.py

Writes `docs/spirals/stage-two.json`, `docs/spirals/lac.json` and
`docs/spirals/index.html`.

Each plate carries a `spine` layer. Every path there is one continuous spine,
split into cubics at 45 degrees of turn, and tagged with `data-span`: `line`,
`arc`, `euler`, `logaesthetic`, `reflected`, `hyperbezier` or `member`. That
tag is the important part — it says which ideal the span was drawn from, so the
recovered data can be compared with our own clothoid chains span by span.

Coordinates are the page's own: 3125-unit lattice, **y down**, as SVG writes
them. Nothing here is flipped; the rest of the project is y up at output, so a
consumer must flip once if it wants design space.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from recover import cards, d_for, fetch, label, parse_d, spans_from  # noqa: E402

SOURCES = [
    ("stage-two", "Stage II", "http://127.0.0.1:8001/stage-two.html"),
    ("lac", "Log-aesthetic family", "http://127.0.0.1:8001/LAC-log-asth-curve.html"),
]
SPINE_RE = re.compile(r'<g[^>]*inkscape:label="spine"[^>]*>(.*?)</g>', re.DOTALL)
PATH_RE = re.compile(r"<path\b[^>]*>")
ATTR_RE = re.compile(r'([a-zA-Z:-]+)="([^"]*)"')

# One colour per ideal, kept clear of the page's own palette.
COLOURS = {
    "line": "#8C6A21",
    "arc": "#B23A2B",
    "euler": "#1F6F4A",
    "logaesthetic": "#2C5AA0",
    "reflected": "#7A4E9E",
    "hyperbezier": "#B07A1E",
    "member": "#55503F",
}


def spine_paths(card: str) -> list[dict]:
    """Every spine path on one card, with its ideal and its cubics."""
    group = SPINE_RE.search(card)
    if not group:
        return []
    out = []
    for tag in PATH_RE.findall(group.group(1)):
        attrs = dict(ATTR_RE.findall(tag))
        if "d" not in attrs:
            continue
        spans = spans_from(parse_d(attrs["d"]))
        if not spans:
            continue
        out.append({
            "id": attrs.get("id", ""),
            "kind": attrs.get("data-span", "unknown"),
            "stroke": attrs.get("stroke", ""),
            "spans": spans,
            "d": d_for(spans),
        })
    return out


def bbox(spines: list[dict]):
    xs, ys = [], []
    for spine in spines:
        for span in spine["spans"]:
            for key in ("p0", "c1", "c2", "p3"):
                xs.append(span[key][0])
                ys.append(span[key][1])
    return min(xs), min(ys), max(xs), max(ys)


def read_page(name: str, title: str, source: str) -> dict:
    page = fetch(source)
    figures = []
    for card in cards(page):
        figure_label, card_title, meta = label(card)
        spines = spine_paths(card)
        if not spines:
            continue
        figures.append({
            "figure": figure_label,
            "title": card_title,
            "family": meta.get("family", ""),
            "plate": meta.get("plate", ""),
            "k0": meta.get("k0", ""),
            "k1": meta.get("k1", ""),
            "spines": spines,
        })
    return {
        "name": name,
        "label": title,
        "source": source,
        "space": "page units on a 3125 lattice, y down (SVG), not design space",
        "figures": figures,
    }


def gallery(pages: list[dict]) -> str:
    sections = []
    for page in pages:
        rows = []
        for figure in page["figures"]:
            spines = figure["spines"]
            x0, y0, x1, y1 = bbox(spines)
            size = max(x1 - x0, y1 - y0)
            pad = size * 0.08
            paths = "".join(
                f'<path d="{spine["d"]}" fill="none" '
                f'stroke="{COLOURS.get(spine["kind"], "#55503F")}" '
                f'stroke-width="{size / 120:.1f}" stroke-linecap="round"/>'
                for spine in spines)
            kinds = " · ".join(dict.fromkeys(s["kind"] for s in spines))
            rows.append(
                f'<tr><th><b>{figure["figure"]}</b>'
                f'<span>{figure["title"]}</span>'
                f'<em>{figure["family"]} · {figure["plate"]}</em>'
                f'<i>{len(spines)} spines · {kinds}</i></th>'
                f'<td><svg viewBox="{x0 - pad:.0f} {y0 - pad:.0f} '
                f'{x1 - x0 + 2 * pad:.0f} {y1 - y0 + 2 * pad:.0f}" '
                f'role="img" aria-label="{figure["figure"]}">'
                f'{paths}</svg></td></tr>')
        count = sum(len(f["spines"]) for f in page["figures"])
        sections.append(
            f'<section><h2>{page["label"]}</h2>'
            f'<p class="meta">{page["source"]} · {count} spines</p>'
            f'<table>{"".join(rows)}</table></section>')

    legend = " ".join(
        f'<span class="key"><i style="background:{colour}"></i>{kind}</span>'
        for kind, colour in COLOURS.items())
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Recovered spirals</title>
<style>
:root {{ color-scheme: light; --paper:#f6f1e4; --card:#fffdf7; --ink:#2e2413;
  --muted:#7b6c4e; --line:#d8ccae; --gold:#8c6a21;
  --mono: ui-monospace,"SF Mono",Menlo,monospace; --serif:"EB Garamond",Georgia,serif; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--paper); color:var(--ink); font:16px/1.55 var(--serif); }}
main {{ max-width:1060px; margin:0 auto; padding:34px 22px 70px; }}
h1 {{ font-size:28px; margin:0 0 4px; }}
p.lead {{ color:var(--gold); margin:0 0 14px; }}
h2 {{ font:600 11px/1.2 var(--mono); letter-spacing:.12em; text-transform:uppercase;
  color:var(--muted); margin:26px 0 6px; }}
p.meta {{ font:12px var(--mono); color:var(--muted); margin:0 0 10px; }}
.key {{ font:11px var(--mono); color:var(--muted); margin-right:12px; white-space:nowrap; }}
.key i {{ display:inline-block; width:14px; height:3px; margin-right:5px; vertical-align:middle; }}
table {{ border-collapse:collapse; width:100%; }}
th,td {{ border-top:1px solid var(--line); padding:8px 6px; text-align:left; vertical-align:top; }}
th {{ width:230px; font-weight:400; }}
th b {{ display:block; font:600 12px var(--mono); }}
th span {{ display:block; font-size:13px; }}
th em, th i {{ display:block; font:11px var(--mono); color:var(--muted); font-style:normal; }}
td svg {{ display:block; width:100%; max-width:520px; height:160px; background:#fff; border:1px solid var(--line); }}
</style></head><body><main>
<h1>Recovered spirals</h1>
<p class="lead">Every spine on the Stage II and log-aesthetic pages, split where the page split it.</p>
<p>Colour is the ideal the span was drawn from, not the stroke width or the family of the plate.
Coordinates are the page's own 3125-unit lattice with y down; nothing has been flipped or rescaled
beyond the viewBox.</p>
<p>{legend}</p>
{"".join(sections)}
</main></body></html>
"""


def main() -> int:
    sources = SOURCES if len(sys.argv) == 1 else [
        (Path(arg).stem.lower(), Path(arg).stem, arg) for arg in sys.argv[1:]
    ]
    out_dir = ROOT / "docs" / "spirals"
    out_dir.mkdir(parents=True, exist_ok=True)
    pages = []
    for name, title, source in sources:
        page = read_page(name, title, source)
        pages.append(page)
        (out_dir / f"{name}.json").write_text(
            json.dumps(page, indent=1) + "\n", encoding="utf-8")
        spines = [s for f in page["figures"] for s in f["spines"]]
        kinds = {}
        for spine in spines:
            kinds[spine["kind"]] = kinds.get(spine["kind"], 0) + 1
        print(f"{title}: {len(page['figures'])} plates, {len(spines)} spines -> "
              f"{out_dir / (name + '.json')}")
        print("  " + ", ".join(f"{k} {v}" for k, v in sorted(kinds.items())))
    (out_dir / "index.html").write_text(gallery(pages), encoding="utf-8")
    print(f"gallery -> {out_dir / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

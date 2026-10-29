"""Shared readers for the ornaments recovery scripts.

Both `extract-terminals.py` and `extract-spirals.py` read static SVG pages from
the ornaments repository. This module holds the parts they have in common: fetch,
split the page into cards, and read absolute path data. Keep it small and
dependency-free; it is a scraper for our own pages, not a general SVG parser.
"""

from __future__ import annotations

import re
import urllib.request
from pathlib import Path

FIG_RE = re.compile(r'class="fig">([^<]*)<')
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.DOTALL)
META_RE = re.compile(r'data-(plate|family|k0|k1|curve)="([^"]*)"')
TOKEN_RE = re.compile(r"[MCLZ]|-?\d+(?:\.\d+)?(?:e-?\d+)?")


def fetch(source: str) -> str:
    if source.startswith(("http://", "https://")):
        with urllib.request.urlopen(source, timeout=15) as response:
            return response.read().decode("utf-8")
    return Path(source).read_text(encoding="utf-8")


def cards(page: str) -> list[str]:
    """The pages are a run of plain card divs, one plate SVG each."""
    parts = page.split('<div class="card">')[1:]
    out = []
    for part in parts:
        end = part.find('<div class="card">')
        out.append(part if end < 0 else part[:end])
    return out


def parse_d(d: str) -> list[tuple[str, list[float]]]:
    """M, C, L and Z with absolute numbers, which is what these pages emit."""
    tokens = TOKEN_RE.findall(d)
    out: list[tuple[str, list[float]]] = []
    i = 0
    while i < len(tokens):
        cmd = tokens[i]
        if cmd in ("M", "L"):
            out.append((cmd, [float(tokens[i + 1]), float(tokens[i + 2])]))
            i += 3
        elif cmd == "C":
            out.append((cmd, [float(v) for v in tokens[i + 1:i + 7]]))
            i += 7
        elif cmd == "Z":
            out.append(("Z", []))
            i += 1
        else:
            raise ValueError(f"unexpected path token {cmd!r}")
    return out


def spans_from(tokens: list[tuple[str, list[float]]]) -> list[dict]:
    """Cubic spans with their start point, from parsed path data."""
    spans: list[dict] = []
    start = None
    for cmd, values in tokens:
        if cmd == "M":
            start = (values[0], values[1])
        elif cmd == "C":
            if start is None:
                raise ValueError("C before M")
            spans.append({
                "p0": start,
                "c1": (values[0], values[1]),
                "c2": (values[2], values[3]),
                "p3": (values[4], values[5]),
            })
            start = (values[4], values[5])
        elif cmd in ("L", "Z"):
            break
    return spans


def d_for(spans: list[dict], precision: int = 1) -> str:
    parts = [f"M {spans[0]['p0'][0]:.{precision}f} {spans[0]['p0'][1]:.{precision}f}"]
    for span in spans:
        parts.append("C {:.{p}f} {:.{p}f} {:.{p}f} {:.{p}f} {:.{p}f} {:.{p}f}".format(
            *span["c1"], *span["c2"], *span["p3"], p=precision))
    return " ".join(parts)


def label(card: str) -> tuple[str, str, dict]:
    """Figure label, title and data-attributes of one card."""
    import html

    fig = FIG_RE.search(card)
    title = TITLE_RE.search(card)
    meta = dict(META_RE.findall(card))
    return (fig.group(1).strip() if fig else "",
            html.unescape(title.group(1).strip()) if title else "",
            meta)

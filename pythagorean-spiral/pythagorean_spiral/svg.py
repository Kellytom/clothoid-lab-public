"""A small SVG writer for these chains.

Design coordinates are +y up, as everywhere in clothoid-lab.  SVG's y is down,
so the flip happens here, once, when the points are written.  The page is
millimetres and the drawing is scaled to fit, so a chain whose integers run to
10^5 still lands on a 200 mm sheet.
"""

from __future__ import annotations

import math


def _fmt(v: float) -> str:
    return f"{v:.3f}".rstrip("0").rstrip(".")


def document(path, spans: list[dict], page=(200.0, 200.0), margin: float = 10.0,
             title: str = "pythagorean-spiral", marks: bool = True) -> str:
    pts = path.floats()
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    w0 = max(xs) - min(xs) or 1.0
    h0 = max(ys) - min(ys) or 1.0
    W, H = page
    scale = min((W - 2 * margin) / w0, (H - 2 * margin) / h0)

    def place(x, y):
        """Design (y up) to page (y down).  The only flip in the writer."""
        return (margin + (x - min(xs)) * scale,
                H - margin - (y - min(ys)) * scale)

    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{_fmt(W)}mm" '
        f'height="{_fmt(H)}mm" viewBox="0 0 {W} {H}">',
        f"<title>{title}</title>",
        f"<desc>{len(path.turns)} chords, exact rationals, y flipped at output"
        f"</desc>",
        f'<g fill="none" stroke="#222" stroke-width="0.6" '
        f'stroke-linecap="round" stroke-linejoin="round">',
    ]

    if spans:
        d = []
        first = spans[0]["p0"]
        p = place(*first)
        d.append(f"M {_fmt(p[0])},{_fmt(p[1])}")
        for s in spans:
            c1, c2, p3 = place(*s["c1"]), place(*s["c2"]), place(*s["p3"])
            d.append(f"C {_fmt(c1[0])},{_fmt(c1[1])} {_fmt(c2[0])},{_fmt(c2[1])} "
                     f"{_fmt(p3[0])},{_fmt(p3[1])}")
        out.append(f'<path d="{" ".join(d)}"/>')
    out.append("</g>")

    if marks:
        out.append('<g fill="#b02818" stroke="none">')
        for x, y in pts:
            px, py = place(x, y)
            out.append(f'<circle cx="{_fmt(px)}" cy="{_fmt(py)}" r="1.1"/>')
        out.append("</g>")

        ex, ey = place(*pts[-1])
        out.append(f'<circle cx="{_fmt(ex)}" cy="{_fmt(ey)}" r="2.2" '
                   f'fill="#1f5fa8"/>')
    out.append("</svg>")
    return "\n".join(out) + "\n"

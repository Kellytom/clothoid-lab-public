"""SVG writing: absolute cubic paths, millimetre units, no surprises.

Rules that make the file open cleanly in Inkscape and stay node-editable:

- Absolute commands only, one `M` and then `C` triples. No relative arithmetic.
- Numbers are fixed-point at a stated precision, never exponent notation. SVG's
  path grammar is stricter than Python's float formatting, and `1e-05` in a `d`
  attribute is exactly the kind of thing that opens fine in one tool and not
  the next.
- One user unit is one millimetre. The document carries width and height in mm
  and a viewBox in the same numbers, so Inkscape's node readout is in mm and no
  transform is needed.
- The design JSON rides along in `<metadata>`, so a round trip has something to
  come back to.

Path data lives in a plain string. A path library is not needed to write `M`
and `C`, and adding one would be a dependency earning nothing.
"""

from __future__ import annotations

import json
import math
from xml.sax.saxutils import escape as _xml_text


def num(value: float, prec: int = 4) -> str:
    """Fixed-point, trailing zeros trimmed, no exponent, no negative zero."""
    if not math.isfinite(value):
        raise ValueError(f"non-finite coordinate: {value}")
    q = round(value, prec)
    if q == 0:
        return "0"
    text = f"{q:.{prec}f}".rstrip("0").rstrip(".")
    return text if text not in ("", "-0") else "0"


def path_d(spans: list[dict], prec: int = 4, close: bool = False) -> str:
    """Absolute `M` then `C` for every span, as one path string."""
    if not spans:
        raise ValueError("no spans to write")
    first = spans[0]["p0"]
    parts = [f"M {num(first[0], prec)},{num(first[1], prec)}"]
    for span in spans:
        parts.append(
            "C {} {}, {} {}, {} {}".format(
                num(span["c1"][0], prec), num(span["c1"][1], prec),
                num(span["c2"][0], prec), num(span["c2"][1], prec),
                num(span["p3"][0], prec), num(span["p3"][1], prec),
            )
        )
    if close:
        parts.append("Z")
    return " ".join(parts)


SODIPODI = "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
INKSCAPE = "http://www.inkscape.org/namespaces/inkscape"


def read_view(path) -> str | None:
    """The Inkscape view element from an existing file, if it has one.

    Zoom, pan, document units and the current layer live in `sodipodi:namedview`,
    which Inkscape writes when it saves. Our rebuilds replace the drawing, so
    without this the view would be thrown away every time and the document would
    re-fit itself on load. Carrying it over is what makes the zoom stay put.
    """
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return None
    start = text.find("<sodipodi:namedview")
    if start < 0:
        return None
    close = text.find("</sodipodi:namedview>", start)
    if close >= 0:
        return text[start:close + len("</sodipodi:namedview>")]
    self_closing = text.find("/>", start)
    if self_closing >= 0:
        return text[start:self_closing + 2]
    return None


def _bbox(spans: list[dict]) -> tuple[float, float, float, float]:
    xs: list[float] = []
    ys: list[float] = []
    for span in spans:
        for px, py in (span["p0"], span["c1"], span["c2"], span["p3"]):
            xs.append(px)
            ys.append(py)
    return min(xs), min(ys), max(xs), max(ys)


def document(design, chain=None, spine=None, rails=None,
             prec: int = 4, margin: float = 5.0, stroke: float | None = None,
             page: tuple[float, float] | None = None,
             frame: tuple[float, float] | None = None,
             view: str | None = None,
             annotations: list[dict] | None = None,
             groups: list[tuple[str, list[dict], float | None]] | None = None,
             linecap: str = "round") -> str:
    """One SVG: the spine, one path per rail, mm units, JSON in the metadata.

    `annotations` are optional standard SVG marks (lines, circles, text) placed
    with the drawing. Coordinates are in design units; line widths, radii and
    font sizes are in page millimetres. Set `front` to draw above the ink.

    `groups` lets a piece supply several named traces instead of the usual
    single spine plus rails. Each tuple is (name, spans, distance-or-None).

    `linecap` sets the stroke cap for the ink group. The single-design default
    stays `round`; a piece passes `butt`, because a ribbon end is geometry, not
    a brush tip, and a round hairline cap would blur the terminal vocabulary.
    """
    if groups is None:
        groups = [("spine", spine, None)]
        for rail in rails or []:
            groups.append((f"rail {num(rail['distance'], 3)}", rail["spans"], rail["distance"]))

    all_spans = [s for _, spans, _ in groups for s in spans]
    x0, y0, x1, y1 = _bbox(all_spans)
    content_w, content_h = x1 - x0, y1 - y0

    # Three ways to size the sheet, and the difference matters in a viewer.
    #
    # `frame` scales the drawing to fill a stated sheet. The sheet is constant,
    # so the viewer's fit-page lands in the same place every time and a parameter
    # change is visible at a constant scale. Absolute size is given up, and the
    # scale is reported.
    #
    # `page` states a sheet without scaling, so millimetres stay true and the
    # drawing moves inside the sheet.
    #
    # Neither means the sheet follows the drawing, which is right for a one-off
    # and wrong in a reload loop, because the view re-fits on every change.
    scale = 1.0
    if frame is not None:
        fw, fh = float(frame[0]), float(frame[1])
        inner_w, inner_h = fw - 2 * margin, fh - 2 * margin
        if inner_w <= 0 or inner_h <= 0:
            raise ValueError(f"frame {fw:g}x{fh:g} mm leaves no room inside a {margin:g} mm margin")
        if content_w <= 0 or content_h <= 0:
            raise ValueError("the drawing has no extent to scale")
        scale = min(inner_w / content_w, inner_h / content_h)
        width, height = fw, fh
        pad_x = (fw - content_w * scale) / 2.0
        pad_y = (fh - content_h * scale) / 2.0
    elif page is not None:
        width, height = float(page[0]), float(page[1])
        if width <= content_w or height <= content_h:
            raise ValueError(
                f"page {width:g}x{height:g} mm is smaller than the drawing "
                f"({content_w:.1f}x{content_h:.1f} mm)"
            )
        pad_x = (width - content_w) / 2.0
        pad_y = (height - content_h) / 2.0
    else:
        width, height = content_w + 2 * margin, content_h + 2 * margin
        pad_x = pad_y = margin

    # SVG's native y is down. The design is y-up, so the writer flips at this
    # boundary and nowhere else: y' = pad_y + (y1 - y). The design JSON and all
    # geometry remain y-up.
    def shift(spans):
        def move(p):
            return ((p[0] - x0) * scale + pad_x,
                    pad_y + (y1 - p[1]) * scale)
        return [{**span, "p0": move(span["p0"]), "c1": move(span["c1"]),
                 "c2": move(span["c2"]), "p3": move(span["p3"])} for span in spans]

    def place(x, y):
        return ((x - x0) * scale + pad_x,
                pad_y + (y1 - y) * scale)

    def annotations_markup(front: bool) -> list[str]:
        marks = []
        for mark in annotations or []:
            if bool(mark.get("front", False)) != front:
                continue
            kind = mark.get("kind")
            if kind == "line":
                x1, y1 = place(float(mark["x1"]), float(mark["y1"]))
                x2, y2 = place(float(mark["x2"]), float(mark["y2"]))
                dash = (f' stroke-dasharray="{mark["dash"]}"'
                        if mark.get("dash") else "")
                marks.append(
                    f'    <line x1="{num(x1, prec)}" y1="{num(y1, prec)}" '
                    f'x2="{num(x2, prec)}" y2="{num(y2, prec)}" '
                    f'stroke="{mark.get("stroke", "#c4c4c4")}" '
                    f'stroke-width="{num(float(mark.get("width", 0.25)), prec)}"'
                    f'{dash}/>')
            elif kind == "circle":
                cx, cy = place(float(mark["x"]), float(mark["y"]))
                marks.append(
                    f'    <circle cx="{num(cx, prec)}" cy="{num(cy, prec)}" '
                    f'r="{num(float(mark.get("r", 1.0)), prec)}" '
                    f'fill="{mark.get("fill", "#555555")}"/>')
            elif kind == "text":
                x, y = place(float(mark["x"]), float(mark["y"]))
                x += float(mark.get("dx", 0.0))
                y += float(mark.get("dy", 0.0))
                marks.append(
                    f'    <text x="{num(x, prec)}" y="{num(y, prec)}" '
                    f'font-family="Helvetica, Arial, sans-serif" '
                    f'font-size="{num(float(mark.get("size", 3.2)), prec)}" '
                    f'fill="{mark.get("fill", "#777777")}" '
                    f'text-anchor="{mark.get("anchor", "start")}">'
                    f'{_xml_text(str(mark["text"]))}</text>')
        return marks

    # Ink weight follows the geometry when the geometry is scaled, or a 7x
    # enlargement would draw hairlines.
    stroke = (design.stroke if stroke is None else stroke) * scale
    width_mm, height_mm = num(width, prec), num(height, prec)
    ns = (f'     xmlns:sodipodi="{SODIPODI}"\n'
          f'     xmlns:inkscape="{INKSCAPE}"\n') if view else ""
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg"',
        ns + '     version="1.1"',
        f'     width="{width_mm}mm" height="{height_mm}mm"',
        f'     viewBox="0 0 {width_mm} {height_mm}">',
    ]
    if view:
        out.append("  " + view.strip())
    out += [
        f"  <title>{_escape(design.name)}</title>",
        f'  <desc id="clothoid-lab-design">{_escape(design.to_json())}</desc>',
    ]
    behind = annotations_markup(False)
    if behind:
        out.append('  <g id="annotation-lines">')
        out.extend(behind)
        out.append("  </g>")
    out += [
        f'  <g id="clothoid" fill="none" stroke="#000000" stroke-linecap="{linecap}"',
        f'     stroke-width="{num(stroke, prec)}">',
    ]
    for index, (name, spans, _) in enumerate(groups):
        gid = _slug(name) or ("spine" if index == 0 else f"rail-{index}")
        out.append(f'    <path id="{gid}" d="{path_d(shift(spans), prec)}"/>')
    out.append("  </g>")
    front = annotations_markup(True)
    if front:
        out.append('  <g id="annotations">')
        out.extend(front)
        out.append("  </g>")
    out.append("</svg>")
    return "\n".join(out) + "\n"


def _slug(name: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in name).strip("-")


def _escape(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                .replace('"', "&quot;"))


def write(path, text: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def parse_d(d: str) -> list[tuple[str, list[float]]]:
    """A small reader for our own path data, for the round-trip tests.

    Not a general SVG parser: it reads `M`, `C`, `L` and `Z` with absolute
    coordinates, which is what this writer emits.
    """
    tokens = d.replace(",", " ").split()
    out: list[tuple[str, list[float]]] = []
    i = 0
    while i < len(tokens):
        cmd = tokens[i]
        if cmd in ("M", "C", "L"):
            n = {"M": 2, "L": 2, "C": 6}[cmd]
            vals = [float(tokens[i + 1 + j]) for j in range(n)]
            out.append((cmd, vals))
            i += 1 + n
        elif cmd == "Z":
            out.append(("Z", []))
            i += 1
        else:
            raise ValueError(f"unsupported path token: {cmd}")
    return out


def metadata_design(svg_text: str) -> dict:
    """Recover the design JSON from a file this writer produced."""
    marker = '<desc id="clothoid-lab-design">'
    start = svg_text.find(marker)
    end = svg_text.find("</desc>", start)
    if start < 0 or end < 0:
        raise ValueError("no design metadata in this file")
    raw = svg_text[start + len(marker):end]
    raw = (raw.replace("&quot;", '"').replace("&lt;", "<")
              .replace("&gt;", ">").replace("&amp;", "&"))
    return json.loads(raw)

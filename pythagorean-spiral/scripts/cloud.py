"""Generate docs/CLOUD.md and its HTML twin: a layered cloud as a veil.

    python scripts/cloud.py
"""

from __future__ import annotations

import math
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from pythagorean_spiral import place, veil as veil_mod  # noqa: E402
from pythagorean_spiral.exact import Dir  # noqa: E402
from pythagorean_spiral.spiral import Spiral  # noqa: E402
from pythagorean_spiral.triples import for_angle  # noqa: E402

import explainer as ex  # noqa: E402
import cloud_form as cf  # noqa: E402

FIG = ex.FIG
REF = ROOT.parent / "reference"
RAW = FIG / "cloud-photo-raw.png"
STATUE = FIG / "cloud-photo-statue.png"
COLOUR_STATUE = FIG / "cloud-colour-statue.png"
COLOUR_FRESCO = FIG / "cloud-colour-fresco.png"
FRESCO = FIG / "cloud-photo-fresco.png"
INK, GOLD, RED, BLUE, FAINT = ex.INK, ex.GOLD, ex.RED, ex.BLUE, ex.FAINT

# one palette: light tans and grays, narrow enough to tone any photograph into
WALL = "#e6dbc9"
PALETTE = {
    "wall": WALL,
    "haze": "#ded8cf",
    "bank": "#cfc9bf",
    "billow": "#ddd0bb",
    "crown": "#f2ead9",
    "shadow": "#b7ad9d",
    "cool": "#9aa0a4",
    "cool_dark": "#71777c",
    "warm": "#c3b49b",
    "warm_dark": "#9b8a70",
    "shade": "#9b8a70",
    "light": "#fbf6ea",
}

STOPS = [(0, (143, 127, 102)), (128, (195, 180, 155)), (255, (242, 234, 217))]


def circle_points(per_degree: float = 2.0):
    tri = for_angle(per_degree)
    n = round(360 / tri.degrees)
    path = Spiral(tri, 1, heading=Dir.east())
    path.extend([0] + [1] * (n - 1))
    return path.nodes, tri


CIRCLE, TRI = circle_points()
STATUE_SIZE = (940, 1185)
VEIL_TARGET = {"v1": 0.85, "v2": 0.85}  # operator: good between 80 and 90


def tone_photo(src: Path, out: Path, width=460):
    """Map a photograph onto the palette: luminance in, tan/gray out."""
    from PIL import Image, ImageOps

    def lut(channel):
        table = []
        for v in range(256):
            for (a, ca), (b, cb) in zip(STOPS, STOPS[1:]):
                if a <= v <= b:
                    t = (v - a) / (b - a)
                    table.append(round(ca[channel] + t * (cb[channel] - ca[channel])))
                    break
            else:
                table.append(STOPS[-1][1][channel])
        return table

    im = Image.open(src).convert("L")
    im = ImageOps.autocontrast(im, cutoff=1)
    im.thumbnail((width, width * 2))
    rgb = Image.merge("RGB", tuple(im.point(lut(c)) for c in range(3)))
    rgb.save(out)
    return rgb.size


def colour_photo(src: Path, out: Path, width=460):
    """The photograph with its colour kept: the starting point, before toning."""
    from PIL import Image, ImageOps
    im = Image.open(src).convert("RGB")
    im = ImageOps.autocontrast(im, cutoff=1)
    im.thumbnail((width, width * 2))
    im.save(out)
    return im.size


def raw_photo(src: Path, out: Path, width=460):
    from PIL import Image, ImageOps
    im = Image.open(src).convert("L")
    im = ImageOps.autocontrast(im, cutoff=1)
    im.thumbnail((width, width * 2))
    im.convert("RGB").save(out)
    return im.size


def image_at(c, x, y, w, h, href):
    x0, y0 = c.xy(x, y + h)
    x1, y1 = c.xy(x + w, y)
    c.out.append(f'<image x="{x0:.2f}" y="{y0:.2f}" width="{x1 - x0:.2f}" '
                 f'height="{y1 - y0:.2f}" href="{href}" '
                 f'preserveAspectRatio="xMidYMid slice"/>')
    c.out.append(f'<rect x="{x0:.2f}" y="{y0:.2f}" width="{x1 - x0:.2f}" '
                 f'height="{y1 - y0:.2f}" fill="none" stroke="{INK}" '
                 f'stroke-width="0.7"/>')


def billow(c, cx, cy, rx, ry, tilt=0, fill=None, alpha=0.4, edge=0.0):
    """An exact ellipse, tilted by whole triangle angles, with a soft edge."""
    d = place.rotation(TRI, int(tilt))
    pts = []
    for x, y in CIRCLE:
        q = place.rotate((Fraction(rx) * x, Fraction(ry) * y), d)
        pts.append((float(q[0]) + cx, float(q[1]) + cy))
    if edge:
        c.poly(pts + [pts[0]], fill=fill, stroke=fill, width=edge,
               opacity=alpha * 0.55)
    c.poly(pts + [pts[0]], fill=fill, stroke=fill, width=0.6, opacity=alpha)
    return pts


# the billows live in pythagorean_spiral.veil: turn-chain ribbons, one polygon
# each, shared by the drawing and the opacity report
CLOUD = veil_mod.BILLOWS
LAYER = veil_mod.V2_LAYER

VEIL = {"v1": 0.05, "v2": 0.32}  # solved at run time: see solve_veil()
_FILTER = [0]


def veil_opacity(x, y, version="v2", veil=None):
    """Composited alpha of every billow covering a point, at a veil setting.

    The same function the drawing uses, so the report cannot drift from the
    picture: every layer carries the veil factor, as it does in `draw_cloud`.
    """
    if veil is None:
        veil = VEIL[version]
    return veil_mod.alpha(x, y, veil, version)


def _veil_test_figure(version="v2"):
    """Section 2b's drawing: the four patterns under one version's veil.

    Imported inside the call because `veil_test` imports this module for the
    palette and `draw_cloud`; a module-level import would close the cycle.
    """
    import veil_test
    letters = ("g", "h", "i", "j") if version == "v1" else ("k", "l", "m", "n")
    return veil_test.figure(VEIL[version], version, letters)


def _slider_html():
    """One slider per picture, with a clear label and a way to save.

    The cloud as a whole is one composition, but the design question is per
    image: how much veil each work tolerates.  So every picture gets its own
    uniform layer and its own control, defaulting to the operator's band
    (80-90 per cent).  Save writes the settings as JSON and one picture as a
    PNG, so a choice can be looked at later instead of remembered.
    """
    # letters continue the page's sequence: a-f are the fixed figures above
    pictures = [("o", "statue, colour", "fig/" + COLOUR_STATUE.name),
                ("p", "fresco, colour", "fig/" + COLOUR_FRESCO.name),
                ("q", "statue, toned", "fig/" + STATUE.name),
                ("r", "fresco, toned", "fig/" + FRESCO.name)]
    cards = []
    for letter, title, href in pictures:
        cards.append(
            '<figure class="card" data-name="' + letter + '">'
            '<div class="pic" style="background-image:url(\'' + href + '\')">'
            '<div class="layer" data-layer style="opacity:0.85"></div>'
            '<span class="tag">' + letter + '</span></div>'
            '<figcaption>' + letter + ' · ' + title + '</figcaption>'
            '<label class="ctl"><span>veil opacity</span>'
            '<input type="range" min="0" max="100" step="1" value="85" '
            'data-slider aria-label="veil opacity for ' + title + '">'
            '<output data-read>85%</output></label></figure>')
    return """<div class="veillab">
<style>
.veillab { margin: 22px 0 10px; }
.veillab .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.veillab .card { margin: 0; border: 1px solid #d8ccae; background: #fffdf7; padding: 8px; }
.veillab .pic { position: relative; height: 220px; background: #e6dbc9 center/cover no-repeat; }
.veillab .layer { position: absolute; inset: 0; background: #ddd0bb; }
.veillab .tag { position: absolute; left: 6px; top: 6px; width: 20px; height: 20px;
  border-radius: 50%; background: #2e2413; color: #fffdf7; font: 11px/20px Georgia, serif;
  text-align: center; }
.veillab figcaption { font: 11px ui-monospace, Menlo, monospace; color: #7b6c4e;
  padding: 6px 0 2px; }
.veillab .ctl { display: grid; grid-template-columns: auto 1fr auto; gap: 8px;
  align-items: center; font: 11px ui-monospace, Menlo, monospace; color: #7b6c4e; }
.veillab input[type=range] { width: 100%; accent-color: #8c6a21; }
.veillab output { font-size: 13px; color: #2e2413; min-width: 40px; text-align: right; }
.veillab .bar { display: flex; gap: 10px; align-items: center; margin-top: 14px;
  flex-wrap: wrap; }
.veillab .bar button { font: 12px ui-monospace, Menlo, monospace; padding: 7px 14px;
  border: 1px solid #8c6a21; background: #f6f1e4; color: #2e2413; cursor: pointer; }
.veillab .bar button:hover { background: #efe6d2; }
.veillab .bar span { font: 11px ui-monospace, Menlo, monospace; color: #7b6c4e; }
</style>
<div class="grid">""" + "".join(cards) + """</div>
<div class="bar">
  <button type="button" id="save-json">save settings (json)</button>
  <button type="button" id="save-png">save o (png)</button>
  <span>the band that read best was 80-90 per cent</span>
</div>
<script>
(function () {
  var cards = Array.prototype.slice.call(document.querySelectorAll('.veillab .card'));
  function sync(card) {
    var v = card.querySelector('[data-slider]').value / 100;
    card.querySelector('[data-layer]').style.opacity = v;
    card.querySelector('[data-read]').textContent = Math.round(v * 100) + '%';
  }
  cards.forEach(function (card) {
    card.querySelector('[data-slider]').addEventListener('input', function () { sync(card); });
    sync(card);
  });
  function settings() {
    var out = {};
    cards.forEach(function (c) { out[c.dataset.name] = c.querySelector('[data-slider]').value / 100; });
    return out;
  }
  function download(name, blob) {
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
  }
  document.getElementById('save-json').addEventListener('click', function () {
    download('veil-settings-chosen.json',
             new Blob([JSON.stringify(settings(), null, 1)], {type: 'application/json'}));
  });
  document.getElementById('save-png').addEventListener('click', function () {
    var card = cards[0], pic = card.querySelector('.pic');
    var img = new Image();
    img.onload = function () {
      var cv = document.createElement('canvas');
      cv.width = img.naturalWidth; cv.height = img.naturalHeight;
      var g = cv.getContext('2d');
      g.drawImage(img, 0, 0, cv.width, cv.height);
      g.globalAlpha = card.querySelector('[data-slider]').value / 100;
      g.fillStyle = '#ddd0bb';
      g.fillRect(0, 0, cv.width, cv.height);
      cv.toBlob(function (b) { download('veil-o.png', b); });
    };
    img.src = pic.style.backgroundImage.slice(5, -2);
  });
})();
</script>
</div>"""


def _veil_rows():
    """Section 2b's table: one row per strip, per version, measured."""
    import veil_test
    rows = [["version", "pattern", "row", "mean", "p95", "worst"]]
    for version in veil_mod.VERSIONS:
        for r in veil_test.report(VEIL[version], version):
            rows.append([version, r["pattern"], f'{r["row"]} {r["side"]}',
                         f'{r["mean"]:.3f}', f'{r["p95"]:.3f}',
                         f'{r["max"]:.3f}'])
    return rows


def works_boxes(sizes):
    """The two work rectangles on the canvas: (x, y, w, h), y up."""
    hs = 32.0
    aw = hs * sizes[STATUE][0] / sizes[STATUE][1]
    bw = hs * sizes[FRESCO][0] / sizes[FRESCO][1]
    return [(16, 10, aw, hs), (100 - bw, 10, bw, hs)]


def artwork_worst_opacity(sizes, veil=None, version="v2"):
    """The most opaque point over the works: the veil is judged there."""
    if veil is None:
        veil = VEIL[version]
    return max(veil_mod.panel(b, veil, version=version)["max"]
               for b in works_boxes(sizes))


def solve_veil(target=0.55, version="v2"):
    """The veil factor whose densest point anywhere reaches `target`.

    Solved on the whole canvas, not on the works and not on one row, so the two
    versions are compared at the same peak density: the difference between them
    is then the geometry, not the strength.  Where that peak lands is the
    finding -- on v1 it lands on the top of the image, on v2 above it.
    """
    return veil_mod.solve(target, None, version=version)


def _cloud_filter(c, scale=8, blur=6):
    """A displacement filter: the geometry stays ellipses, the edge is air."""
    _FILTER[0] += 1
    fid = f"cloud{_FILTER[0]}"
    c.out.append(
        f'<defs><filter id="{fid}" x="-50%" y="-50%" width="200%" '
        f'height="200%"><feTurbulence type="fractalNoise" '
        f'baseFrequency="0.012 0.02" numOctaves="3" seed="7" result="noise"/>'
        f'<feDisplacementMap in="SourceGraphic" in2="noise" scale="{scale}" '
        f'xChannelSelector="R" yChannelSelector="G" result="air"/>'
        f'<feGaussianBlur in="air" stdDeviation="{blur}"/></filter></defs>')
    return fid


def draw_cloud(c, version="v2", only=None, veil=1.0, drop=0.0):
    """Fill the billows of one version.

    Every billow is drawn at `layers(version)[layer] * VEIL[version]` -- the
    same number the opacity report composites, in both versions.  v1 is the
    original ellipse cloud; v2 is the turn-chain cloud.  The displacement
    filter softens the edge optically; it moves pixels, not the alpha model.
    """
    fid = _cloud_filter(c)
    table = veil_mod.layers(version)
    factor = VEIL[version]
    c.out.append(f'<g filter="url(#{fid})">')
    for layer, pts in veil_mod.polygons(version):
        if only is not None and layer != only:
            continue
        moved = [(x, y - drop) for x, y in pts]
        c.poly(moved, fill=PALETTE[layer], stroke=PALETTE[layer], width=0.8,
               opacity=table[layer] * (1.0 if only else factor) * veil)
    c.out.append('</g>')


def draw_statue(c, cx, base_y):
    """A robed figure on a plinth, in the warm tone."""
    light, dark = PALETTE["warm"], PALETTE["warm_dark"]
    c.poly([(cx - 7, base_y), (cx + 7, base_y), (cx + 7, base_y + 3),
            (cx - 7, base_y + 3)], fill=dark, stroke="none")
    c.poly([(cx - 3.6, base_y + 3), (cx - 4.2, base_y + 16),
            (cx - 2.6, base_y + 24), (cx + 2.6, base_y + 24),
            (cx + 4.2, base_y + 16), (cx + 3.6, base_y + 3)],
           fill=light, stroke=dark, width=0.6)
    c.line((cx - 1.0, base_y + 6), (cx - 1.6, base_y + 20), dark, 0.6)
    c.dot((cx, base_y + 26), 2.3, light, dark, 0.5)


def fig_tone(sizes):
    rows = []
    for src, label in ((RAW, "as photographed: value kept, colour dropped"),
                       (STATUE, "toned: the one palette")):
        w, h = sizes[src]
        aspect = w / h
        c = ex.Canvas((0, 120), (0, 54), 760, 320)
        c.poly([(0, 54), (120, 54), (120, 0), (0, 0)], fill=WALL, stroke="none")
        hh = 42
        image_at(c, 22, 5, hh * aspect, hh, f"fig/{src.name}")
        c.text(3, 51, label, 10, GOLD)
        c.text(58, 22, "one work, two treatments", 10, GOLD)
        c.text(58, 17, "the cloud in the next figure sits over both",
               9, PALETTE["warm_dark"])
        rows.append((c, 320))
    return ex.stack(rows, width=760, gap=8)


def badge(c, x, y, letter, size=13):
    """A lettered disc at a picture's corner, so panels can be called by name."""
    c.dot((x, y), size / 22.0, "#2E2413", "#2E2413", 0.0)
    c.text(x, y, letter, size, "#fffdf7", "middle")


def fig_colour(sizes):
    c = ex.Canvas((0, 120), (0, 44), 800, 320)
    c.poly([(0, 44), (120, 44), (120, 0), (0, 0)], fill=WALL, stroke="none")
    hs = 32
    aw = hs * sizes[COLOUR_STATUE][0] / sizes[COLOUR_STATUE][1]
    bw = hs * sizes[COLOUR_FRESCO][0] / sizes[COLOUR_FRESCO][1]
    labelled = {"a": "a · Christ crowned with thorns, in colour", "b": "b · Madonna in terracotta, in colour"}
    for x, w, name, letter in ((16, aw, COLOUR_STATUE, "a"),
                               (76, bw, COLOUR_FRESCO, "b")):
        image_at(c, x, 6, w, hs, f"fig/{name.name}")
        badge(c, x + 3, 6 + hs - 3, letter)
        c.text(x, 2.4, labelled[letter], 7, GOLD)
    return c.svg("the two works in colour")


def fig_veil(sizes, version="v2"):
    hs = 32
    c = ex.Canvas((0, 120), (0, 64), 800, 470)
    c.poly([(0, 64), (120, 64), (120, 0), (0, 0)], fill=WALL, stroke="none")
    aw = hs * sizes[STATUE][0] / sizes[STATUE][1]
    bw = hs * sizes[FRESCO][0] / sizes[FRESCO][1]
    image_at(c, 16, 16, aw, hs, f"fig/{STATUE.name}")
    image_at(c, 100 - bw, 16, bw, hs, f"fig/{FRESCO.name}")
    draw_cloud(c, version)
    badge(c, 19, 45, "c" if version == "v1" else "e")
    badge(c, 103 - bw, 45, "d" if version == "v1" else "f")
    return c.svg(f"cloud over two works, {version}")


def fig_conics():
    """Circle and ellipse, drawn as areas: the two exact members, side by side."""
    c = ex.Canvas((0, 100), (0, 56), 760, 360)
    for cx, rx, ry, label in ((26, 16, 16, "circle"), (72, 22, 13, "ellipse")):
        pts = [(rx * x + cx, ry * y + 28) for x, y in veil_mod._circle()[0]]
        c.poly(pts + [pts[0]], fill=PALETTE["bank"], stroke=INK, width=1.6)
        c.poly(pts + [pts[0]], stroke=INK, width=1.2)
        c.line((cx, 28), (cx + rx, 28), GOLD, 1.0, "3 3")
        c.text(cx, 50, label, 11, GOLD, "middle")
        c.text(cx, 46, f"{rx} × {ry}" if rx != ry else f"r {rx}", 8,
               PALETTE["warm_dark"], "middle")
    c.text(3, 3, "the same rational points, scaled on two rational axes: "
                 "the circle stays a circle, the ellipse stays exact", 8,
           PALETTE["warm_dark"])
    return c.svg("circle and ellipse")


# ----------------------------------------------------------------- text ---
def build_blocks(sizes):
    """Number every illustration once, in page order: Fig. 1, Fig. 2, ..."""
    blocks = _build_blocks(sizes)
    out, n = [], 0
    for block in blocks:
        if block[0] == "fig":
            n += 1
            out.append(("fig", block[1], f"Fig. {n} · {block[2]}"))
        else:
            out.append(block)
    return out


def _build_blocks(sizes):
    blocks = [
        ("h1", "A cloud, for veiling"),
        ("p", "The cathedral has no single artwork problem; it has one per "
              "piece. The proposal is a veil rather than a repair: tone the "
              "photographs into one palette of light tans and grays, and put a "
              "layered, semi-transparent cloud in front. The cloud is the "
              "constant; the works stay different behind it."),
        ("quote", "The cloud is also a theological choice. At the Transfiguration, "
                  "at the baptism, at the temple when Gabriel spoke, at Fatima, "
                  "the cloud does not explain the action -- it shelters it. What "
                  "is hidden stays God's to reveal."),
        ("table", [["role", "tone", "use"],
                   ["wall", PALETTE["wall"], "the constant ground"],
                   ["haze", PALETTE["haze"], f"outer breath, alpha {LAYER['haze'] * VEIL['v2']:.2f}"],
                   ["bank", PALETTE["bank"], f"the flat base, alpha {LAYER['bank'] * VEIL['v2']:.2f}"],
                   ["billow", PALETTE["billow"], f"volume, alpha {LAYER['billow'] * VEIL['v2']:.2f}"],
                   ["crown", PALETTE["crown"], f"lit tops, alpha {LAYER['crown'] * VEIL['v2']:.2f}"],
                   ["shadow", PALETTE["shadow"], "under the mass, never black"]]),
        ("h2", "1. Tone first, then veil"),
        ("fig", lambda: fig_tone(sizes),
         "One photograph: value kept, colour dropped, then mapped onto the palette."),
        ("p", "Tone is the first half of the unification and the cloud is the "
              "second. The photograph here is one of the author's own, reduced "
              "to luminance and mapped onto the ramp above; the value structure "
              "stays, the colour argument goes. Two works of different periods "
              "then sit in the same room before the cloud is even drawn. The "
              "cloud hides the remaining seams -- the edges, the varnish, the "
              "reproduction -- rather than the subjects."),
        ("p", "This is deliberately unheroic: no restoration, no repainting, no "
              "claim that the works match. They do not, and the veil says so "
              "honestly by being visible."),

        ("h2", "2. The veil"),
        ("fig", lambda: fig_colour(sizes),
         "a and b: the two works in colour, before any veil."),
        ("p", "Two versions, same composition, different geometry. **v1** is "
              "the original cloud of exact ellipses -- the one that was right "
              "in principle and only too opaque -- now with the veil factor on "
              "every layer instead of the base alone. **v2** replaces each "
              "ellipse with a turn-chain ribbon. Both are measured by the same "
              "function and judged by the same strips."),
        ("fig", lambda: fig_veil(sizes, "v1"),
         "c and d: v1, the original ellipse cloud, one veil factor on every layer."),
        ("fig", lambda: fig_veil(sizes, "v2"),
         "e and f: v2, the same composition in turn-chain ribbons."),
        ("p", "The cloud is built from **exact turn chains**, not circles. A "
              "billow is a lobe whose turns run k**p and then reverse, so the "
              "exit is parallel to the entry; a taper through "
              "`ribbon.outline` turns it into a closed rational polygon with "
              "pointed ends. The power dial is the layer: p = 1 is the "
              "clothoid, p = 2 and 3 hold the turn back to the apsis and curl "
              "the tail. So each billow can be placed, repeated and stored "
              "without a float deciding its edge. What is not exact is the "
              "compositing: tone and transparency are design numbers, not "
              "geometry."),
        ("code", f"layers   4   haze {LAYER['haze']}, bank {LAYER['bank']}, "
                 f"billow {LAYER['billow']}, crown {LAYER['crown']}\n"
                 f"billows  {len(CLOUD)}  turn-chain ribbons: turns k**p, tapered\n"
                 "edge     fractal displacement + gaussian blur, optical only\n"
                 f"veil     v1 {VEIL['v1']:.3f} (peak {VEIL_TARGET['v1']:.0%}), "
                 f"v2 {VEIL['v2']:.3f} (peak {VEIL_TARGET['v2']:.0%})\n"
                 "overlap  the sum does the softening\n"
                 "geometry exact; opacity and tone are choices"),
        ("p", "Two variants are worth keeping. A **cumulus** (above) has a flat "
              "base and a domed top. An **incense** cloud is taller, thinner and "
              "more transparent, with vertical drift; it is the better veil for "
              "a side chapel or a shrine, where the cloud should rise in front "
              "of the work rather than rest above it. Both are the same palette "
              "and the same ellipses -- only the layout and the opacities "
              "differ."),

        ("h2", "2b. Against four test patterns"),
        ("p", "A veil is judged by what it leaves legible. Four standard "
              "patterns -- a Siemens star, an eleven-step grey wedge, colour "
              "bars and a chequer with a crosshair -- sit under the same "
              "billows as the works: two on top, where the cloud is densest and "
              "meets the top of the image, two below, where it drifts. Each is "
              "sampled on a grid and the composited alpha is reported as mean, "
              "95th percentile and worst. Both versions are solved to the same "
              "peak, 80 per cent -- the number chosen on the slider below -- so "
              "the comparison is about where the density lands, not how strong "
              "it is. The gate reads the row mean, because the mean is how much "
              "of the image is covered: top mean under 0.25 (a hot corner is "
              "allowed up to 0.50), bottom mean under 0.12 (up to 0.30)."),
        ("fig", lambda: _veil_test_figure("v1"),
         "g to j: v1 under the four patterns, two on top, two below."),
        ("fig", lambda: _veil_test_figure("v2"),
         "k to n: v2 under the four patterns."),
        ("table", _veil_rows()),
        ("p", "The numbers come from `pythagorean_spiral.veil`, the same "
              "function the drawing fills, so a strip cannot pass on paper "
              "while the picture covers it. `scripts/veil_test.py` writes the "
              "standalone page and `tests/test_veil.py` holds the gate."),

        ("h2", "2c. Set the transparency by eye (o to r)"),
        ("p", "The model should not be the authority on a design number. This "
              "strip is one uniform layer of one cloud colour over the same four "
              "patterns; drag the slider until the top row is as legible as you "
              "want it and the bottom as light as you want it. The percentage is "
              "the target the veil should then be solved to. Below, o to r each "
              "carry their own control: the design question is per picture, not "
              "per page."),
        ("raw", _slider_html()),

        ("h2", "3. Circles, ellipses, parabolas, hyperbolas"),
        ("fig", fig_conics,
         "A circle and the same circle scaled: both exact, and the rays remain rational under the scale."),
        ("p", "Not all four are the same curve, and it matters which is which. "
              "The chain is built from whole triangle angles, so its exact "
              "members are the circle (constant turn), the straight line (zero "
              "turn), the quarter-turn corner, and the clothoid-like family "
              "where curvature grows linearly. A circle is exact. An ellipse is "
              "exact **as an affine image of a circle** -- scale x by one "
              "rational and y by another, and every point stays rational -- but "
              "it is not a Euclidean circle and its curvature is not a clothoid. "
              "A parabola and a hyperbola have no such rational affine origin "
              "here, and no linear-curvature parameterisation; they can only be "
              "approximated, to the lattice's resolution, and the error should "
              "be measured rather than assumed."),
        ("p", "The constructive part is real: because the ellipse is a scaled "
              "circle, a circle with rays from its diameter scales into an "
              "ellipse with rays, exactly. That is how the second drawing was "
              "made -- same points, same rational slopes, one rational scale. "
              "For a sunburst, a rose-window basis, or a billow with ribs, that "
              "is enough. For a true parabola or hyperbola, use the float path "
              "and report the gap."),

        ("h2", "4. The clothoid-like cloud, in four arcs"),
        ("p", "The simplest form is not a mass of puffs but four arcs: two big "
              "ones under the cloud, turning upward and meeting at (0,0); two "
              "half-size ones on top, turning downward and meeting near "
              "(0,200). Plotted with the stated centres, the form does not "
              "close -- the bottom circles are centred at (120,120) and "
              "(-120,120) with radius 169.7, the top at (60,180) and (-60,180) "
              "with radius 63.2, and the right-hand pair is nested by 21.6, so "
              "there is no side joint."),
        ("fig", cf.fig_literal,
         "The four arcs as stated, with centres and the two meeting points."),
        ("p", "Moving the bottom centres in to (100,100) fixes it more neatly "
              "than a side crossing would: the bottom radius becomes 141.4, "
              "which is also the distance to (0,200), so the bottom pair passes "
              "through both (0,0) and (0,200) -- and the top pair already passes "
              "through (0,200). That is the common point, and the cloud closes "
              "there. Two numbers remain: the big lobes reach x = 241 (about "
              "twice the intended width), and the tangent at (0,200) is G0, not "
              "G1, so the next tune is one centre and one tangent."),
        ("fig", cf.fig_adjusted,
         "Bottom centres at (100,100): all four arcs meet at (0,200)."),
        ("h2", "5. What this is not"),
        ("p", "This framework does not replace the clothoid engine, and it is "
              "not a subset of its curves. Bertolazzi gives real clothoids -- "
              "exact Fresnel geometry, many parameterisations, tolerances. The "
              "chain here is an Euler polygon whose *headings* match a clothoid "
              "at the nodes; its position is up to a chord away, and its "
              "curvature is a staircase. What it adds is the other column: "
              "rational points, rational slopes, exact joins and mirrors, and a "
              "known lattice. The caps in `out/caps` came from the engine and "
              "transfer here by quantising each chord's turn, with a measured "
              "gap. The honest architecture is: engine for the transcendental "
              "curve, chain for the exact plan, and a converter between them."),
        ("h2", "Reproduce"),
        ("code", "cd pythagorean-spiral\n"
                 "../.venv/bin/python scripts/cloud.py\n"
                 "../.venv/bin/python -m unittest discover -s tests -t ."),
    ]
    return blocks


def _size_or_existing(src, out, fn):
    """Regenerate from the photograph if it is present, else reuse the plate.

    The works are the author's own photographs and are not distributed with the
    repository, but the derived plates in `docs/fig` are, so the page still
    builds from a clean clone.
    """
    if src.exists():
        return fn(src, out)
    from PIL import Image
    return Image.open(out).size


def prepare():
    sizes = {}
    sizes[COLOUR_STATUE] = _size_or_existing(REF / "IMG_5903.JPG", COLOUR_STATUE, colour_photo)
    sizes[COLOUR_FRESCO] = _size_or_existing(REF / "IMG_5978.JPG", COLOUR_FRESCO, colour_photo)
    sizes[RAW] = _size_or_existing(REF / "IMG_5903.JPG", RAW, raw_photo)
    sizes[STATUE] = _size_or_existing(REF / "IMG_5903.JPG", STATUE, tone_photo)
    sizes[FRESCO] = _size_or_existing(REF / "IMG_5978.JPG", FRESCO, tone_photo)
    return sizes


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    sizes = prepare()
    global VEIL
    import sys as _sys
    global VEIL_TARGET
    if len(_sys.argv) > 1:
        VEIL_TARGET = {"v1": float(_sys.argv[1]), "v2": float(_sys.argv[1])}
    for version in veil_mod.VERSIONS:
        VEIL[version] = solve_veil(VEIL_TARGET[version], version)
        print(f"{version} veil {VEIL[version]:.3f}  "
              f"worst on the canvas {veil_mod.worst(VEIL[version], version=version):.3f}  "
              f"worst over the works "
              f"{artwork_worst_opacity(sizes, None, version):.3f}")
    blocks = build_blocks(sizes)
    names = ["cloud-tone", "veil-colour", "veil-v1", "veil-v2",
             "veil-test-v1", "veil-test-v2", "cloud-conics",
             "cloud-form-stated", "cloud-form-adjusted"]
    figs, fig_names = [], []
    i = 0
    for kind, *rest in blocks:
        if kind != "fig":
            continue
        svg = rest[0]()
        (FIG / f"{names[i]}.svg").write_text(svg + "\n")
        figs.append((svg, names[i]))
        fig_names.append(f"{names[i]}.svg")
        i += 1
    md = ex.to_md(blocks, fig_names)
    (ROOT / "docs" / "CLOUD.md").write_text(md.rstrip() + "\n")
    html = ex.to_html(blocks, figs, "A cloud, for veiling")
    (ROOT / "docs" / "cloud.html").write_text(html + "\n")
    import json
    settings = {
        "veil_transparency": VEIL,
        "canvas": [120, 80],
        "palette": PALETTE,
        "layers": {k: round(v * VEIL['v2'], 4) for k, v in LAYER.items()},
        "layers_v1": {k: round(v * VEIL['v1'], 4)
                      for k, v in veil_mod.V1_LAYER.items()},
        "billows": [{"x": round(x, 3), "y": round(y, 3), "rx": rx, "ry": ry,
                     "tilt": t, "layer": l, "power": p}
                    for x, y, rx, ry, t, l, p, _shape in CLOUD],
        "filter": {"displacement": 8, "blur": 6},
        "works": {"christ": "reference/IMG_5903.JPG",
                  "madonna": "reference/IMG_5978.JPG"},
    }
    (ROOT / "docs" / "veil-settings.json").write_text(
        json.dumps(settings, indent=1) + "\n")
    print(f"docs/CLOUD.md, docs/cloud.html, docs/veil-settings.json, {len(figs)} figures")


if __name__ == "__main__":
    main()

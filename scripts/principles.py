"""Rebuild docs/principles.html from reference/principles.json + manifest.json.

Images are attached by subject id from the manifest, never hard-coded in a card,
so a re-download cannot leave a broken link. No shape is traced; the images are
for measurement.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "reference" / "principles.json"
MANIFEST = ROOT / "reference" / "manifest.json"

cards = json.loads(CARDS.read_text())
manifest = json.loads(MANIFEST.read_text())
by_subject = {}
for row in manifest:
    by_subject.setdefault(row["subject"], []).append(row["file"])

blocks = []
for card in cards:
    refs = by_subject.get(card["id"], [])
    images = "".join(
        f'<a href="../reference/{f}"><img src="../reference/{f}" alt="{card["name"]}"></a>'
        for f in refs) or '<p class="none">no references</p>'
    numbers = "".join(
        f"<tr><th>{k.replace('_', ' ')}</th><td>{v}</td></tr>"
        for k, v in card["numbers"].items())
    blocks.append(f'''<article class="card"><div class="refs">{images}</div>
<h2>{card["name"]}</h2><p class="cls">{card["class"]}</p>
<p class="gesture">{card["gesture"]}</p>
<table>{numbers}</table>
<p class="dont"><b>Not this:</b> {", ".join(card["not_this"])}</p></article>''')

PAGE = '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Principle cards</title><style>
body{margin:0;background:#f6f1e4;color:#2e2413;font:16px/1.55 Georgia,serif}
main{max-width:1200px;margin:0 auto;padding:32px 20px 70px}
h1{font-size:28px;margin:0 0 4px}.lead{color:#8c6a21;margin:0 0 20px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:18px}
.card{background:#fffdf7;border:1px solid #d8ccae;padding:14px;border-radius:6px}
.refs{display:flex;gap:8px;margin-bottom:8px}
.refs img{width:50%;height:110px;object-fit:cover;border:1px solid #d8ccae}
.none{font:12px ui-monospace,Menlo,monospace;color:#b23a2b}
h2{font-size:18px;margin:6px 0 0}.cls{font:11px ui-monospace,Menlo,monospace;color:#7b6c4e;
margin:0 0 8px;text-transform:uppercase;letter-spacing:.1em}
.gesture{font-size:14px;margin:0 0 10px}
table{width:100%;border-collapse:collapse;font:12px ui-monospace,Menlo,monospace;margin-bottom:8px}
th,td{border-top:1px solid #d8ccae;padding:4px 3px;text-align:left;vertical-align:top}
th{width:42%;color:#7b6c4e;font-weight:500}
.dont{font-size:13px;color:#b23a2b;margin:0}
a{color:#8c6a21}
</style></head><body><main>
<h1>Principle cards</h1>
<p class="lead">What each ornament must do, not what it must look like. Edit <code>reference/principles.json</code> and rebuild.</p>
<div class="cards">''' + "".join(blocks) + '''</div>
<p style="margin-top:24px;font-size:13px">Reference images are for measurement only;
no shape is traced. Attribution: <a href="../reference/ATTRIBUTION.md">reference/ATTRIBUTION.md</a>.</p>
</main></body></html>'''

out = ROOT / "docs" / "principles.html"
out.write_text(PAGE)
print(f"{out} — {len(cards)} cards, {len(manifest)} images")

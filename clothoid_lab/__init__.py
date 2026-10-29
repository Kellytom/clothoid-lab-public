"""clothoid-lab: numerical clothoid chains, out as plain editable SVG.

The engine is Bertolazzi's Clothoids through pyclothoids. Everything around it
is ours: the chain model, the cubic fit, the rails, and the SVG writer.

    from clothoid_lab import presets, render
    text, info = render(presets.get("s-curve"), width=6)
"""

from .engine import build, report
from .model import Design, Segment

__version__ = "0.1.0"
__all__ = ["Design", "Segment", "build", "report", "render", "__version__"]


def render(*args, **kwargs):
    """Lazy re-export, so importing the package does not load the text layer."""
    from .cli import render as _render
    return _render(*args, **kwargs)

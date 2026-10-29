"""Clothoids built out of Pythagorean triangles, in exact rational arithmetic.

The chain is a polygon of equal chords whose direction turns by `k * alpha` at
node k, with `alpha` the acute angle of a primitive right triangle.  Headings
are carried as exact rational unit vectors, so the coordinates are rational at
every node; `Fraction` is the data type, and no `sin` or `cos` is ever
evaluated to build the geometry.

    from pythagorean_spiral import design
    from pythagorean_spiral.triples import thinnest

    path = design.lobe(thinnest(3125), steps=7)
    path.final          # exact Fractions
    path.integer_form() # the same points, exactly scaled to integers

What this is not: the clothoid.  See `docs/AUDIT.md`.
"""

from .exact import Dir
from .triples import Triple, primitive, thinnest
from .spiral import Spiral, triangular
from . import design, hybrid, place, quality, ribbon

__all__ = ["Dir", "Triple", "primitive", "thinnest", "Spiral", "triangular",
           "design", "hybrid", "place", "quality", "ribbon"]
__version__ = "0.1.0"

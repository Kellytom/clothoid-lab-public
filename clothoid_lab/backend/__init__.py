"""Backends: the two ways to reach the same geometry.

`bertolazzi` loads the C++ library compiled from the vendored source, through
the C surface in `csrc/clothoid_api.cpp`. It is the default, because it exposes
what the wheel does not: the exact offset (X_ISO and Y_ISO), the G1 fitter, and
the G2 solver.

`pyclothoids` is the prebuilt wheel kept as a second opinion. It carries the
same library, so it is not an independent oracle for the mathematics; it is an
oracle for this wrapper, which is the thing that can actually be wrong here.

Choose with `CLOTHOID_BACKEND`, or pass a backend to `engine.build`.
"""

from __future__ import annotations

import os

from . import bertolazzi, pyclothoids_backend

BACKENDS = {"bertolazzi": bertolazzi, "pyclothoids": pyclothoids_backend}
DEFAULT = "bertolazzi"


def available() -> dict:
    """Which backends can load right now, and why not when they cannot."""
    out = {}
    for name, module in BACKENDS.items():
        try:
            out[name] = module.probe()
        except Exception as exc:  # a probe never raises, it reports
            out[name] = str(exc)
    return out


def load(name: str | None = None):
    """Return the backend module, defaulting to the compiled library."""
    choice = name or os.environ.get("CLOTHOID_BACKEND") or DEFAULT
    if choice not in BACKENDS:
        raise KeyError(f"unknown backend {choice!r}; have {', '.join(BACKENDS)}")
    module = BACKENDS[choice]
    module.load()
    return module

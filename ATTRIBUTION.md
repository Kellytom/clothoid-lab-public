# Attribution

## Vendored and compiled

**Clothoids**, by Enrico Bertolazzi and Marco Frego. The geometry engine:
clothoid evaluation, exact parallel curves, the G1 fitter, trimming, projection
and intersection. Licence **BSD-2-Clause**, vendored under `vendor/Clothoids` and
built into `build/libclothoidlab.dylib` by `scripts/build-native.sh`. Its
submodules are vendored with it.

**Eigen**, by the Eigen authors, **MPL-2.0**, reached through the vendored
UtilsLite tree. Header-only linear algebra, not used directly here.

**GenericContainer**, **UtilsLite**, **quarticRootsFlocke**, by the same author
and under the same permissive terms, vendored because the engine includes them.

## Optional

**pyclothoids**, by Phillip Dix, 2020, **MIT**. The prebuilt wheel, kept as a
second opinion on the ctypes wrapper and as a fallback when no compiler is
available. It carries the same engine, so it agrees on the mathematics by
construction and is not an independent check of it.

## Used, never linked

**Inkscape**, GPL-2.0-or-later. The renderer and the node editor. This project
hands it a file and runs its command line; nothing is linked in and no Inkscape
code is vendored.

## Ours, MIT

Everything in `clothoid_lab/` and `csrc/` that is not a call into the engine:
the chain model, the anchor and continuity rules, the cubic arm rule and its
adaptive subdivision, the error metric, the rails with their fold reporting, the
SVG writer and reader, the presets, the command line, and the C surface itself.

The arm rule comes from Raph Levien's 2021 work on cleaner parallel curves with
Euler spirals, as recorded in the sibling project's `docs/clothoid-levien.md`.
The rule is used; the code is not.

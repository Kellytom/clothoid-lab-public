# focus-math

A reading library, not a dependency. The maths we may need later for terminals,
clearance, junctions, spirals and instrument outlines, kept where it can be
found again.

Nothing here is imported by `clothoid_lab/`. The working engine stays
Bertolazzi's Clothoids in `vendor/`; this folder is where the other approaches
live so we can write our own code with the prior art in view.

## What is here

| Path | What |
|---|---|
| `SOURCES.md` | Every repository worth knowing, with licence, size and verdict |
| `fetch.sh` | Re-creates `repos/` from the pinned commits in `LOCK.tsv` |
| `LOCK.tsv` | name, URL, commit — the exact state that was read |
| `repos/` | Shallow clones of permissively licensed sources (git-ignored) |
| `notes/` | What each source actually says, and how it maps to our problems |

`repos/` is deliberately **not committed**. Reference code is easy to fetch and
easy to confuse with our code; the notes and the lock file are what belong in
history. Run `bash focus-math/fetch.sh` on a new machine.

## Licence rule

- **Cloned** only when the licence is permissive and the maths is worth reading
  closely: BSD-2, MIT, Apache-2.0, BSL-1.0.
- **Referenced only** when the licence is GPL/LGPL, missing, or the repository
  is too large to justify a copy. The licence column in `SOURCES.md` is the
  boundary; nothing from a referenced GPL project is pasted into this tree.
- `clothoid_lab/` remains MIT. Nothing in `focus-math/repos/` is linked,
  imported or vendored into the build.

## Where to start

- Terminals and the width laws: `notes/03-offsetting-and-strokes.md`
- The 5 mm gap and "no crossing except at terminals":
  `notes/04-clearance-and-crossings.md`
- Leaf → branch → trunk: `notes/05-junctions-and-fillets.md`
- Violin outline, purfling, f-holes: `notes/06-instrument-outlines.md`
- Clothoid and Fresnel maths: `notes/01-clothoids-and-fresnel.md`,
  `notes/02-g1-g2-fitting.md`

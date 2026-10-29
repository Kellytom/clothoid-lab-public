# Project review — 2026-10-26

A senior-dev plus senior-designer pass over the whole repository, written to be
acted on later. Ordered by the cost of discovering each item late, not by how
bad it is today.

**Status:** recorded, not started. Current work continues (canonical fleur,
then studies 02–20) until the sequence below is picked up.

## Solid — leave alone

- Engine choice and the small ctypes surface over Bertolazzi's Clothoids.
- Millimetres as the design unit; the y-flip confined to the SVG writer.
- Design JSON riding in `<desc>`, with a round trip that is tested.
- Clearance's `2·tol` honesty: violation / warning / pass, never false precision.
- Provenance on recovered data (source page, measured taper fraction).
- The MIT / BSD-2 licence boundary; GPL only ever referenced.

## The five that will hurt most

### 1. No page or document model

Every path assumes "one piece → one SVG sized to its own content". A book needs
sheets, margins, a plate grid, captions, numbering, bleeds and crop marks.
Sizing currently lives *inside* the writer (`frame`/`page`), so retrofitting is
a rewrite of the writer rather than an addition above it.

**Do now:** a `Sheet`/`Document` object above `Piece`. Reduce `render_piece` to
"draw this piece inside this box", then a book is a list of
(sheet, box, piece, caption).

### 2. No print backend, and the obvious one is wrong

SVG cannot paginate. "Export each SVG then merge" loses slugs, fonts and colour
intent. But every path is already absolute cubics in millimetres, so a direct
PDF writer (`m`/`c`, base-14 Helvetica, CMYK/registration, one page per plate)
is a few hundred lines and no new native dependency.

**Decision:** artwork source stays SVG; PDF is *written*, not converted. Avoid
`cairosvg`, Inkscape CLI and SVG→PDF mergers as the primary path.

### 3. No outline or fill model

No closed outline means no silhouette test, no fills, no kerf, no masks, no
plate booleans. Rails and caps exist but are never joined into one path, which
is also why "does it look like a fleur?" cannot be answered by a test.

**Do now:** `outline(piece)` returning one closed path per ink instance.

### 4. Contacts and ids are strings and coordinates

`Contact(a="ink/leaf")` breaks silently on rename; radius is a physical guess;
`waives_clearance` conflates three meanings. Before twenty plates carry
junctions: stable ids, typed contacts (terminal / junction / crossing) with a
footprint, and `schema_version` plus `migrate()` in every JSON.

### 5. `Section` exists but nothing uses it

Terminals recompute width, clearance flattens fitted paths, grammar re-walks
chains for nodes. Three notions of "the same station" will drift. Wire
`Section` into terminals and clearance, or delete it. Wiring is preferred: it
is the object the philosophy says is central.

## Print and book readiness

- **Scale is baked into geometry** by `frame`. Physical size must be invariant
  and scale a placement transform. Keep `frame` for previews only.
- **No font strategy.** Captions and plate numbers are `<text>`; PDF needs
  embedding or text-as-paths. Keep text in layout, never in the artwork.
- **No colour system.** One black, no spot, no registration, no overprint, no
  minimum hairline rule. Name inks early: `ink`, `accent`, `registration`.
- **No bleed, crop marks or slug.** Trivial inside a PDF writer, impossible to
  retrofit without redoing page geometry.
- **No plate identity.** A book needs `plate_id`, caption, sequence and a
  `book.json`; `<title>` is not enough.
- **No imposition.** Fine to defer only if the page model exists.

## Design and visual

- **No shared scale or baseline across plates.** Each drawing fits its own
  page, so a book reads as unrelated pages. Add a common height grid and an
  optical scale per family.
- **Layers are not print-aware.** `guide` traces are drawn into the SVG. Split
  `ink` / `construction` / `annotation` with print visibility, and emit real
  Inkscape layers with labels.
- **No silhouette metric.** Rasterise at fixed dpi; measure H/W, lobe count,
  symmetry error, ink/counter ratio; compare to the principle cards.
- **Archetype cards are unenforceable** until their grammars exist. Mark
  `"check": null` and fail the test if a card claims numbers nothing asserts.
- **Terminal vocabulary is incomplete for fire.** Hairpins and the wrapped bulb
  are named, gated, not built; the 120° cap limit is still prose.
- **No optical corrections** (overshoot, junction tapering). Build them as
  terminals or sections, not post-hoc nudges.

## Architecture and code

- `Bundle` is half-real: no `from_dict`, no nesting in `Piece`, no placement.
  Decide: `Piece` contains bundles, or bundles sit outside. Nesting matches
  "a book plate is bundles on a sheet".
- Mutable dataclasses with list fields make caching/hashing unsafe. Freeze core
  objects before adding plate caches.
- **Rebuild destroys Inkscape edits.** Decide and document: generated SVGs are
  outputs, never edited; or ship a sidecar. A book workflow needs the policy.
- One-off scripts are multiplying (`extract-*`, `board`, `principles`, `primal`,
  `study_01`), some untested. Put them behind one entry point and a
  `scripts/recover/` package.
- **No CI.** 215 tests are a local habit. One command must run tests, doc builds
  and parity.
- **README is stale.** It describes the single-design CLI and never mentions
  pieces, clearance, junctions or the book.
- **Reference images are committed** (4.6 MB, copyrighted, private-study use).
  Ignore or replace with links + hashes before the repo goes public. Provenance
  is not permission.
- Generated docs in git (1.4 MB board, 600 KB JSON) will bloat; plan a `dist/`.
- `clothoid_lab` is not installable; scripts use `sys.path.insert`. Add a
  packaged module list before an outsider tries.

## If we changed exactly one thing

Add the sheet/document layer with a PDF writer **before** the canonical fleur
and the nineteen studies. Every other item is local and reversible. Page size,
margins, scale, colour, text and plate identity must exist before the first
twenty drawings are made, or all twenty are remade in the book grid.

## Sequence

1. `outline()` + silhouette metrics (small; unlocks judgement).
2. Stable ids + typed contacts + schema version (small; prevents silent loss).
3. Sheet/document model + PDF writer with crop marks and plate manifest
   (medium; the irreversible one).
4. Wire `Section` into terminals/clearance; layer print-visibility.
5. CI entry point; rewrite the README around pieces and the book.
6. `fleur_canonical()`, then studies 02–20 inside the sheet grid.

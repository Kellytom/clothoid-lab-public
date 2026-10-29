# Ornament board generator

Builds the two planning pages:

- `docs/ornament-board.html` — 85 plates (45 catalogue ornaments, 27 caps, 9
  leaves, 4 presets), 26 work items, 11 decisions.
- `docs/fleur-studies.html` — the twenty fleur studies, P01–P20.

The pages are standalone HTML. They need no server at runtime; `file://` works.

## What the data is

The catalogue plates come from the `ornaments` repository:

- `fleur-de-lis-20-tests.html` renders the twenty parameter studies.
- `ornaments.html` renders Stage I–V, the terminal studies, the hero fleur and
  the style ends.

The caps and presets come from this repository's `out/caps/` and `out/*.svg`.

`data/` holds the extracted JSON. It is derived and ignored by git. Rebuild it
with the two extractors below.

## Prerequisites

- Chrome can run headless with a debugging port.
- The `ornaments` repository is served locally, because its pages load d3 and
  relative assets.

```sh
# terminal 1
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --headless=old --disable-gpu --remote-debugging-port=9223 \
  --user-data-dir=/tmp/clothoid-board-chrome about:blank

# terminal 2
cd ../ornaments
python3 -m http.server 8010 --bind 127.0.0.1
```

Override with `CDP_PORT` and `ORNAMENTS_URL` if needed.

## Build

```sh
cd /Users/thomaskelly/developer/clothoid-lab
node scripts/board/extract-studies.mjs
node scripts/board/extract-ornaments.mjs
node scripts/board/build-board.mjs
```

The last command rewrites both `docs/` pages. Open them directly, or run
`open -a "Google Chrome" docs/ornament-board.html`.

## Editing the copy

The page text lives in `build-board.mjs`:

- `groupBriefs` — the paragraph at the top of each group.
- `groupSuffix` — the plain-language tail on every catalogue plate.
- `workCopy` — the 26 work-item descriptions.
- `decisions` — the eleven decisions and their options.
- `definitions` — the glossary.

Change the generator, not the generated HTML. The board's own **Export JSON**
keeps ranking, stages and edited notes; it does not change the source text.

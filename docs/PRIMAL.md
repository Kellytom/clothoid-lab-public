# Primal ornaments

A category of its own, after the framework and before the archetypes:

    framework → primal (fire, water, earth, air) → archetypal (fleur, acanthus)

**Primal** means elemental: one force, one grammar. **Archetypal** means
cultural: a fleur-de-lis, an acanthus leaf, a palmette — forms that carry
history and composition, not a single physical idea.

The primal set is where the framework is proved against nature rather than
against an existing drawing. Four elements, four studies, one parameter family
each.

## The gate: what "framework is done" means

No primal work starts until all of these are true:

1. **W03 complete** — the twenty fleur studies render from parameter sets, with
   node parity against the old generator.
2. **Terminals complete** — caps, tapers *and* turned terminals (hairpin,
   wrapped bulb), with the cap limit enforced.
3. **Joints** — a junction with a declared contact, a measured gore, and the
   clearance report passing outside the footprint.
4. **Sections** — `Section` exists as a first-class read model, so width laws
   and clearance sample the same stations instead of reconstructing them.
5. **Reachable** — a primal study can be authored, measured and rendered
   through the web app, not only from a script.

Until then this page is intent, not a plan of record.

**Status 2026-10-26:** the first slice exists ahead of the gate, by request —
`clothoid_lab/primal.py` and `docs/primal.html`: one canonical grammar per
element (earth terraces with corners, a water wave, cloud billows, a fire
tongue), rendered from clothoid segments with the terminals each needs. They
are sketches to argue with, not the studies described above: no parameter
families, no measured gores, no web route. The gate still stands for those.

## The four, and what each one tests

| Element | Grammar | What it forces the framework to prove |
|---|---|---|
| **Earth** | strata, roots, facets: long straight runs, true corners, thick-to-thin bands, taper to a point | corner handling (`Segment.corner`), taper laws, heavy/light balance |
| **Water** | flow, parallel waves, droplets: long low-curvature sweeps, bulbs, reflections | section-locked parallels, bulb law, round and teardrop terminals |
| **Air** (cloud) | billows and curls: big arcs into spirals, scalloped edges, light tapers | spiral chains, round caps, clearance between adjacent billows |
| **Fire** | licking tongues: high curvature, hairpins, sharp points, asymmetry | turned terminals, the 120° cap limit, folds at tight radii |

Order of work: **earth → water → air → fire**. Earth is cheapest and tests what
is already built; fire is last because it needs the turned terminals, and it is
the one that will expose any weakness left in the other three.

## What "one study" means

Each element gets the same shape of deliverable as a fleur study:

- one canonical drawing (the acceptance test),
- three to five parameter sets that read as one hand,
- the terminals it needs, named from the existing vocabulary,
- its joints declared, with the gore measured,
- a page under `docs/` with the drawing, the measurements and the parameters.

No fills. Ink on paper, y up, millimetres, one sheet.

## Relationship to the archetypes

The primal studies are not ornaments to copy; they are grammars to reuse. A
fleur's petals are closer to water than to fire; an acanthus is closer to earth
and water than to air. When the archetypes start, their spans should come from
the primal vocabulary — scroll from air, leaf from water, foot and band from
earth — rather than from new special cases.

## Where this sits in the board

The board's work items stop at W26. When the gate above is met, this becomes
**W27 — primal studies** (with W28+ for the four elements if they need separate
tracking), and the archetype work follows as W29. Do not add plates to the board
before their grammar exists; that is the mistake the catalogue already shows.

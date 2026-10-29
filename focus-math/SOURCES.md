# Sources

Everything examined, with the verdict. Stars are a rough signal of who checks
the code, not of whether the maths is right.

## Cloned — permissive, worth reading closely

| Repo | Licence | Size | Why |
|---|---|---|---|
| `ebertolazzi/G1fitting` | BSD-2 | 1 MB | The paper's own G1 fitter: `buildClothoid`, `pointsOnClothoid`, Fresnel. MATLAB + C++ MEX |
| `phillipd94/pyclothoids` | MIT | 129 KB | Python ctypes wrapper over the same engine; a second opinion on calling it |
| `CoffeeKumazaki/euler_spiral` | MIT | 745 KB | Small, readable C++ Euler spiral; useful to check our Fresnel series against |
| `soufianekhiat/qaws` | MIT | 10 MB | Dependency-free C11 curve library: build, evaluate, sample, traverse, inspect |
| `raphlinus/spiro` | Apache-2.0 | 144 KB | Spiral spline through points, G2 by construction. The closest prior art for leaf → branch blends |
| `linebender/kurbo` | Apache-2.0 | 1.3 MB | Curve maths in Rust: cubics, arc fitting, stroke expansion, offsetting |
| `glenzli/paperjs-offset` | MIT | 1.5 MB | Practical Bézier offset / stroke outline, with the failure cases written down |
| `aurimasg/cubic-bezier-offsetter` | MIT | 119 KB | Minimal cubic offset — the smallest readable implementation |
| `AngusJohnson/Clipper2` | BSL-1.0 | 12 MB | Polygon clipping, offsetting, triangulation. For fills, and for clearance via buffered polygons |
| `Mathias1211/Violin_Boundary` | MIT | 213 KB | NURBS violin outline **and f-hole**, plus the optimizer that fits it |

## Referenced — licence, size, or relevance says do not copy

| Repo | Licence | Why not cloned |
|---|---|---|
| `ebertolazzi/Clothoids` | BSD-2 | Already vendored in `vendor/Clothoids` and built into the engine |
| `ebertolazzi/Splines` | not detected (64 MB) | Clothoid/biarc/G2 splines in C++. Licence must be read before any copy; the theory is in the papers |
| `simoncozens/curve-offsetting` | none stated | A paper on offsetting strokes by minimising distance error (the Tunni construction). Read the idea, not the code |
| `nical/lyon` | MIT/Apache (not detected) | 16 MB of path tessellation; we write polylines ourselves |
| `fonttools/fonttools` | MIT | 32 MB; its pens and `cu2qu` are useful reading for stroke work, not worth a clone |
| `CGAL/cgal` | GPL / LGPL-3 | 2D arrangements, straight skeleton, Minkowski sums, exact predicates. The right maths, the wrong licence for this tree |
| `libgeos/geos` | LGPL-2.1 | Distance between polylines, buffers, validity. The engine behind Shapely |
| `shapely/shapely` | BSD-3 | Thin wrapper over GEOS; if we ever want a checker, call it in a script, do not vendor it |
| `boostorg/geometry` | BSL-1.0 | Header-only distance/index/intersection; huge, and we already have an AABB tree in the engine |
| `solvespace/solvespace` | GPL-3.0 | 2D sketch fillet and constraint solving. Read for the algorithm, never paste |
| `OpenCASCADE`, `FreeCAD` | LGPL-2.1 with exception | 2D fillets at a corner, B-spline tooling. Same rule: read, do not copy |
| `micycle1/Clipper2-java` | BSL-1.0 | Port of Clipper2; only if Java enters the picture |
| `ebertolazzi/UtilsLite`, `GenericContainer`, `quarticRootsFlocke` | permissive | Already vendored as Clothoids submodules |

## Looked at, not useful

`matthova/hovalin` (parametric 3D-printable violin body, 22★) — shell, not
outline maths. `RMAReader/Luthier` — abandoned in 2019. Fretboard calculators
and guitar template generators — different problem. Kazakh and Mongolian
ornament generators (`oyu-pattern`, `khee`) — motif-specific, 0–1★, but they
confirm that nobody publishes a general ornament grammar.

## The gap this library does not fill

No public repository carries a ribbon grammar: named ends, a minimum clearance
between strokes, crossings allowed only at declared terminals, and a blend
where a leaf meets a branch. The pieces are spread across the sources above;
the grammar is ours to write.

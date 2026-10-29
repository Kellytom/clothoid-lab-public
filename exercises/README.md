# Exercises

One script per prompt. Each script defines a curve family, writes the closure
residual, solves it with `clothoid_lab.solve.least_squares`, and renders the
result through the normal CLI path. The outputs are `out/<name>.svg` and the
matching `.json`, so an exercise is reproducible from its script.

- `closed_cl_1.py` — start at the origin heading east, a left clothoid, an
  inflection, a right clothoid, back to the origin heading west. Saved as
  `out/closed-cl-1.svg`.

```sh
.venv/bin/python exercises/closed_cl_1.py
```

The solver is a small bounded Levenberg-Marquardt with a numeric Jacobian and no
dependencies beyond the standard library. The geometry calls dominate the cost;
three parameters converge in a few dozen evaluations.

Each exercise prints the solved parameters, the closure residual, and any
property the prompt asked about (here, the ray from the origin meeting the first
clothoid twice, with the nearer hit at the hand-off).

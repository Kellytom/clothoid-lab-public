"""A small bounded least-squares solver for geometry exercises.

No dependencies. A damped Gauss-Newton (Levenberg-Marquardt) step with a
numeric Jacobian is enough for a handful of parameters; the geometry calls are
the expensive part, not the linear algebra.

    result = least_squares(residual, x0, lower=..., upper=...)
    result.x, result.residual, result.converged
"""

from __future__ import annotations

import math


class Result:
    __slots__ = ("x", "residual", "iterations", "converged")

    def __init__(self, x, residual, iterations, converged):
        self.x = x
        self.residual = residual
        self.iterations = iterations
        self.converged = converged

    def __repr__(self):
        return (f"Result(x={self.x!r}, residual={self.residual:.3e}, "
                f"iterations={self.iterations}, converged={self.converged})")


def _linear_solve(a, b):
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[pivot][col]) < 1e-16:
            return None
        m[col], m[pivot] = m[pivot], m[col]
        for row in range(n):
            if row == col:
                continue
            factor = m[row][col] / m[col][col]
            for k in range(col, n + 1):
                m[row][k] -= factor * m[col][k]
    return [m[i][n] / m[i][i] for i in range(n)]


def least_squares(f, x0, lower=None, upper=None, max_iter: int = 200,
                  tol: float = 1e-12, damping: float = 1e-3):
    """Minimise |f(x)|^2. `lower` and `upper` clamp every step.

    Returns a `Result`; `residual` is the final 2-norm, and `converged` says
    whether it fell below `tol`.
    """
    n = len(x0)
    lower = [(-math.inf if lower is None else lower[i]) for i in range(n)]
    upper = [(math.inf if upper is None else upper[i]) for i in range(n)]

    def clamp(values):
        return [min(upper[i], max(lower[i], values[i])) for i in range(n)]

    x = clamp([float(v) for v in x0])
    fx = list(f(x))
    m = len(fx)
    cost = sum(v * v for v in fx)
    lam = damping
    iterations = 0

    for iterations in range(1, max_iter + 1):
        if math.sqrt(cost) <= tol:
            break
        jac = [[0.0] * n for _ in range(m)]
        for j in range(n):
            step = 1e-8 * max(1.0, abs(x[j]))
            trial = list(x)
            trial[j] = min(upper[j], trial[j] + step)
            if trial[j] == x[j]:
                trial[j] = max(lower[j], x[j] - step)
            if trial[j] == x[j]:
                continue
            ft = f(trial)
            delta = trial[j] - x[j]
            for i in range(m):
                jac[i][j] = (ft[i] - fx[i]) / delta

        normal = [[sum(jac[k][i] * jac[k][j] for k in range(m))
                   + (lam if i == j else 0.0) for j in range(n)] for i in range(n)]
        rhs = [-sum(jac[k][i] * fx[k] for k in range(m)) for i in range(n)]
        dx = _linear_solve(normal, rhs)
        if dx is None:
            break

        candidate = clamp([x[i] + dx[i] for i in range(n)])
        fc = list(f(candidate))
        cc = sum(v * v for v in fc)
        if cc < cost:
            x, fx, cost = candidate, fc, cc
            lam = max(1e-12, lam / 3.0)
        else:
            lam *= 10.0
            if lam > 1e14:
                break

    residual = math.sqrt(cost)
    return Result(x, residual, iterations, residual <= tol)

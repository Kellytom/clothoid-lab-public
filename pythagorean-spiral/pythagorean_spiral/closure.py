"""When can a triangle chain end exactly on an axis?

The chain's heading is always `q * alpha` for an integer `q` (plus any exact
right-angle cusps), where `alpha` is the triangle's acute angle.  Landing on an
axis means `q*alpha` is a multiple of pi/2.

That is decidable, and the answer is brutal: with a single triangle it can only
happen at `q = 0`.

    Suppose q*alpha = k*pi/2 with q != 0.  Then alpha is a rational multiple of
    pi, so tan(alpha) is the tangent of a rational multiple of pi.  A classical
    result (Niven) says the only rational tangents of rational multiples of pi
    are 0, +-1.  Here tan(alpha) = a/b with 0 < a < b, so it is neither.  Hence
    q = 0.

So a chain returns to the axis it started on only when the turns cancel
exactly.  It can never *accumulate* its way to 90 degrees: a vertical ending
needs either an explicit right-angle cusp at the join or a global quarter turn
of the finished design.  That is why the sharp join is the only route to a
vertical exit, and it is a theorem, not a limitation of taste.
"""

from __future__ import annotations

def triangular(k: int) -> int:
    return k * (k + 1) // 2


def inverse_triangular(t: int) -> int | None:
    """k with T(k) == t, or None."""
    if t < 0:
        return None
    k = int((_sqrt(8 * t + 1) - 1) // 2)
    for cand in (k - 1, k, k + 1):
        if cand >= 0 and triangular(cand) == t:
            return cand
    return None


def _sqrt(n: int) -> int:
    if n < 0:
        raise ValueError("negative")
    x = int(n ** 0.5)
    while x * x > n:
        x -= 1
    while (x + 1) * (x + 1) <= n:
        x += 1
    return x


# -- closures for a hook: inward +1..+n, outward -m, -2m, ... -----------
def closure_pairs(multiplier: int, max_steps: int = 200) -> list[tuple[int, int]]:
    """(n_in, n_out) with T(n_in) == multiplier * T(n_out).

    These are the only hook configurations that end exactly on the entry axis.
    """
    out = []
    for n_out in range(1, max_steps + 1):
        target = multiplier * triangular(n_out)
        n_in = inverse_triangular(target)
        if n_in is not None:
            out.append((n_in, n_out))
    return sorted(set(out))


# -- closures for a G2 join: exit starts at the entry's last curvature ----
def g2_pairs(max_steps: int = 200) -> list[tuple[int, int]]:
    """(n, j) with j(j+1) == 2 n(n+1).

    Read: enter with turns 1..n, then leave with n, n-1, ..., 1, 0, -1, ..., -j.
    The exit begins at the entry's final curvature, so the join is G2, and the
    turn sum is T(n) + T(n) - T(j) = 0 by the equation above.  Exact closure
    with a smooth join exists, but only at 2, 14, 84, ...
    """
    out = []
    for n in range(1, max_steps + 1):
        # j(j+1) = 2n(n+1)  <=>  T(j) = n(n+1)
        j = inverse_triangular(n * (n + 1))
        if j is not None and j > 0:
            out.append((n, j))
    return out


// csrc/clothoid_api.cpp — the C surface over Bertolazzi's Clothoids.
//
// The Python side holds no C++ types and no compiler knowledge: it loads the
// dylib this file is linked into and speaks these twenty functions. Everything
// here is either a call straight through to G2lib or a bounds and error check
// so a C++ exception cannot cross the boundary.
//
// Functions return 0 on success and a nonzero code on failure. An opaque handle
// is a ClothoidList, which is one chain, not one curve.
//
// The G1 surface: `cl_g1_fit` is the two-point problem (Bertolazzi and Frego's
// buildClothoid), `cl_build_g1` is the spline through points, and `cl_segment`
// reads the fitted pieces back out as the numbers a design needs.

#include <Clothoids.hh>

#include <new>

using G2lib::ClothoidCurve;
using G2lib::ClothoidList;

namespace {
struct Handle {
  // ClothoidList's only usable constructor takes a name; there is no default.
  Handle() : list("clothoid-lab") {}
  ClothoidList list;
};
}  // namespace

extern "C" {

const char *cl_version() { return "clothoids-bertolazzi"; }

Handle *cl_new() {
  try {
    return new Handle();
  } catch (...) {
    return nullptr;
  }
}

void cl_free(Handle *h) { delete h; }

// Continue the chain from where it ended, at a stated curvature and rate.
int cl_push(Handle *h, double k0, double dk, double L) {
  if (h == nullptr || L <= 0) return 1;
  try {
    h->list.push_back(k0, dk, L);
    return 0;
  } catch (...) {
    return 2;
  }
}

// Place a segment at an absolute start point, direction and curvature.
int cl_push_at(Handle *h, double x0, double y0, double t0, double k0, double dk,
               double L) {
  if (h == nullptr || L <= 0) return 1;
  try {
    h->list.push_back(x0, y0, t0, k0, dk, L);
    return 0;
  } catch (...) {
    return 2;
  }
}

// Fit one clothoid from the current end to a point and a direction.
int cl_push_G1(Handle *h, double x1, double y1, double t1) {
  if (h == nullptr) return 1;
  if (h->list.num_segments() == 0) return 3;
  try {
    h->list.push_back_G1(x1, y1, t1);
    return 0;
  } catch (...) {
    return 2;
  }
}

// The two-point G1 fit: a clothoid from (x0,y0,t0) to (x1,y1,t1).
// out[0..2] = starting curvature, curvature rate, arc length.
int cl_g1_fit(double x0, double y0, double t0,
              double x1, double y1, double t1, double tol, double *out) {
  if (out == nullptr) return 1;
  try {
    ClothoidCurve c("clothoid-lab G1");
    int const ok = c.build_G1(x0, y0, t0, x1, y1, t1, tol);
    if (!ok) return 5;
    out[0] = c.kappa_begin();
    out[1] = c.dkappa();
    out[2] = c.length();
    return 0;
  } catch (...) {
    return 2;
  }
}

// A G1 spline through n points. `theta` may be null, in which case the
// directions are estimated; supplied directions are honoured as given.
int cl_build_g1(Handle *h, int n, const double *x, const double *y,
                const double *theta) {
  if (h == nullptr || x == nullptr || y == nullptr || n < 2) return 1;
  try {
    if (theta != nullptr) {
      h->list.build_G1(n, x, y, theta);
    } else {
      h->list.build_G1(n, x, y);
    }
    return 0;
  } catch (...) {
    return 2;
  }
}

// Read segment i back: out[0..5] = x0, y0, theta0, kappa0, dk, length.
int cl_segment(const Handle *h, int i, double *out) {
  if (h == nullptr || out == nullptr) return 1;
  if (i < 0 || i >= h->list.num_segments()) return 3;
  try {
    ClothoidCurve const &c = h->list.get(i);
    out[0] = c.x_begin();
    out[1] = c.y_begin();
    out[2] = c.theta_begin();
    out[3] = c.kappa_begin();
    out[4] = c.dkappa();
    out[5] = c.length();
    return 0;
  } catch (...) {
    return 2;
  }
}

// A G2 spline through n points with prescribed end tangent and curvature.
int cl_build_g2(Handle *h, int n, const double *x, const double *y,
                double theta0, double kappa0, double theta1, double kappa1) {
  if (h == nullptr || x == nullptr || y == nullptr || n < 2) return 1;
  try {
    bool const ok = h->list.build_G2(n, x, y, theta0, kappa0, theta1, kappa1);
    return ok ? 0 : 5;
  } catch (...) {
    return 2;
  }
}

// A closed G2 spline through n points; the list closes on itself.
int cl_build_g2_cyclic(Handle *h, int n, const double *x, const double *y) {
  if (h == nullptr || x == nullptr || y == nullptr || n < 3) return 1;
  try {
    bool const ok = h->list.build_G2_cyclic(n, x, y);
    return ok ? 0 : 5;
  } catch (...) {
    return 2;
  }
}

// Move the shared tangents of a chain to reduce curvature jumps. The positions
// and the two end directions stay put; the pieces are rebuilt around them.
int cl_smooth_g2(Handle *h, int max_iter, double epsi, double *max_dk) {
  if (h == nullptr) return 1;
  try {
    double jump = 0.0;
    bool const ok = h->list.smooth_quasi_G2(max_iter, epsi, jump);
    if (max_dk != nullptr) *max_dk = jump;
    return ok ? 0 : 5;
  } catch (...) {
    return 2;
  }
}

int cl_trim(Handle *h, double s0, double s1) {
  if (h == nullptr) return 1;
  double const L = h->list.length();
  if (s0 < 0.0 || s1 > L || s1 <= s0) return 4;
  try {
    h->list.trim(s0, s1);
    return 0;
  } catch (...) {
    return 2;
  }
}

int cl_reverse(Handle *h) {
  if (h == nullptr) return 1;
  try {
    h->list.reverse();
    return 0;
  } catch (...) {
    return 2;
  }
}

// Fill h with a G2 connector between two end states.
// p = {x0,y0,theta0,kappa0, x1,y1,theta1,kappa1}; method 2, 3 or 0 (CLC).
int cl_g2_connect(Handle *h, int method, const double *p) {
  if (h == nullptr || p == nullptr) return 1;
  try {
    if (method == 2) {
      G2lib::G2solve2arc solver;
      if (solver.build(p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7]) < 0) return 5;
      h->list.build(solver);
    } else if (method == 3) {
      G2lib::G2solve3arc solver;
      if (solver.build(p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7]) < 0) return 5;
      h->list.build(solver);
    } else if (method == 0) {
      G2lib::G2solveCLC solver;
      if (solver.build(p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7]) < 0) return 5;
      h->list.build(solver);
    } else {
      return 1;
    }
    return 0;
  } catch (...) {
    return 2;
  }
}

// Project a point onto the chain. out[0..4] = s, t, x, y, distance.
int cl_project(const Handle *h, double qx, double qy, double *out) {
  if (h == nullptr || out == nullptr) return 1;
  try {
    double x, y, s, t, dst;
    h->list.closest_point_ISO(qx, qy, x, y, s, t, dst);
    out[0] = s; out[1] = t; out[2] = x; out[3] = y; out[4] = dst;
    return 0;
  } catch (...) {
    return 2;
  }
}

// The same against an offset curve: out[0..4] = s, t, x, y, distance.
int cl_project_iso(const Handle *h, double qx, double qy, double d, double *out) {
  if (h == nullptr || out == nullptr) return 1;
  try {
    double x, y, s, t, dst;
    h->list.closest_point_ISO(qx, qy, d, x, y, s, t, dst);
    out[0] = s; out[1] = t; out[2] = x; out[3] = y; out[4] = dst;
    return 0;
  } catch (...) {
    return 2;
  }
}

// Crossings between two chains, as (s on a, s on b) pairs.
// out holds 2*max_hits doubles; count is the number written.
int cl_intersect(const Handle *a, const Handle *b,
                 double iso_a, double iso_b,
                 double *out, int max_hits, int *count) {
  if (a == nullptr || b == nullptr || out == nullptr || count == nullptr ||
      max_hits <= 0) {
    return 1;
  }
  try {
    G2lib::IntersectList hits;
    a->list.intersect_ISO(iso_a, &b->list, iso_b, hits);
    int const n = static_cast<int>(hits.size()) < max_hits
                      ? static_cast<int>(hits.size()) : max_hits;
    for (int i = 0; i < n; ++i) {
      out[2 * i] = hits[i].first;
      out[2 * i + 1] = hits[i].second;
    }
    *count = n;
    return static_cast<int>(hits.size()) > max_hits ? 6 : 0;
  } catch (...) {
    return 2;
  }
}

double cl_length_iso(const Handle *h, double d) {
  return h == nullptr ? 0.0 : h->list.length_ISO(d);
}

int cl_bbox_iso(const Handle *h, double d, double *out) {
  if (h == nullptr || out == nullptr) return 1;
  try {
    double xmin, ymin, xmax, ymax;
    h->list.bbox_ISO(d, xmin, ymin, xmax, ymax);
    out[0] = xmin; out[1] = ymin; out[2] = xmax; out[3] = ymax;
    return 0;
  } catch (...) {
    return 2;
  }
}

// out = {gap x, gap y, gap tx, gap ty}: zero for a closed chain.
int cl_closure_gap(const Handle *h, double *out) {
  if (h == nullptr || out == nullptr) return 1;
  out[0] = h->list.closure_gap_x();
  out[1] = h->list.closure_gap_y();
  out[2] = h->list.closure_gap_tx();
  out[3] = h->list.closure_gap_ty();
  return 0;
}

double cl_length(const Handle *h) {
  return h == nullptr ? 0.0 : h->list.length();
}

int cl_nseg(const Handle *h) {
  return h == nullptr ? 0 : static_cast<int>(h->list.num_segments());
}

// out[0..3] = x, y, theta, kappa
int cl_eval(const Handle *h, double s, double *out) {
  if (h == nullptr || out == nullptr) return 1;
  if (s < 0.0 || s > h->list.length()) return 4;
  try {
    out[0] = h->list.X(s);
    out[1] = h->list.Y(s);
    out[2] = h->list.theta(s);
    out[3] = h->list.kappa(s);
    return 0;
  } catch (...) {
    return 2;
  }
}

// The exact parallel curve at a signed lateral distance, out[0..1].
int cl_eval_offset(const Handle *h, double s, double d, double *out) {
  if (h == nullptr || out == nullptr) return 1;
  if (s < 0.0 || s > h->list.length()) return 4;
  try {
    out[0] = h->list.X_ISO(s, d);
    out[1] = h->list.Y_ISO(s, d);
    return 0;
  } catch (...) {
    return 2;
  }
}

// out[0..3] = xmin, ymin, xmax, ymax
int cl_bbox(const Handle *h, double *out) {
  if (h == nullptr || out == nullptr) return 1;
  try {
    h->list.bbox(out[0], out[1], out[2], out[3]);
    return 0;
  } catch (...) {
    return 2;
  }
}

}  // extern "C"

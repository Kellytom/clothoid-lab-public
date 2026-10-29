"""Watch a design file and rebuild the drawing when it is saved.

This is the two-window loop: Inkscape holds the SVG, an editor holds the design
JSON, and saving the JSON redraws the curve. Inkscape notices the file changed
and offers to reload.

Two rules make it safe to leave running.

The write is atomic. The new document is written beside the old one and renamed
over it, so Inkscape never opens a file that is half written, which is the one
failure that would look like a bug in the geometry.

A design that does not parse, or does not build, leaves the last good drawing
alone. Typing a number one digit at a time passes through states that are not
valid JSON, and a watcher that blanked the file on each of them would be useless.

The poll is a file timestamp, not a daemon and not a socket. Nothing here needs
dbus, and nothing runs when the watcher is not running.
"""

from __future__ import annotations

import os
import subprocess
import time

from . import presets, svg
from .model import Design


def seed(path: str, preset_name: str = "s-curve") -> Design:
    """Write a starting design so there is something to edit."""
    design = presets.get(preset_name)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    design.save(path)
    return design


def rebuild(design_path: str, out_path: str, render, load=None,
            **options) -> tuple[bool, str]:
    """Render the design file into the SVG, atomically. Never clobbers on failure."""
    reader = load or Design.load
    try:
        design = reader(design_path)
        # Always keep the view in the loop: the file Inkscape saved holds the
        # zoom, and a rebuild that dropped it would re-fit the document and move
        # the view under the hand.
        options.setdefault("view", svg.read_view(out_path))
        text, info = render(design, **options)
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    tmp = f"{out_path}.tmp"
    svg.write(tmp, text)
    os.replace(tmp, out_path)
    fit = info["fit"]
    # The two failures look nothing alike, and in the loop the difference is the
    # whole feedback: a fit that misses tolerance is a shape problem, a jumping
    # join is a stale kappa0 in the file you are editing.
    if info["ok"]:
        verdict = "ok"
    elif not info.get("fit_ok", True):
        verdict = f"FIT OVER TOL {fit['error_max']:.4f} mm"
    else:
        verdict = "joins G1: set kappa0 to null to inherit"
    return True, (f"{fit['spans']:3d} cubics  {fit['error_max']:.4f} mm  "
                  f"{info['chain']['backend']}  {verdict}")


def reopen(path: str, app: str = "Inkscape") -> bool:
    """Ask Inkscape to open the file again, so the drawing follows the design.

    This is the macOS open handler, not a file watcher: the app decides whether
    it focuses the window already holding the document or opens a second one.
    Returns whether the handler accepted the request; if it opens a new window
    each time, leave --reopen off and use File > Revert instead.
    """
    try:
        done = subprocess.run(
            ["open", "-a", app, os.path.abspath(path)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15,
        )
        return done.returncode == 0
    except Exception:
        return False


def run(design_path: str, out_path: str, render, interval: float = 0.4,
        seed_preset: str | None = None, reopen_app: str | None = None,
        load=None, **options) -> int:
    """Watch until interrupted. Returns the number of successful rebuilds."""
    if not os.path.exists(design_path):
        if load is not None:
            print(f"no such file: {design_path}", flush=True)
            return 1
        name = seed_preset or "s-curve"
        seed(design_path, name)
        print(f"seeded {design_path} from preset {name}", flush=True)

    def announce(prefix: str, ok: bool, message: str) -> None:
        print(f"{prefix} {message}", flush=True)
        if ok and reopen_app and not reopen(out_path, reopen_app):
            print(f"        could not hand {out_path} to {reopen_app}", flush=True)

    stamp = _stamp(design_path)
    ok, message = rebuild(design_path, out_path, render, load=load, **options)
    print(f"built   {message}" if ok else f"waiting {message}", flush=True)
    if ok and reopen_app:
        reopen(out_path, reopen_app)
    rebuilds = 1 if ok else 0
    started = time.time()

    print(f"watching {design_path} -> {out_path}   (ctrl-c to stop)", flush=True)
    try:
        while True:
            time.sleep(interval)
            now = _stamp(design_path)
            if now == stamp:
                continue
            stamp = now
            ok, message = rebuild(design_path, out_path, render, load=load, **options)
            if ok:
                rebuilds += 1
                announce("rebuilt", ok, message)
            else:
                print(f"kept the last drawing: {message}", flush=True)
    except KeyboardInterrupt:
        secs = time.time() - started
        print(f"stopped after {rebuilds} rebuilds in {secs:.0f}s", flush=True)
        return rebuilds


def _stamp(path: str) -> tuple[int, int]:
    """Change stamp: modification time in nanoseconds, or zero when absent."""
    try:
        st = os.stat(path)
        return (st.st_mtime_ns, st.st_size)
    except OSError:
        return (0, 0)

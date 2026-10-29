"""Put Inkscape's window on one half of the screen, every time it opens.

Inkscape remembers its window frame in its own preferences, in the `geometry`
group, and rewrites that file when it quits. So the frame has to be written
while the application is closed, and the app has to be relaunched afterwards.

This does exactly that, with a backup, and it refuses to force anything: if
Inkscape will not quit, it says so and changes nothing.

    python3 scripts/set_window_geometry.py right
    python3 scripts/set_window_geometry.py left
    python3 scripts/set_window_geometry.py right --no-relaunch

On macOS the file is
`~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/preferences.xml`.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import time

PREFS = os.path.expanduser(
    "~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/preferences.xml"
)
APP = "Inkscape"
MENU_BAR = 25


def screen() -> tuple[int, int]:
    out = subprocess.run(
        ["osascript", "-e", "tell application \"Finder\" to get bounds of window of desktop"],
        capture_output=True, text=True, timeout=20,
    )
    if out.returncode != 0:
        raise SystemExit(f"could not read the screen bounds: {out.stderr.strip()}")
    _, _, w, h = (int(v.strip()) for v in out.stdout.strip().split(","))
    return w, h


def running() -> bool:
    # The bundle launches a process named `inkscape`, lowercase, so the match
    # has to be case-insensitive or the app looks closed while it is running.
    return subprocess.run(["pgrep", "-x", "-i", APP], capture_output=True).returncode == 0


def quit_app(timeout: float = 8.0) -> bool:
    if not running():
        return True
    subprocess.run(["osascript", "-e", f'tell application "{APP}" to quit'],
                   capture_output=True, timeout=20)
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not running():
            return True
        time.sleep(0.3)
    return not running()


def frame(side: str, width: int, height: int) -> dict:
    half_w = width // 2
    half_h = height // 2
    if side == "left":
        return {"x": 0, "y": MENU_BAR, "width": half_w, "height": height - MENU_BAR}
    if side == "top":
        return {"x": 0, "y": MENU_BAR, "width": width, "height": half_h - MENU_BAR}
    if side == "bottom":
        return {"x": 0, "y": half_h, "width": width, "height": height - half_h}
    return {"x": half_w, "y": MENU_BAR, "width": half_w, "height": height - MENU_BAR}


def set_geometry(text: str, values: dict) -> str:
    """Rewrite the attributes of the geometry group, adding any that are missing."""
    match = re.search(r'<group\b[^>]*?id="geometry"[^>]*?/>', text, re.S)
    if not match:
        raise SystemExit("the preferences file has no geometry group to change")
    block = match.group(0)
    new = block
    for name, value in values.items():
        if re.search(rf'{name}="[^"]*"', new):
            new = re.sub(rf'{name}="[^"]*"', f'{name}="{value}"', new)
        else:
            new = new.replace('id="geometry"', f'{name}="{value}"\n       id="geometry"')
    # A maximised window ignores the frame, which is the usual reason it keeps
    # opening across the whole screen.
    new = re.sub(r'maximized="[^"]*"', 'maximized="0"', new)
    return text[:match.start()] + new + text[match.end():]


CHROME = ("commands", "snaptoolbox", "toppanel", "toolbox",
          "statusbar", "panels", "rulers", "scrollbars")


def set_chrome(text: str, hide: bool) -> str:
    """Turn the window chrome off, leaving the menu so the UI can be brought back.

    Inkscape keeps one `state` flag per element under `window`. The `fullscreen`
    and `focus` groups have their own copies, and this leaves them alone: the
    first is what F11 uses, the second what focus mode uses.
    """
    start = text.index('id="window">')
    end = text.index('id="fullscreen">')
    chunk = text[start:end]
    want = "0" if hide else "1"
    for name in CHROME:
        chunk = re.sub(rf'(id="{name}"\s+state=")([01])(")', rf'\g<1>{want}\g<3>', chunk, flags=re.S)
    return text[:start] + chunk + text[end:]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("side", nargs="?", default="right",
                    choices=["right", "left", "top", "bottom"])
    ap.add_argument("--file", default=None, help="an SVG to open after the relaunch")
    ap.add_argument("--no-relaunch", action="store_true", help="leave Inkscape closed")
    ap.add_argument("--bare", action="store_true",
                    help="hide the toolbars, panels, rulers and status bar")
    ap.add_argument("--with-panels", action="store_true",
                    help="put the chrome back")
    args = ap.parse_args(argv)

    if not os.path.exists(PREFS):
        raise SystemExit(f"no Inkscape preferences at {PREFS}")

    was_running = running()
    if not quit_app():
        raise SystemExit("Inkscape did not quit, so its preferences were left alone; "
                         "quit it by hand and run this again")

    width, height = screen()
    values = frame(args.side, width, height)
    backup = PREFS + ".clothoid-lab-backup"
    if not os.path.exists(backup):
        shutil.copy2(PREFS, backup)

    with open(PREFS, "r", encoding="utf-8") as fh:
        text = fh.read()
    updated = set_geometry(text, values)
    if args.bare or args.with_panels:
        updated = set_chrome(updated, hide=args.bare)
    with open(PREFS, "w", encoding="utf-8") as fh:
        fh.write(updated)

    print(f"screen {width}x{height}, {args.side} half: "
          f"{values['width']}x{values['height']} at ({values['x']}, {values['y']})")
    print(f"backup kept at {backup}")
    if args.bare:
        print("chrome hidden: toolbars, panels, rulers, status bar")

    if was_running and not args.no_relaunch:
        cmd = ["open", "-a", APP]
        if args.file:
            cmd.append(os.path.abspath(args.file))
        subprocess.run(cmd, check=False)
        print(f"relaunched {APP}" + (f" with {args.file}" if args.file else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())

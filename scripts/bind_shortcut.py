"""Give Inkscape a keyboard shortcut for File > Revert.

Revert is the refresh key in the two-window loop, and this build ships it with no
binding: the default keymap has `win.document-revert` and no keys on it.

Inkscape loads keymaps from its own `keys` directory, and a user copy named
`default.xml` replaces the system one. So this copies the shipped keymap into the
user config and adds exactly one binding. Nothing else changes, and running it
twice is harmless.

Inkscape reads the keymap at startup, so quit and reopen it afterwards.

    python3 scripts/bind_shortcut.py
    python3 scripts/bind_shortcut.py --keys "<primary>shift+r"
"""

from __future__ import annotations

import argparse
import os
import re
import shutil

SYSTEM_KEYS = ("/Applications/Inkscape.app/Contents/Resources/share/inkscape/"
               "keys/default.xml")
USER_DIR = os.path.expanduser(
    "~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/keys")
USER_KEYS = os.path.join(USER_DIR, "default.xml")
ACTION = "win.document-revert"


def escape(keys: str) -> str:
    return keys.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--keys", default="<primary><alt>r",
                    help='GTK accelerator, for example "<primary><alt>r"')
    args = ap.parse_args(argv)

    if not os.path.exists(SYSTEM_KEYS):
        raise SystemExit(f"no shipped keymap at {SYSTEM_KEYS}")
    os.makedirs(USER_DIR, exist_ok=True)
    if not os.path.exists(USER_KEYS):
        shutil.copy2(SYSTEM_KEYS, USER_KEYS)

    with open(USER_KEYS, "r", encoding="utf-8") as fh:
        text = fh.read()

    binding = f'<bind gaction="{ACTION}" keys="{escape(args.keys)}" />'
    pattern = re.compile(rf'<bind gaction="{re.escape(ACTION)}"[^>]*/>')
    if pattern.search(text):
        text = pattern.sub(binding, text, count=1)
    else:
        text = text.replace("</keys>", f"  {binding}\n</keys>", 1)

    with open(USER_KEYS, "w", encoding="utf-8") as fh:
        fh.write(text)

    print(f"wrote {USER_KEYS}")
    print(f"{ACTION} is now {args.keys}")
    print("Inkscape reads keymaps at startup: quit and reopen it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

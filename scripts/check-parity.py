#!/usr/bin/env python3
"""Compare the local MVP with the public Cloud Run MVP.

Run from the repository root while the local server is up:

    .venv/bin/python scripts/check-parity.py

The remote URL can be overridden with REMOTE_URL, and the local one with
LOCAL_URL. Exit status is 0 only when the served assets and a real render match.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from clothoid_lab.model import Design  # noqa: E402
LOCAL = os.environ.get("LOCAL_URL", "http://127.0.0.1:8000").rstrip("/")
REMOTE = os.environ.get(
    "REMOTE_URL", "https://<your-service>.run.app"
).rstrip("/")


def fetch(url: str, body: bytes | None = None) -> bytes:
    headers = {"content-type": "application/json"} if body is not None else {}
    request = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]


def check(label: str, left: bytes, right: bytes) -> bool:
    same = left == right
    mark = "PASS" if same else "FAIL"
    print(f"{mark}  {label:<22} local {digest(left)}  remote {digest(right)}")
    return same


def main() -> int:
    ok = True
    print(f"local  {LOCAL}")
    print(f"remote {REMOTE}\n")

    for name in ("index.html", "app.js", "style.css"):
        ok &= check(name, fetch(f"{LOCAL}/{name}"), fetch(f"{REMOTE}/{name}"))

    for endpoint in ("presets", "caps"):
        local = json.loads(fetch(f"{LOCAL}/api/{endpoint}"))
        remote = json.loads(fetch(f"{REMOTE}/api/{endpoint}"))
        ok &= check(
            f"/api/{endpoint}",
            json.dumps(local, sort_keys=True).encode(),
            json.dumps(remote, sort_keys=True).encode(),
        )

    design = Design.load(ROOT / "out" / "caps" / "cap-14.json").to_dict()
    payload = json.dumps({
        "design": design,
        "width": 10,
        "page": [200, 250],
    }).encode()
    local = json.loads(fetch(f"{LOCAL}/api/render", payload))
    remote = json.loads(fetch(f"{REMOTE}/api/render", payload))
    ok &= check("render SVG", local["svg"].encode(), remote["svg"].encode())
    ok &= check("render report", local["report"].encode(), remote["report"].encode())

    print("\nPARITY OK" if ok else "\nPARITY FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

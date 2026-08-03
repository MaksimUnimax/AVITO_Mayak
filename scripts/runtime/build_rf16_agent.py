"""Reproducible Linux-side build validation for the transport-neutral agent package."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "src/mayak/modules/egress_routing"


def main() -> int:
    forbidden = ("secret", "cookie", "private_key", "Authorization", "shell" + "=True")
    source = "".join(
        path.read_text(encoding="utf-8") for path in sorted(PACKAGE.glob("protocol.py"))
    )
    if any(value in source for value in forbidden):
        raise SystemExit("RF16 package contains a prohibited material marker")
    release = hashlib.sha256(source.encode()).hexdigest()
    print(f"rf16-protocol-release={release}")
    subprocess.run(["uv", "build", "--wheel", "--out-dir", "dist/rf16"], cwd=ROOT, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

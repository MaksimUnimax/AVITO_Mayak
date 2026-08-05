"""Semantic safety scan for RF22 upload candidates."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

FORBIDDEN = re.compile(
    r"-----BEGIN .*PRIVATE KEY-----|Bearer\s+[A-Za-z0-9._~-]{20,}|postgres(?:ql)?://[^\s:]+:[^\s@]+@",
    re.I,
)
RAW_PROVIDER_KEYS = {
    "html",
    "body",
    "response_body",
    "cookie",
    "session",
    "credential",
    "provider_payload",
}


def walk(value: object, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in RAW_PROVIDER_KEYS:
                raise ValueError(f"raw-provider field at {path}.{key}")
            walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk(child, f"{path}[{index}]")
    elif isinstance(value, str) and FORBIDDEN.search(value):
        raise ValueError(f"credential-like value at {path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    for path in args.paths:
        if path.suffix == ".json":
            walk(json.loads(path.read_text(encoding="utf-8")))
        elif FORBIDDEN.search(path.read_text(encoding="utf-8")):
            raise SystemExit(f"credential-like value in {path}")
    print("RF22_ARTIFACT_SAFETY_VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

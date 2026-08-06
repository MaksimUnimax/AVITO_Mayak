# ruff: noqa: E501
"""Fail-closed scanner for every resilience package payload."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

KEY = re.compile(r"(?:cookie|set-cookie|authorization|bearer|access[_-]?token|refresh[_-]?token|session[_-]?token|password)", re.I)
VALUE = re.compile(r"(?:bearer\s+\S+|mayak_session=\S+|postgres(?:ql)?://[^\s:@/]+:[^\s@/]+@|-----BEGIN [A-Z ]+PRIVATE KEY-----)", re.I)


def findings(paths: list[Path]) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    for path in paths:
        raw = path.read_text(encoding="utf-8", errors="replace")
        if VALUE.search(raw):
            result.append((path.name, "credential-shaped value"))
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            continue
        def walk(item: object) -> None:
            if isinstance(item, dict):
                for key, child in item.items():
                    if KEY.search(str(key)) and child not in (None, "", False, True, "<redacted>", "removed"):
                        result.append((path.name, f"unsafe key: {key}"))
                    walk(child)
            elif isinstance(item, list):
                for child in item:
                    walk(child)
        walk(value)
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("paths", type=Path, nargs="+")
    a = p.parse_args()
    found = findings(a.paths)
    if found:
        raise SystemExit(json.dumps({"finding_count": len(found), "findings": found}))
    print(json.dumps({"finding_count": 0}))


if __name__ == "__main__":
    main()

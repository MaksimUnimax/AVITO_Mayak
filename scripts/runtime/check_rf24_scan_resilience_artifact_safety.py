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


def write_result(paths: list[Path], output: Path) -> list[tuple[str, str]]:
    result = findings(paths)
    output.write_text(json.dumps({
        "scanner": "rf24-scan-resilience-artifact-safety",
        "schema_version": 1,
        "payload_count": len(paths),
        "finding_count": len(result),
        "findings": [{"payload": name, "category": category} for name, category in result],
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("paths", type=Path, nargs="+")
    p.add_argument("--result", type=Path)
    a = p.parse_args()
    found = write_result(a.paths, a.result) if a.result is not None else findings(a.paths)
    if found:
        raise SystemExit(json.dumps({"finding_count": len(found), "findings": found}))
    print(json.dumps({"finding_count": 0}))


if __name__ == "__main__":
    main()

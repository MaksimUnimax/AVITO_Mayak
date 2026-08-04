#!/usr/bin/env python3
"""Fail-closed semantic scan of RF21 JSON values (keys are not scanned)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

SECRET = re.compile(r"(?:-----BEGIN [A-Z ]+PRIVATE KEY-----|Bearer\s+[A-Za-z0-9._~-]{12,}|postgres(?:ql)?://[^\s\"']+:[^\s\"']+@|(?i:cookie)\s*[:=])")


def _values(value: Any) -> list[str]:
    if isinstance(value, dict):
        return [item for child in value.values() for item in _values(child)]
    if isinstance(value, (list, tuple)):
        return [item for child in value for item in _values(child)]
    return [value] if isinstance(value, str) else []


def scan(path: Path) -> None:
    data = json.loads(path.read_text())
    matches = [value for value in _values(data) if SECRET.search(value)]
    if matches:
        raise SystemExit("credential-looking artifact value")
    print(json.dumps({"path": str(path), "result": "PASS", "method": "semantic_value_scan"}))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: check_rf21_artifact_safety.py evidence.json")
    scan(Path(sys.argv[1]))

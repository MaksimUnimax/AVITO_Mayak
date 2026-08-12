#!/usr/bin/env python3
"""Fail-closed semantic scan of RF21 JSON values (keys are not scanned)."""
from __future__ import annotations

import hashlib
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


METHOD = "rf21-semantic-artifact-scan/v3"
EXPECTED_PAYLOADS = frozenset(("rf21.json",))
CLASSIFICATIONS = frozenset(("CLEAN",))


def scan(paths: list[Path], manifest: Path | None = None) -> dict[str, object]:
    if {path.name for path in paths} != EXPECTED_PAYLOADS or any(
        path.name != str(path) or path.is_absolute() for path in paths
    ):
        raise SystemExit("scanner payload inventory must be exactly the two basenames")
    files: list[dict[str, object]] = []
    for path in paths:
        if not path.is_file():
            raise SystemExit(f"missing upload candidate: {path}")
        raw = path.read_bytes()
        # JSON is inspected semantically; text logs/manifests are inspected as
        # text.  In both cases the digest is of the exact upload bytes.
        try:
            values = _values(json.loads(raw)) if path.suffix == ".json" else [raw.decode()]
        except (UnicodeDecodeError, ValueError) as exc:
            raise SystemExit(f"malformed scan candidate: {path}") from exc
        matches = [value for value in values if SECRET.search(value)]
        if matches:
            raise SystemExit("credential-looking artifact value")
        files.append({"basename": path.name, "sha256": hashlib.sha256(raw).hexdigest(),
                      "finding_count": 0, "classification": "CLEAN"})
    result: dict[str, object] = {"scanner_method": METHOD, "result": "PASS",
                                 "finding_count": 0, "payloads": files}
    if manifest is not None:
        serialized = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if any(SECRET.search(value) for value in _values(json.loads(serialized))):
            raise SystemExit("credential-looking scanner manifest value")
        manifest.write_text(serialized)
    print(json.dumps(result, sort_keys=True))
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: check_rf21_artifact_safety.py [--manifest PATH] FILE ...")
    args = sys.argv[1:]
    manifest = None
    if args[:1] == ["--manifest"]:
        if len(args) < 3:
            raise SystemExit("manifest path and at least one file are required")
        manifest, args = Path(args[1]), args[2:]
    scan([Path(arg) for arg in args], manifest)

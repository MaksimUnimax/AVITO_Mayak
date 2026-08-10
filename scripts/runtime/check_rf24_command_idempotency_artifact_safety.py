# ruff: noqa: E501
"""Scan every authoritative RF24 payload for credentials and unsafe data."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

SECRET = re.compile(
    r"(cookie|set-cookie|authorization|bearer|password|session[_-]?token|postgres(?:ql)?://[^\s:@/]+:[^\s@/]+@|BEGIN [A-Z ]+PRIVATE KEY)",
    re.I,
)
NAME = "rf24-command-idempotency-artifact-safety"


def scan(paths: list[Path]) -> dict[str, object]:
    findings: list[dict[str, str]] = []
    for path in paths:
        if not path.is_file() or path.stat().st_size == 0:
            findings.append({"path": path.name, "reason": "missing-or-empty"})
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if SECRET.search(text):
            findings.append({"path": path.name, "reason": "credential-or-session-material"})
        if "PRODUCTION" in text or "personal_data" in text.lower():
            findings.append({"path": path.name, "reason": "production-or-personal-data-marker"})
    return {
        "scanner": NAME,
        "schema_version": 1,
        "finding_count": len(findings),
        "findings": findings,
        "payload_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()
        },
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--result", type=Path, required=True)
    p.add_argument("payloads", type=Path, nargs="+")
    a = p.parse_args()
    result = scan(a.payloads)
    a.result.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if result["finding_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

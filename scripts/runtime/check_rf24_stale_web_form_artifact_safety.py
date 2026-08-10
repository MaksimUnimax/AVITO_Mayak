"""Fail-closed scanner for acceptance artifacts."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

TECHNICAL_ID = "RF24-STALE-WEB-FORM-SCENARIO-01"
PRIVATE_KEY = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")
UNSAFE = re.compile(
    r"(?:authorization:\s*bearer|postgres(?:ql)?://[^\s\"']+:[^\s\"']+@|AKIA[0-9A-Z]{16})", re.I
)


def scan(paths: list[Path]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            findings.append({"path": str(path), "kind": "unreadable", "detail": str(exc)})
            continue
        if PRIVATE_KEY.search(text):
            findings.append(
                {"path": str(path), "kind": "private_key", "detail": "private key material"}
            )
        if UNSAFE.search(text):
            findings.append(
                {
                    "path": str(path),
                    "kind": "credential_or_provider_payload",
                    "detail": "credential-bearing value",
                }
            )
        if "unsafe_environment_dump" in text or "GITHUB_TOKEN=" in text:
            findings.append(
                {
                    "path": str(path),
                    "kind": "environment_dump",
                    "detail": "unsafe environment content",
                }
            )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    findings = scan(args.paths)
    result = {
        "technical_id": TECHNICAL_ID,
        "finding_count": len(findings),
        "findings": findings,
        "real_new_secret_finding_count": sum(
            item["kind"] in {"private_key", "credential_or_provider_payload"} for item in findings
        ),
    }
    args.result.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())

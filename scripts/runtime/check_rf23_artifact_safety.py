"""Scan the exact RF23 acceptance payload and emit its bound manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

VERSION = "rf23-safety-scanner/v1"
EXPECTED = ("rf23-evidence.json", "rf23-full-pytest.log")
FORBIDDEN = re.compile(
    r"-----BEGIN .*PRIVATE KEY-----|Bearer\s+[A-Za-z0-9._~-]{20,}|"
    r"postgres(?:ql)?://[^\s:]+:[^\s@]+@",
    re.I,
)
RAW_KEYS = {
    "html",
    "response_body",
    "cookie",
    "session",
    "credential",
    "password",
    "password_file",
    "access_token",
    "auth_token",
    "private_key",
    "dsn",
    "raw_provider_payload",
}


def _find(value: object, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in RAW_KEYS:
                findings.append(f"sensitive field at {path}.{key}")
            findings.extend(_find(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_find(child, f"{path}[{index}]"))
    elif isinstance(value, str) and FORBIDDEN.search(value):
        findings.append(f"credential-like value at {path}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs=2, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    if tuple(path.name for path in args.paths) != EXPECTED or any(
        path.name != path.parts[-1] or ".." in path.parts for path in args.paths
    ):
        raise SystemExit(
            "RF23 safety scanner requires exact payloads: rf23-evidence.json rf23-full-pytest.log"
        )

    findings: list[str] = []
    payloads: list[dict[str, object]] = []
    for path in args.paths:
        if not path.is_file():
            findings.append(f"missing payload: {path.name}")
            continue
        raw = path.read_bytes()
        if path.name == EXPECTED[0]:
            try:
                findings.extend(_find(json.loads(raw.decode("utf-8"))))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                findings.append(f"malformed JSON: {exc}")
        elif FORBIDDEN.search(raw.decode("utf-8", errors="replace")):
            findings.append(f"credential-like value in {path.name}")
        payloads.append(
            {
                "path": path.resolve().as_posix(),
                "basename": path.name,
                "size": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "result": "PASS" if not findings else "FAIL",
                "classification": "NONE" if not findings else "SENSITIVE_CONTENT",
                "finding_count": len(findings),
            }
        )
    manifest = {
        "scanner_method": VERSION,
        "payloads": payloads,
        "finding_count": len(findings),
        "classification": "PASS" if not findings and len(payloads) == 2 else "BLOCKED",
        "scanner_result": "PASS" if not findings and len(payloads) == 2 else "FAIL",
        "findings": findings,
    }
    args.manifest.write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    if findings:
        raise SystemExit("RF23 safety scanner blocked: " + "; ".join(findings))
    print("RF23_ARTIFACT_SAFETY_VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

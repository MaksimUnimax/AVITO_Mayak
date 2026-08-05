"""Exact-payload RF22 safety scanner and digest manifest producer."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

VERSION = "rf22-safety-scanner/v2"
EXPECTED = ("rf22.json", "rf22-full-pytest.log")
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
    "raw_payload",
}


def _find(value: object, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in RAW_PROVIDER_KEYS:
                findings.append(f"raw-provider field at {path}.{key}")
            findings.extend(_find(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_find(child, f"{path}[{index}]"))
    elif isinstance(value, str) and FORBIDDEN.search(value):
        findings.append(f"credential-like value at {path}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--manifest", type=Path, default=Path("rf22-safety-manifest.json"))
    args = parser.parse_args()
    if tuple(path.name for path in args.paths) != EXPECTED or any(
        ".." in path.parts for path in args.paths
    ):
        raise SystemExit(
            "RF22 safety scanner requires exact payloads: rf22.json rf22-full-pytest.log"
        )
    payloads: list[dict[str, object]] = []
    findings: list[str] = []
    for path in args.paths:
        if not path.is_file() or path.name not in EXPECTED:
            findings.append(f"missing or unsafe payload: {path}")
            continue
        raw = path.read_bytes()
        if path.suffix == ".json":
            try:
                findings.extend(_find(json.loads(raw.decode("utf-8"))))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                findings.append(f"malformed JSON: {exc}")
        elif FORBIDDEN.search(raw.decode("utf-8", errors="replace")):
            findings.append(f"credential-like value in {path.name}")
        payloads.append(
            {"basename": path.name, "size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        )
    manifest = {
        "scanner_method": VERSION,
        "payloads": payloads,
        "finding_count": len(findings),
        "classification": "CLEAN" if not findings and len(payloads) == 2 else "BLOCKED",
        "findings": findings,
    }
    args.manifest.write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    if findings:
        raise SystemExit("RF22 safety scanner blocked: " + "; ".join(findings))
    print("RF22_ARTIFACT_SAFETY_VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

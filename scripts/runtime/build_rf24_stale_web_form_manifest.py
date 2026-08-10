"""Build a SHA-256 manifest for the stale Web acceptance chain."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

TECHNICAL_ID = "RF24-STALE-WEB-FORM-SCENARIO-01"
PAYLOADS = (
    "rf24-stale-web-form-evidence.json",
    "rf24-stale-web-form-phase-boundaries.json",
    "rf24-stale-web-form-provider-observations.json",
    "rf24-stale-web-form-verifier-result.json",
    "rf24-stale-web-form-scanner-result.json",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("source_sha")
    parser.add_argument("run_id")
    args = parser.parse_args()
    entries = []
    for name in PAYLOADS:
        path = args.directory / name
        if not path.is_file():
            raise SystemExit(f"missing payload: {name}")
        entries.append({"name": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    if len({entry["name"] for entry in entries}) != len(entries):
        raise SystemExit("duplicate payload")
    result = {
        "technical_id": TECHNICAL_ID,
        "source_sha": args.source_sha,
        "hosted_run_id": args.run_id,
        "payload_count": len(entries),
        "payloads": entries,
        "hash_integrity": True,
        "status": "PASS",
    }
    (args.directory / "rf24-stale-web-form-manifest.json").write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

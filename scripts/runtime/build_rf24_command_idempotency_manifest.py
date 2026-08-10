# ruff: noqa: E501
"""Build the hash-bound RF24 command idempotency manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--scanner-result", type=Path, required=True)
    p.add_argument("--source-sha", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("payloads", type=Path, nargs="+")
    a = p.parse_args()
    scanner = json.loads(a.scanner_result.read_text(encoding="utf-8"))
    if (
        scanner.get("scanner") != "rf24-command-idempotency-artifact-safety"
        or scanner.get("finding_count") != len(scanner.get("findings", []))
        or scanner.get("finding_count") != 0
    ):
        raise SystemExit("scanner is not zero-finding")
    payloads = [
        {
            "filename": x.name,
            "size": x.stat().st_size,
            "sha256": hashlib.sha256(x.read_bytes()).hexdigest(),
        }
        for x in a.payloads
        if x.is_file() and x.stat().st_size
    ]
    if len(payloads) != len(a.payloads):
        raise SystemExit("missing payload")
    a.output.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_name": "rf24-command-idempotency",
                "source_sha": a.source_sha,
                "acceptance_run_id": a.run_id,
                "finding_count": scanner["finding_count"],
                "scanner_result": {
                    "filename": a.scanner_result.name,
                    "sha256": hashlib.sha256(a.scanner_result.read_bytes()).hexdigest(),
                },
                "payloads": payloads,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

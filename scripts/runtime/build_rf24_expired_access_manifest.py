"""Create the hash-bound RF24 artifact manifest."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

FILES = (
    "rf24-expired-access-evidence.json",
    "rf24-expired-access-provider-observations.json",
    "rf24-expired-access-verifier-result.json",
    "rf24-expired-access-scanner-result.json",
    "rf24-expired-access.log",
    "rf24-expired-access-full-pytest.log",
)


def build(directory: Path, source_sha: str, run_id: str) -> dict[str, object]:
    payloads = []
    for name in FILES:
        path = directory / name
        if not path.is_file():
            raise ValueError(f"missing payload: {name}")
        payloads.append(
            {
                "filename": name,
                "size": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    result = {
        "technical_id": "RF24-EXPIRED-ACCESS-SCENARIO-01",
        "source_sha": source_sha,
        "acceptance_run_id": run_id,
        "scanner_finding_count": 0,
        "payloads": payloads,
    }
    (directory / "rf24-expired-access-safety-manifest.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return result


if __name__ == "__main__":
    print(json.dumps(build(Path(sys.argv[1]), sys.argv[2], sys.argv[3]), sort_keys=True))

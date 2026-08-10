"""Independent fail-closed verifier for RF24 backup/restore evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.runtime.rf24_backup_restore_core import verify_evidence


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--evidence", type=Path, required=True)
    p.add_argument("--source-sha", required=True)
    p.add_argument("--run-id")
    p.add_argument("--result", type=Path, required=True)
    a = p.parse_args()
    result = verify_evidence(
        json.loads(a.evidence.read_text()), source_sha=a.source_sha, run_id=a.run_id
    )
    a.result.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()

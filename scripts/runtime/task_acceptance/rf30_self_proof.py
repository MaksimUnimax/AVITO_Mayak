"""RF-08-owned harmless verifier proving the reusable acceptance contract."""

from __future__ import annotations

import json
import sys


def main() -> int:
    if len(sys.argv) != 4:
        return 2
    technical_id, project, verifier_id = sys.argv[1:]
    envelope = {
        "schema_version": "mayak-task-acceptance-v1",
        "technical_id": technical_id,
        "project": project,
        "verifier_id": verifier_id,
        "status": "PASS",
        "checks": {
            "authority": True,
            "scope_bound": True,
            "synthetic_only": True,
        },
    }
    sys.stdout.write(json.dumps(envelope, sort_keys=True, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

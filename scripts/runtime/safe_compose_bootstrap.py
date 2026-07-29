#!/usr/bin/env python3
"""Emit only allowlisted, stage-coded Compose acceptance diagnostics."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Final

STAGES: Final = (
    "PREFLIGHT", "IMAGE_IDENTITY", "SECRET_ROOT_CREATE", "SECRET_GENERATION",
    "SECRET_OWNERSHIP", "COMPOSE_CONFIG", "NETWORK_CREATE", "POSTGRES_CREATE",
    "POSTGRES_READINESS", "POSTGRES_SECRET_READ", "BOOTSTRAP_SECRET_READ",
    "DB_BOOTSTRAP", "MIGRATION", "MIGRATION_HEAD_VERIFY", "APPLICATION_SECRET_READ",
    "CLEANUP", "COMPLETE",
)
CLASSIFICATIONS: Final = (
    "NONE", "FILESYSTEM_PERMISSION", "OWNER_MISMATCH", "MODE_MISMATCH",
    "SECRET_FILE_MISSING", "SECRET_FILE_PERMISSION", "SOURCE_TARGET_MISMATCH",
    "COMPOSE_CONFIG_ERROR", "DOCKER_RESOURCE_COLLISION", "CONTAINER_EXITED",
    "READINESS_TIMEOUT", "AUTHENTICATION_REJECTED", "BOOTSTRAP_FAILED",
    "MIGRATION_FAILED", "MIGRATION_HEAD_MISMATCH", "APPLICATION_READ_FAILED",
    "OBSERVABLE_SECRET_LEAK", "UNKNOWN_SAFE_FAILURE",
)
_KEYS: Final = {"schema", "stage", "classification", "ok", "detail"}


def safe_result(
    stage: str, classification: str = "NONE", *, ok: bool | None = None
) -> dict[str, object]:
    if stage not in STAGES or classification not in CLASSIFICATIONS:
        raise ValueError("invalid stage or classification")
    return {
        "schema": "rf08-safe-bootstrap-v1",
        "stage": stage,
        "classification": classification,
        "ok": classification == "NONE" if ok is None else ok,
        "detail": "allowlisted-safe-diagnostic",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=STAGES)
    parser.add_argument("--classification", choices=CLASSIFICATIONS, default="NONE")
    args = parser.parse_args(argv)
    try:
        result = safe_result(args.stage, args.classification)
        if set(result) != _KEYS:
            return 1
        sys.stdout.write(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
        return 0 if result["ok"] else 1
    except (OSError, ValueError, TypeError):
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

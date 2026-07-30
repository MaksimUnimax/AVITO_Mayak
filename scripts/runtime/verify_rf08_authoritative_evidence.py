"""Independent RF-08 evidence verifier.

No prover imports are used here.  The stage contract is duplicated as an
immutable review schema so a prover cannot make its own verdict authoritative.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

TASK_ID = "RF-08-CORRECTIVE-NONROOT-FILE-SECRET-DELIVERY-20260729-01"
BASE = "a12963b8d55b415739056eaba168ae9caf986855"
STAGES = tuple(
    """PREFLIGHT
CANONICAL_COMPOSE_VALIDATION
IMAGE_INPUT_DIGEST
APPLICATION_IMAGE_RESOLUTION
APPLICATION_IMAGE_BUILD_OR_REUSE
APPLICATION_IMAGE_INSPECT
APPLICATION_IMAGE_PROVENANCE_VERIFY
APPLICATION_IMAGE_ENVIRONMENT_VERIFY
APPLICATION_IMAGE_IMPORT_PROBE
FOREIGN_RESOURCE_SNAPSHOT_BEFORE
SECRET_GENERATION_A_CREATE
SECRET_GENERATION_A_VALIDATE
SECRET_GENERATION_A_ACTIVATE
SECRET_GENERATION_A_POINTER_VERIFY
SECRET_CONSUMER_COPIES_A_VERIFY
SECRET_INTENDED_READABILITY_A
SECRET_UNINTENDED_DENIAL_A
POSTGRES_A_CREATE
POSTGRES_A_HEALTH
DATABASE_BOOTSTRAP_A
MIGRATION_UPGRADE_A
MIGRATION_HEAD_A
APPLICATION_QUERY_A
POSTGRES_A_STOP
POSTGRES_A_RECREATE
POSTGRES_A_RESTART_HEALTH
DATABASE_BOOTSTRAP_RESTART_A
MIGRATION_HEAD_RESTART_A
APPLICATION_QUERY_RESTART_A
SECRET_GENERATION_B_CREATE
SECRET_GENERATION_B_VALIDATE
SECRET_GENERATION_B_ACTIVATE
SECRET_GENERATION_B_POINTER_VERIFY
APPLICATION_AUTH_REJECTION_B
APPLICATION_AUTH_REJECTION_B_CLASSIFY
SECRET_ROLLBACK_A_ACTIVATE
SECRET_ROLLBACK_A_POINTER_VERIFY
POSTGRES_ROLLBACK_A_RECREATE
POSTGRES_ROLLBACK_A_HEALTH
DATABASE_BOOTSTRAP_ROLLBACK_A
MIGRATION_HEAD_ROLLBACK_A
APPLICATION_QUERY_ROLLBACK_A
SECRET_GENERATION_C_CREATE
SECRET_GENERATION_C_VALIDATE
SECRET_GENERATION_C_ACTIVATE
POSTGRES_C_REMOVE_AND_VOLUME_ABSENCE
POSTGRES_C_CREATE
POSTGRES_C_HEALTH
DATABASE_BOOTSTRAP_C
MIGRATION_UPGRADE_C
MIGRATION_HEAD_C
APPLICATION_QUERY_C
ABRUPT_ACTIVATION_D_EXIT_70
SECRET_RECOVERY_D_AND_POINTER_VERIFY
POST_RECOVERY_DATABASE_AND_APPLICATION_PROOF
TASK_CLEANUP_AND_PRIVATE_OUTPUT_REMOVAL
FOREIGN_RESOURCE_EQUALITY_AND_EVIDENCE_VALIDATION""".splitlines()
)
SENSITIVE = re.compile(r"(?i)(-----BEGIN .*PRIVATE KEY-----|postgresql://|password\s*=|dsn\s*=)")


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_evidence(evidence_path: Path, source_tree: Path) -> dict[str, object]:
    document = json.loads(evidence_path.read_text(encoding="utf-8"))
    if document.get("technical_id") != TASK_ID or document.get("expected_base") != BASE:
        raise ValueError("identity or base mismatch")
    if document.get("required_stage_order") != list(STAGES) or len(STAGES) != 57:
        raise ValueError("exact stage contract mismatch")
    stages = document.get("stages")
    if not isinstance(stages, list) or len(stages) != 57:
        raise ValueError("stage rows missing")
    seen_operations: set[str] = set()
    for expected, row in zip(STAGES, stages):
        if not isinstance(row, dict) or row.get("name") != expected or row.get("status") != "PASS":
            raise ValueError(f"invalid row: {expected}")
        for key in ("operation_id", "parser_id", "oracle_id", "evidence"):
            if not row.get(key):
                raise ValueError(f"missing {key}: {expected}")
        operation = row["operation_id"]
        if operation in seen_operations and expected not in {
            "SECRET_GENERATION_A_VALIDATE",
            "SECRET_GENERATION_B_VALIDATE",
            "SECRET_GENERATION_C_VALIDATE",
        }:
            raise ValueError("incompatible operation reuse")
        seen_operations.add(str(operation))
        if not isinstance(row["evidence"], dict) or "observed" not in row["evidence"]:
            raise ValueError(f"stage-specific evidence missing: {expected}")
    client_row = stages[33]["evidence"]
    classify_row = stages[34]["evidence"]
    if (
        client_row.get("bounded_client_outcome")
        != "CLIENT_CONNECTION_ATTEMPT_FAILED_PENDING_SERVER_CLASSIFICATION"
        or client_row.get("connection_attempted") is not True
        or client_row.get("client_sqlstate") not in (None, "28P01")
    ):
        raise ValueError("B client result is not a bounded failed attempt")
    if (
        classify_row.get("classification") != "POSTGRESQL_AUTHENTICATION_REJECTED_SQLSTATE_28P01"
        or classify_row.get("server_sqlstate") != "28P01"
        or classify_row.get("correlation_method")
        not in ("exact_application_name", "remote_ip_fallback")
        or classify_row.get("matching_event_count") != 1
    ):
        raise ValueError("B server correlation proof missing")
    if not isinstance(classify_row.get("correlation_id"), str):
        raise ValueError("B correlation identity missing")
    hashes = document.get("production_tree_hashes")
    if not isinstance(hashes, dict):
        raise ValueError("source hashes missing")
    for relative, expected in hashes.items():
        if (
            not isinstance(relative, str)
            or not isinstance(expected, str)
            or _hash(source_tree / relative) != expected
        ):
            raise ValueError(f"source hash mismatch: {relative}")
    manifest = document.get("build_input_manifest")
    if not isinstance(manifest, list) or not any(
        isinstance(item, dict) and item.get("path") == "README.md" for item in manifest
    ):
        raise ValueError("complete build input manifest missing README.md")
    if not document.get("image_id"):
        raise ValueError("image id missing")
    snapshots = document.get("foreign_snapshots")
    if not isinstance(snapshots, dict) or not snapshots.get("before") or not snapshots.get("after"):
        raise ValueError("foreign snapshots missing")
    cleanup = document.get("cleanup_result")
    if not isinstance(cleanup, dict) or not cleanup:
        raise ValueError("cleanup result missing")
    tests = document.get("test_runs")
    if (
        not isinstance(tests, dict)
        or not tests
        or any(
            not isinstance(v, dict)
            or not all(k in v for k in ("passed", "failed", "errors", "skipped"))
            for v in tests.values()
        )
    ):
        raise ValueError("test counts missing")
    controls = document.get("b_negative_controls")
    if not isinstance(controls, dict) or controls.get("all_passed") is not True:
        raise ValueError("B negative controls missing")
    encoded = json.dumps(document, sort_keys=True)
    if SENSITIVE.search(encoded):
        raise ValueError("prohibited sensitive material")
    if document.get("verdict") != "PUBLISHED_FOR_CHATGPT_REVIEW":
        raise ValueError("verdict missing")
    return {
        "verified": True,
        "stage_count": 57,
        "source_hashes_checked": len(hashes),
        "test_runs_checked": len(tests),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    parser.add_argument("source_tree", type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(verify_evidence(args.evidence, args.source_tree), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

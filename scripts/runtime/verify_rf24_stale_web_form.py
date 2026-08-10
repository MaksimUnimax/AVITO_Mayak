"""Independent fail-closed verifier for stale Web form evidence."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

TECHNICAL_ID = "RF24-STALE-WEB-FORM-SCENARIO-01"
PHASES = [f"S{i}" for i in range(9)]


def verify(data: dict[str, Any], source_sha: str) -> None:
    if data.get("identity", {}).get("technical_id") != TECHNICAL_ID:
        raise AssertionError("technical identity mismatch")
    if data.get("identity", {}).get("source_sha") != source_sha:
        raise AssertionError("source SHA mismatch")
    phases = data.get("phases")
    if not isinstance(phases, list) or [item.get("phase") for item in phases] != PHASES:
        raise AssertionError("missing, duplicate, or reordered phase")
    summary = data.get("summary")
    if not isinstance(summary, dict):
        raise AssertionError("summary is missing")
    required = {
        "N": int,
        "N+1": int,
        "N+2": int,
        "stale_http_status": int,
        "stale_mutation_accepted": bool,
        "conflict_boundary_reached": bool,
        "stale_revision_delta": int,
        "stale_work_delta": int,
        "stale_notification_outbox_delta": int,
        "stale_provider_call_delta": int,
        "fresh_reload_version": int,
        "final_version": int,
    }
    for key, kind in required.items():
        if not isinstance(summary.get(key), kind):
            raise AssertionError(f"missing or malformed summary fact: {key}")
    if not (
        summary["N"] + 1 == summary["N+1"] == summary["fresh_reload_version"]
        and summary["N"] + 2 == summary["N+2"] == summary["final_version"]
        and summary["stale_http_status"] == 409
        and summary["stale_mutation_accepted"] is False
        and summary["conflict_boundary_reached"] is True
        and all(
            summary[key] == 0
            for key in (
                "stale_revision_delta",
                "stale_lifecycle_success_delta",
                "stale_work_delta",
                "stale_listing_comparison_delta",
                "stale_notification_outbox_delta",
                "stale_provider_call_delta",
            )
        )
        and summary["final_fresh_revision_delta"] == 1
        and summary["stale_value_absent"] is True
        and summary["concurrent_value_survived_stale_rejection"] is True
        and summary["fresh_value_authoritative_after_fresh_submission"] is True
    ):
        raise AssertionError("stale Web invariants failed")
    for key in (
        "direct_Web_business_DML",
        "direct_foreign_module_DML",
        "owner_bypass_DML",
        "raw_provider_payload_persisted",
        "production_personal_data",
        "credential_exposure",
    ):
        if summary.get(key) is not False:
            raise AssertionError(f"unsafe evidence fact: {key}")
    if summary.get("live_provider_calls") != 0:
        raise AssertionError("provider calls were not disabled")
    contract = summary.get("form_contract", {})
    if not all(
        contract.get(key) is True
        for key in (
            "expected_row_version_server_read",
            "single_expected_row_version",
            "extra_authority_fields_rejected",
            "client_validation_not_authority",
        )
    ):
        raise AssertionError("Web contract evidence is incomplete")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    parser.add_argument("source_sha")
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.source_sha):
        raise SystemExit("invalid source SHA")
    try:
        data = json.loads(args.evidence.read_text(encoding="utf-8"))
        verify(data, args.source_sha)
        result = {"technical_id": TECHNICAL_ID, "source_sha": args.source_sha, "status": "PASS"}
    except (OSError, json.JSONDecodeError, AssertionError, TypeError, ValueError) as exc:
        result = {
            "technical_id": TECHNICAL_ID,
            "source_sha": args.source_sha,
            "status": "FAIL",
            "reason": str(exc),
        }
        args.result.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
        return 1
    args.result.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

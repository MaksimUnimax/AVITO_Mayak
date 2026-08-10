"""Fail-closed verifier for RF24 unsupported-filter evidence."""
# ruff: noqa: E501

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

TECHNICAL_ID = "RF24-UNSUPPORTED-FILTER-SCENARIO-01"


def verify(data: dict[str, Any], source_sha: str, run_id: str | None) -> None:
    print(
        "RF24 evidence diagnostic: "
        f"classification={data.get('baseline_classification')!r} "
        f"unsupported={data.get('unsupported', {}).get('validation_state')!r}/"
        f"{data.get('unsupported', {}).get('candidate_state')!r} "
        f"positive={data.get('positive_control', {}).get('validation_state')!r}/"
        f"{data.get('positive_control', {}).get('candidate_state')!r} "
        f"tamper={data.get('client_tamper_denied')!r} "
        f"unknown={data.get('unknown_field_blocked')!r} "
        f"scope={data.get('wrong_scope_fallback_denied')!r} "
        f"zero={data.get('zero_effect', {})!r}"
    )
    if data.get("technical_id") != TECHNICAL_ID or data.get("source_sha") != source_sha:
        raise AssertionError("technical/source binding failed")
    if run_id is not None and data.get("hosted_run_id") != run_id:
        raise AssertionError("run binding failed")
    if data.get("baseline_classification") not in {
        "EXISTING_PRODUCTION_SEMANTICS_SUFFICIENT",
        "PRODUCTION_GAP_WITHIN_UNSUPPORTED_FILTER_BOUNDARY",
        "PRODUCTION_CORRECTIVE_REQUIRED_AND_IMPLEMENTED",
    }:
        raise AssertionError("missing baseline classification")
    unsupported = data.get("unsupported", {})
    if unsupported.get(
        "validation_state"
    ) != "UNSUPPORTED" or "FIELD_UNSUPPORTED" not in unsupported.get("reason_codes", ()):
        raise AssertionError("unsupported validation was not proven")
    if unsupported.get(
        "candidate_state"
    ) != "UNSUPPORTED" or "DRAFT_UNSUPPORTED" not in unsupported.get("candidate_reason_codes", ()):
        raise AssertionError("unsupported candidate was not proven")
    if unsupported.get("candidate_fields"):
        raise AssertionError("unsupported field became a candidate")
    positive = data.get("positive_control", {})
    if positive.get("validation_state") != "VALID" or positive.get("candidate_state") != "PREPARED":
        raise AssertionError("positive control failed")
    if not all(
        data.get(key)
        for key in ("client_tamper_denied", "unknown_field_blocked", "wrong_scope_fallback_denied")
    ):
        raise AssertionError("boundary denial missing")
    zero = data.get("zero_effect", {})
    for key in (
        "beacon_row_version_delta",
        "beacon_revision_delta",
        "scan_work_delta",
        "listing_comparison_delta",
        "notification_outbox_delta",
        "provider_call_delta",
    ):
        if zero.get(key) != 0:
            raise AssertionError(f"non-zero rejected effect: {key}")
    for key in (
        "source_url_unchanged",
        "lifecycle_unchanged",
        "unsupported_value_absent",
        "unknown_value_absent",
    ):
        if zero.get(key) is not True:
            raise AssertionError(f"missing zero-effect proof: {key}")
    if zero.get("filter_catalog_direct_beacon_write") is not False:
        raise AssertionError("catalog foreign write claimed")
    if data.get("catalog_governed_bypass_present") is not False:
        raise AssertionError("Web bypass classification failed")
    for key in (
        "live_provider_calls",
        "raw_provider_payload_persisted",
        "production_personal_data",
        "direct_foreign_module_DML",
        "owner_bypass_DML",
        "public_ingress",
        "postgres_host_published",
        "invented_avito_filter",
    ):
        if data.get(key) not in (0, False):
            raise AssertionError(f"security invariant failed: {key}")
    if data.get("credentials_exposure") != "none" or data.get("foreign_resource_impact") != "none":
        raise AssertionError("security redaction invariant failed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--run-id")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.source_sha):
        raise SystemExit("invalid source SHA")
    verify(json.loads(args.evidence.read_text(encoding="utf-8")), args.source_sha, args.run_id)
    print(f"{TECHNICAL_ID}: verifier=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Fail-closed verifier for the RF24 two-account Web isolation evidence."""
# ruff: noqa
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

TECHNICAL_ID = "RF24-CROSS-ACCOUNT-ACCESS-SCENARIO-01"
PHASES = [f"C{i}" for i in range(11)]


def verify(data: dict[str, Any], source_sha: str, run_id: str | None = None) -> None:
    identity = data.get("identity", {})
    if identity.get("technical_id") != TECHNICAL_ID or identity.get("source_sha") != source_sha:
        raise AssertionError("technical identity or source SHA mismatch")
    if run_id is not None and identity.get("hosted_run_id") != run_id:
        raise AssertionError("hosted run mismatch")
    phases = data.get("phases")
    if not isinstance(phases, list) or [p.get("phase") for p in phases] != PHASES:
        raise AssertionError("C0-C10 phases are missing, duplicated, or reordered")
    summary = data.get("summary")
    if not isinstance(summary, dict):
        raise AssertionError("summary missing")
    if summary.get("account_a") == summary.get("account_b") or not summary.get("distinct_accounts"):
        raise AssertionError("account isolation collapsed")
    if summary.get("session_a_account") != summary.get("account_a") or summary.get("session_b_account") != summary.get("account_b"):
        raise AssertionError("session authority mismatch")
    required_false = ("cross_mutation_accepted", "b_row_version_changed_by_a", "b_revision_changed_by_a",
                      "idempotency_poisoned", "client_authority_tamper_accepted", "direct_Web_business_DML",
                      "direct_foreign_module_DML", "owner_bypass_DML", "raw_provider_payload_persisted",
                      "production_personal_data", "credential_exposure", "public_ingress",
                      "postgres_host_published", "foreign_resource_impact")
    if any(summary.get(k) is not False for k in required_false):
        raise AssertionError("unsafe or cross-account effect claimed")
    if summary.get("cross_detail_status") != 403 or summary.get("cross_mutation_status") != 403:
        raise AssertionError("cross-account requests were not denied")
    if summary.get("tamper_status") != 400 or summary.get("legitimate_b_status") != 200:
        raise AssertionError("tamper or legitimate-owner contract failed")
    if summary.get("legitimate_b_replay_status") != 200 or summary.get("duplicate_b_revision_delta") != 0:
        raise AssertionError("idempotency replay contract failed")
    if summary.get("live_provider_calls") != 0 or summary.get("scanner_finding_count") != 0:
        raise AssertionError("provider or scanner safety failure")
    if not all(summary.get(k) is True for k in ("a_list_excludes_b", "b_detail_hidden", "a_post_projection_isolated",
                                                "lower_owner_boundary_denies", "support_boundary_explicit")):
        raise AssertionError("projection/owner boundary proof incomplete")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    parser.add_argument("source_sha")
    parser.add_argument("--run-id")
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    result = {"technical_id": TECHNICAL_ID, "source_sha": args.source_sha, "status": "PASS"}
    try:
        if not re.fullmatch(r"[0-9a-f]{40}", args.source_sha):
            raise AssertionError("invalid source SHA")
        verify(json.loads(args.evidence.read_text(encoding="utf-8")), args.source_sha, args.run_id)
    except (OSError, json.JSONDecodeError, AssertionError, TypeError, ValueError) as exc:
        result.update(status="FAIL", reason=str(exc))
        args.result.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
        return 1
    args.result.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

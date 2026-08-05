"""Fail-closed verifier for the redacted RF22 producer artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

TECHNICAL_ID = "RF22-FILTER-CATALOG-BUILDER-RUNTIME-01"
TABLES = {
    "filter_catalog_versions",
    "filter_definitions",
    "filter_options",
    "filter_dependencies",
    "filter_category_applicability",
    "filter_evidence_references",
    "filter_capability_profiles",
}
REQUIRED_TRUE = (
    "application_select_proof",
    "application_insert_denied",
    "application_update_denied",
    "application_delete_denied",
    "published_catalog_loaded",
    "draft_catalog_blocked",
    "option_validation",
    "unknown_option_rejected",
    "multivalue_preserved",
    "range_valid",
    "range_unit_rejected",
    "range_bound_rejected",
    "range_step_rejected",
    "requires_cases",
    "excludes_cases",
    "constrains_cases",
    "all_blocked_cases",
    "valid_draft",
    "client_authority_blocked",
    "catalog_conflict",
    "beacon_revision_conflict",
    "candidate_prepared",
    "beacon_acceptance_required",
    "web_redacted",
    "admin_safe_detail",
    "zero_beacon_mutations",
    "zero_foreign_mutations",
    "zero_provider_calls",
    "zero_raw_payload",
    "synthetic_only",
    "no_global_scope_assumption",
)


def _fail(message: str) -> None:
    raise SystemExit(f"RF22 verification failed: {message}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--candidate-sha", required=True)
    args = parser.parse_args()
    try:
        evidence = json.loads(args.artifact.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _fail(f"artifact unreadable: {exc}")
    if evidence.get("technical_id") != TECHNICAL_ID:
        _fail("technical ID mismatch")
    if evidence.get("candidate_sha") != args.candidate_sha:
        _fail("candidate SHA mismatch")
    if evidence.get("postgres_major") != 18:
        _fail("PostgreSQL 18 observation missing")
    if evidence.get("catalog_tables") != sorted(TABLES):
        _fail("exact seven-table inventory missing")
    if evidence.get("synthetic_catalog_version") != "SYNTHETIC_CATALOG_V1":
        _fail("synthetic catalog marker missing")
    if evidence.get("raw_provider_payload_persisted") is not False:
        _fail("raw provider payload invariant missing")
    if (
        evidence.get("beacon_mutation_count") != 0
        or evidence.get("foreign_table_mutation_count") != 0
    ):
        _fail("mutation boundary failed")
    for name in REQUIRED_TRUE:
        if evidence.get(name) is not True:
            _fail(f"missing measured observation: {name}")
    print("RF22_ACCEPTANCE_VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

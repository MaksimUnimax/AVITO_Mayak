"""Fail-closed verifier for the structured RF20 scenario evidence.
Provider-zero evidence is accepted only from the structured provider_zero_provenance
inventory emitted by the shared scenario.
The inventory includes external_provider_calls_observed and
real_provider_secret_reads_observed as explicit boundary measurements.
It also records raw_provider_payload_records_observed.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        return 2
    try:
        evidence = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return 2
    if not isinstance(evidence, dict):
        return 2
    if evidence.get("technical_id") != "RF20-ADMIN-SUPPORT-RUNTIME-01-CORRECTIVE-04":
        return 2
    expected_sha = os.environ.get("GITHUB_SHA")
    if (
        not expected_sha
        or evidence.get("candidate_sha") != expected_sha
        or re.fullmatch(r"[0-9a-f]{40}", str(evidence.get("candidate_sha"))) is None
    ):
        return 2
    provenance = evidence.get("provider_zero_provenance")
    if (
        not isinstance(provenance, dict)
        or any(
            provenance.get(key) is not False
            for key in (
                "live_provider_adapter_instantiated",
                "provider_boundary_invoked",
                "provider_secret_source_requested",
                "raw_provider_payload_fields",
            )
        )
        or any(
            provenance.get(key) != 0
            for key in (
                "external_provider_calls_observed",
                "real_provider_secret_reads_observed",
                "raw_provider_payload_records_observed",
            )
        )
        or any(
            evidence.get(key) != 0
            for key in (
                "live_provider_calls",
                "real_token_reads",
                "raw_provider_payload_persisted",
            )
        )
    ):
        return 2
    if not str(evidence.get("postgresql_version", "")).startswith("PostgreSQL 18"):
        return 2
    if evidence.get("migration_head") != "RF20_ADMIN_SUPPORT_RUNTIME":
        return 2
    required_true = (
        "operator_customer_distinct",
        "case_projection_match",
        "open",
        "assignment",
        "note",
        "note_replay",
        "fingerprint_conflict",
        "tariff_bootstrap",
        "basic_assignment",
        "access_grant",
        "access_revoke",
        "identity_role_mutation",
        "beacon",
        "beacon_replay",
        "beacon_replay_flag",
        "notification_diagnostics",
        "notification_read_only",
        "direct_foreign_dml_denied",
        "correlation_equality",
    )
    if any(evidence.get(key) is not True for key in required_true):
        return 2
    lifecycle = evidence.get("support_lifecycle")
    if (
        not isinstance(lifecycle, dict)
        or any(lifecycle.get(key) is not True for key in ("escalated", "resolved", "closed"))
        or lifecycle.get("final_state") != "CLOSED"
    ):
        return 2
    if (
        evidence.get("scan") != "POLICY_BLOCKED"
        or evidence.get("foreign_beacon") != "POLICY_BLOCKED"
        or evidence.get("foreign_beacon_replay") is not True
        or evidence.get("stale_beacon") != "CONFLICT"
        or evidence.get("support_stale_row_version") != "CONFLICT"
        or evidence.get("support_stale_state_unchanged") is not True
    ):
        return 2
    if (
        evidence.get("ambiguity") != "AMBIGUOUS"
        or evidence.get("ambiguity_replay") is not True
        or evidence.get("ambiguous_owner_calls") != 1
    ):
        return 2
    concurrency = evidence.get("concurrency")
    if (
        not isinstance(concurrency, dict)
        or concurrency.get("independent_sessions") != 2
        or concurrency.get("one_logical_effect") is not True
        or concurrency.get("owner_effect_count") != 1
        or concurrency.get("owner_resource_count") != 1
    ):
        return 2
    if evidence.get("operator_account_id") == evidence.get("customer_account_id"):
        return 2
    if (
        evidence.get("note_body_in_event_details") is not False
        or evidence.get("note_leakage") is not False
        or not evidence.get("event_timestamps_aware")
        or not evidence.get("host_postgres_publication_proof")
        or evidence.get("host_postgres_published") is not False
    ):
        return 2
    topology = evidence.get("postgres_topology_provenance")
    if (
        not isinstance(topology, dict)
        or topology.get("schema") != "RF20_POSTGRES_TOPOLOGY_PROVENANCE_V1"
        or topology.get("endpoint_resolved") is not True
        or topology.get("association") != "exact_network_alias_or_container_ip"
        or topology.get("candidate_count") != 1
        or not isinstance(topology.get("selected_container_id"), str)
        or not topology.get("selected_container_id")
        or topology.get("actual_endpoint_container_id")
        != topology.get("selected_container_id")
        or topology.get("selected_owner") != "RF20-ADMIN-SUPPORT-RUNTIME-01-CORRECTIVE-04"
        or not isinstance(topology.get("selected_networks"), list)
        or not topology.get("selected_networks")
        or topology.get("foreign_same_network_collision") is not False
        or topology.get("host_publication") is not False
        or topology.get("publication_surfaces") != {
            "network_settings_ports": False,
            "host_config_port_bindings": False,
        }
    ):
        return 2
    if (
        not isinstance(evidence.get("rf20_correlation_id"), str)
        or evidence.get("entitlements_owner_correlation") is None
        or evidence.get("correlation_equality") is not True
        or evidence.get("entitlements_owner_correlation")
        != evidence.get("rf20_correlation_id")
    ):
        return 2
    if (
        evidence.get("beacon_revision_count_after_first")
        != evidence.get("beacon_revision_count_before", -1) + 1
        or evidence.get("beacon_revision_count_after_replay")
        != evidence.get("beacon_revision_count_after_first")
        or evidence.get("notification_before_snapshot")
        != evidence.get("notification_after_snapshot")
    ):
        return 2
    provider = evidence.get("provider_boundary")
    if (
        not isinstance(provider, dict)
        or any(
            provider.get(key) is not False
            for key in (
                "live_adapter_enabled",
                "boundary_invoked",
                "secret_source_requested",
                "raw_provider_payload_fields",
            )
        )
        or evidence.get("provider_calls") != 0
    ):
        return 2
    print("RF20 PostgreSQL evidence verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

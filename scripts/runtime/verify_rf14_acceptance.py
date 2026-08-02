"""Independent RF-14 verifier for measured acceptance observations."""

# ruff: noqa: E501

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

MARKER = "RF14_ACCEPTANCE_VERIFIED"
TECHNICAL_ID = "RF-14-AVITO-PARSER-ADAPTER-RUNTIME-POSTGRES-20260802-01"
EXPECTED_PARENT = "37e9ecf1fb3c7fde6f33c4805b5f921b796f620a"
EXPECTED_HEAD = "RF13_BEACON_RUNTIME_HARDEN"
EXPECTED_COLUMNS = [
    "id", "beacon_id", "run_id", "route_id", "outcome_code",
    "listing_snapshot", "observed_at", "fingerprint", "created_at",
]
EXPECTED_SCENARIOS = [
    "usable_configuration", "usable_listing_page", "clean_empty",
    "empty_without_proof", "captcha", "rate_restricted", "explicit_rejection",
    "malformed", "incomplete", "partial", "unsupported", "ambiguous",
    "transport_unavailable", "transport_ambiguous", "stale_profile",
    "missing_profile", "disputed_profile",
]
GATE_IDS = (
    "identity_exact", "toolchain_exact", "migration_head_exact", "parser_schema_exact",
    "synthetic_registry_closed", "synthetic_determinism", "clean_empty_proof",
    "negative_outcome_matrix", "source_analysis_fail_closed", "multivalue_preserved",
    "duplicate_observation_preserved", "batch_mixed_outcomes", "live_default_disabled",
    "caller_cannot_authorize_live", "synthetic_profile_cannot_authorize_live",
    "live_fake_transport_bounded", "redirect_disabled", "no_retry",
    "raw_payload_persistence_blocked", "normalized_snapshot_bounded", "replay_deterministic",
    "concurrent_replay_single_effect", "rollback_retry", "foreign_tables_unchanged",
    "parser_cleanup", "credential_exposure",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("observations", type=Path)
    parser.add_argument("candidate_sha")
    args = parser.parse_args()
    data = json.loads(args.observations.read_text(encoding="utf-8"))
    identity, postgres = data["identity"], data["postgres"]
    persistence, runtime, source = data["persistence"], data["runtime"], data["source_analysis"]
    actual_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    actual_tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], text=True).strip()
    source_text = (args.root / "src/mayak/modules/avito_parser_adapter/runtime.py").read_text()
    lock_digest = hashlib.sha256((args.root / "uv.lock").read_bytes()).hexdigest()
    gates = {
        "identity_exact": identity["technical_id"] == TECHNICAL_ID and identity["candidate_sha"] == actual_sha == args.candidate_sha and identity["parent_sha"] == EXPECTED_PARENT and identity["tree_sha"] == actual_tree,
        "toolchain_exact": identity["python"] == "3.14.6" and identity["uv"].split()[0:2] == ["uv", "0.11.31"] and identity["uv_lock_sha256"] == lock_digest,
        "migration_head_exact": postgres["alembic_head"] == EXPECTED_HEAD,
        "parser_schema_exact": postgres["parser_columns"] == EXPECTED_COLUMNS,
        "synthetic_registry_closed": runtime["scenario_ids"] == EXPECTED_SCENARIOS and runtime["unknown_scenario_rejected"],
        "synthetic_determinism": runtime["deterministic_equal"],
        "clean_empty_proof": runtime["clean_empty_status"] == "USABLE_RESPONSE",
        "negative_outcome_matrix": all(item in source_text for item in ("CAPTCHA_OR_CHALLENGE", "MALFORMED_RESPONSE", "UNSUPPORTED_STRUCTURE", "RESULT_AMBIGUOUS")),
        "source_analysis_fail_closed": source["no_transport"] == "NOT_SENT" and source["unclassified"] == "RESULT_AMBIGUOUS",
        "multivalue_preserved": "MULTIVALUE_PARAMETER_PRESERVED" in source_text,
        "duplicate_observation_preserved": "duplicate_observations" in source_text,
        "batch_mixed_outcomes": runtime["mixed_succeeded"] == 1 and runtime["mixed_failed"] == 1 and runtime["mixed_ambiguous"] == 1,
        "live_default_disabled": runtime["live_calls_before"] == runtime["live_calls_after"] == 0 and runtime["disabled_handler_calls"] == 0 and runtime["disabled_transport"] == "NOT_SENT",
        "caller_cannot_authorize_live": runtime["caller_forgery_rejected"] and "approved:" not in source_text,
        "synthetic_profile_cannot_authorize_live": runtime["synthetic_rejection_explanation"] == "SYNTHETIC_PROFILE_CANNOT_AUTHORIZE_LIVE",
        "live_fake_transport_bounded": "max_response_bytes" in source_text and "httpx.Timeout" in source_text,
        "redirect_disabled": "follow_redirects=False" in source_text,
        "no_retry": "retries" not in source_text,
        "raw_payload_persistence_blocked": runtime["raw_persistence_rejected"] and "listing_snapshot: Any" not in source_text,
        "normalized_snapshot_bounded": persistence["snapshot_bytes"] <= 32768,
        "replay_deterministic": persistence["replayed"],
        "concurrent_replay_single_effect": persistence.get("concurrent_physical_rows") == 1,
        "rollback_retry": persistence["rollback_before"] == persistence["rollback_after"] and persistence["retry_replayed"] is False,
        "foreign_tables_unchanged": persistence["foreign_before"] == persistence["foreign_after"],
        "parser_cleanup": persistence["committed_after_cleanup"] < persistence["committed_before_cleanup"],
        "credential_exposure": all(token not in source_text for token in ("password=", "Bearer ", "/root/.ssh/")),
    }
    if tuple(gates) != GATE_IDS or not all(gates.values()):
        raise SystemExit("RF14 acceptance gate failure: " + ",".join(key for key, value in gates.items() if not value))
    print(MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# ruff: noqa: E501, E702
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _evidence() -> dict[str, object]:
    return {
        "technical_id": "RF24-UNSUPPORTED-FILTER-SCENARIO-01",
        "source_sha": "a" * 40,
        "hosted_run_id": "run",
        "baseline_classification": "EXISTING_PRODUCTION_SEMANTICS_SUFFICIENT",
        "unsupported": {
            "validation_state": "UNSUPPORTED",
            "reason_codes": ["FIELD_UNSUPPORTED"],
            "candidate_state": "UNSUPPORTED",
            "candidate_reason_codes": ["DRAFT_UNSUPPORTED"],
            "candidate_fields": [],
        },
        "positive_control": {"validation_state": "VALID", "candidate_state": "PREPARED"},
        "client_tamper_denied": True,
        "unknown_field_blocked": True,
        "wrong_scope_fallback_denied": True,
        "zero_effect": {
            "beacon_row_version_delta": 0,
            "beacon_revision_delta": 0,
            "scan_work_delta": 0,
            "listing_comparison_delta": 0,
            "notification_outbox_delta": 0,
            "provider_call_delta": 0,
            "source_url_unchanged": True,
            "lifecycle_unchanged": True,
            "unsupported_value_absent": True,
            "unknown_value_absent": True,
            "filter_catalog_direct_beacon_write": False,
        },
        "catalog_governed_bypass_present": False,
        "live_provider_calls": 0,
        "raw_provider_payload_persisted": False,
        "production_personal_data": False,
        "direct_foreign_module_DML": False,
        "owner_bypass_DML": False,
        "public_ingress": False,
        "postgres_host_published": False,
        "invented_avito_filter": False,
        "credentials_exposure": "none",
        "foreign_resource_impact": "none",
    }


def test_verifier_rejects_unsupported_escalation(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    data = _evidence()
    data["unsupported"]["candidate_state"] = "PREPARED"  # type: ignore[index]
    path.write_text(json.dumps(data), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/runtime/verify_rf24_unsupported_filter.py"),
            str(path),
            "--source-sha",
            "a" * 40,
            "--run-id",
            "run",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0


def test_verifier_accepts_complete_redacted_summary(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(_evidence()), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/runtime/verify_rf24_unsupported_filter.py"),
            str(path),
            "--source-sha",
            "a" * 40,
            "--run-id",
            "run",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

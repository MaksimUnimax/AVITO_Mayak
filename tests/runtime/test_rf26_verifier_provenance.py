# ruff: noqa: E501
import hashlib
from datetime import UTC, datetime

import pytest

from scripts.runtime import verify_rf26_operability_acceptance as verifier


def test_rf26_semantic_derivations_ignore_producer_booleans() -> None:
    assert verifier._derive_duplicate_count({
        "schedule_key": {"work_item_id": "w"},
        "work_ids_before_scheduler": [],
        "work_ids_after_first_materialization": ["w"],
        "work_ids_after_second_scheduler_evaluation": ["w"],
        "counts": {"before": 0, "after_first": 1, "after_second": 1},
    }) == 0
    raw = {
        "P1": {"attempts": [{"id": "a", "state": "PENDING_RECONCILIATION"}]},
        "P2": {"attempts": [{"id": "a", "state": "UNKNOWN", "effect_fingerprint": "e"}]},
        "P3": {"snapshot": {}},
        "P4": {"reconciliations": [{"id": "r", "state": "NO_EFFECT_RETRY"}]},
        "P5": {"attempts": [{"id": "a", "state": "DELIVERED", "effect_fingerprint": "e"}]},
    }
    assert verifier._derive_h15(raw)[:4] == (True, True, 0, 0)


def test_rf26_runner_has_no_h14_timing_interruption() -> None:
    source = open("scripts/runtime/run_rf26_operability_acceptance.py", encoding="utf-8").read()
    h14 = source[source.index("def _h14"):source.index("def _h15")]
    assert "time.sleep" not in h14
    assert "terminate()" not in h14
    assert "RF26_SYNTHETIC_MIGRATION_INTERRUPT" in h14


def test_current_c358_fake_pid_receipt_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(verifier, "verify_evidence", lambda *_args, **_kwargs: None)
    now = datetime.now(UTC).isoformat()
    stages = []
    outputs = {
        "H8_REBUILD_FROM_ZERO": {"migration_revision": "head", "readiness_recovered": True, "runtime_seed_observed": True},
        "H9_BACKUP": {"sha256": "a" * 64, "size": 1, "format": "custom", "pg_dump_version": "18", "pg_restore_version": "18", "readability_verified": True, "inventory_verified": True, "migration_revision": "head"},
        "H10_RESTORE_SEMANTIC_EQUIVALENCE": {"source_semantic_digest": "a", "target_semantic_digest": "a", "semantic_equivalence": True, "source_unchanged": True, "application_read": True, "migration_revision": "head"},
        "H11_API_RESTART": {"process_identity_before": "api-123", "process_identity_after": "api-123-restarted", "readiness_recovered": True},
    }
    for stage_id in verifier.STAGES:
        observed_inputs = {"actual": True, "seed_sha256": "a" * 64}
        if stage_id == "H10_RESTORE_SEMANTIC_EQUIVALENCE":
            observed_inputs.update({"source": "source-db", "target": "target-db"})
        item = {"schema_version": 1, "technical_id": verifier.TECHNICAL_ID, "stage_id": stage_id,
                "source_sha": "a" * 40, "hosted_run_id": "1", "environment_id": "env", "started_at": now,
                "finished_at": now, "duration_seconds": 0.1, "observed_inputs": observed_inputs,
                "observed_outputs": outputs.get(stage_id, {"actual": True}), "assertion": {"result": "PASS"},
                "operation_identity": "fixture"}
        item["receipt_sha256"] = hashlib.sha256(verifier._canonical({k: v for k, v in item.items() if k != "receipt_sha256"})).hexdigest()
        stages.append(item)
    data = {"schema_version": 3, "technical_id": verifier.TECHNICAL_ID, "source_sha": "a" * 40,
            "hosted_run_id": "1", "environment_id": "env", "stages": stages, "rf24_current_run": {},
            "security": {"raw_backup_uploaded": False, "credentials_exposure": False,
                          "production_personal_data": False, "live_provider_calls": 0, "foreign_resource_impact": "none"}}
    with pytest.raises(ValueError, match="H8 runtime readiness projection missing|restart provenance"):
        verifier.verify_evidence_file(data, source_sha="a" * 40, run_id="1")


def test_current_6f6335d_surrogate_executor_is_rejected_by_source_contract() -> None:
    import subprocess

    source = subprocess.check_output(
        ["git", "show", "6f6335de8d0a38985342b8db43371c92830fda60:scripts/runtime/run_rf26_operability_acceptance.py"],
        text=True,
    )
    assert "_real_process_pair" in source
    assert '"-c"' in source
    assert "candidate-api-real-child-process-pair" in source
    current = open("scripts/runtime/run_rf26_operability_acceptance.py", encoding="utf-8").read()
    assert "_real_process_pair" not in current
    assert "python -c" not in current
    assert "mayak.runtime.api" in current
    assert "mayak.runtime.scheduler" in current

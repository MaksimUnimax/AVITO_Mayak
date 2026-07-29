import json

import scripts.runtime.prepare_file_secrets as secret_module
from scripts.runtime.safe_compose_bootstrap import (
    CLASSIFICATIONS,
    PROTOCOL_VERSION,
    STAGES,
    run_protocol,
)


class FakeRunner:
    def __init__(self):
        self.commands = []

    def run(self, command, *, stage):
        self.commands.append((stage, command))
        return True


def test_orchestrator_owns_stage_transitions_and_safe_schema(tmp_path, monkeypatch):
    monkeypatch.setattr(secret_module, "_ALLOWED_ROOTS", (tmp_path,))
    runner = FakeRunner()
    result = run_protocol(root=tmp_path / "secrets", source_sha="source", runner=runner)
    assert result.status == "PASS"
    executed = [stage for stage, _ in runner.commands]
    assert all(stage in executed or any(item.startswith(stage + "_") for item in executed)
               for stage in STAGES if stage not in {
        "SECRET_GENERATION", "GENERATION_VALIDATION", "ACTIVE_POINTER_VALIDATION",
        "FAILED_ACTIVATION_ROLLBACK", "ABRUPT_RECOVERY", "CLEANUP",
    })
    assert all("--no-deps" in command for stage, command in runner.commands
               if stage.startswith("SECRET_MOUNT_PROBES") or stage in {
                   "DB_BOOTSTRAP", "MIGRATION", "APPLICATION_ROLE_CONNECTION"
               })
    assert all("--force-recreate" not in command and "--no-start" not in command
               for _, command in runner.commands)
    payload = result.as_dict()
    assert set(payload) == {
        "protocol_version",
        "task_id",
        "source_sha",
        "stage",
        "status",
        "classification",
        "active_generation_id",
        "previous_generation_id",
        "postgres_major",
        "migration_expected_head",
        "migration_observed_safe_head",
        "effective_numeric_uid",
        "effective_numeric_gid",
        "mode",
        "container_state",
        "health_status",
        "cleanup_status",
        "foreign_impact",
        "no-secret-observed",
    }
    json.dumps(payload)
    assert payload["protocol_version"] == PROTOCOL_VERSION
    assert payload["migration_expected_head"] == "RF09_FINALIZE"
    assert payload["no-secret-observed"] is True


def test_unexecuted_success_stage_cannot_be_reported(tmp_path, monkeypatch):
    monkeypatch.setattr(secret_module, "_ALLOWED_ROOTS", (tmp_path,))
    runner = FakeRunner()
    result = run_protocol(
        root=tmp_path / "secrets", source_sha="source", runner=runner, fail_stage="DB_BOOTSTRAP"
    )
    assert result.status == "FAIL"
    assert result.classification == "BOOTSTRAP_FAILED"
    assert result.stage == "DB_BOOTSTRAP"
    assert all(stage != "ALEMBIC_UPGRADE_CURRENT" for stage, _ in runner.commands)
    assert "OBSERVABLE_SECRET_LEAK" in CLASSIFICATIONS

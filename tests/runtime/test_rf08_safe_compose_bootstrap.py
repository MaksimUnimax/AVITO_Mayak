import json

import pytest

import scripts.runtime.prepare_file_secrets as secret_module
from scripts.runtime.safe_compose_bootstrap import (
    CANONICAL_PROJECT,
    CLASSIFICATIONS,
    EXPECTED_IMAGE_SOURCE,
    EXPECTED_IMAGE_TAG,
    EXPECTED_LOCK_IDENTITY,
    TASK_PROJECT,
    PrivateCommandResult,
    build_safe_environment,
    parse_image_identity,
    parse_migration_head,
    run_protocol,
    validate_explicit_environment,
)


class TypedRunner:
    def __init__(self) -> None:
        self.commands: list[tuple[str, tuple[str, ...]]] = []

    def run(self, command: tuple[str, ...], *, stage: str) -> PrivateCommandResult:
        self.commands.append((stage, command))
        if stage == "PREFLIGHT":
            parsed = {"version": "2.30.0"}
        elif stage in {"EXACT_IMAGE_LOOKUP", "APPLICATION_IMAGE_INSPECT"}:
            parsed = {
                "id": "sha256:" + "1" * 64,
                "source": EXPECTED_IMAGE_SOURCE,
                "revision": EXPECTED_IMAGE_TAG.split(":", 1)[1],
                "lock": EXPECTED_LOCK_IDENTITY,
                "owned": "true",
                "arch": "amd64",
                "os": "linux",
                "user": "10001:10001",
                "env": "safe",
                "ports": "none",
            }
        elif stage in {"IMAGE_IDENTITY", "POSTGRES_UID_GID"}:
            parsed = {
                "image": "postgres:18-bookworm@sha256:"
                "1961f96e6029a02c3812d7cb329a3b03a3ac2bb067058dec17b0f5596aca9296",
                "digest": "sha256:1961f96e6029a02c3812d7cb329a3b03a3ac2bb067058dec17b0f5596aca9296",
                "postgres_uid": 999,
                "postgres_gid": 999,
            }
        elif stage in {"MIGRATION_HEAD_A", "MIGRATION_HEAD_C"}:
            parsed = {"observed_head": "RF09_FINALIZE"}
        elif stage == "POSTGRES_A_READINESS":
            parsed = {
                "state": "running",
                "exit_code": 0,
                "restart_count": 0,
                "health": "healthy",
            }
        elif stage == "FINAL_RESOURCE_ABSENCE":
            parsed = {"containers": 0, "networks": 0, "volumes": 0}
        else:
            parsed = {"executed": True}
        exit_code = 1 if stage == "EXPECTED_CANDIDATE_FAILURE_B" else 0
        return PrivateCommandResult(stage, "docker-safe", exit_code, False, True, parsed, True)


def test_authoritative_protocol_requires_typed_results(tmp_path, monkeypatch):
    monkeypatch.setattr(secret_module, "_ALLOWED_ROOTS", (tmp_path,))
    import scripts.runtime.safe_compose_bootstrap as protocol

    monkeypatch.setattr(protocol, "TASK_RUNTIME_ROOT", tmp_path)
    runner = TypedRunner()
    result = run_protocol(root=tmp_path / "task" / "secrets", source_sha="0" * 40, runner=runner)
    assert result.status == "PASS"
    payload = result.as_dict()
    assert payload["canonical_compose_project"] == CANONICAL_PROJECT
    assert payload["effective_task_compose_project"] == TASK_PROJECT
    assert payload["migration_observed_head"] == "RF09_FINALIZE"
    assert payload["candidate_b_failed_as_expected"] is True
    assert payload["final_container_state"] == "ABSENT"
    runtime_stages = {"POSTGRES_A_CREATE", "DB_BOOTSTRAP_A", "MIGRATION_A"}
    assert any(
        "--no-build" in command
        for stage, command in runner.commands
        if stage == "POSTGRES_A_CREATE"
    )
    assert all(
        "--build" not in command
        for stage, command in runner.commands
        if stage in runtime_stages
    )
    json.dumps(payload)


def test_caller_cannot_supply_success_stage(tmp_path, monkeypatch):
    import scripts.runtime.safe_compose_bootstrap as protocol

    monkeypatch.setattr(protocol, "TASK_RUNTIME_ROOT", tmp_path)
    with pytest.raises(ValueError, match="caller cannot"):
        run_protocol(
            root=tmp_path / "task" / "secrets",
            source_sha="0" * 40,
            runner=TypedRunner(),
            fail_stage="DB_BOOTSTRAP_A",
        )


def test_malformed_safe_output_is_rejected():
    with pytest.raises(ValueError):
        parse_migration_head(b"RF09_FINALIZE\nEXTRA\n")
    with pytest.raises(ValueError):
        parse_image_identity(b"postgres:18-bookworm|999|999\n")
    assert "OBSERVABLE_SECRET_LEAK" in CLASSIFICATIONS


def test_environment_allowlist_preserves_safe_secret_root_and_rejects_credentials(
    tmp_path, monkeypatch
):
    import scripts.runtime.safe_compose_bootstrap as protocol

    monkeypatch.setattr(protocol, "TASK_RUNTIME_ROOT", tmp_path)
    root = tmp_path / "task" / "secrets"
    root.mkdir(parents=True)
    safe = build_safe_environment({"PATH": "/usr/bin", "MAYAK_SECRETS_ROOT": "ignored"}, root=root)
    assert safe["MAYAK_SECRETS_ROOT"] == str(root / "active")
    assert "MAYAK_PASSWORD" not in safe
    with pytest.raises(ValueError):
        validate_explicit_environment({"MAYAK_TOKEN": "credential"})

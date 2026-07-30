import ast
from pathlib import Path

import pytest

import scripts.runtime.prepare_file_secrets as secret_module
from scripts.runtime.safe_compose_bootstrap import (
    CLASSIFICATIONS,
    EXPECTED_IMAGE_SOURCE,
    EXPECTED_IMAGE_TAG,
    EXPECTED_LOCK_IDENTITY,
    REQUIRED_STAGES,
    PrivateCommandResult,
    ProtocolFailure,
    ProtocolTranscript,
    StageResult,
    StageSpec,
    _task_resource_preflight_command,
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


def test_injected_runner_cannot_create_authoritative_pass(tmp_path, monkeypatch):
    monkeypatch.setattr(secret_module, "_ALLOWED_ROOTS", (tmp_path,))
    import scripts.runtime.safe_compose_bootstrap as protocol

    monkeypatch.setattr(protocol, "TASK_RUNTIME_ROOT", tmp_path)
    runner = TypedRunner()
    with pytest.raises(ProtocolFailure):
        run_protocol(root=tmp_path / "task" / "secrets", source_sha="0" * 40, runner=runner)


def _spec(name: str, *, executed: bool = True) -> StageSpec:
    result = StageResult(name, "real-operation", executed, 0, {"ok": True}, True, True)
    return StageSpec(
        name, lambda: result, StageResult, lambda actual: {"ok": True}, frozenset({"ok"}), "FAIL"
    )


def test_transcript_rejects_missing_duplicate_order_unknown_and_unexecuted_stages():
    transcript = ProtocolTranscript(REQUIRED_STAGES[:2])
    with pytest.raises(ProtocolFailure):
        transcript.execute(_spec("CANONICAL_COMPOSE_VALIDATION"))
    transcript.execute(_spec("PREFLIGHT"))
    with pytest.raises(ProtocolFailure):
        transcript.execute(_spec("PREFLIGHT"))
    with pytest.raises(ProtocolFailure):
        transcript.finalize(postconditions={"cleanup": True})
    with pytest.raises(ValueError):
        ProtocolTranscript(("PREFLIGHT", "PREFLIGHT"))
    with pytest.raises(ProtocolFailure):
        ProtocolTranscript().execute(_spec("NOT_A_STAGE"))
    with pytest.raises(ProtocolFailure):
        ProtocolTranscript().execute(_spec("PREFLIGHT", executed=False))


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


def test_production_has_one_transcript_append_authority_and_exact_stage_table():
    source_path = Path(__file__).parents[2] / "scripts/runtime/safe_compose_bootstrap.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    append_lines = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "append"
    ]
    assert len(append_lines) == 1
    transcript = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "ProtocolTranscript"
    )
    assert any(
        isinstance(node, ast.FunctionDef)
        and node.name == "execute"
        and any(
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr == "append"
            for call in ast.walk(node)
        )
        for node in transcript.body
    )
    assert len(REQUIRED_STAGES) == 57
    assert len(set(REQUIRED_STAGES)) == 57


def test_finalization_requires_exact_order_and_all_true_postconditions():
    transcript = ProtocolTranscript(REQUIRED_STAGES[:1])
    transcript.execute(StageSpec(
        "PREFLIGHT",
        lambda: StageResult("PREFLIGHT", "operation", True, 0, {}, True),
        StageResult,
        lambda result: {"operation_id": "operation", "executed": True},
        frozenset({"operation_id", "executed"}),
        "FAIL",
    ))
    with pytest.raises(ProtocolFailure):
        transcript.finalize(postconditions={"all_stages_passed": False})


def test_stale_task_resource_preflight_is_exact_and_foreign_safe():
    command = _task_resource_preflight_command()
    script = command[-1]
    assert command[:2] == ("sh", "-c")
    assert "project='avito-mayak-rf08-secret-delivery'" in script
    assert 'container="${project}-mayak-postgres-1"' in script
    assert 'volume="${project}_postgres-data"' in script
    assert "com.avito-mayak.project-owned" in script
    assert "com.avito-mayak.environment-id" in script
    assert "com.avito-mayak.compose-project" in script
    assert "com.avito-mayak.process-kind" in script
    assert "STOP_FOREIGN_RESOURCE" in script
    assert "docker rm -f" in script
    assert "docker volume rm" in script
    assert REQUIRED_STAGES.index("TASK_RESOURCE_PREFLIGHT") < REQUIRED_STAGES.index(
        "SECRET_GENERATION_A_CREATE"
    )

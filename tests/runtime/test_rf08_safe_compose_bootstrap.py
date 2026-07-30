import ast
import json
import os
from pathlib import Path

import pytest

from scripts.runtime import prepare_file_secrets
from scripts.runtime import safe_compose_bootstrap as scb
from scripts.runtime.rf09_public_bootstrap_adapter import (
    INVARIANT_CODES,
    classify_statement,
)
from scripts.runtime.rf08_docker_authority import MutationAuthority
from scripts.runtime.safe_compose_bootstrap import (
    EXACT_EXIT,
    REQUIRED_STAGES,
    ZERO_REQUIRED,
    ApplicationProbeContract,
    PrivateCommandResult,
    ProtocolFailure,
    ProtocolTranscript,
    StageResult,
    StageSpec,
    application_probe_parity,
    build_application_probe_contract,
    build_input_manifest,
    canonical_stage_spec,
    classify_correlated_b_authentication,
    deterministic_build_input_digest,
    parse_bounded_auth_envelope,
    parse_bounded_bootstrap_result,
)
from scripts.runtime.verify_rf08_authoritative_evidence import STAGES, verify_evidence


def _stage34_result(**parsed: object) -> PrivateCommandResult:
    payload = {
        "import_ok": True,
        "file_read_ok": True,
        "connect_attempted": True,
        "exception_class": "OperationalError",
        "client_sqlstate": None,
        "correlation_id": "rf08b_test01",
        "unexpected_success": False,
    }
    payload.update(parsed)
    return PrivateCommandResult(
        "APPLICATION_AUTH_REJECTION_B",
        "rf08.application_auth_rejection_b",
        78,
        True,
        payload,
        True,
        True,
        False,
    )


class _Stage34Runner:
    def __init__(self, result: PrivateCommandResult) -> None:
        self.result = result
        self.env: dict[str, str] = {}

    def run(self, command: tuple[str, ...], *, stage: str) -> PrivateCommandResult:
        assert stage == "APPLICATION_AUTH_REJECTION_B"
        return self.result


def test_exact_canonical_stage_contract() -> None:
    assert REQUIRED_STAGES == STAGES
    assert len(REQUIRED_STAGES) == 57
    assert "APPLICATION_IMAGE_IMPORT_PROBE" in REQUIRED_STAGES
    assert "TASK_RESOURCE_PREFLIGHT" not in REQUIRED_STAGES


def test_post_recovery_bootstrap_parser_is_typed_and_rejects_text_only() -> None:
    complete = parse_bounded_bootstrap_result(
        b"RF09_DATABASE_BOOTSTRAP_COMPLETE\n", b"Container x Created\n", 0
    )
    assert complete == {}
    assert (
        parse_bounded_bootstrap_result(
            b'{"bootstrap_outcome":"RF09_BOOTSTRAP_SUCCESS","client_sqlstate":null,'
            b'"connection_attempted":true,"connected":true,"cause_type":null,'
            b'"committed":true,"connection_closed":true,"cursor_closed":true,'
            b'"current_object_grants":false,"application_role_valid":true,'
            b'"application_schema_create":false,"invariant_code":null,'
            b'"last_rf09_operation":"RF09_COMMIT","migration_role_valid":true,'
            b'"operation_id":"rf09.public.bootstrap","recovered_generation_id":"g",'
            b'"rolled_back":false,"run_id":"r","schema_owner_valid":true,'
            b'"schema_version":"rf08-post-recovery-bootstrap-v1"}\n',
            b"Container x Created\n",
            0,
        )["bootstrap_outcome"]
        == "RF09_BOOTSTRAP_SUCCESS"
    )
    assert (
        parse_bounded_bootstrap_result(
            b"RF09_DATABASE_BOOTSTRAP_ERROR: BootstrapInvariantError\n", b"", 1
        )
        == {}
    )
    assert parse_bounded_bootstrap_result(b"role already exists\n", b"", 1) == {}


def test_public_adapter_uses_exact_invariant_allowlist() -> None:
    assert INVARIANT_CODES["role capability invariant failed"] == (
        "RF09_ROLE_CAPABILITY_INVARIANT_FAILED"
    )
    assert "role capability invariant failed with detail" not in INVARIANT_CODES


def test_public_adapter_operation_classifier_fails_closed() -> None:
    from psycopg import sql

    assert classify_statement(sql.SQL("SELECT pg_advisory_xact_lock(%s)")) == ("RF09_ADVISORY_LOCK")
    assert classify_statement(sql.SQL("SELECT arbitrary_function()")) == (
        "RF09_UNRECOGNIZED_OPERATION"
    )


def test_no_placeholder_authority_or_fallbacks() -> None:
    source = Path(__file__).parents[2] / "scripts/runtime/safe_compose_bootstrap.py"
    text = source.read_text(encoding="utf-8")
    assert "_generic" not in text
    assert "local-contract" not in text
    assert 'text or "OK"' not in text


def test_active_json_log_selects_newest_task_owned_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    log_root = tmp_path / "postgres-jsonlog"
    log_dir = log_root / "run-1"
    log_dir.mkdir(parents=True)
    older = log_dir / "postgresql.json"
    newer = log_dir / "postgresql.json.json"
    older.write_text("old\n", encoding="utf-8")
    newer.write_text("new\n", encoding="utf-8")
    older.chmod(0o600)
    newer.chmod(0o600)
    os.utime(older, ns=(1_000_000_000, 1_000_000_000))
    os.utime(newer, ns=(2_000_000_000, 2_000_000_000))
    monkeypatch.setattr(scb, "JSON_LOG_ROOT", log_root)
    assert scb._active_json_log(log_dir) == newer


def test_every_stage_has_distinct_operation_parser_and_oracle() -> None:
    source = Path(__file__).parents[2] / "scripts/runtime/safe_compose_bootstrap.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    assert not any(isinstance(node, ast.Name) and node.id == "_generic" for node in ast.walk(tree))
    assert "def _named_oracle" in source.read_text(encoding="utf-8")
    assert len(REQUIRED_STAGES) == len(set(REQUIRED_STAGES))


def test_transcript_rejects_order_missing_execution_and_missing_observed() -> None:
    transcript = ProtocolTranscript(REQUIRED_STAGES[:1])
    bad = StageSpec(
        "PREFLIGHT", lambda: StageResult("PREFLIGHT", "op", True, 0, {}), lambda _: {}, "p", "o"
    )
    with pytest.raises(ProtocolFailure):
        transcript.execute(bad)
    good = StageSpec(
        "PREFLIGHT",
        lambda: StageResult("PREFLIGHT", "op", True, 0, {"observed": "real"}),
        lambda r: {"observed": r.parsed["observed"]},
        "p",
        "o",
    )
    transcript.execute(good)
    with pytest.raises(ProtocolFailure):
        transcript.finalize({"cleanup": False})


def test_canonical_stage34_uses_transcript_and_accepts_exact_78(tmp_path: Path) -> None:
    runner = _Stage34Runner(_stage34_result())
    ctx: dict[str, object] = {
        "runner": runner,
        "root": tmp_path,
        "generations": {},
        "b_correlation_id": "rf08b_test01",
        "source_sha": "0" * 40,
    }
    spec = canonical_stage_spec(ctx, "APPLICATION_AUTH_REJECTION_B", Path(__file__).parents[2])
    assert spec.exit_policy == EXACT_EXIT(78)
    transcript = ProtocolTranscript((spec.name,))
    entry = transcript.execute(spec)
    assert entry.status == "PASS"
    assert entry.evidence["observed"] == (
        "CLIENT_CONNECTION_ATTEMPT_FAILED_PENDING_SERVER_CLASSIFICATION"
    )
    assert transcript.result_for(spec.name).exit_code == 78


@pytest.mark.parametrize("code", [0, 77, 79])
def test_stage34_rejects_wrong_exit(code: int) -> None:
    result = _stage34_result()
    result = PrivateCommandResult(
        result.stage,
        result.command_id,
        code,
        result.executed,
        result.parsed,
        result.stdout_scanned,
        result.stderr_scanned,
        result.private_output_cleaned,
    )
    runner = _Stage34Runner(result)
    ctx: dict[str, object] = {
        "runner": runner,
        "root": Path("/tmp"),
        "generations": {},
        "b_correlation_id": "rf08b_test01",
        "source_sha": "0" * 40,
    }
    spec = canonical_stage_spec(ctx, "APPLICATION_AUTH_REJECTION_B", Path(__file__).parents[2])
    with pytest.raises(ProtocolFailure):
        ProtocolTranscript((spec.name,)).execute(spec)


def test_default_zero_policy_rejects_nonzero_and_d_requires_70() -> None:
    zero = StageSpec(
        "PREFLIGHT",
        lambda: StageResult("PREFLIGHT", "op", True, 78, {}),
        lambda _: {"observed": "x"},
        "p",
        "o",
        ZERO_REQUIRED,
    )
    with pytest.raises(ProtocolFailure):
        ProtocolTranscript(("PREFLIGHT",)).execute(zero)
    abrupt = StageSpec(
        "ABRUPT_ACTIVATION_D_EXIT_70",
        lambda: StageResult("ABRUPT_ACTIVATION_D_EXIT_70", "op", True, 70, {}),
        lambda _: {"observed": "x"},
        "p",
        "o",
        EXACT_EXIT(70),
    )
    assert ProtocolTranscript((abrupt.name,)).execute(abrupt).status == "PASS"


def test_build_input_digest_follows_copy_inputs_and_includes_readme() -> None:
    tree = Path(__file__).parents[2]
    manifest = build_input_manifest(tree, gateway=MutationAuthority())
    paths = {item["path"] for item in manifest}
    assert "README.md" in paths
    assert "Dockerfile" not in paths
    assert not any("__pycache__" in path or path.endswith((".pyc", ".pyo")) for path in paths)
    assert deterministic_build_input_digest(tree, gateway=MutationAuthority())


def test_independent_verifier_rejects_missing_test_counts_and_sensitive_material(
    tmp_path: Path,
) -> None:
    source = Path(__file__).parents[2]
    evidence = {
        "technical_id": "RF-08-CORRECTIVE-NONROOT-FILE-SECRET-DELIVERY-20260729-01",
        "expected_base": "a12963b8d55b415739056eaba168ae9caf986855",
    }
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(evidence), encoding="utf-8")
    with pytest.raises(ValueError):
        verify_evidence(path, source, verifier_gateway=MutationAuthority())


def _b_client(**changes: object) -> dict[str, object]:
    result: dict[str, object] = {
        "import_ok": True,
        "file_read_ok": True,
        "connect_attempted": True,
        "exception_class": "OperationalError",
        "client_sqlstate": None,
        "pgconn_present": True,
        "pgconn_status": 1,
        "used_password": True,
        "needs_password": False,
        "correlation_id": "rf08b_test01",
        "unexpected_success": False,
        "exit_code": 78,
    }
    result.update(changes)
    return result


def _b_server(**changes: object) -> dict[str, object]:
    result: dict[str, object] = {
        "sqlstate": "28P01",
        "severity": "FATAL",
        "user": "mayak_application",
        "database": "mayak",
        "application_name": "rf08b_test01",
        "event_timestamp": "2026-07-30T00:00:00Z",
        "task_postgres_identity": True,
        "remote_identity": "task-probe-ip",
        "event_count": 1,
        "event_after_lower_bound": True,
        "no_competing_events": True,
    }
    result.update(changes)
    return result


def test_b_operational_error_without_client_sqlstate_passes_only_with_server_28p01() -> None:
    result = classify_correlated_b_authentication(_b_client(), _b_server())
    assert result["classification"] == "POSTGRESQL_AUTHENTICATION_REJECTED_SQLSTATE_28P01"
    with pytest.raises(ProtocolFailure):
        classify_correlated_b_authentication(_b_client(), _b_server(sqlstate="28P00"))


def test_a_restart_and_b_share_one_immutable_probe_contract() -> None:
    a = build_application_probe_contract("sha256:" + "a" * 64)
    b = build_application_probe_contract("sha256:" + "a" * 64)
    assert isinstance(a, ApplicationProbeContract)
    assert a.contract_id == b.contract_id
    assert application_probe_parity(a, b)["equal"] is True


def test_b_binding_is_active_generation_scoped_and_constant_time_equal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        prepare_file_secrets,
        "_ALLOWED_ROOTS",
        (*prepare_file_secrets._ALLOWED_ROOTS, tmp_path),
    )
    generation = prepare_file_secrets.prepare_generation(
        tmp_path, postgres_uid=999, postgres_gid=999
    )
    prepare_file_secrets.activate_generation(
        tmp_path, generation, postgres_uid=999, postgres_gid=999
    )
    binding = prepare_file_secrets.prepare_consumer_binding(
        tmp_path, generation, postgres_uid=999, postgres_gid=999
    )
    assert binding["generation_id"] == generation
    assert binding["constant_time_equal"] is True
    assert binding["regular_file"] is True
    assert binding["immutable"] is True
    with pytest.raises(prepare_file_secrets.SecretPreparationError):
        prepare_file_secrets.prepare_consumer_binding(
            tmp_path, "g-" + "0" * 24, postgres_uid=999, postgres_gid=999
        )


def test_b_bounded_parser_requires_one_safe_json_object_and_keeps_rejected_exit() -> None:
    payload = {
        "schema_version": "rf08-stage34-auth-v1",
        "operation_id": "rf08.application_auth_rejection_b",
        "correlation_id": "rf08b_test01",
        "import_state": "IMPORTED",
        "secret_binding_state": "REJECTED",
        "mount_state": "PRESENT",
        "file_state": "MISSING",
        "file_read_attempted": False,
        "file_read_state": "NOT_ATTEMPTED",
        "connection_attempted": False,
        "unexpected_success": False,
        "exception_class_name": None,
        "client_sqlstate": None,
        "pgconn_present": False,
        "pgconn_status": None,
        "timeout": False,
        "final_client_outcome": "SECRET_FILE_MISSING",
    }
    parsed = parse_bounded_auth_envelope(
        (json.dumps(payload, separators=(",", ":")) + "\n").encode(), b"", 66
    )
    assert parsed["final_client_outcome"] == "SECRET_FILE_MISSING"
    assert parsed["exit_code"] == 66
    assert parse_bounded_auth_envelope(b"{}\n{}\n", b"", 66) == {}
    assert parse_bounded_auth_envelope((json.dumps(payload) + "\nextra\n").encode(), b"", 66) == {}


@pytest.mark.parametrize(
    "client_change,server_change",
    [
        ({"client_sqlstate": "28P00"}, {}),
        ({}, {"application_name": "wrong"}),
        ({}, {"user": "wrong"}),
        ({}, {"database": "wrong"}),
        ({}, {"task_postgres_identity": False}),
        ({}, {"event_count": 2}),
        ({"connect_attempted": False}, {}),
        ({"import_ok": False}, {}),
        ({"file_read_ok": False}, {}),
        ({"unexpected_success": True}, {}),
        ({"exit_code": 79}, {}),
    ],
)
def test_b_negative_controls_cannot_become_authentication_rejection(
    client_change: dict[str, object], server_change: dict[str, object]
) -> None:
    with pytest.raises(ProtocolFailure):
        classify_correlated_b_authentication(_b_client(**client_change), _b_server(**server_change))

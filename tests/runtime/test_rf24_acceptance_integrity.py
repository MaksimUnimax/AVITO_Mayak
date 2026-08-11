# ruff: noqa: E501
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]


def _module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_scanner = _module("rf24_scanner", "scripts/runtime/check_rf24_spine_artifact_safety.py")
_producer = _module("rf24_producer", "scripts/runtime/run_rf24_vertical_spine.py")
_verifier = _module("rf24_verifier", "scripts/runtime/verify_rf24_vertical_spine.py")
_provenance = _module("rf24_provenance", "src/mayak/runtime/rf24_provenance.py")
scan = _scanner.scan
SafeResponse = _producer.SafeResponse
verify = _verifier.verify


def _provenance_env(monkeypatch: pytest.MonkeyPatch, technical_id: str, tmp_path: Path) -> None:
    monkeypatch.setenv("MAYAK_RUNTIME_PROFILE", "synthetic_acceptance")
    monkeypatch.setenv("MAYAK_ENVIRONMENT_ID", "run-1")
    monkeypatch.setenv("MAYAK_SYNTHETIC_SCENARIO_RUN_ID", "run-1")
    monkeypatch.setenv("RF24_ACCEPTANCE_HOOKS_ENABLED", "true")
    monkeypatch.setenv("RF24_ACCEPTANCE_TECHNICAL_ID", technical_id)
    monkeypatch.setenv("MAYAK_PROCESS_KIND", "mayak-worker")
    monkeypatch.setenv("RF24_WORKER_OBSERVATIONS", str(tmp_path / "worker.jsonl"))


@pytest.mark.parametrize(
    "technical_id",
    [
        "RF24-SCAN-RUNTIME-RESILIENCE-SCENARIOS-01-CORRECTIVE-02",
        "RF24-BACKUP-RESTORE-SCENARIO-01",
    ],
)
def test_bounded_provenance_authorizes_known_ids_and_stamps_actual_id(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, technical_id: str
) -> None:
    _provenance_env(monkeypatch, technical_id, tmp_path)
    assert _provenance._enabled()
    _provenance.emit_process_observation({"record_type": "worker_test"})
    row = json.loads((tmp_path / "worker.jsonl").read_text(encoding="utf-8"))
    assert row["technical_id"] == technical_id
    assert row["acceptance_run_id"] == "run-1"
    assert row["process_kind"] == "mayak-worker"


@pytest.mark.parametrize(
    "changes",
    [
        {"RF24_ACCEPTANCE_TECHNICAL_ID": "RF24-UNKNOWN"},
        {"RF24_ACCEPTANCE_HOOKS_ENABLED": None},
        {"RF24_ACCEPTANCE_HOOKS_ENABLED": "false"},
        {"MAYAK_RUNTIME_PROFILE": "test"},
        {"MAYAK_SYNTHETIC_SCENARIO_RUN_ID": "other-run"},
    ],
)
def test_provenance_gate_is_fail_closed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, changes: dict[str, str | None]) -> None:
    _provenance_env(monkeypatch, "RF24-BACKUP-RESTORE-SCENARIO-01", tmp_path)
    for key, value in changes.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)
    assert not _provenance._enabled()
    _provenance.emit_process_observation({"record_type": "disabled"})
    assert not (tmp_path / "worker.jsonl").exists()


def test_backup_restore_child_authority_is_limited_to_worker_and_scheduler(tmp_path: Path) -> None:
    base = {"MAYAK_SECRETS_DIR": str(tmp_path)}
    for kind in ("worker", "scheduler"):
        child = _producer._child_environment(
            base, source_sha="a" * 40, run_id="run-1", kind=kind,
            database_host="mayak-postgres", database_name="mayak", port="18080",
            scheduler_observations=tmp_path / "scheduler.jsonl", worker_observations=tmp_path / "worker.jsonl",
        )
        assert child["RF24_ACCEPTANCE_HOOKS_ENABLED"] == "true"
        assert child["RF24_ACCEPTANCE_TECHNICAL_ID"] == "RF24-BACKUP-RESTORE-SCENARIO-01"
    api = _producer._child_environment(
        base, source_sha="a" * 40, run_id="run-1", kind="api",
        database_host="mayak-postgres", database_name="mayak", port="18080",
        scheduler_observations=tmp_path / "scheduler.jsonl", worker_observations=tmp_path / "worker.jsonl",
    )
    assert "RF24_ACCEPTANCE_HOOKS_ENABLED" not in api
    assert "RF24_ACCEPTANCE_TECHNICAL_ID" not in api


def test_backup_restore_consumer_rejects_cross_scenario_and_accepts_exact_identity(tmp_path: Path) -> None:
    path = tmp_path / "observations.jsonl"
    exact = {"technical_id": "RF24-BACKUP-RESTORE-SCENARIO-01", "acceptance_run_id": "run-1", "process_kind": "mayak-scheduler"}
    path.write_text(json.dumps(exact) + "\n", encoding="utf-8")
    assert _producer._read_jsonl(path, process_kind="mayak-scheduler", run_id="run-1") == [exact]
    for key, value in (("technical_id", "RF24-SCAN-RUNTIME-RESILIENCE-SCENARIOS-01-CORRECTIVE-02"), ("acceptance_run_id", "other"), ("process_kind", "mayak-worker")):
        wrong = dict(exact, **{key: value})
        path.write_text(json.dumps(wrong) + "\n", encoding="utf-8")
        with pytest.raises(RuntimeError, match="invalid"):
            _producer._read_jsonl(path, process_kind="mayak-scheduler", run_id="run-1")


def test_checkout_head_uses_process_local_exact_safe_directory(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[tuple[tuple[str, ...], dict[str, object]]] = []

    def fake_check_output(args: tuple[str, ...], **kwargs: object) -> str:
        calls.append((args, kwargs))
        return "a" * 40 + "\n"

    monkeypatch.setattr(_producer.subprocess, "check_output", fake_check_output)
    root = tmp_path / "checkout with spaces"
    assert _producer._checkout_head(root) == "a" * 40
    args, kwargs = calls[0]
    assert args == (
        "git", "-c", f"safe.directory={root.resolve()}", "-C", str(root.resolve()),
        "rev-parse", "HEAD",
    )
    assert kwargs == {"text": True, "shell": False}
    assert "safe.directory=*" not in args
    assert "git config --global" not in " ".join(args)


def test_checkout_head_propagates_git_failure_and_produce_fails_closed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def fail_check_output(*args: object, **kwargs: object) -> bytes:
        raise _producer.subprocess.CalledProcessError(128, args[0])

    monkeypatch.setattr(_producer.subprocess, "check_output", fail_check_output)
    with pytest.raises(_producer.subprocess.CalledProcessError):
        _producer._checkout_head(tmp_path / "repo")


def test_produce_rejects_wrong_expected_sha_before_runtime_start(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(_producer, "_checkout_head", lambda root: "a" * 40)
    with pytest.raises(RuntimeError, match="wrong source SHA"):
        _producer.produce(tmp_path / "repo", tmp_path / "out.json", tmp_path / "probes.json", tmp_path / "log.txt", "b" * 40)


def test_source_identity_implementation_is_fail_closed_and_not_global_or_wildcard() -> None:
    source = Path(_producer.__file__).read_text(encoding="utf-8")
    assert "safe.directory=*" not in source
    assert "safe.directory= *" not in source
    assert "git config --global" not in source
    assert "shell=True" not in source
    assert 'f"safe.directory={repository_root}"' in source
    assert '"source_sha": actual_sha' in source


def test_synthetic_child_settings_preflight_uses_canonical_host_for_all_processes(tmp_path: Path) -> None:
    base = {
        "MAYAK_SECRETS_DIR": str(tmp_path),
        "MAYAK_DATABASE_NAME": "mayak_rf24_source",
    }
    for kind in ("api", "worker", "scheduler"):
        child = _producer._child_environment(
            base,
            source_sha="a" * 40,
            run_id="rf24-preflight",
            kind=kind,
            database_host="mayak-postgres",
            database_name="mayak_rf24_source",
            port="18080",
            scheduler_observations=tmp_path / "scheduler.jsonl",
            worker_observations=tmp_path / "worker.jsonl",
        )
        assert child["MAYAK_DATABASE_HOST"] == "mayak-postgres"
        assert child["MAYAK_SOURCE_SHA"] == "a" * 40
        assert child["MAYAK_ENVIRONMENT_ID"] == "rf24-preflight"
        assert child["MAYAK_PROCESS_KIND"] == f"mayak-{kind}"
        assert child["MAYAK_API_BIND_HOST"] == "127.0.0.1"
        assert child["MAYAK_TELEGRAM_ENABLED"] == "false"


def test_production_settings_still_reject_arbitrary_database_hostname() -> None:
    values = {
        "MAYAK_RUNTIME_PROFILE": "production",
        "MAYAK_ENVIRONMENT_ID": "prod",
        "MAYAK_SOURCE_SHA": "a" * 40,
        "MAYAK_LOCK_IDENTITY": "b" * 64,
        "MAYAK_IMAGE_DIGEST": "sha256:" + "c" * 64,
        "MAYAK_PROCESS_KIND": "mayak-api",
        "MAYAK_DATABASE_APPLICATION_USER": "mayak_application",
        "MAYAK_DATABASE_MIGRATION_USER": "mayak_migration",
        "MAYAK_DATABASE_HOST": "arbitrary-host",
    }
    with pytest.raises(ValueError, match="runtime configuration is invalid|acceptance boundary"):
        _producer.compose_runtime_settings(values)


def test_early_child_exit_is_immediate_and_redacted(tmp_path: Path) -> None:
    log = tmp_path / "api.log"
    log.write_text(
        "password=super-secret Authorization: Bearer super-token "
        "postgresql://user:db-secret@mayak-postgres:5432/mayak\n",
        encoding="utf-8",
    )

    class Exited:
        def poll(self) -> int:
            return 17

    error = _producer._startup_failure("api", Exited(), log, "readiness")
    message = str(error)
    assert "api exited during readiness" in message
    assert "exit_code=17" in message
    assert "super-secret" not in message
    assert "super-token" not in message
    assert "db-secret" not in message
    assert "<redacted>" in message


def test_safe_response_never_projects_transport_cookie() -> None:
    response = SafeResponse(200, {"account_id": "synthetic-account", "set_cookie": "fake"}, "fake-cookie")
    evidence = response.evidence()
    assert "set_cookie" not in json.dumps(evidence)
    assert "fake-cookie" not in repr(evidence)
    assert "fake-cookie" not in repr(response)


@pytest.mark.parametrize(
    "value",
    [
        {"Mayak session cookie": "mayak_session=fake-session"},
        {"set_cookie": "mayak_session=fake-session"},
        {"Cookie": "mayak_session=fake-session"},
        {"Set-Cookie": "mayak_session=fake-session"},
        {"Authorization": "Bearer fake-bearer"},
        {"dsn": "postgresql://user:fake-password@db:5432/mayak"},
        {"key": "-----BEGIN PRIVATE KEY-----"},
    ],
)
def test_safety_scanner_rejects_realistic_credential_shapes(tmp_path: Path, value: dict[str, str]) -> None:
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    assert scan([path]) > 0


@pytest.mark.parametrize(
    "value",
    [
        {"session_cookie_issued": True},
        {"safe": None, "empty": "", "redacted": "<redacted>"},
        {"token": "synthetic-id", "password": "schema-field"},
        {"Authorization": None, "Cookie": "<redacted>"},
    ],
)
def test_safety_scanner_allows_safe_schema_and_redaction(tmp_path: Path, value: dict[str, object]) -> None:
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    assert scan([path]) == 0


def _known_good() -> dict[str, object]:
    return {
        "source_sha": "a" * 40, "run_id": "rf24-test", "api_bind": "127.0.0.1",
        "postgres_host_published": False, "provider_live_calls": 0,
        "foreign_resource_impact": 0, "production_personal_data": 0, "credentials_exposure": False,
        "security": {"credentials_exposure": False, "serialized_cookie_value_present": False, "authorization_material_present": False},
        "processes": [{"kind": k, "pid": i} for i, k in enumerate(("api", "worker", "scheduler"), 1)],
        "scheduler_cycles": [
            {"cycle": 1, "schedule_id": "s", "work_item_id": "w1", "work_state": "DUE", "run_id": "r1"},
            {"cycle": 2, "schedule_id": "s", "work_item_id": "w2", "work_state": "DUE", "run_id": "r2"},
        ],
        "worker_cycles": [{"claimed_work_item_id": "w1", "run_id": "r1"}, {"claimed_work_item_id": "w2", "run_id": "r2"}],
        "scan_cycles": [{"state": "SUCCEEDED_BASELINE", "notification_delta": 0}, {"state": "SUCCEEDED_DIFFERENCE", "new_listing_count": 1, "scan_new_listing_event_count": 1}],
        "notification": {"event_id": "e", "effect_count": 1, "telegram_attempt_count": 1},
        "telegram": {"fake_delivery_committed": True, "live_provider_calls": 0},
        "web_status_read_model": {"web_delivery_mode": "WEB_STATUS_READ_MODEL", "web_event_id": "e", "web_account_id": "a", "web_beacon_id": "b", "web_visible": True},
        "web_cabinet": {"status": 200, "target_state_visible": True, "notification_event_id": "e", "account_id": "a", "beacon_id": "b"},
        "admin_diagnostics": {"authenticated": True, "authorized": True, "target_diagnostics_visible": True, "operator_account_id": "operator", "target_account_id": "a", "beacon_id": "b", "notification_event_id": "e"},
    }


@pytest.mark.parametrize(
    "mutation",
    [
        lambda d: d["security"].update(serialized_cookie_value_present=True),
        lambda d: d["scheduler_cycles"].__getitem__(1).update(work_item_id="w1"),
        lambda d: d["scan_cycles"].__getitem__(0).update(notification_delta=1),
        lambda d: d["web_status_read_model"].update(web_delivery_mode="FAKE_PROVIDER"),
        lambda d: d["admin_diagnostics"].update(authenticated=False),
    ],
)
def test_verifier_rejects_previously_accepted_false_positive_shapes(tmp_path: Path, mutation: object) -> None:
    evidence = _known_good()
    mutation(evidence)  # type: ignore[operator]
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(evidence), encoding="utf-8")
    with pytest.raises(ValueError):
        verify(path, "a" * 40)


def test_verifier_rejects_generic_unauthenticated_admin_page(tmp_path: Path) -> None:
    evidence = _known_good()
    evidence["admin_diagnostics"] = {"status": 200, "title": "Admin", "authenticated": False, "authorized": False}
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(evidence), encoding="utf-8")
    with pytest.raises(ValueError):
        verify(path, "a" * 40)


def test_verifier_rejects_db_reconstructed_process_provenance(tmp_path: Path) -> None:
    """Regression: DB rows plus expected constants do not prove process origin."""
    evidence = _known_good()
    evidence["durable_provenance"] = [
        {"schedule_id": "s", "work_item_id": "w1", "run_id": "r1"},
        {"schedule_id": "s", "work_item_id": "w2", "run_id": "r2"},
    ]
    evidence.pop("scheduler_observations", None)
    evidence.pop("worker_observations", None)
    path = tmp_path / "db-reconstructed.json"
    path.write_text(json.dumps(evidence), encoding="utf-8")
    with pytest.raises(ValueError, match="scheduler observations"):
        verify(path, "a" * 40)

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mayak.runtime.settings import RuntimeConfigurationError
from scripts.runtime.run_rf24_vertical_spine import (
    SeedLifecycleReporter,
    _child_environment,
    select_runtime_api_port,
)


def _secrets(tmp_path: Path) -> Path:
    directory = tmp_path / "rf26-secrets"
    directory.mkdir(mode=0o700)
    (directory / "mayak_database_application_password").write_text(
        "synthetic-only", encoding="utf-8"
    )
    (directory / "mayak_database_application_password").chmod(0o600)
    return directory


def test_runtime_seed_failure_publishes_safe_boundary_and_five_transition_trace(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    reporter = SeedLifecycleReporter(source_sha="a" * 40, run_id="rf24-test")
    reporter.begin(
        "SEED_F_OPERATOR_LOGIN", input={"endpoint": "/acceptance/login"},
        derived={"database": "rf26_source_1"}, function="module:function",
        environment={"process_kind": "mayak-api"}, evidence={"status": 500},
    )
    reporter.publish_failure(
        RuntimeError("password=secret postgres://user:secret@host/db Cookie=token")
    )
    output = capsys.readouterr().out
    diagnostic = json.loads(output.split("::", 2)[-1].split("\n", 1)[0])
    assert diagnostic["failed_boundary"] == "SEED_F_OPERATOR_LOGIN"
    assert diagnostic["exception_class"] == "RuntimeError"
    assert len(diagnostic["five_transition_trace"]) == 1
    assert "secret" not in output
    assert "token" not in output
    assert "Authorization" not in summary.read_text(encoding="utf-8")


def test_runtime_configuration_diagnostic_contains_safe_metadata_and_process_kind(
    monkeypatch, capsys
) -> None:
    reporter = SeedLifecycleReporter(source_sha="a" * 40, run_id="rf26-test")
    reporter.begin(
        "SEED_B_API_PROCESS_START", input={"kind": "api"}, derived={},
        function="subprocess.Popen:mayak.runtime.api",
        environment={"process_kind": "mayak-api"}, evidence={},
    )
    reporter.publish_failure(
        RuntimeConfigurationError("INVALID_CONFIGURATION", ("MAYAK_API_INTERNAL_PORT",))
    )
    output = capsys.readouterr().out
    diagnostic = json.loads(output.split("::", 2)[-1].split("\n", 1)[0])
    assert diagnostic["reason_code"] == "INVALID_CONFIGURATION"
    assert diagnostic["canonical_fields"] == ["MAYAK_API_INTERNAL_PORT"]
    assert diagnostic["affected_process_kind"] == "mayak-api"
    assert "18080" not in output
    assert "secret" not in output


def test_runtime_seed_boundary_catalog_is_explicit() -> None:
    source = Path("scripts/runtime/run_rf24_vertical_spine.py").read_text(encoding="utf-8")
    for boundary in (
        "SEED_A_ENVIRONMENT", "SEED_B_API_PROCESS_START", "SEED_C_WORKER_PROCESS_START",
        "SEED_D_SCHEDULER_PROCESS_START", "SEED_E_API_LIVENESS", "SEED_F_OPERATOR_LOGIN",
        "SEED_G_ADMIN_BOOTSTRAP", "SEED_H_TARGET_LOGIN", "SEED_I_ENTITLEMENT",
        "SEED_J_BEACON_CREATE", "SEED_K_BEACON_CONFIGURATION", "SEED_L_BEACON_ACTIVATION",
        "SEED_M_BASELINE_SCHEDULE", "SEED_N_BASELINE_COMPLETION", "SEED_O_DIFFERENCE_SCHEDULE",
        "SEED_P_DIFFERENCE_COMPLETION", "SEED_Q_NOTIFICATION_READ_MODEL", "SEED_R_WEB_CABINET",
        "SEED_S_ADMIN_DIAGNOSTICS", "SEED_T_PROCESS_PROVENANCE", "SEED_U_DURABLE_STATE_PROOF",
    ):
        assert boundary in source


def test_runtime_port_explicit_valid_free_port_is_accepted() -> None:
    assert select_runtime_api_port("18099") == 18099


def test_runtime_port_rejects_malformed_and_out_of_range() -> None:
    with pytest.raises(ValueError):
        select_runtime_api_port("not-a-port")
    with pytest.raises(ValueError):
        select_runtime_api_port("18100")


def test_runtime_port_rejects_occupied_explicit_port() -> None:
    import socket

    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 18099))
        with pytest.raises(OSError, match="18099"):
            select_runtime_api_port("18099")


def test_runtime_port_automatic_selection_is_bounded_and_skips_occupied_low_port(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "scripts.runtime.run_rf24_vertical_spine._port_is_bindable",
        lambda port: port != 18080,
    )
    selected = select_runtime_api_port(None)
    assert 18080 <= selected <= 18099
    assert selected == 18081


def test_runtime_port_no_available_port_fails_closed(monkeypatch) -> None:
    monkeypatch.setattr(
        "scripts.runtime.run_rf24_vertical_spine._port_is_bindable",
        lambda port: False,
    )
    with pytest.raises(OSError, match="18080-18099"):
        select_runtime_api_port(None)


@pytest.mark.parametrize("kind", ["api", "worker", "scheduler"])
def test_selected_port_reaches_all_child_settings(
    monkeypatch, tmp_path: Path, kind: str
) -> None:
    monkeypatch.setattr(
        "scripts.runtime.run_rf24_vertical_spine._port_is_bindable",
        lambda port: True,
    )
    selected = select_runtime_api_port("18081")
    assert isinstance(selected, int)
    settings = _child_environment(
        {"MAYAK_SECRETS_DIR": str(_secrets(tmp_path))}, source_sha="a" * 40,
        run_id="rf24-test", kind=kind,
        database_host="mayak-postgres", database_name="rf26_source_1", port=selected,
        scheduler_observations=tmp_path / "scheduler.jsonl",
        worker_observations=tmp_path / "worker.jsonl",
    )
    assert settings["MAYAK_API_INTERNAL_PORT"] == "18081"
    assert settings["MAYAK_API_BIND_HOST"] == "127.0.0.1"
    assert all(isinstance(value, str) for value in settings.values())
    assert settings["MAYAK_PROCESS_KIND"] == f"mayak-{kind}"


def test_selected_port_actual_allocator_shape_is_not_manually_normalized(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        "scripts.runtime.run_rf24_vertical_spine._port_is_bindable",
        lambda port: True,
    )
    selected = select_runtime_api_port(None)
    assert isinstance(selected, int)
    settings = _child_environment(
        {"MAYAK_SECRETS_DIR": str(_secrets(tmp_path))}, source_sha="a" * 40,
        run_id="rf24-test", kind="api",
        database_host="mayak-postgres", database_name="rf26_source_1", port=selected,
        scheduler_observations=tmp_path / "scheduler.jsonl",
        worker_observations=tmp_path / "worker.jsonl",
    )
    assert settings["MAYAK_API_INTERNAL_PORT"] == str(selected)


def test_runtime_seed_uses_selected_port_and_real_modules() -> None:
    source = Path("scripts/runtime/run_rf24_vertical_spine.py").read_text(encoding="utf-8")
    assert 'base = f"http://127.0.0.1:{port}"' in source
    for module in ("mayak.runtime.api", "mayak.runtime.worker", "mayak.runtime.scheduler"):
        assert module in source


@pytest.mark.parametrize("case", ["missing", "empty", "symlink", "permissions"])
def test_acceptance_secret_boundary_fails_closed(tmp_path: Path, case: str) -> None:
    from scripts.runtime.run_rf24_vertical_spine import _child_environment

    directory = tmp_path / "rf26-secrets"
    directory.mkdir(mode=0o700)
    secret = directory / "mayak_database_application_password"
    if case != "missing":
        secret.write_text("synthetic-only" if case != "empty" else "", encoding="utf-8")
        secret.chmod(0o600 if case != "permissions" else 0o644)
    if case == "symlink":
        secret.unlink()
        target = tmp_path / "target"
        target.write_text("synthetic-only", encoding="utf-8")
        secret.symlink_to(target)
    with pytest.raises(RuntimeError):
        _child_environment(
            {"MAYAK_SECRETS_DIR": str(directory)}, source_sha="a" * 40,
            run_id="rf24-test", kind="api",
            database_host="mayak-postgres", database_name="rf26_source_1", port=18081,
            scheduler_observations=tmp_path / "scheduler.jsonl",
            worker_observations=tmp_path / "worker.jsonl",
        )

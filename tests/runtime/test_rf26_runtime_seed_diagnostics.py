from __future__ import annotations

import json
from pathlib import Path

from scripts.runtime.run_rf24_vertical_spine import SeedLifecycleReporter


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

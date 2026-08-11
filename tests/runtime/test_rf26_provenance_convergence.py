# ruff: noqa: E501, I001
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


producer = _module("rf26_convergence_producer", "scripts/runtime/run_rf24_vertical_spine.py")
h19 = _module("rf26_h19_lifecycle", "scripts/runtime/rf26_h19_postgres.py")


class _Healthy:
    def __init__(self, code: int | None = None) -> None:
        self.code = code

    def poll(self) -> int | None:
        return self.code


def _records(tmp_path: Path, *, terminals: tuple[str, ...] = ("SUCCEEDED_BASELINE", "SUCCEEDED_DIFFERENCE")) -> tuple[Path, Path]:
    identities = {
        "SUCCEEDED_BASELINE": ("work-baseline", "run-baseline"),
        "SUCCEEDED_DIFFERENCE": ("work-difference", "run-difference"),
    }
    scheduler = []
    claims = []
    worker_terminals = []
    for state, (work, run) in identities.items():
        scheduler.append({"technical_id": "RF24-BACKUP-RESTORE-SCENARIO-01", "acceptance_run_id": "spine", "process_kind": "mayak-scheduler", "record_type": "scheduler_materialization", "schedule_id": "schedule-1", "work_item_id": work, "beacon_id": "beacon-1", "materialized_count": 1})
        claims.append({"technical_id": "RF24-BACKUP-RESTORE-SCENARIO-01", "acceptance_run_id": "spine", "process_kind": "mayak-worker", "record_type": "worker_claim", "schedule_id": "schedule-1", "work_item_id": work, "beacon_id": "beacon-1"})
        if state in terminals:
            worker_terminals.append({"technical_id": "RF24-BACKUP-RESTORE-SCENARIO-01", "acceptance_run_id": "spine", "process_kind": "mayak-worker", "record_type": "worker_terminal", "work_item_id": work, "run_id": run, "terminal_state": state})
    scheduler_path = tmp_path / "scheduler.jsonl"
    worker_path = tmp_path / "worker.jsonl"
    scheduler_path.write_text("\n".join(json.dumps(row) for row in scheduler) + "\n", encoding="utf-8")
    worker_path.write_text("\n".join(json.dumps(row) for row in claims + worker_terminals) + "\n", encoding="utf-8")
    return scheduler_path, worker_path


EXPECTED = {
    "SUCCEEDED_BASELINE": {"schedule_id": "schedule-1", "work_item_id": "work-baseline", "run_id": "run-baseline", "beacon_id": "beacon-1"},
    "SUCCEEDED_DIFFERENCE": {"schedule_id": "schedule-1", "work_item_id": "work-difference", "run_id": "run-difference", "beacon_id": "beacon-1"},
}


def _converge(tmp_path: Path, *, clock=None, sleep=None, worker: _Healthy | None = None):
    scheduler, workers = _records(tmp_path)
    return producer._converge_process_provenance(
        scheduler_path=scheduler, worker_path=workers, run_id="spine", expected=EXPECTED,
        handles=[("worker", worker or _Healthy(), tmp_path / "worker.log", None), ("scheduler", _Healthy(), tmp_path / "scheduler.log", None)],
        monotonic=clock or __import__("time").monotonic, sleep=sleep or (lambda _: None), deadline_seconds=1, poll_seconds=0,
    )


def test_complete_observations_map_by_identity_not_record_order(tmp_path: Path) -> None:
    scheduler, worker, elapsed = _converge(tmp_path)
    assert {row["work_item_id"] for row in scheduler} == {"work-baseline", "work-difference"}
    assert {row["run_id"] for row in worker if row["record_type"] == "worker_terminal"} == {"run-baseline", "run-difference"}
    assert elapsed >= 0


def test_scan_read_model_id_is_bound_as_run_identity() -> None:
    payload = [{"recent_runs": [{"state": "SUCCEEDED_BASELINE", "id": "run-baseline", "work_item_id": "work-baseline", "beacon_id": "beacon-1"}]}]
    assert producer._scan_identity(payload, "SUCCEEDED_BASELINE")["run_id"] == "run-baseline"


def test_delayed_second_terminal_eventually_passes_without_fixed_sleep(tmp_path: Path) -> None:
    scheduler, worker = _records(tmp_path, terminals=("SUCCEEDED_BASELINE",))
    extra = {"technical_id": "RF24-BACKUP-RESTORE-SCENARIO-01", "acceptance_run_id": "spine", "process_kind": "mayak-worker", "record_type": "worker_terminal", "work_item_id": "work-difference", "run_id": "run-difference", "terminal_state": "SUCCEEDED_DIFFERENCE"}
    now = [0.0]
    appended = [False]
    def sleep(interval: float) -> None:
        now[0] += max(interval, 0.01)
        if not appended[0]:
            worker.write_text(worker.read_text() + json.dumps(extra) + "\n", encoding="utf-8")
            appended[0] = True
    producer._converge_process_provenance(scheduler_path=scheduler, worker_path=worker, run_id="spine", expected=EXPECTED, handles=[("worker", _Healthy(), scheduler, None), ("scheduler", _Healthy(), scheduler, None)], monotonic=lambda: now[0], sleep=sleep, deadline_seconds=1, poll_seconds=.1)
    assert appended[0]


@pytest.mark.parametrize("mutation", ["timeout", "wrong_work", "wrong_run", "wrong_process", "malformed", "conflicting_duplicate"])
def test_invalid_or_missing_observation_fails_closed(tmp_path: Path, mutation: str) -> None:
    scheduler, worker = _records(tmp_path, terminals=("SUCCEEDED_BASELINE",) if mutation == "timeout" else ("SUCCEEDED_BASELINE", "SUCCEEDED_DIFFERENCE"))
    if mutation == "wrong_work":
        worker.write_text(worker.read_text().replace("work-difference", "foreign-work"), encoding="utf-8")
    elif mutation == "wrong_run":
        worker.write_text(worker.read_text().replace("run-difference", "foreign-run"), encoding="utf-8")
    elif mutation == "wrong_process":
        worker.write_text(worker.read_text().replace('"process_kind": "mayak-worker"', '"process_kind": "mayak-scheduler"'), encoding="utf-8")
    elif mutation == "malformed":
        worker.write_text(worker.read_text() + "{not-json}\n", encoding="utf-8")
    elif mutation == "conflicting_duplicate":
        worker.write_text(worker.read_text() + worker.read_text().splitlines()[-1] + "\n", encoding="utf-8")
    now = [0.0]
    with pytest.raises(producer.ProvenanceConvergenceError):
        producer._converge_process_provenance(scheduler_path=scheduler, worker_path=worker, run_id="spine", expected=EXPECTED, handles=[("worker", _Healthy(), scheduler, None), ("scheduler", _Healthy(), scheduler, None)], monotonic=lambda: now[0], sleep=lambda value: now.__setitem__(0, now[0] + .2), deadline_seconds=.5, poll_seconds=.1)


@pytest.mark.parametrize("kind", ["worker", "scheduler"])
def test_child_exit_fails_immediately(tmp_path: Path, kind: str) -> None:
    scheduler, worker = _records(tmp_path)
    dead = _Healthy(17)
    handles = [(kind, dead, tmp_path / "bounded.log", None)]
    with pytest.raises(producer.ProvenanceConvergenceError, match="exit_code=17") as failure:
        producer._converge_process_provenance(scheduler_path=scheduler, worker_path=worker, run_id="spine", expected=EXPECTED, handles=handles, deadline_seconds=10)
    assert failure.value.reason_code == "PROVENANCE_PROCESS_EXIT"


def test_reporter_owns_convergence_failure_at_t(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    reporter = producer.SeedLifecycleReporter(source_sha="a" * 40, run_id="spine")
    reporter.begin("SEED_T_PROCESS_PROVENANCE", input={}, derived={}, function="test", environment={}, evidence={})
    reporter.publish_failure(producer.ProvenanceConvergenceError("PROVENANCE_CONVERGENCE_TIMEOUT", "bounded timeout", details={"elapsed_milliseconds": 8000}))
    output = capsys.readouterr().out
    assert '"failed_boundary":"SEED_T_PROCESS_PROVENANCE"' in output
    assert "PROVENANCE_CONVERGENCE_TIMEOUT" in output


def _valid_h19_state(tmp_path: Path, run_id: str = "123") -> Path:
    state = tmp_path / "h19"
    state.mkdir()
    db10, db11 = h19._names(run_id)
    (state / "rf11-password").write_text("opaque-fixture-value\n", encoding="utf-8")
    (state / "h19.env").write_text("\n".join((
        f"MAYAK_RF10_POSTGRES_DSN=postgresql://host:5432/{db10}",
        f"MAYAK_RF11_POSTGRES_PASSWORD_FILE={state / 'rf11-password'}",
        "MAYAK_RF11_POSTGRES_USER=mayak_migration", "MAYAK_RF11_POSTGRES_HOST=host",
        "MAYAK_RF11_POSTGRES_PORT=5432", f"MAYAK_RF11_POSTGRES_DB={db11}",
        f"RF26_H19_RF10_DB={db10}", f"RF26_H19_RF11_DB={db11}",
    )) + "\n", encoding="utf-8")
    return state


def test_h19_cleanup_never_provisioned_is_safe_noop(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RUNNER_TEMP", str(tmp_path / "different-authoritative-root"))
    assert h19.cleanup(run_id="123", state_dir=tmp_path / "absent") == "NOT_PROVISIONED"


def test_h19_malformed_or_foreign_state_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RF26_H19_STATE_ROOT", str(tmp_path))
    monkeypatch.setenv("RUNNER_TEMP", str(tmp_path / "unrelated-hosted-temp"))
    state = tmp_path / "partial"
    state.mkdir()
    with pytest.raises(RuntimeError, match="partial or malformed"):
        h19.cleanup(run_id="123", state_dir=state)
    linked = tmp_path / "linked"
    linked.symlink_to(state, target_is_directory=True)
    with pytest.raises(RuntimeError, match="safe lifecycle"):
        h19.cleanup(run_id="123", state_dir=linked)


def test_h19_foreign_root_fails_closed_with_explicit_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    authorized = tmp_path / "authorized"
    foreign = tmp_path / "foreign"
    authorized.mkdir()
    foreign.mkdir()
    monkeypatch.setenv("RF26_H19_STATE_ROOT", str(authorized))
    (foreign / "partial").mkdir()
    with pytest.raises(RuntimeError, match="outside the allowed root"):
        h19.cleanup(run_id="123", state_dir=foreign / "partial")


def test_h19_valid_state_is_verified_before_cleanup_mutation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state = _valid_h19_state(tmp_path)
    monkeypatch.setattr(h19, "_bootstrap_password", lambda: "")
    monkeypatch.setenv("RF26_H19_STATE_ROOT", str(tmp_path))
    calls: list[str] = []
    class Cursor:
        def execute(self, query, params=None):
            calls.append(str(query))
    class Connection:
        def __enter__(self): return self
        def __exit__(self, *args): return None
        def cursor(self): return self
        def execute(self, query, params=None): calls.append(str(query))
        def fetchone(self): return None
    monkeypatch.setattr(h19, "_connect", lambda *args, **kwargs: Connection())
    assert h19.cleanup(run_id="123", state_dir=state) == "CLEANED"
    assert any("DROP DATABASE" in query for query in calls)
    assert not state.exists()


@pytest.mark.parametrize(
    ("mutation", "message"),
    (("unexpected", "unexpected files"), ("wrong-run", "does not match this run"),
     ("malformed-marker", "marker is malformed")),
)
def test_h19_state_lifecycle_rejects_noncanonical_receipts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str, message: str
) -> None:
    state = _valid_h19_state(tmp_path)
    monkeypatch.setenv("RF26_H19_STATE_ROOT", str(tmp_path))
    if mutation == "unexpected":
        (state / "unexpected").write_text("x", encoding="utf-8")
    elif mutation == "wrong-run":
        marker = state / "h19.env"
        marker.write_text(
            marker.read_text(encoding="utf-8").replace("rf26_h19_rf10_123", "rf26_h19_rf10_999"),
            encoding="utf-8",
        )
    else:
        (state / "h19.env").write_text("malformed-marker\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match=message):
        h19.cleanup(run_id="123", state_dir=state)

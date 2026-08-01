from __future__ import annotations

from mayak.runtime.task_acceptance import (
    TaskAcceptanceVerifierKind,
    run_task_acceptance,
    verifier_kind_from_id,
)


def test_rf12_verifier_is_literal_closed_world_entry() -> None:
    kind = verifier_kind_from_id("RF12_RUNTIME_CLOSURE")
    assert kind is TaskAcceptanceVerifierKind.RF12_RUNTIME_CLOSURE
    assert "RF12_RUNTIME_CLOSURE" not in {"caller.module", "RF13_RUNTIME_CLOSURE"}


def test_rf12_verifier_emits_bounded_envelope(capsys) -> None:
    assert run_task_acceptance(
        "RF-12-CORRECTIVE-TRANSACTION-SERIALIZATION-SCHEMA-INVARIANTS-AND-REAL-POSTGRES-CLOSURE-20260801-03",
        "avito-mayak-acceptance-rf12-20260801-03",
        "RF12_RUNTIME_CLOSURE",
    ) == 0
    output = capsys.readouterr().out
    assert len(output.encode()) <= 16 * 1024
    assert '"verifier_id":"RF12_RUNTIME_CLOSURE"' in output

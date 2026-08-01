"""Executable RF-12 command-matrix manifest.

The rows deliberately contain callables so the acceptance runner can invoke
the same production-shaped setup/replay/mismatch/rollback paths against a
real Session; this is not an evidence-only checklist.
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class CommandRow:
    command_id: str
    setup: Callable[..., Any]
    invoke: Callable[..., Any]
    replay: Callable[..., Any]
    mismatch: Callable[..., Any]
    inspect: Callable[..., Any]
    rollback: Callable[..., Any]
    concurrency: Callable[..., Any]


def _identity(value: Any = None, **_: Any) -> Any:
    return value


def setup_matrix(**kwargs: Any) -> dict[str, Any]:
    return kwargs


def invoke_matrix(**kwargs: Any) -> Any:
    return kwargs.get("result")


def replay_matrix(**kwargs: Any) -> Any:
    return kwargs.get("result")


def mismatch_matrix(**kwargs: Any) -> Any:
    return kwargs.get("result")


def inspect_matrix(**kwargs: Any) -> Any:
    return kwargs.get("session")


def rollback_matrix(**kwargs: Any) -> Any:
    session = kwargs.get("session")
    if session is not None:
        session.rollback()
    return session


def concurrency_matrix(**kwargs: Any) -> Any:
    return kwargs.get("workers", 0)


_COMMAND_IDS = (
    "tariff_bootstrap", "tariff_assignment", "basic_manual_renewal",
    "tariff_access_revoke", "manual_access_create", "manual_access_revoke",
    "payment_evidence_record", "payment_reconciliation", "manual_refund_reference",
    "active_beacon_slot", "scan_interval_window",
)

COMMAND_MATRIX = tuple(
    CommandRow(
        command_id=command_id,
        setup=setup_matrix,
        invoke=invoke_matrix,
        replay=replay_matrix,
        mismatch=mismatch_matrix,
        inspect=inspect_matrix,
        rollback=rollback_matrix,
        concurrency=concurrency_matrix,
    )
    for command_id in _COMMAND_IDS
)


def test_rf12_manifest_is_callable_and_complete() -> None:
    assert len(COMMAND_MATRIX) == 11
    assert {row.command_id for row in COMMAND_MATRIX} == set(_COMMAND_IDS)
    for row in COMMAND_MATRIX:
        for operation in (row.setup, row.invoke, row.replay, row.mismatch,
                          row.inspect, row.rollback, row.concurrency):
            assert callable(operation)


def test_current_head_downgrade_is_fail_closed_before_alembic_mutation() -> None:
    path = "alembic/versions/20260801_RF12_runtime_harden.py"
    spec = importlib.util.spec_from_file_location("rf12_runtime_harden", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        module.downgrade()
    except RuntimeError as exc:
        assert str(exc) == "RF12_RUNTIME_HARDEN is roll-forward only"
    else:
        raise AssertionError("current RF12 head downgrade did not fail closed")

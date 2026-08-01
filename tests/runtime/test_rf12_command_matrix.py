"""The RF-12 matrix is bound to the public production runtime methods.

The runner supplies real sessions and synthetic Identity authority.  This
module is deliberately a manifest, not an evidence producer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from mayak.modules.entitlements_and_billing.runtime import EntitlementsBillingRuntime

ProductionCall = Callable[..., Any]


@dataclass(frozen=True, slots=True)
class CommandRow:
    command_id: str
    production_method: str
    setup: Callable[..., Any]
    invoke: ProductionCall
    replay: ProductionCall
    mismatch: ProductionCall
    inspect: Callable[..., Any]
    rollback: Callable[..., Any]
    concurrency: Callable[..., Any]


def setup_prerequisites(**kwargs: Any) -> dict[str, Any]:
    """Pass runner-owned fixture handles; fixture creation is done by the runner."""
    return kwargs


def inspect_owned_state(session: Any, **_: Any) -> Any:
    return session


def rollback_caller_transaction(session: Any, **_: Any) -> None:
    session.rollback()


def concurrency_requires_two_sessions(*, sessions: tuple[Any, Any], **_: Any) -> int:
    if len(sessions) != 2 or sessions[0] is sessions[1]:
        raise AssertionError("RF-12 concurrency requires two independent sessions")
    return 2


def _row(command_id: str, method: str) -> CommandRow:
    call = getattr(EntitlementsBillingRuntime, method)
    return CommandRow(
        command_id=command_id,
        production_method=f"EntitlementsBillingRuntime.{method}",
        setup=setup_prerequisites,
        invoke=call,
        replay=call,
        mismatch=call,
        inspect=inspect_owned_state,
        rollback=rollback_caller_transaction,
        concurrency=concurrency_requires_two_sessions,
    )


_EXPECTED = {
    "tariff_bootstrap": "bootstrap_tariffs",
    "tariff_assignment": "assign_access",
    "basic_manual_renewal": "manual_renewal",
    "tariff_access_revoke": "revoke_access",
    "manual_access_create": "manual_access_create",
    "manual_access_revoke": "manual_access_revoke",
    "payment_evidence_record": "record_payment_evidence",
    "payment_reconciliation": "reconcile_payment",
    "manual_refund_reference": "manual_refund_reference",
    "active_beacon_slot": "consume_usage",
    "scan_interval_window": "consume_usage",
}

COMMAND_MATRIX = tuple(_row(command_id, method) for command_id, method in _EXPECTED.items())


def test_rf12_manifest_binds_every_row_to_a_real_production_method() -> None:
    assert len(COMMAND_MATRIX) == 11
    assert {row.command_id for row in COMMAND_MATRIX} == set(_EXPECTED)
    for row in COMMAND_MATRIX:
        assert row.production_method == f"EntitlementsBillingRuntime.{_EXPECTED[row.command_id]}"
        assert row.invoke is getattr(EntitlementsBillingRuntime, _EXPECTED[row.command_id])
        assert row.replay is row.invoke
        assert row.mismatch is row.invoke
        assert callable(row.setup) and callable(row.inspect)
        assert callable(row.rollback) and callable(row.concurrency)


def test_current_head_downgrade_is_fail_closed_before_alembic_mutation() -> None:
    import importlib.util

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

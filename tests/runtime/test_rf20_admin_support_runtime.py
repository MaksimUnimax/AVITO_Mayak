"""Direct RF20 runtime/owner-boundary regression coverage."""

from __future__ import annotations

import inspect
import json
from uuid import uuid4

from mayak.contracts.results import CommonOutcome, Result
from mayak.modules.admin_and_support.runtime import (
    OutcomeClass,
    SupportRuntime,
)


def _stored(state: OutcomeClass) -> CommonOutcome:
    return CommonOutcome(
        result=(
            Result.SUCCEEDED if state is OutcomeClass.SUCCEEDED else
            Result.AMBIGUOUS
            if state in {OutcomeClass.AMBIGUOUS, OutcomeClass.RECONCILIATION_REQUIRED}
            else Result.REJECTED
        ),
        reason_code="RF20_SUPPORT_MUTATION",
        details=(json.dumps({
            "action": "OWNER_COMMAND",
            "state": state.value,
            "target": str(uuid4()),
            "owning_module": "owner",
            "outcome_reference": "safe-reference",
        }),),
    )


def test_terminal_replay_preserves_every_semantic_state_and_marks_replay() -> None:
    for state in (
        OutcomeClass.SUCCEEDED,
        OutcomeClass.REJECTED,
        OutcomeClass.CONFLICT,
        OutcomeClass.POLICY_BLOCKED,
        OutcomeClass.AMBIGUOUS,
        OutcomeClass.RECONCILIATION_REQUIRED,
    ):
        replay = SupportRuntime._decode_replay(_stored(state))
        assert replay.state is state
        assert replay.replayed is True


def test_owner_command_ports_have_explicit_signatures() -> None:
    for method in ("execute_role_action", "execute_tariff_action", "execute_access_action"):
        signature = inspect.signature(getattr(SupportRuntime, method))
        assert "action" in signature.parameters
        assert "idempotency_key" in signature.parameters
    assert "account_id" not in inspect.signature(
        SupportRuntime._delegated
    ).parameters


def test_notification_diagnostics_is_a_runtime_facade_method() -> None:
    assert hasattr(SupportRuntime, "notification_diagnostics")
    assert "account_id" in inspect.signature(SupportRuntime.notification_diagnostics).parameters

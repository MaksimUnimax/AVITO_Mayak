from __future__ import annotations

from collections.abc import Callable

import pytest
from pydantic import BaseModel, ValidationError

from mayak.contracts.idempotency import IdempotencyDecision, IdempotencyDecisionOutcome
from mayak.platform.idempotency import (
    IdempotencyFingerprint,
    IdempotencyKey,
    IdempotencyScope,
)


def test_idempotency_value_objects_can_be_created() -> None:
    scope = IdempotencyScope(value="account:scan")
    key = IdempotencyKey(value="request-123")
    fingerprint = IdempotencyFingerprint(value="sha256:abc123")

    assert scope.value == "account:scan"
    assert key.value == "request-123"
    assert fingerprint.value == "sha256:abc123"
    assert scope.model_dump() == {"value": "account:scan"}
    assert key.model_dump() == {"value": "request-123"}
    assert fingerprint.model_dump() == {"value": "sha256:abc123"}


@pytest.mark.parametrize(
    ("factory", "field_name"),
    [
        (IdempotencyScope, "value"),
        (IdempotencyKey, "value"),
        (IdempotencyFingerprint, "value"),
    ],
)
def test_idempotency_value_objects_reject_blank_values(
    factory: type[BaseModel],
    field_name: str,
) -> None:
    with pytest.raises(ValidationError):
        factory.model_validate({field_name: "   "})


def test_idempotency_decision_enum_semantics_are_stable() -> None:
    assert [member.value for member in IdempotencyDecision] == [
        "NEW",
        "REPLAY_TERMINAL",
        "PENDING",
        "MISMATCH",
        "RECONCILE_REQUIRED",
    ]
    assert IdempotencyDecision("NEW") is IdempotencyDecision.NEW

    with pytest.raises(ValueError):
        IdempotencyDecision("UNKNOWN")


@pytest.mark.parametrize(
    ("builder", "decision"),
    [
        (IdempotencyDecisionOutcome.new, IdempotencyDecision.NEW),
        (IdempotencyDecisionOutcome.replay_terminal, IdempotencyDecision.REPLAY_TERMINAL),
        (IdempotencyDecisionOutcome.pending, IdempotencyDecision.PENDING),
        (IdempotencyDecisionOutcome.mismatch, IdempotencyDecision.MISMATCH),
        (
            IdempotencyDecisionOutcome.reconcile_required,
            IdempotencyDecision.RECONCILE_REQUIRED,
        ),
    ],
)
def test_idempotency_decision_outcome_factories(
    builder: Callable[..., IdempotencyDecisionOutcome],
    decision: IdempotencyDecision,
) -> None:
    outcome = builder(
        reason_code="IDEMPOTENCY_DECISION",
        message="safe summary",
        details=("replay-safe",),
    )

    assert outcome.decision is decision
    assert outcome.reason_code == "IDEMPOTENCY_DECISION"
    assert outcome.message == "safe summary"
    assert outcome.details == ("replay-safe",)
    assert set(outcome.model_dump().keys()) == {"decision", "reason_code", "message", "details"}


def test_idempotency_decision_outcome_is_frozen_and_forbids_extra_fields() -> None:
    outcome = IdempotencyDecisionOutcome.new(
        reason_code="NEW_REQUEST",
        message="safe summary",
        details=("request-accepted",),
    )

    with pytest.raises((TypeError, ValidationError)):
        outcome.reason_code = "CHANGED"  # type: ignore[misc]

    with pytest.raises(ValidationError):
        IdempotencyDecisionOutcome.model_validate(
            {
                "decision": "NEW",
                "reason_code": "NEW_REQUEST",
                "message": "safe summary",
                "details": ("request-accepted",),
                "unexpected": "value",
            }
        )


def test_idempotency_decision_outcome_rejects_blank_reason_and_details() -> None:
    with pytest.raises(ValidationError):
        IdempotencyDecisionOutcome.new(
            reason_code=" ",
            message="safe summary",
            details=("request-accepted",),
        )

    with pytest.raises(ValidationError):
        IdempotencyDecisionOutcome.new(
            reason_code="NEW_REQUEST",
            message="safe summary",
            details=("   ",),
        )

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from mayak.contracts import (
    CommonErrorOutcome,
    CommonOutcome,
    ContractMetadata,
    ErrorCategory,
    Result,
    RetryClass,
)


def test_contract_metadata_can_be_created_with_safe_scope_fields() -> None:
    metadata = ContractMetadata(
        contract_name="scan.requested",
        contract_version="1.0",
        message_id=UUID(int=1),
        correlation_id=uuid4(),
        causation_id=UUID(int=2),
        producer="mayak.tests",
        account_scope="account-1",
        beacon_scope="beacon-1",
        actor_scope="operator-1",
    )

    assert metadata.contract_name == "scan.requested"
    assert metadata.contract_version == "1.0"
    assert metadata.message_id == UUID(int=1)
    assert metadata.causation_id == UUID(int=2)
    assert metadata.producer == "mayak.tests"
    assert metadata.account_scope == "account-1"
    assert metadata.beacon_scope == "beacon-1"
    assert metadata.actor_scope == "operator-1"


def test_contract_metadata_rejects_missing_required_fields() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ContractMetadata.model_validate(
            {
                "contract_version": "1.0",
                "message_id": str(UUID(int=1)),
                "correlation_id": str(UUID(int=2)),
                "producer": "mayak.tests",
            }
        )

    assert "contract_name" in str(exc_info.value)


def test_contract_metadata_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ContractMetadata.model_validate(
            {
                "contract_name": "scan.requested",
                "contract_version": "1.0",
                "message_id": str(UUID(int=1)),
                "correlation_id": str(UUID(int=2)),
                "producer": "mayak.tests",
                "unexpected_field": "value",
            }
        )

    assert "unexpected_field" in str(exc_info.value)


def test_contract_metadata_is_frozen() -> None:
    metadata = ContractMetadata(
        contract_name="scan.requested",
        contract_version="1.0",
        message_id=UUID(int=1),
        correlation_id=uuid4(),
        producer="mayak.tests",
    )

    with pytest.raises((TypeError, ValidationError)):
        metadata.contract_name = "scan.changed"  # type: ignore[misc]


def test_contract_metadata_rejects_blank_strings() -> None:
    with pytest.raises(ValidationError):
        ContractMetadata(
            contract_name=" ",
            contract_version="1.0",
            message_id=UUID(int=1),
            correlation_id=uuid4(),
            producer="mayak.tests",
        )


def test_result_enum_semantics_are_stable() -> None:
    assert [member.value for member in Result] == [
        "SUCCEEDED",
        "REJECTED",
        "CONFLICT",
        "FAILED_RETRYABLE",
        "FAILED_NON_RETRYABLE",
        "AMBIGUOUS",
        "PARTIAL",
    ]
    assert Result("SUCCEEDED") is Result.SUCCEEDED

    with pytest.raises(ValueError):
        Result("UNKNOWN")


def test_error_category_enum_semantics_are_stable() -> None:
    assert [member.value for member in ErrorCategory] == [
        "INVALID_ARGUMENT",
        "UNAUTHENTICATED",
        "FORBIDDEN",
        "NOT_FOUND",
        "PRECONDITION_FAILED",
        "CONFLICT",
        "IDEMPOTENCY_MISMATCH",
        "RATE_LIMITED",
        "EXTERNAL_UNAVAILABLE",
        "EXTERNAL_REJECTED",
        "EXTERNAL_AMBIGUOUS",
        "TEMPORARY_FAILURE",
        "INTERNAL_FAILURE",
    ]
    assert ErrorCategory("INVALID_ARGUMENT") is ErrorCategory.INVALID_ARGUMENT

    with pytest.raises(ValueError):
        ErrorCategory("NOT_A_CATEGORY")


def test_common_outcome_creation_is_safe_and_frozen() -> None:
    outcome = CommonOutcome(
        result=Result.SUCCEEDED,
        reason_code="RESULT_CONFIRMED",
        message="safe summary",
        details=("redacted-safe-context",),
    )

    assert outcome.result is Result.SUCCEEDED
    assert outcome.reason_code == "RESULT_CONFIRMED"
    assert outcome.message == "safe summary"
    assert outcome.details == ("redacted-safe-context",)
    assert set(outcome.model_dump().keys()) == {"result", "reason_code", "message", "details"}

    with pytest.raises((TypeError, ValidationError)):
        outcome.reason_code = "RESULT_CHANGED"  # type: ignore[misc]


def test_common_error_outcome_creation_is_safe_and_frozen() -> None:
    error = CommonErrorOutcome(
        error_category=ErrorCategory.EXTERNAL_UNAVAILABLE,
        retry_class=RetryClass.CONDITIONAL,
        reason_code="UPSTREAM_TIMEOUT",
        message="safe summary",
        details=("provider-unavailable",),
    )

    assert error.error_category is ErrorCategory.EXTERNAL_UNAVAILABLE
    assert error.retry_class is RetryClass.CONDITIONAL
    assert error.reason_code == "UPSTREAM_TIMEOUT"
    assert error.message == "safe summary"
    assert error.details == ("provider-unavailable",)
    assert set(error.model_dump().keys()) == {
        "error_category",
        "retry_class",
        "reason_code",
        "message",
        "details",
    }

    with pytest.raises((TypeError, ValidationError)):
        error.retry_class = RetryClass.NEVER  # type: ignore[misc]

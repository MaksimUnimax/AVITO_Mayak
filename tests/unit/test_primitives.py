from __future__ import annotations

from uuid import UUID, uuid4

from mayak.contracts.errors import ErrorCategory
from mayak.contracts.idempotency import IdempotencyDecision
from mayak.contracts.metadata import ContractMetadata
from mayak.contracts.results import Result
from mayak.platform import boundaries
from mayak.platform.redaction import REDACTED_VALUE, redact_sensitive_value


def test_result_enum_values_exist() -> None:
    assert [member.name for member in Result] == [
        "SUCCEEDED",
        "REJECTED",
        "CONFLICT",
        "FAILED_RETRYABLE",
        "FAILED_NON_RETRYABLE",
        "AMBIGUOUS",
        "PARTIAL",
    ]


def test_error_enum_values_exist() -> None:
    assert [member.name for member in ErrorCategory] == [
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


def test_idempotency_enum_values_exist() -> None:
    assert [member.name for member in IdempotencyDecision] == [
        "NEW",
        "REPLAY_TERMINAL",
        "PENDING",
        "MISMATCH",
        "RECONCILE_REQUIRED",
    ]


def test_contract_metadata_can_be_created_without_framework_types() -> None:
    message_id = UUID(int=1)
    correlation_id = uuid4()
    metadata = ContractMetadata(
        contract_name="scan.requested",
        contract_version="1.0",
        message_id=message_id,
        correlation_id=correlation_id,
        causation_id=None,
        producer="mayak.tests",
        account_scope="account-1",
        beacon_scope="beacon-1",
    )

    assert metadata.contract_name == "scan.requested"
    assert metadata.contract_version == "1.0"
    assert metadata.message_id == message_id
    assert metadata.correlation_id == correlation_id
    assert metadata.causation_id is None
    assert metadata.producer == "mayak.tests"
    assert metadata.account_scope == "account-1"
    assert metadata.beacon_scope == "beacon-1"


def test_module_ids_exist() -> None:
    assert len(boundaries.MODULE_IDS) == 13
    assert boundaries.MODULE_IDS[0] == boundaries.PLATFORM_AND_CONTRACTS_MODULE_ID
    assert boundaries.MODULE_IDS[-1] == boundaries.FILTER_CATALOG_AND_BUILDER_MODULE_ID


def test_redaction_helper_replaces_sensitive_value() -> None:
    redacted = redact_sensitive_value("super-secret-token")

    assert redacted.placeholder == REDACTED_VALUE
    assert redacted.is_redacted is True
    assert redacted.model_dump() == {
        "placeholder": REDACTED_VALUE,
        "is_redacted": True,
    }

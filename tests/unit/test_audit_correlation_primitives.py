from __future__ import annotations

import pytest
from pydantic import ValidationError

from mayak.contracts import (
    AuditActorCategory,
    AuditConfigurationReference,
    AuditContext,
    AuditContractReference,
    AuditErrorReference,
    AuditReadinessReference,
    AuditResultReference,
    AuditTargetScope,
    ConfigurationValidationStatus,
    CorrelationContext,
    CorrelationId,
    ErrorCategory,
    MessageId,
    ProcessReadinessStatus,
    RequestId,
    Result,
    RunId,
    WorkId,
)
from mayak.platform.audit import AuditModuleIdentifier, AuditOperation, AuditReason


def test_correlation_context_can_be_created_with_safe_semantic_identifiers() -> None:
    context = CorrelationContext(
        correlation_id=CorrelationId(value="correlation-123"),
        request_id=RequestId(value="request-123"),
        message_id=MessageId(value="message-123"),
        run_id=RunId(value="run-123"),
        work_id=WorkId(value="work-123"),
    )

    assert context.correlation_id.value == "correlation-123"
    assert context.request_id is not None and context.request_id.value == "request-123"
    assert context.message_id is not None and context.message_id.value == "message-123"
    assert context.run_id is not None and context.run_id.value == "run-123"
    assert context.work_id is not None and context.work_id.value == "work-123"

    with pytest.raises((TypeError, ValidationError)):
        context.correlation_id = CorrelationId(value="changed")  # type: ignore[misc]


def test_correlation_context_rejects_unknown_fields_and_blank_identifiers() -> None:
    with pytest.raises(ValidationError) as exc_info:
        CorrelationContext.model_validate(
            {
                "correlation_id": {"value": "correlation-123"},
                "unexpected_field": "value",
            }
        )

    assert "unexpected_field" in str(exc_info.value)

    with pytest.raises(ValidationError):
        CorrelationId(value=" ")


def test_audit_context_can_be_created_with_redacted_actor_and_safe_scope() -> None:
    correlation = CorrelationContext(
        correlation_id=CorrelationId(value="correlation-123"),
        request_id=RequestId(value="request-123"),
    )
    audit = AuditContext(
        actor_category=AuditActorCategory.REDACTED,
        operation=AuditOperation(value="audit.record"),
        module_id=AuditModuleIdentifier(value="01-platform-and-contracts"),
        target_scope=AuditTargetScope(value="module-scope"),
        reason=AuditReason(value="safe summary"),
        details=("target scope is category-only",),
        correlation=correlation,
        result_reference=AuditResultReference(result=Result.SUCCEEDED),
        error_reference=AuditErrorReference(error_category=ErrorCategory.EXTERNAL_UNAVAILABLE),
        readiness_reference=AuditReadinessReference(status=ProcessReadinessStatus.READY),
        configuration_reference=AuditConfigurationReference(
            status=ConfigurationValidationStatus.READY,
            schema_version=None,
        ),
        contract_reference=AuditContractReference(contract_version="1.0"),
    )

    assert audit.actor_category is AuditActorCategory.REDACTED
    assert audit.operation.value == "audit.record"
    assert audit.module_id.value == "01-platform-and-contracts"
    assert audit.target_scope.value == "module-scope"
    assert audit.reason.value == "safe summary"
    assert audit.details == ("target scope is category-only",)
    assert audit.correlation == correlation
    assert audit.result_reference is not None and audit.result_reference.result is Result.SUCCEEDED
    assert (
        audit.error_reference is not None
        and audit.error_reference.error_category is ErrorCategory.EXTERNAL_UNAVAILABLE
    )
    assert (
        audit.readiness_reference is not None
        and audit.readiness_reference.status is ProcessReadinessStatus.READY
    )
    assert (
        audit.configuration_reference is not None
        and audit.configuration_reference.status is ConfigurationValidationStatus.READY
    )
    assert audit.contract_reference is not None
    assert audit.contract_reference.contract_version == "1.0"

    with pytest.raises((TypeError, ValidationError)):
        audit.target_scope = AuditTargetScope(value="changed")  # type: ignore[misc]


def test_audit_context_rejects_unknown_fields_and_blank_details() -> None:
    with pytest.raises(ValidationError) as exc_info:
        AuditContext.model_validate(
            {
                "actor_category": "REDACTED",
                "operation": {"value": "audit.record"},
                "module_id": {"value": "01-platform-and-contracts"},
                "target_scope": {"value": "module-scope"},
                "reason": {"value": "safe summary"},
                "details": ("safe",),
                "unexpected_field": "value",
            }
        )

    assert "unexpected_field" in str(exc_info.value)

    with pytest.raises(ValidationError):
        AuditContext(
            actor_category=AuditActorCategory.REDACTED,
            operation=AuditOperation(value="audit.record"),
            module_id=AuditModuleIdentifier(value="01-platform-and-contracts"),
            target_scope=AuditTargetScope(value="module-scope"),
            reason=AuditReason(value="safe summary"),
            details=(" ",),
        )


def test_audit_references_remain_transport_neutral() -> None:
    result_reference = AuditResultReference(result=Result.REJECTED)
    error_reference = AuditErrorReference(error_category=ErrorCategory.CONFLICT)
    readiness_reference = AuditReadinessReference(status=ProcessReadinessStatus.BLOCKED)
    configuration_reference = AuditConfigurationReference(
        status=ConfigurationValidationStatus.SOURCE_UNPROVEN,
        schema_version=None,
    )
    contract_reference = AuditContractReference(contract_version="2.0")

    assert result_reference.model_dump() == {"result": Result.REJECTED}
    assert error_reference.model_dump() == {"error_category": ErrorCategory.CONFLICT}
    assert readiness_reference.model_dump() == {"status": ProcessReadinessStatus.BLOCKED}
    assert configuration_reference.model_dump() == {
        "status": ConfigurationValidationStatus.SOURCE_UNPROVEN,
        "schema_version": None,
    }
    assert contract_reference.model_dump() == {"contract_version": "2.0"}

    with pytest.raises(ValidationError):
        AuditResultReference.model_validate({"result": "UNKNOWN"})


def test_audit_and_correlation_models_do_not_require_runtime_specific_types() -> None:
    audit = AuditContext(
        actor_category=AuditActorCategory.SYSTEM,
        operation=AuditOperation(value="audit.check"),
        module_id=AuditModuleIdentifier(value="01-platform-and-contracts"),
        target_scope=AuditTargetScope(value="public-contracts"),
        reason=AuditReason(value="readiness snapshot"),
        correlation=CorrelationContext(correlation_id=CorrelationId(value="correlation-1")),
    )

    assert audit.correlation is not None
    assert isinstance(audit.correlation.correlation_id.value, str)
    assert audit.actor_category is AuditActorCategory.SYSTEM
    assert audit.operation.value == "audit.check"
    assert audit.target_scope.value == "public-contracts"

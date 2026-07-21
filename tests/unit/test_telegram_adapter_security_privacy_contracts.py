from __future__ import annotations

from uuid import UUID

import pytest
from pydantic import ValidationError

from mayak.contracts import ContractMetadata
from mayak.modules.telegram_adapter import (
    TelegramDiagnosticPurpose,
    TelegramPrivacyBoundaryOutcome,
    TelegramPrivacyBoundaryRequest,
    TelegramPrivacyDataClass,
    TelegramPrivacyProjectionState,
    TelegramPrivacyReasonCode,
    TelegramRetentionGateReference,
    TelegramSafeDiagnosticFact,
    TelegramSafeDiagnosticProjection,
    TelegramUntrustedPrivacyReference,
)


def metadata() -> ContractMetadata:
    return ContractMetadata(
        contract_name="telegram.privacy.boundary",
        contract_version="1",
        message_id=UUID("00000000-0000-0000-0000-000000000001"),
        correlation_id=UUID("00000000-0000-0000-0000-000000000002"),
        producer="synthetic-telegram-security-test",
    )


def reference(**overrides: object) -> TelegramUntrustedPrivacyReference:
    values: dict[str, object] = {
        "telegram_untrusted_privacy_reference_id": "privacy-ref-001",
        "metadata": metadata(),
        "data_class": TelegramPrivacyDataClass.SAFE_PROVIDER_IDENTIFIER,
        "source_reference_id": "source-ref-001",
        "provider_bot_scope_reference_id": "bot-scope-ref-001",
        "provider_identifier_reference_ids": ("provider-id-ref-001",),
        "safe_evidence_reference_ids": ("evidence-ref-001",),
        "raw_provider_payload_observed": False,
        "secret_material_observed": False,
        "private_message_content_observed": False,
        "contact_or_phone_data_observed": False,
        "group_membership_data_observed": False,
        "unnecessary_profile_data_observed": False,
        "external_string_present": False,
        "external_string_requires_execution": False,
    }
    values.update(overrides)
    return TelegramUntrustedPrivacyReference(**values)


def fact(ref: TelegramUntrustedPrivacyReference, **overrides: object) -> TelegramSafeDiagnosticFact:
    values: dict[str, object] = {
        "telegram_safe_diagnostic_fact_id": "fact-001",
        "metadata": metadata(),
        "diagnostic_purpose": TelegramDiagnosticPurpose.SECURITY_REJECTION,
        "fact_class": "provider-identifier",
        "reason_code": TelegramPrivacyReasonCode.SAFE_MINIMIZED_DIAGNOSTIC,
        "provider_bot_scope_reference_id": "bot-scope-ref-001",
        "provider_identifier_reference_ids": ("provider-id-ref-001",),
        "correlation_id": "correlation-ref-001",
        "causation_id": "causation-ref-001",
        "source_privacy_reference_ids": (ref.telegram_untrusted_privacy_reference_id,),
        "safe_evidence_reference_ids": ("evidence-ref-001",),
    }
    values.update(overrides)
    return TelegramSafeDiagnosticFact(**values)


def request(
    ref: TelegramUntrustedPrivacyReference | None = None, **overrides: object
) -> TelegramPrivacyBoundaryRequest:
    ref = ref or reference()
    values: dict[str, object] = {
        "telegram_privacy_boundary_request_id": "request-001",
        "metadata": metadata(),
        "privacy_reference": ref,
        "diagnostic_purpose": TelegramDiagnosticPurpose.SECURITY_REJECTION,
        "safe_diagnostic_facts": (fact(ref),),
        "retention_gate": TelegramRetentionGateReference(
            telegram_retention_gate_reference_id="retention-gate-001",
            od_reference="OD-013",
            decision_state="OPEN",
        ),
        "retention_or_storage_policy_requested": False,
        "persistence_requested": False,
        "deletion_requested": False,
        "archive_requested": False,
        "compaction_requested": False,
    }
    values.update(overrides)
    return TelegramPrivacyBoundaryRequest(**values)


def outcome(req: TelegramPrivacyBoundaryRequest) -> TelegramPrivacyBoundaryOutcome:
    projection = TelegramSafeDiagnosticProjection(
        telegram_safe_diagnostic_projection_id=f"{req.telegram_privacy_boundary_request_id}:projection",
        metadata=req.metadata,
        request_reference_id=req.telegram_privacy_boundary_request_id,
        diagnostic_purpose=req.diagnostic_purpose,
        safe_diagnostic_facts=req.safe_diagnostic_facts,
        source_privacy_reference_ids=(
            req.privacy_reference.telegram_untrusted_privacy_reference_id,
        ),
        reason_code=TelegramPrivacyReasonCode.SAFE_MINIMIZED_DIAGNOSTIC,
        retention_gate_reference_id=req.retention_gate.telegram_retention_gate_reference_id,
    )
    return TelegramPrivacyBoundaryOutcome(
        telegram_privacy_boundary_outcome_id="outcome-001",
        metadata=req.metadata,
        request=req,
        state=TelegramPrivacyProjectionState.SAFE_DIAGNOSTIC_PROJECTED,
        reason_code=TelegramPrivacyReasonCode.SAFE_MINIMIZED_DIAGNOSTIC,
        safe_projection=projection,
        safe_diagnostic_reference_id=None,
    )


def test_exact_enum_values_and_immutable_extra_forbid() -> None:
    assert [item.value for item in TelegramPrivacyDataClass] == [
        "SAFE_PROVIDER_IDENTIFIER",
        "SAFE_DIAGNOSTIC_METADATA",
        "PRIVATE_MESSAGE_OR_COMMAND_CONTENT",
        "CALLBACK_OR_DEEP_LINK_INPUT",
        "MINI_APP_LAUNCH_DATA",
        "CONTACT_OR_PHONE_DATA",
        "PROFILE_OR_MEMBERSHIP_DATA",
        "RAW_PROVIDER_PAYLOAD",
        "PROVIDER_SECRET",
    ]
    assert [item.value for item in TelegramPrivacyProjectionState] == [
        "SAFE_DIAGNOSTIC_PROJECTED",
        "BLOCKED_SECRET",
        "BLOCKED_RAW_PAYLOAD",
        "BLOCKED_PRIVATE_CONTENT",
        "BLOCKED_EXCESS_PERSONAL_DATA",
        "BLOCKED_UNSAFE_EXTERNAL_STRING",
        "RETENTION_DECISION_REQUIRED",
        "INVALID_SCOPE",
        "AMBIGUOUS",
    ]
    model = reference()
    with pytest.raises((ValidationError, TypeError)):
        model.telegram_untrusted_privacy_reference_id = "changed"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        reference(unexpected="rejected")


@pytest.mark.parametrize(
    ("flag", "data_class", "state", "reason"),
    [
        (
            "secret_material_observed",
            TelegramPrivacyDataClass.PROVIDER_SECRET,
            TelegramPrivacyProjectionState.BLOCKED_SECRET,
            TelegramPrivacyReasonCode.SECRET_MATERIAL_FORBIDDEN,
        ),
        (
            "raw_provider_payload_observed",
            TelegramPrivacyDataClass.RAW_PROVIDER_PAYLOAD,
            TelegramPrivacyProjectionState.BLOCKED_RAW_PAYLOAD,
            TelegramPrivacyReasonCode.RAW_PROVIDER_PAYLOAD_FORBIDDEN,
        ),
        (
            "private_message_content_observed",
            TelegramPrivacyDataClass.PRIVATE_MESSAGE_OR_COMMAND_CONTENT,
            TelegramPrivacyProjectionState.BLOCKED_PRIVATE_CONTENT,
            TelegramPrivacyReasonCode.PRIVATE_MESSAGE_ARCHIVE_FORBIDDEN,
        ),
        (
            "contact_or_phone_data_observed",
            TelegramPrivacyDataClass.CONTACT_OR_PHONE_DATA,
            TelegramPrivacyProjectionState.BLOCKED_EXCESS_PERSONAL_DATA,
            TelegramPrivacyReasonCode.CONTACT_OR_PHONE_DEFAULT_FORBIDDEN,
        ),
        (
            "group_membership_data_observed",
            TelegramPrivacyDataClass.PROFILE_OR_MEMBERSHIP_DATA,
            TelegramPrivacyProjectionState.BLOCKED_EXCESS_PERSONAL_DATA,
            TelegramPrivacyReasonCode.GROUP_MEMBERSHIP_RETENTION_FORBIDDEN,
        ),
        (
            "unnecessary_profile_data_observed",
            TelegramPrivacyDataClass.PROFILE_OR_MEMBERSHIP_DATA,
            TelegramPrivacyProjectionState.BLOCKED_EXCESS_PERSONAL_DATA,
            TelegramPrivacyReasonCode.UNNECESSARY_PROFILE_DATA_FORBIDDEN,
        ),
    ],
)
def test_untrusted_observation_is_blocked_by_precedence(
    flag: str,
    data_class: TelegramPrivacyDataClass,
    state: TelegramPrivacyProjectionState,
    reason: TelegramPrivacyReasonCode,
) -> None:
    ref = reference(**{flag: True, "data_class": data_class})
    req = request(ref)
    result = TelegramPrivacyBoundaryOutcome(
        telegram_privacy_boundary_outcome_id="outcome-001",
        metadata=req.metadata,
        request=req,
        state=state,
        reason_code=reason,
        safe_projection=None,
        safe_diagnostic_reference_id="safe-diagnostic-ref-001",
    )
    assert result.state is state


def test_safe_projection_is_deterministic_and_has_no_authority() -> None:
    result = outcome(request())
    assert result.safe_projection is not None
    assert result.safe_projection.telegram_safe_diagnostic_projection_id == "request-001:projection"
    assert result.model_dump()["provider_call_performed"] is False
    assert "message" not in result.model_json_schema()["properties"]


@pytest.mark.parametrize(
    "field",
    [
        "retention_or_storage_policy_requested",
        "persistence_requested",
        "deletion_requested",
        "archive_requested",
        "compaction_requested",
    ],
)
def test_retention_and_mutation_requests_are_gate_blocked(field: str) -> None:
    req = request(**{field: True})
    result = TelegramPrivacyBoundaryOutcome(
        telegram_privacy_boundary_outcome_id="outcome-001",
        metadata=req.metadata,
        request=req,
        state=TelegramPrivacyProjectionState.RETENTION_DECISION_REQUIRED,
        reason_code=TelegramPrivacyReasonCode.OD_013_RETENTION_POLICY_OPEN,
        safe_projection=None,
        safe_diagnostic_reference_id="safe-diagnostic-ref-001",
    )
    assert result.reason_code is TelegramPrivacyReasonCode.OD_013_RETENTION_POLICY_OPEN


def test_duplicate_blank_and_scope_mismatch_rejected() -> None:
    with pytest.raises(ValidationError):
        reference(provider_identifier_reference_ids=("provider-id-ref-001", "provider-id-ref-001"))
    with pytest.raises(ValidationError):
        reference(safe_evidence_reference_ids=("",))
    with pytest.raises(ValidationError):
        request(diagnostic_purpose=TelegramDiagnosticPurpose.RECONCILIATION)


def test_external_string_requires_execution_is_untrusted_and_blocked() -> None:
    ref = reference(
        data_class=TelegramPrivacyDataClass.CALLBACK_OR_DEEP_LINK_INPUT,
        external_string_present=True,
        external_string_requires_execution=True,
    )
    req = request(ref)
    result = TelegramPrivacyBoundaryOutcome(
        telegram_privacy_boundary_outcome_id="outcome-001",
        metadata=req.metadata,
        request=req,
        state=TelegramPrivacyProjectionState.BLOCKED_UNSAFE_EXTERNAL_STRING,
        reason_code=TelegramPrivacyReasonCode.EXTERNAL_STRING_EXECUTION_FORBIDDEN,
        safe_projection=None,
        safe_diagnostic_reference_id="safe-diagnostic-ref-001",
    )
    assert result.external_string_executed is False

from __future__ import annotations

# ruff: noqa: E501
from uuid import uuid4

import pytest
from pydantic import ValidationError

from mayak.contracts import ContractMetadata
from mayak.modules.telegram_adapter import contracts as c


def md() -> ContractMetadata:
    return ContractMetadata(
        contract_name="telegram.provider.outcome",
        contract_version="1",
        message_id=uuid4(),
        correlation_id=uuid4(),
        producer="test",
    )


def transport(**changes: object) -> c.TelegramTransportOutcomeObservation:
    v: dict[str, object] = dict(
        telegram_transport_outcome_observation_id="transport-1",
        metadata=md(),
        outbound_mapping_outcome_reference_id="outcome-1",
        notification_attempt_reference_id="attempt-1",
        notification_target_reference_id="target-1",
        egress_dispatch_attempt_reference_id="dispatch-1",
        egress_transport_outcome_reference_id="transport-outcome-1",
        dispatch_status="SENT",
        transport_outcome_status="USABLE_RESPONSE_TRANSPORT_ONLY",
        egress_reconciliation_status="NOT_REQUIRED",
        transport_outcome_committed=True,
        provider_request_sent=True,
        provider_response_received=True,
        provider_response_usable=True,
        provider_effect_known=False,
        provider_safe_response_reference_id=None,
        egress_correlation_reference_id="egress-correlation-1",
        evidence_reference_ids=("evidence-1",),
    )
    v.update(changes)
    return c.TelegramTransportOutcomeObservation(**v)  # type: ignore[arg-type]


def response(**changes: object) -> c.TelegramProviderResponseObservation:
    v: dict[str, object] = dict(
        telegram_provider_response_observation_id="response-1",
        metadata=md(),
        transport_observation_reference_id="transport-1",
        provider_response_reference_id="provider-response-1",
        provider_response_committed=True,
        provider_ok=True,
        provider_rejected=False,
        provider_unavailable=False,
        rate_or_access_restricted=False,
        malformed_or_unusable_response=False,
        provider_effect_known=True,
        provider_effect_committed=True,
        provider_safe_delivery_reference_id="delivery-1",
        telegram_message_reference_id="message-1",
        telegram_callback_correlation_reference_id=None,
        evidence_reference_ids=("evidence-2",),
    )
    v.update(changes)
    return c.TelegramProviderResponseObservation(**v)  # type: ignore[arg-type]


def test_transport_boundary_is_projection_only() -> None:
    item = transport()
    assert item.egress_transport_projection is True
    assert item.transport_success_is_provider_success is False
    assert item.notification_delivery_inferred is False
    with pytest.raises(ValidationError):
        transport(transport_outcome_committed=False)
    with pytest.raises(ValidationError):
        transport(transport_outcome_status="SENT_NO_RESPONSE", provider_response_received=True)
    with pytest.raises(ValidationError):
        transport(transport_outcome_status="DISPATCH_UNKNOWN", provider_effect_known=True)


def test_provider_ok_only_proves_provider_acceptance() -> None:
    item = response()
    assert item.provider_ok is True
    assert item.human_read_or_click_proven is False
    assert item.business_success_proven is False
    assert item.notification_delivery_accepted is False
    assert item.retry_authorized is False
    with pytest.raises(ValidationError):
        response(provider_safe_delivery_reference_id=None)
    with pytest.raises(ValidationError):
        response(provider_rejected=True)


def prepared_request(metadata: ContractMetadata) -> c.TelegramProviderOutcomeMappingRequest:
    handoff = c.TelegramNotificationAttemptHandoff.model_construct(
        metadata=metadata,
        attempt_reference_id="attempt-1",
        attempt_target_reference_id="target-1",
        attempt_correlation_id="correlation-1",
        attempt_causation_id="causation-1",
    )
    outbound_request = c.TelegramOutboundMappingRequest.model_construct(
        telegram_outbound_mapping_request_id="request-1",
        metadata=metadata,
        notification_attempt_handoff=handoff,
    )
    intent = c.TelegramOutboundRequestIntent.model_construct(
        correlation_id="correlation-1", causation_id="causation-1"
    )
    outbound = c.TelegramOutboundMappingOutcome.model_construct(
        telegram_outbound_mapping_outcome_id="outcome-1",
        metadata=metadata,
        request=outbound_request,
        request_intent=intent,
        state=c.TelegramOutboundMappingState.REQUEST_PREPARED,
        reason_code=c.TelegramOutboundMappingReasonCode.TELEGRAM_PRIVATE_CHAT_REQUEST_PREPARED,
        evidence_reference_ids=("outbound-evidence-1",),
    )
    return c.TelegramProviderOutcomeMappingRequest.model_construct(
        telegram_provider_outcome_mapping_request_id="mapping-request-1",
        metadata=metadata,
        outbound_mapping_outcome=outbound,
        transport_observation=None,
        provider_response_observation=None,
        reconciliation_observation=None,
        outcome_policy_reference_id="policy-1",
    )


def test_provider_acceptance_mapping_is_not_notification_acceptance() -> None:
    metadata = md()
    base = prepared_request(metadata)
    transport_observation = transport(
        metadata=metadata,
        outbound_mapping_outcome_reference_id="outcome-1",
    )
    provider_observation = response(
        metadata=metadata,
        transport_observation_reference_id="transport-1",
    )
    request = base.model_copy(
        update={
            "transport_observation": transport_observation,
            "provider_response_observation": provider_observation,
        }
    )
    template = c.TelegramProviderOutcomeMappingDecision.model_construct(request=request)
    outcome = template._build_outcome(
        c.TelegramProviderOutcomeClass.PROVIDER_ACCEPTED,
        c.TelegramProviderOutcomeReasonCode.PROVIDER_ACCEPTED,
    )
    decision = c.TelegramProviderOutcomeMappingDecision(
        telegram_provider_outcome_mapping_decision_id="decision-1",
        metadata=metadata,
        request=request,
        state=c.TelegramProviderOutcomeMappingState.OUTCOME_MAPPED,
        reason_code=c.TelegramProviderOutcomeReasonCode.PROVIDER_ACCEPTED,
        outcome=outcome,
        safe_diagnostic_reference_id=None,
        evidence_reference_ids=("decision-evidence-1",),
    )
    assert decision.outcome is not None
    assert decision.outcome.provider_accepted is True
    assert decision.outcome.notification_delivery_accepted is False
    assert decision.outcome.human_read_or_click_proven is False
    assert decision.outcome.business_success_proven is False
    assert decision.outcome.retry_authorized is False


def test_transport_only_success_maps_ambiguous_and_reconciliation_first() -> None:
    metadata = md()
    base = prepared_request(metadata)
    request = base.model_copy(
        update={
            "transport_observation": transport(
                metadata=metadata,
                outbound_mapping_outcome_reference_id="outcome-1",
            )
        }
    )
    template = c.TelegramProviderOutcomeMappingDecision.model_construct(request=request)
    outcome = template._build_outcome(
        c.TelegramProviderOutcomeClass.PROVIDER_EFFECT_AMBIGUOUS,
        c.TelegramProviderOutcomeReasonCode.PROVIDER_EFFECT_AMBIGUOUS,
    )
    decision = c.TelegramProviderOutcomeMappingDecision(
        telegram_provider_outcome_mapping_decision_id="decision-2",
        metadata=metadata,
        request=request,
        state=c.TelegramProviderOutcomeMappingState.OUTCOME_MAPPED,
        reason_code=c.TelegramProviderOutcomeReasonCode.PROVIDER_EFFECT_AMBIGUOUS,
        outcome=outcome,
        safe_diagnostic_reference_id=None,
        evidence_reference_ids=("decision-evidence-2",),
    )
    assert decision.outcome is not None
    assert decision.outcome.reconciliation_required is True
    assert decision.outcome.blind_retry_authorized is False


@pytest.mark.parametrize(
    "status", ["REQUIRED", "PENDING", "REMAINS_AMBIGUOUS", "MANUAL_REVIEW_REQUIRED"]
)
def test_unresolved_reconciliation_has_no_resolution_facts(status: str) -> None:
    with pytest.raises(ValidationError):
        c.TelegramProviderReconciliationObservation(
            telegram_provider_reconciliation_observation_id="recon-1",
            metadata=md(),
            transport_observation_reference_id="transport-1",
            original_provider_outcome_reference_id="outcome-1",
            egress_reconciliation_reference_id="reconciliation-1",
            egress_reconciliation_status=status,  # type: ignore[arg-type]
            reconciliation_committed=True,
            resolved_outcome_reference_id=None,
            provider_effect_observed=True,
            provider_safe_delivery_reference_id=None,
            evidence_reference_ids=("evidence-1",),
        )

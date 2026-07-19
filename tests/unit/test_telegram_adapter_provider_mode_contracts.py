from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from mayak.contracts import ContractMetadata
from mayak.modules.telegram_adapter import (
    TelegramGetUpdatesModeRequirements,
    TelegramProviderMode,
    TelegramProviderModeBoundary,
    TelegramProviderModeBoundaryState,
    TelegramWebhookModeRequirements,
)


def meta() -> ContractMetadata:
    return ContractMetadata(
        contract_name="telegram.provider-mode-boundary",
        contract_version="1",
        message_id=uuid4(),
        correlation_id=uuid4(),
        producer="telegram-adapter",
    )


def webhook(evidence: str = "official-evidence") -> TelegramWebhookModeRequirements:
    return TelegramWebhookModeRequirements(
        telegram_webhook_mode_requirements_id="webhook-requirements",
        official_telegram_evidence_ref=evidence,
        endpoint_ownership_decision_ref="endpoint-policy",
        tls_domain_port_certificate_gate_ref="tls-policy",
        secret_token_handling_policy_ref="secret-policy",
        authenticity_verification_policy_ref="auth-policy",
        durable_acceptance_policy_ref="durable-policy",
        duplicate_delivery_idempotency_policy_ref="duplicate-policy",
        failure_response_policy_ref="failure-policy",
        drop_pending_transition_policy_ref="webhook-drop-policy",
    )


def get_updates(evidence: str = "official-evidence") -> TelegramGetUpdatesModeRequirements:
    return TelegramGetUpdatesModeRequirements(
        telegram_get_updates_mode_requirements_id="get-updates-requirements",
        official_telegram_evidence_ref=evidence,
        allowed_environment_class_decision_ref="environment-policy",
        polling_ownership_decision_ref="ownership-policy",
        scheduler_worker_boundary_ref="scheduler-policy",
        durable_acceptance_policy_ref="durable-policy",
        offset_advancement_policy_ref="offset-policy",
        interruption_replay_policy_ref="replay-policy",
        mode_transition_policy_ref="transition-policy",
        drop_pending_policy_ref="get-updates-drop-policy",
        timeout_limit_interval_policy_ref="timing-policy",
    )


def boundary(
    state: TelegramProviderModeBoundaryState, **changes: object
) -> TelegramProviderModeBoundary:
    values: dict[str, object] = dict(
        telegram_provider_mode_boundary_id="boundary-ref",
        metadata=meta(),
        telegram_bot_ref="bot-ref",
        environment_ref="environment-ref",
        owner_direction_reference_id="owner-ref",
        official_telegram_evidence_ref="official-evidence",
        state=state,
        reason_code="requires-future-gate",
    )
    values.update(changes)
    return TelegramProviderModeBoundary.model_validate(values)


def test_exact_mode_and_boundary_states() -> None:
    assert [mode.value for mode in TelegramProviderMode] == ["WEBHOOK", "GET_UPDATES"]
    assert [state.value for state in TelegramProviderModeBoundaryState] == [
        "UNSELECTED",
        "WEBHOOK_CANDIDATE",
        "GET_UPDATES_CANDIDATE",
        "TRANSITION_REQUIRED",
        "BLOCKED",
    ]


@pytest.mark.parametrize(
    "state,changes",
    [
        (TelegramProviderModeBoundaryState.UNSELECTED, {}),
        (
            TelegramProviderModeBoundaryState.WEBHOOK_CANDIDATE,
            {"candidate_mode": TelegramProviderMode.WEBHOOK, "webhook_requirements": webhook()},
        ),
        (
            TelegramProviderModeBoundaryState.GET_UPDATES_CANDIDATE,
            {
                "candidate_mode": TelegramProviderMode.GET_UPDATES,
                "get_updates_requirements": get_updates(),
            },
        ),
        (
            TelegramProviderModeBoundaryState.TRANSITION_REQUIRED,
            {
                "current_mode": TelegramProviderMode.WEBHOOK,
                "requested_mode": TelegramProviderMode.GET_UPDATES,
                "get_updates_requirements": get_updates(),
                "mode_transition_policy_ref": "transition-policy",
                "drop_pending_policy_ref": "drop-policy",
            },
        ),
        (
            TelegramProviderModeBoundaryState.TRANSITION_REQUIRED,
            {
                "current_mode": TelegramProviderMode.GET_UPDATES,
                "requested_mode": TelegramProviderMode.WEBHOOK,
                "webhook_requirements": webhook(),
                "mode_transition_policy_ref": "transition-policy",
                "drop_pending_policy_ref": "drop-policy",
            },
        ),
        (
            TelegramProviderModeBoundaryState.BLOCKED,
            {"blocking_decision_reference_id": "blocking-ref"},
        ),
    ],
)
def test_valid_exact_state_matrix(
    state: TelegramProviderModeBoundaryState, changes: dict[str, object]
) -> None:
    assert boundary(state, **changes).state is state


@pytest.mark.parametrize(
    "changes",
    [
        {"candidate_mode": TelegramProviderMode.WEBHOOK},
        {"current_mode": TelegramProviderMode.WEBHOOK},
        {"requested_mode": TelegramProviderMode.GET_UPDATES},
        {"webhook_requirements": webhook()},
        {"get_updates_requirements": get_updates()},
        {"mode_transition_policy_ref": "x"},
        {"drop_pending_policy_ref": "x"},
        {"blocking_decision_reference_id": "x"},
    ],
)
def test_unselected_rejects_all_mode_matrix_additions(changes: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        boundary(TelegramProviderModeBoundaryState.UNSELECTED, **changes)


@pytest.mark.parametrize(
    "state,changes",
    [
        (
            TelegramProviderModeBoundaryState.WEBHOOK_CANDIDATE,
            {"candidate_mode": TelegramProviderMode.GET_UPDATES, "webhook_requirements": webhook()},
        ),
        (
            TelegramProviderModeBoundaryState.WEBHOOK_CANDIDATE,
            {
                "candidate_mode": TelegramProviderMode.WEBHOOK,
                "webhook_requirements": webhook(),
                "get_updates_requirements": get_updates(),
            },
        ),
        (
            TelegramProviderModeBoundaryState.WEBHOOK_CANDIDATE,
            {
                "candidate_mode": TelegramProviderMode.WEBHOOK,
                "webhook_requirements": webhook("other"),
            },
        ),
        (
            TelegramProviderModeBoundaryState.GET_UPDATES_CANDIDATE,
            {
                "candidate_mode": TelegramProviderMode.GET_UPDATES,
                "get_updates_requirements": get_updates(),
                "webhook_requirements": webhook(),
            },
        ),
        (
            TelegramProviderModeBoundaryState.GET_UPDATES_CANDIDATE,
            {
                "candidate_mode": TelegramProviderMode.GET_UPDATES,
                "get_updates_requirements": get_updates("other"),
            },
        ),
        (
            TelegramProviderModeBoundaryState.TRANSITION_REQUIRED,
            {
                "current_mode": TelegramProviderMode.WEBHOOK,
                "requested_mode": TelegramProviderMode.WEBHOOK,
                "webhook_requirements": webhook(),
                "mode_transition_policy_ref": "x",
                "drop_pending_policy_ref": "x",
            },
        ),
        (
            TelegramProviderModeBoundaryState.TRANSITION_REQUIRED,
            {
                "current_mode": TelegramProviderMode.WEBHOOK,
                "requested_mode": TelegramProviderMode.GET_UPDATES,
                "webhook_requirements": webhook(),
                "mode_transition_policy_ref": "x",
                "drop_pending_policy_ref": "x",
            },
        ),
        (
            TelegramProviderModeBoundaryState.TRANSITION_REQUIRED,
            {
                "current_mode": TelegramProviderMode.WEBHOOK,
                "requested_mode": TelegramProviderMode.GET_UPDATES,
                "get_updates_requirements": get_updates(),
                "drop_pending_policy_ref": "x",
            },
        ),
        (TelegramProviderModeBoundaryState.BLOCKED, {"blocking_decision_reference_id": None}),
        (
            TelegramProviderModeBoundaryState.BLOCKED,
            {"blocking_decision_reference_id": "x", "candidate_mode": TelegramProviderMode.WEBHOOK},
        ),
    ],
)
def test_invalid_state_matrix_combinations(
    state: TelegramProviderModeBoundaryState, changes: dict[str, object]
) -> None:
    with pytest.raises(ValidationError):
        boundary(state, **changes)


def test_requirements_are_complete_immutable_and_reference_only() -> None:
    assert set(TelegramWebhookModeRequirements.model_fields) == {
        "telegram_webhook_mode_requirements_id",
        "official_telegram_evidence_ref",
        "endpoint_ownership_decision_ref",
        "tls_domain_port_certificate_gate_ref",
        "secret_token_handling_policy_ref",
        "authenticity_verification_policy_ref",
        "durable_acceptance_policy_ref",
        "duplicate_delivery_idempotency_policy_ref",
        "failure_response_policy_ref",
        "drop_pending_transition_policy_ref",
        "secret_material_present",
        "http_acknowledgement_is_business_success",
        "provider_request_authorized",
    }
    assert set(TelegramGetUpdatesModeRequirements.model_fields) == {
        "telegram_get_updates_mode_requirements_id",
        "official_telegram_evidence_ref",
        "allowed_environment_class_decision_ref",
        "polling_ownership_decision_ref",
        "scheduler_worker_boundary_ref",
        "durable_acceptance_policy_ref",
        "offset_advancement_policy_ref",
        "interruption_replay_policy_ref",
        "mode_transition_policy_ref",
        "drop_pending_policy_ref",
        "timeout_limit_interval_policy_ref",
        "process_local_cursor_authoritative",
        "arrival_is_trusted_without_validation",
        "offset_advance_before_durable_acceptance_authorized",
        "provider_request_authorized",
    }
    with pytest.raises(ValidationError):
        TelegramWebhookModeRequirements.model_validate(
            {**webhook().model_dump(), "token_value": "synthetic"}
        )
    with pytest.raises(ValidationError):
        TelegramWebhookModeRequirements.model_validate(
            {**webhook().model_dump(), "secret_material_present": True}
        )
    with pytest.raises(ValidationError):
        TelegramGetUpdatesModeRequirements.model_validate(
            {**get_updates().model_dump(), "timeout": 1}
        )
    with pytest.raises(ValidationError):
        webhook(" ")
    with pytest.raises(ValidationError):
        boundary(TelegramProviderModeBoundaryState.BLOCKED, blocking_decision_reference_id=" ")
    with pytest.raises((TypeError, ValidationError)):
        webhook().telegram_webhook_mode_requirements_id = "changed"  # type: ignore[misc]


def test_boundary_is_frozen_and_safety_literals_are_not_runtime_authorizations() -> None:
    model = boundary(TelegramProviderModeBoundaryState.UNSELECTED)
    assert model.production_staging_target_mode is TelegramProviderMode.WEBHOOK
    assert model.development_proof_mode_candidate is TelegramProviderMode.GET_UPDATES
    assert model.development_proof_requires_explicit_gate is True
    assert model.environment_mode_selected is False
    assert model.simultaneous_modes_authorized is False
    assert model.provider_runtime_authorized is False
    assert model.provider_call_authorized is False
    assert webhook().http_acknowledgement_is_business_success is False
    assert (
        "http_acknowledgement_is_business_success"
        in TelegramWebhookModeRequirements.model_fields
    )
    assert "provider_runtime_authorized" in TelegramProviderModeBoundary.model_fields
    assert (
        webhook().model_json_schema()["properties"][
            "http_acknowledgement_is_business_success"
        ]["default"]
        is False
    )
    assert (
        model.model_json_schema()["properties"]["provider_runtime_authorized"]["default"]
        is False
    )
    assert webhook().model_dump()["http_acknowledgement_is_business_success"] is False
    assert model.model_dump()["provider_runtime_authorized"] is False
    assert (
        TelegramWebhookModeRequirements.model_validate(
            webhook().model_dump()
        ).http_acknowledgement_is_business_success
        is False
    )
    assert (
        TelegramProviderModeBoundary.model_validate(
            model.model_dump()
        ).provider_runtime_authorized
        is False
    )
    with pytest.raises(ValidationError):
        TelegramWebhookModeRequirements.model_validate(
            {**webhook().model_dump(), "http_acknowledgement_is_business_success": True}
        )
    with pytest.raises(ValidationError):
        TelegramProviderModeBoundary.model_validate(
            {**model.model_dump(), "provider_runtime_authorized": True}
        )
    with pytest.raises((TypeError, ValidationError)):
        model.reason_code = "changed"  # type: ignore[misc]
    with pytest.raises((TypeError, ValidationError)):
        webhook().http_acknowledgement_is_business_success = True  # type: ignore[assignment]
    with pytest.raises((TypeError, ValidationError)):
        model.provider_runtime_authorized = True  # type: ignore[assignment]


def test_official_provider_semantics_are_only_policy_evidence() -> None:
    facts = {
        "modes_are_mutually_exclusive": "official-evidence",
        "offset_follows_durable_acceptance": "official-evidence",
        "non_2xx_may_redeliver": "official-evidence",
        "secret_header_is_provider_verified": "official-evidence",
        "http_ack_is_not_business_success": "official-evidence",
    }
    assert all(value and "/" not in value for value in facts.values())
    assert boundary(TelegramProviderModeBoundaryState.UNSELECTED).environment_mode_selected is False

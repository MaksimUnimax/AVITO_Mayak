from __future__ import annotations

import copy

import pytest
from pydantic import ValidationError

from mayak.contracts import IdempotencyFingerprint
from mayak.modules.telegram_adapter import (
    TelegramMiniAppContextOwnerBoundary,
    TelegramMiniAppFreshnessState,
    TelegramMiniAppFrontendDecisionState,
    TelegramMiniAppInitDataValidationState,
    TelegramMiniAppOfficialValidationEvidence,
    TelegramMiniAppPurpose,
    TelegramMiniAppValidationOutcome,
    TelegramMiniAppValidationRequest,
    TelegramMiniAppValidationState,
    TelegramProviderIdentity,
    TelegramUntrustedMiniAppLaunchReference,
    VerifiedTelegramIdentityEvidence,
)

PURPOSE_OWNERS = {
    TelegramMiniAppPurpose.SHOW_FULL_LISTING_RESULT: (
        TelegramMiniAppContextOwnerBoundary.NOTIFICATION_DELIVERY
    ),
    TelegramMiniAppPurpose.SHOW_BEACON_SETTINGS: (
        TelegramMiniAppContextOwnerBoundary.BEACON_MANAGEMENT
    ),
    TelegramMiniAppPurpose.SHOW_BEACON_STATUS: (
        TelegramMiniAppContextOwnerBoundary.BEACON_MANAGEMENT
    ),
    TelegramMiniAppPurpose.RICH_ONBOARDING: (
        TelegramMiniAppContextOwnerBoundary.IDENTITY_AND_ACCESS
    ),
    TelegramMiniAppPurpose.OPEN_FROM_NOTIFICATION_ACTION: (
        TelegramMiniAppContextOwnerBoundary.NOTIFICATION_DELIVERY
    ),
    TelegramMiniAppPurpose.UNSUPPORTED: TelegramMiniAppContextOwnerBoundary.NONE,
    TelegramMiniAppPurpose.AMBIGUOUS: TelegramMiniAppContextOwnerBoundary.NONE,
}


def launch(
    purpose: TelegramMiniAppPurpose = TelegramMiniAppPurpose.RICH_ONBOARDING,
) -> TelegramUntrustedMiniAppLaunchReference:
    return TelegramUntrustedMiniAppLaunchReference(
        telegram_mini_app_launch_reference_id=" launch-ref ",
        telegram_bot_ref=" bot-ref ",
        launch_context_reference=" context-ref ",
        launch_data_fingerprint=IdempotencyFingerprint(value="launch-fp"),
        purpose_candidate=purpose,
        unsafe_context_present=True,
    )


def evidence(
    state: TelegramMiniAppInitDataValidationState = (
        TelegramMiniAppInitDataValidationState.OFFICIAL_VALIDATION_PASSED
    ),
    freshness: TelegramMiniAppFreshnessState = TelegramMiniAppFreshnessState.WITHIN_EXTERNAL_POLICY,
    *,
    received: bool = True,
    policy_ref: str | None = "freshness-policy",
) -> TelegramMiniAppOfficialValidationEvidence:
    return TelegramMiniAppOfficialValidationEvidence(
        telegram_mini_app_official_validation_evidence_id=" evidence-ref ",
        telegram_bot_ref="bot-ref",
        matching_launch_data_fingerprint=IdempotencyFingerprint(value="launch-fp"),
        init_data_validation_state=state,
        freshness_state=freshness,
        official_provider_evidence_reference="provider-evidence",
        official_validation_policy_reference="official-policy",
        external_freshness_policy_reference=policy_ref,
        backend_received_raw_launch_data_for_validation=received,
    )


def request(
    purpose: TelegramMiniAppPurpose = TelegramMiniAppPurpose.RICH_ONBOARDING,
    *,
    validation: TelegramMiniAppOfficialValidationEvidence | None = None,
    frontend: TelegramMiniAppFrontendDecisionState = (
        TelegramMiniAppFrontendDecisionState.EXTERNAL_DECISION_ACCEPTED
    ),
    frontend_ref: str | None = "frontend-decision",
    verified: bool | None = None,
) -> TelegramMiniAppValidationRequest:
    validation = validation or evidence()
    if verified is None:
        verified = (
            validation.init_data_validation_state
            is TelegramMiniAppInitDataValidationState.OFFICIAL_VALIDATION_PASSED
        )
    identity = (
        VerifiedTelegramIdentityEvidence(
            verified_identity_evidence_ref="verified-ref",
            provider_identity=TelegramProviderIdentity(
                telegram_provider_identity_ref="provider-ref",
                telegram_bot_ref="bot-ref",
                telegram_user_id="external-user",
            ),
            verification_method_ref="verification-policy",
            verification_result_ref="verification-result",
        )
        if verified
        else None
    )
    return TelegramMiniAppValidationRequest(
        telegram_mini_app_validation_request_id="request-ref",
        untrusted_launch_reference=launch(purpose),
        official_validation_evidence=validation,
        verified_telegram_provider_identity_evidence=identity,
        frontend_decision_state=frontend,
        external_frontend_decision_reference=frontend_ref,
        requested_context_owner_boundary=PURPOSE_OWNERS[purpose],
    )


def outcome(
    req: TelegramMiniAppValidationRequest, state: TelegramMiniAppValidationState
) -> TelegramMiniAppValidationOutcome:
    success = state is TelegramMiniAppValidationState.IDENTITY_HANDOFF_REQUIRED
    return TelegramMiniAppValidationOutcome(
        telegram_mini_app_validation_outcome_id="outcome-ref",
        validation_request=req,
        validation_state=state,
        requested_context_owner_boundary=req.requested_context_owner_boundary,
        identity_handoff_reference="identity-handoff" if success else None,
        blocking_or_rejection_reason_reference=None if success else "safe-reason",
    )


def test_exact_enums_and_purpose_owner_mapping() -> None:
    assert tuple(TelegramMiniAppPurpose) == tuple(PURPOSE_OWNERS)
    assert tuple(TelegramMiniAppContextOwnerBoundary) == (
        TelegramMiniAppContextOwnerBoundary.IDENTITY_AND_ACCESS,
        TelegramMiniAppContextOwnerBoundary.BEACON_MANAGEMENT,
        TelegramMiniAppContextOwnerBoundary.NOTIFICATION_DELIVERY,
        TelegramMiniAppContextOwnerBoundary.NONE,
    )
    assert {p: PURPOSE_OWNERS[p] for p in TelegramMiniAppPurpose} == PURPOSE_OWNERS


def test_records_are_frozen_forbid_extra_and_strip_strings() -> None:
    item = launch()
    assert item.telegram_mini_app_launch_reference_id == "launch-ref"
    with pytest.raises(ValidationError):
        item.telegram_bot_ref = "other"  # type: ignore[misc]
    for factory in (launch, evidence):
        data = factory().model_dump()
        data["unknown"] = "rejected"
        with pytest.raises(ValidationError):
            type(factory())(**data)


@pytest.mark.parametrize("purpose", tuple(PURPOSE_OWNERS))
def test_supported_purposes_have_positive_identity_handoff(purpose: TelegramMiniAppPurpose) -> None:
    if purpose in {TelegramMiniAppPurpose.UNSUPPORTED, TelegramMiniAppPurpose.AMBIGUOUS}:
        return
    req = request(purpose)
    assert outcome(req, TelegramMiniAppValidationState.IDENTITY_HANDOFF_REQUIRED)


@pytest.mark.parametrize(
    ("state", "freshness", "received", "policy"),
    (
        (
            TelegramMiniAppInitDataValidationState.OFFICIAL_VALIDATION_PASSED,
            TelegramMiniAppFreshnessState.WITHIN_EXTERNAL_POLICY,
            True,
            "p",
        ),
        (
            TelegramMiniAppInitDataValidationState.OFFICIAL_VALIDATION_REJECTED,
            TelegramMiniAppFreshnessState.STALE,
            True,
            "p",
        ),
        (
            TelegramMiniAppInitDataValidationState.AMBIGUOUS,
            TelegramMiniAppFreshnessState.AMBIGUOUS,
            True,
            "p",
        ),
        (
            TelegramMiniAppInitDataValidationState.INIT_DATA_MISSING,
            TelegramMiniAppFreshnessState.MISSING,
            False,
            "p",
        ),
        (
            TelegramMiniAppInitDataValidationState.INIT_DATA_UNSAFE_ONLY,
            TelegramMiniAppFreshnessState.POLICY_NOT_SELECTED,
            False,
            None,
        ),
        (
            TelegramMiniAppInitDataValidationState.NOT_PERFORMED,
            TelegramMiniAppFreshnessState.POLICY_NOT_SELECTED,
            False,
            None,
        ),
    ),
)
def test_exact_official_validation_evidence_matrix(
    state: TelegramMiniAppInitDataValidationState,
    freshness: TelegramMiniAppFreshnessState,
    received: bool,
    policy: str | None,
) -> None:
    evidence(state, freshness, received=received, policy_ref=policy)


@pytest.mark.parametrize(
    ("state", "freshness", "received", "policy"),
    (
        (
            TelegramMiniAppInitDataValidationState.INIT_DATA_MISSING,
            TelegramMiniAppFreshnessState.WITHIN_EXTERNAL_POLICY,
            False,
            "p",
        ),
        (
            TelegramMiniAppInitDataValidationState.NOT_PERFORMED,
            TelegramMiniAppFreshnessState.MISSING,
            False,
            "p",
        ),
        (
            TelegramMiniAppInitDataValidationState.OFFICIAL_VALIDATION_REJECTED,
            TelegramMiniAppFreshnessState.WITHIN_EXTERNAL_POLICY,
            True,
            "p",
        ),
    ),
)
def test_invalid_official_matrix_rejected(
    state: TelegramMiniAppInitDataValidationState,
    freshness: TelegramMiniAppFreshnessState,
    received: bool,
    policy: str | None,
) -> None:
    with pytest.raises(ValidationError):
        evidence(state, freshness, received=received, policy_ref=policy)


@pytest.mark.parametrize("decision", tuple(TelegramMiniAppFrontendDecisionState))
def test_frontend_decision_matrix(decision: TelegramMiniAppFrontendDecisionState) -> None:
    ref = (
        "frontend-decision"
        if decision is TelegramMiniAppFrontendDecisionState.EXTERNAL_DECISION_ACCEPTED
        else None
    )
    request(frontend=decision, frontend_ref=ref)
    if decision is TelegramMiniAppFrontendDecisionState.EXTERNAL_DECISION_ACCEPTED:
        with pytest.raises(ValidationError):
            request(frontend=decision, frontend_ref=None)


@pytest.mark.parametrize(
    ("validation", "state"),
    (
        (
            evidence(
                TelegramMiniAppInitDataValidationState.INIT_DATA_UNSAFE_ONLY,
                TelegramMiniAppFreshnessState.POLICY_NOT_SELECTED,
                received=False,
                policy_ref=None,
            ),
            TelegramMiniAppValidationState.REJECTED_INIT_DATA_UNSAFE_ONLY,
        ),
        (
            evidence(
                TelegramMiniAppInitDataValidationState.INIT_DATA_MISSING,
                TelegramMiniAppFreshnessState.MISSING,
                received=False,
            ),
            TelegramMiniAppValidationState.REJECTED_INIT_DATA_MISSING,
        ),
        (
            evidence(
                TelegramMiniAppInitDataValidationState.NOT_PERFORMED,
                TelegramMiniAppFreshnessState.POLICY_NOT_SELECTED,
                received=False,
                policy_ref=None,
            ),
            TelegramMiniAppValidationState.BLOCKED,
        ),
        (
            evidence(
                TelegramMiniAppInitDataValidationState.OFFICIAL_VALIDATION_REJECTED,
                TelegramMiniAppFreshnessState.STALE,
            ),
            TelegramMiniAppValidationState.REJECTED_OFFICIAL_VALIDATION,
        ),
        (
            evidence(freshness=TelegramMiniAppFreshnessState.POLICY_NOT_SELECTED, policy_ref=None),
            TelegramMiniAppValidationState.BLOCKED_PENDING_FRESHNESS_POLICY,
        ),
        (
            evidence(freshness=TelegramMiniAppFreshnessState.STALE),
            TelegramMiniAppValidationState.REJECTED_STALE_OR_MISSING_AUTH_DATE,
        ),
        (
            evidence(freshness=TelegramMiniAppFreshnessState.MISSING),
            TelegramMiniAppValidationState.REJECTED_STALE_OR_MISSING_AUTH_DATE,
        ),
        (
            evidence(freshness=TelegramMiniAppFreshnessState.AMBIGUOUS),
            TelegramMiniAppValidationState.AMBIGUOUS,
        ),
    ),
)
def test_validation_outcome_matrix(
    validation: TelegramMiniAppOfficialValidationEvidence,
    state: TelegramMiniAppValidationState,
) -> None:
    req = request(
        validation=validation,
        verified=validation.init_data_validation_state
        is TelegramMiniAppInitDataValidationState.OFFICIAL_VALIDATION_PASSED,
    )
    assert outcome(req, state).validation_state is state


def test_supported_frontend_and_purpose_outcomes() -> None:
    for purpose in PURPOSE_OWNERS:
        if purpose in {TelegramMiniAppPurpose.UNSUPPORTED, TelegramMiniAppPurpose.AMBIGUOUS}:
            continue
        assert outcome(request(purpose), TelegramMiniAppValidationState.IDENTITY_HANDOFF_REQUIRED)
        assert outcome(
            request(
                purpose, frontend=TelegramMiniAppFrontendDecisionState.MISSING, frontend_ref=None
            ),
            TelegramMiniAppValidationState.BLOCKED_PENDING_FRONTEND_DECISION,
        )
        assert outcome(
            request(
                purpose, frontend=TelegramMiniAppFrontendDecisionState.REJECTED, frontend_ref=None
            ),
            TelegramMiniAppValidationState.BLOCKED,
        )
        assert outcome(
            request(
                purpose, frontend=TelegramMiniAppFrontendDecisionState.AMBIGUOUS, frontend_ref=None
            ),
            TelegramMiniAppValidationState.AMBIGUOUS,
        )
    assert outcome(
        request(TelegramMiniAppPurpose.UNSUPPORTED), TelegramMiniAppValidationState.UNSUPPORTED
    )
    assert outcome(
        request(TelegramMiniAppPurpose.AMBIGUOUS), TelegramMiniAppValidationState.AMBIGUOUS
    )


def test_identity_handoff_and_reason_references_are_exclusive() -> None:
    req = request()
    with pytest.raises(ValidationError):
        data = outcome(req, TelegramMiniAppValidationState.IDENTITY_HANDOFF_REQUIRED).model_dump(
            mode="python"
        )
        data["blocking_or_rejection_reason_reference"] = "reason"
        TelegramMiniAppValidationOutcome(**data)
    with pytest.raises(ValidationError):
        data = outcome(req, TelegramMiniAppValidationState.BLOCKED).model_dump(mode="python")
        data["identity_handoff_reference"] = "handoff"
        TelegramMiniAppValidationOutcome(**data)


@pytest.mark.parametrize(
    "field", ("telegram_bot_ref", "launch_data_fingerprint", "purpose_candidate")
)
def test_each_single_mismatch_is_rejected_from_fresh_copy(field: str) -> None:
    data = copy.deepcopy(launch().model_dump())
    data[field] = (
        "defect" if field != "purpose_candidate" else TelegramMiniAppPurpose.SHOW_BEACON_STATUS
    )
    with pytest.raises(ValidationError):
        TelegramMiniAppValidationRequest(
            telegram_mini_app_validation_request_id="request-ref",
            untrusted_launch_reference=TelegramUntrustedMiniAppLaunchReference(**data),
            official_validation_evidence=evidence(),
            verified_telegram_provider_identity_evidence=request().verified_telegram_provider_identity_evidence,
            frontend_decision_state=TelegramMiniAppFrontendDecisionState.EXTERNAL_DECISION_ACCEPTED,
            external_frontend_decision_reference="frontend-decision",
            requested_context_owner_boundary=TelegramMiniAppContextOwnerBoundary.IDENTITY_AND_ACCESS,
        )


def test_verified_identity_required_only_after_passed_and_scope_matches() -> None:
    with pytest.raises(ValidationError):
        request(
            validation=evidence(
                TelegramMiniAppInitDataValidationState.NOT_PERFORMED,
                TelegramMiniAppFreshnessState.POLICY_NOT_SELECTED,
                received=False,
                policy_ref=None,
            ),
            verified=True,
        )
    bad = request().model_dump()
    bad["verified_telegram_provider_identity_evidence"]["provider_identity"]["telegram_bot_ref"] = (
        "other-bot"
    )
    with pytest.raises(ValidationError):
        TelegramMiniAppValidationRequest(**bad)

from __future__ import annotations

import pytest
from typing import Any, cast

from mayak.contracts.idempotency import IdempotencyDecision
from mayak.modules.notification_delivery.deduplication import (
    NotificationDeduplicationAuthority,
    NotificationDeduplicationDecisionStatus,
    NotificationDeduplicationRecord,
    NotificationDeduplicationRecordState,
    NotificationDeduplicationRequest,
    NotificationDeduplicationStage,
    evaluate_notification_deduplication,
)
from mayak.modules.notification_delivery.eligibility import NotificationChannelClass
from mayak.modules.notification_delivery.source_intake import NotificationSourceFamily
from mayak.platform.idempotency import IdempotencyFingerprint as PlatformIdempotencyFingerprint
from mayak.platform.idempotency import IdempotencyKey as PlatformIdempotencyKey
from mayak.platform.idempotency import IdempotencyScope as PlatformIdempotencyScope


class _KeySubclass(PlatformIdempotencyKey):
    pass


class _Lookalike:
    def __init__(self, value: str) -> None:
        self.value = value


def _key(value: str = "key-1") -> PlatformIdempotencyKey:
    return PlatformIdempotencyKey(value=value)


def _fingerprint(value: str = "fingerprint-1") -> PlatformIdempotencyFingerprint:
    return PlatformIdempotencyFingerprint(value=value)


def _scope(value: str = "scope-1") -> PlatformIdempotencyScope:
    return PlatformIdempotencyScope(value=value)


def _request(
    *,
    stage: NotificationDeduplicationStage,
    source_family: NotificationSourceFamily = NotificationSourceFamily.RECOVERY_SCAN_COMPLETED,
    account_id: str = "account-1",
    beacon_id: str | None = "beacon-1",
    channel_class: NotificationChannelClass | None = None,
    semantic_effect_reference_id: str = "semantic-effect-1",
    idempotency_key: PlatformIdempotencyKey | None = _key(),
    idempotency_fingerprint: PlatformIdempotencyFingerprint | None = _fingerprint(),
    idempotency_scope: PlatformIdempotencyScope | None = _scope(),
    proposed_record_state: NotificationDeduplicationRecordState = (
        NotificationDeduplicationRecordState.TERMINAL
    ),
    proposed_result_reference_id: str = "proposed-result-1",
    correlation_id: str = "correlation-1",
    causation_id: str = "causation-1",
    evidence_reference_ids: tuple[str, ...] = ("request-1", "shared", "request-2", "request-1"),
) -> NotificationDeduplicationRequest:
    return NotificationDeduplicationRequest(
        stage=stage,
        source_family=source_family,
        account_id=account_id,
        beacon_id=beacon_id,
        channel_class=channel_class,
        semantic_effect_reference_id=semantic_effect_reference_id,
        idempotency_key=idempotency_key,
        idempotency_fingerprint=idempotency_fingerprint,
        idempotency_scope=idempotency_scope,
        proposed_record_state=proposed_record_state,
        proposed_result_reference_id=proposed_result_reference_id,
        correlation_id=correlation_id,
        causation_id=causation_id,
        evidence_reference_ids=evidence_reference_ids,
    )


def _record(
    request: NotificationDeduplicationRequest,
    *,
    record_state: NotificationDeduplicationRecordState,
    record_id: str = "record-1",
    protected_result_reference_id: str = "protected-result-1",
    evidence_reference_ids: tuple[str, ...] = ("existing-1", "shared", "existing-2", "existing-1"),
) -> NotificationDeduplicationRecord:
    assert request.idempotency_key is not None
    assert request.idempotency_fingerprint is not None
    assert request.idempotency_scope is not None
    return NotificationDeduplicationRecord(
        record_id=record_id,
        authority=NotificationDeduplicationAuthority.NOTIFICATION_DELIVERY_SERVER,
        stage=request.stage,
        source_family=request.source_family,
        account_id=request.account_id,
        beacon_id=request.beacon_id,
        channel_class=request.channel_class,
        semantic_effect_reference_id=request.semantic_effect_reference_id,
        idempotency_key=request.idempotency_key,
        idempotency_fingerprint=request.idempotency_fingerprint,
        idempotency_scope=request.idempotency_scope,
        record_state=record_state,
        protected_result_reference_id=protected_result_reference_id,
        correlation_id=request.correlation_id,
        causation_id=request.causation_id,
        reason_codes=(
            {
                NotificationDeduplicationRecordState.PENDING: "dedup-record-pending",
                NotificationDeduplicationRecordState.TERMINAL: "dedup-record-terminal",
                NotificationDeduplicationRecordState.AMBIGUOUS: "dedup-record-ambiguous",
            }[record_state],
        ),
        evidence_reference_ids=evidence_reference_ids,
    )


def test_missing_idempotency_is_rejected_before_effect() -> None:
    request = _request(
        stage=NotificationDeduplicationStage.SOURCE_INTAKE,
        source_family=NotificationSourceFamily.RECOVERY_SCAN_COMPLETED,
        idempotency_key=None,
        idempotency_fingerprint=None,
        idempotency_scope=None,
    )
    unrelated_existing_record = _record(
        _request(
            stage=NotificationDeduplicationStage.SOURCE_INTAKE,
            source_family=NotificationSourceFamily.RECOVERY_SCAN_COMPLETED,
            idempotency_key=_key("other-key"),
            idempotency_fingerprint=_fingerprint("other-fingerprint"),
            idempotency_scope=_scope("other-scope"),
        ),
        record_state=NotificationDeduplicationRecordState.TERMINAL,
        protected_result_reference_id="original-result-1",
    )

    decision = evaluate_notification_deduplication(
        decision_id="decision-1",
        record_id="record-new-1",
        request=request,
        existing_record=unrelated_existing_record,
        evidence_reference_ids=("command-1", "shared", "command-2", "command-1"),
    )

    assert decision.status is NotificationDeduplicationDecisionStatus.MISSING_REQUIRED_IDEMPOTENCY
    assert decision.existing_record is None
    assert decision.resulting_record is None
    assert decision.effect_authorized is False
    assert decision.replayed is False
    assert decision.reconciliation_required is False
    assert decision.idempotency_decision is None
    assert decision.reason_codes == ("dedup-missing-idempotency",)
    assert decision.evidence_reference_ids == (
        "request-1",
        "shared",
        "request-2",
        "command-1",
        "command-2",
    )


def test_new_record_authorizes_semantic_only_effect() -> None:
    request = _request(
        stage=NotificationDeduplicationStage.OUTBOX_CREATION,
        source_family=NotificationSourceFamily.EXTERNAL_UNAVAILABLE_STATUS,
        proposed_record_state=NotificationDeduplicationRecordState.AMBIGUOUS,
        proposed_result_reference_id="new-outbox-result-1",
        evidence_reference_ids=("request-1", "shared", "request-2", "request-1"),
    )

    decision = evaluate_notification_deduplication(
        decision_id="decision-2",
        record_id="record-2",
        request=request,
        existing_record=None,
        evidence_reference_ids=("command-1", "shared", "command-2", "command-1"),
    )

    assert decision.status is NotificationDeduplicationDecisionStatus.NEW_EFFECT
    assert decision.existing_record is None
    assert decision.resulting_record is not None
    assert decision.resulting_record.record_id == "record-2"
    assert decision.resulting_record.protected_result_reference_id == "new-outbox-result-1"
    assert decision.resulting_record.record_state is NotificationDeduplicationRecordState.AMBIGUOUS
    assert decision.resulting_record.reason_codes == ("dedup-record-ambiguous",)
    assert decision.resulting_record.evidence_reference_ids == (
        "request-1",
        "shared",
        "request-2",
        "command-1",
        "command-2",
    )
    assert decision.effect_authorized is True
    assert decision.replayed is False
    assert decision.reconciliation_required is True
    assert decision.idempotency_decision is IdempotencyDecision.NEW
    assert decision.reason_codes == ("dedup-new-effect",)
    assert decision.evidence_reference_ids == (
        "request-1",
        "shared",
        "request-2",
        "command-1",
        "command-2",
    )


@pytest.mark.parametrize(
    ("stage", "channel_class", "source_family", "original_reference", "replayed_reference"),
    [
        (
            NotificationDeduplicationStage.SOURCE_INTAKE,
            None,
            NotificationSourceFamily.RECOVERY_SCAN_COMPLETED,
            "original-source-reference-1",
            "replayed-source-reference-1",
        ),
        (
            NotificationDeduplicationStage.OUTBOX_CREATION,
            None,
            NotificationSourceFamily.EXTERNAL_UNAVAILABLE_STATUS,
            "original-outbox-reference-1",
            "replayed-outbox-reference-1",
        ),
        (
            NotificationDeduplicationStage.ATTEMPT_CREATION,
            NotificationChannelClass.TELEGRAM,
            NotificationSourceFamily.NO_NEW_LISTINGS_STATUS,
            "original-attempt-reference-1",
            "replayed-attempt-reference-1",
        ),
        (
            NotificationDeduplicationStage.PROVIDER_OUTCOME_RECORDING,
            NotificationChannelClass.MAX,
            NotificationSourceFamily.NO_NEW_LISTINGS_STATUS,
            "original-outcome-reference-1",
            "replayed-outcome-reference-1",
        ),
    ],
)
def test_terminal_replay_returns_original_reference_and_preserves_identity(
    *,
    stage: NotificationDeduplicationStage,
    channel_class: NotificationChannelClass | None,
    source_family: NotificationSourceFamily,
    original_reference: str,
    replayed_reference: str,
) -> None:
    request = _request(
        stage=stage,
        source_family=source_family,
        channel_class=channel_class,
        proposed_record_state=NotificationDeduplicationRecordState.TERMINAL,
        proposed_result_reference_id=replayed_reference,
        evidence_reference_ids=("request-1", "shared", "request-2", "request-1"),
    )
    existing_record = _record(
        request,
        record_state=NotificationDeduplicationRecordState.TERMINAL,
        protected_result_reference_id=original_reference,
        evidence_reference_ids=("existing-1", "shared", "existing-2", "existing-1"),
    )

    decision = evaluate_notification_deduplication(
        decision_id="decision-3",
        record_id="record-3",
        request=request,
        existing_record=existing_record,
        evidence_reference_ids=("command-1", "shared", "command-2", "command-1"),
    )

    assert decision.status is NotificationDeduplicationDecisionStatus.REPLAY_TERMINAL
    assert decision.existing_record is existing_record
    assert decision.resulting_record is existing_record
    assert decision.resulting_record.protected_result_reference_id == original_reference
    assert decision.effect_authorized is False
    assert decision.replayed is True
    assert decision.reconciliation_required is False
    assert decision.idempotency_decision is IdempotencyDecision.REPLAY_TERMINAL
    assert decision.reason_codes == ("dedup-replay-terminal",)
    assert decision.evidence_reference_ids == (
        "existing-1",
        "shared",
        "existing-2",
        "request-1",
        "request-2",
        "command-1",
        "command-2",
    )


def test_pending_replay_returns_original_attempt_reference() -> None:
    request = _request(
        stage=NotificationDeduplicationStage.ATTEMPT_CREATION,
        source_family=NotificationSourceFamily.NO_NEW_LISTINGS_STATUS,
        channel_class=NotificationChannelClass.TELEGRAM,
        proposed_record_state=NotificationDeduplicationRecordState.PENDING,
        proposed_result_reference_id="replayed-attempt-reference-2",
        evidence_reference_ids=("request-1", "shared", "request-2", "request-1"),
    )
    existing_record = _record(
        request,
        record_state=NotificationDeduplicationRecordState.PENDING,
        protected_result_reference_id="original-attempt-reference-2",
        evidence_reference_ids=("existing-1", "shared", "existing-2", "existing-1"),
    )

    decision = evaluate_notification_deduplication(
        decision_id="decision-4",
        record_id="record-4",
        request=request,
        existing_record=existing_record,
        evidence_reference_ids=("command-1", "shared", "command-2", "command-1"),
    )

    assert decision.status is NotificationDeduplicationDecisionStatus.REPLAY_PENDING
    assert decision.existing_record is existing_record
    assert decision.resulting_record is existing_record
    assert decision.resulting_record.protected_result_reference_id == "original-attempt-reference-2"
    assert decision.effect_authorized is False
    assert decision.replayed is True
    assert decision.reconciliation_required is False
    assert decision.idempotency_decision is IdempotencyDecision.PENDING
    assert decision.reason_codes == ("dedup-replay-pending",)
    assert decision.evidence_reference_ids == (
        "existing-1",
        "shared",
        "existing-2",
        "request-1",
        "request-2",
        "command-1",
        "command-2",
    )


def test_ambiguous_provider_outcome_replay_requires_reconciliation() -> None:
    request = _request(
        stage=NotificationDeduplicationStage.PROVIDER_OUTCOME_RECORDING,
        source_family=NotificationSourceFamily.EXTERNAL_UNAVAILABLE_STATUS,
        channel_class=NotificationChannelClass.MAX,
        proposed_record_state=NotificationDeduplicationRecordState.AMBIGUOUS,
        proposed_result_reference_id="replayed-outcome-reference-2",
        evidence_reference_ids=("request-1", "shared", "request-2", "request-1"),
    )
    existing_record = _record(
        request,
        record_state=NotificationDeduplicationRecordState.AMBIGUOUS,
        protected_result_reference_id="original-outcome-reference-2",
        evidence_reference_ids=("existing-1", "shared", "existing-2", "existing-1"),
    )

    decision = evaluate_notification_deduplication(
        decision_id="decision-5",
        record_id="record-5",
        request=request,
        existing_record=existing_record,
        evidence_reference_ids=("command-1", "shared", "command-2", "command-1"),
    )

    assert decision.status is NotificationDeduplicationDecisionStatus.RECONCILIATION_REQUIRED
    assert decision.existing_record is existing_record
    assert decision.resulting_record is existing_record
    assert decision.resulting_record.protected_result_reference_id == "original-outcome-reference-2"
    assert decision.effect_authorized is False
    assert decision.replayed is True
    assert decision.reconciliation_required is True
    assert decision.idempotency_decision is IdempotencyDecision.RECONCILE_REQUIRED
    assert decision.reason_codes == ("dedup-reconciliation-required",)
    assert decision.evidence_reference_ids == (
        "existing-1",
        "shared",
        "existing-2",
        "request-1",
        "request-2",
        "command-1",
        "command-2",
    )


@pytest.mark.parametrize(
    ("account_id", "beacon_id"),
    [
        ("account-2", "beacon-1"),
        ("account-1", "beacon-2"),
    ],
)
def test_same_key_and_fingerprint_do_not_cross_account_or_beacon(
    *,
    account_id: str,
    beacon_id: str,
) -> None:
    request = _request(
        stage=NotificationDeduplicationStage.ATTEMPT_CREATION,
        source_family=NotificationSourceFamily.NO_NEW_LISTINGS_STATUS,
        channel_class=NotificationChannelClass.TELEGRAM,
        account_id="account-1",
        beacon_id="beacon-1",
        semantic_effect_reference_id="semantic-effect-2",
        proposed_result_reference_id="replayed-attempt-reference-3",
    )
    existing_record = _record(
        request,
        record_state=NotificationDeduplicationRecordState.TERMINAL,
        protected_result_reference_id="original-attempt-reference-3",
    )
    mutated_request = _request(
        stage=NotificationDeduplicationStage.ATTEMPT_CREATION,
        source_family=NotificationSourceFamily.NO_NEW_LISTINGS_STATUS,
        channel_class=NotificationChannelClass.TELEGRAM,
        account_id=account_id,
        beacon_id=beacon_id,
        semantic_effect_reference_id="semantic-effect-2",
        proposed_result_reference_id="replayed-attempt-reference-3",
    )

    decision = evaluate_notification_deduplication(
        decision_id="decision-6",
        record_id="record-6",
        request=mutated_request,
        existing_record=existing_record,
        evidence_reference_ids=("command-1", "shared", "command-2", "command-1"),
    )

    assert decision.status is NotificationDeduplicationDecisionStatus.IDEMPOTENCY_MISMATCH
    assert decision.existing_record is existing_record
    assert decision.resulting_record is None
    assert decision.effect_authorized is False
    assert decision.replayed is False
    assert decision.reconciliation_required is False
    assert decision.idempotency_decision is IdempotencyDecision.MISMATCH
    assert decision.reason_codes == ("dedup-semantic-mismatch",)


def test_same_channel_scope_is_independent_between_telegram_and_max() -> None:
    request = _request(
        stage=NotificationDeduplicationStage.ATTEMPT_CREATION,
        source_family=NotificationSourceFamily.NO_NEW_LISTINGS_STATUS,
        channel_class=NotificationChannelClass.MAX,
        account_id="account-1",
        beacon_id="beacon-1",
        semantic_effect_reference_id="semantic-effect-3",
        proposed_result_reference_id="replayed-attempt-reference-4",
    )
    existing_record = _record(
        _request(
            stage=NotificationDeduplicationStage.ATTEMPT_CREATION,
            source_family=NotificationSourceFamily.NO_NEW_LISTINGS_STATUS,
            channel_class=NotificationChannelClass.TELEGRAM,
            account_id="account-1",
            beacon_id="beacon-1",
            semantic_effect_reference_id="semantic-effect-3",
            proposed_result_reference_id="original-attempt-reference-4",
        ),
        record_state=NotificationDeduplicationRecordState.TERMINAL,
        protected_result_reference_id="original-attempt-reference-4",
    )

    decision = evaluate_notification_deduplication(
        decision_id="decision-7",
        record_id="record-7",
        request=request,
        existing_record=existing_record,
        evidence_reference_ids=("command-1", "shared", "command-2", "command-1"),
    )

    assert decision.status is NotificationDeduplicationDecisionStatus.IDEMPOTENCY_MISMATCH
    assert decision.existing_record is existing_record
    assert decision.resulting_record is None
    assert decision.idempotency_decision is IdempotencyDecision.MISMATCH
    assert decision.reason_codes == ("dedup-semantic-mismatch",)


def test_same_key_with_different_fingerprint_is_rejected() -> None:
    request = _request(
        stage=NotificationDeduplicationStage.SOURCE_INTAKE,
        source_family=NotificationSourceFamily.RECOVERY_SCAN_COMPLETED,
        account_id="account-1",
        beacon_id="beacon-1",
        semantic_effect_reference_id="semantic-effect-4",
        proposed_result_reference_id="replayed-source-reference-4",
    )
    existing_record = _record(
        request,
        record_state=NotificationDeduplicationRecordState.TERMINAL,
        protected_result_reference_id="original-source-reference-4",
    )
    mutated_request = _request(
        stage=NotificationDeduplicationStage.SOURCE_INTAKE,
        source_family=NotificationSourceFamily.RECOVERY_SCAN_COMPLETED,
        account_id="account-1",
        beacon_id="beacon-1",
        semantic_effect_reference_id="semantic-effect-4",
        idempotency_fingerprint=_fingerprint("fingerprint-2"),
        proposed_result_reference_id="replayed-source-reference-4",
    )

    decision = evaluate_notification_deduplication(
        decision_id="decision-8",
        record_id="record-8",
        request=mutated_request,
        existing_record=existing_record,
        evidence_reference_ids=("command-1", "shared", "command-2", "command-1"),
    )

    assert decision.status is NotificationDeduplicationDecisionStatus.IDEMPOTENCY_MISMATCH
    assert decision.resulting_record is None
    assert decision.effect_authorized is False
    assert decision.replayed is False
    assert decision.reconciliation_required is False
    assert decision.idempotency_decision is IdempotencyDecision.MISMATCH
    assert decision.reason_codes == ("dedup-idempotency-fingerprint-mismatch",)


def test_same_key_different_semantic_effect_reference_is_rejected() -> None:
    request = _request(
        stage=NotificationDeduplicationStage.OUTBOX_CREATION,
        source_family=NotificationSourceFamily.EXTERNAL_UNAVAILABLE_STATUS,
        account_id="account-1",
        beacon_id="beacon-1",
        semantic_effect_reference_id="semantic-effect-5",
        proposed_result_reference_id="replayed-outbox-reference-5",
    )
    existing_record = _record(
        request,
        record_state=NotificationDeduplicationRecordState.TERMINAL,
        protected_result_reference_id="original-outbox-reference-5",
    )
    mutated_request = _request(
        stage=NotificationDeduplicationStage.OUTBOX_CREATION,
        source_family=NotificationSourceFamily.EXTERNAL_UNAVAILABLE_STATUS,
        account_id="account-1",
        beacon_id="beacon-1",
        semantic_effect_reference_id="semantic-effect-5-b",
        proposed_result_reference_id="replayed-outbox-reference-5",
    )

    decision = evaluate_notification_deduplication(
        decision_id="decision-9",
        record_id="record-9",
        request=mutated_request,
        existing_record=existing_record,
        evidence_reference_ids=("command-1", "shared", "command-2", "command-1"),
    )

    assert decision.status is NotificationDeduplicationDecisionStatus.IDEMPOTENCY_MISMATCH
    assert decision.resulting_record is None
    assert decision.idempotency_decision is IdempotencyDecision.MISMATCH
    assert decision.reason_codes == ("dedup-semantic-mismatch",)


def test_unrelated_record_key_or_scope_mismatch_raises_value_error() -> None:
    request = _request(
        stage=NotificationDeduplicationStage.OUTBOX_CREATION,
        source_family=NotificationSourceFamily.EXTERNAL_UNAVAILABLE_STATUS,
        account_id="account-1",
        beacon_id="beacon-1",
        semantic_effect_reference_id="semantic-effect-6",
        proposed_result_reference_id="replayed-outbox-reference-6",
    )

    mismatch_by_key = _record(
        _request(
            stage=NotificationDeduplicationStage.OUTBOX_CREATION,
            source_family=NotificationSourceFamily.EXTERNAL_UNAVAILABLE_STATUS,
            account_id="account-1",
            beacon_id="beacon-1",
            semantic_effect_reference_id="semantic-effect-6",
            idempotency_key=_key("other-key"),
            proposed_result_reference_id="original-outbox-reference-6",
        ),
        record_state=NotificationDeduplicationRecordState.TERMINAL,
        protected_result_reference_id="original-outbox-reference-6",
    )
    mismatch_by_scope = _record(
        _request(
            stage=NotificationDeduplicationStage.OUTBOX_CREATION,
            source_family=NotificationSourceFamily.EXTERNAL_UNAVAILABLE_STATUS,
            account_id="account-1",
            beacon_id="beacon-1",
            semantic_effect_reference_id="semantic-effect-6",
            idempotency_scope=_scope("other-scope"),
            proposed_result_reference_id="original-outbox-reference-6",
        ),
        record_state=NotificationDeduplicationRecordState.TERMINAL,
        protected_result_reference_id="original-outbox-reference-6",
    )

    with pytest.raises(ValueError):
        evaluate_notification_deduplication(
            decision_id="decision-10",
            record_id="record-10",
            request=request,
            existing_record=mismatch_by_key,
            evidence_reference_ids=("command-1",),
        )

    with pytest.raises(ValueError):
        evaluate_notification_deduplication(
            decision_id="decision-11",
            record_id="record-11",
            request=request,
            existing_record=mismatch_by_scope,
            evidence_reference_ids=("command-1",),
        )


def test_stage_scope_invariants_are_enforced() -> None:
    invalid_cases = [
        (
            NotificationDeduplicationStage.SOURCE_INTAKE,
            NotificationChannelClass.TELEGRAM,
        ),
        (
            NotificationDeduplicationStage.OUTBOX_CREATION,
            NotificationChannelClass.MAX,
        ),
        (
            NotificationDeduplicationStage.ATTEMPT_CREATION,
            NotificationChannelClass.WEB_STATUS_READ_MODEL,
        ),
        (
            NotificationDeduplicationStage.PROVIDER_OUTCOME_RECORDING,
            NotificationChannelClass.WEB_STATUS_READ_MODEL,
        ),
        (
            NotificationDeduplicationStage.ATTEMPT_CREATION,
            None,
        ),
    ]

    for stage, channel_class in invalid_cases:
        with pytest.raises(ValueError):
            _request(stage=stage, channel_class=channel_class)


def test_exact_platform_idempotency_types_are_required() -> None:
    with pytest.raises(ValueError):
        _request(
            stage=NotificationDeduplicationStage.SOURCE_INTAKE,
            idempotency_key=_KeySubclass(value="subclass-key"),
        )

    with pytest.raises(ValueError):
        _request(
            stage=NotificationDeduplicationStage.SOURCE_INTAKE,
            idempotency_key=cast(Any, _Lookalike("lookalike-key")),
        )

    with pytest.raises(ValueError):
        _request(
            stage=NotificationDeduplicationStage.SOURCE_INTAKE,
            idempotency_fingerprint=cast(Any, _Lookalike("lookalike-fingerprint")),
        )

    with pytest.raises(ValueError):
        _request(
            stage=NotificationDeduplicationStage.SOURCE_INTAKE,
            idempotency_scope=cast(Any, _Lookalike("lookalike-scope")),
        )


def test_existing_record_identity_is_preserved_on_replay() -> None:
    request = _request(
        stage=NotificationDeduplicationStage.ATTEMPT_CREATION,
        source_family=NotificationSourceFamily.NO_NEW_LISTINGS_STATUS,
        channel_class=NotificationChannelClass.TELEGRAM,
        semantic_effect_reference_id="semantic-effect-7",
        proposed_result_reference_id="replayed-attempt-reference-7",
    )
    existing_record = _record(
        request,
        record_state=NotificationDeduplicationRecordState.TERMINAL,
        protected_result_reference_id="original-attempt-reference-7",
    )

    decision = evaluate_notification_deduplication(
        decision_id="decision-12",
        record_id="record-12",
        request=request,
        existing_record=existing_record,
        evidence_reference_ids=("command-1", "shared", "command-2", "command-1"),
    )

    assert decision.existing_record is existing_record
    assert decision.resulting_record is existing_record
    assert decision.replayed is True
    assert decision.evidence_reference_ids == (
        "existing-1",
        "shared",
        "existing-2",
        "request-1",
        "request-2",
        "command-1",
        "command-2",
    )

# ruff: noqa: E501, F401, I001
from __future__ import annotations

from copy import deepcopy
from dataclasses import fields, is_dataclass
from typing import Any, cast

import pytest

from mayak.modules.notification_delivery.read_model import (
    NotificationDeliveryHistoryClassification,
    NotificationDeliveryHistoryEntry,
    NotificationDeliveryReadStatus,
    NotificationReadAudience,
    NotificationReadAuthorizationScope,
    NotificationReadModel,
    NotificationReadModelProjectionDecision,
    NotificationReadProjectionStatus,
    project_notification_read_model,
)
from mayak.modules.notification_delivery.batch import (
    NotificationBatchAuthority,
    NotificationBatchDecision,
    NotificationBatchDecisionStatus,
    NotificationBatchDisposition,
    NotificationBatchItemInput,
    NotificationBatchItemResult,
    NotificationBatchSafeErrorCategory,
    NotificationBatchStage,
)
from mayak.modules.notification_delivery.eligibility import NotificationChannelClass

ACCOUNT_ID = "account-nd12-1"
BEACON_ID = "beacon-nd12-1"
FOREIGN_BEACON_ID = "beacon-foreign-nd12"

_REASON_BY_DISPOSITION = {
    NotificationBatchDisposition.CREATED: ("batch-item-created",),
    NotificationBatchDisposition.REPLAYED: ("batch-item-replayed",),
    NotificationBatchDisposition.SUPPRESSED: ("batch-item-suppressed",),
    NotificationBatchDisposition.BLOCKED: ("batch-item-blocked",),
    NotificationBatchDisposition.DELIVERED: ("batch-item-delivered",),
    NotificationBatchDisposition.FAILED: ("batch-item-failed",),
    NotificationBatchDisposition.RECONCILIATION_REQUIRED: (
        "batch-item-reconciliation-required",
    ),
}

_ERROR_BY_DISPOSITION = {
    NotificationBatchDisposition.CREATED: NotificationBatchSafeErrorCategory.NONE,
    NotificationBatchDisposition.REPLAYED: NotificationBatchSafeErrorCategory.NONE,
    NotificationBatchDisposition.SUPPRESSED: NotificationBatchSafeErrorCategory.ELIGIBILITY_BLOCKED,
    NotificationBatchDisposition.BLOCKED: NotificationBatchSafeErrorCategory.CHANNEL_PLAN_BLOCKED,
    NotificationBatchDisposition.DELIVERED: NotificationBatchSafeErrorCategory.NONE,
    NotificationBatchDisposition.FAILED: NotificationBatchSafeErrorCategory.PROVIDER_FAILURE,
    NotificationBatchDisposition.RECONCILIATION_REQUIRED: (
        NotificationBatchSafeErrorCategory.AMBIGUOUS_RECONCILIATION
    ),
}


def _make_item_input(
    *,
    batch_item_id: str,
    evidence_reference_ids: tuple[str, ...],
) -> NotificationBatchItemInput:
    item_input = cast(Any, object.__new__(NotificationBatchItemInput))
    object.__setattr__(item_input, "batch_item_id", batch_item_id)
    object.__setattr__(item_input, "source_decision", f"{batch_item_id}-source-decision")
    object.__setattr__(item_input, "outbox_item_context", None)
    object.__setattr__(item_input, "evidence_reference_ids", evidence_reference_ids)
    return item_input


def _make_item_result(
    *,
    batch_item_id: str,
    disposition: NotificationBatchDisposition,
    account_id: str = ACCOUNT_ID,
    beacon_id: str | None = BEACON_ID,
    safe_listing_reference_ids: tuple[str, ...] = ("listing-1",),
    channel_class: NotificationChannelClass | None = NotificationChannelClass.TELEGRAM,
    outbox_item_id: str | None = "outbox-1",
    attempt_id: str | None = "attempt-1",
    replayed: bool = False,
    delivery_accepted: bool = False,
    reconciliation_required: bool = False,
    retry_policy_required: bool = False,
    evidence_reference_ids: tuple[str, ...] = ("item-evidence-1",),
) -> NotificationBatchItemResult:
    item_input = _make_item_input(
        batch_item_id=batch_item_id,
        evidence_reference_ids=(f"{batch_item_id}-input-evidence",),
    )
    item_result = cast(Any, object.__new__(NotificationBatchItemResult))
    object.__setattr__(item_result, "batch_item_id", batch_item_id)
    object.__setattr__(
        item_result,
        "authority",
        NotificationBatchAuthority.NOTIFICATION_DELIVERY_SERVER,
    )
    object.__setattr__(item_result, "item_input", item_input)
    object.__setattr__(item_result, "stage", NotificationBatchStage.PROVIDER_OUTCOME)
    object.__setattr__(item_result, "source_decision_id", f"{batch_item_id}-source-decision")
    object.__setattr__(item_result, "account_id", account_id)
    object.__setattr__(item_result, "beacon_id", beacon_id)
    object.__setattr__(item_result, "channel_class", channel_class)
    object.__setattr__(item_result, "outbox_item_id", outbox_item_id)
    object.__setattr__(item_result, "attempt_id", attempt_id)
    object.__setattr__(item_result, "safe_result_reference_id", f"{batch_item_id}-result")
    object.__setattr__(item_result, "safe_listing_reference_ids", safe_listing_reference_ids)
    object.__setattr__(item_result, "disposition", disposition)
    object.__setattr__(item_result, "safe_error_category", _ERROR_BY_DISPOSITION[disposition])
    object.__setattr__(item_result, "replayed", replayed)
    object.__setattr__(item_result, "delivery_accepted", delivery_accepted)
    object.__setattr__(item_result, "reconciliation_required", reconciliation_required)
    object.__setattr__(item_result, "retry_policy_required", retry_policy_required)
    object.__setattr__(item_result, "execution_authorized", False)
    object.__setattr__(item_result, "provider_mapping_authorized", False)
    object.__setattr__(item_result, "reason_codes", _REASON_BY_DISPOSITION[disposition])
    object.__setattr__(item_result, "evidence_reference_ids", evidence_reference_ids)
    return item_result


def _batch_status_for(item_results: tuple[NotificationBatchItemResult, ...]) -> NotificationBatchDecisionStatus:
    if any(item_result.disposition is NotificationBatchDisposition.RECONCILIATION_REQUIRED for item_result in item_results):
        return NotificationBatchDecisionStatus.RECONCILIATION_REQUIRED
    accepted_count = sum(
        item_result.disposition.name in {"CREATED", "REPLAYED", "DELIVERED"}
        for item_result in item_results
    )
    if accepted_count == len(item_results):
        return NotificationBatchDecisionStatus.ALL_ACCEPTED
    if accepted_count > 0:
        return NotificationBatchDecisionStatus.PARTIAL_OUTCOME
    return NotificationBatchDecisionStatus.ALL_BLOCKED_OR_FAILED


def _batch_reason_codes(status: NotificationBatchDecisionStatus) -> tuple[str, ...]:
    return {
        NotificationBatchDecisionStatus.ALL_ACCEPTED: ("batch-all-accepted",),
        NotificationBatchDecisionStatus.PARTIAL_OUTCOME: ("batch-partial-outcome",),
        NotificationBatchDecisionStatus.ALL_BLOCKED_OR_FAILED: ("batch-all-blocked-or-failed",),
        NotificationBatchDecisionStatus.RECONCILIATION_REQUIRED: (
            "batch-reconciliation-required",
        ),
    }[status]


def _make_batch_decision(
    *,
    batch_id: str = "batch-nd12-1",
    item_results: tuple[NotificationBatchItemResult, ...],
    account_id: str = ACCOUNT_ID,
    evidence_reference_ids: tuple[str, ...] = ("batch-evidence-1",),
) -> NotificationBatchDecision:
    item_inputs = tuple(item_result.item_input for item_result in item_results)
    status = _batch_status_for(item_results)
    batch_decision = cast(Any, object.__new__(NotificationBatchDecision))
    object.__setattr__(batch_decision, "batch_id", batch_id)
    object.__setattr__(
        batch_decision,
        "authority",
        NotificationBatchAuthority.NOTIFICATION_DELIVERY_SERVER,
    )
    object.__setattr__(batch_decision, "account_id", account_id)
    object.__setattr__(batch_decision, "item_inputs", item_inputs)
    object.__setattr__(batch_decision, "item_results", item_results)
    object.__setattr__(batch_decision, "status", status)
    object.__setattr__(batch_decision, "item_count", len(item_results))
    accepted_count = sum(
        item_result.disposition.name in {"CREATED", "REPLAYED", "DELIVERED"}
        for item_result in item_results
    )
    object.__setattr__(batch_decision, "accepted_count", accepted_count)
    object.__setattr__(
        batch_decision,
        "created_count",
        sum(item_result.disposition is NotificationBatchDisposition.CREATED for item_result in item_results),
    )
    object.__setattr__(
        batch_decision,
        "replayed_count",
        sum(item_result.disposition is NotificationBatchDisposition.REPLAYED for item_result in item_results),
    )
    object.__setattr__(
        batch_decision,
        "suppressed_count",
        sum(item_result.disposition is NotificationBatchDisposition.SUPPRESSED for item_result in item_results),
    )
    object.__setattr__(
        batch_decision,
        "blocked_count",
        sum(item_result.disposition is NotificationBatchDisposition.BLOCKED for item_result in item_results),
    )
    object.__setattr__(
        batch_decision,
        "delivered_count",
        sum(item_result.disposition is NotificationBatchDisposition.DELIVERED for item_result in item_results),
    )
    object.__setattr__(
        batch_decision,
        "failed_count",
        sum(item_result.disposition is NotificationBatchDisposition.FAILED for item_result in item_results),
    )
    object.__setattr__(
        batch_decision,
        "reconciliation_count",
        sum(
            item_result.disposition is NotificationBatchDisposition.RECONCILIATION_REQUIRED
            for item_result in item_results
        ),
    )
    object.__setattr__(
        batch_decision,
        "retry_policy_required_count",
        sum(item_result.retry_policy_required for item_result in item_results),
    )
    object.__setattr__(batch_decision, "listing_references_preserved", True)
    object.__setattr__(batch_decision, "per_item_outcomes_exposed", True)
    object.__setattr__(batch_decision, "execution_authorized", False)
    object.__setattr__(batch_decision, "provider_mapping_authorized", False)
    object.__setattr__(batch_decision, "reason_codes", _batch_reason_codes(status))
    object.__setattr__(
        batch_decision,
        "evidence_reference_ids",
        tuple(
            dict.fromkeys(
                (*evidence_reference_ids, *tuple(ref for result in item_results for ref in result.evidence_reference_ids))
            )
        ),
    )
    return batch_decision


def _make_scope(
    *,
    audience: NotificationReadAudience,
    authorized: bool = True,
    account_id: str = ACCOUNT_ID,
    beacon_scope_ids: tuple[str, ...] = (BEACON_ID,),
) -> NotificationReadAuthorizationScope:
    return NotificationReadAuthorizationScope(
        scope_id=f"scope-{audience.value.lower()}",
        audience=audience,
        authorized=authorized,
        account_id=account_id,
        beacon_scope_ids=beacon_scope_ids,
        authorization_reference_id=f"auth-{audience.value.lower()}",
        evidence_reference_ids=(f"scope-{audience.value.lower()}-evidence-1",),
        freshness_reference_ids=(f"scope-{audience.value.lower()}-freshness-1",),
        provenance_reference_ids=(f"scope-{audience.value.lower()}-provenance-1",),
    )


def _project(
    *,
    audience: NotificationReadAudience,
    batch_decision: NotificationBatchDecision,
    authorized: bool = True,
    account_id: str = ACCOUNT_ID,
    beacon_scope_ids: tuple[str, ...] = (BEACON_ID,),
) -> NotificationReadModelProjectionDecision:
    return project_notification_read_model(
        decision_id=f"{batch_decision.batch_id}-{audience.value.lower()}-projection",
        authorization_scope=_make_scope(
            audience=audience,
            authorized=authorized,
            account_id=account_id,
            beacon_scope_ids=beacon_scope_ids,
        ),
        source_batch_decision=batch_decision,
        evidence_reference_ids=(f"{batch_decision.batch_id}-{audience.value.lower()}-projection-evidence",),
    )


def _single_item_batch(
    disposition: NotificationBatchDisposition,
    *,
    batch_item_id: str = "item-1",
    account_id: str = ACCOUNT_ID,
    beacon_id: str | None = BEACON_ID,
    safe_listing_reference_ids: tuple[str, ...] = ("listing-1", "listing-2"),
    channel_class: NotificationChannelClass | None = NotificationChannelClass.TELEGRAM,
    outbox_item_id: str | None = "outbox-1",
    attempt_id: str | None = "attempt-1",
    replayed: bool = False,
    delivery_accepted: bool = False,
    reconciliation_required: bool = False,
    retry_policy_required: bool = False,
    evidence_reference_ids: tuple[str, ...] = ("item-evidence-1",),
) -> NotificationBatchDecision:
    return _make_batch_decision(
        batch_id=f"{batch_item_id}-batch",
        item_results=(
            _make_item_result(
                batch_item_id=batch_item_id,
                disposition=disposition,
                account_id=account_id,
                beacon_id=beacon_id,
                safe_listing_reference_ids=safe_listing_reference_ids,
                channel_class=channel_class,
                outbox_item_id=outbox_item_id,
                attempt_id=attempt_id,
                replayed=replayed,
                delivery_accepted=delivery_accepted,
                reconciliation_required=reconciliation_required,
                retry_policy_required=retry_policy_required,
                evidence_reference_ids=evidence_reference_ids,
            ),
        ),
        account_id=account_id,
        evidence_reference_ids=(f"{batch_item_id}-batch-evidence",),
    )


def test_user_admin_and_support_audiences_project_successfully() -> None:
    batch_decision = _single_item_batch(NotificationBatchDisposition.DELIVERED)
    for audience in (
        NotificationReadAudience.USER,
        NotificationReadAudience.ADMIN,
        NotificationReadAudience.SUPPORT,
    ):
        projection = _project(audience=audience, batch_decision=batch_decision)
        assert type(projection) is NotificationReadModelProjectionDecision
        assert projection.status is NotificationReadProjectionStatus.PROJECTED
        assert projection.read_model.audience is audience
        assert projection.read_model.execution_authorized is False
        assert projection.read_model.provider_mapping_authorized is False
        assert projection.read_model.mutation_authorized is False
        assert projection.read_model.read_tracking_authorized is False
        assert projection.read_model.click_tracking_authorized is False
        assert projection.read_model.retention_authorized is False


def test_authorized_same_account_projection_preserves_input_objects() -> None:
    batch_decision = _make_batch_decision(
        batch_id="batch-mixed",
        item_results=(
            _make_item_result(
                batch_item_id="item-delivered",
                disposition=NotificationBatchDisposition.DELIVERED,
                safe_listing_reference_ids=("listing-a", "listing-b"),
                channel_class=NotificationChannelClass.TELEGRAM,
                outbox_item_id="outbox-delivered",
                attempt_id="attempt-delivered",
                delivery_accepted=True,
                evidence_reference_ids=("delivered-evidence-1",),
            ),
            _make_item_result(
                batch_item_id="item-failed",
                disposition=NotificationBatchDisposition.FAILED,
                safe_listing_reference_ids=("listing-c", "listing-d"),
                channel_class=NotificationChannelClass.MAX,
                outbox_item_id="outbox-failed",
                attempt_id="attempt-failed",
                retry_policy_required=True,
                evidence_reference_ids=("failed-evidence-1",),
            ),
        ),
    )
    scope = _make_scope(audience=NotificationReadAudience.SUPPORT, beacon_scope_ids=(BEACON_ID,))
    batch_before = deepcopy(batch_decision)
    scope_before = deepcopy(scope)

    projection = project_notification_read_model(
        decision_id="projection-mixed-1",
        authorization_scope=scope,
        source_batch_decision=batch_decision,
        evidence_reference_ids=("projection-evidence-1",),
    )

    assert batch_decision == batch_before
    assert scope == scope_before
    assert projection.read_model.history_entry_count == 2
    assert tuple(entry.delivery_status for entry in projection.read_model.history_entries) == (
        NotificationDeliveryReadStatus.DELIVERED,
        NotificationDeliveryReadStatus.FAILED,
    )
    assert projection.read_model.safe_listing_reference_ids == (
        "listing-a",
        "listing-b",
        "listing-c",
        "listing-d",
    )
    assert projection.read_model.failure_visible is True
    assert projection.read_model.reconciliation_required is False
    assert projection.status is NotificationReadProjectionStatus.PROJECTED


def test_unauthorized_projection_fails_closed() -> None:
    batch_decision = _single_item_batch(NotificationBatchDisposition.DELIVERED)
    with pytest.raises(ValueError, match="authorization scope must be authorized"):
        _project(
            audience=NotificationReadAudience.USER,
            batch_decision=batch_decision,
            authorized=False,
        )


def test_account_mismatch_fails_closed_without_foreign_details() -> None:
    batch_decision = _single_item_batch(NotificationBatchDisposition.DELIVERED)
    with pytest.raises(ValueError, match="authorization scope does not match the batch decision") as exc_info:
        _project(
            audience=NotificationReadAudience.USER,
            batch_decision=batch_decision,
            account_id="foreign-account",
        )
    assert "foreign-account" not in str(exc_info.value)


def test_beacon_scope_filtering_blocks_out_of_scope_beacon() -> None:
    batch_decision = _single_item_batch(
        NotificationBatchDisposition.DELIVERED,
        beacon_id=FOREIGN_BEACON_ID,
    )
    with pytest.raises(ValueError, match="authorization scope does not cover the batch beacons"):
        _project(
            audience=NotificationReadAudience.ADMIN,
            batch_decision=batch_decision,
            beacon_scope_ids=(BEACON_ID,),
        )


def test_duplicate_identity_rejection_happens_before_projection() -> None:
    duplicate_result = _make_item_result(
        batch_item_id="duplicate-item",
        disposition=NotificationBatchDisposition.DELIVERED,
        safe_listing_reference_ids=("listing-1",),
        evidence_reference_ids=("duplicate-evidence-1",),
    )
    batch_decision = _make_batch_decision(
        batch_id="duplicate-batch",
        item_results=(duplicate_result, duplicate_result),
    )
    with pytest.raises(ValueError, match="duplicate batch item identities are not allowed"):
        _project(audience=NotificationReadAudience.USER, batch_decision=batch_decision)


@pytest.mark.parametrize(
    ("disposition", "expected_status"),
    [
        (NotificationBatchDisposition.CREATED, NotificationDeliveryReadStatus.PLANNED),
        (NotificationBatchDisposition.REPLAYED, NotificationDeliveryReadStatus.REPLAYED),
        (NotificationBatchDisposition.SUPPRESSED, NotificationDeliveryReadStatus.SUPPRESSED),
        (NotificationBatchDisposition.BLOCKED, NotificationDeliveryReadStatus.BLOCKED),
        (NotificationBatchDisposition.DELIVERED, NotificationDeliveryReadStatus.DELIVERED),
        (NotificationBatchDisposition.FAILED, NotificationDeliveryReadStatus.FAILED),
        (
            NotificationBatchDisposition.RECONCILIATION_REQUIRED,
            NotificationDeliveryReadStatus.RECONCILIATION_REQUIRED,
        ),
    ],
)
def test_exact_disposition_to_status_mapping(
    disposition: NotificationBatchDisposition,
    expected_status: NotificationDeliveryReadStatus,
) -> None:
    projection = _project(
        audience=NotificationReadAudience.SUPPORT,
        batch_decision=_single_item_batch(
            disposition,
            replayed=disposition is NotificationBatchDisposition.REPLAYED,
            delivery_accepted=disposition is NotificationBatchDisposition.DELIVERED,
            reconciliation_required=disposition
            is NotificationBatchDisposition.RECONCILIATION_REQUIRED,
            retry_policy_required=disposition is NotificationBatchDisposition.FAILED,
            channel_class=None
            if disposition in {
                NotificationBatchDisposition.CREATED,
                NotificationBatchDisposition.SUPPRESSED,
                NotificationBatchDisposition.BLOCKED,
            }
            else NotificationChannelClass.TELEGRAM,
            outbox_item_id=None
            if disposition in {
                NotificationBatchDisposition.SUPPRESSED,
                NotificationBatchDisposition.BLOCKED,
            }
            else "outbox-1",
            attempt_id=None
            if disposition
            in {
                NotificationBatchDisposition.CREATED,
                NotificationBatchDisposition.SUPPRESSED,
                NotificationBatchDisposition.BLOCKED,
            }
            else "attempt-1",
        ),
    )
    assert projection.read_model.history_entry_count == 1
    assert projection.read_model.history_entries[0].delivery_status is expected_status
    assert projection.read_model.history_entries[0].history_classification.value == expected_status.value


def test_delivered_and_failed_mixed_result_remains_partial_and_visible() -> None:
    projection = _project(
        audience=NotificationReadAudience.ADMIN,
        batch_decision=_make_batch_decision(
            batch_id="batch-partial",
            item_results=(
                _make_item_result(
                    batch_item_id="item-delivered",
                    disposition=NotificationBatchDisposition.DELIVERED,
                    safe_listing_reference_ids=("listing-a", "listing-b"),
                    channel_class=NotificationChannelClass.TELEGRAM,
                    outbox_item_id="outbox-delivered",
                    attempt_id="attempt-delivered",
                    delivery_accepted=True,
                    evidence_reference_ids=("delivered-evidence-1",),
                ),
                _make_item_result(
                    batch_item_id="item-failed",
                    disposition=NotificationBatchDisposition.FAILED,
                    safe_listing_reference_ids=("listing-c", "listing-d"),
                    channel_class=NotificationChannelClass.MAX,
                    outbox_item_id="outbox-failed",
                    attempt_id="attempt-failed",
                    retry_policy_required=True,
                    evidence_reference_ids=("failed-evidence-1",),
                ),
            ),
        ),
    )
    assert projection.status is NotificationReadProjectionStatus.PROJECTED
    assert tuple(entry.delivery_status for entry in projection.read_model.history_entries) == (
        NotificationDeliveryReadStatus.DELIVERED,
        NotificationDeliveryReadStatus.FAILED,
    )
    assert projection.read_model.failure_visible is True
    assert projection.read_model.replay_visible is False
    assert projection.read_model.ambiguous_visible is False
    assert projection.read_model.reconciliation_required is False
    assert projection.read_model.safe_listing_reference_ids == (
        "listing-a",
        "listing-b",
        "listing-c",
        "listing-d",
    )


def test_replay_remains_replay_not_new_delivery() -> None:
    projection = _project(
        audience=NotificationReadAudience.SUPPORT,
        batch_decision=_single_item_batch(
            NotificationBatchDisposition.REPLAYED,
            replayed=True,
            outbox_item_id="outbox-replay",
            attempt_id="attempt-replay",
            evidence_reference_ids=("replay-evidence-1",),
        ),
    )
    entry = projection.read_model.history_entries[0]
    assert entry.delivery_status is NotificationDeliveryReadStatus.REPLAYED
    assert entry.history_classification is NotificationDeliveryHistoryClassification.REPLAYED
    assert entry.delivery_status is not NotificationDeliveryReadStatus.DELIVERED
    assert projection.read_model.replay_visible is True


def test_ambiguous_outcome_remains_reconciliation_required() -> None:
    projection = _project(
        audience=NotificationReadAudience.USER,
        batch_decision=_single_item_batch(
            NotificationBatchDisposition.RECONCILIATION_REQUIRED,
            reconciliation_required=True,
            retry_policy_required=False,
            outbox_item_id="outbox-ambiguous",
            attempt_id="attempt-ambiguous",
            evidence_reference_ids=("ambiguous-evidence-1",),
        ),
    )
    entry = projection.read_model.history_entries[0]
    assert entry.delivery_status is NotificationDeliveryReadStatus.RECONCILIATION_REQUIRED
    assert entry.history_classification is NotificationDeliveryHistoryClassification.RECONCILIATION_REQUIRED
    assert projection.status is NotificationReadProjectionStatus.RECONCILIATION_REQUIRED
    assert projection.read_model.reconciliation_required is True
    assert projection.read_model.ambiguous_visible is True


def test_all_safe_listing_references_are_preserved_without_preview_truncation() -> None:
    projection = _project(
        audience=NotificationReadAudience.ADMIN,
        batch_decision=_make_batch_decision(
            batch_id="batch-listings",
            item_results=(
                _make_item_result(
                    batch_item_id="item-1",
                    disposition=NotificationBatchDisposition.DELIVERED,
                    safe_listing_reference_ids=("listing-a", "listing-b"),
                    evidence_reference_ids=("listings-evidence-1",),
                ),
                _make_item_result(
                    batch_item_id="item-2",
                    disposition=NotificationBatchDisposition.FAILED,
                    safe_listing_reference_ids=("listing-c", "listing-d"),
                    evidence_reference_ids=("listings-evidence-2",),
                ),
            ),
        ),
    )
    assert projection.read_model.safe_listing_reference_ids == (
        "listing-a",
        "listing-b",
        "listing-c",
        "listing-d",
    )
    assert all(
        entry.safe_listing_reference_ids
        == expected
        for entry, expected in zip(
            projection.read_model.history_entries,
            (("listing-a", "listing-b"), ("listing-c", "listing-d")),
            strict=True,
        )
    )
    assert not any("preview" in field.name for field in fields(NotificationReadModel))


def test_provider_safe_errors_only_and_no_raw_payload_fields() -> None:
    projection = _project(
        audience=NotificationReadAudience.USER,
        batch_decision=_single_item_batch(
            NotificationBatchDisposition.FAILED,
            retry_policy_required=True,
            evidence_reference_ids=("failure-evidence-1",),
        ),
    )
    entry = projection.read_model.history_entries[0]
    assert entry.provider_safe_error_category is NotificationBatchSafeErrorCategory.PROVIDER_FAILURE
    assert entry.safe_reason_codes == ("batch-item-failed",)
    assert not hasattr(entry, "raw_payload")
    assert not hasattr(entry, "provider_payload")
    assert not hasattr(entry, "token")
    assert not hasattr(entry, "secret")


def test_output_flags_prove_non_authority_boundary() -> None:
    projection = _project(
        audience=NotificationReadAudience.SUPPORT,
        batch_decision=_single_item_batch(NotificationBatchDisposition.DELIVERED),
    )
    entry = projection.read_model.history_entries[0]
    for value in (
        projection.read_model.execution_authorized,
        projection.read_model.provider_mapping_authorized,
        projection.read_model.mutation_authorized,
        projection.read_model.read_tracking_authorized,
        projection.read_model.click_tracking_authorized,
        projection.read_model.retention_authorized,
        projection.execution_authorized,
        projection.provider_mapping_authorized,
        projection.mutation_authorized,
        projection.read_tracking_authorized,
        projection.click_tracking_authorized,
        projection.retention_authorized,
        entry.execution_authorized,
        entry.provider_mapping_authorized,
        entry.mutation_authorized,
        entry.read_tracking_authorized,
        entry.click_tracking_authorized,
        entry.retention_authorized,
    ):
        assert value is False


def test_exact_enum_and_tuple_validation_rejects_invalid_input() -> None:
    with pytest.raises(ValueError, match="beacon_scope_ids must be a tuple"):
        NotificationReadAuthorizationScope(
            scope_id="scope-1",
            audience=NotificationReadAudience.USER,
            authorized=True,
            account_id=ACCOUNT_ID,
            beacon_scope_ids=[BEACON_ID],  # type: ignore[list-item]
            authorization_reference_id="auth-1",
            evidence_reference_ids=("scope-evidence-1",),
            freshness_reference_ids=("scope-freshness-1",),
            provenance_reference_ids=("scope-provenance-1",),
        )

    with pytest.raises(ValueError, match="delivery_status must be NotificationDeliveryReadStatus"):
        NotificationDeliveryHistoryEntry(
            history_entry_id="history-1",
            batch_item_id="batch-item-1",
            account_id=ACCOUNT_ID,
            beacon_id=BEACON_ID,
            source_decision_id="source-decision-1",
            outbox_item_id="outbox-1",
            attempt_id="attempt-1",
            channel_class=NotificationChannelClass.TELEGRAM,
            delivery_status="PLANNED",  # type: ignore[arg-type]
            history_classification=NotificationDeliveryHistoryClassification.PLANNED,
            reconciliation_required=False,
            retry_policy_required=False,
            provider_safe_error_category=NotificationBatchSafeErrorCategory.NONE,
            safe_reason_codes=("reason-1",),
            safe_listing_reference_ids=("listing-1",),
            listing_count=1,
            evidence_reference_ids=("evidence-1",),
            freshness_reference_ids=("freshness-1",),
            provenance_reference_ids=("provenance-1",),
            audience=NotificationReadAudience.USER,
            mutation_authorized=False,
            execution_authorized=False,
            provider_mapping_authorized=False,
            read_tracking_authorized=False,
            click_tracking_authorized=False,
            retention_authorized=False,
        )


def test_projection_decision_and_read_model_are_frozen_slots_dataclasses() -> None:
    projection = _project(
        audience=NotificationReadAudience.USER,
        batch_decision=_single_item_batch(NotificationBatchDisposition.DELIVERED),
    )
    assert type(projection) is NotificationReadModelProjectionDecision
    assert type(projection.read_model) is NotificationReadModel
    assert is_dataclass(type(projection))
    assert is_dataclass(type(projection.read_model))
    with pytest.raises(Exception):
        projection.decision_id = "mutated"  # type: ignore[misc]

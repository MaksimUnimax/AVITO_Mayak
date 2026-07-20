from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from mayak.contracts import ContractMetadata
from mayak.modules.notification_delivery import (
    NotificationListingCard,
    NotificationListingCardFieldFact,
    NotificationListingCardProjectionDecision,
)
from mayak.modules.telegram_adapter import (
    TelegramDisplayActionReference,
    TelegramDisplayClass,
    TelegramListingCardDisplaySnapshot,
    TelegramSafeListingFieldFact,
)


def metadata() -> ContractMetadata:
    return ContractMetadata(
        contract_name="telegram.display.projection",
        contract_version="1",
        message_id=uuid4(),
        correlation_id=uuid4(),
        producer="telegram-adapter",
    )


def _project_notification_field(
    upstream: NotificationListingCardFieldFact,
) -> TelegramSafeListingFieldFact:
    """Test-only compatibility projector: public fields and exact enum values only."""
    if type(upstream) is not NotificationListingCardFieldFact:
        raise TypeError("upstream field schema drift")
    values = {
        name: getattr(upstream, name)
        for name in (
            "field_fact_id",
            "listing_reference_id",
            "field_class",
            "value_class",
            "safe_value",
            "upstream_field_family",
            "provenance_tier",
            "upstream_field_reference_id",
            "compatibility_profile_reference_id",
            "source_committed",
            "source_commit_reference",
            "field_evidence_approved",
            "detail_gate_approved",
            "contact_gate_approved",
            "contains_raw_provider_payload",
            "evidence_reference_ids",
        )
    }
    assert all(
        hasattr(value, "value")
        for value in (
            values["field_class"],
            values["value_class"],
            values["provenance_tier"],
        )
    )
    return TelegramSafeListingFieldFact(
        telegram_safe_listing_field_fact_id=values["field_fact_id"],
        listing_reference_id=values["listing_reference_id"],
        field_class=values["field_class"].value,
        value_class=values["value_class"].value,
        safe_value=values["safe_value"],
        upstream_field_family=values["upstream_field_family"],
        provenance_tier=values["provenance_tier"].value,
        upstream_field_reference_id=values["upstream_field_reference_id"],
        compatibility_profile_reference_id=values["compatibility_profile_reference_id"],
        source_committed=values["source_committed"],
        source_commit_reference=values["source_commit_reference"],
        field_evidence_approved=values["field_evidence_approved"],
        detail_gate_approved=values["detail_gate_approved"],
        contact_gate_approved=values["contact_gate_approved"],
        contains_raw_provider_payload=values["contains_raw_provider_payload"],
        evidence_reference_ids=values["evidence_reference_ids"],
    )


def _project_notification_decision(
    upstream: NotificationListingCardProjectionDecision,
) -> tuple[NotificationListingCard, ...]:
    """Test-only projector boundary; production never imports Notification Delivery."""
    if type(upstream) is not NotificationListingCardProjectionDecision:
        raise TypeError("upstream decision schema drift")
    if not all(hasattr(card, "listing_card_id") for card in upstream.cards):
        raise TypeError("upstream card schema drift")
    return upstream.cards


def field(**changes: object) -> TelegramSafeListingFieldFact:
    values: dict[str, object] = {
        "telegram_safe_listing_field_fact_id": "field-1",
        "listing_reference_id": "listing-1",
        "field_class": "TITLE",
        "value_class": "SAFE_TEXT",
        "safe_value": "safe title",
        "upstream_field_family": "TITLE",
        "provenance_tier": "TIER_1_SEARCH_RESULT",
        "upstream_field_reference_id": "upstream-field-1",
        "compatibility_profile_reference_id": "compatibility-1",
        "source_committed": True,
        "source_commit_reference": "commit-1",
        "field_evidence_approved": True,
        "detail_gate_approved": False,
        "contact_gate_approved": False,
        "evidence_reference_ids": ("evidence-1",),
    }
    values.update(changes)
    return TelegramSafeListingFieldFact(**values)  # type: ignore[arg-type]


def card(**changes: object) -> TelegramListingCardDisplaySnapshot:
    values: dict[str, object] = {
        "telegram_listing_card_display_snapshot_id": "card-1",
        "listing_card_reference_id": "listing-card-1",
        "listing_reference_id": "listing-1",
        "account_reference_id": "account-1",
        "beacon_reference_id": "beacon-1",
        "source_event_reference_id": "event-1",
        "source_fact_reference_id": "fact-1",
        "source_family": "NEW_LISTINGS_FOUND",
        "reason_class": "NEW_LISTING",
        "beacon_name_reference_id": None,
        "field_facts": (field(),),
        "correlation_id": "correlation-1",
        "causation_id": "causation-1",
        "evidence_reference_ids": ("card-evidence-1",),
    }
    values.update(changes)
    return TelegramListingCardDisplaySnapshot(**values)  # type: ignore[arg-type]


def test_enum_order_and_safe_field_compatibility_matrix() -> None:
    assert [item.value for item in TelegramDisplayClass] == [
        "NEW_LISTINGS_SUMMARY",
        "NEW_LISTINGS_COMPACT_LIST",
        "FULL_RESULT_OPEN_ACTION",
        "SHOW_MORE_ACTION",
        "BEACON_SETTINGS_ACTION",
        "NO_NEW_STATUS_MESSAGE",
        "AVITO_UNAVAILABLE_STATUS_MESSAGE",
        "RECOVERY_RESULT_MESSAGE",
        "LOST_ANCHORS_RESTORED_MESSAGE",
        "UNSUPPORTED_CONTENT_BLOCKED",
    ]
    assert field().safe_field_snapshot_only is True
    with pytest.raises(ValidationError):
        field(source_committed=False)
    with pytest.raises(ValidationError):
        field(contains_raw_provider_payload=True)
    with pytest.raises(ValidationError):
        field(value_class="SAFE_REFERENCE")


def test_optional_and_detail_contact_gates_are_safe() -> None:
    assert card(field_facts=()).field_facts == ()
    with pytest.raises(ValidationError):
        field(
            field_class="PHONE",
            upstream_field_family="PHONE_VALUE",
            provenance_tier="TIER_3_CONTACT",
            contact_gate_approved=False,
        )
    assert (
        TelegramDisplayActionReference(
            telegram_display_action_reference_id="action-1",
            action_class=TelegramDisplayClass.SHOW_MORE_ACTION,
            context_owner="NOTIFICATION_DELIVERY",
            source_subject_reference_id="outbox-1",
            safe_context_reference_id="opaque-context-1",
            action_policy_reference_id="policy-1",
            evidence_reference_ids=("action-evidence-1",),
        ).callback_payload_defined
        is False
    )


def test_snapshot_rejects_foreign_shapes_and_duplicate_field_classes() -> None:
    with pytest.raises(ValidationError):
        card(field_facts=[field()])
    with pytest.raises(ValidationError):
        card(field_facts=(field(), field(telegram_safe_listing_field_fact_id="field-2")))

# ruff: noqa: E501, F401, I001
from __future__ import annotations

from copy import deepcopy

import pytest

from mayak.contracts.idempotency import IdempotencyFingerprint, IdempotencyKey, IdempotencyScope
from mayak.modules.avito_parser_adapter.contracts import ListingFieldFamily, ListingFieldTier
from mayak.modules.notification_delivery.listing_card import (
    NotificationListingCard,
    NotificationListingCardAuthority,
    NotificationListingCardFieldClass,
    NotificationListingCardFieldFact,
    NotificationListingCardInput,
    NotificationListingCardProvenanceTier,
    NotificationListingCardProjectionDecision,
    NotificationListingCardProjectionStatus,
    NotificationListingCardReasonClass,
    NotificationListingCardValueClass,
    NotificationSourceFamily,
    NotificationSourceIntakeAuthority,
    NotificationSourceIntakeDecision,
    NotificationSourceIntakeStatus,
    NotificationSourceProducer,
    project_notification_listing_cards,
)
from mayak.modules.notification_delivery.source_intake import (
    NotificationSourceEvent,
    evaluate_notification_source_intake,
)

ACCOUNT_ID = "account-nd10-1"
BEACON_ID = "beacon-nd10-1"
SCAN_RUN_ID = "scan-run-nd10-1"
SOURCE_EVENT_ID = "source-event-nd10-1"
SOURCE_FACT_ID = "source-fact-nd10-1"
SOURCE_CONTRACT = "scan.notification.v1"
SOURCE_CONTRACT_VERSION = "1.0"
SOURCE_COMMIT_REFERENCE = "commit-nd10-1"
SOURCE_EVIDENCE_REFERENCE_IDS = ("source-evidence-1", "source-evidence-2")
INTAKE_EVIDENCE_REFERENCE_IDS = ("intake-evidence-1", "shared-evidence")
CARD_EVIDENCE_REFERENCE_IDS = ("card-evidence-1", "shared-evidence")
FIELD_EVIDENCE_REFERENCE_IDS = ("field-evidence-1", "shared-field-evidence")
FUNCTION_EVIDENCE_REFERENCE_IDS = ("function-evidence-1", "shared-function-evidence")


def _source_event(
    *,
    family: NotificationSourceFamily = NotificationSourceFamily.NEW_LISTINGS_FOUND,
    listing_count: int = 1,
    safe_listing_reference_ids: tuple[str, ...] = ("listing-1",),
    producer: NotificationSourceProducer = NotificationSourceProducer.SCAN_ORCHESTRATION,
    committed: bool = True,
    commit_reference: str | None = SOURCE_COMMIT_REFERENCE,
    source_identity_ambiguous: bool = False,
    contains_raw_provider_payload: bool = False,
    beacon_id: str | None = BEACON_ID,
    scan_run_id: str | None = SCAN_RUN_ID,
    evidence_reference_ids: tuple[str, ...] = SOURCE_EVIDENCE_REFERENCE_IDS,
) -> NotificationSourceEvent:
    return NotificationSourceEvent(
        source_event_id=SOURCE_EVENT_ID,
        source_family=family,
        source_producer=producer,
        source_contract=SOURCE_CONTRACT,
        source_contract_version=SOURCE_CONTRACT_VERSION,
        source_fact_id=SOURCE_FACT_ID,
        source_committed=committed,
        source_commit_reference=commit_reference,
        account_id=ACCOUNT_ID,
        beacon_id=beacon_id,
        scan_run_id=scan_run_id,
        listing_count=listing_count,
        safe_listing_reference_ids=safe_listing_reference_ids,
        correlation_id="correlation-nd10-1",
        causation_id="causation-nd10-1",
        idempotency_key=IdempotencyKey(value="idempotency-key-nd10-1"),
        idempotency_fingerprint=IdempotencyFingerprint(value="idempotency-fingerprint-nd10-1"),
        idempotency_scope=IdempotencyScope(value="idempotency-scope-nd10-1"),
        source_identity_ambiguous=source_identity_ambiguous,
        contains_raw_provider_payload=contains_raw_provider_payload,
        service_access_gate_approved=False,
        evidence_reference_ids=evidence_reference_ids,
    )


def _evaluated_intake_decision(
    *,
    family: NotificationSourceFamily = NotificationSourceFamily.NEW_LISTINGS_FOUND,
    listing_count: int = 1,
    safe_listing_reference_ids: tuple[str, ...] = ("listing-1",),
    producer: NotificationSourceProducer = NotificationSourceProducer.SCAN_ORCHESTRATION,
    committed: bool = True,
    commit_reference: str | None = SOURCE_COMMIT_REFERENCE,
    source_identity_ambiguous: bool = False,
    contains_raw_provider_payload: bool = False,
    beacon_id: str | None = BEACON_ID,
    scan_run_id: str | None = SCAN_RUN_ID,
    evidence_reference_ids: tuple[str, ...] = INTAKE_EVIDENCE_REFERENCE_IDS,
    decision_id: str = "intake-decision-nd10-1",
) -> NotificationSourceIntakeDecision:
    event = _source_event(
        family=family,
        listing_count=listing_count,
        safe_listing_reference_ids=safe_listing_reference_ids,
        producer=producer,
        committed=committed,
        commit_reference=commit_reference,
        source_identity_ambiguous=source_identity_ambiguous,
        contains_raw_provider_payload=contains_raw_provider_payload,
        beacon_id=beacon_id,
        scan_run_id=scan_run_id,
    )
    return evaluate_notification_source_intake(
        decision_id=decision_id,
        source_event=event,
        evidence_reference_ids=evidence_reference_ids,
    )


def _forged_intake_decision(
    *,
    source_event: NotificationSourceEvent,
    reason_codes: tuple[str, ...],
    evidence_reference_ids: tuple[str, ...] = INTAKE_EVIDENCE_REFERENCE_IDS,
    decision_id: str = "forged-intake-decision-nd10-1",
) -> NotificationSourceIntakeDecision:
    return NotificationSourceIntakeDecision(
        decision_id=decision_id,
        authority=NotificationSourceIntakeAuthority.NOTIFICATION_DELIVERY_SERVER,
        source_event=source_event,
        status=NotificationSourceIntakeStatus.ACCEPTED_NOTIFICATION_CANDIDATE,
        source_accepted=True,
        notification_candidate=True,
        status_read_model_candidate=True,
        outbox_effect_authorized=False,
        delivery_attempt_authorized=False,
        reason_codes=reason_codes,
        evidence_reference_ids=evidence_reference_ids,
    )


def _field_fact(
    *,
    field_fact_id: str,
    listing_reference_id: str,
    field_class: NotificationListingCardFieldClass,
    value_class: NotificationListingCardValueClass,
    safe_value: str,
    upstream_field_family: str,
    provenance_tier: NotificationListingCardProvenanceTier,
    upstream_field_reference_id: str,
    compatibility_profile_reference_id: str,
    source_committed: bool = True,
    source_commit_reference: str = SOURCE_COMMIT_REFERENCE,
    field_evidence_approved: bool = True,
    detail_gate_approved: bool = False,
    contact_gate_approved: bool = False,
    contains_raw_provider_payload: bool = False,
    evidence_reference_ids: tuple[str, ...] = FIELD_EVIDENCE_REFERENCE_IDS,
) -> NotificationListingCardFieldFact:
    return NotificationListingCardFieldFact(
        field_fact_id=field_fact_id,
        listing_reference_id=listing_reference_id,
        field_class=field_class,
        value_class=value_class,
        safe_value=safe_value,
        upstream_field_family=upstream_field_family,
        provenance_tier=provenance_tier,
        upstream_field_reference_id=upstream_field_reference_id,
        compatibility_profile_reference_id=compatibility_profile_reference_id,
        source_committed=source_committed,
        source_commit_reference=source_commit_reference,
        field_evidence_approved=field_evidence_approved,
        detail_gate_approved=detail_gate_approved,
        contact_gate_approved=contact_gate_approved,
        contains_raw_provider_payload=contains_raw_provider_payload,
        evidence_reference_ids=evidence_reference_ids,
    )


def _card_input(
    *,
    listing_card_id: str,
    listing_reference_id: str,
    field_facts: tuple[NotificationListingCardFieldFact, ...] = (),
    beacon_name_reference_id: str | None = "beacon-name-nd10-1",
    evidence_reference_ids: tuple[str, ...] = CARD_EVIDENCE_REFERENCE_IDS,
) -> NotificationListingCardInput:
    return NotificationListingCardInput(
        listing_card_id=listing_card_id,
        listing_reference_id=listing_reference_id,
        beacon_name_reference_id=beacon_name_reference_id,
        field_facts=field_facts,
        evidence_reference_ids=evidence_reference_ids,
    )


def _project(
    *,
    decision_id: str = "projection-decision-nd10-1",
    source_intake_decision: NotificationSourceIntakeDecision,
    card_inputs: tuple[NotificationListingCardInput, ...],
    evidence_reference_ids: tuple[str, ...] = FUNCTION_EVIDENCE_REFERENCE_IDS,
) -> NotificationListingCardProjectionDecision:
    return project_notification_listing_cards(
        decision_id=decision_id,
        source_intake_decision=source_intake_decision,
        card_inputs=card_inputs,
        evidence_reference_ids=evidence_reference_ids,
    )


def test_tier1_compatibility_matches_current_parser_contract_values() -> None:
    expected_mapping = {
        NotificationListingCardFieldClass.TITLE: (ListingFieldFamily.TITLE, ListingFieldTier.TIER_1_SEARCH_RESULT),
        NotificationListingCardFieldClass.PRICE: (
            ListingFieldFamily.NORMALIZED_PRICE,
            ListingFieldTier.TIER_1_SEARCH_RESULT,
        ),
        NotificationListingCardFieldClass.GEOGRAPHY: (
            ListingFieldFamily.GEOGRAPHY,
            ListingFieldTier.TIER_1_SEARCH_RESULT,
        ),
        NotificationListingCardFieldClass.LISTING_URL_REFERENCE: (
            ListingFieldFamily.LISTING_URL,
            ListingFieldTier.TIER_1_SEARCH_RESULT,
        ),
        NotificationListingCardFieldClass.PREVIEW_REFERENCE: (
            ListingFieldFamily.PREVIEW_IMAGE,
            ListingFieldTier.TIER_1_SEARCH_RESULT,
        ),
    }

    for field_class, (parser_family, parser_tier) in expected_mapping.items():
        field_fact = _field_fact(
            field_fact_id=f"{field_class.value.lower()}-field-fact",
            listing_reference_id="listing-1",
            field_class=field_class,
            value_class=(
                NotificationListingCardValueClass.SAFE_REFERENCE
                if field_class in {
                    NotificationListingCardFieldClass.LISTING_URL_REFERENCE,
                    NotificationListingCardFieldClass.PREVIEW_REFERENCE,
                }
                else NotificationListingCardValueClass.SAFE_TEXT
            ),
            safe_value=f"{field_class.value.lower()}-safe-value",
            upstream_field_family=parser_family.value,
            provenance_tier=NotificationListingCardProvenanceTier(parser_tier.value),
            upstream_field_reference_id=f"{field_class.value.lower()}-upstream-ref",
            compatibility_profile_reference_id=f"{field_class.value.lower()}-compat-profile",
        )
        assert field_fact.field_class is field_class
        assert field_fact.upstream_field_family == parser_family.value
        assert field_fact.provenance_tier.value == parser_tier.value


def test_all_tier1_mappings_are_preserved_in_projection() -> None:
    intake_decision = _evaluated_intake_decision(listing_count=1, safe_listing_reference_ids=("listing-1",))
    field_facts = (
        _field_fact(
            field_fact_id="title-field-fact",
            listing_reference_id="listing-1",
            field_class=NotificationListingCardFieldClass.TITLE,
            value_class=NotificationListingCardValueClass.SAFE_TEXT,
            safe_value="title-safe",
            upstream_field_family="TITLE",
            provenance_tier=NotificationListingCardProvenanceTier.TIER_1_SEARCH_RESULT,
            upstream_field_reference_id="title-upstream-ref",
            compatibility_profile_reference_id="title-compat-profile",
        ),
        _field_fact(
            field_fact_id="price-field-fact",
            listing_reference_id="listing-1",
            field_class=NotificationListingCardFieldClass.PRICE,
            value_class=NotificationListingCardValueClass.SAFE_TEXT,
            safe_value="price-safe",
            upstream_field_family="NORMALIZED_PRICE",
            provenance_tier=NotificationListingCardProvenanceTier.TIER_1_SEARCH_RESULT,
            upstream_field_reference_id="price-upstream-ref",
            compatibility_profile_reference_id="price-compat-profile",
        ),
        _field_fact(
            field_fact_id="geography-field-fact",
            listing_reference_id="listing-1",
            field_class=NotificationListingCardFieldClass.GEOGRAPHY,
            value_class=NotificationListingCardValueClass.SAFE_TEXT,
            safe_value="geography-safe",
            upstream_field_family="GEOGRAPHY",
            provenance_tier=NotificationListingCardProvenanceTier.TIER_1_SEARCH_RESULT,
            upstream_field_reference_id="geography-upstream-ref",
            compatibility_profile_reference_id="geography-compat-profile",
        ),
        _field_fact(
            field_fact_id="listing-url-field-fact",
            listing_reference_id="listing-1",
            field_class=NotificationListingCardFieldClass.LISTING_URL_REFERENCE,
            value_class=NotificationListingCardValueClass.SAFE_REFERENCE,
            safe_value="listing-url-safe",
            upstream_field_family="LISTING_URL",
            provenance_tier=NotificationListingCardProvenanceTier.TIER_1_SEARCH_RESULT,
            upstream_field_reference_id="listing-url-upstream-ref",
            compatibility_profile_reference_id="listing-url-compat-profile",
        ),
        _field_fact(
            field_fact_id="preview-field-fact",
            listing_reference_id="listing-1",
            field_class=NotificationListingCardFieldClass.PREVIEW_REFERENCE,
            value_class=NotificationListingCardValueClass.SAFE_REFERENCE,
            safe_value="preview-safe",
            upstream_field_family="PREVIEW_IMAGE",
            provenance_tier=NotificationListingCardProvenanceTier.TIER_1_SEARCH_RESULT,
            upstream_field_reference_id="preview-upstream-ref",
            compatibility_profile_reference_id="preview-compat-profile",
        ),
    )
    card_input = _card_input(
        listing_card_id="card-nd10-1",
        listing_reference_id="listing-1",
        field_facts=field_facts,
    )

    decision = _project(source_intake_decision=intake_decision, card_inputs=(card_input,))

    assert decision.status is NotificationListingCardProjectionStatus.ACCEPTED_FIELDS
    assert decision.reason_codes == ("listing-card-fields-accepted",)
    assert decision.listing_references_preserved is True
    assert decision.optional_fields_missing_allowed is True
    assert decision.display_rendering_authorized is False
    assert decision.delivery_attempt_authorized is False
    assert decision.provider_mapping_authorized is False
    assert decision.source_intake_decision is intake_decision
    assert len(decision.cards) == 1
    assert decision.cards[0].field_facts == field_facts
    assert tuple(field.field_class for field in decision.cards[0].field_facts) == (
        NotificationListingCardFieldClass.TITLE,
        NotificationListingCardFieldClass.PRICE,
        NotificationListingCardFieldClass.GEOGRAPHY,
        NotificationListingCardFieldClass.LISTING_URL_REFERENCE,
        NotificationListingCardFieldClass.PREVIEW_REFERENCE,
    )


def test_tier2_mappings_require_detail_gate_and_missing_phone_does_not_fail() -> None:
    intake_decision = _evaluated_intake_decision(listing_count=1, safe_listing_reference_ids=("listing-1",))
    field_facts = (
        _field_fact(
            field_fact_id="description-field-fact",
            listing_reference_id="listing-1",
            field_class=NotificationListingCardFieldClass.DESCRIPTION,
            value_class=NotificationListingCardValueClass.SAFE_TEXT,
            safe_value="description-safe",
            upstream_field_family="DESCRIPTION",
            provenance_tier=NotificationListingCardProvenanceTier.TIER_2_LISTING_DETAIL,
            upstream_field_reference_id="description-upstream-ref",
            compatibility_profile_reference_id="description-compat-profile",
            detail_gate_approved=True,
        ),
        _field_fact(
            field_fact_id="seller-field-fact",
            listing_reference_id="listing-1",
            field_class=NotificationListingCardFieldClass.SELLER,
            value_class=NotificationListingCardValueClass.SAFE_TEXT,
            safe_value="seller-safe",
            upstream_field_family="SELLER",
            provenance_tier=NotificationListingCardProvenanceTier.TIER_2_LISTING_DETAIL,
            upstream_field_reference_id="seller-upstream-ref",
            compatibility_profile_reference_id="seller-compat-profile",
            detail_gate_approved=True,
        ),
        _field_fact(
            field_fact_id="seller-rating-field-fact",
            listing_reference_id="listing-1",
            field_class=NotificationListingCardFieldClass.SELLER_RATING,
            value_class=NotificationListingCardValueClass.SAFE_TEXT,
            safe_value="seller-rating-safe",
            upstream_field_family="SELLER_RATING",
            provenance_tier=NotificationListingCardProvenanceTier.TIER_2_LISTING_DETAIL,
            upstream_field_reference_id="seller-rating-upstream-ref",
            compatibility_profile_reference_id="seller-rating-compat-profile",
            detail_gate_approved=True,
        ),
    )
    card_input = _card_input(
        listing_card_id="card-nd10-2",
        listing_reference_id="listing-1",
        field_facts=field_facts,
    )

    decision = _project(source_intake_decision=intake_decision, card_inputs=(card_input,))

    assert decision.status is NotificationListingCardProjectionStatus.ACCEPTED_FIELDS
    assert decision.cards[0].field_facts == field_facts
    assert all(field.detail_gate_approved is True for field in decision.cards[0].field_facts)
    assert all(field.contact_gate_approved is False for field in decision.cards[0].field_facts)
    assert all(
        field.field_class
        in {
            NotificationListingCardFieldClass.DESCRIPTION,
            NotificationListingCardFieldClass.SELLER,
            NotificationListingCardFieldClass.SELLER_RATING,
        }
        for field in decision.cards[0].field_facts
    )


def test_tier2_field_without_detail_gate_is_rejected() -> None:
    intake_decision = _evaluated_intake_decision(listing_count=1, safe_listing_reference_ids=("listing-1",))
    field_fact = _field_fact(
        field_fact_id="tier2-no-detail-field-fact",
        listing_reference_id="listing-1",
        field_class=NotificationListingCardFieldClass.DESCRIPTION,
        value_class=NotificationListingCardValueClass.SAFE_TEXT,
        safe_value="tier2-no-detail-safe",
        upstream_field_family="DESCRIPTION",
        provenance_tier=NotificationListingCardProvenanceTier.TIER_2_LISTING_DETAIL,
        upstream_field_reference_id="tier2-no-detail-upstream-ref",
        compatibility_profile_reference_id="tier2-no-detail-compat-profile",
        detail_gate_approved=False,
    )
    card_input = _card_input(
        listing_card_id="card-nd10-2b",
        listing_reference_id="listing-1",
        field_facts=(field_fact,),
    )

    with pytest.raises(ValueError):
        _project(source_intake_decision=intake_decision, card_inputs=(card_input,))


def test_phone_requires_detail_and_contact_gate_and_missing_detail_fields_does_not_fail() -> None:
    intake_decision = _evaluated_intake_decision(listing_count=1, safe_listing_reference_ids=("listing-1",))
    field_fact = _field_fact(
        field_fact_id="phone-field-fact",
        listing_reference_id="listing-1",
        field_class=NotificationListingCardFieldClass.PHONE,
        value_class=NotificationListingCardValueClass.SAFE_TEXT,
        safe_value="phone-safe",
        upstream_field_family="PHONE_VALUE",
        provenance_tier=NotificationListingCardProvenanceTier.TIER_3_CONTACT,
        upstream_field_reference_id="phone-upstream-ref",
        compatibility_profile_reference_id="phone-compat-profile",
        detail_gate_approved=True,
        contact_gate_approved=True,
    )
    card_input = _card_input(
        listing_card_id="card-nd10-3",
        listing_reference_id="listing-1",
        field_facts=(field_fact,),
    )

    decision = _project(source_intake_decision=intake_decision, card_inputs=(card_input,))

    assert decision.status is NotificationListingCardProjectionStatus.ACCEPTED_FIELDS
    assert decision.cards[0].field_facts == (field_fact,)
    assert decision.cards[0].field_facts[0].detail_gate_approved is True
    assert decision.cards[0].field_facts[0].contact_gate_approved is True
    assert decision.display_rendering_authorized is False
    assert decision.delivery_attempt_authorized is False
    assert decision.provider_mapping_authorized is False


def test_phone_without_contact_gate_is_rejected() -> None:
    intake_decision = _evaluated_intake_decision(listing_count=1, safe_listing_reference_ids=("listing-1",))
    field_fact = _field_fact(
        field_fact_id="phone-no-contact-field-fact",
        listing_reference_id="listing-1",
        field_class=NotificationListingCardFieldClass.PHONE,
        value_class=NotificationListingCardValueClass.SAFE_TEXT,
        safe_value="phone-no-contact-safe",
        upstream_field_family="PHONE_VALUE",
        provenance_tier=NotificationListingCardProvenanceTier.TIER_3_CONTACT,
        upstream_field_reference_id="phone-no-contact-upstream-ref",
        compatibility_profile_reference_id="phone-no-contact-compat-profile",
        detail_gate_approved=True,
        contact_gate_approved=False,
    )
    card_input = _card_input(
        listing_card_id="card-nd10-3b",
        listing_reference_id="listing-1",
        field_facts=(field_fact,),
    )

    with pytest.raises(ValueError):
        _project(source_intake_decision=intake_decision, card_inputs=(card_input,))


def test_reference_only_cards_are_accepted() -> None:
    intake_decision = _evaluated_intake_decision(listing_count=1, safe_listing_reference_ids=("listing-1",))
    card_input = _card_input(
        listing_card_id="card-nd10-4",
        listing_reference_id="listing-1",
        field_facts=(),
    )

    decision = _project(source_intake_decision=intake_decision, card_inputs=(card_input,))

    assert decision.status is NotificationListingCardProjectionStatus.ACCEPTED_REFERENCE_ONLY
    assert decision.reason_codes == ("listing-card-reference-only-accepted",)
    assert decision.cards[0].field_facts == ()
    assert decision.listing_references_preserved is True
    assert decision.optional_fields_missing_allowed is True
    assert decision.display_rendering_authorized is False
    assert decision.delivery_attempt_authorized is False
    assert decision.provider_mapping_authorized is False


def test_mixed_cards_preserve_reference_only_cards_without_dropping_them() -> None:
    intake_decision = _evaluated_intake_decision(
        listing_count=2,
        safe_listing_reference_ids=("listing-1", "listing-2"),
    )
    field_fact = _field_fact(
        field_fact_id="mixed-title-field-fact",
        listing_reference_id="listing-1",
        field_class=NotificationListingCardFieldClass.TITLE,
        value_class=NotificationListingCardValueClass.SAFE_TEXT,
        safe_value="mixed-title-safe",
        upstream_field_family="TITLE",
        provenance_tier=NotificationListingCardProvenanceTier.TIER_1_SEARCH_RESULT,
        upstream_field_reference_id="mixed-title-upstream-ref",
        compatibility_profile_reference_id="mixed-title-compat-profile",
    )
    card_with_fields = _card_input(
        listing_card_id="card-nd10-5a",
        listing_reference_id="listing-1",
        field_facts=(field_fact,),
    )
    reference_only_card = _card_input(
        listing_card_id="card-nd10-5b",
        listing_reference_id="listing-2",
        field_facts=(),
    )

    decision = _project(
        source_intake_decision=intake_decision,
        card_inputs=(card_with_fields, reference_only_card),
    )

    assert decision.status is NotificationListingCardProjectionStatus.ACCEPTED_FIELDS
    assert decision.cards[0].field_facts == (field_fact,)
    assert decision.cards[1].field_facts == ()
    assert decision.cards[1].listing_reference_id == "listing-2"


def test_zero_listing_recovery_is_not_applicable_and_returns_no_cards() -> None:
    intake_decision = _evaluated_intake_decision(
        family=NotificationSourceFamily.RECOVERY_SCAN_COMPLETED,
        listing_count=0,
        safe_listing_reference_ids=(),
        evidence_reference_ids=("recovery-intake-evidence-1",),
    )

    decision = _project(source_intake_decision=intake_decision, card_inputs=())

    assert decision.status is NotificationListingCardProjectionStatus.NOT_APPLICABLE_NO_LISTINGS
    assert decision.cards == ()
    assert decision.reason_codes == ("listing-card-no-listings-not-applicable",)
    assert decision.listing_references_preserved is True
    assert decision.optional_fields_missing_allowed is True
    assert decision.display_rendering_authorized is False
    assert decision.delivery_attempt_authorized is False
    assert decision.provider_mapping_authorized is False


def test_zero_listing_recovery_rejects_non_empty_card_inputs() -> None:
    intake_decision = _evaluated_intake_decision(
        family=NotificationSourceFamily.RECOVERY_SCAN_COMPLETED,
        listing_count=0,
        safe_listing_reference_ids=(),
    )
    field_fact = _field_fact(
        field_fact_id="unused-field-fact",
        listing_reference_id="listing-1",
        field_class=NotificationListingCardFieldClass.TITLE,
        value_class=NotificationListingCardValueClass.SAFE_TEXT,
        safe_value="unused",
        upstream_field_family="TITLE",
        provenance_tier=NotificationListingCardProvenanceTier.TIER_1_SEARCH_RESULT,
        upstream_field_reference_id="unused-upstream-ref",
        compatibility_profile_reference_id="unused-compat-profile",
    )
    card_input = _card_input(
        listing_card_id="card-nd10-zero-1",
        listing_reference_id="listing-1",
        field_facts=(field_fact,),
    )

    with pytest.raises(ValueError):
        _project(source_intake_decision=intake_decision, card_inputs=(card_input,))


def test_recovery_with_listings_uses_recovered_new_reason() -> None:
    intake_decision = _evaluated_intake_decision(
        family=NotificationSourceFamily.RECOVERY_SCAN_COMPLETED,
        listing_count=1,
        safe_listing_reference_ids=("listing-1",),
    )
    field_fact = _field_fact(
        field_fact_id="recovery-field-fact",
        listing_reference_id="listing-1",
        field_class=NotificationListingCardFieldClass.TITLE,
        value_class=NotificationListingCardValueClass.SAFE_TEXT,
        safe_value="recovery-title",
        upstream_field_family="TITLE",
        provenance_tier=NotificationListingCardProvenanceTier.TIER_1_SEARCH_RESULT,
        upstream_field_reference_id="recovery-upstream-ref",
        compatibility_profile_reference_id="recovery-compat-profile",
    )
    card_input = _card_input(
        listing_card_id="card-nd10-6",
        listing_reference_id="listing-1",
        field_facts=(field_fact,),
    )

    decision = _project(source_intake_decision=intake_decision, card_inputs=(card_input,))

    assert decision.cards[0].reason_class is NotificationListingCardReasonClass.RECOVERED_NEW_LISTING
    assert decision.cards[0].field_facts == (field_fact,)
    assert decision.status is NotificationListingCardProjectionStatus.ACCEPTED_FIELDS


def test_lost_anchors_map_only_to_latest_fresh_state_restored() -> None:
    intake_decision = _evaluated_intake_decision(
        family=NotificationSourceFamily.LOST_ANCHORS_RECOVERED,
        listing_count=1,
        safe_listing_reference_ids=("listing-1",),
        evidence_reference_ids=("lost-anchors-intake-evidence-1",),
    )
    card_input = _card_input(
        listing_card_id="card-nd10-7",
        listing_reference_id="listing-1",
        field_facts=(),
    )

    decision = _project(source_intake_decision=intake_decision, card_inputs=(card_input,))

    assert decision.cards[0].reason_class is NotificationListingCardReasonClass.LATEST_FRESH_STATE_RESTORED
    assert decision.cards[0].field_facts == ()
    assert decision.status is NotificationListingCardProjectionStatus.ACCEPTED_REFERENCE_ONLY


def test_raw_provider_payload_is_rejected() -> None:
    source_event = _source_event(
        contains_raw_provider_payload=True,
    )
    intake_decision = _forged_intake_decision(
        source_event=source_event,
        reason_codes=("source-accepted-new-listings",),
    )
    card_input = _card_input(
        listing_card_id="card-nd10-8",
        listing_reference_id="listing-1",
    )

    with pytest.raises(ValueError):
        _project(source_intake_decision=intake_decision, card_inputs=(card_input,))


def test_raw_provider_field_fact_is_rejected() -> None:
    intake_decision = _evaluated_intake_decision(listing_count=1, safe_listing_reference_ids=("listing-1",))
    field_fact = _field_fact(
        field_fact_id="raw-provider-field-fact",
        listing_reference_id="listing-1",
        field_class=NotificationListingCardFieldClass.TITLE,
        value_class=NotificationListingCardValueClass.SAFE_TEXT,
        safe_value="raw-provider-safe",
        upstream_field_family="TITLE",
        provenance_tier=NotificationListingCardProvenanceTier.TIER_1_SEARCH_RESULT,
        upstream_field_reference_id="raw-provider-upstream-ref",
        compatibility_profile_reference_id="raw-provider-compat-profile",
        contains_raw_provider_payload=True,
    )
    card_input = _card_input(
        listing_card_id="card-nd10-raw-field-1",
        listing_reference_id="listing-1",
        field_facts=(field_fact,),
    )

    with pytest.raises(ValueError):
        _project(source_intake_decision=intake_decision, card_inputs=(card_input,))


@pytest.mark.parametrize(
    ("source_committed", "source_commit_reference"),
    [
        (False, SOURCE_COMMIT_REFERENCE),
        (True, "commit-nd10-mismatch"),
    ],
)
def test_uncommitted_field_fact_and_commit_reference_mismatch_are_rejected(
    source_committed: bool,
    source_commit_reference: str,
) -> None:
    intake_decision = _evaluated_intake_decision(listing_count=1, safe_listing_reference_ids=("listing-1",))
    field_fact = _field_fact(
        field_fact_id="field-fact-invalid",
        listing_reference_id="listing-1",
        field_class=NotificationListingCardFieldClass.TITLE,
        value_class=NotificationListingCardValueClass.SAFE_TEXT,
        safe_value="invalid-field",
        upstream_field_family="TITLE",
        provenance_tier=NotificationListingCardProvenanceTier.TIER_1_SEARCH_RESULT,
        upstream_field_reference_id="invalid-upstream-ref",
        compatibility_profile_reference_id="invalid-compat-profile",
        source_committed=source_committed,
        source_commit_reference=source_commit_reference,
    )
    card_input = _card_input(
        listing_card_id="card-nd10-9",
        listing_reference_id="listing-1",
        field_facts=(field_fact,),
    )

    with pytest.raises(ValueError):
        _project(source_intake_decision=intake_decision, card_inputs=(card_input,))


@pytest.mark.parametrize(
    "family",
    [
        NotificationSourceFamily.PARSER_ONLY_OUTCOME,
        NotificationSourceFamily.EGRESS_ONLY_OUTCOME,
        NotificationSourceFamily.PROVIDER_ONLY_CALLBACK,
        NotificationSourceFamily.BEACON_BASELINE_ESTABLISHED,
        NotificationSourceFamily.LISTING_PRICE_PAIR_FIRST_SEEN,
        NotificationSourceFamily.EXTERNAL_UNAVAILABLE_STATUS,
        NotificationSourceFamily.NO_NEW_LISTINGS_STATUS,
    ],
)
def test_forged_parser_and_non_listing_source_families_are_rejected(
    family: NotificationSourceFamily,
) -> None:
    source_event = _source_event(
        family=family,
        listing_count=0 if family in {
            NotificationSourceFamily.BEACON_BASELINE_ESTABLISHED,
            NotificationSourceFamily.EXTERNAL_UNAVAILABLE_STATUS,
            NotificationSourceFamily.NO_NEW_LISTINGS_STATUS,
        } else 1,
        safe_listing_reference_ids=() if family in {
            NotificationSourceFamily.BEACON_BASELINE_ESTABLISHED,
            NotificationSourceFamily.EXTERNAL_UNAVAILABLE_STATUS,
            NotificationSourceFamily.NO_NEW_LISTINGS_STATUS,
        } else ("listing-1",),
    )
    intake_decision = _forged_intake_decision(
        source_event=source_event,
        reason_codes=(
            {
                NotificationSourceFamily.PARSER_ONLY_OUTCOME: "source-accepted-parser-outcome",
                NotificationSourceFamily.EGRESS_ONLY_OUTCOME: "source-accepted-egress-outcome",
                NotificationSourceFamily.PROVIDER_ONLY_CALLBACK: "source-accepted-provider-callback",
                NotificationSourceFamily.BEACON_BASELINE_ESTABLISHED: "source-accepted-baseline",
                NotificationSourceFamily.LISTING_PRICE_PAIR_FIRST_SEEN: "source-accepted-price-pair",
                NotificationSourceFamily.EXTERNAL_UNAVAILABLE_STATUS: "source-accepted-external-status",
                NotificationSourceFamily.NO_NEW_LISTINGS_STATUS: "source-accepted-no-new-status",
            }[family],
        ),
    )
    card_input = _card_input(
        listing_card_id="card-nd10-forged",
        listing_reference_id="listing-1",
    )

    with pytest.raises(ValueError):
        _project(source_intake_decision=intake_decision, card_inputs=(card_input,))


@pytest.mark.parametrize(
    "field_fact",
    [
        _field_fact(
            field_fact_id="wrong-value-class",
            listing_reference_id="listing-1",
            field_class=NotificationListingCardFieldClass.TITLE,
            value_class=NotificationListingCardValueClass.SAFE_REFERENCE,
            safe_value="wrong-value-class",
            upstream_field_family="TITLE",
            provenance_tier=NotificationListingCardProvenanceTier.TIER_1_SEARCH_RESULT,
            upstream_field_reference_id="wrong-value-class-upstream-ref",
            compatibility_profile_reference_id="wrong-value-class-compat-profile",
        ),
        _field_fact(
            field_fact_id="wrong-tier",
            listing_reference_id="listing-1",
            field_class=NotificationListingCardFieldClass.DESCRIPTION,
            value_class=NotificationListingCardValueClass.SAFE_TEXT,
            safe_value="wrong-tier",
            upstream_field_family="DESCRIPTION",
            provenance_tier=NotificationListingCardProvenanceTier.TIER_1_SEARCH_RESULT,
            upstream_field_reference_id="wrong-tier-upstream-ref",
            compatibility_profile_reference_id="wrong-tier-compat-profile",
            detail_gate_approved=False,
        ),
        _field_fact(
            field_fact_id="wrong-family",
            listing_reference_id="listing-1",
            field_class=NotificationListingCardFieldClass.PHONE,
            value_class=NotificationListingCardValueClass.SAFE_TEXT,
            safe_value="wrong-family",
            upstream_field_family="PHONE_AVAILABILITY",
            provenance_tier=NotificationListingCardProvenanceTier.TIER_3_CONTACT,
            upstream_field_reference_id="wrong-family-upstream-ref",
            compatibility_profile_reference_id="wrong-family-compat-profile",
            detail_gate_approved=True,
            contact_gate_approved=True,
        ),
    ],
)
def test_wrong_field_family_tier_or_value_class_is_rejected(
    field_fact: NotificationListingCardFieldFact,
) -> None:
    intake_decision = _evaluated_intake_decision(listing_count=1, safe_listing_reference_ids=("listing-1",))
    card_input = _card_input(
        listing_card_id="card-nd10-field-invalid",
        listing_reference_id="listing-1",
        field_facts=(field_fact,),
    )

    with pytest.raises(ValueError):
        _project(source_intake_decision=intake_decision, card_inputs=(card_input,))


def test_duplicate_field_class_is_rejected() -> None:
    intake_decision = _evaluated_intake_decision(listing_count=1, safe_listing_reference_ids=("listing-1",))
    duplicate_title_1 = _field_fact(
        field_fact_id="duplicate-title-1",
        listing_reference_id="listing-1",
        field_class=NotificationListingCardFieldClass.TITLE,
        value_class=NotificationListingCardValueClass.SAFE_TEXT,
        safe_value="duplicate-title-1",
        upstream_field_family="TITLE",
        provenance_tier=NotificationListingCardProvenanceTier.TIER_1_SEARCH_RESULT,
        upstream_field_reference_id="duplicate-title-1-upstream-ref",
        compatibility_profile_reference_id="duplicate-title-1-compat-profile",
    )
    duplicate_title_2 = _field_fact(
        field_fact_id="duplicate-title-2",
        listing_reference_id="listing-1",
        field_class=NotificationListingCardFieldClass.TITLE,
        value_class=NotificationListingCardValueClass.SAFE_TEXT,
        safe_value="duplicate-title-2",
        upstream_field_family="TITLE",
        provenance_tier=NotificationListingCardProvenanceTier.TIER_1_SEARCH_RESULT,
        upstream_field_reference_id="duplicate-title-2-upstream-ref",
        compatibility_profile_reference_id="duplicate-title-2-compat-profile",
    )
    card_input = _card_input(
        listing_card_id="card-nd10-10",
        listing_reference_id="listing-1",
        field_facts=(duplicate_title_1, duplicate_title_2),
    )

    with pytest.raises(ValueError):
        _project(source_intake_decision=intake_decision, card_inputs=(card_input,))


def test_duplicate_card_id_is_rejected() -> None:
    intake_decision = _evaluated_intake_decision(
        listing_count=2,
        safe_listing_reference_ids=("listing-1", "listing-2"),
    )
    card_input_1 = _card_input(
        listing_card_id="duplicate-card-id",
        listing_reference_id="listing-1",
    )
    card_input_2 = _card_input(
        listing_card_id="duplicate-card-id",
        listing_reference_id="listing-2",
    )

    with pytest.raises(ValueError):
        _project(source_intake_decision=intake_decision, card_inputs=(card_input_1, card_input_2))


def test_duplicate_listing_reference_is_rejected() -> None:
    intake_decision = _evaluated_intake_decision(
        listing_count=2,
        safe_listing_reference_ids=("listing-1", "listing-2"),
    )
    card_input_1 = _card_input(
        listing_card_id="card-nd10-11a",
        listing_reference_id="listing-1",
    )
    card_input_2 = _card_input(
        listing_card_id="card-nd10-11b",
        listing_reference_id="listing-1",
    )

    with pytest.raises(ValueError):
        _project(source_intake_decision=intake_decision, card_inputs=(card_input_1, card_input_2))


@pytest.mark.parametrize(
    "card_inputs",
    [
        (
            _card_input(listing_card_id="card-nd10-order-1", listing_reference_id="listing-2"),
            _card_input(listing_card_id="card-nd10-order-2", listing_reference_id="listing-1"),
            _card_input(listing_card_id="card-nd10-order-3", listing_reference_id="listing-3"),
        ),
        (
            _card_input(listing_card_id="card-nd10-missing-1", listing_reference_id="listing-1"),
            _card_input(listing_card_id="card-nd10-missing-2", listing_reference_id="listing-2"),
        ),
        (
            _card_input(listing_card_id="card-nd10-extra-1", listing_reference_id="listing-1"),
            _card_input(listing_card_id="card-nd10-extra-2", listing_reference_id="listing-2"),
            _card_input(listing_card_id="card-nd10-extra-3", listing_reference_id="listing-999"),
        ),
    ],
)
def test_reordered_missing_and_extra_listing_references_are_rejected(
    card_inputs: tuple[NotificationListingCardInput, ...],
) -> None:
    intake_decision = _evaluated_intake_decision(
        listing_count=3,
        safe_listing_reference_ids=("listing-1", "listing-2", "listing-3"),
    )

    with pytest.raises(ValueError):
        _project(source_intake_decision=intake_decision, card_inputs=card_inputs)


def test_no_input_mutation_and_deterministic_evidence_union() -> None:
    intake_decision = _evaluated_intake_decision(
        listing_count=1,
        safe_listing_reference_ids=("listing-1",),
        evidence_reference_ids=("intake-evidence-1", "shared-evidence"),
    )
    field_fact = _field_fact(
        field_fact_id="deterministic-field-fact",
        listing_reference_id="listing-1",
        field_class=NotificationListingCardFieldClass.TITLE,
        value_class=NotificationListingCardValueClass.SAFE_TEXT,
        safe_value="deterministic-safe",
        upstream_field_family="TITLE",
        provenance_tier=NotificationListingCardProvenanceTier.TIER_1_SEARCH_RESULT,
        upstream_field_reference_id="deterministic-upstream-ref",
        compatibility_profile_reference_id="deterministic-compat-profile",
        evidence_reference_ids=("field-evidence-1", "shared-function-evidence"),
    )
    card_input = _card_input(
        listing_card_id="card-nd10-12",
        listing_reference_id="listing-1",
        field_facts=(field_fact,),
        evidence_reference_ids=("card-evidence-1", "shared-evidence"),
    )

    intake_decision_before = deepcopy(intake_decision)
    card_input_before = deepcopy(card_input)
    field_fact_before = deepcopy(field_fact)

    decision = _project(
        source_intake_decision=intake_decision,
        card_inputs=(card_input,),
        evidence_reference_ids=("function-evidence-1", "shared-function-evidence"),
    )

    assert intake_decision == intake_decision_before
    assert card_input == card_input_before
    assert field_fact == field_fact_before
    assert decision.source_intake_decision is intake_decision
    assert decision.cards[0].field_facts[0] is field_fact
    assert decision.cards[0].evidence_reference_ids == (
        "intake-evidence-1",
        "shared-evidence",
        "source-evidence-1",
        "source-evidence-2",
        "card-evidence-1",
        "field-evidence-1",
        "shared-function-evidence",
        "function-evidence-1",
    )
    assert decision.evidence_reference_ids == (
        "intake-evidence-1",
        "shared-evidence",
        "source-evidence-1",
        "source-evidence-2",
        "card-evidence-1",
        "field-evidence-1",
        "shared-function-evidence",
        "function-evidence-1",
    )
    assert decision.display_rendering_authorized is False
    assert decision.delivery_attempt_authorized is False
    assert decision.provider_mapping_authorized is False

# ruff: noqa: E501
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .source_intake import (
    NotificationSourceEvent,
    NotificationSourceFamily,
    NotificationSourceIntakeAuthority,
    NotificationSourceIntakeDecision,
    NotificationSourceIntakeStatus,
    NotificationSourceProducer,
)

ND10_TASK_ID = "ND-10-LISTING-CARD-PAYLOAD-BOUNDARY-SEMANTICS-20260716-017"


class NotificationListingCardAuthority(str, Enum):
    NOTIFICATION_DELIVERY_SERVER = "NOTIFICATION_DELIVERY_SERVER"


class NotificationListingCardReasonClass(str, Enum):
    NEW_LISTING = "NEW_LISTING"
    RECOVERED_NEW_LISTING = "RECOVERED_NEW_LISTING"
    LATEST_FRESH_STATE_RESTORED = "LATEST_FRESH_STATE_RESTORED"


class NotificationListingCardFieldClass(str, Enum):
    TITLE = "TITLE"
    PRICE = "PRICE"
    GEOGRAPHY = "GEOGRAPHY"
    LISTING_URL_REFERENCE = "LISTING_URL_REFERENCE"
    PREVIEW_REFERENCE = "PREVIEW_REFERENCE"
    DESCRIPTION = "DESCRIPTION"
    SELLER = "SELLER"
    SELLER_RATING = "SELLER_RATING"
    PHONE = "PHONE"


class NotificationListingCardValueClass(str, Enum):
    SAFE_TEXT = "SAFE_TEXT"
    SAFE_REFERENCE = "SAFE_REFERENCE"


class NotificationListingCardProvenanceTier(str, Enum):
    TIER_1_SEARCH_RESULT = "TIER_1_SEARCH_RESULT"
    TIER_2_LISTING_DETAIL = "TIER_2_LISTING_DETAIL"
    TIER_3_CONTACT = "TIER_3_CONTACT"


class NotificationListingCardProjectionStatus(str, Enum):
    ACCEPTED_FIELDS = "ACCEPTED_FIELDS"
    ACCEPTED_REFERENCE_ONLY = "ACCEPTED_REFERENCE_ONLY"
    NOT_APPLICABLE_NO_LISTINGS = "NOT_APPLICABLE_NO_LISTINGS"


_ALLOWED_SOURCE_FAMILIES = (
    NotificationSourceFamily.NEW_LISTINGS_FOUND,
    NotificationSourceFamily.RECOVERY_SCAN_COMPLETED,
    NotificationSourceFamily.LOST_ANCHORS_RECOVERED,
)

_SOURCE_REASON_CODES = {
    NotificationSourceFamily.NEW_LISTINGS_FOUND: ("source-accepted-new-listings",),
    NotificationSourceFamily.RECOVERY_SCAN_COMPLETED: ("source-accepted-recovery-result",),
    NotificationSourceFamily.LOST_ANCHORS_RECOVERED: (
        "source-accepted-lost-anchors-state-restored",
    ),
}

_REASON_CLASS_BY_FAMILY = {
    NotificationSourceFamily.NEW_LISTINGS_FOUND: NotificationListingCardReasonClass.NEW_LISTING,
    NotificationSourceFamily.RECOVERY_SCAN_COMPLETED: (
        NotificationListingCardReasonClass.RECOVERED_NEW_LISTING
    ),
    NotificationSourceFamily.LOST_ANCHORS_RECOVERED: (
        NotificationListingCardReasonClass.LATEST_FRESH_STATE_RESTORED
    ),
}

_PROJECTION_REASON_CODES_BY_STATUS = {
    NotificationListingCardProjectionStatus.ACCEPTED_FIELDS: ("listing-card-fields-accepted",),
    NotificationListingCardProjectionStatus.ACCEPTED_REFERENCE_ONLY: (
        "listing-card-reference-only-accepted",
    ),
    NotificationListingCardProjectionStatus.NOT_APPLICABLE_NO_LISTINGS: (
        "listing-card-no-listings-not-applicable",
    ),
}

_FIELD_COMPATIBILITY = {
    NotificationListingCardFieldClass.TITLE: (
        NotificationListingCardValueClass.SAFE_TEXT,
        "TITLE",
        NotificationListingCardProvenanceTier.TIER_1_SEARCH_RESULT,
        False,
        False,
    ),
    NotificationListingCardFieldClass.PRICE: (
        NotificationListingCardValueClass.SAFE_TEXT,
        "NORMALIZED_PRICE",
        NotificationListingCardProvenanceTier.TIER_1_SEARCH_RESULT,
        False,
        False,
    ),
    NotificationListingCardFieldClass.GEOGRAPHY: (
        NotificationListingCardValueClass.SAFE_TEXT,
        "GEOGRAPHY",
        NotificationListingCardProvenanceTier.TIER_1_SEARCH_RESULT,
        False,
        False,
    ),
    NotificationListingCardFieldClass.LISTING_URL_REFERENCE: (
        NotificationListingCardValueClass.SAFE_REFERENCE,
        "LISTING_URL",
        NotificationListingCardProvenanceTier.TIER_1_SEARCH_RESULT,
        False,
        False,
    ),
    NotificationListingCardFieldClass.PREVIEW_REFERENCE: (
        NotificationListingCardValueClass.SAFE_REFERENCE,
        "PREVIEW_IMAGE",
        NotificationListingCardProvenanceTier.TIER_1_SEARCH_RESULT,
        False,
        False,
    ),
    NotificationListingCardFieldClass.DESCRIPTION: (
        NotificationListingCardValueClass.SAFE_TEXT,
        "DESCRIPTION",
        NotificationListingCardProvenanceTier.TIER_2_LISTING_DETAIL,
        True,
        False,
    ),
    NotificationListingCardFieldClass.SELLER: (
        NotificationListingCardValueClass.SAFE_TEXT,
        "SELLER",
        NotificationListingCardProvenanceTier.TIER_2_LISTING_DETAIL,
        True,
        False,
    ),
    NotificationListingCardFieldClass.SELLER_RATING: (
        NotificationListingCardValueClass.SAFE_TEXT,
        "SELLER_RATING",
        NotificationListingCardProvenanceTier.TIER_2_LISTING_DETAIL,
        True,
        False,
    ),
    NotificationListingCardFieldClass.PHONE: (
        NotificationListingCardValueClass.SAFE_TEXT,
        "PHONE_VALUE",
        NotificationListingCardProvenanceTier.TIER_3_CONTACT,
        True,
        True,
    ),
}


def _require_text(value: object, field_name: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-blank string")
    return value


def _require_optional_text(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_text(value, field_name)


def _require_bool(value: object, field_name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_exact_true(value: object, field_name: str) -> None:
    if value is not True:
        raise ValueError(f"{field_name} must be True")


def _require_exact_false(value: object, field_name: str) -> None:
    if value is not False:
        raise ValueError(f"{field_name} must be False")


def _require_exact_enum(value: object, enum_type: type[Enum], field_name: str) -> Enum:
    if type(value) is not enum_type:
        raise ValueError(f"{field_name} must be {enum_type.__name__}")
    return value


def _require_text_tuple(value: object, field_name: str) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    return tuple(_require_text(item, field_name) for item in value)


def _first_occurrence_union(*tuples: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for items in tuples:
        for item in items:
            if item not in seen:
                seen.add(item)
                ordered.append(item)
    return tuple(ordered)


@dataclass(frozen=True, slots=True)
class NotificationListingCardFieldFact:
    field_fact_id: str
    listing_reference_id: str
    field_class: NotificationListingCardFieldClass
    value_class: NotificationListingCardValueClass
    safe_value: str
    upstream_field_family: str
    provenance_tier: NotificationListingCardProvenanceTier
    upstream_field_reference_id: str
    compatibility_profile_reference_id: str
    source_committed: bool
    source_commit_reference: str
    field_evidence_approved: bool
    detail_gate_approved: bool
    contact_gate_approved: bool
    contains_raw_provider_payload: bool
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.field_fact_id, "field_fact_id")
        _require_text(self.listing_reference_id, "listing_reference_id")
        _require_exact_enum(self.field_class, NotificationListingCardFieldClass, "field_class")
        _require_exact_enum(self.value_class, NotificationListingCardValueClass, "value_class")
        _require_text(self.safe_value, "safe_value")
        _require_text(self.upstream_field_family, "upstream_field_family")
        _require_exact_enum(
            self.provenance_tier,
            NotificationListingCardProvenanceTier,
            "provenance_tier",
        )
        _require_text(self.upstream_field_reference_id, "upstream_field_reference_id")
        _require_text(
            self.compatibility_profile_reference_id,
            "compatibility_profile_reference_id",
        )
        _require_bool(self.source_committed, "source_committed")
        _require_text(self.source_commit_reference, "source_commit_reference")
        _require_bool(self.field_evidence_approved, "field_evidence_approved")
        _require_bool(self.detail_gate_approved, "detail_gate_approved")
        _require_bool(self.contact_gate_approved, "contact_gate_approved")
        _require_text_tuple(self.evidence_reference_ids, "evidence_reference_ids")


@dataclass(frozen=True, slots=True)
class NotificationListingCardInput:
    listing_card_id: str
    listing_reference_id: str
    beacon_name_reference_id: str | None
    field_facts: tuple[NotificationListingCardFieldFact, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.listing_card_id, "listing_card_id")
        _require_text(self.listing_reference_id, "listing_reference_id")
        _require_optional_text(self.beacon_name_reference_id, "beacon_name_reference_id")
        if type(self.field_facts) is not tuple:
            raise ValueError("field_facts must be a tuple")
        for field_fact in self.field_facts:
            if type(field_fact) is not NotificationListingCardFieldFact:
                raise ValueError("field_facts must contain NotificationListingCardFieldFact")
        _require_text_tuple(self.evidence_reference_ids, "evidence_reference_ids")


@dataclass(frozen=True, slots=True)
class NotificationListingCard:
    listing_card_id: str
    listing_reference_id: str
    account_id: str
    beacon_id: str
    source_event_id: str
    source_fact_id: str
    source_family: NotificationSourceFamily
    reason_class: NotificationListingCardReasonClass
    beacon_name_reference_id: str | None
    field_facts: tuple[NotificationListingCardFieldFact, ...]
    correlation_id: str
    causation_id: str
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.listing_card_id, "listing_card_id")
        _require_text(self.listing_reference_id, "listing_reference_id")
        _require_text(self.account_id, "account_id")
        _require_text(self.beacon_id, "beacon_id")
        _require_text(self.source_event_id, "source_event_id")
        _require_text(self.source_fact_id, "source_fact_id")
        _require_exact_enum(self.source_family, NotificationSourceFamily, "source_family")
        _require_exact_enum(self.reason_class, NotificationListingCardReasonClass, "reason_class")
        _require_optional_text(self.beacon_name_reference_id, "beacon_name_reference_id")
        if type(self.field_facts) is not tuple:
            raise ValueError("field_facts must be a tuple")
        seen_field_classes: set[NotificationListingCardFieldClass] = set()
        for field_fact in self.field_facts:
            if type(field_fact) is not NotificationListingCardFieldFact:
                raise ValueError("field_facts must contain NotificationListingCardFieldFact")
            if field_fact.field_class in seen_field_classes:
                raise ValueError("field_facts must not repeat field classes")
            seen_field_classes.add(field_fact.field_class)
        _require_text(self.correlation_id, "correlation_id")
        _require_text(self.causation_id, "causation_id")
        _require_text_tuple(self.evidence_reference_ids, "evidence_reference_ids")


@dataclass(frozen=True, slots=True)
class NotificationListingCardProjectionDecision:
    decision_id: str
    authority: NotificationListingCardAuthority
    source_intake_decision: NotificationSourceIntakeDecision
    cards: tuple[NotificationListingCard, ...]
    status: NotificationListingCardProjectionStatus
    listing_references_preserved: bool
    optional_fields_missing_allowed: bool
    display_rendering_authorized: bool
    delivery_attempt_authorized: bool
    provider_mapping_authorized: bool
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.decision_id, "decision_id")
        _require_exact_enum(self.authority, NotificationListingCardAuthority, "authority")
        if type(self.source_intake_decision) is not NotificationSourceIntakeDecision:
            raise ValueError("source_intake_decision must be NotificationSourceIntakeDecision")
        if type(self.cards) is not tuple:
            raise ValueError("cards must be a tuple")
        for card in self.cards:
            if type(card) is not NotificationListingCard:
                raise ValueError("cards must contain NotificationListingCard")
        _require_exact_enum(self.status, NotificationListingCardProjectionStatus, "status")
        _require_exact_true(self.listing_references_preserved, "listing_references_preserved")
        _require_exact_true(self.optional_fields_missing_allowed, "optional_fields_missing_allowed")
        _require_exact_false(self.display_rendering_authorized, "display_rendering_authorized")
        _require_exact_false(self.delivery_attempt_authorized, "delivery_attempt_authorized")
        _require_exact_false(self.provider_mapping_authorized, "provider_mapping_authorized")
        _require_text_tuple(self.reason_codes, "reason_codes")
        _require_text_tuple(self.evidence_reference_ids, "evidence_reference_ids")

        source_event = _validate_source_intake_decision(self.source_intake_decision)

        expected_reason_codes = _PROJECTION_REASON_CODES_BY_STATUS[self.status]
        if self.reason_codes != expected_reason_codes:
            raise ValueError("reason_codes must match projection status")

        if self.status is NotificationListingCardProjectionStatus.NOT_APPLICABLE_NO_LISTINGS:
            if source_event.source_family is not NotificationSourceFamily.RECOVERY_SCAN_COMPLETED:
                raise ValueError("no-listings projection requires recovery source family")
            if source_event.listing_count != 0:
                raise ValueError("no-listings projection requires zero listing_count")
            if source_event.safe_listing_reference_ids:
                raise ValueError("no-listings projection requires empty safe references")
            if self.cards:
                raise ValueError("no-listings projection must not contain cards")
            return

        if source_event.listing_count <= 0:
            raise ValueError("listing-bearing projection requires listings")
        if len(self.cards) != source_event.listing_count:
            raise ValueError("cards must match source_event listing_count")
        if len(self.cards) != len(source_event.safe_listing_reference_ids):
            raise ValueError("cards must preserve safe listing references")
        if tuple(card.listing_reference_id for card in self.cards) != source_event.safe_listing_reference_ids:
            raise ValueError("cards must preserve listing reference order")

        listing_card_ids = tuple(card.listing_card_id for card in self.cards)
        if len(set(listing_card_ids)) != len(listing_card_ids):
            raise ValueError("cards must not contain duplicate listing_card_id values")

        listing_reference_ids = tuple(card.listing_reference_id for card in self.cards)
        if len(set(listing_reference_ids)) != len(listing_reference_ids):
            raise ValueError("cards must not contain duplicate listing_reference_id values")

        expected_reason_class = _REASON_CLASS_BY_FAMILY[source_event.source_family]
        has_any_fields = False

        for card in self.cards:
            if card.account_id != source_event.account_id:
                raise ValueError("card account_id must match source_event")
            if card.beacon_id != source_event.beacon_id:
                raise ValueError("card beacon_id must match source_event")
            if card.source_event_id != source_event.source_event_id:
                raise ValueError("card source_event_id must match source_event")
            if card.source_fact_id != source_event.source_fact_id:
                raise ValueError("card source_fact_id must match source_event")
            if card.source_family is not source_event.source_family:
                raise ValueError("card source_family must match source_event")
            if card.correlation_id != source_event.correlation_id:
                raise ValueError("card correlation_id must match source_event")
            if card.causation_id != source_event.causation_id:
                raise ValueError("card causation_id must match source_event")
            if card.reason_class is not expected_reason_class:
                raise ValueError("card reason_class must match source family")
            if type(card.field_facts) is not tuple:
                raise ValueError("field_facts must be a tuple")

            seen_field_classes: set[NotificationListingCardFieldClass] = set()
            validated_field_facts: list[NotificationListingCardFieldFact] = []
            for field_fact in card.field_facts:
                validated_field_fact = _validate_field_fact_safety(
                    field_fact=field_fact,
                    source_event=source_event,
                    listing_reference_id=card.listing_reference_id,
                )
                if validated_field_fact.field_class in seen_field_classes:
                    raise ValueError("card field facts must not repeat field classes")
                seen_field_classes.add(validated_field_fact.field_class)
                validated_field_facts.append(validated_field_fact)

            if validated_field_facts:
                has_any_fields = True
            elif self.status is NotificationListingCardProjectionStatus.ACCEPTED_REFERENCE_ONLY:
                continue

        if self.status is NotificationListingCardProjectionStatus.ACCEPTED_FIELDS:
            if not has_any_fields:
                raise ValueError("accepted fields projections require at least one field fact")
        elif self.status is NotificationListingCardProjectionStatus.ACCEPTED_REFERENCE_ONLY:
            if has_any_fields:
                raise ValueError("reference-only projections must not contain field facts")
        else:
            raise ValueError("unsupported projection status")


def _validate_source_intake_decision(
    source_intake_decision: NotificationSourceIntakeDecision,
) -> NotificationSourceEvent:
    if type(source_intake_decision) is not NotificationSourceIntakeDecision:
        raise ValueError("source_intake_decision must be NotificationSourceIntakeDecision")
    if source_intake_decision.authority is not NotificationSourceIntakeAuthority.NOTIFICATION_DELIVERY_SERVER:
        raise ValueError("source_intake_decision authority must be NOTIFICATION_DELIVERY_SERVER")
    if source_intake_decision.status is not NotificationSourceIntakeStatus.ACCEPTED_NOTIFICATION_CANDIDATE:
        raise ValueError("source_intake_decision must be accepted")
    if (
        source_intake_decision.source_accepted is not True
        or source_intake_decision.notification_candidate is not True
        or source_intake_decision.status_read_model_candidate is not True
    ):
        raise ValueError("source_intake_decision must be accepted for notification delivery")
    if (
        source_intake_decision.outbox_effect_authorized is not False
        or source_intake_decision.delivery_attempt_authorized is not False
    ):
        raise ValueError("source_intake_decision must not authorize delivery effects")

    source_event = source_intake_decision.source_event
    if type(source_event) is not NotificationSourceEvent:
        raise ValueError("source_event must be NotificationSourceEvent")
    if source_event.source_producer is not NotificationSourceProducer.SCAN_ORCHESTRATION:
        raise ValueError("source_event producer must be SCAN_ORCHESTRATION")
    if source_event.source_committed is not True:
        raise ValueError("source_event must be committed")
    _require_text(source_event.source_commit_reference, "source_commit_reference")
    if source_event.source_identity_ambiguous is not False:
        raise ValueError("source_event must not be identity ambiguous")
    if source_event.contains_raw_provider_payload is not False:
        raise ValueError("source_event must not carry raw provider content")
    if source_event.beacon_id is None:
        raise ValueError("source_event must include beacon_id")
    if source_event.scan_run_id is None:
        raise ValueError("source_event must include scan_run_id")
    if source_event.source_family not in _ALLOWED_SOURCE_FAMILIES:
        raise ValueError("source_event family is not allowed for listing card projection")

    expected_reason_codes = _SOURCE_REASON_CODES[source_event.source_family]
    if source_intake_decision.reason_codes != expected_reason_codes:
        raise ValueError("source_intake_decision reason codes do not match source family")

    if source_event.source_family is NotificationSourceFamily.RECOVERY_SCAN_COMPLETED:
        if source_event.listing_count == 0:
            if source_event.safe_listing_reference_ids:
                raise ValueError("zero-listing recovery must not carry listing references")
        elif source_event.listing_count != len(source_event.safe_listing_reference_ids):
            raise ValueError("source_event listing references must match listing_count")
    else:
        if source_event.listing_count <= 0:
            raise ValueError("listing-bearing source_event must have listings")
        if source_event.listing_count != len(source_event.safe_listing_reference_ids):
            raise ValueError("source_event listing references must match listing_count")

    return source_event


def _validate_field_fact_safety(
    *,
    field_fact: NotificationListingCardFieldFact,
    source_event: NotificationSourceEvent,
    listing_reference_id: str,
) -> NotificationListingCardFieldFact:
    if type(field_fact) is not NotificationListingCardFieldFact:
        raise ValueError("field_fact must be NotificationListingCardFieldFact")
    if field_fact.listing_reference_id != listing_reference_id:
        raise ValueError("field_fact listing reference must match its card")

    field_compatibility = _FIELD_COMPATIBILITY.get(field_fact.field_class)
    if field_compatibility is None:
        raise ValueError("field_fact field class is not allowed")

    (
        expected_value_class,
        expected_upstream_field_family,
        expected_provenance_tier,
        expected_detail_gate_approved,
        expected_contact_gate_approved,
    ) = field_compatibility

    if field_fact.value_class is not expected_value_class:
        raise ValueError("field_fact value class is not allowed")
    if field_fact.upstream_field_family != expected_upstream_field_family:
        raise ValueError("field_fact upstream family is not allowed")
    if field_fact.provenance_tier is not expected_provenance_tier:
        raise ValueError("field_fact provenance tier is not allowed")
    if field_fact.source_committed is not True:
        raise ValueError("field_fact must be committed")
    if field_fact.source_commit_reference != source_event.source_commit_reference:
        raise ValueError("field_fact source commit reference must match source event")
    if field_fact.field_evidence_approved is not True:
        raise ValueError("field_fact evidence must be approved")
    if field_fact.detail_gate_approved is not expected_detail_gate_approved:
        raise ValueError("field_fact detail gate is not allowed")
    if field_fact.contact_gate_approved is not expected_contact_gate_approved:
        raise ValueError("field_fact contact gate is not allowed")
    if field_fact.contains_raw_provider_payload is not False:
        raise ValueError("field_fact must not carry raw provider content")
    _require_text(field_fact.upstream_field_reference_id, "upstream_field_reference_id")
    _require_text(
        field_fact.compatibility_profile_reference_id,
        "compatibility_profile_reference_id",
    )
    return field_fact


def project_notification_listing_cards(
    *,
    decision_id: str,
    source_intake_decision: NotificationSourceIntakeDecision,
    card_inputs: tuple[NotificationListingCardInput, ...],
    evidence_reference_ids: tuple[str, ...],
) -> NotificationListingCardProjectionDecision:
    _require_text(decision_id, "decision_id")
    if type(card_inputs) is not tuple:
        raise ValueError("card_inputs must be a tuple")
    _require_text_tuple(evidence_reference_ids, "evidence_reference_ids")

    source_event = _validate_source_intake_decision(source_intake_decision)

    if source_event.source_family is NotificationSourceFamily.RECOVERY_SCAN_COMPLETED and source_event.listing_count == 0:
        if card_inputs:
            raise ValueError("zero-listing recovery must not produce card inputs")
        if source_event.safe_listing_reference_ids:
            raise ValueError("zero-listing recovery must not carry listing references")
        decision_evidence_reference_ids = _first_occurrence_union(
            source_intake_decision.evidence_reference_ids,
            source_event.evidence_reference_ids,
            evidence_reference_ids,
        )
        return NotificationListingCardProjectionDecision(
            decision_id=decision_id,
            authority=NotificationListingCardAuthority.NOTIFICATION_DELIVERY_SERVER,
            source_intake_decision=source_intake_decision,
            cards=(),
            status=NotificationListingCardProjectionStatus.NOT_APPLICABLE_NO_LISTINGS,
            listing_references_preserved=True,
            optional_fields_missing_allowed=True,
            display_rendering_authorized=False,
            delivery_attempt_authorized=False,
            provider_mapping_authorized=False,
            reason_codes=("listing-card-no-listings-not-applicable",),
            evidence_reference_ids=decision_evidence_reference_ids,
        )

    if len(card_inputs) != source_event.listing_count:
        raise ValueError("card_inputs must match source_event listing_count")
    if len(card_inputs) != len(source_event.safe_listing_reference_ids):
        raise ValueError("card_inputs must preserve safe listing references")
    if tuple(card_input.listing_reference_id for card_input in card_inputs) != source_event.safe_listing_reference_ids:
        raise ValueError("card_inputs must preserve listing reference order")

    listing_card_ids = tuple(card_input.listing_card_id for card_input in card_inputs)
    if len(set(listing_card_ids)) != len(listing_card_ids):
        raise ValueError("card_inputs must not contain duplicate listing_card_id values")

    listing_reference_ids = tuple(card_input.listing_reference_id for card_input in card_inputs)
    if len(set(listing_reference_ids)) != len(listing_reference_ids):
        raise ValueError("card_inputs must not contain duplicate listing_reference_id values")

    cards: list[NotificationListingCard] = []
    has_any_fields = False
    beacon_id = source_event.beacon_id
    assert beacon_id is not None

    for card_input in card_inputs:
        if type(card_input) is not NotificationListingCardInput:
            raise ValueError("card_inputs must contain NotificationListingCardInput")

        reason_class = _REASON_CLASS_BY_FAMILY[source_event.source_family]
        validated_field_facts: list[NotificationListingCardFieldFact] = []
        seen_field_classes: set[NotificationListingCardFieldClass] = set()

        for field_fact in card_input.field_facts:
            validated_field_fact = _validate_field_fact_safety(
                field_fact=field_fact,
                source_event=source_event,
                listing_reference_id=card_input.listing_reference_id,
            )
            if validated_field_fact.field_class in seen_field_classes:
                raise ValueError("card field facts must not repeat field classes")
            seen_field_classes.add(validated_field_fact.field_class)
            validated_field_facts.append(validated_field_fact)

        if validated_field_facts:
            has_any_fields = True

        card_evidence_reference_ids = _first_occurrence_union(
            source_intake_decision.evidence_reference_ids,
            source_event.evidence_reference_ids,
            card_input.evidence_reference_ids,
            *(field_fact.evidence_reference_ids for field_fact in validated_field_facts),
            evidence_reference_ids,
        )
        cards.append(
            NotificationListingCard(
                listing_card_id=card_input.listing_card_id,
                listing_reference_id=card_input.listing_reference_id,
                account_id=source_event.account_id,
                beacon_id=beacon_id,
                source_event_id=source_event.source_event_id,
                source_fact_id=source_event.source_fact_id,
                source_family=source_event.source_family,
                reason_class=reason_class,
                beacon_name_reference_id=card_input.beacon_name_reference_id,
                field_facts=tuple(validated_field_facts),
                correlation_id=source_event.correlation_id,
                causation_id=source_event.causation_id,
                evidence_reference_ids=card_evidence_reference_ids,
            )
        )

    decision_evidence_reference_ids = _first_occurrence_union(
        source_intake_decision.evidence_reference_ids,
        source_event.evidence_reference_ids,
        *(card_input.evidence_reference_ids for card_input in card_inputs),
        *(field_fact.evidence_reference_ids for card_input in card_inputs for field_fact in card_input.field_facts),
        evidence_reference_ids,
    )

    if has_any_fields:
        status = NotificationListingCardProjectionStatus.ACCEPTED_FIELDS
        reason_codes = ("listing-card-fields-accepted",)
    else:
        status = NotificationListingCardProjectionStatus.ACCEPTED_REFERENCE_ONLY
        reason_codes = ("listing-card-reference-only-accepted",)

    return NotificationListingCardProjectionDecision(
        decision_id=decision_id,
        authority=NotificationListingCardAuthority.NOTIFICATION_DELIVERY_SERVER,
        source_intake_decision=source_intake_decision,
        cards=tuple(cards),
        status=status,
        listing_references_preserved=True,
        optional_fields_missing_allowed=True,
        display_rendering_authorized=False,
        delivery_attempt_authorized=False,
        provider_mapping_authorized=False,
        reason_codes=reason_codes,
        evidence_reference_ids=decision_evidence_reference_ids,
    )


__all__ = (
    "ND10_TASK_ID",
    "NotificationListingCardAuthority",
    "NotificationListingCardReasonClass",
    "NotificationListingCardFieldClass",
    "NotificationListingCardValueClass",
    "NotificationListingCardProvenanceTier",
    "NotificationListingCardProjectionStatus",
    "NotificationListingCardFieldFact",
    "NotificationListingCardInput",
    "NotificationListingCard",
    "NotificationListingCardProjectionDecision",
    "project_notification_listing_cards",
)

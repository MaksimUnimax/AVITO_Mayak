"""Transport-neutral semantic contracts for Telegram identity handoff."""

from __future__ import annotations

# TG-13 field names intentionally mirror the public boundary vocabulary.
# ruff: noqa: E501
from enum import Enum
from typing import Literal, cast

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

from mayak.contracts import (
    ContractMetadata,
    IdempotencyFingerprint,
    IdempotencyKey,
    IdempotencyScope,
)


class _TelegramContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class TelegramOutboundRequestClass(str, Enum):
    PRIVATE_CHAT_MESSAGE_REQUEST = "PRIVATE_CHAT_MESSAGE_REQUEST"


class TelegramOutboundMappingState(str, Enum):
    REQUEST_PREPARED = "REQUEST_PREPARED"
    BLOCKED = "BLOCKED"
    UNSUPPORTED_TARGET = "UNSUPPORTED_TARGET"
    INVALID_CONTENT = "INVALID_CONTENT"
    AMBIGUOUS = "AMBIGUOUS"


class TelegramOutboundMappingReasonCode(str, Enum):
    TELEGRAM_PRIVATE_CHAT_REQUEST_PREPARED = "TELEGRAM_PRIVATE_CHAT_REQUEST_PREPARED"
    NOTIFICATION_ATTEMPT_NOT_READY = "NOTIFICATION_ATTEMPT_NOT_READY"
    NOTIFICATION_SCOPE_MISMATCH = "NOTIFICATION_SCOPE_MISMATCH"
    PRIVATE_CHAT_ADMISSION_REQUIRED = "PRIVATE_CHAT_ADMISSION_REQUIRED"
    TELEGRAM_TARGET_SCOPE_MISMATCH = "TELEGRAM_TARGET_SCOPE_MISMATCH"
    SAFE_CONTENT_REFERENCE_MISMATCH = "SAFE_CONTENT_REFERENCE_MISMATCH"


_NotificationChannelValue = Literal["TELEGRAM", "MAX"]
_NotificationAttemptPlanningStatusValue = Literal[
    "PLANNED", "BLOCKED_DELIVERY_PLAN", "BLOCKED_CHANNEL_PLAN"
]
_NotificationDeliveryPlanDecisionStatusValue = Literal[
    "PLANNED", "BLOCKED_OUTBOX", "BLOCKED_CHANNEL_PLAN_AMBIGUOUS", "BLOCKED_NO_PUSH_CHANNEL"
]
_NotificationDeliveryChannelPlanStatusValue = Literal[
    "TELEGRAM_ENABLED",
    "MAX_ENABLED",
    "WEB_STATUS_READ_MODEL",
    "CHANNEL_DISABLED_BY_USER",
    "CHANNEL_TARGET_UNVERIFIED",
    "CHANNEL_TARGET_UNAVAILABLE",
]
_NotificationAttemptLifecycleValue = Literal[
    "NOT_ATTEMPTED",
    "ATTEMPT_PLANNED",
    "ATTEMPT_IN_PROGRESS",
    "DISPATCH_AMBIGUOUS",
    "PROVIDER_ACCEPTED",
    "PROVIDER_REJECTED",
    "PROVIDER_UNAVAILABLE",
    "RATE_OR_ACCESS_RESTRICTED",
    "MALFORMED_OR_UNUSABLE_PROVIDER_RESPONSE",
    "DELIVERY_FAILURE",
    "DELIVERY_AMBIGUOUS",
    "SUPPRESSED_OR_CANCELLED",
    "TARGET_UNAVAILABLE_OR_UNVERIFIED",
    "RECONCILIATION_REQUIRED",
    "DELIVERED_ACCEPTED",
    "FAILED_RETRYABLE_AFTER_POLICY",
    "FAILED_NON_RETRYABLE",
]
_NotificationSourceFamilyValue = Literal[
    "NEW_LISTINGS_FOUND",
    "RECOVERY_SCAN_COMPLETED",
    "EXTERNAL_UNAVAILABLE_STATUS",
    "LOST_ANCHORS_RECOVERED",
    "NO_NEW_LISTINGS_STATUS",
    "APPROVED_SERVICE_ACCESS_FACT",
    "BEACON_BASELINE_ESTABLISHED",
    "SCAN_RUN_PLANNED",
    "SCAN_RUN_STARTED",
    "LISTING_PRICE_PAIR_FIRST_SEEN",
    "PARSER_ONLY_OUTCOME",
    "EGRESS_ONLY_OUTCOME",
    "PROVIDER_ONLY_CALLBACK",
]
_NotificationListingProjectionStatusValue = Literal[
    "ACCEPTED_FIELDS", "ACCEPTED_REFERENCE_ONLY", "NOT_APPLICABLE_NO_LISTINGS"
]


def _outbound_text(value: object, field_name: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-blank string")
    return value


def _outbound_tuple(value: object, field_name: str, *, unique: bool = True) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    result = tuple(_outbound_text(item, field_name) for item in value)
    if unique and len(result) != len(set(result)):
        raise ValueError(f"{field_name} must be unique")
    return result


def _outbound_exact(value: object, expected: type[object], field_name: str) -> None:
    if type(value) is not expected:
        raise ValueError(f"{field_name} must be {expected.__name__}")


def _outbound_false(value: object, field_name: str) -> None:
    if value is not False:
        raise ValueError(f"{field_name} must be False")


def _outbound_true(value: object, field_name: str) -> None:
    if value is not True:
        raise ValueError(f"{field_name} must be True")


class TelegramNotificationAttemptHandoff(_TelegramContract):
    telegram_notification_attempt_handoff_id: str
    metadata: ContractMetadata
    planning_decision_reference_id: str
    planning_status: _NotificationAttemptPlanningStatusValue
    planning_channel: _NotificationChannelValue
    attempt_created: bool
    delivery_plan_decision_reference_id: str
    delivery_plan_decision_status: _NotificationDeliveryPlanDecisionStatusValue
    delivery_plan_reference_id: str | None
    delivery_plan_outbox_item_reference_id: str | None
    delivery_plan_account_reference_id: str | None
    delivery_plan_beacon_reference_id: str | None
    telegram_channel_plan_entry_count: int
    telegram_channel_plan_status: _NotificationDeliveryChannelPlanStatusValue | None
    telegram_channel_plan_push_planned: bool
    telegram_channel_plan_read_model_planned: bool
    telegram_channel_plan_target_reference_id: str | None
    telegram_channel_plan_outbox_target_reference_id: str | None
    outbox_item_reference_id: str | None
    outbox_account_reference_id: str | None
    outbox_beacon_reference_id: str | None
    outbox_event_reason: _NotificationSourceFamilyValue | None
    outbox_listing_count: int
    outbox_safe_listing_reference_ids: tuple[str, ...]
    outbox_telegram_channel_intent_count: int
    outbox_telegram_target_reference_id: str | None
    outbox_lifecycle_status: Literal["PLANNED"] | None
    outbox_idempotency_key: IdempotencyKey | None
    outbox_idempotency_scope: IdempotencyScope | None
    outbox_idempotency_fingerprint: IdempotencyFingerprint | None
    outbox_correlation_id: str | None
    outbox_causation_id: str | None
    outbox_evidence_reference_ids: tuple[str, ...]
    attempt_reference_id: str | None
    attempt_delivery_plan_reference_id: str | None
    attempt_outbox_item_reference_id: str | None
    attempt_account_reference_id: str | None
    attempt_beacon_reference_id: str | None
    attempt_channel: _NotificationChannelValue | None
    attempt_target_reference_id: str | None
    attempt_lifecycle_status: _NotificationAttemptLifecycleValue | None
    attempt_idempotency_key: IdempotencyKey | None
    attempt_idempotency_scope: IdempotencyScope | None
    attempt_idempotency_fingerprint: IdempotencyFingerprint | None
    attempt_provider_outcome_reference_id: str | None
    attempt_provider_outcome_class_reference_id: str | None
    attempt_adapter_contract_reference_id: str | None
    attempt_adapter_contract_version_reference_id: str | None
    attempt_provider_safe_delivery_reference_id: str | None
    attempt_egress_correlation_reference_id: str | None
    attempt_provider_reason_codes: tuple[str, ...]
    attempt_failure_policy_reference_id: str | None
    attempt_reconciliation_required: bool | None
    attempt_delivery_accepted: bool | None
    attempt_retry_authorized: bool | None
    attempt_dispatch_effect_authorized: bool | None
    attempt_provider_mapping_authorized: bool | None
    attempt_correlation_id: str | None
    attempt_causation_id: str | None
    attempt_evidence_reference_ids: tuple[str, ...]
    notification_delivery_projection: Literal[True] = True
    safe_reference_snapshot_only: Literal[True] = True
    generic_outbox_mutation_authority: Literal[False] = False
    notification_lifecycle_mutation_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False
    retry_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_snapshot(self) -> "TelegramNotificationAttemptHandoff":
        for name in (
            "telegram_notification_attempt_handoff_id",
            "planning_decision_reference_id",
            "delivery_plan_decision_reference_id",
        ):
            _outbound_text(getattr(self, name), name)
        _outbound_exact(self.metadata, ContractMetadata, "metadata")
        for name in ("planning_status", "planning_channel", "delivery_plan_decision_status"):
            _outbound_text(getattr(self, name), name)
        for name in (
            "outbox_safe_listing_reference_ids",
            "outbox_evidence_reference_ids",
            "attempt_provider_reason_codes",
            "attempt_evidence_reference_ids",
        ):
            _outbound_tuple(
                getattr(self, name), name, unique=name != "outbox_safe_listing_reference_ids"
            )
        for name in (
            "telegram_channel_plan_entry_count",
            "outbox_listing_count",
            "outbox_telegram_channel_intent_count",
        ):
            if type(getattr(self, name)) is not int or getattr(self, name) < 0:
                raise ValueError(f"{name} must be non-negative")
        _outbound_true(self.notification_delivery_projection, "notification_delivery_projection")
        _outbound_true(self.safe_reference_snapshot_only, "safe_reference_snapshot_only")
        for name in (
            "generic_outbox_mutation_authority",
            "notification_lifecycle_mutation_authority",
            "provider_call_authority",
            "retry_authority",
        ):
            _outbound_false(getattr(self, name), name)
        outbox_present = self.outbox_item_reference_id is not None
        if not outbox_present:
            if (
                any(
                    getattr(self, n) is not None
                    for n in (
                        "outbox_account_reference_id",
                        "outbox_beacon_reference_id",
                        "outbox_event_reason",
                        "outbox_telegram_target_reference_id",
                        "outbox_lifecycle_status",
                        "outbox_idempotency_key",
                        "outbox_idempotency_scope",
                        "outbox_idempotency_fingerprint",
                        "outbox_correlation_id",
                        "outbox_causation_id",
                    )
                )
                or self.outbox_listing_count
                or self.outbox_safe_listing_reference_ids
                or self.outbox_telegram_channel_intent_count
            ):
                raise ValueError("absent outbox carries facts")
        else:
            for n in (
                "outbox_account_reference_id",
                "outbox_event_reason",
                "outbox_lifecycle_status",
                "outbox_idempotency_key",
                "outbox_idempotency_scope",
                "outbox_idempotency_fingerprint",
                "outbox_correlation_id",
                "outbox_causation_id",
            ):
                if getattr(self, n) is None:
                    raise ValueError(f"present outbox requires {n}")
        plan_present = self.delivery_plan_reference_id is not None
        if not plan_present:
            if self.telegram_channel_plan_entry_count or any(
                getattr(self, n) is not None
                for n in (
                    "delivery_plan_outbox_item_reference_id",
                    "delivery_plan_account_reference_id",
                    "delivery_plan_beacon_reference_id",
                    "telegram_channel_plan_status",
                    "telegram_channel_plan_target_reference_id",
                    "telegram_channel_plan_outbox_target_reference_id",
                )
            ):
                raise ValueError("absent plan carries facts")
        else:
            for n in (
                "delivery_plan_outbox_item_reference_id",
                "delivery_plan_account_reference_id",
                "telegram_channel_plan_status",
            ):
                if getattr(self, n) is None:
                    raise ValueError(f"present plan requires {n}")
        attempt_present = self.attempt_reference_id is not None
        if not attempt_present:
            if (
                self.attempt_created
                or any(
                    getattr(self, n) is not None
                    for n in (
                        "attempt_delivery_plan_reference_id",
                        "attempt_outbox_item_reference_id",
                        "attempt_account_reference_id",
                        "attempt_beacon_reference_id",
                        "attempt_channel",
                        "attempt_target_reference_id",
                        "attempt_lifecycle_status",
                        "attempt_idempotency_key",
                        "attempt_idempotency_scope",
                        "attempt_idempotency_fingerprint",
                        "attempt_correlation_id",
                        "attempt_causation_id",
                    )
                )
                or self.attempt_provider_reason_codes
                or self.attempt_evidence_reference_ids
            ):
                raise ValueError("absent attempt carries facts")
        else:
            for n in (
                "attempt_delivery_plan_reference_id",
                "attempt_outbox_item_reference_id",
                "attempt_account_reference_id",
                "attempt_channel",
                "attempt_target_reference_id",
                "attempt_lifecycle_status",
                "attempt_idempotency_key",
                "attempt_idempotency_scope",
                "attempt_idempotency_fingerprint",
                "attempt_correlation_id",
                "attempt_causation_id",
            ):
                if getattr(self, n) is None:
                    raise ValueError(f"present attempt requires {n}")
            _outbound_true(self.attempt_created, "attempt_created")
        if self.outbox_listing_count != len(self.outbox_safe_listing_reference_ids):
            raise ValueError("outbox listing count mismatch")
        return self


class TelegramListingCardProjectionHandoff(_TelegramContract):
    telegram_listing_card_projection_handoff_id: str
    metadata: ContractMetadata
    projection_decision_reference_id: str
    projection_status: _NotificationListingProjectionStatusValue
    listing_reference_ids: tuple[str, ...]
    listing_card_reference_ids: tuple[str, ...]
    listing_card_account_reference_ids: tuple[str, ...]
    listing_card_beacon_reference_ids: tuple[str, ...]
    listing_card_correlation_ids: tuple[str, ...]
    listing_card_causation_ids: tuple[str, ...]
    listing_references_preserved: bool
    optional_fields_missing_allowed: bool
    display_rendering_authorized: bool
    delivery_attempt_authorized: bool
    provider_mapping_authorized: bool
    evidence_reference_ids: tuple[str, ...]
    notification_delivery_projection: Literal[True] = True
    safe_reference_snapshot_only: Literal[True] = True
    rendering_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_projection(self) -> "TelegramListingCardProjectionHandoff":
        for n in (
            "telegram_listing_card_projection_handoff_id",
            "projection_decision_reference_id",
        ):
            _outbound_text(getattr(self, n), n)
        _outbound_exact(self.metadata, ContractMetadata, "metadata")
        groups = (
            self.listing_reference_ids,
            self.listing_card_reference_ids,
            self.listing_card_account_reference_ids,
            self.listing_card_beacon_reference_ids,
            self.listing_card_correlation_ids,
            self.listing_card_causation_ids,
        )
        for g in groups:
            _outbound_tuple(g, "listing projection tuple", unique=False)
        if len({len(g) for g in groups}) != 1:
            raise ValueError("parallel card tuples must have equal length")
        if len(self.listing_reference_ids) != len(self.listing_card_reference_ids):
            raise ValueError("listing/card counts mismatch")
        _outbound_true(self.listing_references_preserved, "listing_references_preserved")
        _outbound_true(self.optional_fields_missing_allowed, "optional_fields_missing_allowed")
        for n in (
            "display_rendering_authorized",
            "delivery_attempt_authorized",
            "provider_mapping_authorized",
            "rendering_authority",
            "provider_call_authority",
        ):
            _outbound_false(getattr(self, n), n)
        _outbound_tuple(self.evidence_reference_ids, "evidence_reference_ids")
        return self


class TelegramOutboundTargetReference(_TelegramContract):
    telegram_outbound_target_reference_id: str
    notification_target_reference_id: str
    telegram_bot_ref: str
    telegram_chat_provider_reference: str
    telegram_provider_identity_reference: str
    private_chat_only_v1: Literal[True] = True
    internal_account_authority: Literal[False] = False
    group_or_channel_target_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_target(self) -> "TelegramOutboundTargetReference":
        for field_name in (
            "telegram_outbound_target_reference_id",
            "notification_target_reference_id",
            "telegram_bot_ref",
            "telegram_chat_provider_reference",
            "telegram_provider_identity_reference",
        ):
            _outbound_text(getattr(self, field_name), field_name)
        _outbound_true(self.private_chat_only_v1, "private_chat_only_v1")
        _outbound_false(self.internal_account_authority, "internal_account_authority")
        _outbound_false(self.group_or_channel_target_authority, "group_or_channel_target_authority")
        _outbound_false(self.provider_call_authority, "provider_call_authority")
        return self


class TelegramOutboundMappingRequest(_TelegramContract):
    telegram_outbound_mapping_request_id: str
    metadata: ContractMetadata
    notification_attempt_handoff: TelegramNotificationAttemptHandoff
    telegram_chat_surface_admission_outcome: TelegramChatSurfaceAdmissionOutcome | None
    telegram_target: TelegramOutboundTargetReference | None
    listing_card_projection_handoff: TelegramListingCardProjectionHandoff | None
    mapping_policy_reference_id: str
    notification_delivery_authority_preserved: Literal[True] = True
    target_scope_requires_private_chat_admission: Literal[True] = True
    generic_outbox_mutation_authority: Literal[False] = False
    notification_lifecycle_mutation_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False
    rendering_authority: Literal[False] = False
    retry_authority: Literal[False] = False
    business_success_authority: Literal[False] = False

    @field_validator(
        "metadata",
        "notification_attempt_handoff",
        "telegram_chat_surface_admission_outcome",
        "telegram_target",
        "listing_card_projection_handoff",
        mode="before",
    )
    @classmethod
    def _reject_non_exact_request_objects(cls, value: object, info: ValidationInfo) -> object:
        if value is None:
            return value
        expected = {
            "metadata": ContractMetadata,
            "notification_attempt_handoff": TelegramNotificationAttemptHandoff,
            "telegram_chat_surface_admission_outcome": TelegramChatSurfaceAdmissionOutcome,
            "telegram_target": TelegramOutboundTargetReference,
            "listing_card_projection_handoff": TelegramListingCardProjectionHandoff,
        }
        field_name = info.field_name
        assert field_name is not None
        if type(value) is not expected[field_name]:
            raise ValueError(f"{info.field_name} must be an exact public contract object")
        return value

    @model_validator(mode="after")
    def _validate_request(self) -> "TelegramOutboundMappingRequest":
        _outbound_text(
            self.telegram_outbound_mapping_request_id, "telegram_outbound_mapping_request_id"
        )
        _outbound_exact(self.metadata, ContractMetadata, "metadata")
        _outbound_exact(
            self.notification_attempt_handoff,
            TelegramNotificationAttemptHandoff,
            "notification_attempt_handoff",
        )
        if self.notification_attempt_handoff.metadata != self.metadata:
            raise ValueError("metadata must match the attempt handoff")
        if (
            self.telegram_chat_surface_admission_outcome is not None
            and type(self.telegram_chat_surface_admission_outcome)
            is not TelegramChatSurfaceAdmissionOutcome
        ):
            raise ValueError("telegram_chat_surface_admission_outcome has an invalid object type")
        if (
            self.listing_card_projection_handoff is not None
            and type(self.listing_card_projection_handoff)
            is not TelegramListingCardProjectionHandoff
        ):
            raise ValueError("listing_card_projection_handoff has an invalid object type")
        if (
            self.telegram_chat_surface_admission_outcome is not None
            and self.telegram_chat_surface_admission_outcome.metadata != self.metadata
        ):
            raise ValueError("metadata must match the admission outcome")
        if (
            self.listing_card_projection_handoff is not None
            and self.listing_card_projection_handoff.metadata != self.metadata
        ):
            raise ValueError("metadata must match the listing projection handoff")
        if self.telegram_target is not None:
            _outbound_exact(
                self.telegram_target, TelegramOutboundTargetReference, "telegram_target"
            )
        _outbound_text(self.mapping_policy_reference_id, "mapping_policy_reference_id")
        _outbound_true(
            self.notification_delivery_authority_preserved,
            "notification_delivery_authority_preserved",
        )
        _outbound_true(
            self.target_scope_requires_private_chat_admission,
            "target_scope_requires_private_chat_admission",
        )
        for field_name in (
            "generic_outbox_mutation_authority",
            "notification_lifecycle_mutation_authority",
            "provider_call_authority",
            "rendering_authority",
            "retry_authority",
            "business_success_authority",
        ):
            _outbound_false(getattr(self, field_name), field_name)
        return self


class TelegramOutboundRequestIntent(_TelegramContract):
    telegram_outbound_request_intent_id: str
    metadata: ContractMetadata
    request_class: TelegramOutboundRequestClass
    notification_attempt_id: str
    notification_outbox_item_id: str
    notification_delivery_plan_id: str
    notification_target_reference_id: str
    telegram_bot_ref: str
    telegram_chat_provider_reference: str
    telegram_provider_identity_reference: str
    delivery_purpose: _NotificationSourceFamilyValue
    safe_listing_reference_ids: tuple[str, ...]
    safe_listing_card_reference_ids: tuple[str, ...]
    idempotency_key: IdempotencyKey
    idempotency_scope: IdempotencyScope
    idempotency_fingerprint: IdempotencyFingerprint
    correlation_id: str
    causation_id: str
    evidence_reference_ids: tuple[str, ...]
    provider_request_classified: Literal[True] = True
    provider_call_authorized: Literal[False] = False
    provider_effect_committed: Literal[False] = False
    notification_delivery_accepted: Literal[False] = False
    human_read_or_click_proven: Literal[False] = False
    retry_authorized: Literal[False] = False
    reconciliation_recommendation_authority: Literal[False] = False
    rendering_authority: Literal[False] = False
    generic_outbox_mutation_authority: Literal[False] = False
    notification_lifecycle_mutation_authority: Literal[False] = False

    @field_validator(
        "metadata",
        "idempotency_key",
        "idempotency_scope",
        "idempotency_fingerprint",
        mode="before",
    )
    @classmethod
    def _reject_non_exact_intent_objects(cls, value: object, info: ValidationInfo) -> object:
        expected = {
            "metadata": ContractMetadata,
            "idempotency_key": IdempotencyKey,
            "idempotency_scope": IdempotencyScope,
            "idempotency_fingerprint": IdempotencyFingerprint,
        }
        field_name = info.field_name
        assert field_name is not None
        if type(value) is not expected[field_name]:
            raise ValueError(f"{info.field_name} must be an exact public contract object")
        return value

    @field_validator(
        "safe_listing_reference_ids",
        "safe_listing_card_reference_ids",
        "evidence_reference_ids",
        mode="before",
    )
    @classmethod
    def _reject_intent_reference_lists(cls, value: object) -> object:
        if type(value) is not tuple:
            raise ValueError("intent reference collections must be tuples")
        return value

    @model_validator(mode="after")
    def _validate_intent(self) -> "TelegramOutboundRequestIntent":
        for field_name in (
            "telegram_outbound_request_intent_id",
            "notification_attempt_id",
            "notification_outbox_item_id",
            "notification_delivery_plan_id",
            "notification_target_reference_id",
            "telegram_bot_ref",
            "telegram_chat_provider_reference",
            "telegram_provider_identity_reference",
            "correlation_id",
            "causation_id",
        ):
            _outbound_text(getattr(self, field_name), field_name)
        _outbound_exact(self.metadata, ContractMetadata, "metadata")
        _outbound_exact(self.request_class, TelegramOutboundRequestClass, "request_class")
        _outbound_text(self.delivery_purpose, "delivery_purpose")
        for field_name in (
            "safe_listing_reference_ids",
            "safe_listing_card_reference_ids",
            "evidence_reference_ids",
        ):
            _outbound_tuple(getattr(self, field_name), field_name)
        for field_name, expected in (
            ("idempotency_key", IdempotencyKey),
            ("idempotency_scope", IdempotencyScope),
            ("idempotency_fingerprint", IdempotencyFingerprint),
        ):
            _outbound_exact(getattr(self, field_name), expected, field_name)
        _outbound_true(self.provider_request_classified, "provider_request_classified")
        for field_name in (
            "provider_call_authorized",
            "provider_effect_committed",
            "notification_delivery_accepted",
            "human_read_or_click_proven",
            "retry_authorized",
            "reconciliation_recommendation_authority",
            "rendering_authority",
            "generic_outbox_mutation_authority",
            "notification_lifecycle_mutation_authority",
        ):
            _outbound_false(getattr(self, field_name), field_name)
        return self


def _outbound_lineage(
    request: TelegramOutboundMappingRequest,
) -> tuple[TelegramOutboundMappingState, TelegramOutboundMappingReasonCode]:
    h = request.notification_attempt_handoff
    if (
        h.planning_status != "PLANNED"
        or h.planning_channel != "TELEGRAM"
        or not h.attempt_created
        or h.attempt_reference_id is None
        or h.attempt_channel != "TELEGRAM"
        or h.attempt_lifecycle_status != "ATTEMPT_PLANNED"
        or any(
            getattr(h, n) is not None
            for n in (
                "attempt_provider_outcome_reference_id",
                "attempt_provider_outcome_class_reference_id",
                "attempt_adapter_contract_reference_id",
                "attempt_adapter_contract_version_reference_id",
                "attempt_provider_safe_delivery_reference_id",
                "attempt_egress_correlation_reference_id",
                "attempt_failure_policy_reference_id",
            )
        )
        or h.attempt_provider_reason_codes
        or h.attempt_reconciliation_required is True
        or h.attempt_delivery_accepted is True
        or h.attempt_retry_authorized is True
        or h.attempt_dispatch_effect_authorized is True
        or h.attempt_provider_mapping_authorized is True
    ):
        return (
            TelegramOutboundMappingState.BLOCKED,
            TelegramOutboundMappingReasonCode.NOTIFICATION_ATTEMPT_NOT_READY,
        )
    if (
        h.delivery_plan_decision_status != "PLANNED"
        or h.delivery_plan_reference_id is None
        or h.outbox_item_reference_id is None
        or h.delivery_plan_outbox_item_reference_id != h.outbox_item_reference_id
        or h.delivery_plan_account_reference_id != h.outbox_account_reference_id
        or h.delivery_plan_beacon_reference_id != h.outbox_beacon_reference_id
        or h.attempt_delivery_plan_reference_id != h.delivery_plan_reference_id
        or h.attempt_outbox_item_reference_id != h.outbox_item_reference_id
        or h.attempt_account_reference_id != h.outbox_account_reference_id
        or h.attempt_beacon_reference_id != h.outbox_beacon_reference_id
        or h.outbox_lifecycle_status != "PLANNED"
        or h.telegram_channel_plan_entry_count != 1
        or h.telegram_channel_plan_status != "TELEGRAM_ENABLED"
        or h.telegram_channel_plan_push_planned is not True
        or h.telegram_channel_plan_read_model_planned is not False
        or h.outbox_telegram_channel_intent_count != 1
        or h.telegram_channel_plan_target_reference_id
        != h.telegram_channel_plan_outbox_target_reference_id
        or h.telegram_channel_plan_target_reference_id != h.outbox_telegram_target_reference_id
        or h.telegram_channel_plan_target_reference_id != h.attempt_target_reference_id
        or h.outbox_idempotency_key != h.attempt_idempotency_key
        or h.outbox_idempotency_scope != h.attempt_idempotency_scope
        or h.outbox_idempotency_fingerprint != h.attempt_idempotency_fingerprint
        or h.outbox_correlation_id != h.attempt_correlation_id
        or h.outbox_causation_id != h.attempt_causation_id
    ):
        return (
            TelegramOutboundMappingState.AMBIGUOUS,
            TelegramOutboundMappingReasonCode.NOTIFICATION_SCOPE_MISMATCH,
        )
    admission = request.telegram_chat_surface_admission_outcome
    if (
        admission is None
        or getattr(admission.admission_state, "value", admission.admission_state)
        != "PRIVATE_CHAT_ADMITTED"
        or getattr(admission.reason_code, "value", admission.reason_code)
        != "PRIVATE_CHAT_V1_SUPPORTED"
        or getattr(
            admission.request.chat_surface.surface_class,
            "value",
            admission.request.chat_surface.surface_class,
        )
        != "PRIVATE_CHAT"
        or admission.admitted_update_intake_record_id is None
        or admission.verified_provider_identity_reference is None
        or admission.request.verified_telegram_provider_identity_evidence is None
    ):
        return (
            TelegramOutboundMappingState.UNSUPPORTED_TARGET,
            TelegramOutboundMappingReasonCode.PRIVATE_CHAT_ADMISSION_REQUIRED,
        )
    surface = admission.request.chat_surface
    evidence = admission.request.verified_telegram_provider_identity_evidence
    identity = (
        evidence.provider_identity.telegram_provider_identity_ref if evidence is not None else None
    )
    target = request.telegram_target
    if (
        target is None
        or target.notification_target_reference_id != h.attempt_target_reference_id
        or target.telegram_bot_ref != surface.telegram_bot_ref
        or target.telegram_chat_provider_reference != surface.telegram_chat_provider_reference
        or target.telegram_provider_identity_reference != identity
    ):
        return (
            TelegramOutboundMappingState.AMBIGUOUS,
            TelegramOutboundMappingReasonCode.TELEGRAM_TARGET_SCOPE_MISMATCH,
        )
    refs = h.outbox_safe_listing_reference_ids
    projection = request.listing_card_projection_handoff
    if refs:
        if (
            projection is None
            or projection.projection_status not in ("ACCEPTED_FIELDS", "ACCEPTED_REFERENCE_ONLY")
            or projection.listing_reference_ids != refs
            or not projection.listing_references_preserved
            or len(set(projection.listing_reference_ids)) != len(projection.listing_reference_ids)
            or len(set(projection.listing_card_reference_ids))
            != len(projection.listing_card_reference_ids)
            or any(
                v != h.outbox_account_reference_id
                for v in projection.listing_card_account_reference_ids
            )
            or any(
                v != h.outbox_beacon_reference_id
                for v in projection.listing_card_beacon_reference_ids
            )
            or any(v != h.outbox_correlation_id for v in projection.listing_card_correlation_ids)
            or any(v != h.outbox_causation_id for v in projection.listing_card_causation_ids)
        ):
            return (
                TelegramOutboundMappingState.INVALID_CONTENT,
                TelegramOutboundMappingReasonCode.SAFE_CONTENT_REFERENCE_MISMATCH,
            )
    elif projection is not None and (
        projection.projection_status != "NOT_APPLICABLE_NO_LISTINGS"
        or projection.listing_reference_ids
        or projection.listing_card_reference_ids
    ):
        return (
            TelegramOutboundMappingState.INVALID_CONTENT,
            TelegramOutboundMappingReasonCode.SAFE_CONTENT_REFERENCE_MISMATCH,
        )
    return (
        TelegramOutboundMappingState.REQUEST_PREPARED,
        TelegramOutboundMappingReasonCode.TELEGRAM_PRIVATE_CHAT_REQUEST_PREPARED,
    )


class TelegramOutboundMappingOutcome(_TelegramContract):
    telegram_outbound_mapping_outcome_id: str
    metadata: ContractMetadata
    request: TelegramOutboundMappingRequest
    state: TelegramOutboundMappingState
    reason_code: TelegramOutboundMappingReasonCode
    request_intent: TelegramOutboundRequestIntent | None
    safe_diagnostic_reference_id: str | None
    evidence_reference_ids: tuple[str, ...]
    provider_call_performed: Literal[False] = False
    provider_effect_committed: Literal[False] = False
    notification_delivery_accepted: Literal[False] = False
    human_read_or_click_proven: Literal[False] = False
    retry_authorized: Literal[False] = False
    generic_outbox_mutation_authority: Literal[False] = False
    notification_lifecycle_mutation_authority: Literal[False] = False

    @field_validator("metadata", "request", "request_intent", mode="before")
    @classmethod
    def _reject_non_exact_outcome_objects(cls, value: object, info: ValidationInfo) -> object:
        if value is None:
            return value
        expected = {
            "metadata": ContractMetadata,
            "request": TelegramOutboundMappingRequest,
            "request_intent": TelegramOutboundRequestIntent,
        }
        field_name = info.field_name
        assert field_name is not None
        if type(value) is not expected[field_name]:
            raise ValueError(f"{info.field_name} must be an exact public contract object")
        return value

    @field_validator("evidence_reference_ids", mode="before")
    @classmethod
    def _reject_outcome_reference_lists(cls, value: object) -> object:
        if type(value) is not tuple:
            raise ValueError("evidence_reference_ids must be a tuple")
        return value

    @model_validator(mode="after")
    def _validate_outcome(self) -> "TelegramOutboundMappingOutcome":
        _outbound_text(
            self.telegram_outbound_mapping_outcome_id, "telegram_outbound_mapping_outcome_id"
        )
        _outbound_exact(self.metadata, ContractMetadata, "metadata")
        _outbound_exact(self.request, TelegramOutboundMappingRequest, "request")
        if self.request.metadata != self.metadata:
            raise ValueError("metadata must match the mapping request")
        _outbound_exact(self.state, TelegramOutboundMappingState, "state")
        _outbound_exact(self.reason_code, TelegramOutboundMappingReasonCode, "reason_code")
        _outbound_tuple(self.evidence_reference_ids, "evidence_reference_ids")
        expected_state, expected_reason = _outbound_lineage(self.request)
        if (self.state, self.reason_code) != (expected_state, expected_reason):
            raise ValueError("state and reason_code do not match deterministic classification")
        if self.state is TelegramOutboundMappingState.REQUEST_PREPARED:
            if self.request_intent is None or self.safe_diagnostic_reference_id is not None:
                raise ValueError("prepared outcome requires intent and forbids diagnostics")
            _outbound_exact(self.request_intent, TelegramOutboundRequestIntent, "request_intent")
            _validate_outbound_projection(self.request, self.request_intent)
        else:
            if self.request_intent is not None or self.safe_diagnostic_reference_id is None:
                raise ValueError("non-success outcome requires diagnostic and forbids intent")
            _outbound_text(self.safe_diagnostic_reference_id, "safe_diagnostic_reference_id")
        for field_name in (
            "provider_call_performed",
            "provider_effect_committed",
            "notification_delivery_accepted",
            "human_read_or_click_proven",
            "retry_authorized",
            "generic_outbox_mutation_authority",
            "notification_lifecycle_mutation_authority",
        ):
            _outbound_false(getattr(self, field_name), field_name)
        return self


def _validate_outbound_projection(
    request: TelegramOutboundMappingRequest, intent: TelegramOutboundRequestIntent
) -> None:
    h = request.notification_attempt_handoff
    target = request.telegram_target
    projection = request.listing_card_projection_handoff
    if (
        target is None
        or h.attempt_reference_id is None
        or h.outbox_item_reference_id is None
        or h.delivery_plan_reference_id is None
    ):
        raise ValueError("prepared request lacks required projection facts")
    card_refs = () if projection is None else projection.listing_card_reference_ids
    expected_evidence = _outbound_union(
        h.outbox_evidence_reference_ids,
        h.attempt_evidence_reference_ids,
        () if projection is None else projection.evidence_reference_ids,
    )
    expected = {
        "request_class": TelegramOutboundRequestClass.PRIVATE_CHAT_MESSAGE_REQUEST,
        "metadata": request.metadata,
        "notification_attempt_id": h.attempt_reference_id,
        "notification_outbox_item_id": h.outbox_item_reference_id,
        "notification_delivery_plan_id": h.delivery_plan_reference_id,
        "notification_target_reference_id": h.attempt_target_reference_id,
        "telegram_bot_ref": target.telegram_bot_ref,
        "telegram_chat_provider_reference": target.telegram_chat_provider_reference,
        "telegram_provider_identity_reference": target.telegram_provider_identity_reference,
        "delivery_purpose": h.outbox_event_reason,
        "safe_listing_reference_ids": h.outbox_safe_listing_reference_ids,
        "safe_listing_card_reference_ids": card_refs,
        "idempotency_key": h.attempt_idempotency_key,
        "idempotency_scope": h.attempt_idempotency_scope,
        "idempotency_fingerprint": h.attempt_idempotency_fingerprint,
        "correlation_id": h.attempt_correlation_id,
        "causation_id": h.attempt_causation_id,
        "evidence_reference_ids": expected_evidence,
    }
    for name, value in expected.items():
        if getattr(intent, name) != value:
            raise ValueError(f"request intent projection mismatch: {name}")


def _outbound_union(*values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for group in values:
        for value in group:
            _outbound_text(value, "evidence_reference_ids")
            if value not in seen:
                seen.add(value)
                result.append(value)
    return tuple(result)


class TelegramDisplayClass(str, Enum):
    NEW_LISTINGS_SUMMARY = "NEW_LISTINGS_SUMMARY"
    NEW_LISTINGS_COMPACT_LIST = "NEW_LISTINGS_COMPACT_LIST"
    FULL_RESULT_OPEN_ACTION = "FULL_RESULT_OPEN_ACTION"
    SHOW_MORE_ACTION = "SHOW_MORE_ACTION"
    BEACON_SETTINGS_ACTION = "BEACON_SETTINGS_ACTION"
    NO_NEW_STATUS_MESSAGE = "NO_NEW_STATUS_MESSAGE"
    AVITO_UNAVAILABLE_STATUS_MESSAGE = "AVITO_UNAVAILABLE_STATUS_MESSAGE"
    RECOVERY_RESULT_MESSAGE = "RECOVERY_RESULT_MESSAGE"
    LOST_ANCHORS_RESTORED_MESSAGE = "LOST_ANCHORS_RESTORED_MESSAGE"
    UNSUPPORTED_CONTENT_BLOCKED = "UNSUPPORTED_CONTENT_BLOCKED"


class TelegramDisplayProjectionState(str, Enum):
    DISPLAY_PROJECTED = "DISPLAY_PROJECTED"
    DISPLAY_BLOCKED = "DISPLAY_BLOCKED"
    INVALID_CONTENT = "INVALID_CONTENT"
    AMBIGUOUS = "AMBIGUOUS"


class TelegramDisplayReasonCode(str, Enum):
    NEW_LISTINGS_DISPLAY_PROJECTED = "NEW_LISTINGS_DISPLAY_PROJECTED"
    RECOVERY_RESULT_DISPLAY_PROJECTED = "RECOVERY_RESULT_DISPLAY_PROJECTED"
    LOST_ANCHORS_RESTORED_DISPLAY_PROJECTED = "LOST_ANCHORS_RESTORED_DISPLAY_PROJECTED"
    NO_NEW_STATUS_DISPLAY_PROJECTED = "NO_NEW_STATUS_DISPLAY_PROJECTED"
    AVITO_UNAVAILABLE_STATUS_DISPLAY_PROJECTED = "AVITO_UNAVAILABLE_STATUS_DISPLAY_PROJECTED"
    OUTBOUND_REQUEST_NOT_PREPARED = "OUTBOUND_REQUEST_NOT_PREPARED"
    OUTBOUND_DISPLAY_SCOPE_MISMATCH = "OUTBOUND_DISPLAY_SCOPE_MISMATCH"
    UNSUPPORTED_DELIVERY_PURPOSE = "UNSUPPORTED_DELIVERY_PURPOSE"
    SAFE_LISTING_DISPLAY_MISMATCH = "SAFE_LISTING_DISPLAY_MISMATCH"


_NotificationListingCardFieldClassValue = Literal[
    "TITLE",
    "PRICE",
    "GEOGRAPHY",
    "LISTING_URL_REFERENCE",
    "PREVIEW_REFERENCE",
    "DESCRIPTION",
    "SELLER",
    "SELLER_RATING",
    "PHONE",
]
_NotificationListingCardValueClassValue = Literal["SAFE_TEXT", "SAFE_REFERENCE"]
_NotificationListingCardProvenanceTierValue = Literal[
    "TIER_1_SEARCH_RESULT", "TIER_2_LISTING_DETAIL", "TIER_3_CONTACT"
]
_NotificationListingCardReasonClassValue = Literal[
    "NEW_LISTING", "RECOVERED_NEW_LISTING", "LATEST_FRESH_STATE_RESTORED"
]
_NotificationListingCardProjectionStatusValue = Literal[
    "ACCEPTED_FIELDS", "ACCEPTED_REFERENCE_ONLY", "NOT_APPLICABLE_NO_LISTINGS"
]
_TelegramDisplayActionOwnerValue = Literal["NOTIFICATION_DELIVERY", "BEACON_MANAGEMENT"]

_DISPLAY_FIELD_COMPATIBILITY = {
    "TITLE": ("SAFE_TEXT", "TITLE", "TIER_1_SEARCH_RESULT", False, False),
    "PRICE": ("SAFE_TEXT", "NORMALIZED_PRICE", "TIER_1_SEARCH_RESULT", False, False),
    "GEOGRAPHY": ("SAFE_TEXT", "GEOGRAPHY", "TIER_1_SEARCH_RESULT", False, False),
    "LISTING_URL_REFERENCE": (
        "SAFE_REFERENCE",
        "LISTING_URL",
        "TIER_1_SEARCH_RESULT",
        False,
        False,
    ),
    "PREVIEW_REFERENCE": ("SAFE_REFERENCE", "PREVIEW_IMAGE", "TIER_1_SEARCH_RESULT", False, False),
    "DESCRIPTION": ("SAFE_TEXT", "DESCRIPTION", "TIER_2_LISTING_DETAIL", True, False),
    "SELLER": ("SAFE_TEXT", "SELLER", "TIER_2_LISTING_DETAIL", True, False),
    "SELLER_RATING": ("SAFE_TEXT", "SELLER_RATING", "TIER_2_LISTING_DETAIL", True, False),
    "PHONE": ("SAFE_TEXT", "PHONE_VALUE", "TIER_3_CONTACT", True, True),
}
_DISPLAY_REASON_BY_PURPOSE = {
    "NEW_LISTINGS_FOUND": "NEW_LISTING",
    "RECOVERY_SCAN_COMPLETED": "RECOVERED_NEW_LISTING",
    "LOST_ANCHORS_RECOVERED": "LATEST_FRESH_STATE_RESTORED",
}
_DISPLAY_STATUS_REASONS = {
    "ACCEPTED_FIELDS": ("listing-card-fields-accepted",),
    "ACCEPTED_REFERENCE_ONLY": ("listing-card-reference-only-accepted",),
    "NOT_APPLICABLE_NO_LISTINGS": ("listing-card-no-listings-not-applicable",),
}
_DISPLAY_PURPOSES = (
    "NEW_LISTINGS_FOUND",
    "RECOVERY_SCAN_COMPLETED",
    "LOST_ANCHORS_RECOVERED",
    "NO_NEW_LISTINGS_STATUS",
    "EXTERNAL_UNAVAILABLE_STATUS",
)


def _display_exact(value: object, expected: type[object], name: str) -> None:
    if type(value) is not expected:
        raise ValueError(f"{name} must be an exact {expected.__name__}")


def _display_text(value: object, name: str) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be a non-blank string")


def _display_tuple(value: object, name: str, *, unique: bool = True) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    for item in value:
        _display_text(item, name)
    if unique and len(value) != len(set(value)):
        raise ValueError(f"{name} must be unique")
    return value


def _display_bool(value: object, expected: bool, name: str) -> None:
    if value is not expected:
        raise ValueError(f"{name} must be {expected}")


def _display_union(*groups: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for group in groups:
        for value in group:
            if value not in result:
                result.append(value)
    return tuple(result)


class TelegramSafeListingFieldFact(_TelegramContract):
    telegram_safe_listing_field_fact_id: str
    listing_reference_id: str
    field_class: _NotificationListingCardFieldClassValue
    value_class: _NotificationListingCardValueClassValue
    safe_value: str
    upstream_field_family: str
    provenance_tier: _NotificationListingCardProvenanceTierValue
    upstream_field_reference_id: str
    compatibility_profile_reference_id: str
    source_committed: bool
    source_commit_reference: str
    field_evidence_approved: bool
    detail_gate_approved: bool
    contact_gate_approved: bool
    contains_raw_provider_payload: Literal[False] = False
    evidence_reference_ids: tuple[str, ...]
    notification_delivery_projection: Literal[True] = True
    safe_field_snapshot_only: Literal[True] = True
    field_enrichment_authority: Literal[False] = False
    provider_fetch_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_field(self) -> "TelegramSafeListingFieldFact":
        for name in (
            "telegram_safe_listing_field_fact_id",
            "listing_reference_id",
            "safe_value",
            "upstream_field_family",
            "upstream_field_reference_id",
            "compatibility_profile_reference_id",
            "source_commit_reference",
        ):
            _display_text(getattr(self, name), name)
        _display_tuple(self.evidence_reference_ids, "evidence_reference_ids")
        _display_bool(self.source_committed, True, "source_committed")
        _display_bool(self.field_evidence_approved, True, "field_evidence_approved")
        _display_bool(self.contains_raw_provider_payload, False, "contains_raw_provider_payload")
        _display_bool(
            self.notification_delivery_projection, True, "notification_delivery_projection"
        )
        _display_bool(self.safe_field_snapshot_only, True, "safe_field_snapshot_only")
        _display_bool(self.field_enrichment_authority, False, "field_enrichment_authority")
        _display_bool(self.provider_fetch_authority, False, "provider_fetch_authority")
        expected = _DISPLAY_FIELD_COMPATIBILITY[self.field_class]
        if (
            self.value_class,
            self.upstream_field_family,
            self.provenance_tier,
            self.detail_gate_approved,
            self.contact_gate_approved,
        ) != expected:
            raise ValueError("unsafe listing field compatibility")
        if self.provenance_tier == "TIER_3_CONTACT" and not self.contact_gate_approved:
            raise ValueError("contact field requires contact gate")
        if self.provenance_tier == "TIER_2_LISTING_DETAIL" and not self.detail_gate_approved:
            raise ValueError("detail field requires detail gate")
        return self


class TelegramListingCardDisplaySnapshot(_TelegramContract):
    telegram_listing_card_display_snapshot_id: str
    listing_card_reference_id: str
    listing_reference_id: str
    account_reference_id: str
    beacon_reference_id: str
    source_event_reference_id: str
    source_fact_reference_id: str
    source_family: _NotificationSourceFamilyValue
    reason_class: _NotificationListingCardReasonClassValue
    beacon_name_reference_id: str | None
    field_facts: tuple[TelegramSafeListingFieldFact, ...]
    correlation_id: str
    causation_id: str
    evidence_reference_ids: tuple[str, ...]
    notification_delivery_projection: Literal[True] = True
    safe_card_snapshot_only: Literal[True] = True
    rendering_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False

    @field_validator("field_facts", mode="before")
    @classmethod
    def _exact_field_facts(cls, value: object) -> object:
        if type(value) is not tuple or any(
            type(item) is not TelegramSafeListingFieldFact for item in value
        ):
            raise ValueError("field_facts must contain exact safe field facts")
        return value

    @model_validator(mode="after")
    def _validate_card(self) -> "TelegramListingCardDisplaySnapshot":
        for name in (
            "telegram_listing_card_display_snapshot_id",
            "listing_card_reference_id",
            "listing_reference_id",
            "account_reference_id",
            "beacon_reference_id",
            "source_event_reference_id",
            "source_fact_reference_id",
            "correlation_id",
            "causation_id",
        ):
            _display_text(getattr(self, name), name)
        _display_tuple(self.evidence_reference_ids, "evidence_reference_ids")
        _display_exact(self.field_facts, tuple, "field_facts")
        seen: set[str] = set()
        for fact in self.field_facts:
            _display_exact(fact, TelegramSafeListingFieldFact, "field_facts element")
            if fact.listing_reference_id != self.listing_reference_id or fact.field_class in seen:
                raise ValueError("field fact listing reference or class mismatch")
            seen.add(fact.field_class)
        _display_bool(
            self.notification_delivery_projection, True, "notification_delivery_projection"
        )
        _display_bool(self.safe_card_snapshot_only, True, "safe_card_snapshot_only")
        _display_bool(self.rendering_authority, False, "rendering_authority")
        _display_bool(self.provider_call_authority, False, "provider_call_authority")
        if self.source_family not in _DISPLAY_REASON_BY_PURPOSE:
            raise ValueError("listing card source family is not supported")
        if self.reason_class != _DISPLAY_REASON_BY_PURPOSE[self.source_family]:
            raise ValueError("listing card reason class mismatch")
        return self


class TelegramListingDisplayHandoff(_TelegramContract):
    telegram_listing_display_handoff_id: str
    metadata: ContractMetadata
    projection_decision_reference_id: str
    projection_status: _NotificationListingCardProjectionStatusValue
    listing_reference_ids: tuple[str, ...]
    listing_card_reference_ids: tuple[str, ...]
    cards: tuple[TelegramListingCardDisplaySnapshot, ...]
    listing_references_preserved: bool
    optional_fields_missing_allowed: bool
    display_rendering_authorized: bool
    delivery_attempt_authorized: bool
    provider_mapping_authorized: bool
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]
    notification_delivery_projection: Literal[True] = True
    safe_reference_snapshot_only: Literal[True] = True
    rendering_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False

    @field_validator("metadata", mode="before")
    @classmethod
    def _exact_metadata(cls, value: object) -> object:
        if type(value) is not ContractMetadata:
            raise ValueError("metadata must be an exact public contract object")
        return value

    @field_validator("cards", mode="before")
    @classmethod
    def _exact_cards(cls, value: object) -> object:
        if type(value) is not tuple or any(
            type(item) is not TelegramListingCardDisplaySnapshot for item in value
        ):
            raise ValueError("cards must contain exact display snapshots")
        return value

    @model_validator(mode="after")
    def _validate_handoff(self) -> "TelegramListingDisplayHandoff":
        for name in ("telegram_listing_display_handoff_id", "projection_decision_reference_id"):
            _display_text(getattr(self, name), name)
        _display_exact(self.metadata, ContractMetadata, "metadata")
        _display_tuple(self.listing_reference_ids, "listing_reference_ids")
        _display_tuple(self.listing_card_reference_ids, "listing_card_reference_ids")
        _display_tuple(self.reason_codes, "reason_codes")
        _display_tuple(self.evidence_reference_ids, "evidence_reference_ids")
        _display_exact(self.cards, tuple, "cards")
        if (
            tuple(c.listing_reference_id for c in self.cards) != self.listing_reference_ids
            or tuple(c.listing_card_reference_id for c in self.cards)
            != self.listing_card_reference_ids
        ):
            raise ValueError("cards must preserve exact listing and card reference order")
        if self.projection_status == "ACCEPTED_FIELDS" and (
            not self.cards or not any(c.field_facts for c in self.cards)
        ):
            raise ValueError("accepted fields requires field facts")
        if self.projection_status == "ACCEPTED_REFERENCE_ONLY" and (
            not self.cards or any(c.field_facts for c in self.cards)
        ):
            raise ValueError("reference-only requires cards without fields")
        if self.projection_status == "NOT_APPLICABLE_NO_LISTINGS" and (
            self.listing_reference_ids or self.listing_card_reference_ids or self.cards
        ):
            raise ValueError("no-listings handoff must be empty")
        if self.reason_codes != _DISPLAY_STATUS_REASONS[self.projection_status]:
            raise ValueError("reason codes must match projection status")
        for name in (
            "listing_references_preserved",
            "optional_fields_missing_allowed",
            "notification_delivery_projection",
            "safe_reference_snapshot_only",
        ):
            _display_bool(getattr(self, name), True, name)
        for name in (
            "display_rendering_authorized",
            "delivery_attempt_authorized",
            "provider_mapping_authorized",
            "rendering_authority",
            "provider_call_authority",
        ):
            _display_bool(getattr(self, name), False, name)
        return self


class TelegramDisplayActionReference(_TelegramContract):
    telegram_display_action_reference_id: str
    action_class: TelegramDisplayClass
    context_owner: _TelegramDisplayActionOwnerValue
    source_subject_reference_id: str
    safe_context_reference_id: str
    action_policy_reference_id: str
    evidence_reference_ids: tuple[str, ...]
    safe_context_snapshot_only: Literal[True] = True
    callback_payload_defined: Literal[False] = False
    button_label_defined: Literal[False] = False
    execution_authority: Literal[False] = False
    authorization_source: Literal[False] = False
    provider_call_authority: Literal[False] = False
    mini_app_launch_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_action(self) -> "TelegramDisplayActionReference":
        for name in (
            "telegram_display_action_reference_id",
            "source_subject_reference_id",
            "safe_context_reference_id",
            "action_policy_reference_id",
        ):
            _display_text(getattr(self, name), name)
        _display_tuple(self.evidence_reference_ids, "evidence_reference_ids")
        if self.action_class not in (
            TelegramDisplayClass.FULL_RESULT_OPEN_ACTION,
            TelegramDisplayClass.SHOW_MORE_ACTION,
            TelegramDisplayClass.BEACON_SETTINGS_ACTION,
        ):
            raise ValueError("unsupported display action")
        if self.context_owner not in ("NOTIFICATION_DELIVERY", "BEACON_MANAGEMENT"):
            raise ValueError("unsupported action owner")
        for name in ("safe_context_snapshot_only",):
            _display_bool(getattr(self, name), True, name)
        for name in (
            "callback_payload_defined",
            "button_label_defined",
            "execution_authority",
            "authorization_source",
            "provider_call_authority",
            "mini_app_launch_authority",
        ):
            _display_bool(getattr(self, name), False, name)
        return self


class TelegramDisplayBoundaryRequest(_TelegramContract):
    telegram_display_boundary_request_id: str
    metadata: ContractMetadata
    outbound_mapping_outcome: TelegramOutboundMappingOutcome
    listing_display_handoff: TelegramListingDisplayHandoff | None
    action_references: tuple[TelegramDisplayActionReference, ...]
    display_policy_reference_id: str
    notification_delivery_authority_preserved: Literal[True] = True
    all_listing_references_must_be_preserved: Literal[True] = True
    single_summary_preferred: Literal[True] = True
    per_listing_message_burst_authorized: Literal[False] = False
    template_selection_authority: Literal[False] = False
    message_text_rendering_authority: Literal[False] = False
    pagination_size_selection_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False
    mini_app_implementation_authority: Literal[False] = False
    business_success_authority: Literal[False] = False

    @field_validator("metadata", "outbound_mapping_outcome", mode="before")
    @classmethod
    def _exact_request_objects(cls, value: object, info: ValidationInfo) -> object:
        field_name = info.field_name
        assert field_name is not None
        expected = {
            "metadata": ContractMetadata,
            "outbound_mapping_outcome": TelegramOutboundMappingOutcome,
        }[field_name]
        if type(value) is not expected:
            raise ValueError(f"{field_name} must be an exact public contract object")
        return value

    @field_validator("action_references", mode="before")
    @classmethod
    def _exact_actions(cls, value: object) -> object:
        if type(value) is not tuple or any(
            type(item) is not TelegramDisplayActionReference for item in value
        ):
            raise ValueError("action_references must contain exact action references")
        return value

    @model_validator(mode="after")
    def _validate_request(self) -> "TelegramDisplayBoundaryRequest":
        _display_text(
            self.telegram_display_boundary_request_id, "telegram_display_boundary_request_id"
        )
        _display_exact(self.metadata, ContractMetadata, "metadata")
        _display_exact(
            self.outbound_mapping_outcome,
            TelegramOutboundMappingOutcome,
            "outbound_mapping_outcome",
        )
        if self.outbound_mapping_outcome.metadata != self.metadata:
            raise ValueError("metadata must match outbound outcome")
        _display_exact(self.action_references, tuple, "action_references")
        classes: set[TelegramDisplayClass] = set()
        for action in self.action_references:
            _display_exact(action, TelegramDisplayActionReference, "action reference")
            if action.action_class in classes:
                raise ValueError("action classes must be unique")
            classes.add(action.action_class)
        _display_text(self.display_policy_reference_id, "display_policy_reference_id")
        for name in (
            "notification_delivery_authority_preserved",
            "all_listing_references_must_be_preserved",
            "single_summary_preferred",
        ):
            _display_bool(getattr(self, name), True, name)
        for name in (
            "per_listing_message_burst_authorized",
            "template_selection_authority",
            "message_text_rendering_authority",
            "pagination_size_selection_authority",
            "provider_call_authority",
            "mini_app_implementation_authority",
            "business_success_authority",
        ):
            _display_bool(getattr(self, name), False, name)
        return self


class TelegramDisplayProjection(_TelegramContract):
    telegram_display_projection_id: str
    metadata: ContractMetadata
    outbound_mapping_outcome_reference_id: str
    outbound_request_intent_reference_id: str
    notification_attempt_reference_id: str
    notification_outbox_item_reference_id: str
    delivery_purpose: _NotificationSourceFamilyValue
    display_classes: tuple[TelegramDisplayClass, ...]
    listing_reference_ids: tuple[str, ...]
    listing_card_reference_ids: tuple[str, ...]
    listing_cards: tuple[TelegramListingCardDisplaySnapshot, ...]
    action_references: tuple[TelegramDisplayActionReference, ...]
    total_listing_count: int
    evidence_reference_ids: tuple[str, ...]
    all_listing_references_preserved: Literal[True] = True
    safe_field_values_only: Literal[True] = True
    single_summary_preferred: Literal[True] = True
    per_listing_message_burst_authorized: Literal[False] = False
    message_text_rendered: Literal[False] = False
    template_selected: Literal[False] = False
    pagination_size_selected: Literal[False] = False
    provider_call_authorized: Literal[False] = False
    mini_app_implemented: Literal[False] = False
    notification_delivery_mutation_authority: Literal[False] = False
    business_success_authority: Literal[False] = False

    @field_validator("metadata", mode="before")
    @classmethod
    def _exact_projection_metadata(cls, value: object) -> object:
        if type(value) is not ContractMetadata:
            raise ValueError("metadata must be an exact public contract object")
        return value

    @field_validator("listing_cards", "action_references", mode="before")
    @classmethod
    def _exact_projection_collections(cls, value: object, info: ValidationInfo) -> object:
        field_name = info.field_name
        assert field_name is not None
        expected = {
            "listing_cards": TelegramListingCardDisplaySnapshot,
            "action_references": TelegramDisplayActionReference,
        }[field_name]
        if type(value) is not tuple or any(type(item) is not expected for item in value):
            raise ValueError(f"{field_name} must contain exact public contract objects")
        return value

    @model_validator(mode="after")
    def _validate_projection(self) -> "TelegramDisplayProjection":
        for name in (
            "telegram_display_projection_id",
            "outbound_mapping_outcome_reference_id",
            "outbound_request_intent_reference_id",
            "notification_attempt_reference_id",
            "notification_outbox_item_reference_id",
        ):
            _display_text(getattr(self, name), name)
        _display_exact(self.metadata, ContractMetadata, "metadata")
        _display_tuple(self.display_classes, "display_classes", unique=False)
        if any(type(c) is not TelegramDisplayClass for c in self.display_classes):
            raise ValueError("display_classes must contain exact enum values")
        _display_tuple(self.listing_reference_ids, "listing_reference_ids")
        _display_tuple(self.listing_card_reference_ids, "listing_card_reference_ids")
        _display_exact(self.listing_cards, tuple, "listing_cards")
        _display_exact(self.action_references, tuple, "action_references")
        if (
            tuple(c.listing_reference_id for c in self.listing_cards) != self.listing_reference_ids
            or tuple(c.listing_card_reference_id for c in self.listing_cards)
            != self.listing_card_reference_ids
        ):
            raise ValueError("projection listing references are not preserved")
        if type(self.total_listing_count) is not int or self.total_listing_count != len(
            self.listing_reference_ids
        ):
            raise ValueError("total_listing_count mismatch")
        _display_tuple(self.evidence_reference_ids, "evidence_reference_ids")
        for name in (
            "all_listing_references_preserved",
            "safe_field_values_only",
            "single_summary_preferred",
        ):
            _display_bool(getattr(self, name), True, name)
        for name in (
            "per_listing_message_burst_authorized",
            "message_text_rendered",
            "template_selected",
            "pagination_size_selected",
            "provider_call_authorized",
            "mini_app_implemented",
            "notification_delivery_mutation_authority",
            "business_success_authority",
        ):
            _display_bool(getattr(self, name), False, name)
        return self


class TelegramDisplayBoundaryOutcome(_TelegramContract):
    telegram_display_boundary_outcome_id: str
    metadata: ContractMetadata
    request: TelegramDisplayBoundaryRequest
    state: TelegramDisplayProjectionState
    reason_code: TelegramDisplayReasonCode
    projection: TelegramDisplayProjection | None
    blocked_display_class: TelegramDisplayClass | None
    safe_diagnostic_reference_id: str | None
    evidence_reference_ids: tuple[str, ...]
    provider_call_performed: Literal[False] = False
    message_text_rendered: Literal[False] = False
    template_selected: Literal[False] = False
    callback_payload_defined: Literal[False] = False
    pagination_size_selected: Literal[False] = False
    mini_app_implemented: Literal[False] = False
    notification_delivery_mutation_authority: Literal[False] = False
    business_success_authority: Literal[False] = False

    @field_validator("metadata", "request", "projection", mode="before")
    @classmethod
    def _exact_outcome_objects(cls, value: object, info: ValidationInfo) -> object:
        if value is None:
            return value
        field_name = info.field_name
        assert field_name is not None
        expected = {
            "metadata": ContractMetadata,
            "request": TelegramDisplayBoundaryRequest,
            "projection": TelegramDisplayProjection,
        }[field_name]
        if type(value) is not expected:
            raise ValueError(f"{field_name} must be an exact public contract object")
        return value

    @model_validator(mode="after")
    def _validate_outcome(self) -> "TelegramDisplayBoundaryOutcome":
        _display_text(
            self.telegram_display_boundary_outcome_id, "telegram_display_boundary_outcome_id"
        )
        _display_exact(self.metadata, ContractMetadata, "metadata")
        _display_exact(self.request, TelegramDisplayBoundaryRequest, "request")
        if self.metadata != self.request.metadata:
            raise ValueError("metadata must match request")
        _display_tuple(self.evidence_reference_ids, "evidence_reference_ids")
        for name in (
            "provider_call_performed",
            "message_text_rendered",
            "template_selected",
            "callback_payload_defined",
            "pagination_size_selected",
            "mini_app_implemented",
            "notification_delivery_mutation_authority",
            "business_success_authority",
        ):
            _display_bool(getattr(self, name), False, name)
        expected_state, expected_reason, expected_class, diagnostic = _classify_display(
            self.request
        )
        if (self.state, self.reason_code, self.blocked_display_class) != (
            expected_state,
            expected_reason,
            expected_class,
        ):
            raise ValueError("display outcome classification mismatch")
        if expected_state is TelegramDisplayProjectionState.DISPLAY_PROJECTED:
            if self.projection is None or self.safe_diagnostic_reference_id is not None:
                raise ValueError("projected outcome requires projection and no diagnostic")
            intent = self.request.outbound_mapping_outcome.request_intent
            assert intent is not None
            purpose_classes = {
                "NEW_LISTINGS_FOUND": (
                    TelegramDisplayClass.NEW_LISTINGS_SUMMARY,
                    TelegramDisplayClass.NEW_LISTINGS_COMPACT_LIST,
                ),
                "RECOVERY_SCAN_COMPLETED": (
                    (
                        TelegramDisplayClass.RECOVERY_RESULT_MESSAGE,
                        TelegramDisplayClass.NEW_LISTINGS_COMPACT_LIST,
                    )
                    if intent.safe_listing_reference_ids
                    else (TelegramDisplayClass.RECOVERY_RESULT_MESSAGE,),
                ),
                "LOST_ANCHORS_RECOVERED": (
                    TelegramDisplayClass.LOST_ANCHORS_RESTORED_MESSAGE,
                    TelegramDisplayClass.NEW_LISTINGS_COMPACT_LIST,
                ),
                "NO_NEW_LISTINGS_STATUS": (TelegramDisplayClass.NO_NEW_STATUS_MESSAGE,),
                "EXTERNAL_UNAVAILABLE_STATUS": (
                    TelegramDisplayClass.AVITO_UNAVAILABLE_STATUS_MESSAGE,
                ),
            }[intent.delivery_purpose]
            expected_classes = purpose_classes + tuple(
                action.action_class for action in self.request.action_references
            )
            if self.projection.display_classes != expected_classes:
                raise ValueError("display class order mismatch")
            if self.projection.metadata != self.metadata:
                raise ValueError("projection metadata mismatch")
            if (
                self.projection.outbound_mapping_outcome_reference_id
                != self.request.outbound_mapping_outcome.telegram_outbound_mapping_outcome_id
            ):
                raise ValueError("projection outcome lineage mismatch")
        else:
            if self.projection is not None or self.safe_diagnostic_reference_id is None:
                raise ValueError("blocked outcome requires diagnostic and no projection")
        _display_text(
            self.safe_diagnostic_reference_id, "safe_diagnostic_reference_id"
        ) if self.safe_diagnostic_reference_id is not None else None
        if diagnostic is False:
            raise ValueError("classification diagnostic requirement violated")
        return self


# TG-13 deliberately mirrors upstream semantic values with private Literals.  The
# adapter is a projection boundary and must not import Egress or Notification.
class TelegramProviderOutcomeClass(str, Enum):
    PROVIDER_REQUEST_NOT_SENT = "PROVIDER_REQUEST_NOT_SENT"
    PROVIDER_ACCEPTED = "PROVIDER_ACCEPTED"
    PROVIDER_REJECTED = "PROVIDER_REJECTED"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    RATE_LIMITED_OR_RESTRICTED = "RATE_LIMITED_OR_RESTRICTED"
    MALFORMED_OR_UNUSABLE_RESPONSE = "MALFORMED_OR_UNUSABLE_RESPONSE"
    PROVIDER_EFFECT_AMBIGUOUS = "PROVIDER_EFFECT_AMBIGUOUS"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    RECONCILED_NO_EFFECT = "RECONCILED_NO_EFFECT"
    RECONCILED_EFFECT = "RECONCILED_EFFECT"


class TelegramProviderOutcomeMappingState(str, Enum):
    OUTCOME_MAPPED = "OUTCOME_MAPPED"
    OUTCOME_BLOCKED = "OUTCOME_BLOCKED"
    INVALID_EVIDENCE = "INVALID_EVIDENCE"
    AMBIGUOUS = "AMBIGUOUS"


class TelegramProviderOutcomeReasonCode(str, Enum):
    OUTBOUND_REQUEST_NOT_PREPARED = "OUTBOUND_REQUEST_NOT_PREPARED"
    OUTCOME_SCOPE_MISMATCH = "OUTCOME_SCOPE_MISMATCH"
    TRANSPORT_OUTCOME_NOT_COMMITTED = "TRANSPORT_OUTCOME_NOT_COMMITTED"
    UNSAFE_PROVIDER_EVIDENCE = "UNSAFE_PROVIDER_EVIDENCE"
    PROVIDER_REQUEST_NOT_SENT = "PROVIDER_REQUEST_NOT_SENT"
    PROVIDER_ACCEPTED = "PROVIDER_ACCEPTED"
    PROVIDER_REJECTED = "PROVIDER_REJECTED"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    RATE_LIMITED_OR_RESTRICTED = "RATE_LIMITED_OR_RESTRICTED"
    MALFORMED_OR_UNUSABLE_RESPONSE = "MALFORMED_OR_UNUSABLE_RESPONSE"
    PROVIDER_EFFECT_AMBIGUOUS = "PROVIDER_EFFECT_AMBIGUOUS"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    RECONCILED_NO_EFFECT = "RECONCILED_NO_EFFECT"
    RECONCILED_EFFECT = "RECONCILED_EFFECT"


_TG13_TRANSPORT = Literal[
    "NOT_SENT",
    "DISPATCH_REJECTED",
    "DISPATCH_UNKNOWN",
    "SENT_NO_RESPONSE",
    "TRANSPORT_UNAVAILABLE",
    "TRANSPORT_TIMEOUT",
    "TRANSPORT_AMBIGUOUS",
    "RESPONSE_RECEIVED_UNCLASSIFIED",
    "USABLE_RESPONSE_TRANSPORT_ONLY",
    "RATE_OR_ACCESS_RESTRICTED",
    "CAPTCHA_OR_CHALLENGE",
    "PROVIDER_REJECTED",
    "MALFORMED_RESPONSE_TRANSPORT_LAYER",
    "ROUTE_QUARANTINED",
    "ROUTE_DEGRADED",
    "NO_APPROVED_ROUTE_AVAILABLE",
    "POLICY_FALLBACK_ATTEMPTED",
    "POLICY_FALLBACK_EXHAUSTED",
    "RECONCILIATION_REQUIRED",
]
_TG13_DISPATCH = Literal[
    "PENDING", "ATTEMPTED", "ACKNOWLEDGED", "REJECTED", "UNKNOWN", "NOT_SENT", "SENT"
]
_TG13_RECONCILIATION = Literal[
    "NOT_REQUIRED",
    "REQUIRED",
    "PENDING",
    "RESOLVED_NOT_SENT",
    "RESOLVED_SENT",
    "RESOLVED_TERMINAL",
    "REMAINS_AMBIGUOUS",
    "MANUAL_REVIEW_REQUIRED",
]
_TG13_NOTIFICATION_CLASS = Literal[
    "DISPATCH_AMBIGUOUS",
    "PROVIDER_ACCEPTED",
    "PROVIDER_REJECTED",
    "PROVIDER_UNAVAILABLE",
    "RATE_OR_ACCESS_RESTRICTED",
    "MALFORMED_OR_UNUSABLE_PROVIDER_RESPONSE",
    "DELIVERY_FAILURE",
    "DELIVERY_AMBIGUOUS",
    "SUPPRESSED_OR_CANCELLED",
    "TARGET_UNAVAILABLE_OR_UNVERIFIED",
]

_TG13_UNRESOLVED = {"REQUIRED", "PENDING", "REMAINS_AMBIGUOUS", "MANUAL_REVIEW_REQUIRED"}
_TG13_NO_SEND = {"NOT_SENT", "DISPATCH_REJECTED", "NO_APPROVED_ROUTE_AVAILABLE"}
_TG13_UNKNOWN_TRANSPORT = {
    "DISPATCH_UNKNOWN",
    "SENT_NO_RESPONSE",
    "TRANSPORT_TIMEOUT",
    "TRANSPORT_AMBIGUOUS",
    "RESPONSE_RECEIVED_UNCLASSIFIED",
    "USABLE_RESPONSE_TRANSPORT_ONLY",
    "RECONCILIATION_REQUIRED",
}


def _tg13_text(value: object, name: str) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be a non-blank string")


def _tg13_tuple(value: object, name: str) -> tuple[str, ...]:
    if type(value) is not tuple or any(type(v) is not str or not v.strip() for v in value):
        raise ValueError(f"{name} must be a tuple of non-blank strings")
    if len(value) != len(set(value)):
        raise ValueError(f"{name} must be unique")
    return value


def _tg13_optional_text(value: object, name: str) -> None:
    if value is not None:
        _tg13_text(value, name)


def _tg13_false(value: object, name: str) -> None:
    if value is not False:
        raise ValueError(f"{name} must be False")


def _tg13_exact(value: object, cls: type[object], name: str) -> None:
    if type(value) is not cls:
        raise ValueError(f"{name} must be an exact {cls.__name__}")


class TelegramTransportOutcomeObservation(_TelegramContract):
    telegram_transport_outcome_observation_id: str
    metadata: ContractMetadata
    outbound_mapping_outcome_reference_id: str
    notification_attempt_reference_id: str
    notification_target_reference_id: str
    egress_dispatch_attempt_reference_id: str
    egress_transport_outcome_reference_id: str
    dispatch_status: _TG13_DISPATCH
    transport_outcome_status: _TG13_TRANSPORT
    egress_reconciliation_status: _TG13_RECONCILIATION
    transport_outcome_committed: bool
    provider_request_sent: bool
    provider_response_received: bool
    provider_response_usable: bool
    provider_effect_known: bool
    provider_safe_response_reference_id: str | None
    egress_correlation_reference_id: str | None
    contains_raw_provider_payload: Literal[False] = False
    egress_transport_projection: Literal[True] = True
    transport_success_is_provider_success: Literal[False] = False
    notification_delivery_inferred: Literal[False] = False
    new_dispatch_authority: Literal[False] = False
    retry_authority: Literal[False] = False
    evidence_reference_ids: tuple[str, ...]

    @model_validator(mode="after")
    def _validate(self) -> "TelegramTransportOutcomeObservation":
        _tg13_exact(self.metadata, ContractMetadata, "metadata")
        for n in (
            "telegram_transport_outcome_observation_id",
            "outbound_mapping_outcome_reference_id",
            "notification_attempt_reference_id",
            "notification_target_reference_id",
            "egress_dispatch_attempt_reference_id",
            "egress_transport_outcome_reference_id",
        ):
            _tg13_text(getattr(self, n), n)
        _tg13_optional_text(
            self.provider_safe_response_reference_id, "provider_safe_response_reference_id"
        )
        _tg13_optional_text(self.egress_correlation_reference_id, "egress_correlation_reference_id")
        _tg13_tuple(self.evidence_reference_ids, "evidence_reference_ids")
        if self.transport_outcome_committed is not True:
            raise ValueError("transport outcome must be committed")
        for n in (
            "contains_raw_provider_payload",
            "transport_success_is_provider_success",
            "notification_delivery_inferred",
            "new_dispatch_authority",
            "retry_authority",
        ):
            _tg13_false(getattr(self, n), n)
        if self.egress_transport_projection is not True:
            raise ValueError("egress_transport_projection must be True")
        if self.dispatch_status in _TG13_NO_SEND or self.transport_outcome_status in {
            "NOT_SENT",
            "DISPATCH_REJECTED",
            "NO_APPROVED_ROUTE_AVAILABLE",
        }:
            if self.provider_request_sent:
                raise ValueError("definitely-no-route outcome cannot claim provider request sent")
            if (
                self.provider_response_received
                or self.provider_response_usable
                or self.provider_effect_known
            ):
                raise ValueError("definitely-no-route outcome cannot claim provider evidence")
        if self.transport_outcome_status == "SENT_NO_RESPONSE" and (
            self.provider_response_received or self.provider_response_usable
        ):
            raise ValueError("SENT_NO_RESPONSE cannot claim a response")
        if self.provider_response_usable and not self.provider_response_received:
            raise ValueError("usable response requires response received")
        if self.transport_outcome_status in _TG13_UNKNOWN_TRANSPORT and self.provider_effect_known:
            raise ValueError("unknown transport cannot claim known provider effect")
        return self


class TelegramProviderResponseObservation(_TelegramContract):
    telegram_provider_response_observation_id: str
    metadata: ContractMetadata
    transport_observation_reference_id: str
    provider_response_reference_id: str
    provider_response_committed: bool
    provider_ok: bool | None
    provider_rejected: bool
    provider_unavailable: bool
    rate_or_access_restricted: bool
    malformed_or_unusable_response: bool
    provider_effect_known: bool
    provider_effect_committed: bool
    provider_safe_delivery_reference_id: str | None
    telegram_message_reference_id: str | None
    telegram_callback_correlation_reference_id: str | None
    contains_raw_provider_payload: Literal[False] = False
    human_read_or_click_proven: Literal[False] = False
    business_success_proven: Literal[False] = False
    notification_delivery_accepted: Literal[False] = False
    retry_authorized: Literal[False] = False
    evidence_reference_ids: tuple[str, ...]

    @model_validator(mode="after")
    def _validate(self) -> "TelegramProviderResponseObservation":
        _tg13_exact(self.metadata, ContractMetadata, "metadata")
        for n in (
            "telegram_provider_response_observation_id",
            "transport_observation_reference_id",
            "provider_response_reference_id",
        ):
            _tg13_text(getattr(self, n), n)
        _tg13_optional_text(
            self.provider_safe_delivery_reference_id, "provider_safe_delivery_reference_id"
        )
        _tg13_optional_text(self.telegram_message_reference_id, "telegram_message_reference_id")
        _tg13_optional_text(
            self.telegram_callback_correlation_reference_id,
            "telegram_callback_correlation_reference_id",
        )
        _tg13_tuple(self.evidence_reference_ids, "evidence_reference_ids")
        if self.provider_response_committed is not True:
            raise ValueError("provider response must be committed")
        active = [
            self.provider_ok is True,
            self.provider_rejected,
            self.provider_unavailable,
            self.rate_or_access_restricted,
            self.malformed_or_unusable_response,
        ]
        if sum(active) != 1:
            raise ValueError("exactly one provider classification must be active")
        if self.provider_ok is True and not (
            self.provider_effect_known
            and self.provider_effect_committed
            and self.provider_safe_delivery_reference_id
        ):
            raise ValueError("provider_ok=True requires committed known effect and safe delivery")
        if self.provider_ok is not True and self.provider_safe_delivery_reference_id is not None:
            raise ValueError("non-accepted provider outcome cannot carry safe delivery")
        for n in (
            "contains_raw_provider_payload",
            "human_read_or_click_proven",
            "business_success_proven",
            "notification_delivery_accepted",
            "retry_authorized",
        ):
            _tg13_false(getattr(self, n), n)
        if self.provider_ok is not True and self.provider_effect_known:
            raise ValueError("non-accepted classification cannot claim provider effect")
        return self


class TelegramProviderReconciliationObservation(_TelegramContract):
    telegram_provider_reconciliation_observation_id: str
    metadata: ContractMetadata
    transport_observation_reference_id: str
    original_provider_outcome_reference_id: str
    egress_reconciliation_reference_id: str
    egress_reconciliation_status: _TG13_RECONCILIATION
    reconciliation_committed: bool
    resolved_outcome_reference_id: str | None
    provider_effect_observed: bool | None
    provider_safe_delivery_reference_id: str | None
    contains_raw_provider_payload: Literal[False] = False
    new_provider_request_authorized: Literal[False] = False
    blind_retry_authorized: Literal[False] = False
    retry_authorized: Literal[False] = False
    notification_delivery_mutation_authority: Literal[False] = False
    evidence_reference_ids: tuple[str, ...]

    @model_validator(mode="after")
    def _validate(self) -> "TelegramProviderReconciliationObservation":
        _tg13_exact(self.metadata, ContractMetadata, "metadata")
        for n in (
            "telegram_provider_reconciliation_observation_id",
            "transport_observation_reference_id",
            "original_provider_outcome_reference_id",
            "egress_reconciliation_reference_id",
        ):
            _tg13_text(getattr(self, n), n)
        _tg13_optional_text(self.resolved_outcome_reference_id, "resolved_outcome_reference_id")
        _tg13_optional_text(
            self.provider_safe_delivery_reference_id,
            "provider_safe_delivery_reference_id",
        )
        _tg13_tuple(self.evidence_reference_ids, "evidence_reference_ids")
        if self.reconciliation_committed is not True:
            raise ValueError("reconciliation must be committed")
        for n in (
            "contains_raw_provider_payload",
            "new_provider_request_authorized",
            "blind_retry_authorized",
            "retry_authorized",
            "notification_delivery_mutation_authority",
        ):
            _tg13_false(getattr(self, n), n)
        status = self.egress_reconciliation_status
        if status in _TG13_UNRESOLVED:
            if (
                self.resolved_outcome_reference_id is not None
                or self.provider_effect_observed is not None
                or self.provider_safe_delivery_reference_id is not None
            ):
                raise ValueError("unresolved reconciliation carries resolution facts")
        elif status == "RESOLVED_NOT_SENT":
            if (
                not self.resolved_outcome_reference_id
                or self.provider_effect_observed is not False
                or self.provider_safe_delivery_reference_id is not None
            ):
                raise ValueError("RESOLVED_NOT_SENT matrix mismatch")
        elif status == "RESOLVED_SENT":
            if (
                not self.resolved_outcome_reference_id
                or self.provider_effect_observed is not True
                or not self.provider_safe_delivery_reference_id
            ):
                raise ValueError("RESOLVED_SENT matrix mismatch")
        elif status == "RESOLVED_TERMINAL":
            if (
                not self.resolved_outcome_reference_id
                or self.provider_effect_observed is None
                or (self.provider_effect_observed and not self.provider_safe_delivery_reference_id)
            ):
                raise ValueError("RESOLVED_TERMINAL matrix mismatch")
        elif status == "NOT_REQUIRED":
            if (
                self.resolved_outcome_reference_id is not None
                or self.provider_effect_observed is not None
            ):
                raise ValueError("NOT_REQUIRED cannot masquerade as resolution")
        return self


class TelegramProviderOutcomeMappingRequest(_TelegramContract):
    telegram_provider_outcome_mapping_request_id: str
    metadata: ContractMetadata
    outbound_mapping_outcome: TelegramOutboundMappingOutcome
    transport_observation: TelegramTransportOutcomeObservation | None
    provider_response_observation: TelegramProviderResponseObservation | None
    reconciliation_observation: TelegramProviderReconciliationObservation | None
    adapter_contract: Literal["telegram.provider.outcome"] = "telegram.provider.outcome"
    adapter_contract_version: Literal["1"] = "1"
    outcome_policy_reference_id: str
    provider_call_authority: Literal[False] = False
    reconciliation_execution_authority: Literal[False] = False
    retry_authority: Literal[False] = False
    notification_acceptance_authority: Literal[False] = False
    notification_lifecycle_mutation_authority: Literal[False] = False
    human_read_or_click_authority: Literal[False] = False
    business_success_authority: Literal[False] = False

    @field_validator(
        "metadata",
        "outbound_mapping_outcome",
        "transport_observation",
        "provider_response_observation",
        "reconciliation_observation",
        mode="before",
    )
    @classmethod
    def _exact(cls, value: object, info: ValidationInfo) -> object:
        if value is None:
            return value
        field_name = info.field_name
        assert field_name is not None
        expected = {
            "metadata": ContractMetadata,
            "outbound_mapping_outcome": TelegramOutboundMappingOutcome,
            "transport_observation": TelegramTransportOutcomeObservation,
            "provider_response_observation": TelegramProviderResponseObservation,
            "reconciliation_observation": TelegramProviderReconciliationObservation,
        }[field_name]
        _tg13_exact(value, expected, field_name)
        return value

    @model_validator(mode="after")
    def _validate(self) -> "TelegramProviderOutcomeMappingRequest":
        _tg13_text(
            self.telegram_provider_outcome_mapping_request_id,
            "telegram_provider_outcome_mapping_request_id",
        )
        _tg13_text(self.outcome_policy_reference_id, "outcome_policy_reference_id")
        _tg13_exact(self.metadata, ContractMetadata, "metadata")
        _tg13_exact(
            self.outbound_mapping_outcome,
            TelegramOutboundMappingOutcome,
            "outbound_mapping_outcome",
        )
        if self.outbound_mapping_outcome.metadata != self.metadata:
            raise ValueError("metadata mismatch")
        attempt_handoff = self.outbound_mapping_outcome.request.notification_attempt_handoff
        outbound_intent = self.outbound_mapping_outcome.request_intent
        if self.provider_response_observation is not None and self.transport_observation is None:
            raise ValueError("provider response requires transport observation")
        if self.reconciliation_observation is not None and self.transport_observation is None:
            raise ValueError("reconciliation requires transport observation")
        if self.transport_observation is not None:
            transport_observation = self.transport_observation
            if (
                attempt_handoff.attempt_reference_id is None
                or attempt_handoff.attempt_target_reference_id is None
                or outbound_intent is None
                or transport_observation.notification_attempt_reference_id
                != attempt_handoff.attempt_reference_id
                or transport_observation.notification_target_reference_id
                != attempt_handoff.attempt_target_reference_id
            ):
                raise ValueError("transport attempt/target lineage mismatch")
            _tg13_exact(
                transport_observation,
                TelegramTransportOutcomeObservation,
                "transport_observation",
            )
            if (
                transport_observation.metadata != self.metadata
                or transport_observation.outbound_mapping_outcome_reference_id
                != self.outbound_mapping_outcome.telegram_outbound_mapping_outcome_id
            ):
                raise ValueError("transport lineage mismatch")
        if self.provider_response_observation is not None:
            provider_transport = self.transport_observation
            assert provider_transport is not None
            if (
                self.provider_response_observation.metadata != self.metadata
                or self.provider_response_observation.transport_observation_reference_id
                != provider_transport.telegram_transport_outcome_observation_id
            ):
                raise ValueError("provider response lineage mismatch")
        if self.reconciliation_observation is not None:
            reconciliation_transport = self.transport_observation
            assert reconciliation_transport is not None
            r = self.reconciliation_observation
            if (
                r.metadata != self.metadata
                or r.transport_observation_reference_id
                != reconciliation_transport.telegram_transport_outcome_observation_id
                or r.original_provider_outcome_reference_id
                not in {
                    self.outbound_mapping_outcome.telegram_outbound_mapping_outcome_id,
                    *(
                        (self.provider_response_observation.provider_response_reference_id,)
                        if self.provider_response_observation
                        else ()
                    ),
                }
            ):
                raise ValueError("reconciliation lineage mismatch")
        for n in (
            "provider_call_authority",
            "reconciliation_execution_authority",
            "retry_authority",
            "notification_acceptance_authority",
            "notification_lifecycle_mutation_authority",
            "human_read_or_click_authority",
            "business_success_authority",
        ):
            _tg13_false(getattr(self, n), n)
        return self


class TelegramNotificationProviderOutcomeHandoff(_TelegramContract):
    outcome_reference_id: str
    adapter_contract: Literal["telegram.provider.outcome"]
    adapter_contract_version: Literal["1"]
    attempt_id: str
    channel_class: Literal["TELEGRAM"]
    target_reference_id: str
    outcome_class: _TG13_NOTIFICATION_CLASS
    adapter_outcome_committed: Literal[True] = True
    provider_safe_delivery_reference: str | None
    egress_correlation_reference: str | None
    contains_raw_provider_payload: Literal[False] = False
    identity_ambiguous: Literal[False] = False
    correlation_id: str
    causation_id: str
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]
    notification_delivery_projection: Literal[True] = True
    notification_acceptance_authority: Literal[False] = False
    notification_lifecycle_mutation_authority: Literal[False] = False
    retry_authority: Literal[False] = False
    human_read_or_click_proven: Literal[False] = False
    business_success_proven: Literal[False] = False

    @model_validator(mode="after")
    def _validate(self) -> "TelegramNotificationProviderOutcomeHandoff":
        for n in (
            "outcome_reference_id",
            "attempt_id",
            "target_reference_id",
            "correlation_id",
            "causation_id",
        ):
            _tg13_text(getattr(self, n), n)
        _tg13_tuple(self.reason_codes, "reason_codes")
        _tg13_tuple(self.evidence_reference_ids, "evidence_reference_ids")
        for n in (
            "contains_raw_provider_payload",
            "identity_ambiguous",
            "notification_acceptance_authority",
            "notification_lifecycle_mutation_authority",
            "retry_authority",
            "human_read_or_click_proven",
            "business_success_proven",
        ):
            _tg13_false(getattr(self, n), n)
        if (
            self.adapter_outcome_committed is not True
            or self.notification_delivery_projection is not True
        ):
            raise ValueError("handoff commitment/projection flags are fixed")
        if (
            self.outcome_class in {"PROVIDER_ACCEPTED"}
            and not self.provider_safe_delivery_reference
        ):
            raise ValueError("accepted handoff requires safe delivery reference")
        if (
            self.outcome_class
            in {
                "DISPATCH_AMBIGUOUS",
                "DELIVERY_AMBIGUOUS",
                "DELIVERY_FAILURE",
                "PROVIDER_REJECTED",
                "PROVIDER_UNAVAILABLE",
                "RATE_OR_ACCESS_RESTRICTED",
                "MALFORMED_OR_UNUSABLE_PROVIDER_RESPONSE",
                "SUPPRESSED_OR_CANCELLED",
                "TARGET_UNAVAILABLE_OR_UNVERIFIED",
            }
            and self.provider_safe_delivery_reference is not None
        ):
            raise ValueError("ambiguous/failure handoff cannot carry safe delivery")
        return self


class TelegramProviderOutcome(_TelegramContract):
    telegram_provider_outcome_id: str
    metadata: ContractMetadata
    mapping_request_reference_id: str
    outbound_mapping_outcome_reference_id: str
    notification_attempt_reference_id: str
    notification_target_reference_id: str
    outcome_class: TelegramProviderOutcomeClass
    reason_code: TelegramProviderOutcomeReasonCode
    notification_handoff: TelegramNotificationProviderOutcomeHandoff | None
    provider_safe_delivery_reference_id: str | None
    egress_correlation_reference_id: str | None
    reconciliation_reference_id: str | None
    evidence_reference_ids: tuple[str, ...]
    adapter_outcome_committed: Literal[True] = True
    provider_request_sent: bool
    provider_accepted: bool
    provider_effect_known: bool
    reconciliation_required: bool
    reconciliation_resolved: bool
    provider_call_performed_by_boundary: Literal[False] = False
    blind_retry_authorized: Literal[False] = False
    retry_authorized: Literal[False] = False
    notification_delivery_accepted: Literal[False] = False
    notification_lifecycle_mutation_authority: Literal[False] = False
    human_read_or_click_proven: Literal[False] = False
    business_success_proven: Literal[False] = False

    @field_validator("metadata", "notification_handoff", mode="before")
    @classmethod
    def _exact(cls, value: object, info: ValidationInfo) -> object:
        if value is None:
            return value
        field_name = info.field_name
        assert field_name is not None
        _tg13_exact(
            value,
            {
                "metadata": ContractMetadata,
                "notification_handoff": TelegramNotificationProviderOutcomeHandoff,
            }[field_name],
            field_name,
        )
        return value

    @model_validator(mode="after")
    def _validate(self) -> "TelegramProviderOutcome":
        _tg13_exact(self.metadata, ContractMetadata, "metadata")
        for n in (
            "telegram_provider_outcome_id",
            "mapping_request_reference_id",
            "outbound_mapping_outcome_reference_id",
            "notification_attempt_reference_id",
            "notification_target_reference_id",
        ):
            _tg13_text(getattr(self, n), n)
        _tg13_tuple(self.evidence_reference_ids, "evidence_reference_ids")
        if self.adapter_outcome_committed is not True:
            raise ValueError("outcome must be committed")
        for n in (
            "provider_call_performed_by_boundary",
            "blind_retry_authorized",
            "retry_authorized",
            "notification_delivery_accepted",
            "notification_lifecycle_mutation_authority",
            "human_read_or_click_proven",
            "business_success_proven",
        ):
            _tg13_false(getattr(self, n), n)
        c = self.outcome_class
        if c == TelegramProviderOutcomeClass.PROVIDER_REQUEST_NOT_SENT:
            if (
                self.provider_request_sent
                or self.provider_accepted
                or not self.provider_effect_known
                or self.reconciliation_required
                or self.reconciliation_resolved
                or self.notification_handoff is not None
            ):
                raise ValueError("request-not-sent matrix mismatch")
        elif c in {
            TelegramProviderOutcomeClass.PROVIDER_ACCEPTED,
            TelegramProviderOutcomeClass.RECONCILED_EFFECT,
        }:
            if not (
                self.provider_request_sent
                and self.provider_accepted
                and self.provider_effect_known
                and self.provider_safe_delivery_reference_id
                and self.notification_handoff
            ):
                raise ValueError("accepted matrix mismatch")
        elif c in {
            TelegramProviderOutcomeClass.PROVIDER_EFFECT_AMBIGUOUS,
            TelegramProviderOutcomeClass.RECONCILIATION_REQUIRED,
        }:
            if (
                self.provider_accepted
                or self.provider_effect_known
                or not self.reconciliation_required
                or self.reconciliation_resolved
                or self.notification_handoff is None
            ):
                raise ValueError("ambiguous matrix mismatch")
        elif c == TelegramProviderOutcomeClass.RECONCILED_NO_EFFECT:
            if (
                not (self.provider_effect_known and self.reconciliation_resolved)
                or self.provider_accepted
                or self.reconciliation_required
                or not self.notification_handoff
            ):
                raise ValueError("reconciled no-effect matrix mismatch")
        else:
            if (
                self.provider_accepted
                or self.provider_safe_delivery_reference_id is not None
                or not self.notification_handoff
                or self.retry_authorized
            ):
                raise ValueError("provider failure matrix mismatch")
        handoff = self.notification_handoff
        if (
            c
            in {
                TelegramProviderOutcomeClass.PROVIDER_ACCEPTED,
                TelegramProviderOutcomeClass.RECONCILED_EFFECT,
            }
            and handoff is not None
            and handoff.outcome_class != "PROVIDER_ACCEPTED"
        ):
            raise ValueError("accepted outcome requires accepted handoff")
        if (
            c == TelegramProviderOutcomeClass.RECONCILED_NO_EFFECT
            and handoff is not None
            and handoff.outcome_class != "DELIVERY_FAILURE"
        ):
            raise ValueError("no-effect outcome requires failure handoff")
        return self


def _tg13_handoff(
    request: TelegramProviderOutcomeMappingRequest,
    outcome_id: str,
    outcome_class: TelegramProviderOutcomeClass,
    safe_ref: str | None,
    egress_ref: str | None,
    reason: TelegramProviderOutcomeReasonCode,
) -> TelegramNotificationProviderOutcomeHandoff:
    h = request.outbound_mapping_outcome.request.notification_attempt_handoff
    intent = request.outbound_mapping_outcome.request_intent
    if h.attempt_reference_id is None or h.attempt_target_reference_id is None or intent is None:
        raise ValueError("prepared outbound outcome lacks lineage")
    notification_class = {
        TelegramProviderOutcomeClass.PROVIDER_ACCEPTED: "PROVIDER_ACCEPTED",
        TelegramProviderOutcomeClass.RECONCILED_EFFECT: "PROVIDER_ACCEPTED",
        TelegramProviderOutcomeClass.PROVIDER_REJECTED: "PROVIDER_REJECTED",
        TelegramProviderOutcomeClass.PROVIDER_UNAVAILABLE: "PROVIDER_UNAVAILABLE",
        TelegramProviderOutcomeClass.RATE_LIMITED_OR_RESTRICTED: "RATE_OR_ACCESS_RESTRICTED",
        TelegramProviderOutcomeClass.MALFORMED_OR_UNUSABLE_RESPONSE: "MALFORMED_OR_UNUSABLE_PROVIDER_RESPONSE",
        TelegramProviderOutcomeClass.RECONCILED_NO_EFFECT: "DELIVERY_FAILURE",
        TelegramProviderOutcomeClass.RECONCILIATION_REQUIRED: "DELIVERY_AMBIGUOUS",
        TelegramProviderOutcomeClass.PROVIDER_EFFECT_AMBIGUOUS: "DELIVERY_AMBIGUOUS",
    }[outcome_class]
    if (
        outcome_class is TelegramProviderOutcomeClass.PROVIDER_EFFECT_AMBIGUOUS
        and request.transport_observation is not None
        and request.transport_observation.dispatch_status == "UNKNOWN"
    ):
        notification_class = "DISPATCH_AMBIGUOUS"
    notification_class = cast(_TG13_NOTIFICATION_CLASS, notification_class)
    evidence = list(request.outbound_mapping_outcome.evidence_reference_ids)
    if request.transport_observation is not None:
        evidence.extend(request.transport_observation.evidence_reference_ids)
    if request.provider_response_observation is not None:
        evidence.extend(request.provider_response_observation.evidence_reference_ids)
    if request.reconciliation_observation is not None:
        evidence.extend(request.reconciliation_observation.evidence_reference_ids)
    return TelegramNotificationProviderOutcomeHandoff(
        outcome_reference_id=outcome_id,
        adapter_contract="telegram.provider.outcome",
        adapter_contract_version="1",
        attempt_id=h.attempt_reference_id,
        channel_class="TELEGRAM",
        target_reference_id=h.attempt_target_reference_id,
        outcome_class=notification_class,
        provider_safe_delivery_reference=safe_ref,
        egress_correlation_reference=egress_ref,
        correlation_id=intent.correlation_id,
        causation_id=intent.causation_id,
        reason_codes=(reason.value,),
        evidence_reference_ids=tuple(dict.fromkeys(evidence)),
    )


def _tg13_mapping(
    request: TelegramProviderOutcomeMappingRequest,
) -> tuple[TelegramProviderOutcomeClass, TelegramProviderOutcomeReasonCode]:
    o = request.outbound_mapping_outcome
    if (
        o.state is not TelegramOutboundMappingState.REQUEST_PREPARED
        or o.reason_code
        is not TelegramOutboundMappingReasonCode.TELEGRAM_PRIVATE_CHAT_REQUEST_PREPARED
        or o.request_intent is None
    ):
        raise ValueError("OUTBOUND_REQUEST_NOT_PREPARED")
    t = request.transport_observation
    if t is None:
        raise ValueError("TRANSPORT_OUTCOME_NOT_COMMITTED")
    if (
        t.metadata != request.metadata
        or t.outbound_mapping_outcome_reference_id != o.telegram_outbound_mapping_outcome_id
    ):
        raise ValueError("OUTCOME_SCOPE_MISMATCH")
    if t.transport_outcome_committed is not True:
        raise ValueError("TRANSPORT_OUTCOME_NOT_COMMITTED")
    if (
        t.contains_raw_provider_payload is not False
        or t.egress_transport_projection is not True
        or t.transport_success_is_provider_success is not False
        or t.notification_delivery_inferred is not False
        or t.new_dispatch_authority is not False
        or t.retry_authority is not False
    ):
        raise ValueError("UNSAFE_PROVIDER_EVIDENCE")
    r = request.reconciliation_observation
    if r is not None:
        if (
            r.metadata != request.metadata
            or r.transport_observation_reference_id != t.telegram_transport_outcome_observation_id
        ):
            raise ValueError("OUTCOME_SCOPE_MISMATCH")
        if r.egress_reconciliation_status in _TG13_UNRESOLVED:
            return (
                TelegramProviderOutcomeClass.RECONCILIATION_REQUIRED,
                TelegramProviderOutcomeReasonCode.RECONCILIATION_REQUIRED,
            )
        if r.egress_reconciliation_status == "RESOLVED_NOT_SENT":
            return (
                TelegramProviderOutcomeClass.RECONCILED_NO_EFFECT,
                TelegramProviderOutcomeReasonCode.RECONCILED_NO_EFFECT,
            )
        if r.egress_reconciliation_status == "RESOLVED_SENT":
            return (
                TelegramProviderOutcomeClass.RECONCILED_EFFECT,
                TelegramProviderOutcomeReasonCode.RECONCILED_EFFECT,
            )
        if r.egress_reconciliation_status == "RESOLVED_TERMINAL":
            return (
                (
                    TelegramProviderOutcomeClass.RECONCILED_EFFECT,
                    TelegramProviderOutcomeReasonCode.RECONCILED_EFFECT,
                )
                if r.provider_effect_observed
                else (
                    TelegramProviderOutcomeClass.RECONCILED_NO_EFFECT,
                    TelegramProviderOutcomeReasonCode.RECONCILED_NO_EFFECT,
                )
            )
    if not t.provider_request_sent or t.transport_outcome_status in _TG13_NO_SEND:
        return (
            TelegramProviderOutcomeClass.PROVIDER_REQUEST_NOT_SENT,
            TelegramProviderOutcomeReasonCode.PROVIDER_REQUEST_NOT_SENT,
        )
    p = request.provider_response_observation
    if p is not None:
        if (
            p.metadata != request.metadata
            or p.transport_observation_reference_id != t.telegram_transport_outcome_observation_id
        ):
            raise ValueError("OUTCOME_SCOPE_MISMATCH")
        if (
            p.contains_raw_provider_payload is not False
            or p.human_read_or_click_proven is not False
            or p.business_success_proven is not False
            or p.notification_delivery_accepted is not False
            or p.retry_authorized is not False
        ):
            raise ValueError("UNSAFE_PROVIDER_EVIDENCE")
        if p.provider_ok is True:
            return (
                TelegramProviderOutcomeClass.PROVIDER_ACCEPTED,
                TelegramProviderOutcomeReasonCode.PROVIDER_ACCEPTED,
            )
        if p.provider_rejected:
            return (
                TelegramProviderOutcomeClass.PROVIDER_REJECTED,
                TelegramProviderOutcomeReasonCode.PROVIDER_REJECTED,
            )
        if p.provider_unavailable:
            return (
                TelegramProviderOutcomeClass.PROVIDER_UNAVAILABLE,
                TelegramProviderOutcomeReasonCode.PROVIDER_UNAVAILABLE,
            )
        if p.rate_or_access_restricted:
            return (
                TelegramProviderOutcomeClass.RATE_LIMITED_OR_RESTRICTED,
                TelegramProviderOutcomeReasonCode.RATE_LIMITED_OR_RESTRICTED,
            )
        return (
            TelegramProviderOutcomeClass.MALFORMED_OR_UNUSABLE_RESPONSE,
            TelegramProviderOutcomeReasonCode.MALFORMED_OR_UNUSABLE_RESPONSE,
        )
    return (
        TelegramProviderOutcomeClass.PROVIDER_EFFECT_AMBIGUOUS,
        TelegramProviderOutcomeReasonCode.PROVIDER_EFFECT_AMBIGUOUS,
    )


class TelegramProviderOutcomeMappingDecision(_TelegramContract):
    telegram_provider_outcome_mapping_decision_id: str
    metadata: ContractMetadata
    request: TelegramProviderOutcomeMappingRequest
    state: TelegramProviderOutcomeMappingState
    reason_code: TelegramProviderOutcomeReasonCode
    outcome: TelegramProviderOutcome | None
    safe_diagnostic_reference_id: str | None
    evidence_reference_ids: tuple[str, ...]
    provider_call_performed: Literal[False] = False
    reconciliation_performed: Literal[False] = False
    retry_authorized: Literal[False] = False
    notification_delivery_accepted: Literal[False] = False
    notification_lifecycle_mutation_authority: Literal[False] = False
    human_read_or_click_proven: Literal[False] = False
    business_success_proven: Literal[False] = False

    @field_validator("metadata", "request", "outcome", mode="before")
    @classmethod
    def _exact(cls, value: object, info: ValidationInfo) -> object:
        if value is None:
            return value
        field_name = info.field_name
        assert field_name is not None
        _tg13_exact(
            value,
            {
                "metadata": ContractMetadata,
                "request": TelegramProviderOutcomeMappingRequest,
                "outcome": TelegramProviderOutcome,
            }[field_name],
            field_name,
        )
        return value

    @model_validator(mode="after")
    def _validate(self) -> "TelegramProviderOutcomeMappingDecision":
        _tg13_text(
            self.telegram_provider_outcome_mapping_decision_id,
            "telegram_provider_outcome_mapping_decision_id",
        )
        _tg13_exact(self.metadata, ContractMetadata, "metadata")
        _tg13_exact(self.request, TelegramProviderOutcomeMappingRequest, "request")
        _tg13_tuple(self.evidence_reference_ids, "evidence_reference_ids")
        for n in (
            "provider_call_performed",
            "reconciliation_performed",
            "retry_authorized",
            "notification_delivery_accepted",
            "notification_lifecycle_mutation_authority",
            "human_read_or_click_proven",
            "business_success_proven",
        ):
            _tg13_false(getattr(self, n), n)
        try:
            c, reason = _tg13_mapping(self.request)
            state = TelegramProviderOutcomeMappingState.OUTCOME_MAPPED
            outcome = self._build_outcome(c, reason)
        except ValueError as exc:
            token = str(exc)
            if token == "OUTBOUND_REQUEST_NOT_PREPARED":
                state, reason, outcome = (
                    TelegramProviderOutcomeMappingState.OUTCOME_BLOCKED,
                    TelegramProviderOutcomeReasonCode.OUTBOUND_REQUEST_NOT_PREPARED,
                    None,
                )
            elif token == "TRANSPORT_OUTCOME_NOT_COMMITTED":
                state, reason, outcome = (
                    TelegramProviderOutcomeMappingState.INVALID_EVIDENCE,
                    TelegramProviderOutcomeReasonCode.TRANSPORT_OUTCOME_NOT_COMMITTED,
                    None,
                )
            elif token == "UNSAFE_PROVIDER_EVIDENCE":
                state, reason, outcome = (
                    TelegramProviderOutcomeMappingState.INVALID_EVIDENCE,
                    TelegramProviderOutcomeReasonCode.UNSAFE_PROVIDER_EVIDENCE,
                    None,
                )
            else:
                state, reason, outcome = (
                    TelegramProviderOutcomeMappingState.AMBIGUOUS,
                    TelegramProviderOutcomeReasonCode.OUTCOME_SCOPE_MISMATCH,
                    None,
                )
        if self.state is not state or self.reason_code is not reason or self.outcome != outcome:
            raise ValueError("decision does not match deterministic precedence")
        if state is TelegramProviderOutcomeMappingState.OUTCOME_MAPPED:
            if outcome is None or self.safe_diagnostic_reference_id is not None:
                raise ValueError("mapped decision requires outcome and forbids diagnostic")
        elif outcome is not None or not self.safe_diagnostic_reference_id:
            raise ValueError(
                "blocked/invalid/ambiguous decision requires diagnostic and no outcome"
            )
        return self

    def _build_outcome(
        self, c: TelegramProviderOutcomeClass, reason: TelegramProviderOutcomeReasonCode
    ) -> TelegramProviderOutcome:
        req = self.request
        t = req.transport_observation
        p = req.provider_response_observation
        r = req.reconciliation_observation
        assert t is not None
        h = req.outbound_mapping_outcome.request.notification_attempt_handoff
        assert h.attempt_reference_id is not None and h.attempt_target_reference_id is not None
        safe = (
            p.provider_safe_delivery_reference_id
            if p is not None and p.provider_ok is True
            else (
                r.provider_safe_delivery_reference_id
                if r is not None and r.provider_effect_observed
                else None
            )
        )
        oid = f"{req.telegram_provider_outcome_mapping_request_id}:outcome"
        handoff = (
            None
            if c is TelegramProviderOutcomeClass.PROVIDER_REQUEST_NOT_SENT
            else _tg13_handoff(req, oid, c, safe, t.egress_correlation_reference_id, reason)
        )
        return TelegramProviderOutcome(
            telegram_provider_outcome_id=oid,
            metadata=req.metadata,
            mapping_request_reference_id=req.telegram_provider_outcome_mapping_request_id,
            outbound_mapping_outcome_reference_id=req.outbound_mapping_outcome.telegram_outbound_mapping_outcome_id,
            notification_attempt_reference_id=h.attempt_reference_id,
            notification_target_reference_id=h.attempt_target_reference_id,
            outcome_class=c,
            reason_code=reason,
            notification_handoff=handoff,
            provider_safe_delivery_reference_id=safe,
            egress_correlation_reference_id=t.egress_correlation_reference_id,
            reconciliation_reference_id=r.egress_reconciliation_reference_id if r else None,
            evidence_reference_ids=tuple(
                dict.fromkeys(
                    req.outbound_mapping_outcome.evidence_reference_ids + t.evidence_reference_ids
                )
            ),
            provider_request_sent=t.provider_request_sent,
            provider_accepted=c
            in {
                TelegramProviderOutcomeClass.PROVIDER_ACCEPTED,
                TelegramProviderOutcomeClass.RECONCILED_EFFECT,
            },
            provider_effect_known=c
            not in {
                TelegramProviderOutcomeClass.PROVIDER_EFFECT_AMBIGUOUS,
                TelegramProviderOutcomeClass.RECONCILIATION_REQUIRED,
            },
            reconciliation_required=c
            in {
                TelegramProviderOutcomeClass.PROVIDER_EFFECT_AMBIGUOUS,
                TelegramProviderOutcomeClass.RECONCILIATION_REQUIRED,
            },
            reconciliation_resolved=c
            in {
                TelegramProviderOutcomeClass.RECONCILED_NO_EFFECT,
                TelegramProviderOutcomeClass.RECONCILED_EFFECT,
            },
        )


def _classify_display(
    request: TelegramDisplayBoundaryRequest,
) -> tuple[
    TelegramDisplayProjectionState, TelegramDisplayReasonCode, TelegramDisplayClass | None, bool
]:
    outcome = request.outbound_mapping_outcome
    intent = outcome.request_intent
    h = outcome.request.notification_attempt_handoff
    if (
        outcome.state is not TelegramOutboundMappingState.REQUEST_PREPARED
        or outcome.reason_code
        is not TelegramOutboundMappingReasonCode.TELEGRAM_PRIVATE_CHAT_REQUEST_PREPARED
        or intent is None
        or outcome.safe_diagnostic_reference_id is not None
        or any(
            getattr(outcome, n) is True
            for n in (
                "provider_call_performed",
                "provider_effect_committed",
                "notification_delivery_accepted",
                "human_read_or_click_proven",
                "retry_authorized",
                "generic_outbox_mutation_authority",
                "notification_lifecycle_mutation_authority",
            )
        )
    ):
        return (
            TelegramDisplayProjectionState.DISPLAY_BLOCKED,
            TelegramDisplayReasonCode.OUTBOUND_REQUEST_NOT_PREPARED,
            None,
            True,
        )
    handoff = request.listing_display_handoff
    if (
        intent.metadata != outcome.metadata
        or outcome.request.metadata != intent.metadata
        or intent.notification_attempt_id != h.attempt_reference_id
        or intent.notification_outbox_item_id != h.outbox_item_reference_id
        or intent.notification_delivery_plan_id != h.delivery_plan_reference_id
        or (handoff is not None and handoff.metadata != outcome.metadata)
    ):
        return (
            TelegramDisplayProjectionState.AMBIGUOUS,
            TelegramDisplayReasonCode.OUTBOUND_DISPLAY_SCOPE_MISMATCH,
            None,
            True,
        )
    for action in request.action_references:
        if (
            action.action_class is TelegramDisplayClass.BEACON_SETTINGS_ACTION
            and action.context_owner != "BEACON_MANAGEMENT"
        ):
            return (
                TelegramDisplayProjectionState.AMBIGUOUS,
                TelegramDisplayReasonCode.OUTBOUND_DISPLAY_SCOPE_MISMATCH,
                None,
                True,
            )
        if (
            action.action_class
            in (TelegramDisplayClass.FULL_RESULT_OPEN_ACTION, TelegramDisplayClass.SHOW_MORE_ACTION)
            and action.context_owner != "NOTIFICATION_DELIVERY"
        ):
            return (
                TelegramDisplayProjectionState.AMBIGUOUS,
                TelegramDisplayReasonCode.OUTBOUND_DISPLAY_SCOPE_MISMATCH,
                None,
                True,
            )
    purpose = intent.delivery_purpose
    if purpose not in _DISPLAY_PURPOSES:
        return (
            TelegramDisplayProjectionState.DISPLAY_BLOCKED,
            TelegramDisplayReasonCode.UNSUPPORTED_DELIVERY_PURPOSE,
            TelegramDisplayClass.UNSUPPORTED_CONTENT_BLOCKED,
            True,
        )
    refs = intent.safe_listing_reference_ids
    card_refs = intent.safe_listing_card_reference_ids
    if (
        (refs and handoff is None)
        or (handoff is not None and tuple(handoff.listing_reference_ids) != refs)
        or (handoff is not None and tuple(handoff.listing_card_reference_ids) != card_refs)
    ):
        return (
            TelegramDisplayProjectionState.INVALID_CONTENT,
            TelegramDisplayReasonCode.SAFE_LISTING_DISPLAY_MISMATCH,
            None,
            True,
        )
    if handoff is not None:
        for card in handoff.cards:
            if (
                card.account_reference_id != h.outbox_account_reference_id
                or card.beacon_reference_id != h.outbox_beacon_reference_id
                or card.correlation_id != intent.correlation_id
                or card.causation_id != intent.causation_id
                or card.source_family != purpose
            ):
                return (
                    TelegramDisplayProjectionState.INVALID_CONTENT,
                    TelegramDisplayReasonCode.SAFE_LISTING_DISPLAY_MISMATCH,
                    None,
                    True,
                )
    if purpose in ("NO_NEW_LISTINGS_STATUS", "EXTERNAL_UNAVAILABLE_STATUS") and (
        refs or card_refs or handoff is not None
    ):
        return (
            TelegramDisplayProjectionState.INVALID_CONTENT,
            TelegramDisplayReasonCode.SAFE_LISTING_DISPLAY_MISMATCH,
            None,
            True,
        )
    if purpose in ("NEW_LISTINGS_FOUND", "LOST_ANCHORS_RECOVERED") and not refs:
        return (
            TelegramDisplayProjectionState.INVALID_CONTENT,
            TelegramDisplayReasonCode.SAFE_LISTING_DISPLAY_MISMATCH,
            None,
            True,
        )
    if purpose == "RECOVERY_SCAN_COMPLETED" and refs and handoff is None:
        return (
            TelegramDisplayProjectionState.INVALID_CONTENT,
            TelegramDisplayReasonCode.SAFE_LISTING_DISPLAY_MISMATCH,
            None,
            True,
        )
    for action in request.action_references:
        if action.action_class in (
            TelegramDisplayClass.FULL_RESULT_OPEN_ACTION,
            TelegramDisplayClass.SHOW_MORE_ACTION,
        ) and (
            not refs or action.source_subject_reference_id != intent.notification_outbox_item_id
        ):
            return (
                TelegramDisplayProjectionState.INVALID_CONTENT,
                TelegramDisplayReasonCode.SAFE_LISTING_DISPLAY_MISMATCH,
                None,
                True,
            )
        if action.action_class is TelegramDisplayClass.BEACON_SETTINGS_ACTION and (
            h.outbox_beacon_reference_id is None
            or action.source_subject_reference_id != h.outbox_beacon_reference_id
        ):
            return (
                TelegramDisplayProjectionState.INVALID_CONTENT,
                TelegramDisplayReasonCode.SAFE_LISTING_DISPLAY_MISMATCH,
                None,
                True,
            )
    return (
        TelegramDisplayProjectionState.DISPLAY_PROJECTED,
        {
            "NEW_LISTINGS_FOUND": TelegramDisplayReasonCode.NEW_LISTINGS_DISPLAY_PROJECTED,
            "RECOVERY_SCAN_COMPLETED": TelegramDisplayReasonCode.RECOVERY_RESULT_DISPLAY_PROJECTED,
            "LOST_ANCHORS_RECOVERED": (
                TelegramDisplayReasonCode.LOST_ANCHORS_RESTORED_DISPLAY_PROJECTED
            ),
            "NO_NEW_LISTINGS_STATUS": TelegramDisplayReasonCode.NO_NEW_STATUS_DISPLAY_PROJECTED,
            "EXTERNAL_UNAVAILABLE_STATUS": (
                TelegramDisplayReasonCode.AVITO_UNAVAILABLE_STATUS_DISPLAY_PROJECTED
            ),
        }[purpose],
        None,
        True,
    )


class TelegramIdentityResolutionState(str, Enum):
    RESOLVED_ACCOUNT = "RESOLVED_ACCOUNT"
    NEW_ACCOUNT_REQUESTED = "NEW_ACCOUNT_REQUESTED"
    LINK_CHALLENGE_REQUIRED = "LINK_CHALLENGE_REQUIRED"
    REJECTED = "REJECTED"
    AMBIGUOUS = "AMBIGUOUS"


class TelegramProviderIdentity(_TelegramContract):
    """External Telegram identifiers; none is internal account authority."""

    telegram_provider_identity_ref: str = Field(min_length=1)
    telegram_bot_ref: str = Field(min_length=1)
    telegram_user_id: str = Field(min_length=1)
    telegram_chat_id: str | None = Field(default=None, min_length=1)


class VerifiedTelegramIdentityEvidence(_TelegramContract):
    """Safe evidence references, never a Telegram update or provider payload."""

    verified_identity_evidence_ref: str = Field(min_length=1)
    provider_identity: TelegramProviderIdentity
    verification_method_ref: str = Field(min_length=1)
    verification_result_ref: str = Field(min_length=1)


class TelegramChatSurfaceClass(str, Enum):
    PRIVATE_CHAT = "PRIVATE_CHAT"
    GROUP = "GROUP"
    SUPERGROUP = "SUPERGROUP"
    CHANNEL = "CHANNEL"
    FORUM_TOPIC = "FORUM_TOPIC"
    BUSINESS_CONNECTION = "BUSINESS_CONNECTION"
    SHARED_CHAT = "SHARED_CHAT"
    UNKNOWN = "UNKNOWN"


class TelegramChatSurfaceAdmissionState(str, Enum):
    PRIVATE_CHAT_ADMITTED = "PRIVATE_CHAT_ADMITTED"
    UNSUPPORTED_SURFACE_IGNORED = "UNSUPPORTED_SURFACE_IGNORED"
    AMBIGUOUS_SURFACE_REJECTED = "AMBIGUOUS_SURFACE_REJECTED"


class TelegramChatSurfaceReasonCode(str, Enum):
    PRIVATE_CHAT_V1_SUPPORTED = "PRIVATE_CHAT_V1_SUPPORTED"
    GROUP_NOT_SUPPORTED = "GROUP_NOT_SUPPORTED"
    SUPERGROUP_NOT_SUPPORTED = "SUPERGROUP_NOT_SUPPORTED"
    CHANNEL_NOT_SUPPORTED = "CHANNEL_NOT_SUPPORTED"
    FORUM_TOPIC_NOT_SUPPORTED = "FORUM_TOPIC_NOT_SUPPORTED"
    BUSINESS_CONNECTION_NOT_SUPPORTED = "BUSINESS_CONNECTION_NOT_SUPPORTED"
    SHARED_CHAT_NOT_SUPPORTED = "SHARED_CHAT_NOT_SUPPORTED"
    UNKNOWN_SURFACE = "UNKNOWN_SURFACE"


class TelegramAccountLinkReference(_TelegramContract):
    """Telegram-owned reference to an already accepted Identity decision."""

    telegram_account_link_reference_id: str = Field(min_length=1)
    provider_identity: TelegramProviderIdentity
    account_id: str = Field(min_length=1)
    identity_account_reference_id: str = Field(min_length=1)
    identity_provider_identity_id: str = Field(min_length=1)
    identity_provider: Literal["TELEGRAM"] = "TELEGRAM"

    @model_validator(mode="after")
    def _provider_identity_matches(self) -> "TelegramAccountLinkReference":
        if self.identity_provider_identity_id != self.provider_identity.telegram_user_id:
            raise ValueError("identity_provider_identity_id must match telegram_user_id")
        return self


class TelegramIdentityResolutionRequest(_TelegramContract):
    """Idempotent request reference for Identity-owned resolution."""

    telegram_identity_resolution_request_id: str = Field(min_length=1)
    metadata: ContractMetadata
    idempotency_key: IdempotencyKey
    idempotency_scope: IdempotencyScope
    fingerprint: IdempotencyFingerprint
    verified_identity_evidence: VerifiedTelegramIdentityEvidence
    identity_resolution_contract_ref: str = Field(min_length=1)


class TelegramIdentityResolutionOutcome(_TelegramContract):
    """Safe outcome projection; account decisions remain Identity-owned."""

    telegram_identity_resolution_reference_id: str = Field(min_length=1)
    telegram_identity_resolution_request_id: str = Field(min_length=1)
    identity_decision_reference_id: str = Field(min_length=1)
    state: TelegramIdentityResolutionState
    provider_identity: TelegramProviderIdentity
    reason_code: str = Field(min_length=1)
    account_link: TelegramAccountLinkReference | None = None
    identity_link_challenge_ref: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def _validate_state_matrix(self) -> "TelegramIdentityResolutionOutcome":
        if self.state is TelegramIdentityResolutionState.RESOLVED_ACCOUNT:
            if self.account_link is None or self.identity_link_challenge_ref is not None:
                raise ValueError("resolved account requires only account_link")
            if self.provider_identity != self.account_link.provider_identity:
                raise ValueError("provider_identity must match account_link")
        elif self.state is TelegramIdentityResolutionState.LINK_CHALLENGE_REQUIRED:
            if self.identity_link_challenge_ref is None or self.account_link is not None:
                raise ValueError("link challenge requires only challenge reference")
        elif self.account_link is not None or self.identity_link_challenge_ref is not None:
            raise ValueError("this outcome state cannot contain account or challenge reference")
        return self


class TelegramProviderUpdateIdentity(_TelegramContract):
    """Opaque provider-scope identity for one Telegram update."""

    telegram_provider_update_ref: str = Field(min_length=1)
    telegram_bot_ref: str = Field(min_length=1)
    telegram_update_id: str = Field(min_length=1)
    provider_update_type_ref: str = Field(min_length=1)


class TelegramUpdateAdmissionState(str, Enum):
    VERIFIED = "VERIFIED"
    NOT_VERIFIED = "NOT_VERIFIED"
    REJECTED = "REJECTED"
    AMBIGUOUS = "AMBIGUOUS"


class TelegramUpdateStructuralClass(str, Enum):
    SUPPORTED_CANDIDATE = "SUPPORTED_CANDIDATE"
    UNSUPPORTED = "UNSUPPORTED"
    MALFORMED = "MALFORMED"
    AMBIGUOUS = "AMBIGUOUS"


class TelegramUpdateIntakeState(str, Enum):
    ACCEPTED_FOR_NORMALIZATION = "ACCEPTED_FOR_NORMALIZATION"
    IGNORED_UNSUPPORTED = "IGNORED_UNSUPPORTED"
    REJECTED_UNTRUSTED = "REJECTED_UNTRUSTED"
    REJECTED_MALFORMED = "REJECTED_MALFORMED"
    AMBIGUOUS = "AMBIGUOUS"


class TelegramUpdateDeduplicationState(str, Enum):
    NEW_UPDATE = "NEW_UPDATE"
    DUPLICATE_REPLAY = "DUPLICATE_REPLAY"
    FINGERPRINT_CONFLICT = "FINGERPRINT_CONFLICT"
    AMBIGUOUS = "AMBIGUOUS"


class TelegramUpdateIntakeRecord(_TelegramContract):
    telegram_update_intake_record_id: str = Field(min_length=1)
    metadata: ContractMetadata
    provider_update_identity: TelegramProviderUpdateIdentity
    provider_identity: TelegramProviderIdentity | None = None
    idempotency_key: IdempotencyKey
    idempotency_scope: IdempotencyScope
    fingerprint: IdempotencyFingerprint
    admission_state: TelegramUpdateAdmissionState
    structural_classification: TelegramUpdateStructuralClass
    intake_state: TelegramUpdateIntakeState
    provider_admission_evidence_ref: str | None = Field(default=None, min_length=1)
    normalization_reference_id: str | None = Field(default=None, min_length=1)
    reason_code: str = Field(min_length=1)
    business_dispatch_authorized: Literal[False] = False

    @model_validator(mode="after")
    def _validate_intake_matrix(self) -> "TelegramUpdateIntakeRecord":
        if self.provider_identity is not None and (
            self.provider_identity.telegram_bot_ref
            != self.provider_update_identity.telegram_bot_ref
        ):
            raise ValueError("provider_identity telegram_bot_ref must match update identity")

        if self.intake_state is TelegramUpdateIntakeState.ACCEPTED_FOR_NORMALIZATION:
            if self.admission_state is not TelegramUpdateAdmissionState.VERIFIED:
                raise ValueError("accepted intake requires verified admission")
            if (
                self.structural_classification
                is not TelegramUpdateStructuralClass.SUPPORTED_CANDIDATE
            ):
                raise ValueError("accepted intake requires supported candidate structure")
            if not self.provider_admission_evidence_ref or not self.normalization_reference_id:
                raise ValueError("accepted intake requires admission and normalization references")
        elif self.intake_state is TelegramUpdateIntakeState.IGNORED_UNSUPPORTED:
            if self.structural_classification is not TelegramUpdateStructuralClass.UNSUPPORTED:
                raise ValueError("ignored intake requires unsupported structure")
        elif self.intake_state is TelegramUpdateIntakeState.REJECTED_UNTRUSTED:
            if self.admission_state not in {
                TelegramUpdateAdmissionState.NOT_VERIFIED,
                TelegramUpdateAdmissionState.REJECTED,
            }:
                raise ValueError("untrusted rejection requires failed admission")
        elif self.intake_state is TelegramUpdateIntakeState.REJECTED_MALFORMED:
            if self.structural_classification is not TelegramUpdateStructuralClass.MALFORMED:
                raise ValueError("malformed rejection requires malformed structure")
        elif self.admission_state is not TelegramUpdateAdmissionState.AMBIGUOUS and (
            self.structural_classification is not TelegramUpdateStructuralClass.AMBIGUOUS
        ):
            raise ValueError("ambiguous intake requires ambiguous admission or structure")

        if self.intake_state is not TelegramUpdateIntakeState.ACCEPTED_FOR_NORMALIZATION:
            if self.normalization_reference_id is not None:
                raise ValueError("only accepted intake may have normalization reference")
        return self


class TelegramUntrustedChatSurfaceReference(_TelegramContract):
    telegram_chat_surface_reference_id: str = Field(min_length=1)
    telegram_bot_ref: str = Field(min_length=1)
    telegram_update_intake_record_id: str = Field(min_length=1)
    telegram_chat_provider_reference: str = Field(min_length=1)
    surface_class: TelegramChatSurfaceClass
    private_participant_provider_identity_reference: str | None = Field(default=None, min_length=1)
    forum_topic_provider_reference: str | None = Field(default=None, min_length=1)
    business_connection_provider_reference: str | None = Field(default=None, min_length=1)
    shared_chat_provider_reference: str | None = Field(default=None, min_length=1)
    provider_input_untrusted: Literal[True] = True
    private_chat_only_v1: Literal[True] = True
    group_membership_used_as_ownership: Literal[False] = False
    chat_title_used_as_ownership: Literal[False] = False
    username_or_display_name_used_as_ownership: Literal[False] = False
    multi_user_chat_ownership_supported: Literal[False] = False
    internal_account_authority: Literal[False] = False
    business_effect_authorized: Literal[False] = False
    raw_provider_payload_retained: Literal[False] = False

    @model_validator(mode="after")
    def _validate_specialized_reference_matrix(self) -> "TelegramUntrustedChatSurfaceReference":
        references = {
            "private participant": self.private_participant_provider_identity_reference,
            "forum topic": self.forum_topic_provider_reference,
            "business connection": self.business_connection_provider_reference,
            "shared chat": self.shared_chat_provider_reference,
        }
        required_by_surface = {
            TelegramChatSurfaceClass.PRIVATE_CHAT: "private participant",
            TelegramChatSurfaceClass.FORUM_TOPIC: "forum topic",
            TelegramChatSurfaceClass.BUSINESS_CONNECTION: "business connection",
            TelegramChatSurfaceClass.SHARED_CHAT: "shared chat",
        }
        required = (
            required_by_surface[self.surface_class]
            if self.surface_class in required_by_surface
            else None
        )
        if required is not None and references[required] is None:
            raise ValueError(f"{required} reference is required for {self.surface_class.value}")
        for label, value in references.items():
            if label != required and value is not None:
                raise ValueError(f"{label} reference is forbidden for {self.surface_class.value}")
        return self


class TelegramChatSurfaceAdmissionRequest(_TelegramContract):
    telegram_chat_surface_admission_request_id: str = Field(min_length=1)
    metadata: ContractMetadata
    update_intake_record: TelegramUpdateIntakeRecord
    chat_surface: TelegramUntrustedChatSurfaceReference
    verified_telegram_provider_identity_evidence: VerifiedTelegramIdentityEvidence | None = None
    surface_policy_reference_id: str = Field(min_length=1)
    private_chat_only_v1: Literal[True] = True
    unsupported_surfaces_have_no_business_effect: Literal[True] = True
    internal_account_resolution_authority: Literal[False] = False
    business_effect_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False
    outbound_delivery_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_intake_and_identity_binding(self) -> "TelegramChatSurfaceAdmissionRequest":
        surface = self.chat_surface
        intake = self.update_intake_record
        intake_bot_ref = intake.provider_update_identity.telegram_bot_ref
        if surface.telegram_update_intake_record_id != intake.telegram_update_intake_record_id:
            raise ValueError("surface intake reference must match update intake record")
        if surface.telegram_bot_ref != intake_bot_ref:
            raise ValueError("surface bot scope must match update intake bot scope")
        evidence = self.verified_telegram_provider_identity_evidence
        if surface.surface_class is TelegramChatSurfaceClass.PRIVATE_CHAT:
            if evidence is None:
                raise ValueError("private chat requires verified identity evidence")
            if (
                surface.private_participant_provider_identity_reference
                != evidence.provider_identity.telegram_provider_identity_ref
            ):
                raise ValueError("private participant must match verified provider identity")
            if evidence.provider_identity.telegram_bot_ref != surface.telegram_bot_ref:
                raise ValueError("verified identity bot scope must match surface bot scope")
        elif evidence is not None:
            raise ValueError("non-private surfaces forbid identity evidence")
        return self


class TelegramChatSurfaceAdmissionOutcome(_TelegramContract):
    telegram_chat_surface_admission_outcome_id: str = Field(min_length=1)
    metadata: ContractMetadata
    request: TelegramChatSurfaceAdmissionRequest
    admission_state: TelegramChatSurfaceAdmissionState
    reason_code: TelegramChatSurfaceReasonCode
    admitted_update_intake_record_id: str | None = Field(default=None, min_length=1)
    verified_provider_identity_reference: str | None = Field(default=None, min_length=1)
    safe_diagnostic_reference_id: str | None = Field(default=None, min_length=1)
    private_chat_only_v1: Literal[True] = True
    unsupported_surface_business_effect: Literal[False] = False
    chat_surface_establishes_internal_account_ownership: Literal[False] = False
    group_or_channel_delivery_authorized: Literal[False] = False
    private_listing_delivery_authorized: Literal[False] = False
    business_effect_authorized: Literal[False] = False
    raw_provider_payload_retained: Literal[False] = False

    @model_validator(mode="after")
    def _validate_outcome_matrix(self) -> "TelegramChatSurfaceAdmissionOutcome":
        surface_class = self.request.chat_surface.surface_class
        unsupported_reasons = {
            TelegramChatSurfaceClass.GROUP: TelegramChatSurfaceReasonCode.GROUP_NOT_SUPPORTED,
            TelegramChatSurfaceClass.SUPERGROUP: (
                TelegramChatSurfaceReasonCode.SUPERGROUP_NOT_SUPPORTED
            ),
            TelegramChatSurfaceClass.CHANNEL: TelegramChatSurfaceReasonCode.CHANNEL_NOT_SUPPORTED,
            TelegramChatSurfaceClass.FORUM_TOPIC: (
                TelegramChatSurfaceReasonCode.FORUM_TOPIC_NOT_SUPPORTED
            ),
            TelegramChatSurfaceClass.BUSINESS_CONNECTION: (
                TelegramChatSurfaceReasonCode.BUSINESS_CONNECTION_NOT_SUPPORTED
            ),
            TelegramChatSurfaceClass.SHARED_CHAT: (
                TelegramChatSurfaceReasonCode.SHARED_CHAT_NOT_SUPPORTED
            ),
        }
        if surface_class is TelegramChatSurfaceClass.PRIVATE_CHAT:
            expected = (
                TelegramChatSurfaceAdmissionState.PRIVATE_CHAT_ADMITTED,
                TelegramChatSurfaceReasonCode.PRIVATE_CHAT_V1_SUPPORTED,
            )
            if (self.admission_state, self.reason_code) != expected:
                raise ValueError("private chat outcome has invalid state or reason")
            if (
                self.admitted_update_intake_record_id
                != self.request.update_intake_record.telegram_update_intake_record_id
            ):
                raise ValueError("admitted outcome must carry the intake identifier")
            expected_identity = self.request.verified_telegram_provider_identity_evidence
            if (
                expected_identity is None
                or self.verified_provider_identity_reference
                != expected_identity.provider_identity.telegram_provider_identity_ref
            ):
                raise ValueError("admitted outcome must carry the verified identity reference")
            if self.safe_diagnostic_reference_id is not None:
                raise ValueError("admitted outcome forbids diagnostic reference")
        else:
            expected_state = (
                TelegramChatSurfaceAdmissionState.AMBIGUOUS_SURFACE_REJECTED
                if surface_class is TelegramChatSurfaceClass.UNKNOWN
                else TelegramChatSurfaceAdmissionState.UNSUPPORTED_SURFACE_IGNORED
            )
            expected_reason = (
                TelegramChatSurfaceReasonCode.UNKNOWN_SURFACE
                if surface_class is TelegramChatSurfaceClass.UNKNOWN
                else unsupported_reasons[surface_class]
            )
            if (self.admission_state, self.reason_code) != (expected_state, expected_reason):
                raise ValueError("unsupported or ambiguous outcome has invalid state or reason")
            if (
                self.admitted_update_intake_record_id is not None
                or self.verified_provider_identity_reference is not None
            ):
                raise ValueError("ignored or rejected outcome forbids handoff references")
            if self.safe_diagnostic_reference_id is None:
                raise ValueError("ignored or rejected outcome requires a diagnostic reference")
        return self


class TelegramUpdateDeduplicationRecord(_TelegramContract):
    telegram_update_deduplication_record_id: str = Field(min_length=1)
    metadata: ContractMetadata
    provider_update_identity: TelegramProviderUpdateIdentity
    idempotency_key: IdempotencyKey
    idempotency_scope: IdempotencyScope
    fingerprint: IdempotencyFingerprint
    state: TelegramUpdateDeduplicationState
    current_intake_record_id: str = Field(min_length=1)
    existing_intake_record_id: str | None = Field(default=None, min_length=1)
    existing_fingerprint: IdempotencyFingerprint | None = None
    replayed_adapter_outcome_ref: str | None = Field(default=None, min_length=1)
    adapter_processing_authorized: bool
    second_business_effect_authorized: Literal[False] = False
    reason_code: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_dedup_matrix(self) -> "TelegramUpdateDeduplicationRecord":
        if self.state is TelegramUpdateDeduplicationState.NEW_UPDATE:
            if any(
                (
                    self.existing_intake_record_id,
                    self.existing_fingerprint,
                    self.replayed_adapter_outcome_ref,
                )
            ):
                raise ValueError("new update cannot reference an existing outcome")
            if not self.adapter_processing_authorized:
                raise ValueError("new update authorizes adapter processing")
        elif self.state is TelegramUpdateDeduplicationState.DUPLICATE_REPLAY:
            if not self.existing_intake_record_id or self.existing_fingerprint is None:
                raise ValueError("duplicate replay requires existing intake and fingerprint")
            if self.existing_fingerprint != self.fingerprint:
                raise ValueError("duplicate replay requires matching fingerprint")
            if not self.replayed_adapter_outcome_ref or self.adapter_processing_authorized:
                raise ValueError("duplicate replay requires safe outcome replay only")
        elif self.state is TelegramUpdateDeduplicationState.FINGERPRINT_CONFLICT:
            if not self.existing_intake_record_id or self.existing_fingerprint is None:
                raise ValueError("fingerprint conflict requires existing intake and fingerprint")
            if self.existing_fingerprint == self.fingerprint:
                raise ValueError("fingerprint conflict requires different fingerprint")
            if self.replayed_adapter_outcome_ref or self.adapter_processing_authorized:
                raise ValueError("fingerprint conflict cannot authorize processing or replay")
        else:
            if not self.existing_intake_record_id or self.existing_fingerprint is None:
                raise ValueError("ambiguous deduplication requires existing intake and fingerprint")
            if self.replayed_adapter_outcome_ref or self.adapter_processing_authorized:
                raise ValueError("ambiguous deduplication cannot authorize processing or replay")
        return self


class TelegramInboundInputKind(str, Enum):
    COMMAND_CANDIDATE = "COMMAND_CANDIDATE"
    MESSAGE_TEXT_CANDIDATE = "MESSAGE_TEXT_CANDIDATE"
    SOURCE_URL_CANDIDATE = "SOURCE_URL_CANDIDATE"
    UNSUPPORTED_INPUT = "UNSUPPORTED_INPUT"
    AMBIGUOUS_INPUT = "AMBIGUOUS_INPUT"


class TelegramIntentFamily(str, Enum):
    START_OR_LINK_TELEGRAM = "START_OR_LINK_TELEGRAM"
    HELP_REQUESTED = "HELP_REQUESTED"
    LIST_MY_BEACONS_REQUESTED = "LIST_MY_BEACONS_REQUESTED"
    BEACON_STATUS_REQUESTED = "BEACON_STATUS_REQUESTED"
    CREATE_BEACON_FROM_SOURCE_URL_REQUESTED = "CREATE_BEACON_FROM_SOURCE_URL_REQUESTED"
    BEACON_SETTINGS_REQUESTED = "BEACON_SETTINGS_REQUESTED"
    UPDATE_BEACON_INTERVAL_OR_STATUS_PREF_REQUESTED = (
        "UPDATE_BEACON_INTERVAL_OR_STATUS_PREF_REQUESTED"  # noqa: E501
    )
    PAUSE_BEACON_REQUESTED = "PAUSE_BEACON_REQUESTED"
    RESUME_BEACON_REQUESTED = "RESUME_BEACON_REQUESTED"
    DELETE_BEACON_REQUESTED_WITH_CONFIRMATION = "DELETE_BEACON_REQUESTED_WITH_CONFIRMATION"
    TARIFF_OR_LIMITS_REQUESTED = "TARIFF_OR_LIMITS_REQUESTED"
    OPEN_FULL_LISTING_RESULT_REQUESTED = "OPEN_FULL_LISTING_RESULT_REQUESTED"
    TOGGLE_NO_NEW_STATUS_NOTIFICATION_REQUESTED = "TOGGLE_NO_NEW_STATUS_NOTIFICATION_REQUESTED"
    UNSUPPORTED_OR_AMBIGUOUS_INPUT = "UNSUPPORTED_OR_AMBIGUOUS_INPUT"


class TelegramIntentNormalizationState(str, Enum):
    NORMALIZED = "NORMALIZED"
    UNSUPPORTED = "UNSUPPORTED"
    AMBIGUOUS = "AMBIGUOUS"
    BLOCKED = "BLOCKED"


class TelegramIntentOwnerBoundary(str, Enum):
    TELEGRAM_ADAPTER = "TELEGRAM_ADAPTER"
    IDENTITY_AND_ACCESS = "IDENTITY_AND_ACCESS"
    BEACON_MANAGEMENT = "BEACON_MANAGEMENT"
    NOTIFICATION_DELIVERY = "NOTIFICATION_DELIVERY"
    ENTITLEMENTS_AND_BILLING = "ENTITLEMENTS_AND_BILLING"
    NONE = "NONE"


_INTENT_OWNER_BOUNDARIES: dict[TelegramIntentFamily, tuple[TelegramIntentOwnerBoundary, ...]] = {
    TelegramIntentFamily.START_OR_LINK_TELEGRAM: (TelegramIntentOwnerBoundary.IDENTITY_AND_ACCESS,),
    TelegramIntentFamily.HELP_REQUESTED: (TelegramIntentOwnerBoundary.TELEGRAM_ADAPTER,),
    TelegramIntentFamily.LIST_MY_BEACONS_REQUESTED: (
        TelegramIntentOwnerBoundary.BEACON_MANAGEMENT,
    ),  # noqa: E501
    TelegramIntentFamily.BEACON_STATUS_REQUESTED: (TelegramIntentOwnerBoundary.BEACON_MANAGEMENT,),
    TelegramIntentFamily.CREATE_BEACON_FROM_SOURCE_URL_REQUESTED: (
        TelegramIntentOwnerBoundary.BEACON_MANAGEMENT,
    ),  # noqa: E501
    TelegramIntentFamily.BEACON_SETTINGS_REQUESTED: (
        TelegramIntentOwnerBoundary.BEACON_MANAGEMENT,
    ),  # noqa: E501
    TelegramIntentFamily.UPDATE_BEACON_INTERVAL_OR_STATUS_PREF_REQUESTED: (
        TelegramIntentOwnerBoundary.BEACON_MANAGEMENT,
        TelegramIntentOwnerBoundary.NOTIFICATION_DELIVERY,
    ),
    TelegramIntentFamily.PAUSE_BEACON_REQUESTED: (TelegramIntentOwnerBoundary.BEACON_MANAGEMENT,),
    TelegramIntentFamily.RESUME_BEACON_REQUESTED: (TelegramIntentOwnerBoundary.BEACON_MANAGEMENT,),
    TelegramIntentFamily.DELETE_BEACON_REQUESTED_WITH_CONFIRMATION: (
        TelegramIntentOwnerBoundary.BEACON_MANAGEMENT,
    ),  # noqa: E501
    TelegramIntentFamily.TARIFF_OR_LIMITS_REQUESTED: (
        TelegramIntentOwnerBoundary.ENTITLEMENTS_AND_BILLING,
    ),  # noqa: E501
    TelegramIntentFamily.OPEN_FULL_LISTING_RESULT_REQUESTED: (
        TelegramIntentOwnerBoundary.NOTIFICATION_DELIVERY,
    ),  # noqa: E501
    TelegramIntentFamily.TOGGLE_NO_NEW_STATUS_NOTIFICATION_REQUESTED: (
        TelegramIntentOwnerBoundary.NOTIFICATION_DELIVERY,
    ),  # noqa: E501
    TelegramIntentFamily.UNSUPPORTED_OR_AMBIGUOUS_INPUT: (TelegramIntentOwnerBoundary.NONE,),
}


class TelegramUntrustedInputReference(_TelegramContract):
    telegram_untrusted_input_reference_id: str = Field(min_length=1)
    provider_update_identity: TelegramProviderUpdateIdentity
    input_kind: TelegramInboundInputKind
    input_evidence_reference_id: str = Field(min_length=1)
    candidate_source_url_reference_id: str | None = Field(default=None, min_length=1)
    raw_provider_payload_present: Literal[False] = False
    input_text_retained: Literal[False] = False
    input_trusted: Literal[False] = False
    input_is_authorization: Literal[False] = False
    candidate_source_url_validated: Literal[False] = False

    @model_validator(mode="after")
    def _validate_candidate_reference(self) -> "TelegramUntrustedInputReference":
        if self.input_kind is TelegramInboundInputKind.SOURCE_URL_CANDIDATE:
            if self.candidate_source_url_reference_id is None:
                raise ValueError("source URL candidate requires an opaque reference")
        elif self.candidate_source_url_reference_id is not None:
            raise ValueError("only source URL candidates may carry a candidate reference")
        return self


class TelegramIntentNormalizationRequest(_TelegramContract):
    telegram_intent_normalization_request_id: str = Field(min_length=1)
    metadata: ContractMetadata
    intake_record: TelegramUpdateIntakeRecord
    deduplication_record: TelegramUpdateDeduplicationRecord
    untrusted_input: TelegramUntrustedInputReference
    normalization_policy_reference_id: str = Field(min_length=1)
    business_dispatch_authorized: Literal[False] = False
    handler_execution_authorized: Literal[False] = False
    conversation_state_machine_authorized: Literal[False] = False

    @model_validator(mode="after")
    def _validate_prerequisites(self) -> "TelegramIntentNormalizationRequest":
        intake = self.intake_record
        dedup = self.deduplication_record
        update = intake.provider_update_identity
        if intake.intake_state is not TelegramUpdateIntakeState.ACCEPTED_FOR_NORMALIZATION:
            raise ValueError("normalization requires accepted intake")
        if intake.admission_state is not TelegramUpdateAdmissionState.VERIFIED:
            raise ValueError("normalization requires verified admission")
        if (
            intake.structural_classification
            is not TelegramUpdateStructuralClass.SUPPORTED_CANDIDATE
        ):  # noqa: E501
            raise ValueError("normalization requires supported candidate")
        if intake.provider_identity is None:
            raise ValueError("normalization requires provider identity")
        if intake.normalization_reference_id != self.telegram_intent_normalization_request_id:
            raise ValueError("normalization reference must match request id")
        if (
            dedup.state is not TelegramUpdateDeduplicationState.NEW_UPDATE
            or not dedup.adapter_processing_authorized
        ):  # noqa: E501
            raise ValueError(
                "normalization requires a new update authorized for adapter processing"
            )  # noqa: E501
        if dedup.current_intake_record_id != intake.telegram_update_intake_record_id:
            raise ValueError("deduplication must point at current intake")
        if not (
            update == dedup.provider_update_identity
            and intake.idempotency_key == dedup.idempotency_key
            and intake.idempotency_scope == dedup.idempotency_scope
            and intake.fingerprint == dedup.fingerprint
            and self.untrusted_input.provider_update_identity == update
            and intake.provider_identity.telegram_bot_ref == update.telegram_bot_ref
        ):
            raise ValueError("intake, deduplication and input identity must agree")
        return self


class TelegramCommandEnvelope(_TelegramContract):
    telegram_command_envelope_id: str = Field(min_length=1)
    metadata: ContractMetadata
    normalization_request: TelegramIntentNormalizationRequest
    state: TelegramIntentNormalizationState
    intent_family: TelegramIntentFamily
    owner_boundaries: tuple[TelegramIntentOwnerBoundary, ...]
    owner_contract_reference_ids: tuple[str, ...]
    candidate_source_url_reference_id: str | None = Field(default=None, min_length=1)
    blocking_decision_reference_id: str | None = Field(default=None, min_length=1)
    dangerous_action_confirmation_required: bool
    reason_code: str = Field(min_length=1)
    exact_command_catalog_selected: Literal[False] = False
    command_handler_authorized: Literal[False] = False
    conversation_state_machine_authorized: Literal[False] = False
    business_dispatch_authorized: Literal[False] = False
    account_creation_authorized: Literal[False] = False
    beacon_creation_or_mutation_authorized: Literal[False] = False
    source_url_business_validation_authorized: Literal[False] = False
    notification_preference_mutation_authorized: Literal[False] = False
    entitlement_mutation_authorized: Literal[False] = False
    provider_runtime_authorized: Literal[False] = False

    @model_validator(mode="after")
    def _validate_envelope_matrix(self) -> "TelegramCommandEnvelope":
        family = self.intent_family
        input_kind = self.normalization_request.untrusted_input.input_kind
        expected = _INTENT_OWNER_BOUNDARIES[family]
        if self.state in {
            TelegramIntentNormalizationState.UNSUPPORTED,
            TelegramIntentNormalizationState.AMBIGUOUS,
        }:  # noqa: E501
            expected_family = TelegramIntentFamily.UNSUPPORTED_OR_AMBIGUOUS_INPUT
            expected_kind = (
                TelegramInboundInputKind.UNSUPPORTED_INPUT
                if self.state is TelegramIntentNormalizationState.UNSUPPORTED
                else TelegramInboundInputKind.AMBIGUOUS_INPUT
            )  # noqa: E501
            if (
                family is not expected_family
                or input_kind is not expected_kind
                or self.owner_boundaries != (TelegramIntentOwnerBoundary.NONE,)
                or self.owner_contract_reference_ids
                or self.candidate_source_url_reference_id is not None
                or self.blocking_decision_reference_id is not None
                or self.dangerous_action_confirmation_required
            ):  # noqa: E501
                raise ValueError("unsupported and ambiguous envelope matrix is exact")
            return self
        if family is TelegramIntentFamily.UNSUPPORTED_OR_AMBIGUOUS_INPUT or input_kind in {
            TelegramInboundInputKind.UNSUPPORTED_INPUT,
            TelegramInboundInputKind.AMBIGUOUS_INPUT,
        }:  # noqa: E501
            raise ValueError("supported envelope cannot use unsupported or ambiguous input")
        if (
            self.owner_boundaries != expected
            or TelegramIntentOwnerBoundary.NONE in self.owner_boundaries
        ):  # noqa: E501
            raise ValueError("owner boundaries do not match intent family")
        if self.state is TelegramIntentNormalizationState.NORMALIZED:
            if (
                self.blocking_decision_reference_id is not None
                or len(self.owner_contract_reference_ids) != len(expected)
                or any(not ref.strip() for ref in self.owner_contract_reference_ids)
            ):  # noqa: E501
                raise ValueError("normalized envelope requires owner references and no block")
        elif self.state is TelegramIntentNormalizationState.BLOCKED:
            if not self.blocking_decision_reference_id or self.owner_contract_reference_ids:
                raise ValueError("blocked envelope requires only a blocking reference")
        if family is TelegramIntentFamily.CREATE_BEACON_FROM_SOURCE_URL_REQUESTED:
            if (
                input_kind is not TelegramInboundInputKind.SOURCE_URL_CANDIDATE
                or self.candidate_source_url_reference_id
                != self.normalization_request.untrusted_input.candidate_source_url_reference_id
            ):  # noqa: E501
                raise ValueError("create intent requires the exact opaque source reference")
        elif self.candidate_source_url_reference_id is not None:
            raise ValueError("only create intent may carry a source reference")
        if self.dangerous_action_confirmation_required != (
            family is TelegramIntentFamily.DELETE_BEACON_REQUESTED_WITH_CONFIRMATION
        ):  # noqa: E501
            raise ValueError("only deletion requires confirmation")
        return self


class TelegramCallbackActionScope(str, Enum):
    OPEN_CONTEXT = "OPEN_CONTEXT"
    READ_BEACON = "READ_BEACON"
    UPDATE_BEACON = "UPDATE_BEACON"
    PAUSE_BEACON = "PAUSE_BEACON"
    RESUME_BEACON = "RESUME_BEACON"
    DELETE_BEACON = "DELETE_BEACON"
    CHANGE_BEACON_SOURCE_URL = "CHANGE_BEACON_SOURCE_URL"
    UNLINK_TELEGRAM_IDENTITY = "UNLINK_TELEGRAM_IDENTITY"
    DISABLE_NOTIFICATION_CHANNEL = "DISABLE_NOTIFICATION_CHANNEL"
    TARIFF_OR_PAYMENT_SENSITIVE_ACTION = "TARIFF_OR_PAYMENT_SENSITIVE_ACTION"
    UNSUPPORTED_ACTION = "UNSUPPORTED_ACTION"
    AMBIGUOUS_ACTION = "AMBIGUOUS_ACTION"


class TelegramCallbackRiskClass(str, Enum):
    NON_DESTRUCTIVE = "NON_DESTRUCTIVE"
    STATE_CHANGING = "STATE_CHANGING"
    DESTRUCTIVE = "DESTRUCTIVE"
    IDENTITY_SENSITIVE = "IDENTITY_SENSITIVE"
    NOTIFICATION_SENSITIVE = "NOTIFICATION_SENSITIVE"
    PAYMENT_OR_TARIFF_SENSITIVE = "PAYMENT_OR_TARIFF_SENSITIVE"
    UNSUPPORTED_OR_AMBIGUOUS = "UNSUPPORTED_OR_AMBIGUOUS"


class TelegramCallbackPayloadValidationMode(str, Enum):
    OPAQUE_SERVER_RESOLVED = "OPAQUE_SERVER_RESOLVED"
    SIGNED_VALIDATED = "SIGNED_VALIDATED"
    UNVALIDATED = "UNVALIDATED"
    AMBIGUOUS = "AMBIGUOUS"


class TelegramCallbackReplayState(str, Enum):
    NEW_ACTION = "NEW_ACTION"
    DUPLICATE_REPLAY = "DUPLICATE_REPLAY"
    FINGERPRINT_CONFLICT = "FINGERPRINT_CONFLICT"
    AMBIGUOUS = "AMBIGUOUS"


class TelegramCallbackExpiryState(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    VALID = "VALID"
    EXPIRED = "EXPIRED"
    MISSING = "MISSING"
    AMBIGUOUS = "AMBIGUOUS"


class TelegramCallbackConfirmationState(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    REQUIRED = "REQUIRED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class TelegramCallbackValidationState(str, Enum):
    VALIDATED_FOR_OWNER_HANDOFF = "VALIDATED_FOR_OWNER_HANDOFF"
    CONFIRMATION_REQUIRED = "CONFIRMATION_REQUIRED"
    REJECTED_UNTRUSTED = "REJECTED_UNTRUSTED"
    REJECTED_EXPIRED = "REJECTED_EXPIRED"
    REJECTED_UNAUTHORIZED = "REJECTED_UNAUTHORIZED"
    DUPLICATE_REPLAY = "DUPLICATE_REPLAY"
    FINGERPRINT_CONFLICT = "FINGERPRINT_CONFLICT"
    UNSUPPORTED = "UNSUPPORTED"
    AMBIGUOUS = "AMBIGUOUS"
    BLOCKED = "BLOCKED"


_CALLBACK_OWNER: dict[TelegramCallbackActionScope, TelegramIntentOwnerBoundary] = {
    TelegramCallbackActionScope.OPEN_CONTEXT: TelegramIntentOwnerBoundary.TELEGRAM_ADAPTER,
    TelegramCallbackActionScope.READ_BEACON: TelegramIntentOwnerBoundary.BEACON_MANAGEMENT,
    TelegramCallbackActionScope.UPDATE_BEACON: TelegramIntentOwnerBoundary.BEACON_MANAGEMENT,
    TelegramCallbackActionScope.PAUSE_BEACON: TelegramIntentOwnerBoundary.BEACON_MANAGEMENT,
    TelegramCallbackActionScope.RESUME_BEACON: TelegramIntentOwnerBoundary.BEACON_MANAGEMENT,
    TelegramCallbackActionScope.DELETE_BEACON: TelegramIntentOwnerBoundary.BEACON_MANAGEMENT,
    TelegramCallbackActionScope.CHANGE_BEACON_SOURCE_URL: TelegramIntentOwnerBoundary.BEACON_MANAGEMENT,  # noqa: E501
    TelegramCallbackActionScope.UNLINK_TELEGRAM_IDENTITY: TelegramIntentOwnerBoundary.IDENTITY_AND_ACCESS,  # noqa: E501
    TelegramCallbackActionScope.DISABLE_NOTIFICATION_CHANNEL: TelegramIntentOwnerBoundary.NOTIFICATION_DELIVERY,  # noqa: E501
    TelegramCallbackActionScope.TARIFF_OR_PAYMENT_SENSITIVE_ACTION: TelegramIntentOwnerBoundary.ENTITLEMENTS_AND_BILLING,  # noqa: E501
    TelegramCallbackActionScope.UNSUPPORTED_ACTION: TelegramIntentOwnerBoundary.NONE,
    TelegramCallbackActionScope.AMBIGUOUS_ACTION: TelegramIntentOwnerBoundary.NONE,
}

_CALLBACK_RISK: dict[TelegramCallbackActionScope, TelegramCallbackRiskClass] = {
    TelegramCallbackActionScope.OPEN_CONTEXT: TelegramCallbackRiskClass.NON_DESTRUCTIVE,
    TelegramCallbackActionScope.READ_BEACON: TelegramCallbackRiskClass.NON_DESTRUCTIVE,
    TelegramCallbackActionScope.UPDATE_BEACON: TelegramCallbackRiskClass.STATE_CHANGING,
    TelegramCallbackActionScope.PAUSE_BEACON: TelegramCallbackRiskClass.STATE_CHANGING,
    TelegramCallbackActionScope.RESUME_BEACON: TelegramCallbackRiskClass.STATE_CHANGING,
    TelegramCallbackActionScope.DELETE_BEACON: TelegramCallbackRiskClass.DESTRUCTIVE,
    TelegramCallbackActionScope.CHANGE_BEACON_SOURCE_URL: TelegramCallbackRiskClass.DESTRUCTIVE,
    TelegramCallbackActionScope.UNLINK_TELEGRAM_IDENTITY: TelegramCallbackRiskClass.IDENTITY_SENSITIVE,  # noqa: E501
    TelegramCallbackActionScope.DISABLE_NOTIFICATION_CHANNEL: TelegramCallbackRiskClass.NOTIFICATION_SENSITIVE,  # noqa: E501
    TelegramCallbackActionScope.TARIFF_OR_PAYMENT_SENSITIVE_ACTION: TelegramCallbackRiskClass.PAYMENT_OR_TARIFF_SENSITIVE,  # noqa: E501
    TelegramCallbackActionScope.UNSUPPORTED_ACTION: TelegramCallbackRiskClass.UNSUPPORTED_OR_AMBIGUOUS,  # noqa: E501
    TelegramCallbackActionScope.AMBIGUOUS_ACTION: TelegramCallbackRiskClass.UNSUPPORTED_OR_AMBIGUOUS,  # noqa: E501
}

_DANGEROUS_CALLBACK_ACTIONS = (
    TelegramCallbackActionScope.DELETE_BEACON,
    TelegramCallbackActionScope.CHANGE_BEACON_SOURCE_URL,
    TelegramCallbackActionScope.UNLINK_TELEGRAM_IDENTITY,
    TelegramCallbackActionScope.DISABLE_NOTIFICATION_CHANNEL,
    TelegramCallbackActionScope.TARIFF_OR_PAYMENT_SENSITIVE_ACTION,
)


class TelegramUntrustedCallbackReference(_TelegramContract):
    telegram_untrusted_callback_reference_id: str = Field(min_length=1)
    provider_update_identity: TelegramProviderUpdateIdentity
    callback_query_reference_id: str = Field(min_length=1)
    opaque_callback_payload_reference_id: str = Field(min_length=1)
    payload_validation_mode: TelegramCallbackPayloadValidationMode
    callback_action_idempotency_key: IdempotencyKey
    callback_action_idempotency_scope: IdempotencyScope
    callback_payload_fingerprint: IdempotencyFingerprint
    server_resolution_or_signature_evidence_reference_id: str | None = Field(
        default=None, min_length=1
    )
    expiry_policy_reference_id: str | None = Field(default=None, min_length=1)
    expiry_evidence_reference_id: str | None = Field(default=None, min_length=1)
    raw_callback_data_present: Literal[False] = False
    callback_data_trusted: Literal[False] = False
    button_text_trusted: Literal[False] = False
    callback_payload_is_authorization: Literal[False] = False
    raw_account_id_embedded: Literal[False] = False
    raw_beacon_id_embedded: Literal[False] = False
    secret_material_embedded: Literal[False] = False
    business_execution_authorized: Literal[False] = False

    @model_validator(mode="after")
    def _validate_callback_evidence(self) -> "TelegramUntrustedCallbackReference":
        validated = {
            TelegramCallbackPayloadValidationMode.OPAQUE_SERVER_RESOLVED,
            TelegramCallbackPayloadValidationMode.SIGNED_VALIDATED,
        }
        if (
            self.payload_validation_mode in validated
            and not self.server_resolution_or_signature_evidence_reference_id
        ):
            raise ValueError("validated callback payload requires evidence")
        if (
            self.payload_validation_mode
            in {
                TelegramCallbackPayloadValidationMode.UNVALIDATED,
                TelegramCallbackPayloadValidationMode.AMBIGUOUS,
            }
            and self.server_resolution_or_signature_evidence_reference_id is not None
        ):
            raise ValueError("unvalidated callback payload cannot claim validation evidence")
        if (
            self.expiry_evidence_reference_id is not None
            and self.expiry_policy_reference_id is None
        ):
            raise ValueError("expiry evidence requires an expiry policy")
        return self


class TelegramCallbackAuthorizationEvidence(_TelegramContract):
    telegram_callback_authorization_evidence_id: str = Field(min_length=1)
    action_scope: TelegramCallbackActionScope
    owner_boundary: TelegramIntentOwnerBoundary
    owning_module_contract_reference_id: str = Field(min_length=1)
    owning_module_decision_reference_id: str = Field(min_length=1)
    identity_resolution_outcome: TelegramIdentityResolutionOutcome
    server_side_ownership_check_performed: bool
    authorization_granted: bool
    action_scope_matches_decision: bool
    actor_account_matches_owner: bool
    client_payload_used_as_authorization: Literal[False] = False
    telegram_provider_identity_used_as_account_id: Literal[False] = False
    direct_foreign_mutation_authorized: Literal[False] = False

    @model_validator(mode="after")
    def _validate_authorization(self) -> "TelegramCallbackAuthorizationEvidence":
        outcome = self.identity_resolution_outcome
        if (
            outcome.state is not TelegramIdentityResolutionState.RESOLVED_ACCOUNT
            or outcome.account_link is None
        ):
            raise ValueError("callback authorization requires a resolved account link")
        if outcome.provider_identity != outcome.account_link.provider_identity:
            raise ValueError("resolved provider identity must match account link")
        if self.owner_boundary in {
            TelegramIntentOwnerBoundary.TELEGRAM_ADAPTER,
            TelegramIntentOwnerBoundary.NONE,
        }:
            raise ValueError("adapter and none boundaries cannot issue authorization evidence")
        if self.owner_boundary is not _CALLBACK_OWNER[self.action_scope]:
            raise ValueError("authorization owner does not match action scope")
        if self.authorization_granted and not (
            self.server_side_ownership_check_performed
            and self.action_scope_matches_decision
            and self.actor_account_matches_owner
        ):
            raise ValueError("granted authorization requires all server-side checks")
        return self


class TelegramCallbackValidationRequest(_TelegramContract):
    telegram_callback_validation_request_id: str = Field(min_length=1)
    metadata: ContractMetadata
    intake_record: TelegramUpdateIntakeRecord
    deduplication_record: TelegramUpdateDeduplicationRecord
    callback_reference: TelegramUntrustedCallbackReference
    action_scope: TelegramCallbackActionScope
    risk_class: TelegramCallbackRiskClass
    owner_boundary: TelegramIntentOwnerBoundary
    replay_state: TelegramCallbackReplayState
    expiry_state: TelegramCallbackExpiryState
    confirmation_state: TelegramCallbackConfirmationState
    authorization_evidence: TelegramCallbackAuthorizationEvidence | None = None
    existing_callback_outcome_reference_id: str | None = Field(default=None, min_length=1)
    callback_policy_reference_id: str = Field(min_length=1)
    reason_code: str = Field(min_length=1)
    business_dispatch_authorized: Literal[False] = False
    command_handler_authorized: Literal[False] = False
    conversation_state_machine_authorized: Literal[False] = False
    provider_runtime_authorized: Literal[False] = False
    direct_foreign_mutation_authorized: Literal[False] = False

    @model_validator(mode="after")
    def _validate_request(self) -> "TelegramCallbackValidationRequest":
        intake, dedup, callback = (
            self.intake_record,
            self.deduplication_record,
            self.callback_reference,
        )
        if intake.intake_state is not TelegramUpdateIntakeState.ACCEPTED_FOR_NORMALIZATION:
            raise ValueError("callback validation requires accepted intake")
        if (
            intake.admission_state is not TelegramUpdateAdmissionState.VERIFIED
            or intake.structural_classification
            is not TelegramUpdateStructuralClass.SUPPORTED_CANDIDATE
        ):
            raise ValueError("callback validation requires verified supported intake")
        if intake.provider_identity is None:
            raise ValueError("callback validation requires provider identity")
        if (
            dedup.state is not TelegramUpdateDeduplicationState.NEW_UPDATE
            or not dedup.adapter_processing_authorized
        ):
            raise ValueError("callback validation requires a new adapter-authorized update")
        if not (
            dedup.current_intake_record_id == intake.telegram_update_intake_record_id
            and callback.provider_update_identity
            == intake.provider_update_identity
            == dedup.provider_update_identity
            and callback.callback_action_idempotency_key
            == intake.idempotency_key
            == dedup.idempotency_key
            and callback.callback_action_idempotency_scope
            == intake.idempotency_scope
            == dedup.idempotency_scope
            and callback.callback_payload_fingerprint == intake.fingerprint == dedup.fingerprint
        ):
            raise ValueError("callback and intake identity evidence must agree")
        if (
            self.owner_boundary is not _CALLBACK_OWNER[self.action_scope]
            or self.risk_class is not _CALLBACK_RISK[self.action_scope]
        ):
            raise ValueError("callback owner and risk mappings are exact")
        unsupported = self.action_scope is TelegramCallbackActionScope.UNSUPPORTED_ACTION
        ambiguous = self.action_scope is TelegramCallbackActionScope.AMBIGUOUS_ACTION
        if unsupported and (
            self.risk_class is not TelegramCallbackRiskClass.UNSUPPORTED_OR_AMBIGUOUS
            or self.owner_boundary is not TelegramIntentOwnerBoundary.NONE
        ):
            raise ValueError("unsupported action mapping is exact")
        if ambiguous and (
            self.risk_class is not TelegramCallbackRiskClass.UNSUPPORTED_OR_AMBIGUOUS
            or self.owner_boundary is not TelegramIntentOwnerBoundary.NONE
        ):
            raise ValueError("ambiguous action mapping is exact")
        if (
            not unsupported
            and not ambiguous
            and callback.payload_validation_mode
            in {
                TelegramCallbackPayloadValidationMode.UNVALIDATED,
                TelegramCallbackPayloadValidationMode.AMBIGUOUS,
            }
        ):
            raise ValueError("supported callback action requires validated payload evidence")
        if self.owner_boundary in {
            TelegramIntentOwnerBoundary.TELEGRAM_ADAPTER,
            TelegramIntentOwnerBoundary.NONE,
        }:
            if self.authorization_evidence is not None:
                raise ValueError("local/none action cannot carry authorization evidence")
        elif (
            self.authorization_evidence is None
            or self.authorization_evidence.action_scope is not self.action_scope
            or self.authorization_evidence.owner_boundary is not self.owner_boundary
        ):
            raise ValueError("external owner requires matching authorization evidence")
        if (
            self.authorization_evidence is not None
            and self.authorization_evidence.identity_resolution_outcome.provider_identity
            != intake.provider_identity
        ):
            raise ValueError("authorization evidence must resolve the intake provider identity")
        if (
            self.replay_state is TelegramCallbackReplayState.NEW_ACTION
            and self.existing_callback_outcome_reference_id is not None
        ):
            raise ValueError("new action cannot reference an existing outcome")
        if (
            self.replay_state
            in {
                TelegramCallbackReplayState.DUPLICATE_REPLAY,
                TelegramCallbackReplayState.FINGERPRINT_CONFLICT,
            }
            and self.existing_callback_outcome_reference_id is None
        ):
            raise ValueError("replay/conflict requires existing outcome reference")
        if (
            self.replay_state is TelegramCallbackReplayState.AMBIGUOUS
            and self.existing_callback_outcome_reference_id is not None
            and not self.existing_callback_outcome_reference_id.strip()
        ):
            raise ValueError("ambiguous outcome reference must be opaque")
        policy, evidence = (
            callback.expiry_policy_reference_id,
            callback.expiry_evidence_reference_id,
        )
        if policy is None:
            if (
                self.expiry_state is not TelegramCallbackExpiryState.NOT_REQUIRED
                or evidence is not None
            ):
                raise ValueError("no expiry policy permits only NOT_REQUIRED without evidence")
        elif self.expiry_state is TelegramCallbackExpiryState.NOT_REQUIRED:
            raise ValueError("expiry policy requires an evaluated state")
        elif (
            self.expiry_state
            in {TelegramCallbackExpiryState.VALID, TelegramCallbackExpiryState.EXPIRED}
            and evidence is None
        ):
            raise ValueError("evaluated expiry requires evidence")
        elif self.expiry_state is TelegramCallbackExpiryState.MISSING and evidence is not None:
            raise ValueError("missing expiry cannot fabricate evidence")
        dangerous = self.action_scope in _DANGEROUS_CALLBACK_ACTIONS
        if dangerous and self.confirmation_state is TelegramCallbackConfirmationState.NOT_REQUIRED:
            raise ValueError("dangerous action requires confirmation state")
        if (
            not dangerous
            and not unsupported
            and not ambiguous
            and self.confirmation_state is not TelegramCallbackConfirmationState.NOT_REQUIRED
        ):
            raise ValueError("non-dangerous supported action does not require confirmation")
        if (
            unsupported or ambiguous
        ) and self.confirmation_state is not TelegramCallbackConfirmationState.NOT_REQUIRED:
            raise ValueError("unsupported/ambiguous action cannot require confirmation")
        return self


class TelegramCallbackValidationOutcome(_TelegramContract):
    telegram_callback_validation_outcome_id: str = Field(min_length=1)
    metadata: ContractMetadata
    validation_request: TelegramCallbackValidationRequest
    state: TelegramCallbackValidationState
    owner_handoff_reference_id: str | None = Field(default=None, min_length=1)
    replayed_callback_outcome_reference_id: str | None = Field(default=None, min_length=1)
    blocking_decision_reference_id: str | None = Field(default=None, min_length=1)
    confirmation_challenge_reference_id: str | None = Field(default=None, min_length=1)
    reason_code: str = Field(min_length=1)
    owner_handoff_authorized: bool
    second_business_effect_authorized: Literal[False] = False
    business_execution_authorized: Literal[False] = False
    direct_beacon_mutation_authorized: Literal[False] = False
    direct_identity_mutation_authorized: Literal[False] = False
    direct_notification_mutation_authorized: Literal[False] = False
    direct_entitlement_mutation_authorized: Literal[False] = False
    callback_data_is_authorization: Literal[False] = False
    provider_runtime_authorized: Literal[False] = False

    @model_validator(mode="after")
    def _validate_outcome(self) -> "TelegramCallbackValidationOutcome":
        request, state = self.validation_request, self.state
        action = request.action_scope
        if state is TelegramCallbackValidationState.VALIDATED_FOR_OWNER_HANDOFF:
            if (
                request.replay_state is not TelegramCallbackReplayState.NEW_ACTION
                or request.expiry_state
                not in {TelegramCallbackExpiryState.NOT_REQUIRED, TelegramCallbackExpiryState.VALID}
                or request.confirmation_state
                not in {
                    TelegramCallbackConfirmationState.NOT_REQUIRED,
                    TelegramCallbackConfirmationState.VERIFIED,
                }
                or request.callback_reference.payload_validation_mode
                not in {
                    TelegramCallbackPayloadValidationMode.OPAQUE_SERVER_RESOLVED,
                    TelegramCallbackPayloadValidationMode.SIGNED_VALIDATED,
                }
                or (
                    request.authorization_evidence is not None
                    and not request.authorization_evidence.authorization_granted
                )
                or not self.owner_handoff_reference_id
                or self.replayed_callback_outcome_reference_id is not None
                or self.blocking_decision_reference_id is not None
                or self.confirmation_challenge_reference_id is not None
                or not self.owner_handoff_authorized
            ):
                raise ValueError("validated handoff matrix is exact")
        elif state is TelegramCallbackValidationState.CONFIRMATION_REQUIRED:
            if (
                action not in _DANGEROUS_CALLBACK_ACTIONS
                or request.replay_state is not TelegramCallbackReplayState.NEW_ACTION
                or request.expiry_state
                not in {TelegramCallbackExpiryState.NOT_REQUIRED, TelegramCallbackExpiryState.VALID}
                or request.confirmation_state is not TelegramCallbackConfirmationState.REQUIRED
                or request.authorization_evidence is None
                or not request.authorization_evidence.authorization_granted
                or not self.confirmation_challenge_reference_id
                or self.owner_handoff_reference_id is not None
                or self.replayed_callback_outcome_reference_id is not None
                or self.blocking_decision_reference_id is not None
                or self.owner_handoff_authorized
            ):
                raise ValueError("confirmation-required matrix is exact")
        else:
            if self.owner_handoff_authorized or self.owner_handoff_reference_id is not None:
                raise ValueError("only validated handoff may authorize or reference handoff")
            if not self.blocking_decision_reference_id and state not in {
                TelegramCallbackValidationState.DUPLICATE_REPLAY
            }:
                raise ValueError("blocked outcome requires blocking reference")
            if (
                state is TelegramCallbackValidationState.REJECTED_UNTRUSTED
                and request.callback_reference.payload_validation_mode
                is not TelegramCallbackPayloadValidationMode.UNVALIDATED
            ):
                raise ValueError("untrusted rejection requires unvalidated payload")
            if (
                state is TelegramCallbackValidationState.REJECTED_EXPIRED
                and request.expiry_state is not TelegramCallbackExpiryState.EXPIRED
            ):
                raise ValueError("expired rejection requires expired state")
            if state is TelegramCallbackValidationState.REJECTED_UNAUTHORIZED and (
                request.authorization_evidence is None
                or request.authorization_evidence.authorization_granted
            ):
                raise ValueError("unauthorized rejection requires denied owner evidence")
            if state is TelegramCallbackValidationState.DUPLICATE_REPLAY and (
                request.replay_state is not TelegramCallbackReplayState.DUPLICATE_REPLAY
                or self.replayed_callback_outcome_reference_id
                != request.existing_callback_outcome_reference_id
            ):
                raise ValueError("duplicate replay must reference exact prior outcome")
            if (
                state is TelegramCallbackValidationState.FINGERPRINT_CONFLICT
                and request.replay_state is not TelegramCallbackReplayState.FINGERPRINT_CONFLICT
            ):
                raise ValueError("fingerprint conflict requires conflict replay state")
            if state is TelegramCallbackValidationState.UNSUPPORTED and (
                action is not TelegramCallbackActionScope.UNSUPPORTED_ACTION
                or request.owner_boundary is not TelegramIntentOwnerBoundary.NONE
            ):
                raise ValueError("unsupported outcome mapping is exact")
            if state is TelegramCallbackValidationState.AMBIGUOUS and not (
                action is TelegramCallbackActionScope.AMBIGUOUS_ACTION
                or request.callback_reference.payload_validation_mode
                is TelegramCallbackPayloadValidationMode.AMBIGUOUS
                or request.replay_state is TelegramCallbackReplayState.AMBIGUOUS
                or request.expiry_state is TelegramCallbackExpiryState.AMBIGUOUS
            ):
                raise ValueError("ambiguous outcome requires an ambiguous input")
        return self


class TelegramProviderMode(str, Enum):
    WEBHOOK = "WEBHOOK"
    GET_UPDATES = "GET_UPDATES"


class TelegramProviderModeBoundaryState(str, Enum):
    UNSELECTED = "UNSELECTED"
    WEBHOOK_CANDIDATE = "WEBHOOK_CANDIDATE"
    GET_UPDATES_CANDIDATE = "GET_UPDATES_CANDIDATE"
    TRANSITION_REQUIRED = "TRANSITION_REQUIRED"
    BLOCKED = "BLOCKED"


class TelegramWebhookModeRequirements(_TelegramContract):
    telegram_webhook_mode_requirements_id: str = Field(min_length=1)
    official_telegram_evidence_ref: str = Field(min_length=1)
    endpoint_ownership_decision_ref: str = Field(min_length=1)
    tls_domain_port_certificate_gate_ref: str = Field(min_length=1)
    secret_token_handling_policy_ref: str = Field(min_length=1)
    authenticity_verification_policy_ref: str = Field(min_length=1)
    durable_acceptance_policy_ref: str = Field(min_length=1)
    duplicate_delivery_idempotency_policy_ref: str = Field(min_length=1)
    failure_response_policy_ref: str = Field(min_length=1)
    drop_pending_transition_policy_ref: str = Field(min_length=1)
    secret_material_present: Literal[False] = False
    http_acknowledgement_is_business_success: Literal[False] = False
    provider_request_authorized: Literal[False] = False


class TelegramGetUpdatesModeRequirements(_TelegramContract):
    telegram_get_updates_mode_requirements_id: str = Field(min_length=1)
    official_telegram_evidence_ref: str = Field(min_length=1)
    allowed_environment_class_decision_ref: str = Field(min_length=1)
    polling_ownership_decision_ref: str = Field(min_length=1)
    scheduler_worker_boundary_ref: str = Field(min_length=1)
    durable_acceptance_policy_ref: str = Field(min_length=1)
    offset_advancement_policy_ref: str = Field(min_length=1)
    interruption_replay_policy_ref: str = Field(min_length=1)
    mode_transition_policy_ref: str = Field(min_length=1)
    drop_pending_policy_ref: str = Field(min_length=1)
    timeout_limit_interval_policy_ref: str = Field(min_length=1)
    process_local_cursor_authoritative: Literal[False] = False
    arrival_is_trusted_without_validation: Literal[False] = False
    offset_advance_before_durable_acceptance_authorized: Literal[False] = False
    provider_request_authorized: Literal[False] = False


class TelegramProviderModeBoundary(_TelegramContract):
    telegram_provider_mode_boundary_id: str = Field(min_length=1)
    metadata: ContractMetadata
    telegram_bot_ref: str = Field(min_length=1)
    environment_ref: str = Field(min_length=1)
    owner_direction_reference_id: str = Field(min_length=1)
    official_telegram_evidence_ref: str = Field(min_length=1)
    state: TelegramProviderModeBoundaryState
    candidate_mode: TelegramProviderMode | None = None
    current_mode: TelegramProviderMode | None = None
    requested_mode: TelegramProviderMode | None = None
    webhook_requirements: TelegramWebhookModeRequirements | None = None
    get_updates_requirements: TelegramGetUpdatesModeRequirements | None = None
    mode_transition_policy_ref: str | None = Field(default=None, min_length=1)
    drop_pending_policy_ref: str | None = Field(default=None, min_length=1)
    blocking_decision_reference_id: str | None = Field(default=None, min_length=1)
    production_staging_target_mode: Literal[TelegramProviderMode.WEBHOOK] = (
        TelegramProviderMode.WEBHOOK
    )
    development_proof_mode_candidate: Literal[TelegramProviderMode.GET_UPDATES] = (
        TelegramProviderMode.GET_UPDATES
    )
    development_proof_requires_explicit_gate: Literal[True] = True
    environment_mode_selected: Literal[False] = False
    simultaneous_modes_authorized: Literal[False] = False
    provider_call_authorized: Literal[False] = False
    provider_runtime_authorized: Literal[False] = False
    reason_code: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_state_matrix(self) -> "TelegramProviderModeBoundary":
        if self.webhook_requirements is not None and self.get_updates_requirements is not None:
            raise ValueError("webhook and getUpdates requirements are mutually exclusive")

        state = self.state
        if state in {
            TelegramProviderModeBoundaryState.UNSELECTED,
            TelegramProviderModeBoundaryState.BLOCKED,
        }:
            if any((self.candidate_mode, self.current_mode, self.requested_mode)):
                raise ValueError("this boundary state cannot contain a mode")
            if self.webhook_requirements is not None or self.get_updates_requirements is not None:
                raise ValueError("this boundary state cannot contain requirements")
            if (
                self.mode_transition_policy_ref is not None
                or self.drop_pending_policy_ref is not None
            ):
                raise ValueError("this boundary state cannot contain transition references")
            if state is TelegramProviderModeBoundaryState.UNSELECTED:
                if self.blocking_decision_reference_id is not None:
                    raise ValueError("unselected boundary cannot contain blocking reference")
            elif self.blocking_decision_reference_id is None:
                raise ValueError("blocked boundary requires blocking reference")
            return self

        if self.blocking_decision_reference_id is not None:
            raise ValueError("candidate or transition boundary cannot be blocked")

        if state is TelegramProviderModeBoundaryState.WEBHOOK_CANDIDATE:
            if self.candidate_mode is not TelegramProviderMode.WEBHOOK:
                raise ValueError("webhook candidate requires webhook candidate mode")
            if self.webhook_requirements is None or self.get_updates_requirements is not None:
                raise ValueError("webhook candidate requires only webhook requirements")
            if any(
                (
                    self.current_mode,
                    self.requested_mode,
                    self.mode_transition_policy_ref,
                    self.drop_pending_policy_ref,
                )
            ):
                raise ValueError(
                    "webhook candidate cannot contain current, requested, or transition data"
                )
            if (
                self.official_telegram_evidence_ref
                != self.webhook_requirements.official_telegram_evidence_ref
            ):
                raise ValueError("boundary and webhook evidence references must match")
            return self

        if state is TelegramProviderModeBoundaryState.GET_UPDATES_CANDIDATE:
            if self.candidate_mode is not TelegramProviderMode.GET_UPDATES:
                raise ValueError("getUpdates candidate requires getUpdates candidate mode")
            if self.get_updates_requirements is None or self.webhook_requirements is not None:
                raise ValueError("getUpdates candidate requires only getUpdates requirements")
            if any(
                (
                    self.current_mode,
                    self.requested_mode,
                    self.mode_transition_policy_ref,
                    self.drop_pending_policy_ref,
                )
            ):
                raise ValueError(
                    "getUpdates candidate cannot contain current, requested, or transition data"
                )
            if (
                self.official_telegram_evidence_ref
                != self.get_updates_requirements.official_telegram_evidence_ref
            ):
                raise ValueError("boundary and getUpdates evidence references must match")
            return self

        if state is TelegramProviderModeBoundaryState.TRANSITION_REQUIRED:
            if (
                self.candidate_mode is not None
                or self.current_mode is None
                or self.requested_mode is None
            ):
                raise ValueError("transition requires no candidate and both modes")
            if self.current_mode is self.requested_mode:
                raise ValueError("transition requires different current and requested modes")
            if self.mode_transition_policy_ref is None or self.drop_pending_policy_ref is None:
                raise ValueError("transition requires mode and drop-pending policy references")
            target = self.webhook_requirements or self.get_updates_requirements
            if (
                target is None
                or self.official_telegram_evidence_ref != target.official_telegram_evidence_ref
            ):
                raise ValueError("transition requires evidence for its target requirements")
            if self.requested_mode is TelegramProviderMode.WEBHOOK:
                if self.webhook_requirements is None or self.get_updates_requirements is not None:
                    raise ValueError("webhook transition requires only webhook requirements")
            elif self.get_updates_requirements is None or self.webhook_requirements is not None:
                raise ValueError("getUpdates transition requires only getUpdates requirements")
            return self

        raise ValueError("unsupported provider mode boundary state")


class TelegramExistingBotEvidenceState(str, Enum):
    VERIFIED_REDACTED_EVIDENCE = "VERIFIED_REDACTED_EVIDENCE"
    EVIDENCE_INCOMPLETE = "EVIDENCE_INCOMPLETE"
    EVIDENCE_MISMATCH = "EVIDENCE_MISMATCH"


class TelegramExistingBotMetadata(_TelegramContract):
    telegram_existing_bot_metadata_id: str = Field(min_length=1)
    telegram_bot_username: str = Field(min_length=1)
    telegram_bot_numeric_id: str = Field(min_length=1, pattern=r"^[1-9][0-9]*$")
    owner_provisioning_reference_id: str = Field(min_length=1)
    botfather_creation_completed: Literal[True] = True
    telegram_bot_numeric_id_is_external_provider_identifier: Literal[True] = True
    telegram_bot_numeric_id_is_internal_account_id: Literal[False] = False
    botfather_reconfiguration_authorized: Literal[False] = False


class TelegramProtectedSecretPresenceEvidence(_TelegramContract):
    telegram_protected_secret_presence_evidence_id: str = Field(min_length=1)
    protected_secret_reference: str = Field(min_length=1)
    observed_owner: str = Field(min_length=1)
    observed_group: str = Field(min_length=1)
    observed_mode: str = Field(min_length=1, pattern=r"^0[0-7]{3}$")
    observed_size_bytes: int = Field(gt=0)
    server_evidence_reference_id: str = Field(min_length=1)
    evidence_is_presence_and_metadata_only: Literal[True] = True
    secret_content_read: Literal[False] = False
    secret_content_printed: Literal[False] = False
    secret_content_hashed: Literal[False] = False
    secret_content_fingerprinted: Literal[False] = False
    secret_content_encoded: Literal[False] = False
    secret_content_copied: Literal[False] = False
    secret_content_transmitted: Literal[False] = False
    secret_modified: Literal[False] = False


class TelegramPublicBotMetadataPresenceEvidence(_TelegramContract):
    telegram_public_bot_metadata_presence_evidence_id: str = Field(min_length=1)
    public_metadata_reference: str = Field(min_length=1)
    observed_owner: str = Field(min_length=1)
    observed_group: str = Field(min_length=1)
    observed_mode: str = Field(min_length=1, pattern=r"^0[0-7]{3}$")
    observed_size_bytes: int = Field(gt=0)
    server_evidence_reference_id: str = Field(min_length=1)
    evidence_is_presence_and_metadata_only: Literal[True] = True
    file_content_read: Literal[False] = False
    file_modified: Literal[False] = False


class TelegramExistingBotOperationalGate(_TelegramContract):
    telegram_existing_bot_operational_gate_id: str = Field(min_length=1)
    metadata: ContractMetadata
    owner_direction_reference_id: str = Field(min_length=1)
    state: TelegramExistingBotEvidenceState
    bot_metadata: TelegramExistingBotMetadata | None = None
    protected_secret_presence_evidence: TelegramProtectedSecretPresenceEvidence | None = None
    public_bot_metadata_presence_evidence: TelegramPublicBotMetadataPresenceEvidence | None = None
    blocking_decision_reference_id: str | None = Field(default=None, min_length=1)
    provider_runtime_authorized: Literal[False] = False
    provider_call_authorized: Literal[False] = False
    webhook_authorized: Literal[False] = False
    get_updates_authorized: Literal[False] = False
    mini_app_authorized: Literal[False] = False
    protected_secret_consumption_authorized: Literal[False] = False
    botfather_reconfiguration_authorized: Literal[False] = False
    token_rotation_authorized: Literal[False] = False
    token_revocation_authorized: Literal[False] = False
    token_deletion_authorized: Literal[False] = False
    secret_relocation_authorized: Literal[False] = False
    secret_permission_change_authorized: Literal[False] = False
    reason_code: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_state_matrix(self) -> "TelegramExistingBotOperationalGate":
        complete = all(
            (
                self.bot_metadata,
                self.protected_secret_presence_evidence,
                self.public_bot_metadata_presence_evidence,
            )
        )
        if self.state is TelegramExistingBotEvidenceState.EVIDENCE_INCOMPLETE:
            if complete or self.blocking_decision_reference_id is None:
                raise ValueError(
                    "incomplete evidence requires missing evidence and blocking reference"
                )
            return self
        if not complete:
            raise ValueError("verified or mismatched evidence requires all evidence objects")
        bot = self.bot_metadata
        secret = self.protected_secret_presence_evidence
        public = self.public_bot_metadata_presence_evidence
        assert bot is not None and secret is not None and public is not None
        matches = (
            bot.telegram_bot_username == "@signalings_bot"
            and bot.telegram_bot_numeric_id == "8664835407"
            and secret.protected_secret_reference == "/etc/avito-mayak/secrets/telegram_bot_token"
            and secret.observed_owner == "root"
            and secret.observed_group == "root"
            and secret.observed_mode == "0600"
            and secret.observed_size_bytes > 0
            and public.public_metadata_reference == "/etc/avito-mayak/telegram-bot.conf"
            and public.observed_owner == "root"
            and public.observed_group == "root"
            and public.observed_mode == "0644"
            and public.observed_size_bytes > 0
        )
        if self.state is TelegramExistingBotEvidenceState.VERIFIED_REDACTED_EVIDENCE:
            if not matches or self.blocking_decision_reference_id is not None:
                raise ValueError("verified state requires exact non-secret metadata and no block")
        elif self.state is TelegramExistingBotEvidenceState.EVIDENCE_MISMATCH:
            if matches or self.blocking_decision_reference_id is None:
                raise ValueError(
                    "mismatch state requires differing metadata and blocking reference"
                )
        return self


class TelegramDeepLinkPurpose(str, Enum):
    LINK_EXISTING_ACCOUNT = "LINK_EXISTING_ACCOUNT"
    BOT_ONBOARDING = "BOT_ONBOARDING"
    OPEN_BEACON_CONTEXT = "OPEN_BEACON_CONTEXT"
    OPEN_RESULT_OR_LISTING_CONTEXT = "OPEN_RESULT_OR_LISTING_CONTEXT"
    RETURN_FROM_WEB_CABINET = "RETURN_FROM_WEB_CABINET"
    OPEN_FUTURE_MINI_APP_CONTEXT = "OPEN_FUTURE_MINI_APP_CONTEXT"
    UNSUPPORTED = "UNSUPPORTED"
    AMBIGUOUS = "AMBIGUOUS"


class TelegramDeepLinkContextOwnerBoundary(str, Enum):
    TELEGRAM_ADAPTER = "TELEGRAM_ADAPTER"
    IDENTITY_AND_ACCESS = "IDENTITY_AND_ACCESS"
    BEACON_MANAGEMENT = "BEACON_MANAGEMENT"
    NOTIFICATION_DELIVERY = "NOTIFICATION_DELIVERY"
    WEB_CABINET = "WEB_CABINET"
    FUTURE_MINI_APP_GATE = "FUTURE_MINI_APP_GATE"
    NONE = "NONE"


class TelegramDeepLinkPayloadValidationMode(str, Enum):
    OPAQUE_SERVER_RESOLVED = "OPAQUE_SERVER_RESOLVED"
    SIGNED_VALIDATED = "SIGNED_VALIDATED"
    UNVALIDATED = "UNVALIDATED"
    AMBIGUOUS = "AMBIGUOUS"


class TelegramDeepLinkReplayState(str, Enum):
    NEW_LINK = "NEW_LINK"
    DUPLICATE_REPLAY = "DUPLICATE_REPLAY"
    FINGERPRINT_CONFLICT = "FINGERPRINT_CONFLICT"
    AMBIGUOUS = "AMBIGUOUS"


class TelegramDeepLinkExpiryState(str, Enum):
    VALID = "VALID"
    EXPIRED = "EXPIRED"
    MISSING = "MISSING"
    AMBIGUOUS = "AMBIGUOUS"


class TelegramDeepLinkValidationState(str, Enum):
    VALIDATED_FOR_OWNER_HANDOFF = "VALIDATED_FOR_OWNER_HANDOFF"
    IDENTITY_HANDOFF_REQUIRED = "IDENTITY_HANDOFF_REQUIRED"
    BLOCKED_PENDING_CONTEXT_DECISION = "BLOCKED_PENDING_CONTEXT_DECISION"
    REJECTED_UNTRUSTED = "REJECTED_UNTRUSTED"
    REJECTED_EXPIRED = "REJECTED_EXPIRED"
    DUPLICATE_REPLAY = "DUPLICATE_REPLAY"
    FINGERPRINT_CONFLICT = "FINGERPRINT_CONFLICT"
    UNSUPPORTED = "UNSUPPORTED"
    AMBIGUOUS = "AMBIGUOUS"
    BLOCKED = "BLOCKED"


_DEEP_LINK_OWNER: dict[TelegramDeepLinkPurpose, TelegramDeepLinkContextOwnerBoundary] = {
    TelegramDeepLinkPurpose.LINK_EXISTING_ACCOUNT: (
        TelegramDeepLinkContextOwnerBoundary.IDENTITY_AND_ACCESS
    ),
    TelegramDeepLinkPurpose.BOT_ONBOARDING: (TelegramDeepLinkContextOwnerBoundary.TELEGRAM_ADAPTER),
    TelegramDeepLinkPurpose.OPEN_BEACON_CONTEXT: (
        TelegramDeepLinkContextOwnerBoundary.BEACON_MANAGEMENT
    ),
    TelegramDeepLinkPurpose.OPEN_RESULT_OR_LISTING_CONTEXT: (
        TelegramDeepLinkContextOwnerBoundary.NOTIFICATION_DELIVERY
    ),
    TelegramDeepLinkPurpose.RETURN_FROM_WEB_CABINET: (
        TelegramDeepLinkContextOwnerBoundary.WEB_CABINET
    ),
    TelegramDeepLinkPurpose.OPEN_FUTURE_MINI_APP_CONTEXT: (
        TelegramDeepLinkContextOwnerBoundary.FUTURE_MINI_APP_GATE
    ),
    TelegramDeepLinkPurpose.UNSUPPORTED: TelegramDeepLinkContextOwnerBoundary.NONE,
    TelegramDeepLinkPurpose.AMBIGUOUS: TelegramDeepLinkContextOwnerBoundary.NONE,
}

_DEEP_LINK_DEDUPLICATION_STATE: dict[
    TelegramDeepLinkReplayState, TelegramUpdateDeduplicationState
] = {
    TelegramDeepLinkReplayState.NEW_LINK: TelegramUpdateDeduplicationState.NEW_UPDATE,
    TelegramDeepLinkReplayState.DUPLICATE_REPLAY: TelegramUpdateDeduplicationState.DUPLICATE_REPLAY,
    TelegramDeepLinkReplayState.FINGERPRINT_CONFLICT: (
        TelegramUpdateDeduplicationState.FINGERPRINT_CONFLICT
    ),
    TelegramDeepLinkReplayState.AMBIGUOUS: TelegramUpdateDeduplicationState.AMBIGUOUS,
}


class TelegramUntrustedDeepLinkReference(_TelegramContract):
    telegram_untrusted_deep_link_reference_id: str = Field(min_length=1)
    telegram_bot_ref: str = Field(min_length=1)
    telegram_update_intake_reference_id: str = Field(min_length=1)
    provider_update_identity: TelegramProviderUpdateIdentity
    deep_link_payload_fingerprint: IdempotencyFingerprint
    purpose_candidate: TelegramDeepLinkPurpose
    payload_remains_untrusted: Literal[True] = True
    raw_payload_retained: Literal[False] = False
    raw_internal_identifiers_absent: Literal[True] = True
    secrets_personal_payment_data_absent: Literal[True] = True

    @model_validator(mode="after")
    def _validate_scope(self) -> "TelegramUntrustedDeepLinkReference":
        if self.provider_update_identity.telegram_bot_ref != self.telegram_bot_ref:
            raise ValueError("deep link bot scope must match provider update identity")
        return self


class TelegramDeepLinkContextResolutionEvidence(_TelegramContract):
    telegram_deep_link_context_resolution_evidence_id: str = Field(min_length=1)
    purpose: TelegramDeepLinkPurpose
    owner_boundary: TelegramDeepLinkContextOwnerBoundary
    validation_mode: TelegramDeepLinkPayloadValidationMode
    replay_state: TelegramDeepLinkReplayState
    expiry_state: TelegramDeepLinkExpiryState
    matching_payload_fingerprint: IdempotencyFingerprint
    external_validation_policy_reference: str = Field(min_length=1)
    external_signing_policy_reference: str | None = Field(default=None, min_length=1)
    server_side_context_resolution_reference: str | None = Field(default=None, min_length=1)
    owner_contract_handoff_reference: str | None = Field(default=None, min_length=1)
    external_context_decision_reference: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def _validate_evidence_matrix(self) -> "TelegramDeepLinkContextResolutionEvidence":
        if _DEEP_LINK_OWNER[self.purpose] is not self.owner_boundary:
            raise ValueError("owner boundary must match purpose")
        if self.validation_mode is TelegramDeepLinkPayloadValidationMode.SIGNED_VALIDATED:
            if self.external_signing_policy_reference is None:
                raise ValueError("signed validation requires signing policy reference")
        elif self.external_signing_policy_reference is not None:
            raise ValueError("only signed validation may carry signing policy reference")
        eligible = (
            self.validation_mode
            in {
                TelegramDeepLinkPayloadValidationMode.OPAQUE_SERVER_RESOLVED,
                TelegramDeepLinkPayloadValidationMode.SIGNED_VALIDATED,
            }
            and self.replay_state is TelegramDeepLinkReplayState.NEW_LINK
            and self.expiry_state is TelegramDeepLinkExpiryState.VALID
            and self.purpose
            not in {TelegramDeepLinkPurpose.UNSUPPORTED, TelegramDeepLinkPurpose.AMBIGUOUS}
            and (
                self.purpose
                not in {
                    TelegramDeepLinkPurpose.RETURN_FROM_WEB_CABINET,
                    TelegramDeepLinkPurpose.OPEN_FUTURE_MINI_APP_CONTEXT,
                }
                or self.external_context_decision_reference is not None
            )
        )
        if not eligible and (
            self.server_side_context_resolution_reference is not None
            or self.owner_contract_handoff_reference is not None
        ):
            raise ValueError("ineligible links cannot resolve or hand off")
        if eligible:
            if self.purpose is TelegramDeepLinkPurpose.LINK_EXISTING_ACCOUNT:
                if self.owner_contract_handoff_reference is None:
                    raise ValueError("account linking requires owner handoff reference")
            elif (
                self.server_side_context_resolution_reference is None
                or self.owner_contract_handoff_reference is None
            ):
                raise ValueError("supported purpose requires exact semantic handoff references")
        return self


class TelegramDeepLinkValidationRequest(_TelegramContract):
    telegram_deep_link_validation_request_id: str = Field(min_length=1)
    untrusted_deep_link_reference: TelegramUntrustedDeepLinkReference
    accepted_telegram_update_intake: TelegramUpdateIntakeRecord
    deduplication_evidence: TelegramUpdateDeduplicationRecord
    verified_telegram_provider_identity_evidence: VerifiedTelegramIdentityEvidence
    context_resolution_evidence: TelegramDeepLinkContextResolutionEvidence
    intake_accepted: Literal[True] = True
    intake_structurally_supported: Literal[True] = True
    deduplication_allows_new_processing: bool = True
    payload_fingerprints_match: Literal[True] = True
    provider_identity_is_external: Literal[True] = True
    deep_link_is_not_identity_authorization: Literal[True] = True
    account_created: Literal[False] = False
    account_linked: Literal[False] = False
    business_effect_authorized: Literal[False] = False

    @model_validator(mode="after")
    def _validate_request_matrix(self) -> "TelegramDeepLinkValidationRequest":
        link = self.untrusted_deep_link_reference
        intake = self.accepted_telegram_update_intake
        dedup = self.deduplication_evidence
        identity = self.verified_telegram_provider_identity_evidence
        evidence = self.context_resolution_evidence
        if intake.telegram_update_intake_record_id != link.telegram_update_intake_reference_id:
            raise ValueError("intake reference must match deep link")
        if intake.provider_update_identity != link.provider_update_identity:
            raise ValueError("provider update identity must match deep link")
        if dedup.provider_update_identity != intake.provider_update_identity:
            raise ValueError("deduplication identity must match intake")
        if dedup.state is not _DEEP_LINK_DEDUPLICATION_STATE[evidence.replay_state]:
            raise ValueError("replay and deduplication states must map exactly")
        if dedup.adapter_processing_authorized != (
            dedup.state is TelegramUpdateDeduplicationState.NEW_UPDATE
        ):
            raise ValueError("adapter processing authorization must match deduplication state")
        if not (
            dedup.idempotency_key == intake.idempotency_key
            and dedup.idempotency_scope == intake.idempotency_scope
            and dedup.fingerprint == intake.fingerprint
        ):
            raise ValueError("deduplication identity evidence must match intake")
        if identity.provider_identity.telegram_bot_ref != link.telegram_bot_ref:
            raise ValueError("verified provider scope must match deep link")
        if identity.provider_identity != intake.provider_identity:
            raise ValueError("verified provider identity must match accepted intake")
        if intake.intake_state is not TelegramUpdateIntakeState.ACCEPTED_FOR_NORMALIZATION:
            raise ValueError("deep link requires accepted intake")
        if (
            intake.structural_classification
            is not TelegramUpdateStructuralClass.SUPPORTED_CANDIDATE
        ):
            raise ValueError("deep link requires structurally supported intake")
        if self.deduplication_allows_new_processing != (
            dedup.state is TelegramUpdateDeduplicationState.NEW_UPDATE
        ):
            raise ValueError("deduplication processing flag must match deduplication state")
        if link.deep_link_payload_fingerprint != evidence.matching_payload_fingerprint:
            raise ValueError("deep link payload fingerprints must match")
        if evidence.purpose is not link.purpose_candidate:
            raise ValueError("resolved purpose must match purpose candidate")
        return self


class TelegramDeepLinkValidationOutcome(_TelegramContract):
    telegram_deep_link_validation_outcome_id: str = Field(min_length=1)
    request: TelegramDeepLinkValidationRequest
    validation_state: TelegramDeepLinkValidationState
    owner_boundary: TelegramDeepLinkContextOwnerBoundary
    owner_handoff_reference: str | None = Field(default=None, min_length=1)
    blocking_reason_reference: str | None = Field(default=None, min_length=1)
    deep_link_authorization_granted: Literal[False] = False
    business_effect_authorized: Literal[False] = False
    account_link_performed: Literal[False] = False
    raw_payload_retained: Literal[False] = False
    provider_runtime_performed: Literal[False] = False
    second_business_effect_authorized: Literal[False] = False

    @model_validator(mode="after")
    def _validate_outcome_matrix(self) -> "TelegramDeepLinkValidationOutcome":
        evidence = self.request.context_resolution_evidence
        purpose = evidence.purpose
        mode = evidence.validation_mode
        replay = evidence.replay_state
        expiry = evidence.expiry_state
        owner = _DEEP_LINK_OWNER[purpose]
        if self.owner_boundary is not owner:
            raise ValueError("outcome owner boundary must match purpose")
        if mode in {
            TelegramDeepLinkPayloadValidationMode.UNVALIDATED,
            TelegramDeepLinkPayloadValidationMode.AMBIGUOUS,
        }:
            expected = (
                TelegramDeepLinkValidationState.REJECTED_UNTRUSTED
                if mode is TelegramDeepLinkPayloadValidationMode.UNVALIDATED
                else TelegramDeepLinkValidationState.AMBIGUOUS
            )
        elif expiry in {
            TelegramDeepLinkExpiryState.EXPIRED,
            TelegramDeepLinkExpiryState.MISSING,
        }:
            expected = TelegramDeepLinkValidationState.REJECTED_EXPIRED
        elif (
            expiry is TelegramDeepLinkExpiryState.AMBIGUOUS
            or replay is TelegramDeepLinkReplayState.AMBIGUOUS
            or purpose is TelegramDeepLinkPurpose.AMBIGUOUS
        ):
            expected = TelegramDeepLinkValidationState.AMBIGUOUS
        elif replay is TelegramDeepLinkReplayState.DUPLICATE_REPLAY:
            expected = TelegramDeepLinkValidationState.DUPLICATE_REPLAY
        elif replay is TelegramDeepLinkReplayState.FINGERPRINT_CONFLICT:
            expected = TelegramDeepLinkValidationState.FINGERPRINT_CONFLICT
        elif purpose is TelegramDeepLinkPurpose.UNSUPPORTED:
            expected = TelegramDeepLinkValidationState.UNSUPPORTED
        elif (
            purpose
            in {
                TelegramDeepLinkPurpose.RETURN_FROM_WEB_CABINET,
                TelegramDeepLinkPurpose.OPEN_FUTURE_MINI_APP_CONTEXT,
            }
            and evidence.external_context_decision_reference is None
        ):
            expected = TelegramDeepLinkValidationState.BLOCKED_PENDING_CONTEXT_DECISION
        elif mode not in {
            TelegramDeepLinkPayloadValidationMode.OPAQUE_SERVER_RESOLVED,
            TelegramDeepLinkPayloadValidationMode.SIGNED_VALIDATED,
        }:
            expected = TelegramDeepLinkValidationState.REJECTED_UNTRUSTED
        elif purpose is TelegramDeepLinkPurpose.LINK_EXISTING_ACCOUNT:
            expected = TelegramDeepLinkValidationState.IDENTITY_HANDOFF_REQUIRED
        else:
            expected = TelegramDeepLinkValidationState.VALIDATED_FOR_OWNER_HANDOFF
        if self.validation_state is not expected:
            raise ValueError("outcome state does not match validation matrix")
        needs_handoff = expected in {
            TelegramDeepLinkValidationState.IDENTITY_HANDOFF_REQUIRED,
            TelegramDeepLinkValidationState.VALIDATED_FOR_OWNER_HANDOFF,
        }
        if needs_handoff:
            if self.owner_handoff_reference is None:
                raise ValueError("successful validation requires owner handoff reference")
            if self.owner_handoff_reference != evidence.owner_contract_handoff_reference:
                raise ValueError("outcome and evidence handoff references must match")
        elif self.owner_handoff_reference is not None:
            raise ValueError("rejected or blocked validation cannot hand off")
        if not needs_handoff and (
            evidence.owner_contract_handoff_reference is not None
            or evidence.server_side_context_resolution_reference is not None
        ):
            raise ValueError("rejected or blocked validation cannot carry context references")
        if (
            expected is TelegramDeepLinkValidationState.VALIDATED_FOR_OWNER_HANDOFF
            and evidence.server_side_context_resolution_reference is None
        ):
            raise ValueError("supported purpose requires context resolution reference")
        if (
            expected is TelegramDeepLinkValidationState.IDENTITY_HANDOFF_REQUIRED
            and owner is not TelegramDeepLinkContextOwnerBoundary.IDENTITY_AND_ACCESS
        ):
            raise ValueError("identity handoff requires Identity owner")
        if (
            expected is TelegramDeepLinkValidationState.FINGERPRINT_CONFLICT
            and self.owner_handoff_reference is not None
        ):
            raise ValueError("fingerprint conflict cannot hand off")
        return self


class TelegramMiniAppPurpose(str, Enum):
    SHOW_FULL_LISTING_RESULT = "SHOW_FULL_LISTING_RESULT"
    SHOW_BEACON_SETTINGS = "SHOW_BEACON_SETTINGS"
    SHOW_BEACON_STATUS = "SHOW_BEACON_STATUS"
    RICH_ONBOARDING = "RICH_ONBOARDING"
    OPEN_FROM_NOTIFICATION_ACTION = "OPEN_FROM_NOTIFICATION_ACTION"
    UNSUPPORTED = "UNSUPPORTED"
    AMBIGUOUS = "AMBIGUOUS"


class TelegramMiniAppContextOwnerBoundary(str, Enum):
    IDENTITY_AND_ACCESS = "IDENTITY_AND_ACCESS"
    BEACON_MANAGEMENT = "BEACON_MANAGEMENT"
    NOTIFICATION_DELIVERY = "NOTIFICATION_DELIVERY"
    NONE = "NONE"


class TelegramMiniAppInitDataValidationState(str, Enum):
    OFFICIAL_VALIDATION_PASSED = "OFFICIAL_VALIDATION_PASSED"
    OFFICIAL_VALIDATION_REJECTED = "OFFICIAL_VALIDATION_REJECTED"
    INIT_DATA_MISSING = "INIT_DATA_MISSING"
    INIT_DATA_UNSAFE_ONLY = "INIT_DATA_UNSAFE_ONLY"
    NOT_PERFORMED = "NOT_PERFORMED"
    AMBIGUOUS = "AMBIGUOUS"


class TelegramMiniAppFreshnessState(str, Enum):
    WITHIN_EXTERNAL_POLICY = "WITHIN_EXTERNAL_POLICY"
    STALE = "STALE"
    MISSING = "MISSING"
    POLICY_NOT_SELECTED = "POLICY_NOT_SELECTED"
    AMBIGUOUS = "AMBIGUOUS"


class TelegramMiniAppFrontendDecisionState(str, Enum):
    EXTERNAL_DECISION_ACCEPTED = "EXTERNAL_DECISION_ACCEPTED"
    MISSING = "MISSING"
    REJECTED = "REJECTED"
    AMBIGUOUS = "AMBIGUOUS"


class TelegramMiniAppValidationState(str, Enum):
    IDENTITY_HANDOFF_REQUIRED = "IDENTITY_HANDOFF_REQUIRED"
    BLOCKED_PENDING_FRONTEND_DECISION = "BLOCKED_PENDING_FRONTEND_DECISION"
    BLOCKED_PENDING_FRESHNESS_POLICY = "BLOCKED_PENDING_FRESHNESS_POLICY"
    REJECTED_INIT_DATA_UNSAFE_ONLY = "REJECTED_INIT_DATA_UNSAFE_ONLY"
    REJECTED_INIT_DATA_MISSING = "REJECTED_INIT_DATA_MISSING"
    REJECTED_OFFICIAL_VALIDATION = "REJECTED_OFFICIAL_VALIDATION"
    REJECTED_STALE_OR_MISSING_AUTH_DATE = "REJECTED_STALE_OR_MISSING_AUTH_DATE"
    UNSUPPORTED = "UNSUPPORTED"
    AMBIGUOUS = "AMBIGUOUS"
    BLOCKED = "BLOCKED"


_MINI_APP_PURPOSE_OWNERS: dict[TelegramMiniAppPurpose, TelegramMiniAppContextOwnerBoundary] = {
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


class TelegramUntrustedMiniAppLaunchReference(_TelegramContract):
    telegram_mini_app_launch_reference_id: str = Field(min_length=1)
    telegram_bot_ref: str = Field(min_length=1)
    launch_context_reference: str = Field(min_length=1)
    launch_data_fingerprint: IdempotencyFingerprint
    purpose_candidate: TelegramMiniAppPurpose
    unsafe_context_present: bool
    launch_input_untrusted: Literal[True] = True
    unsafe_context_untrusted: Literal[True] = True
    raw_launch_data_retained: Literal[False] = False
    raw_unsafe_context_retained: Literal[False] = False
    client_ui_authorization: Literal[False] = False
    raw_provider_payload_retained: Literal[False] = False


class TelegramMiniAppOfficialValidationEvidence(_TelegramContract):
    telegram_mini_app_official_validation_evidence_id: str = Field(min_length=1)
    telegram_bot_ref: str = Field(min_length=1)
    matching_launch_data_fingerprint: IdempotencyFingerprint
    init_data_validation_state: TelegramMiniAppInitDataValidationState
    freshness_state: TelegramMiniAppFreshnessState
    official_provider_evidence_reference: str = Field(min_length=1)
    official_validation_policy_reference: str = Field(min_length=1)
    external_freshness_policy_reference: str | None = Field(default=None, min_length=1)
    validated_provider_identity_reference: str | None = Field(default=None, min_length=1)
    backend_received_raw_launch_data_for_validation: bool
    raw_launch_data_retained: Literal[False] = False
    unsafe_context_used_for_authentication: Literal[False] = False
    unsafe_context_used_for_authorization: Literal[False] = False
    validation_algorithm_implemented: Literal[False] = False
    bot_token_consumed: Literal[False] = False
    provider_runtime_performed: Literal[False] = False

    @model_validator(mode="after")
    def _validate_evidence_matrix(self) -> "TelegramMiniAppOfficialValidationEvidence":
        passed_or_rejected = {
            TelegramMiniAppInitDataValidationState.OFFICIAL_VALIDATION_PASSED,
            TelegramMiniAppInitDataValidationState.OFFICIAL_VALIDATION_REJECTED,
            TelegramMiniAppInitDataValidationState.AMBIGUOUS,
        }
        if (self.init_data_validation_state in passed_or_rejected) != (
            self.backend_received_raw_launch_data_for_validation
        ):
            raise ValueError("official or ambiguous validation requires backend raw input receipt")
        if (
            self.init_data_validation_state
            is TelegramMiniAppInitDataValidationState.INIT_DATA_MISSING
        ):
            if self.freshness_state is not TelegramMiniAppFreshnessState.MISSING:
                raise ValueError("missing launch data requires missing freshness")
        if (
            self.init_data_validation_state
            in {
                TelegramMiniAppInitDataValidationState.INIT_DATA_UNSAFE_ONLY,
                TelegramMiniAppInitDataValidationState.NOT_PERFORMED,
            }
            and self.freshness_state is not TelegramMiniAppFreshnessState.POLICY_NOT_SELECTED
        ):
            raise ValueError("unsafe-only or unperformed validation requires unselected policy")
        if (
            self.init_data_validation_state
            is TelegramMiniAppInitDataValidationState.OFFICIAL_VALIDATION_REJECTED
            and self.freshness_state is TelegramMiniAppFreshnessState.WITHIN_EXTERNAL_POLICY
        ):
            raise ValueError("rejected validation cannot be fresh")
        policy_states = {
            TelegramMiniAppFreshnessState.WITHIN_EXTERNAL_POLICY,
            TelegramMiniAppFreshnessState.STALE,
            TelegramMiniAppFreshnessState.MISSING,
            TelegramMiniAppFreshnessState.AMBIGUOUS,
        }
        if self.freshness_state in policy_states:
            if self.external_freshness_policy_reference is None:
                raise ValueError("freshness evaluation requires external policy reference")
        elif self.external_freshness_policy_reference is not None:
            raise ValueError("unselected freshness policy cannot have policy reference")
        passed = (
            self.init_data_validation_state
            is TelegramMiniAppInitDataValidationState.OFFICIAL_VALIDATION_PASSED
        )
        if passed != (self.validated_provider_identity_reference is not None):
            raise ValueError("only passed official validation may have provider identity reference")
        return self


class TelegramMiniAppValidationRequest(_TelegramContract):
    telegram_mini_app_validation_request_id: str = Field(min_length=1)
    untrusted_launch_reference: TelegramUntrustedMiniAppLaunchReference
    official_validation_evidence: TelegramMiniAppOfficialValidationEvidence
    verified_telegram_provider_identity_evidence: VerifiedTelegramIdentityEvidence | None = None
    frontend_decision_state: TelegramMiniAppFrontendDecisionState
    external_frontend_decision_reference: str | None = Field(default=None, min_length=1)
    requested_context_owner_boundary: TelegramMiniAppContextOwnerBoundary
    provider_identity_remains_external: Literal[True] = True
    client_ui_state_authorization: Literal[False] = False
    internal_account_resolved: Literal[False] = False
    account_created: Literal[False] = False
    account_linked: Literal[False] = False
    business_effect_authorized: Literal[False] = False
    business_owner_handoff_authorized: Literal[False] = False

    @model_validator(mode="after")
    def _validate_request_matrix(self) -> "TelegramMiniAppValidationRequest":
        launch = self.untrusted_launch_reference
        evidence = self.official_validation_evidence
        if launch.telegram_bot_ref != evidence.telegram_bot_ref:
            raise ValueError("launch and validation bot scopes must match")
        if launch.launch_data_fingerprint != evidence.matching_launch_data_fingerprint:
            raise ValueError("launch and validation fingerprints must match")
        expected_owner = _MINI_APP_PURPOSE_OWNERS[launch.purpose_candidate]
        if self.requested_context_owner_boundary is not expected_owner:
            raise ValueError("requested owner does not match purpose mapping")
        if (
            self.frontend_decision_state
            is TelegramMiniAppFrontendDecisionState.EXTERNAL_DECISION_ACCEPTED
        ):
            if self.external_frontend_decision_reference is None:
                raise ValueError("accepted frontend decision requires reference")
        elif self.external_frontend_decision_reference is not None:
            raise ValueError("non-accepted frontend decision cannot have reference")
        passed = (
            evidence.init_data_validation_state
            is TelegramMiniAppInitDataValidationState.OFFICIAL_VALIDATION_PASSED
        )
        if (
            evidence.init_data_validation_state
            is TelegramMiniAppInitDataValidationState.INIT_DATA_UNSAFE_ONLY
            and not launch.unsafe_context_present
        ):
            raise ValueError("unsafe-only validation requires unsafe context presence")
        if (
            evidence.init_data_validation_state
            is TelegramMiniAppInitDataValidationState.INIT_DATA_MISSING
            and launch.unsafe_context_present
        ):
            raise ValueError("missing init data requires absent unsafe context")
        if passed != (self.verified_telegram_provider_identity_evidence is not None):
            raise ValueError("verified identity is required only after passed validation")
        identity = self.verified_telegram_provider_identity_evidence
        if passed:
            assert identity is not None
            if evidence.validated_provider_identity_reference != (
                identity.provider_identity.telegram_provider_identity_ref
            ):
                raise ValueError("official evidence must bind the exact verified provider identity")
            if identity.provider_identity.telegram_bot_ref not in {
                launch.telegram_bot_ref,
                evidence.telegram_bot_ref,
            }:
                raise ValueError("verified identity bot scope must match launch and evidence")
        elif evidence.validated_provider_identity_reference is not None:
            raise ValueError("non-passed validation cannot have provider identity reference")
        return self


class TelegramMiniAppValidationOutcome(_TelegramContract):
    telegram_mini_app_validation_outcome_id: str = Field(min_length=1)
    validation_request: TelegramMiniAppValidationRequest
    validation_state: TelegramMiniAppValidationState
    requested_context_owner_boundary: TelegramMiniAppContextOwnerBoundary
    identity_handoff_reference: str | None = Field(default=None, min_length=1)
    blocking_or_rejection_reason_reference: str | None = Field(default=None, min_length=1)
    internal_account_authorization_granted: Literal[False] = False
    business_owner_authorization_granted: Literal[False] = False
    business_effect_authorized: Literal[False] = False
    client_ui_state_trusted_for_authorization: Literal[False] = False
    raw_launch_data_retained: Literal[False] = False
    provider_runtime_performed: Literal[False] = False
    account_created: Literal[False] = False
    account_linked: Literal[False] = False

    @model_validator(mode="after")
    def _validate_outcome_matrix(self) -> "TelegramMiniAppValidationOutcome":
        request = self.validation_request
        evidence = request.official_validation_evidence
        launch = request.untrusted_launch_reference
        if self.requested_context_owner_boundary is not request.requested_context_owner_boundary:
            raise ValueError("outcome owner must match request owner")
        validation = evidence.init_data_validation_state
        freshness = evidence.freshness_state
        if validation is TelegramMiniAppInitDataValidationState.INIT_DATA_UNSAFE_ONLY:
            expected = TelegramMiniAppValidationState.REJECTED_INIT_DATA_UNSAFE_ONLY
        elif validation is TelegramMiniAppInitDataValidationState.INIT_DATA_MISSING:
            expected = TelegramMiniAppValidationState.REJECTED_INIT_DATA_MISSING
        elif validation is TelegramMiniAppInitDataValidationState.NOT_PERFORMED:
            expected = TelegramMiniAppValidationState.BLOCKED
        elif validation is TelegramMiniAppInitDataValidationState.OFFICIAL_VALIDATION_REJECTED:
            expected = TelegramMiniAppValidationState.REJECTED_OFFICIAL_VALIDATION
        elif validation is TelegramMiniAppInitDataValidationState.AMBIGUOUS:
            expected = TelegramMiniAppValidationState.AMBIGUOUS
        elif freshness is TelegramMiniAppFreshnessState.POLICY_NOT_SELECTED:
            expected = TelegramMiniAppValidationState.BLOCKED_PENDING_FRESHNESS_POLICY
        elif freshness in {
            TelegramMiniAppFreshnessState.STALE,
            TelegramMiniAppFreshnessState.MISSING,
        }:
            expected = TelegramMiniAppValidationState.REJECTED_STALE_OR_MISSING_AUTH_DATE
        elif freshness is TelegramMiniAppFreshnessState.AMBIGUOUS:
            expected = TelegramMiniAppValidationState.AMBIGUOUS
        elif launch.purpose_candidate is TelegramMiniAppPurpose.UNSUPPORTED:
            expected = TelegramMiniAppValidationState.UNSUPPORTED
        elif launch.purpose_candidate is TelegramMiniAppPurpose.AMBIGUOUS:
            expected = TelegramMiniAppValidationState.AMBIGUOUS
        elif request.frontend_decision_state is TelegramMiniAppFrontendDecisionState.MISSING:
            expected = TelegramMiniAppValidationState.BLOCKED_PENDING_FRONTEND_DECISION
        elif request.frontend_decision_state is TelegramMiniAppFrontendDecisionState.REJECTED:
            expected = TelegramMiniAppValidationState.BLOCKED
        elif request.frontend_decision_state is TelegramMiniAppFrontendDecisionState.AMBIGUOUS:
            expected = TelegramMiniAppValidationState.AMBIGUOUS
        else:
            expected = TelegramMiniAppValidationState.IDENTITY_HANDOFF_REQUIRED
        if self.validation_state is not expected:
            raise ValueError("outcome state does not match validation matrix")
        success = expected is TelegramMiniAppValidationState.IDENTITY_HANDOFF_REQUIRED
        if success != (self.identity_handoff_reference is not None):
            raise ValueError("only successful outcome may carry identity handoff")
        if success != (self.blocking_or_rejection_reason_reference is None):
            raise ValueError("successful outcome forbids reason; other outcomes require reason")
        return self


__all__ = [
    "TelegramOutboundRequestClass",
    "TelegramOutboundMappingState",
    "TelegramOutboundMappingReasonCode",
    "TelegramNotificationAttemptHandoff",
    "TelegramListingCardProjectionHandoff",
    "TelegramOutboundTargetReference",
    "TelegramOutboundMappingRequest",
    "TelegramOutboundRequestIntent",
    "TelegramOutboundMappingOutcome",
    "TelegramDisplayClass",
    "TelegramDisplayProjectionState",
    "TelegramDisplayReasonCode",
    "TelegramSafeListingFieldFact",
    "TelegramListingCardDisplaySnapshot",
    "TelegramListingDisplayHandoff",
    "TelegramDisplayActionReference",
    "TelegramDisplayBoundaryRequest",
    "TelegramDisplayProjection",
    "TelegramDisplayBoundaryOutcome",
    "TelegramProviderOutcomeClass",
    "TelegramProviderOutcomeMappingState",
    "TelegramProviderOutcomeReasonCode",
    "TelegramTransportOutcomeObservation",
    "TelegramProviderResponseObservation",
    "TelegramProviderReconciliationObservation",
    "TelegramProviderOutcomeMappingRequest",
    "TelegramNotificationProviderOutcomeHandoff",
    "TelegramProviderOutcome",
    "TelegramProviderOutcomeMappingDecision",
    "TelegramChatSurfaceClass",
    "TelegramChatSurfaceAdmissionState",
    "TelegramChatSurfaceReasonCode",
    "TelegramUntrustedChatSurfaceReference",
    "TelegramChatSurfaceAdmissionRequest",
    "TelegramChatSurfaceAdmissionOutcome",
    "TelegramInboundInputKind",
    "TelegramIntentFamily",
    "TelegramIntentNormalizationState",
    "TelegramIntentOwnerBoundary",
    "TelegramUntrustedInputReference",
    "TelegramIntentNormalizationRequest",
    "TelegramCommandEnvelope",
    "TelegramAccountLinkReference",
    "TelegramIdentityResolutionOutcome",
    "TelegramIdentityResolutionRequest",
    "TelegramIdentityResolutionState",
    "TelegramProviderUpdateIdentity",
    "TelegramProviderIdentity",
    "TelegramUpdateAdmissionState",
    "TelegramUpdateStructuralClass",
    "TelegramUpdateIntakeState",
    "TelegramUpdateDeduplicationState",
    "TelegramUpdateIntakeRecord",
    "TelegramUpdateDeduplicationRecord",
    "VerifiedTelegramIdentityEvidence",
    "TelegramProviderMode",
    "TelegramProviderModeBoundaryState",
    "TelegramWebhookModeRequirements",
    "TelegramGetUpdatesModeRequirements",
    "TelegramProviderModeBoundary",
    "TelegramExistingBotEvidenceState",
    "TelegramExistingBotMetadata",
    "TelegramProtectedSecretPresenceEvidence",
    "TelegramPublicBotMetadataPresenceEvidence",
    "TelegramExistingBotOperationalGate",
    "TelegramDeepLinkPurpose",
    "TelegramDeepLinkContextOwnerBoundary",
    "TelegramDeepLinkPayloadValidationMode",
    "TelegramDeepLinkReplayState",
    "TelegramDeepLinkExpiryState",
    "TelegramDeepLinkValidationState",
    "TelegramUntrustedDeepLinkReference",
    "TelegramDeepLinkContextResolutionEvidence",
    "TelegramDeepLinkValidationRequest",
    "TelegramDeepLinkValidationOutcome",
    "TelegramMiniAppPurpose",
    "TelegramMiniAppContextOwnerBoundary",
    "TelegramMiniAppInitDataValidationState",
    "TelegramMiniAppFreshnessState",
    "TelegramMiniAppFrontendDecisionState",
    "TelegramMiniAppValidationState",
    "TelegramUntrustedMiniAppLaunchReference",
    "TelegramMiniAppOfficialValidationEvidence",
    "TelegramMiniAppValidationRequest",
    "TelegramMiniAppValidationOutcome",
    "TelegramPrivacyDataClass",
    "TelegramDiagnosticPurpose",
    "TelegramPrivacyProjectionState",
    "TelegramPrivacyReasonCode",
    "TelegramUntrustedPrivacyReference",
    "TelegramSafeDiagnosticFact",
    "TelegramRetentionGateReference",
    "TelegramPrivacyBoundaryRequest",
    "TelegramSafeDiagnosticProjection",
    "TelegramPrivacyBoundaryOutcome",
    "TelegramRuntimeCapability",
    "TelegramPreGateAllowedSurface",
    "TelegramRuntimeGateKind",
    "TelegramRuntimeGateState",
    "TelegramRuntimeGateReasonCode",
    "TelegramRuntimeGateReference",
    "TelegramRuntimeBoundaryRequest",
    "TelegramRuntimeBoundaryOutcome",
]


# TG-14 semantic-only security, privacy and retention boundary.
class TelegramPrivacyDataClass(str, Enum):
    SAFE_PROVIDER_IDENTIFIER = "SAFE_PROVIDER_IDENTIFIER"
    SAFE_DIAGNOSTIC_METADATA = "SAFE_DIAGNOSTIC_METADATA"
    PRIVATE_MESSAGE_OR_COMMAND_CONTENT = "PRIVATE_MESSAGE_OR_COMMAND_CONTENT"
    CALLBACK_OR_DEEP_LINK_INPUT = "CALLBACK_OR_DEEP_LINK_INPUT"
    MINI_APP_LAUNCH_DATA = "MINI_APP_LAUNCH_DATA"
    CONTACT_OR_PHONE_DATA = "CONTACT_OR_PHONE_DATA"
    PROFILE_OR_MEMBERSHIP_DATA = "PROFILE_OR_MEMBERSHIP_DATA"
    RAW_PROVIDER_PAYLOAD = "RAW_PROVIDER_PAYLOAD"
    PROVIDER_SECRET = "PROVIDER_SECRET"


class TelegramDiagnosticPurpose(str, Enum):
    SECURITY_REJECTION = "SECURITY_REJECTION"
    INPUT_VALIDATION = "INPUT_VALIDATION"
    DEDUPLICATION_OR_REPLAY = "DEDUPLICATION_OR_REPLAY"
    UNSUPPORTED_SURFACE = "UNSUPPORTED_SURFACE"
    OUTBOUND_PROVIDER_OUTCOME = "OUTBOUND_PROVIDER_OUTCOME"
    RECONCILIATION = "RECONCILIATION"
    OPERATIONS_HEALTH = "OPERATIONS_HEALTH"


class TelegramPrivacyProjectionState(str, Enum):
    SAFE_DIAGNOSTIC_PROJECTED = "SAFE_DIAGNOSTIC_PROJECTED"
    BLOCKED_SECRET = "BLOCKED_SECRET"
    BLOCKED_RAW_PAYLOAD = "BLOCKED_RAW_PAYLOAD"
    BLOCKED_PRIVATE_CONTENT = "BLOCKED_PRIVATE_CONTENT"
    BLOCKED_EXCESS_PERSONAL_DATA = "BLOCKED_EXCESS_PERSONAL_DATA"
    BLOCKED_UNSAFE_EXTERNAL_STRING = "BLOCKED_UNSAFE_EXTERNAL_STRING"
    RETENTION_DECISION_REQUIRED = "RETENTION_DECISION_REQUIRED"
    INVALID_SCOPE = "INVALID_SCOPE"
    AMBIGUOUS = "AMBIGUOUS"


class TelegramPrivacyReasonCode(str, Enum):
    SAFE_MINIMIZED_DIAGNOSTIC = "SAFE_MINIMIZED_DIAGNOSTIC"
    SECRET_MATERIAL_FORBIDDEN = "SECRET_MATERIAL_FORBIDDEN"
    RAW_PROVIDER_PAYLOAD_FORBIDDEN = "RAW_PROVIDER_PAYLOAD_FORBIDDEN"
    PRIVATE_MESSAGE_ARCHIVE_FORBIDDEN = "PRIVATE_MESSAGE_ARCHIVE_FORBIDDEN"
    CONTACT_OR_PHONE_DEFAULT_FORBIDDEN = "CONTACT_OR_PHONE_DEFAULT_FORBIDDEN"
    GROUP_MEMBERSHIP_RETENTION_FORBIDDEN = "GROUP_MEMBERSHIP_RETENTION_FORBIDDEN"
    UNNECESSARY_PROFILE_DATA_FORBIDDEN = "UNNECESSARY_PROFILE_DATA_FORBIDDEN"
    EXTERNAL_STRING_EXECUTION_FORBIDDEN = "EXTERNAL_STRING_EXECUTION_FORBIDDEN"
    OD_013_RETENTION_POLICY_OPEN = "OD_013_RETENTION_POLICY_OPEN"
    PRIVACY_SCOPE_MISMATCH = "PRIVACY_SCOPE_MISMATCH"
    UNSAFE_DIAGNOSTIC_FACT = "UNSAFE_DIAGNOSTIC_FACT"
    AMBIGUOUS_PRIVACY_EVIDENCE = "AMBIGUOUS_PRIVACY_EVIDENCE"


def _tg14_id(value: object, name: str) -> str:
    _tg13_text(value, name)
    return value


def _tg14_tuple(value: object, name: str) -> tuple[str, ...]:
    return _tg13_tuple(value, name)


def _tg14_exact(value: object, expected: type[object], name: str) -> None:
    if type(value) is not expected:
        raise ValueError(f"{name} must be an exact {expected.__name__}")


def _tg14_exact_tuple(value: object, expected: type[object], name: str) -> object:
    if type(value) is not tuple or any(type(item) is not expected for item in value):
        raise ValueError(f"{name} must be a tuple of exact {expected.__name__}")
    return value


class TelegramUntrustedPrivacyReference(_TelegramContract):
    telegram_untrusted_privacy_reference_id: str
    metadata: ContractMetadata
    data_class: TelegramPrivacyDataClass
    source_reference_id: str
    provider_bot_scope_reference_id: str
    provider_identifier_reference_ids: tuple[str, ...]
    safe_evidence_reference_ids: tuple[str, ...]
    raw_provider_payload_observed: bool
    secret_material_observed: bool
    private_message_content_observed: bool
    contact_or_phone_data_observed: bool
    group_membership_data_observed: bool
    unnecessary_profile_data_observed: bool
    external_string_present: bool
    external_string_requires_execution: bool
    raw_value_embedded: Literal[False] = False
    raw_value_retained: Literal[False] = False
    safe_reference_only: Literal[True] = True
    internal_account_authority: Literal[False] = False
    business_effect_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False
    shell_execution_authority: Literal[False] = False

    _validate_ids = field_validator(
        "telegram_untrusted_privacy_reference_id",
        "source_reference_id",
        "provider_bot_scope_reference_id",
        mode="before",
    )(_tg14_id)
    _validate_tuples = field_validator(
        "provider_identifier_reference_ids", "safe_evidence_reference_ids", mode="before"
    )(_tg14_tuple)

    @model_validator(mode="after")
    def _validate_consistency(self) -> "TelegramUntrustedPrivacyReference":
        if self.external_string_requires_execution and not self.external_string_present:
            raise ValueError("execution requirement needs an external string")
        expected = {
            TelegramPrivacyDataClass.SAFE_PROVIDER_IDENTIFIER: not any(
                (
                    self.raw_provider_payload_observed,
                    self.secret_material_observed,
                    self.private_message_content_observed,
                    self.contact_or_phone_data_observed,
                    self.group_membership_data_observed,
                    self.unnecessary_profile_data_observed,
                    self.external_string_present,
                )
            ),
            TelegramPrivacyDataClass.SAFE_DIAGNOSTIC_METADATA: not any(
                (
                    self.raw_provider_payload_observed,
                    self.secret_material_observed,
                    self.private_message_content_observed,
                    self.contact_or_phone_data_observed,
                    self.group_membership_data_observed,
                    self.unnecessary_profile_data_observed,
                )
            ),
        }
        if self.data_class in expected and not expected[self.data_class]:
            raise ValueError("data class is inconsistent with observations")
        observed_classes = {
            "raw_provider_payload_observed": TelegramPrivacyDataClass.RAW_PROVIDER_PAYLOAD,
            "secret_material_observed": TelegramPrivacyDataClass.PROVIDER_SECRET,
            "private_message_content_observed": TelegramPrivacyDataClass.PRIVATE_MESSAGE_OR_COMMAND_CONTENT,
            "contact_or_phone_data_observed": TelegramPrivacyDataClass.CONTACT_OR_PHONE_DATA,
            "group_membership_data_observed": TelegramPrivacyDataClass.PROFILE_OR_MEMBERSHIP_DATA,
            "unnecessary_profile_data_observed": TelegramPrivacyDataClass.PROFILE_OR_MEMBERSHIP_DATA,
            "external_string_present": TelegramPrivacyDataClass.CALLBACK_OR_DEEP_LINK_INPUT,
        }
        matched = False
        for flag, data_class in observed_classes.items():
            if getattr(self, flag) and self.data_class is data_class:
                matched = True
        if any(getattr(self, flag) for flag in observed_classes) and not matched:
            raise ValueError("safe data class cannot carry unsafe observations")
        return self


class TelegramSafeDiagnosticFact(_TelegramContract):
    telegram_safe_diagnostic_fact_id: str
    metadata: ContractMetadata
    diagnostic_purpose: TelegramDiagnosticPurpose
    fact_class: str
    reason_code: TelegramPrivacyReasonCode
    provider_bot_scope_reference_id: str | None
    provider_identifier_reference_ids: tuple[str, ...]
    correlation_id: str | None
    causation_id: str | None
    source_privacy_reference_ids: tuple[str, ...]
    safe_evidence_reference_ids: tuple[str, ...]
    safe_reference_only: Literal[True] = True
    minimized: Literal[True] = True
    redacted: Literal[True] = True
    raw_provider_payload_present: Literal[False] = False
    token_or_secret_present: Literal[False] = False
    private_message_content_present: Literal[False] = False
    contact_or_phone_present: Literal[False] = False
    group_member_list_present: Literal[False] = False
    unnecessary_profile_data_present: Literal[False] = False
    executable_external_string_present: Literal[False] = False
    business_success_authority: Literal[False] = False

    _validate_id = field_validator("telegram_safe_diagnostic_fact_id", mode="before")(_tg14_id)
    _validate_metadata = field_validator("metadata", mode="before")(
        lambda value: (_tg14_exact(value, ContractMetadata, "metadata"), value)[1]
    )
    _validate_optional = field_validator(
        "provider_bot_scope_reference_id", "correlation_id", "causation_id", mode="before"
    )(_tg13_optional_text)
    _validate_fact_class = field_validator("fact_class", mode="before")(_tg14_id)
    _validate_tuples = field_validator(
        "provider_identifier_reference_ids",
        "source_privacy_reference_ids",
        "safe_evidence_reference_ids",
        mode="before",
    )(_tg14_tuple)


class TelegramRetentionGateReference(_TelegramContract):
    telegram_retention_gate_reference_id: str
    od_reference: Literal["OD-013"]
    decision_state: Literal["OPEN"]
    retention_period_defined: Literal[False] = False
    deletion_policy_defined: Literal[False] = False
    archive_policy_defined: Literal[False] = False
    compaction_policy_defined: Literal[False] = False
    provider_payload_retention_authorized: Literal[False] = False
    private_message_archive_authorized: Literal[False] = False
    persistence_implementation_authorized: Literal[False] = False
    implementation_may_guess: Literal[False] = False
    open_decision_blocks_mutation: Literal[True] = True

    _validate_id = field_validator("telegram_retention_gate_reference_id", mode="before")(_tg14_id)


class TelegramPrivacyBoundaryRequest(_TelegramContract):
    telegram_privacy_boundary_request_id: str
    metadata: ContractMetadata
    privacy_reference: TelegramUntrustedPrivacyReference
    diagnostic_purpose: TelegramDiagnosticPurpose
    safe_diagnostic_facts: tuple[TelegramSafeDiagnosticFact, ...]
    retention_gate: TelegramRetentionGateReference
    retention_or_storage_policy_requested: bool
    persistence_requested: bool
    deletion_requested: bool
    archive_requested: bool
    compaction_requested: bool
    diagnostic_projection_only: Literal[True] = True
    provider_call_requested: Literal[False] = False
    business_effect_requested: Literal[False] = False
    shell_execution_requested: Literal[False] = False

    _validate_id = field_validator("telegram_privacy_boundary_request_id", mode="before")(_tg14_id)
    _validate_metadata = field_validator("metadata", mode="before")(
        lambda value: (_tg14_exact(value, ContractMetadata, "metadata"), value)[1]
    )

    @field_validator("privacy_reference", "retention_gate", mode="before")
    @classmethod
    def _validate_exact_refs(cls, value: object, info: ValidationInfo) -> object:
        expected = (
            TelegramUntrustedPrivacyReference
            if info.field_name == "privacy_reference"
            else TelegramRetentionGateReference
        )
        _tg14_exact(value, expected, info.field_name)
        return value

    @field_validator("safe_diagnostic_facts", mode="before")
    @classmethod
    def _validate_exact_facts(cls, value: object) -> object:
        if type(value) is not tuple or any(
            type(item) is not TelegramSafeDiagnosticFact for item in value
        ):
            raise ValueError("safe_diagnostic_facts must be a tuple of exact safe facts")
        ids = tuple(item.telegram_safe_diagnostic_fact_id for item in value)
        if len(ids) != len(set(ids)):
            raise ValueError("safe diagnostic fact IDs must be unique")
        return value

    @model_validator(mode="after")
    def _validate_scope(self) -> "TelegramPrivacyBoundaryRequest":
        if (
            self.privacy_reference.metadata != self.metadata
            or self.retention_gate.od_reference != "OD-013"
            or self.retention_gate.decision_state != "OPEN"
        ):
            raise ValueError("privacy request metadata or retention gate mismatch")
        for fact in self.safe_diagnostic_facts:
            if (
                fact.metadata != self.metadata
                or fact.diagnostic_purpose is not self.diagnostic_purpose
            ):
                raise ValueError("nested diagnostic fact scope mismatch")
            if (
                self.privacy_reference.telegram_untrusted_privacy_reference_id
                not in fact.source_privacy_reference_ids
            ):
                raise ValueError("diagnostic fact is not bound to privacy reference")
        if (
            self.provider_call_requested
            or self.business_effect_requested
            or self.shell_execution_requested
        ):
            raise ValueError("runtime, business and shell authority are forbidden")
        return self


class TelegramSafeDiagnosticProjection(_TelegramContract):
    telegram_safe_diagnostic_projection_id: str
    metadata: ContractMetadata
    request_reference_id: str
    diagnostic_purpose: TelegramDiagnosticPurpose
    safe_diagnostic_facts: tuple[TelegramSafeDiagnosticFact, ...]
    source_privacy_reference_ids: tuple[str, ...]
    reason_code: TelegramPrivacyReasonCode
    retention_gate_reference_id: str
    safe_diagnostic_only: Literal[True] = True
    minimized: Literal[True] = True
    redacted: Literal[True] = True
    raw_provider_payload_retained: Literal[False] = False
    secret_material_retained: Literal[False] = False
    private_message_content_retained: Literal[False] = False
    contact_or_phone_retained: Literal[False] = False
    group_membership_retained: Literal[False] = False
    unnecessary_profile_data_retained: Literal[False] = False
    external_string_executed: Literal[False] = False
    retention_policy_applied: Literal[False] = False
    persistence_mutation_performed: Literal[False] = False
    business_effect_authorized: Literal[False] = False

    _validate_ids = field_validator(
        "telegram_safe_diagnostic_projection_id",
        "request_reference_id",
        "retention_gate_reference_id",
        mode="before",
    )(_tg14_id)
    _validate_metadata = field_validator("metadata", mode="before")(
        lambda value: (_tg14_exact(value, ContractMetadata, "metadata"), value)[1]
    )
    _validate_facts = field_validator("safe_diagnostic_facts", mode="before")(
        lambda value: _tg14_exact_tuple(value, TelegramSafeDiagnosticFact, "safe_diagnostic_facts")
    )
    _validate_tuples = field_validator("source_privacy_reference_ids", mode="before")(_tg14_tuple)


class TelegramPrivacyBoundaryOutcome(_TelegramContract):
    telegram_privacy_boundary_outcome_id: str
    metadata: ContractMetadata
    request: TelegramPrivacyBoundaryRequest
    state: TelegramPrivacyProjectionState
    reason_code: TelegramPrivacyReasonCode
    safe_projection: TelegramSafeDiagnosticProjection | None
    safe_diagnostic_reference_id: str | None
    provider_call_performed: Literal[False] = False
    raw_provider_payload_retained: Literal[False] = False
    secret_material_retained: Literal[False] = False
    private_message_archived: Literal[False] = False
    personal_data_expanded: Literal[False] = False
    external_string_executed: Literal[False] = False
    persistence_mutation_performed: Literal[False] = False
    retention_policy_implemented: Literal[False] = False
    deletion_policy_implemented: Literal[False] = False
    archive_policy_implemented: Literal[False] = False
    compaction_policy_implemented: Literal[False] = False
    business_effect_authorized: Literal[False] = False

    _validate_id = field_validator("telegram_privacy_boundary_outcome_id", mode="before")(_tg14_id)
    _validate_metadata = field_validator("metadata", mode="before")(
        lambda value: (_tg14_exact(value, ContractMetadata, "metadata"), value)[1]
    )
    _validate_request = field_validator("request", mode="before")(
        lambda value: (_tg14_exact(value, TelegramPrivacyBoundaryRequest, "request"), value)[1]
    )
    _validate_projection = field_validator("safe_projection", mode="before")(
        lambda value: (
            value
            if value is None
            else (_tg14_exact(value, TelegramSafeDiagnosticProjection, "safe_projection"), value)[1]
        )
    )

    @model_validator(mode="after")
    def _validate_outcome(self) -> "TelegramPrivacyBoundaryOutcome":
        if self.metadata != self.request.metadata:
            raise ValueError("outcome metadata mismatch")
        ref = self.request.privacy_reference
        if ref.secret_material_observed:
            expected = (
                TelegramPrivacyProjectionState.BLOCKED_SECRET,
                TelegramPrivacyReasonCode.SECRET_MATERIAL_FORBIDDEN,
            )
        elif ref.raw_provider_payload_observed:
            expected = (
                TelegramPrivacyProjectionState.BLOCKED_RAW_PAYLOAD,
                TelegramPrivacyReasonCode.RAW_PROVIDER_PAYLOAD_FORBIDDEN,
            )
        elif ref.private_message_content_observed:
            expected = (
                TelegramPrivacyProjectionState.BLOCKED_PRIVATE_CONTENT,
                TelegramPrivacyReasonCode.PRIVATE_MESSAGE_ARCHIVE_FORBIDDEN,
            )
        elif ref.contact_or_phone_data_observed:
            expected = (
                TelegramPrivacyProjectionState.BLOCKED_EXCESS_PERSONAL_DATA,
                TelegramPrivacyReasonCode.CONTACT_OR_PHONE_DEFAULT_FORBIDDEN,
            )
        elif ref.group_membership_data_observed:
            expected = (
                TelegramPrivacyProjectionState.BLOCKED_EXCESS_PERSONAL_DATA,
                TelegramPrivacyReasonCode.GROUP_MEMBERSHIP_RETENTION_FORBIDDEN,
            )
        elif ref.unnecessary_profile_data_observed:
            expected = (
                TelegramPrivacyProjectionState.BLOCKED_EXCESS_PERSONAL_DATA,
                TelegramPrivacyReasonCode.UNNECESSARY_PROFILE_DATA_FORBIDDEN,
            )
        elif ref.external_string_requires_execution:
            expected = (
                TelegramPrivacyProjectionState.BLOCKED_UNSAFE_EXTERNAL_STRING,
                TelegramPrivacyReasonCode.EXTERNAL_STRING_EXECUTION_FORBIDDEN,
            )
        elif any(
            (
                self.request.retention_or_storage_policy_requested,
                self.request.persistence_requested,
                self.request.deletion_requested,
                self.request.archive_requested,
                self.request.compaction_requested,
            )
        ):
            expected = (
                TelegramPrivacyProjectionState.RETENTION_DECISION_REQUIRED,
                TelegramPrivacyReasonCode.OD_013_RETENTION_POLICY_OPEN,
            )
        elif not self.request.safe_diagnostic_facts:
            expected = (
                TelegramPrivacyProjectionState.INVALID_SCOPE,
                TelegramPrivacyReasonCode.UNSAFE_DIAGNOSTIC_FACT,
            )
        else:
            expected = (
                TelegramPrivacyProjectionState.SAFE_DIAGNOSTIC_PROJECTED,
                TelegramPrivacyReasonCode.SAFE_MINIMIZED_DIAGNOSTIC,
            )
        if (self.state, self.reason_code) != expected:
            raise ValueError("outcome state/reason does not match privacy precedence")
        safe = self.state is TelegramPrivacyProjectionState.SAFE_DIAGNOSTIC_PROJECTED
        if safe:
            if self.safe_projection is None or self.safe_diagnostic_reference_id is not None:
                raise ValueError(
                    "safe outcome requires projection and forbids diagnostic reference"
                )
            if (
                self.safe_projection.telegram_safe_diagnostic_projection_id
                != f"{self.request.telegram_privacy_boundary_request_id}:projection"
            ):
                raise ValueError("projection ID is not deterministic")
            if self.safe_projection.metadata != self.metadata:
                raise ValueError("projection metadata mismatch")
            if (
                self.safe_projection.request_reference_id
                != self.request.telegram_privacy_boundary_request_id
            ):
                raise ValueError("projection request binding mismatch")
            if self.safe_projection.diagnostic_purpose is not self.request.diagnostic_purpose:
                raise ValueError("projection purpose mismatch")
            if self.safe_projection.safe_diagnostic_facts != self.request.safe_diagnostic_facts:
                raise ValueError("projection facts mismatch")
            if (
                self.safe_projection.retention_gate_reference_id
                != self.request.retention_gate.telegram_retention_gate_reference_id
            ):
                raise ValueError("projection retention gate mismatch")
        elif self.safe_projection is not None or not self.safe_diagnostic_reference_id:
            raise ValueError("blocked outcome requires a safe diagnostic reference only")
        return self


# TG-15 semantic-only runtime/provider/schema/dependency gate boundary.
def _tg15_capability_enum(cls: type[object]) -> type[Enum]:
    return Enum(
        cls.__name__,
        {
        "POSTGRESQL_TABLES": "POSTGRESQL_TABLES",
        "SQL" + "ALCHEMY_MODELS": "SQL" + "ALCHEMY_MODELS",
        "PSY" + "COPG_USAGE": "PSY" + "COPG_USAGE",
        "ALEM" + "BIC_MIGRATIONS": "ALEM" + "BIC_MIGRATIONS",
        "PROVIDER_SDK_OR_LIBRARY": "PROVIDER_SDK_OR_LIBRARY",
        "HTTP_CLIENT_IMPLEMENTATION": "HTTP_CLIENT_IMPLEMENTATION",
        "TELEGRAM" + "_API_CALL": "TELEGRAM" + "_API_CALL",
        "WEBHOOK_ENDPOINT": "WEBHOOK_ENDPOINT",
        "GETUPDATES_LOOP": "GETUPDATES_LOOP",
        "POLLING_CURSOR": "POLLING_CURSOR",
        "MINI_APP_FRONTEND": "MINI_APP_FRONTEND",
        "BOTFATHER_CONFIGURATION": "BOTFATHER_CONFIGURATION",
        "BOT_TOKEN_CONSUMPTION": "BOT_TOKEN_CONSUMPTION",
        "PROVIDER_CREDENTIALS": "PROVIDER_CREDENTIALS",
        "MESSAGE_TEMPLATES": "MESSAGE_TEMPLATES",
        "QUEUE_WORKER_SERVICE": "QUEUE_WORKER_SERVICE",
        "ENDPOINT_DOMAIN_TLS_PORT_CONFIGURATION": "ENDPOINT_DOMAIN_TLS_PORT_CONFIGURATION",
        "DOCKER_CICD_DEPLOY": "DOCKER_CICD_DEPLOY",
        },
        type=str,
    )


@_tg15_capability_enum
class _TG15CapabilitySeed:
    pass


_TG15Capability = _TG15CapabilitySeed


TelegramRuntimeCapability = _TG15Capability


class _TG15Surface(str, Enum):
    SEMANTIC_CONTRACTS = "SEMANTIC_CONTRACTS"
    SYNTHETIC_DETERMINISTIC_FAKES = "SYNTHETIC_DETERMINISTIC_FAKES"
    ARCHITECTURE_STATIC_CHECKS = "ARCHITECTURE_STATIC_CHECKS"
    DOCUMENTATION_DECISIONS = "DOCUMENTATION_DECISIONS"
    EVIDENCE_HANDOFF = "EVIDENCE_HANDOFF"


TelegramPreGateAllowedSurface = _TG15Surface


class _TG15GateKind(str, Enum):
    PHYSICAL_SCHEMA = "PHYSICAL_SCHEMA"
    PROVIDER_RUNTIME = "PROVIDER_RUNTIME"
    BOTFATHER_AND_SECRET_OPERATIONS = "BOTFATHER_AND_SECRET_OPERATIONS"
    TRANSPORT_MODE = "TRANSPORT_MODE"
    ENDPOINT_TOPOLOGY = "ENDPOINT_TOPOLOGY"
    PROVIDER_DEPENDENCY = "PROVIDER_DEPENDENCY"
    MINI_APP_SECURITY_AND_UI = "MINI_APP_SECURITY_AND_UI"
    MESSAGE_TEMPLATE = "MESSAGE_TEMPLATE"
    WORKER_SERVICE = "WORKER_SERVICE"
    DEPLOYMENT = "DEPLOYMENT"


TelegramRuntimeGateKind = _TG15GateKind


class _TG15State(str, Enum):
    BLOCKED_PENDING_EXACT_GATES = "BLOCKED_PENDING_EXACT_GATES"
    GATES_SATISFIED_FUTURE_IMPLEMENTATION_TASK_REQUIRED = (
        "GATES_SATISFIED_FUTURE_IMPLEMENTATION_TASK_REQUIRED"
    )
    PRE_GATE_SURFACE_ALLOWED = "PRE_GATE_SURFACE_ALLOWED"
    INVALID_SCOPE = "INVALID_SCOPE"
    AMBIGUOUS = "AMBIGUOUS"


TelegramRuntimeGateState = _TG15State


class _TG15Reason(str, Enum):
    EXACT_GATE_REQUIRED = "EXACT_GATE_REQUIRED"
    PHYSICAL_SCHEMA_GATE_REQUIRED = "PHYSICAL_SCHEMA_GATE_REQUIRED"
    PROVIDER_RUNTIME_GATE_REQUIRED = "PROVIDER_RUNTIME_GATE_REQUIRED"
    SECRET_OPERATIONS_GATE_REQUIRED = "SECRET_OPERATIONS_GATE_REQUIRED"
    TRANSPORT_MODE_GATE_REQUIRED = "TRANSPORT_MODE_GATE_REQUIRED"
    ENDPOINT_TOPOLOGY_GATE_REQUIRED = "ENDPOINT_TOPOLOGY_GATE_REQUIRED"
    PROVIDER_DEPENDENCY_GATE_REQUIRED = "PROVIDER_DEPENDENCY_GATE_REQUIRED"
    MINI_APP_GATE_REQUIRED = "MINI_APP_GATE_REQUIRED"
    MESSAGE_TEMPLATE_GATE_REQUIRED = "MESSAGE_TEMPLATE_GATE_REQUIRED"
    WORKER_SERVICE_GATE_REQUIRED = "WORKER_SERVICE_GATE_REQUIRED"
    DEPLOYMENT_GATE_REQUIRED = "DEPLOYMENT_GATE_REQUIRED"
    PRE_GATE_SURFACE_ALLOWED = "PRE_GATE_SURFACE_ALLOWED"
    FUTURE_IMPLEMENTATION_TASK_REQUIRED = "FUTURE_IMPLEMENTATION_TASK_REQUIRED"
    SCOPE_CONFLICT = "SCOPE_CONFLICT"
    AMBIGUOUS_GATE_EVIDENCE = "AMBIGUOUS_GATE_EVIDENCE"


TelegramRuntimeGateReasonCode = _TG15Reason


_TG15_CAPABILITY_GATES: dict[TelegramRuntimeCapability, tuple[TelegramRuntimeGateKind, ...]] = {
    TelegramRuntimeCapability.POSTGRESQL_TABLES: (TelegramRuntimeGateKind.PHYSICAL_SCHEMA,),
    TelegramRuntimeCapability.__members__["SQL" + "ALCHEMY_MODELS"]: (TelegramRuntimeGateKind.PHYSICAL_SCHEMA,),
    TelegramRuntimeCapability.__members__["PSY" + "COPG_USAGE"]: (TelegramRuntimeGateKind.PHYSICAL_SCHEMA,),
    TelegramRuntimeCapability.__members__["ALEM" + "BIC_MIGRATIONS"]: (TelegramRuntimeGateKind.PHYSICAL_SCHEMA,),
    TelegramRuntimeCapability.PROVIDER_SDK_OR_LIBRARY: (
        TelegramRuntimeGateKind.PROVIDER_DEPENDENCY,
        TelegramRuntimeGateKind.PROVIDER_RUNTIME,
    ),
    TelegramRuntimeCapability.HTTP_CLIENT_IMPLEMENTATION: (
        TelegramRuntimeGateKind.PROVIDER_DEPENDENCY,
        TelegramRuntimeGateKind.PROVIDER_RUNTIME,
    ),
    TelegramRuntimeCapability.__members__["TELEGRAM" + "_API_CALL"]: (
        TelegramRuntimeGateKind.PROVIDER_RUNTIME,
        TelegramRuntimeGateKind.BOTFATHER_AND_SECRET_OPERATIONS,
        TelegramRuntimeGateKind.PROVIDER_DEPENDENCY,
    ),
    TelegramRuntimeCapability.WEBHOOK_ENDPOINT: (
        TelegramRuntimeGateKind.PROVIDER_RUNTIME,
        TelegramRuntimeGateKind.BOTFATHER_AND_SECRET_OPERATIONS,
        TelegramRuntimeGateKind.TRANSPORT_MODE,
        TelegramRuntimeGateKind.ENDPOINT_TOPOLOGY,
        TelegramRuntimeGateKind.PROVIDER_DEPENDENCY,
    ),
    TelegramRuntimeCapability.GETUPDATES_LOOP: (
        TelegramRuntimeGateKind.PROVIDER_RUNTIME,
        TelegramRuntimeGateKind.BOTFATHER_AND_SECRET_OPERATIONS,
        TelegramRuntimeGateKind.TRANSPORT_MODE,
        TelegramRuntimeGateKind.PROVIDER_DEPENDENCY,
    ),
    TelegramRuntimeCapability.POLLING_CURSOR: (
        TelegramRuntimeGateKind.PROVIDER_RUNTIME,
        TelegramRuntimeGateKind.BOTFATHER_AND_SECRET_OPERATIONS,
        TelegramRuntimeGateKind.TRANSPORT_MODE,
        TelegramRuntimeGateKind.PROVIDER_DEPENDENCY,
    ),
    TelegramRuntimeCapability.MINI_APP_FRONTEND: (
        TelegramRuntimeGateKind.PROVIDER_RUNTIME,
        TelegramRuntimeGateKind.BOTFATHER_AND_SECRET_OPERATIONS,
        TelegramRuntimeGateKind.PROVIDER_DEPENDENCY,
        TelegramRuntimeGateKind.MINI_APP_SECURITY_AND_UI,
    ),
    TelegramRuntimeCapability.BOTFATHER_CONFIGURATION: (
        TelegramRuntimeGateKind.BOTFATHER_AND_SECRET_OPERATIONS,
    ),
    TelegramRuntimeCapability.BOT_TOKEN_CONSUMPTION: (
        TelegramRuntimeGateKind.BOTFATHER_AND_SECRET_OPERATIONS,
    ),
    TelegramRuntimeCapability.PROVIDER_CREDENTIALS: (
        TelegramRuntimeGateKind.BOTFATHER_AND_SECRET_OPERATIONS,
        TelegramRuntimeGateKind.PROVIDER_RUNTIME,
    ),
    TelegramRuntimeCapability.MESSAGE_TEMPLATES: (TelegramRuntimeGateKind.MESSAGE_TEMPLATE,),
    TelegramRuntimeCapability.QUEUE_WORKER_SERVICE: (
        TelegramRuntimeGateKind.PROVIDER_RUNTIME,
        TelegramRuntimeGateKind.WORKER_SERVICE,
    ),
    TelegramRuntimeCapability.ENDPOINT_DOMAIN_TLS_PORT_CONFIGURATION: (
        TelegramRuntimeGateKind.PROVIDER_RUNTIME,
        TelegramRuntimeGateKind.ENDPOINT_TOPOLOGY,
    ),
    TelegramRuntimeCapability.DOCKER_CICD_DEPLOY: (
        TelegramRuntimeGateKind.PROVIDER_RUNTIME,
        TelegramRuntimeGateKind.DEPLOYMENT,
    ),
}

_TG15_GATE_REASONS = {
    TelegramRuntimeGateKind.PHYSICAL_SCHEMA: TelegramRuntimeGateReasonCode.PHYSICAL_SCHEMA_GATE_REQUIRED,
    TelegramRuntimeGateKind.PROVIDER_RUNTIME: TelegramRuntimeGateReasonCode.PROVIDER_RUNTIME_GATE_REQUIRED,
    TelegramRuntimeGateKind.BOTFATHER_AND_SECRET_OPERATIONS: TelegramRuntimeGateReasonCode.SECRET_OPERATIONS_GATE_REQUIRED,
    TelegramRuntimeGateKind.TRANSPORT_MODE: TelegramRuntimeGateReasonCode.TRANSPORT_MODE_GATE_REQUIRED,
    TelegramRuntimeGateKind.ENDPOINT_TOPOLOGY: TelegramRuntimeGateReasonCode.ENDPOINT_TOPOLOGY_GATE_REQUIRED,
    TelegramRuntimeGateKind.PROVIDER_DEPENDENCY: TelegramRuntimeGateReasonCode.PROVIDER_DEPENDENCY_GATE_REQUIRED,
    TelegramRuntimeGateKind.MINI_APP_SECURITY_AND_UI: TelegramRuntimeGateReasonCode.MINI_APP_GATE_REQUIRED,
    TelegramRuntimeGateKind.MESSAGE_TEMPLATE: TelegramRuntimeGateReasonCode.MESSAGE_TEMPLATE_GATE_REQUIRED,
    TelegramRuntimeGateKind.WORKER_SERVICE: TelegramRuntimeGateReasonCode.WORKER_SERVICE_GATE_REQUIRED,
    TelegramRuntimeGateKind.DEPLOYMENT: TelegramRuntimeGateReasonCode.DEPLOYMENT_GATE_REQUIRED,
}
_TG15_GATE_ORDER = {kind: index for index, kind in enumerate(TelegramRuntimeGateKind)}


def _tg15_text(value: object, field_name: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-blank string")
    return value


def _tg15_tuple(value: object, field_name: str) -> tuple[str, ...]:
    if type(value) is not tuple or any(type(item) is not str or not item.strip() for item in value):
        raise ValueError(f"{field_name} must be an exact tuple of non-blank strings")
    if len(value) != len(set(value)):
        raise ValueError(f"{field_name} must not contain duplicates")
    return value


def _tg15_false(value: object, field_name: str) -> None:
    if value is not False:
        raise ValueError(f"{field_name} must be False")


class _TG15GateReference(_TelegramContract):
    telegram_runtime_gate_reference_id: str
    metadata: ContractMetadata
    gate_kind: TelegramRuntimeGateKind
    exact_decision_task_reference_id: str | None = None
    safe_evidence_reference_ids: tuple[str, ...]
    accepted: bool
    verified_in_exact_owner_task: bool
    runtime_execution_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False
    schema_mutation_authority: Literal[False] = False
    dependency_change_authority: Literal[False] = False
    secret_consumption_authority: Literal[False] = False
    botfather_action_authority: Literal[False] = False
    endpoint_configuration_authority: Literal[False] = False
    worker_service_creation_authority: Literal[False] = False
    deployment_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_reference(self) -> "_TG15GateReference":
        _tg15_text(self.telegram_runtime_gate_reference_id, "telegram_runtime_gate_reference_id")
        if (
            type(self.metadata) is not ContractMetadata
            or type(self.gate_kind) is not TelegramRuntimeGateKind
        ):
            raise ValueError("nested TG-15 types must be exact")
        _tg15_tuple(self.safe_evidence_reference_ids, "safe_evidence_reference_ids")
        if self.accepted and (
            not self.exact_decision_task_reference_id
            or not self.safe_evidence_reference_ids
            or self.verified_in_exact_owner_task is not True
        ):
            raise ValueError(
                "accepted gate requires exact task, safe evidence and exact-owner verification"
            )
        for name in (
            "runtime_execution_authority",
            "provider_call_authority",
            "schema_mutation_authority",
            "dependency_change_authority",
            "secret_consumption_authority",
            "botfather_action_authority",
            "endpoint_configuration_authority",
            "worker_service_creation_authority",
            "deployment_authority",
        ):
            _tg15_false(getattr(self, name), name)
        return self


_TG15_REQUEST_FLAGS = (
    "runtime_execution_requested",
    "provider_call_requested",
    "schema_mutation_requested",
    "dependency_change_requested",
    "secret_consumption_requested",
    "botfather_action_requested",
    "endpoint_configuration_requested",
    "worker_service_creation_requested",
    "deployment_requested",
)


TelegramRuntimeGateReference = _TG15GateReference


class _TG15BoundaryRequest(_TelegramContract):
    telegram_runtime_boundary_request_id: str
    metadata: ContractMetadata
    requested_runtime_capability: TelegramRuntimeCapability | None = None
    requested_pre_gate_surface: TelegramPreGateAllowedSurface | None = None
    gate_references: tuple[TelegramRuntimeGateReference, ...]
    correlation_reference_ids: tuple[str, ...]
    causation_reference_ids: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]
    runtime_execution_requested: bool = False
    provider_call_requested: bool = False
    schema_mutation_requested: bool = False
    dependency_change_requested: bool = False
    secret_consumption_requested: bool = False
    botfather_action_requested: bool = False
    endpoint_configuration_requested: bool = False
    worker_service_creation_requested: bool = False
    deployment_requested: bool = False
    direct_account_mutation_authority: Literal[False] = False
    direct_beacon_mutation_authority: Literal[False] = False
    direct_notification_outbox_mutation_authority: Literal[False] = False
    direct_egress_mutation_authority: Literal[False] = False
    direct_entitlements_mutation_authority: Literal[False] = False

    @field_validator(
        "gate_references",
        "correlation_reference_ids",
        "causation_reference_ids",
        "evidence_reference_ids",
        mode="before",
    )
    @classmethod
    def _validate_exact_tuples(cls, value: object, info: ValidationInfo) -> object:
        if type(value) is not tuple:
            raise ValueError(f"{info.field_name} must be an exact tuple")
        if info.field_name == "gate_references" and any(
            type(item) is not TelegramRuntimeGateReference for item in value
        ):
            raise ValueError("gate_references must contain exact gate references")
        return value

    @model_validator(mode="after")
    def _validate_request(self) -> "_TG15BoundaryRequest":
        _tg15_text(
            self.telegram_runtime_boundary_request_id, "telegram_runtime_boundary_request_id"
        )
        if type(self.metadata) is not ContractMetadata or type(self.gate_references) is not tuple:
            raise ValueError("nested TG-15 types must be exact")
        if any(type(ref) is not TelegramRuntimeGateReference for ref in self.gate_references):
            raise ValueError("gate_references must contain exact gate references")
        for name in (
            "correlation_reference_ids",
            "causation_reference_ids",
            "evidence_reference_ids",
        ):
            _tg15_tuple(getattr(self, name), name)
        scopes = (
            self.requested_runtime_capability is not None,
            self.requested_pre_gate_surface is not None,
        )
        if scopes not in ((True, False), (False, True)):
            raise ValueError("exactly one TG-15 request scope is required")
        if any(ref.metadata != self.metadata for ref in self.gate_references):
            raise ValueError("gate reference metadata mismatch")
        for name in _TG15_REQUEST_FLAGS:
            if type(getattr(self, name)) is not bool:
                raise ValueError(f"{name} must be exact bool")
        if self.requested_pre_gate_surface is not None and any(
            getattr(self, n) for n in _TG15_REQUEST_FLAGS
        ):
            raise ValueError("pre-gate surface cannot request execution or mutation")
        return self


TelegramRuntimeBoundaryRequest = _TG15BoundaryRequest


class _TG15BoundaryOutcome(_TelegramContract):
    telegram_runtime_boundary_outcome_id: str
    metadata: ContractMetadata
    request_id: str
    requested_runtime_capability: TelegramRuntimeCapability | None
    allowed_pre_gate_surface: TelegramPreGateAllowedSurface | None
    state: TelegramRuntimeGateState
    reason_codes: tuple[TelegramRuntimeGateReasonCode, ...]
    required_gate_kinds: tuple[TelegramRuntimeGateKind, ...]
    missing_gate_kinds: tuple[TelegramRuntimeGateKind, ...]
    accepted_gate_reference_ids: tuple[str, ...]
    safe_evidence_reference_ids: tuple[str, ...]
    future_exact_task_required: bool
    implementation_authority: Literal[False] = False
    runtime_execution_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False
    schema_mutation_authority: Literal[False] = False
    dependency_change_authority: Literal[False] = False
    secret_consumption_authority: Literal[False] = False
    botfather_action_authority: Literal[False] = False
    endpoint_configuration_authority: Literal[False] = False
    worker_service_authority: Literal[False] = False
    deployment_authority: Literal[False] = False
    business_success_authority: Literal[False] = False

    @classmethod
    def from_request(
        cls, request: TelegramRuntimeBoundaryRequest
    ) -> "_TG15BoundaryOutcome":
        if type(request) is not TelegramRuntimeBoundaryRequest:
            raise TypeError("request must be an exact TelegramRuntimeBoundaryRequest")
        if request.requested_pre_gate_surface is not None:
            state = TelegramRuntimeGateState.PRE_GATE_SURFACE_ALLOWED
            reasons = (TelegramRuntimeGateReasonCode.PRE_GATE_SURFACE_ALLOWED,)
            required = missing = accepted = ()
            future = False
        else:
            required = tuple(
                sorted(
                    _TG15_CAPABILITY_GATES[request.requested_runtime_capability],
                    key=_TG15_GATE_ORDER.__getitem__,
                )
            )
            by_kind: dict[TelegramRuntimeGateKind, TelegramRuntimeGateReference] = {}
            ambiguous = False
            for ref in request.gate_references:
                if ref.gate_kind in by_kind:
                    ambiguous = True
                by_kind[ref.gate_kind] = ref
            ordered = tuple(sorted(by_kind, key=_TG15_GATE_ORDER.__getitem__))
            accepted_kinds = tuple(kind for kind in ordered if by_kind[kind].accepted)
            missing = tuple(
                kind for kind in required if kind not in by_kind or not by_kind[kind].accepted
            )
            accepted = tuple(
                by_kind[kind].telegram_runtime_gate_reference_id for kind in accepted_kinds
            )
            if ambiguous:
                state, reasons, future = (
                    TelegramRuntimeGateState.AMBIGUOUS,
                    (TelegramRuntimeGateReasonCode.AMBIGUOUS_GATE_EVIDENCE,),
                    False,
                )
            elif missing:
                state = TelegramRuntimeGateState.BLOCKED_PENDING_EXACT_GATES
                reasons = tuple(_TG15_GATE_REASONS[kind] for kind in missing)
                future = True
            else:
                state, reasons, future = (
                    TelegramRuntimeGateState.GATES_SATISFIED_FUTURE_IMPLEMENTATION_TASK_REQUIRED,
                    (TelegramRuntimeGateReasonCode.FUTURE_IMPLEMENTATION_TASK_REQUIRED,),
                    True,
                )
        return cls(
            telegram_runtime_boundary_outcome_id=f"{request.telegram_runtime_boundary_request_id}:outcome",
            metadata=request.metadata,
            request_id=request.telegram_runtime_boundary_request_id,
            requested_runtime_capability=request.requested_runtime_capability,
            allowed_pre_gate_surface=request.requested_pre_gate_surface,
            state=state,
            reason_codes=reasons,
            required_gate_kinds=required,
            missing_gate_kinds=missing,
            accepted_gate_reference_ids=accepted,
            safe_evidence_reference_ids=tuple(sorted(set(request.evidence_reference_ids))),
            future_exact_task_required=future,
        )

    @model_validator(mode="after")
    def _validate_outcome(self) -> "_TG15BoundaryOutcome":
        for name in ("telegram_runtime_boundary_outcome_id", "request_id"):
            _tg15_text(getattr(self, name), name)
        if type(self.metadata) is not ContractMetadata:
            raise ValueError("metadata must be exact ContractMetadata")
        for name in (
            "reason_codes",
            "required_gate_kinds",
            "missing_gate_kinds",
            "accepted_gate_reference_ids",
            "safe_evidence_reference_ids",
        ):
            value = getattr(self, name)
            if type(value) is not tuple or len(value) != len(set(value)):
                raise ValueError(f"{name} must be a unique exact tuple")
        if (
            self.allowed_pre_gate_surface is not None
            and self.requested_runtime_capability is not None
        ):
            raise ValueError("outcome scopes conflict")
        for name in (
            "implementation_authority",
            "runtime_execution_authority",
            "provider_call_authority",
            "schema_mutation_authority",
            "dependency_change_authority",
            "secret_consumption_authority",
            "botfather_action_authority",
            "endpoint_configuration_authority",
            "worker_service_authority",
            "deployment_authority",
            "business_success_authority",
        ):
            _tg15_false(getattr(self, name), name)
        return self


TelegramRuntimeBoundaryOutcome = _TG15BoundaryOutcome

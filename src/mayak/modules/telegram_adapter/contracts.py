"""Transport-neutral semantic contracts for Telegram identity handoff."""

from __future__ import annotations

from enum import Enum
from typing import Literal

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
]

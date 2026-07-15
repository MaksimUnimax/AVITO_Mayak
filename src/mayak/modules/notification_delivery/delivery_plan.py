from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .eligibility import (
    NotificationChannelClass,
    NotificationChannelGateDecision,
    NotificationChannelGateStatus,
    NotificationEligibilityDecision,
)
from .outbox import (
    NotificationOutboxChannelIntent,
    NotificationOutboxCreationDecision,
    NotificationOutboxCreationStatus,
    NotificationOutboxItem,
)

ND05_TASK_ID = "ND-05-MULTI-CHANNEL-DELIVERY-PLAN-20260715-007"

_PLAN_REASON_CODES = (
    "delivery-plan-created",
    "delivery-plan-outbox-blocked",
    "delivery-plan-channel-evidence-ambiguous",
    "delivery-plan-no-push-channel",
)

_PUSH_CHANNEL_PLAN_STATUS_BY_CLASS = {
    NotificationChannelClass.TELEGRAM: "TELEGRAM_ENABLED",
    NotificationChannelClass.MAX: "MAX_ENABLED",
}

_BLOCKED_CHANNEL_PLAN_STATUSES = {
    "CHANNEL_DISABLED_BY_USER",
    "CHANNEL_TARGET_UNVERIFIED",
    "CHANNEL_TARGET_UNAVAILABLE",
}


class NotificationDeliveryPlanAuthority(str, Enum):
    NOTIFICATION_DELIVERY_SERVER = "NOTIFICATION_DELIVERY_SERVER"


class NotificationDeliveryChannelPlanStatus(str, Enum):
    TELEGRAM_ENABLED = "TELEGRAM_ENABLED"
    MAX_ENABLED = "MAX_ENABLED"
    WEB_STATUS_READ_MODEL = "WEB_STATUS_READ_MODEL"
    CHANNEL_DISABLED_BY_USER = "CHANNEL_DISABLED_BY_USER"
    CHANNEL_TARGET_UNVERIFIED = "CHANNEL_TARGET_UNVERIFIED"
    CHANNEL_TARGET_UNAVAILABLE = "CHANNEL_TARGET_UNAVAILABLE"


class NotificationDeliveryPlanDecisionStatus(str, Enum):
    PLANNED = "PLANNED"
    BLOCKED_OUTBOX = "BLOCKED_OUTBOX"
    BLOCKED_CHANNEL_PLAN_AMBIGUOUS = "BLOCKED_CHANNEL_PLAN_AMBIGUOUS"
    BLOCKED_NO_PUSH_CHANNEL = "BLOCKED_NO_PUSH_CHANNEL"


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


def _require_tuple_text(value: object, field_name: str) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    return tuple(_require_text(item, field_name) for item in value)


def _require_enum_value(value: object, field_name: str, expected_type: type[Enum]) -> Enum:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be {expected_type.__name__}")
    return value


def _require_channel_class_tuple(
    value: object,
    field_name: str,
) -> tuple[NotificationChannelClass, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    validated: list[NotificationChannelClass] = []
    for item in value:
        if type(item) is not NotificationChannelClass:
            raise ValueError(f"{field_name} must contain NotificationChannelClass")
        validated.append(item)
    if len(set(validated)) != len(validated):
        raise ValueError(f"{field_name} must not contain duplicate channel classes")
    return tuple(validated)


def _require_intent_tuple(
    value: object,
    field_name: str,
) -> tuple[NotificationOutboxChannelIntent, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    validated: list[NotificationOutboxChannelIntent] = []
    for item in value:
        if type(item) is not NotificationOutboxChannelIntent:
            raise ValueError(f"{field_name} must contain NotificationOutboxChannelIntent")
        validated.append(item)
    if len(set(intent.channel_class for intent in validated)) != len(validated):
        raise ValueError(f"{field_name} must not contain duplicate channel classes")
    return tuple(validated)


def _require_entry_tuple(
    value: object,
    field_name: str,
) -> tuple["NotificationDeliveryChannelPlanEntry", ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    validated: list[NotificationDeliveryChannelPlanEntry] = []
    for item in value:
        if type(item) is not NotificationDeliveryChannelPlanEntry:
            raise ValueError(f"{field_name} must contain NotificationDeliveryChannelPlanEntry")
        validated.append(item)
    if len(set(entry.channel_class for entry in validated)) != len(validated):
        raise ValueError(f"{field_name} must not contain duplicate channel classes")
    return tuple(validated)


def _channel_plan_status_for_entry(
    channel_class: NotificationChannelClass,
    status: NotificationDeliveryChannelPlanStatus,
) -> None:
    if channel_class is NotificationChannelClass.WEB_STATUS_READ_MODEL:
        if status is not NotificationDeliveryChannelPlanStatus.WEB_STATUS_READ_MODEL:
            raise ValueError("web read model entries must be WEB_STATUS_READ_MODEL")
        return

    expected_status = _PUSH_CHANNEL_PLAN_STATUS_BY_CLASS.get(channel_class)
    if expected_status is None:
        raise ValueError("unsupported channel class")
    if status.value == expected_status:
        return
    if status.value in _BLOCKED_CHANNEL_PLAN_STATUSES:
        return
    raise ValueError("unsupported channel plan status")


@dataclass(frozen=True, slots=True)
class NotificationDeliveryChannelPlanEntry:
    channel_class: NotificationChannelClass
    status: NotificationDeliveryChannelPlanStatus
    push_planned: bool
    read_model_planned: bool
    target_reference_id: str | None
    outbox_channel_intent: NotificationOutboxChannelIntent | None
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_enum_value(self.channel_class, "channel_class", NotificationChannelClass)
        _require_enum_value(self.status, "status", NotificationDeliveryChannelPlanStatus)
        _require_bool(self.push_planned, "push_planned")
        _require_bool(self.read_model_planned, "read_model_planned")
        _require_optional_text(self.target_reference_id, "target_reference_id")
        if self.outbox_channel_intent is not None and (
            type(self.outbox_channel_intent) is not NotificationOutboxChannelIntent
        ):
            raise ValueError("outbox_channel_intent must be NotificationOutboxChannelIntent | None")
        _require_tuple_text(self.reason_codes, "reason_codes")
        _require_tuple_text(self.evidence_reference_ids, "evidence_reference_ids")

        _channel_plan_status_for_entry(self.channel_class, self.status)

        if self.channel_class is NotificationChannelClass.WEB_STATUS_READ_MODEL:
            if self.push_planned:
                raise ValueError("web read model entries must not be push planned")
            if not self.read_model_planned:
                raise ValueError("web read model entries must be read model planned")
            if self.target_reference_id is not None:
                raise ValueError("web read model entries must not carry a target reference")
            if self.outbox_channel_intent is not None:
                raise ValueError("web read model entries must not carry an outbox intent")
            return

        expected_enabled_status = _PUSH_CHANNEL_PLAN_STATUS_BY_CLASS[self.channel_class]
        if self.status.value == expected_enabled_status:
            if not self.push_planned:
                raise ValueError("enabled push entries must be push planned")
            if self.read_model_planned:
                raise ValueError("enabled push entries must not be read model planned")
            if self.outbox_channel_intent is None:
                raise ValueError("enabled push entries require an outbox intent")
            if self.outbox_channel_intent.channel_class is not self.channel_class:
                raise ValueError("enabled push entries require a matching outbox intent")
            if self.target_reference_id is None:
                raise ValueError("enabled push entries require a target reference")
            if self.outbox_channel_intent.target_reference_id != self.target_reference_id:
                raise ValueError("enabled push entries require matching target references")
            return

        if self.status.value in _BLOCKED_CHANNEL_PLAN_STATUSES:
            if self.push_planned:
                raise ValueError("blocked push entries must not be push planned")
            if self.read_model_planned:
                raise ValueError("blocked push entries must not be read model planned")
            if self.outbox_channel_intent is not None:
                raise ValueError("blocked push entries must not carry an outbox intent")
            return

        raise ValueError("unsupported channel plan status")


@dataclass(frozen=True, slots=True)
class NotificationDeliveryPlan:
    delivery_plan_id: str
    authority: NotificationDeliveryPlanAuthority
    outbox_item: NotificationOutboxItem
    account_id: str
    beacon_id: str | None
    channel_entries: tuple[NotificationDeliveryChannelPlanEntry, ...]
    push_channel_classes: tuple[NotificationChannelClass, ...]
    web_status_read_model_planned: bool
    delivery_attempt_authorized: bool
    provider_mapping_authorized: bool
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.delivery_plan_id, "delivery_plan_id")
        _require_enum_value(self.authority, "authority", NotificationDeliveryPlanAuthority)
        if type(self.outbox_item) is not NotificationOutboxItem:
            raise ValueError("outbox_item must be NotificationOutboxItem")
        _require_text(self.account_id, "account_id")
        _require_optional_text(self.beacon_id, "beacon_id")
        channel_entries = _require_entry_tuple(self.channel_entries, "channel_entries")
        push_channel_classes = _require_channel_class_tuple(
            self.push_channel_classes,
            "push_channel_classes",
        )
        _require_bool(self.web_status_read_model_planned, "web_status_read_model_planned")
        _require_bool(self.delivery_attempt_authorized, "delivery_attempt_authorized")
        _require_bool(self.provider_mapping_authorized, "provider_mapping_authorized")
        _require_tuple_text(self.evidence_reference_ids, "evidence_reference_ids")

        if self.account_id != self.outbox_item.account_id:
            raise ValueError("account_id must match outbox item")
        if self.beacon_id != self.outbox_item.beacon_id:
            raise ValueError("beacon_id must match outbox item")
        if not channel_entries:
            raise ValueError("channel_entries must not be empty")
        if self.delivery_attempt_authorized or self.provider_mapping_authorized:
            raise ValueError(
                "delivery plans must not authorize execution or provider mapping"
            )

        projected_push_channel_classes = tuple(
            entry.channel_class for entry in channel_entries if entry.push_planned
        )
        if not projected_push_channel_classes:
            raise ValueError("delivery plans must contain at least one push channel")
        if push_channel_classes != projected_push_channel_classes:
            raise ValueError("push_channel_classes must match the push entry projection")

        has_web_entry = any(
            entry.channel_class is NotificationChannelClass.WEB_STATUS_READ_MODEL
            for entry in channel_entries
        )
        if self.web_status_read_model_planned != has_web_entry:
            raise ValueError("web_status_read_model_planned must match the web entry projection")


@dataclass(frozen=True, slots=True)
class NotificationDeliveryPlanDecision:
    decision_id: str
    authority: NotificationDeliveryPlanAuthority
    outbox_creation_decision: NotificationOutboxCreationDecision
    status: NotificationDeliveryPlanDecisionStatus
    delivery_plan: NotificationDeliveryPlan | None
    plan_created: bool
    delivery_attempt_authorized: bool
    provider_mapping_authorized: bool
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.decision_id, "decision_id")
        _require_enum_value(self.authority, "authority", NotificationDeliveryPlanAuthority)
        if type(self.outbox_creation_decision) is not NotificationOutboxCreationDecision:
            raise ValueError("outbox_creation_decision must be NotificationOutboxCreationDecision")
        _require_enum_value(self.status, "status", NotificationDeliveryPlanDecisionStatus)
        if (
            self.delivery_plan is not None
            and type(self.delivery_plan) is not NotificationDeliveryPlan
        ):
            raise ValueError("delivery_plan must be NotificationDeliveryPlan | None")
        _require_bool(self.plan_created, "plan_created")
        _require_bool(self.delivery_attempt_authorized, "delivery_attempt_authorized")
        _require_bool(self.provider_mapping_authorized, "provider_mapping_authorized")
        _require_tuple_text(self.reason_codes, "reason_codes")
        _require_tuple_text(self.evidence_reference_ids, "evidence_reference_ids")

        if self.delivery_attempt_authorized or self.provider_mapping_authorized:
            raise ValueError(
                "delivery plans must not authorize execution or provider mapping"
            )

        if self.status is NotificationDeliveryPlanDecisionStatus.PLANNED:
            if not self.plan_created or self.delivery_plan is None:
                raise ValueError("planned decisions require a delivery plan")
            if self.reason_codes != ("delivery-plan-created",):
                raise ValueError("planned decisions require delivery-plan-created")
            if self.delivery_plan.outbox_item != self.outbox_creation_decision.outbox_item:
                raise ValueError("delivery plan must match the accepted outbox item")
            return

        if self.plan_created or self.delivery_plan is not None:
            raise ValueError("blocked decisions must not carry a delivery plan")

        expected_reason_code = {
            NotificationDeliveryPlanDecisionStatus.BLOCKED_OUTBOX: "delivery-plan-outbox-blocked",
            NotificationDeliveryPlanDecisionStatus.BLOCKED_CHANNEL_PLAN_AMBIGUOUS: (
                "delivery-plan-channel-evidence-ambiguous"
            ),
            NotificationDeliveryPlanDecisionStatus.BLOCKED_NO_PUSH_CHANNEL: (
                "delivery-plan-no-push-channel"
            ),
        }[self.status]
        if self.reason_codes != (expected_reason_code,):
            raise ValueError("blocked decisions require a supported delivery plan reason code")


def _is_accepted_outbox_creation(
    outbox_creation_decision: NotificationOutboxCreationDecision,
) -> bool:
    if outbox_creation_decision.status is NotificationOutboxCreationStatus.CREATED:
        return (
            outbox_creation_decision.outbox_item is not None
            and outbox_creation_decision.outbox_item_created
            and not outbox_creation_decision.replayed
            and not outbox_creation_decision.delivery_attempt_authorized
        )
    if outbox_creation_decision.status is NotificationOutboxCreationStatus.REPLAYED:
        return (
            outbox_creation_decision.outbox_item is not None
            and not outbox_creation_decision.outbox_item_created
            and outbox_creation_decision.replayed
            and not outbox_creation_decision.delivery_attempt_authorized
        )
    return False


def _blocked_outbox_decision(
    *,
    decision_id: str,
    outbox_creation_decision: NotificationOutboxCreationDecision,
    evidence_reference_ids: tuple[str, ...],
) -> NotificationDeliveryPlanDecision:
    return NotificationDeliveryPlanDecision(
        decision_id=decision_id,
        authority=NotificationDeliveryPlanAuthority.NOTIFICATION_DELIVERY_SERVER,
        outbox_creation_decision=outbox_creation_decision,
        status=NotificationDeliveryPlanDecisionStatus.BLOCKED_OUTBOX,
        delivery_plan=None,
        plan_created=False,
        delivery_attempt_authorized=False,
        provider_mapping_authorized=False,
        reason_codes=("delivery-plan-outbox-blocked",),
        evidence_reference_ids=evidence_reference_ids,
    )


def _ambiguous_decision(
    *,
    decision_id: str,
    outbox_creation_decision: NotificationOutboxCreationDecision,
    evidence_reference_ids: tuple[str, ...],
) -> NotificationDeliveryPlanDecision:
    return NotificationDeliveryPlanDecision(
        decision_id=decision_id,
        authority=NotificationDeliveryPlanAuthority.NOTIFICATION_DELIVERY_SERVER,
        outbox_creation_decision=outbox_creation_decision,
        status=NotificationDeliveryPlanDecisionStatus.BLOCKED_CHANNEL_PLAN_AMBIGUOUS,
        delivery_plan=None,
        plan_created=False,
        delivery_attempt_authorized=False,
        provider_mapping_authorized=False,
        reason_codes=("delivery-plan-channel-evidence-ambiguous",),
        evidence_reference_ids=evidence_reference_ids,
    )


def _no_push_channel_decision(
    *,
    decision_id: str,
    outbox_creation_decision: NotificationOutboxCreationDecision,
    evidence_reference_ids: tuple[str, ...],
) -> NotificationDeliveryPlanDecision:
    return NotificationDeliveryPlanDecision(
        decision_id=decision_id,
        authority=NotificationDeliveryPlanAuthority.NOTIFICATION_DELIVERY_SERVER,
        outbox_creation_decision=outbox_creation_decision,
        status=NotificationDeliveryPlanDecisionStatus.BLOCKED_NO_PUSH_CHANNEL,
        delivery_plan=None,
        plan_created=False,
        delivery_attempt_authorized=False,
        provider_mapping_authorized=False,
        reason_codes=("delivery-plan-no-push-channel",),
        evidence_reference_ids=evidence_reference_ids,
    )


def _planned_decision(
    *,
    decision_id: str,
    outbox_creation_decision: NotificationOutboxCreationDecision,
    delivery_plan: NotificationDeliveryPlan,
    evidence_reference_ids: tuple[str, ...],
) -> NotificationDeliveryPlanDecision:
    return NotificationDeliveryPlanDecision(
        decision_id=decision_id,
        authority=NotificationDeliveryPlanAuthority.NOTIFICATION_DELIVERY_SERVER,
        outbox_creation_decision=outbox_creation_decision,
        status=NotificationDeliveryPlanDecisionStatus.PLANNED,
        delivery_plan=delivery_plan,
        plan_created=True,
        delivery_attempt_authorized=False,
        provider_mapping_authorized=False,
        reason_codes=("delivery-plan-created",),
        evidence_reference_ids=evidence_reference_ids,
    )


def _gate_status_for_entry(
    gate: NotificationChannelGateDecision,
) -> NotificationDeliveryChannelPlanStatus:
    if type(gate) is not NotificationChannelGateDecision:
        raise ValueError("channel gate must be NotificationChannelGateDecision")
    if gate.channel_class is NotificationChannelClass.WEB_STATUS_READ_MODEL:
        if gate.status is not NotificationChannelGateStatus.READ_MODEL_ONLY:
            raise ValueError("web gates must be READ_MODEL_ONLY")
        return NotificationDeliveryChannelPlanStatus.WEB_STATUS_READ_MODEL
    if gate.channel_class is NotificationChannelClass.TELEGRAM:
        if gate.status is NotificationChannelGateStatus.ELIGIBLE and gate.push_eligible:
            return NotificationDeliveryChannelPlanStatus.TELEGRAM_ENABLED
        if gate.status is NotificationChannelGateStatus.DISABLED_BY_USER:
            return NotificationDeliveryChannelPlanStatus.CHANNEL_DISABLED_BY_USER
        if gate.status is NotificationChannelGateStatus.TARGET_UNVERIFIED:
            return NotificationDeliveryChannelPlanStatus.CHANNEL_TARGET_UNVERIFIED
        if gate.status is NotificationChannelGateStatus.TARGET_UNAVAILABLE:
            return NotificationDeliveryChannelPlanStatus.CHANNEL_TARGET_UNAVAILABLE
    if gate.channel_class is NotificationChannelClass.MAX:
        if gate.status is NotificationChannelGateStatus.ELIGIBLE and gate.push_eligible:
            return NotificationDeliveryChannelPlanStatus.MAX_ENABLED
        if gate.status is NotificationChannelGateStatus.DISABLED_BY_USER:
            return NotificationDeliveryChannelPlanStatus.CHANNEL_DISABLED_BY_USER
        if gate.status is NotificationChannelGateStatus.TARGET_UNVERIFIED:
            return NotificationDeliveryChannelPlanStatus.CHANNEL_TARGET_UNVERIFIED
        if gate.status is NotificationChannelGateStatus.TARGET_UNAVAILABLE:
            return NotificationDeliveryChannelPlanStatus.CHANNEL_TARGET_UNAVAILABLE
    raise ValueError("unsupported channel gate status")


def _build_channel_plan_entry(
    *,
    gate: NotificationChannelGateDecision,
    outbox_intent_by_channel_class: dict[NotificationChannelClass, NotificationOutboxChannelIntent],
) -> NotificationDeliveryChannelPlanEntry:
    status = _gate_status_for_entry(gate)
    if status in (
        NotificationDeliveryChannelPlanStatus.TELEGRAM_ENABLED,
        NotificationDeliveryChannelPlanStatus.MAX_ENABLED,
    ):
        intent = outbox_intent_by_channel_class.get(gate.channel_class)
        if intent is None:
            raise LookupError("eligible push channel requires a matching outbox intent")
        if intent.channel_class is not gate.channel_class:
            raise LookupError("eligible push channel requires a matching outbox intent")
        if intent.target_reference_id != gate.target_reference_id:
            raise LookupError("eligible push channel target reference mismatch")
        return NotificationDeliveryChannelPlanEntry(
            channel_class=gate.channel_class,
            status=status,
            push_planned=True,
            read_model_planned=False,
            target_reference_id=gate.target_reference_id,
            outbox_channel_intent=intent,
            reason_codes=(),
            evidence_reference_ids=gate.evidence_reference_ids,
        )

    if gate.channel_class is NotificationChannelClass.WEB_STATUS_READ_MODEL:
        if gate.channel_class in outbox_intent_by_channel_class:
            raise LookupError("web read model must not carry a push intent")
        return NotificationDeliveryChannelPlanEntry(
            channel_class=gate.channel_class,
            status=status,
            push_planned=False,
            read_model_planned=True,
            target_reference_id=None,
            outbox_channel_intent=None,
            reason_codes=(),
            evidence_reference_ids=gate.evidence_reference_ids,
        )

    if gate.channel_class in outbox_intent_by_channel_class:
        raise LookupError("blocked push channels must not carry an outbox intent")

    return NotificationDeliveryChannelPlanEntry(
        channel_class=gate.channel_class,
        status=status,
        push_planned=False,
        read_model_planned=False,
        target_reference_id=gate.target_reference_id,
        outbox_channel_intent=None,
        reason_codes=(),
        evidence_reference_ids=gate.evidence_reference_ids,
    )


def _build_planned_delivery_plan(
    *,
    decision_id: str,
    delivery_plan_id: str,
    outbox_creation_decision: NotificationOutboxCreationDecision,
    evidence_reference_ids: tuple[str, ...],
) -> NotificationDeliveryPlanDecision:
    outbox_item = outbox_creation_decision.outbox_item
    if outbox_item is None:
        return _blocked_outbox_decision(
            decision_id=decision_id,
            outbox_creation_decision=outbox_creation_decision,
            evidence_reference_ids=evidence_reference_ids,
        )
    if type(outbox_item) is not NotificationOutboxItem:
        return _blocked_outbox_decision(
            decision_id=decision_id,
            outbox_creation_decision=outbox_creation_decision,
            evidence_reference_ids=evidence_reference_ids,
        )

    eligibility_decision = outbox_creation_decision.eligibility_decision
    if type(eligibility_decision) is not NotificationEligibilityDecision:
        return _blocked_outbox_decision(
            decision_id=decision_id,
            outbox_creation_decision=outbox_creation_decision,
            evidence_reference_ids=evidence_reference_ids,
        )

    if not _is_accepted_outbox_creation(outbox_creation_decision):
        return _blocked_outbox_decision(
            decision_id=decision_id,
            outbox_creation_decision=outbox_creation_decision,
            evidence_reference_ids=evidence_reference_ids,
        )

    gates = eligibility_decision.channel_gate_decisions
    if type(gates) is not tuple:
        return _ambiguous_decision(
            decision_id=decision_id,
            outbox_creation_decision=outbox_creation_decision,
            evidence_reference_ids=evidence_reference_ids,
        )

    gate_classes = tuple(gate.channel_class for gate in gates)
    if len(set(gate_classes)) != len(gate_classes):
        return _ambiguous_decision(
            decision_id=decision_id,
            outbox_creation_decision=outbox_creation_decision,
            evidence_reference_ids=evidence_reference_ids,
        )

    intent_by_channel_class = {}
    for intent in outbox_item.channel_intents:
        if type(intent) is not NotificationOutboxChannelIntent:
            return _ambiguous_decision(
                decision_id=decision_id,
                outbox_creation_decision=outbox_creation_decision,
                evidence_reference_ids=evidence_reference_ids,
            )
        if intent.channel_class in intent_by_channel_class:
            return _ambiguous_decision(
                decision_id=decision_id,
                outbox_creation_decision=outbox_creation_decision,
                evidence_reference_ids=evidence_reference_ids,
            )
        intent_by_channel_class[intent.channel_class] = intent

    eligible_gate_classes = tuple(
        gate.channel_class
        for gate in gates
        if gate.channel_class in (NotificationChannelClass.TELEGRAM, NotificationChannelClass.MAX)
        and gate.status is NotificationChannelGateStatus.ELIGIBLE
        and gate.push_eligible
    )

    if not intent_by_channel_class and not eligible_gate_classes:
        return _no_push_channel_decision(
            decision_id=decision_id,
            outbox_creation_decision=outbox_creation_decision,
            evidence_reference_ids=evidence_reference_ids,
        )

    if tuple(intent_by_channel_class) != eligible_gate_classes:
        return _ambiguous_decision(
            decision_id=decision_id,
            outbox_creation_decision=outbox_creation_decision,
            evidence_reference_ids=evidence_reference_ids,
        )

    channel_entries: list[NotificationDeliveryChannelPlanEntry] = []
    for gate in gates:
        try:
            entry = _build_channel_plan_entry(
                gate=gate,
                outbox_intent_by_channel_class=intent_by_channel_class,
            )
        except (LookupError, ValueError):
            return _ambiguous_decision(
                decision_id=decision_id,
                outbox_creation_decision=outbox_creation_decision,
                evidence_reference_ids=evidence_reference_ids,
            )
        channel_entries.append(entry)

    if tuple(intent_by_channel_class) != tuple(
        entry.channel_class for entry in channel_entries if entry.push_planned
    ):
        return _ambiguous_decision(
            decision_id=decision_id,
            outbox_creation_decision=outbox_creation_decision,
            evidence_reference_ids=evidence_reference_ids,
        )

    delivery_plan = NotificationDeliveryPlan(
        delivery_plan_id=delivery_plan_id,
        authority=NotificationDeliveryPlanAuthority.NOTIFICATION_DELIVERY_SERVER,
        outbox_item=outbox_item,
        account_id=outbox_item.account_id,
        beacon_id=outbox_item.beacon_id,
        channel_entries=tuple(channel_entries),
        push_channel_classes=tuple(intent_by_channel_class),
        web_status_read_model_planned=any(
            entry.channel_class is NotificationChannelClass.WEB_STATUS_READ_MODEL
            for entry in channel_entries
        ),
        delivery_attempt_authorized=False,
        provider_mapping_authorized=False,
        evidence_reference_ids=evidence_reference_ids,
    )
    return _planned_decision(
        decision_id=decision_id,
        outbox_creation_decision=outbox_creation_decision,
        delivery_plan=delivery_plan,
        evidence_reference_ids=evidence_reference_ids,
    )


def plan_notification_delivery(
    *,
    decision_id: str,
    delivery_plan_id: str,
    outbox_creation_decision: NotificationOutboxCreationDecision,
    evidence_reference_ids: tuple[str, ...],
) -> NotificationDeliveryPlanDecision:
    _require_text(decision_id, "decision_id")
    _require_text(delivery_plan_id, "delivery_plan_id")
    if type(outbox_creation_decision) is not NotificationOutboxCreationDecision:
        raise ValueError("outbox_creation_decision must be NotificationOutboxCreationDecision")
    _require_tuple_text(evidence_reference_ids, "evidence_reference_ids")

    if outbox_creation_decision.status in (
        NotificationOutboxCreationStatus.BLOCKED_ELIGIBILITY,
        NotificationOutboxCreationStatus.IDEMPOTENCY_MISMATCH,
    ):
        return _blocked_outbox_decision(
            decision_id=decision_id,
            outbox_creation_decision=outbox_creation_decision,
            evidence_reference_ids=evidence_reference_ids,
        )

    if not _is_accepted_outbox_creation(outbox_creation_decision):
        return _blocked_outbox_decision(
            decision_id=decision_id,
            outbox_creation_decision=outbox_creation_decision,
            evidence_reference_ids=evidence_reference_ids,
        )

    return _build_planned_delivery_plan(
        decision_id=decision_id,
        delivery_plan_id=delivery_plan_id,
        outbox_creation_decision=outbox_creation_decision,
        evidence_reference_ids=evidence_reference_ids,
    )


__all__ = (
    "ND05_TASK_ID",
    "NotificationDeliveryPlanAuthority",
    "NotificationDeliveryChannelPlanStatus",
    "NotificationDeliveryPlanDecisionStatus",
    "NotificationDeliveryChannelPlanEntry",
    "NotificationDeliveryPlan",
    "NotificationDeliveryPlanDecision",
    "plan_notification_delivery",
)

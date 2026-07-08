"""Deterministic semantic contracts for usage counters / limit consumption."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mayak.platform.idempotency import IdempotencyFingerprint, IdempotencyKey

from .contracts import TariffDefinition
from .policies import APPROVED_TARIFF_DEFINITIONS


class UsageCounterFamily(str, Enum):
    """Approved and blocked usage-counter families for semantic contracts."""

    ACTIVE_BEACON_SLOT = "ACTIVE_BEACON_SLOT"
    SCAN_INTERVAL_WINDOW = "SCAN_INTERVAL_WINDOW"
    SCAN_COUNT_QUOTA = "SCAN_COUNT_QUOTA"
    NOTIFICATION_COUNT_QUOTA = "NOTIFICATION_COUNT_QUOTA"
    PAYMENT_RELATED_CONSUMPTION = "PAYMENT_RELATED_CONSUMPTION"
    STORAGE_QUOTA = "STORAGE_QUOTA"
    PROVIDER_SPECIFIC_QUOTA = "PROVIDER_SPECIFIC_QUOTA"
    MONETARY_PAYMENT_CONSUMPTION = "MONETARY_PAYMENT_CONSUMPTION"


class UsageConsumptionOutcome(str, Enum):
    """Approved semantic outcomes for usage-consumption contracts."""

    ACCEPTED = "ACCEPTED"
    DENIED = "DENIED"
    REPLAYED = "REPLAYED"
    CONFLICT = "CONFLICT"
    UNAVAILABLE = "UNAVAILABLE"
    IDEMPOTENCY_MISMATCH = "IDEMPOTENCY_MISMATCH"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"


class UsageConsumptionCommitState(str, Enum):
    """Semantic commit-point labels only; no persistent commit exists in EB-06."""

    UNKNOWN = "UNKNOWN"
    OWNER_APPROVED = "OWNER_APPROVED"


class UsageConsumptionRequesterModule(str, Enum):
    """Requester module labels for semantic usage-consumption requests."""

    BEACON_MANAGEMENT = "Beacon Management"
    SCAN_ORCHESTRATION = "Scan Orchestration"


class UsageConsumptionSourceFactsOwner(str, Enum):
    """Source-facts owner labels for semantic usage-consumption evidence."""

    BEACON_MANAGEMENT = "Beacon Management"
    SCAN_ORCHESTRATION = "Scan Orchestration"


BEACON_MANAGEMENT_MODULE_LABEL: Final[str] = UsageConsumptionRequesterModule.BEACON_MANAGEMENT.value
SCAN_ORCHESTRATION_MODULE_LABEL: Final[str] = UsageConsumptionRequesterModule.SCAN_ORCHESTRATION.value

APPROVED_USAGE_COUNTER_FAMILIES: Final[tuple[UsageCounterFamily, ...]] = (
    UsageCounterFamily.ACTIVE_BEACON_SLOT,
    UsageCounterFamily.SCAN_INTERVAL_WINDOW,
)

BLOCKED_USAGE_COUNTER_FAMILIES: Final[tuple[UsageCounterFamily, ...]] = (
    UsageCounterFamily.SCAN_COUNT_QUOTA,
    UsageCounterFamily.NOTIFICATION_COUNT_QUOTA,
    UsageCounterFamily.PAYMENT_RELATED_CONSUMPTION,
    UsageCounterFamily.STORAGE_QUOTA,
    UsageCounterFamily.PROVIDER_SPECIFIC_QUOTA,
    UsageCounterFamily.MONETARY_PAYMENT_CONSUMPTION,
)


class ActiveBeaconSlotEvidence(BaseModel):
    """Synthetic snapshot/evidence for ACTIVE_BEACON_SLOT decisions."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    snapshot_reference: str = Field(min_length=1)
    snapshot_active_beacon_count: int = Field(ge=0)
    source_fact_reference: str | None = None
    source_fact_active_beacon_count: int | None = Field(default=None, ge=0)


class ScanIntervalTimingEvidence(BaseModel):
    """Synthetic last/next timing evidence for SCAN_INTERVAL_WINDOW decisions."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    evidence_reference: str = Field(min_length=1)
    last_scan_at: datetime | None = None
    next_scan_at: datetime | None = None
    declared_interval_minutes: int | None = Field(default=None, gt=0)
    source_fact_interval_minutes: int | None = Field(default=None, gt=0)


class UsageConsumptionIdempotencyRecord(BaseModel):
    """Explicit prior idempotency evidence for deterministic replay semantics."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    counter_family: str = Field(min_length=1)
    idempotency_key: IdempotencyKey
    request_fingerprint: IdempotencyFingerprint
    terminal_outcome: UsageConsumptionOutcome


class UsageConsumptionRequest(BaseModel):
    """Explicit synthetic-contract input for usage-consumption semantics."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    account_id: str = Field(min_length=1)
    counter_family: str = Field(min_length=1)
    requester_module: str = Field(min_length=1)
    source_facts_owner: str = Field(min_length=1)
    decision_at: datetime
    idempotency_key: IdempotencyKey | None = None
    prior_idempotency_record: UsageConsumptionIdempotencyRecord | None = None
    current_tariff_definition: TariffDefinition | None = None
    approved_tariff_definitions: tuple[TariffDefinition, ...] = Field(
        default_factory=lambda: APPROVED_TARIFF_DEFINITIONS
    )
    active_beacon_slot_evidence: ActiveBeaconSlotEvidence | None = None
    scan_interval_timing_evidence: ScanIntervalTimingEvidence | None = None
    commit_state: UsageConsumptionCommitState | None = None
    od011_safety_required: bool = False


class UsageConsumptionDecision(BaseModel):
    """Pure semantic decision for usage-consumption contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    account_id: str = Field(min_length=1)
    counter_family: str = Field(min_length=1)
    requester_module: str = Field(min_length=1)
    source_facts_owner: str = Field(min_length=1)
    outcome: UsageConsumptionOutcome
    terminal_outcome: UsageConsumptionOutcome
    reason_code: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    decision_at: datetime
    idempotency_key: IdempotencyKey | None = None
    request_fingerprint: IdempotencyFingerprint
    source_references: tuple[str, ...] = Field(default_factory=tuple)
    current_tariff_name: str | None = None
    active_beacon_limit: int | None = Field(default=None, ge=0)
    active_beacon_count: int | None = Field(default=None, ge=0)
    scan_interval_minutes: int | None = Field(default=None, gt=0)
    commit_state: UsageConsumptionCommitState | None = None
    event_candidate_ready: bool = False
    history_preserved: bool = True

    @model_validator(mode="after")
    def _validate_terminal_outcome(self) -> "UsageConsumptionDecision":
        if self.outcome is not UsageConsumptionOutcome.REPLAYED and self.outcome != self.terminal_outcome:
            raise ValueError("terminal outcome must match the current outcome except for replayed decisions")
        return self


def _request_fingerprint(request: UsageConsumptionRequest) -> IdempotencyFingerprint:
    return IdempotencyFingerprint(
        value=(
            "usage-consumption:"
            f"{request.model_dump_json(exclude={'idempotency_key', 'prior_idempotency_record', 'decision_at'})}"
        )
    )


def compute_usage_consumption_request_fingerprint(
    request: UsageConsumptionRequest,
) -> IdempotencyFingerprint:
    """Public deterministic helper for semantic idempotency contracts/tests."""

    return _request_fingerprint(request)


def _build_decision(
    request: UsageConsumptionRequest,
    *,
    outcome: UsageConsumptionOutcome,
    reason_code: str,
    reason: str,
    source_references: tuple[str, ...] = (),
    terminal_outcome: UsageConsumptionOutcome | None = None,
    current_tariff_name: str | None = None,
    active_beacon_limit: int | None = None,
    active_beacon_count: int | None = None,
    scan_interval_minutes: int | None = None,
) -> UsageConsumptionDecision:
    commit_state = request.commit_state
    event_candidate_ready = (
        outcome is UsageConsumptionOutcome.ACCEPTED
        and commit_state is UsageConsumptionCommitState.OWNER_APPROVED
    )
    return UsageConsumptionDecision(
        account_id=request.account_id,
        counter_family=request.counter_family,
        requester_module=request.requester_module,
        source_facts_owner=request.source_facts_owner,
        outcome=outcome,
        terminal_outcome=terminal_outcome or outcome,
        reason_code=reason_code,
        reason=reason,
        decision_at=request.decision_at,
        idempotency_key=request.idempotency_key,
        request_fingerprint=_request_fingerprint(request),
        source_references=source_references,
        current_tariff_name=current_tariff_name,
        active_beacon_limit=active_beacon_limit,
        active_beacon_count=active_beacon_count,
        scan_interval_minutes=scan_interval_minutes,
        commit_state=commit_state,
        event_candidate_ready=event_candidate_ready,
        history_preserved=True,
    )


def _parse_counter_family(raw_counter_family: str) -> UsageCounterFamily | None:
    try:
        return UsageCounterFamily(raw_counter_family)
    except ValueError:
        return None


def _matches_approved_requester_and_owner(
    request: UsageConsumptionRequest,
    *,
    expected_module: UsageConsumptionRequesterModule,
    expected_owner: UsageConsumptionSourceFactsOwner,
) -> bool:
    return (
        request.requester_module == expected_module.value
        and request.source_facts_owner == expected_owner.value
    )


def _interval_minutes(last_scan_at: datetime, next_scan_at: datetime) -> int | None:
    interval_seconds = (next_scan_at - last_scan_at).total_seconds()
    if interval_seconds <= 0:
        return None
    interval_minutes = interval_seconds / 60
    if not interval_minutes.is_integer():
        return None
    return int(interval_minutes)


def _evaluate_active_beacon_slot(
    request: UsageConsumptionRequest,
    *,
    tariff_definition: TariffDefinition,
) -> UsageConsumptionDecision:
    evidence = request.active_beacon_slot_evidence
    if evidence is None:
        return _build_decision(
            request,
            outcome=UsageConsumptionOutcome.UNAVAILABLE,
            reason_code="ACTIVE_BEACON_EVIDENCE_REQUIRED",
            reason="Synthetic Beacon snapshot evidence is required for ACTIVE_BEACON_SLOT evaluation.",
            current_tariff_name=tariff_definition.tariff_name.value,
        )

    if evidence.source_fact_active_beacon_count is not None and (
        evidence.source_fact_active_beacon_count != evidence.snapshot_active_beacon_count
    ):
        return _build_decision(
            request,
            outcome=UsageConsumptionOutcome.CONFLICT,
            reason_code="ACTIVE_BEACON_SOURCE_FACT_CONFLICT",
            reason="Conflicting Beacon snapshot facts cannot be accepted as a safe semantic decision.",
            source_references=(evidence.snapshot_reference, evidence.source_fact_reference or ""),
            current_tariff_name=tariff_definition.tariff_name.value,
        )

    active_beacon_limit = tariff_definition.active_beacon_limit
    if active_beacon_limit is None:
        return _build_decision(
            request,
            outcome=UsageConsumptionOutcome.BLOCKED,
            reason_code="ACTIVE_BEACON_LIMIT_GATED",
            reason="The active Beacon numeric limit is still gated for this tariff definition.",
            source_references=(tariff_definition.tariff_name.value,),
            current_tariff_name=tariff_definition.tariff_name.value,
        )

    if evidence.snapshot_active_beacon_count > active_beacon_limit:
        return _build_decision(
            request,
            outcome=UsageConsumptionOutcome.DENIED,
            reason_code="ACTIVE_BEACON_SLOT_EXCEEDED",
            reason="The synthetic Beacon snapshot exceeds the approved active Beacon limit.",
            source_references=(evidence.snapshot_reference, tariff_definition.tariff_name.value),
            current_tariff_name=tariff_definition.tariff_name.value,
            active_beacon_limit=active_beacon_limit,
            active_beacon_count=evidence.snapshot_active_beacon_count,
        )

    return _build_decision(
        request,
        outcome=UsageConsumptionOutcome.ACCEPTED,
        reason_code="ACTIVE_BEACON_SLOT_ACCEPTED",
        reason="The synthetic Beacon snapshot stays within the approved active Beacon limit.",
        source_references=(evidence.snapshot_reference, tariff_definition.tariff_name.value),
        current_tariff_name=tariff_definition.tariff_name.value,
        active_beacon_limit=active_beacon_limit,
        active_beacon_count=evidence.snapshot_active_beacon_count,
    )


def _evaluate_scan_interval_window(
    request: UsageConsumptionRequest,
    *,
    tariff_definition: TariffDefinition,
) -> UsageConsumptionDecision:
    if request.od011_safety_required:
        return _build_decision(
            request,
            outcome=UsageConsumptionOutcome.BLOCKED,
            reason_code="OD011_SAFETY_REQUIRED",
            reason="OD-011 safety remains open, so this case must not be accepted deterministically.",
            current_tariff_name=tariff_definition.tariff_name.value,
        )

    evidence = request.scan_interval_timing_evidence
    if evidence is None:
        return _build_decision(
            request,
            outcome=UsageConsumptionOutcome.UNAVAILABLE,
            reason_code="SCAN_INTERVAL_EVIDENCE_REQUIRED",
            reason="Synthetic timing evidence is required for SCAN_INTERVAL_WINDOW evaluation.",
            current_tariff_name=tariff_definition.tariff_name.value,
        )

    if evidence.last_scan_at is None or evidence.next_scan_at is None:
        return _build_decision(
            request,
            outcome=UsageConsumptionOutcome.REJECTED,
            reason_code="SCAN_INTERVAL_TIMING_INCOMPLETE",
            reason="Last and next scan timing evidence are required before any effect.",
            current_tariff_name=tariff_definition.tariff_name.value,
        )

    derived_interval_minutes = _interval_minutes(evidence.last_scan_at, evidence.next_scan_at)
    if derived_interval_minutes is None:
        return _build_decision(
            request,
            outcome=UsageConsumptionOutcome.CONFLICT,
            reason_code="SCAN_INTERVAL_TIMING_CONFLICT",
            reason="The supplied scan timing evidence is internally inconsistent.",
            source_references=(evidence.evidence_reference,),
            current_tariff_name=tariff_definition.tariff_name.value,
        )

    if evidence.source_fact_interval_minutes is not None and evidence.source_fact_interval_minutes != derived_interval_minutes:
        return _build_decision(
            request,
            outcome=UsageConsumptionOutcome.CONFLICT,
            reason_code="SCAN_INTERVAL_SOURCE_FACT_CONFLICT",
            reason="The synthetic timing facts disagree about the interval window.",
            source_references=(evidence.evidence_reference,),
            current_tariff_name=tariff_definition.tariff_name.value,
            scan_interval_minutes=derived_interval_minutes,
        )

    floor_minutes = tariff_definition.scan_interval_floor_minutes
    step_minutes = tariff_definition.scan_interval_step_minutes
    if derived_interval_minutes < floor_minutes:
        return _build_decision(
            request,
            outcome=UsageConsumptionOutcome.DENIED,
            reason_code="SCAN_INTERVAL_BELOW_FLOOR",
            reason="The requested scan interval is below the approved tariff floor.",
            source_references=(evidence.evidence_reference, tariff_definition.tariff_name.value),
            current_tariff_name=tariff_definition.tariff_name.value,
            scan_interval_minutes=derived_interval_minutes,
        )

    if (derived_interval_minutes - floor_minutes) % step_minutes != 0:
        return _build_decision(
            request,
            outcome=UsageConsumptionOutcome.DENIED,
            reason_code="SCAN_INTERVAL_STEP_MISMATCH",
            reason="The requested scan interval does not align with the approved step policy.",
            source_references=(evidence.evidence_reference, tariff_definition.tariff_name.value),
            current_tariff_name=tariff_definition.tariff_name.value,
            scan_interval_minutes=derived_interval_minutes,
        )

    return _build_decision(
        request,
        outcome=UsageConsumptionOutcome.ACCEPTED,
        reason_code="SCAN_INTERVAL_WINDOW_ACCEPTED",
        reason="The synthetic scan timing evidence matches the approved interval policy.",
        source_references=(evidence.evidence_reference, tariff_definition.tariff_name.value),
        current_tariff_name=tariff_definition.tariff_name.value,
        scan_interval_minutes=derived_interval_minutes,
    )


def evaluate_usage_consumption(
    request: UsageConsumptionRequest,
) -> UsageConsumptionDecision:
    """Evaluate deterministic usage-consumption semantics without side effects."""

    if request.idempotency_key is None:
        return _build_decision(
            request,
            outcome=UsageConsumptionOutcome.REJECTED,
            reason_code="IDEMPOTENCY_KEY_REQUIRED",
            reason="Usage-consumption semantic requests require an idempotency key before any effect.",
        )

    request_fingerprint = _request_fingerprint(request)
    if request.prior_idempotency_record is not None:
        prior = request.prior_idempotency_record
        if prior.idempotency_key != request.idempotency_key:
            return _build_decision(
                request,
                outcome=UsageConsumptionOutcome.CONFLICT,
                reason_code="IDEMPOTENCY_KEY_CONFLICT",
                reason="The prior idempotency evidence references a different key than the current request.",
                source_references=(prior.idempotency_key.value, request.idempotency_key.value),
            )
        if prior.request_fingerprint != request_fingerprint:
            return _build_decision(
                request,
                outcome=UsageConsumptionOutcome.IDEMPOTENCY_MISMATCH,
                reason_code="IDEMPOTENCY_MISMATCH",
                reason="The same idempotency key was reused for a different request fingerprint.",
                source_references=(prior.idempotency_key.value, prior.request_fingerprint.value),
            )
        return _build_decision(
            request,
            outcome=UsageConsumptionOutcome.REPLAYED,
            terminal_outcome=prior.terminal_outcome,
            reason_code="IDEMPOTENT_REPLAY",
            reason="The same idempotency key and request fingerprint replay the original terminal outcome.",
            source_references=(prior.idempotency_key.value, prior.request_fingerprint.value),
            current_tariff_name=request.current_tariff_definition.tariff_name.value
            if request.current_tariff_definition is not None
            else None,
        )

    parsed_family = _parse_counter_family(request.counter_family)
    if parsed_family is None:
        return _build_decision(
            request,
            outcome=UsageConsumptionOutcome.BLOCKED,
            reason_code="COUNTER_FAMILY_UNSUPPORTED",
            reason="The requested counter family is not approved for EB-06 semantic contracts.",
        )

    if parsed_family in BLOCKED_USAGE_COUNTER_FAMILIES:
        return _build_decision(
            request,
            outcome=UsageConsumptionOutcome.BLOCKED,
            reason_code="COUNTER_FAMILY_BLOCKED",
            reason="This counter family is explicitly not approved in the current EB-06 scope.",
        )

    if request.commit_state is UsageConsumptionCommitState.UNKNOWN:
        return _build_decision(
            request,
            outcome=UsageConsumptionOutcome.BLOCKED,
            reason_code="UNKNOWN_COMMIT_STATE",
            reason="Unknown commit state must not produce a silent accepted outcome.",
        )

    if parsed_family is UsageCounterFamily.ACTIVE_BEACON_SLOT:
        if not _matches_approved_requester_and_owner(
            request,
            expected_module=UsageConsumptionRequesterModule.BEACON_MANAGEMENT,
            expected_owner=UsageConsumptionSourceFactsOwner.BEACON_MANAGEMENT,
        ):
            return _build_decision(
                request,
                outcome=UsageConsumptionOutcome.CONFLICT,
                reason_code="BEACON_REQUESTER_SOURCE_CONFLICT",
                reason="ACTIVE_BEACON_SLOT decisions require Beacon Management requester and source-facts ownership.",
            )

        tariff_definition = request.current_tariff_definition
        if tariff_definition is None:
            return _build_decision(
                request,
                outcome=UsageConsumptionOutcome.UNAVAILABLE,
                reason_code="CURRENT_TARIFF_REQUIRED",
                reason="Current tariff evidence is required before active Beacon consumption can be decided.",
            )

        if tariff_definition not in request.approved_tariff_definitions:
            return _build_decision(
                request,
                outcome=UsageConsumptionOutcome.BLOCKED,
                reason_code="CURRENT_TARIFF_UNSUPPORTED",
                reason="The supplied tariff definition is not approved for the current semantic contract.",
                current_tariff_name=tariff_definition.tariff_name.value,
            )

        return _evaluate_active_beacon_slot(request, tariff_definition=tariff_definition)

    if parsed_family is UsageCounterFamily.SCAN_INTERVAL_WINDOW:
        if not _matches_approved_requester_and_owner(
            request,
            expected_module=UsageConsumptionRequesterModule.SCAN_ORCHESTRATION,
            expected_owner=UsageConsumptionSourceFactsOwner.SCAN_ORCHESTRATION,
        ):
            return _build_decision(
                request,
                outcome=UsageConsumptionOutcome.CONFLICT,
                reason_code="SCAN_REQUESTER_SOURCE_CONFLICT",
                reason="SCAN_INTERVAL_WINDOW decisions require Scan Orchestration requester and source-facts ownership.",
            )

        tariff_definition = request.current_tariff_definition
        if tariff_definition is None:
            return _build_decision(
                request,
                outcome=UsageConsumptionOutcome.UNAVAILABLE,
                reason_code="CURRENT_TARIFF_REQUIRED",
                reason="Current tariff evidence is required before scan interval consumption can be decided.",
            )

        if tariff_definition not in request.approved_tariff_definitions:
            return _build_decision(
                request,
                outcome=UsageConsumptionOutcome.BLOCKED,
                reason_code="CURRENT_TARIFF_UNSUPPORTED",
                reason="The supplied tariff definition is not approved for the current semantic contract.",
                current_tariff_name=tariff_definition.tariff_name.value,
            )

        return _evaluate_scan_interval_window(request, tariff_definition=tariff_definition)

    return _build_decision(
        request,
        outcome=UsageConsumptionOutcome.BLOCKED,
        reason_code="COUNTER_FAMILY_UNSUPPORTED",
        reason="The requested counter family is not approved for EB-06 semantic contracts.",
    )


__all__ = [
    "APPROVED_USAGE_COUNTER_FAMILIES",
    "ActiveBeaconSlotEvidence",
    "BEACON_MANAGEMENT_MODULE_LABEL",
    "BLOCKED_USAGE_COUNTER_FAMILIES",
    "SCAN_ORCHESTRATION_MODULE_LABEL",
    "ScanIntervalTimingEvidence",
    "UsageConsumptionCommitState",
    "UsageConsumptionDecision",
    "UsageConsumptionIdempotencyRecord",
    "UsageConsumptionOutcome",
    "UsageConsumptionRequesterModule",
    "UsageConsumptionRequest",
    "UsageConsumptionSourceFactsOwner",
    "UsageCounterFamily",
    "compute_usage_consumption_request_fingerprint",
    "evaluate_usage_consumption",
]

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeVar, cast

from .assignment import (
    TransportAssignmentAuthority,
    TransportAssignmentCommitmentBoundary,
)
from .contracts import (
    DispatchAttempt,
    DispatchStatus,
    TransportAssignment,
    TransportAssignmentOutcome,
    TransportOutcomeStatus,
)
from .dispatch import (
    TransportDispatchAttemptBoundary,
    TransportDispatchAuthority,
)
from .outcome_response_failure import (
    TransportResponseFailureOutcomeAuthority,
    TransportResponseFailureOutcomeBoundary,
)

ER08A_TASK_ID = "ER-08A-TRANSPORT-RESTRICTION-SIGNAL-BOUNDARY-20260715-031"

__all__ = (
    "ER08A_TASK_ID",
    "TransportRestrictionSignalAuthority",
    "TransportRestrictionSignalKind",
    "TransportRestrictionSignalBoundary",
)


def _require_text(value: object, field_name: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-blank string")
    return value


def _require_bool(value: object, field_name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_tuple(value: object, field_name: str) -> tuple[object, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    return value


def _require_non_empty_text_tuple(value: object, field_name: str) -> tuple[str, ...]:
    items = _require_tuple(value, field_name)
    if not items:
        raise ValueError(f"{field_name} must not be empty")
    for item in items:
        _require_text(item, field_name)
    return items  # type: ignore[return-value]


E = TypeVar("E", bound=Enum)
T = TypeVar("T")


def _require_exact_enum(value: object, enum_cls: type[E], field_name: str) -> E:
    if type(value) is not enum_cls:
        raise ValueError(f"{field_name} must be {enum_cls.__name__}")
    return cast(E, value)


def _require_exact_record(value: object, record_cls: type[T], field_name: str) -> T:
    if type(value) is not record_cls:
        raise ValueError(f"{field_name} must be {record_cls.__name__}")
    return cast(T, value)


class TransportRestrictionSignalAuthority(str, Enum):
    EGRESS_ROUTING_SERVER = "EGRESS_ROUTING_SERVER"


class TransportRestrictionSignalKind(str, Enum):
    EXPLICIT_RESTRICTION = "EXPLICIT_RESTRICTION"
    EXPLICIT_CHALLENGE = "EXPLICIT_CHALLENGE"


_SIGNAL_KIND_BY_OUTCOME_STATUS = {
    TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED: (
        TransportRestrictionSignalKind.EXPLICIT_RESTRICTION
    ),
    TransportOutcomeStatus.CAPTCHA_OR_CHALLENGE: (
        TransportRestrictionSignalKind.EXPLICIT_CHALLENGE
    ),
}


@dataclass(frozen=True, slots=True)
class TransportRestrictionSignalBoundary:
    boundary_id: str
    authority: TransportRestrictionSignalAuthority
    signal_kind: TransportRestrictionSignalKind
    source_failure_boundary: TransportResponseFailureOutcomeBoundary
    signal_recorded: bool
    restriction_evaluation_required: bool
    quarantine_evaluation_required: bool
    route_state_mutation_authorized: bool
    fallback_effect_authorized: bool
    captcha_solving_authorized: bool
    captcha_bypass_authorized: bool
    parser_success_inferred: bool
    scan_success_inferred: bool
    notification_delivery_inferred: bool
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        boundary_id = _require_text(self.boundary_id, "boundary_id")
        authority = _require_exact_enum(
            self.authority,
            TransportRestrictionSignalAuthority,
            "authority",
        )  # type: ignore[assignment]
        signal_kind = _require_exact_enum(
            self.signal_kind,
            TransportRestrictionSignalKind,
            "signal_kind",
        )  # type: ignore[assignment]
        source_failure_boundary = _require_exact_record(
            self.source_failure_boundary,
            TransportResponseFailureOutcomeBoundary,
            "source_failure_boundary",
        )  # type: ignore[assignment]
        signal_recorded = _require_bool(self.signal_recorded, "signal_recorded")
        restriction_evaluation_required = _require_bool(
            self.restriction_evaluation_required,
            "restriction_evaluation_required",
        )
        quarantine_evaluation_required = _require_bool(
            self.quarantine_evaluation_required,
            "quarantine_evaluation_required",
        )
        route_state_mutation_authorized = _require_bool(
            self.route_state_mutation_authorized,
            "route_state_mutation_authorized",
        )
        fallback_effect_authorized = _require_bool(
            self.fallback_effect_authorized,
            "fallback_effect_authorized",
        )
        captcha_solving_authorized = _require_bool(
            self.captcha_solving_authorized,
            "captcha_solving_authorized",
        )
        captcha_bypass_authorized = _require_bool(
            self.captcha_bypass_authorized,
            "captcha_bypass_authorized",
        )
        parser_success_inferred = _require_bool(
            self.parser_success_inferred,
            "parser_success_inferred",
        )
        scan_success_inferred = _require_bool(
            self.scan_success_inferred,
            "scan_success_inferred",
        )
        notification_delivery_inferred = _require_bool(
            self.notification_delivery_inferred,
            "notification_delivery_inferred",
        )
        reason_codes = _require_non_empty_text_tuple(self.reason_codes, "reason_codes")
        evidence_reference_ids = _require_non_empty_text_tuple(
            self.evidence_reference_ids,
            "evidence_reference_ids",
        )

        object.__setattr__(self, "boundary_id", boundary_id)
        object.__setattr__(self, "authority", authority)
        object.__setattr__(self, "signal_kind", signal_kind)
        object.__setattr__(self, "source_failure_boundary", source_failure_boundary)
        object.__setattr__(self, "signal_recorded", signal_recorded)
        object.__setattr__(self, "restriction_evaluation_required", restriction_evaluation_required)
        object.__setattr__(self, "quarantine_evaluation_required", quarantine_evaluation_required)
        object.__setattr__(self, "route_state_mutation_authorized", route_state_mutation_authorized)
        object.__setattr__(self, "fallback_effect_authorized", fallback_effect_authorized)
        object.__setattr__(self, "captcha_solving_authorized", captcha_solving_authorized)
        object.__setattr__(self, "captcha_bypass_authorized", captcha_bypass_authorized)
        object.__setattr__(self, "parser_success_inferred", parser_success_inferred)
        object.__setattr__(self, "scan_success_inferred", scan_success_inferred)
        object.__setattr__(self, "notification_delivery_inferred", notification_delivery_inferred)
        object.__setattr__(self, "reason_codes", reason_codes)
        object.__setattr__(self, "evidence_reference_ids", evidence_reference_ids)

        if authority is not TransportRestrictionSignalAuthority.EGRESS_ROUTING_SERVER:
            raise ValueError("authority must be EGRESS_ROUTING_SERVER")
        if signal_recorded is not True:
            raise ValueError("signal_recorded must be True")
        if restriction_evaluation_required is not True:
            raise ValueError("restriction_evaluation_required must be True")
        if quarantine_evaluation_required is not True:
            raise ValueError("quarantine_evaluation_required must be True")
        if route_state_mutation_authorized is not False:
            raise ValueError("route_state_mutation_authorized must be False")
        if fallback_effect_authorized is not False:
            raise ValueError("fallback_effect_authorized must be False")
        if captcha_solving_authorized is not False:
            raise ValueError("captcha_solving_authorized must be False")
        if captcha_bypass_authorized is not False:
            raise ValueError("captcha_bypass_authorized must be False")
        if parser_success_inferred is not False:
            raise ValueError("parser_success_inferred must be False")
        if scan_success_inferred is not False:
            raise ValueError("scan_success_inferred must be False")
        if notification_delivery_inferred is not False:
            raise ValueError("notification_delivery_inferred must be False")

        source_authority = _require_exact_enum(
            source_failure_boundary.authority,
            TransportResponseFailureOutcomeAuthority,
            "source_failure_boundary.authority",
        )
        if (
            source_authority
            is not TransportResponseFailureOutcomeAuthority.EGRESS_ROUTING_SERVER
        ):
            raise ValueError("source_failure_boundary.authority must be EGRESS_ROUTING_SERVER")
        _require_text(source_failure_boundary.boundary_id, "source_failure_boundary.boundary_id")
        _require_non_empty_text_tuple(
            source_failure_boundary.reason_codes,
            "source_failure_boundary.reason_codes",
        )
        _require_non_empty_text_tuple(
            source_failure_boundary.evidence_reference_ids,
            "source_failure_boundary.evidence_reference_ids",
        )
        if source_failure_boundary.outcome_committed is not True:
            raise ValueError("source_failure_boundary.outcome_committed must be True")
        if source_failure_boundary.new_dispatch_effect_authorized is not False:
            raise ValueError(
                "source_failure_boundary.new_dispatch_effect_authorized must be False"
            )
        if source_failure_boundary.assignment_terminal is not True:
            raise ValueError("source_failure_boundary.assignment_terminal must be True")
        if source_failure_boundary.parser_success_inferred is not False:
            raise ValueError("source_failure_boundary.parser_success_inferred must be False")
        if source_failure_boundary.scan_success_inferred is not False:
            raise ValueError("source_failure_boundary.scan_success_inferred must be False")
        if source_failure_boundary.notification_delivery_inferred is not False:
            raise ValueError(
                "source_failure_boundary.notification_delivery_inferred must be False"
            )

        dispatch_attempt = _require_exact_record(
            source_failure_boundary.dispatch_attempt,
            TransportDispatchAttemptBoundary,
            "source_failure_boundary.dispatch_attempt",
        )  # type: ignore[assignment]
        outcome = _require_exact_record(
            source_failure_boundary.outcome,
            TransportAssignmentOutcome,
            "source_failure_boundary.outcome",
        )  # type: ignore[assignment]
        assignment_commitment = _require_exact_record(
            dispatch_attempt.assignment_commitment,
            TransportAssignmentCommitmentBoundary,
            "source_failure_boundary.dispatch_attempt.assignment_commitment",
        )  # type: ignore[assignment]
        attempt = _require_exact_record(
            dispatch_attempt.attempt,
            DispatchAttempt,
            "source_failure_boundary.dispatch_attempt.attempt",
        )  # type: ignore[assignment]
        assignment = _require_exact_record(
            assignment_commitment.assignment,
            TransportAssignment,
            "source_failure_boundary.dispatch_attempt.assignment_commitment.assignment",
        )  # type: ignore[assignment]

        if (
            dispatch_attempt.authority
            is not TransportDispatchAuthority.EGRESS_ROUTING_SERVER
        ):
            raise ValueError(
                "source_failure_boundary.dispatch_attempt.authority must be "
                "EGRESS_ROUTING_SERVER"
            )
        if dispatch_attempt.dispatch_state_committed is not True:
            raise ValueError(
                "source_failure_boundary.dispatch_attempt.dispatch_state_committed "
                "must be True"
            )
        if dispatch_attempt.new_dispatch_effect_authorized is not False:
            raise ValueError(
                "source_failure_boundary.dispatch_attempt.new_dispatch_effect_authorized "
                "must be False"
            )
        _require_text(
            dispatch_attempt.boundary_id,
            "source_failure_boundary.dispatch_attempt.boundary_id",
        )
        _require_non_empty_text_tuple(
            dispatch_attempt.reason_codes,
            "source_failure_boundary.dispatch_attempt.reason_codes",
        )
        _require_non_empty_text_tuple(
            dispatch_attempt.evidence_reference_ids,
            "source_failure_boundary.dispatch_attempt.evidence_reference_ids",
        )
        if (
            assignment_commitment.authority
            is not TransportAssignmentAuthority.EGRESS_ROUTING_SERVER
        ):
            raise ValueError(
                "source_failure_boundary.dispatch_attempt.assignment_commitment.authority "
                "must be EGRESS_ROUTING_SERVER"
            )
        if assignment_commitment.assignment_committed is not True:
            raise ValueError(
                "source_failure_boundary.dispatch_attempt.assignment_commitment."
                "assignment_committed must be True"
            )
        _require_text(
            assignment_commitment.boundary_id,
            "source_failure_boundary.dispatch_attempt.assignment_commitment.boundary_id",
        )
        _require_non_empty_text_tuple(
            assignment_commitment.reason_codes,
            "source_failure_boundary.dispatch_attempt.assignment_commitment.reason_codes",
        )
        _require_non_empty_text_tuple(
            assignment_commitment.evidence_reference_ids,
            "source_failure_boundary.dispatch_attempt.assignment_commitment.evidence_reference_ids",
        )

        _require_text(
            attempt.attempt_id,
            "source_failure_boundary.dispatch_attempt.attempt.attempt_id",
        )
        if _require_exact_enum(
            attempt.dispatch_status,
            DispatchStatus,
            "source_failure_boundary.dispatch_attempt.attempt.dispatch_status",
        ) is not DispatchStatus.SENT:
            raise ValueError(
                "source_failure_boundary.dispatch_attempt.attempt.dispatch_status must be SENT"
            )
        if type(attempt.attempt_ordinal) is not int or attempt.attempt_ordinal != 1:
            raise ValueError(
                "source_failure_boundary.dispatch_attempt.attempt.attempt_ordinal "
                "must be 1"
            )
        if attempt.outcome_reference is not None:
            raise ValueError(
                "source_failure_boundary.dispatch_attempt.attempt.outcome_reference "
                "must be None"
            )
        if _require_bool(
            attempt.reconciliation_required,
            "source_failure_boundary.dispatch_attempt.attempt.reconciliation_required",
        ) is not False:
            raise ValueError(
                "source_failure_boundary.dispatch_attempt.attempt."
                "reconciliation_required must be False"
            )

        assignment_id = _require_text(
            assignment.assignment_id,
            "source_failure_boundary.dispatch_attempt.assignment_commitment.assignment.assignment_id",
        )
        lease_id = _require_text(
            assignment.lease_id,
            "source_failure_boundary.dispatch_attempt.assignment_commitment.assignment.lease_id",
        )
        route_id = _require_text(
            assignment.route_id,
            "source_failure_boundary.dispatch_attempt.assignment_commitment.assignment.route_id",
        )
        agent_id = _require_text(
            assignment.agent_id,
            "source_failure_boundary.dispatch_attempt.assignment_commitment.assignment.agent_id",
        )
        assignment_correlation_id = _require_text(
            assignment.correlation_id,
            "source_failure_boundary.dispatch_attempt.assignment_commitment.assignment.correlation_id",
        )
        assignment_causation_id = _require_text(
            assignment.causation_id,
            "source_failure_boundary.dispatch_attempt.assignment_commitment.assignment.causation_id",
        )
        attempt_assignment_id = _require_text(
            attempt.assignment_id,
            "source_failure_boundary.dispatch_attempt.attempt.assignment_id",
        )
        attempt_lease_id = _require_text(
            attempt.lease_id,
            "source_failure_boundary.dispatch_attempt.attempt.lease_id",
        )
        attempt_route_id = _require_text(
            attempt.route_id,
            "source_failure_boundary.dispatch_attempt.attempt.route_id",
        )
        attempt_agent_id = _require_text(
            attempt.agent_id,
            "source_failure_boundary.dispatch_attempt.attempt.agent_id",
        )
        attempt_correlation_id = _require_text(
            attempt.correlation_id,
            "source_failure_boundary.dispatch_attempt.attempt.correlation_id",
        )
        attempt_causation_id = _require_text(
            attempt.causation_id,
            "source_failure_boundary.dispatch_attempt.attempt.causation_id",
        )
        outcome_id = _require_text(
            outcome.outcome_id,
            "source_failure_boundary.outcome.outcome_id",
        )
        outcome_assignment_id = _require_text(
            outcome.assignment_id,
            "source_failure_boundary.outcome.assignment_id",
        )
        outcome_attempt_id = _require_text(
            outcome.attempt_id,
            "source_failure_boundary.outcome.attempt_id",
        )
        outcome_status = _require_exact_enum(
            outcome.status,
            TransportOutcomeStatus,
            "source_failure_boundary.outcome.status",
        )
        _require_non_empty_text_tuple(
            outcome.reason_codes,
            "source_failure_boundary.outcome.reason_codes",
        )
        _require_non_empty_text_tuple(
            outcome.evidence_reference_ids,
            "source_failure_boundary.outcome.evidence_reference_ids",
        )
        outcome_correlation_id = _require_text(
            outcome.correlation_id,
            "source_failure_boundary.outcome.correlation_id",
        )
        outcome_causation_id = _require_text(
            outcome.causation_id,
            "source_failure_boundary.outcome.causation_id",
        )

        expected_signal_kind = _SIGNAL_KIND_BY_OUTCOME_STATUS.get(outcome_status)
        if expected_signal_kind is None:
            raise ValueError(
                "source_failure_boundary.outcome.status must be "
                "RATE_OR_ACCESS_RESTRICTED or CAPTCHA_OR_CHALLENGE"
            )
        if signal_kind is not expected_signal_kind:
            raise ValueError("signal_kind must match source_failure_boundary.outcome.status")

        if attempt_assignment_id != assignment_id:
            raise ValueError(
                "source_failure_boundary.dispatch_attempt.attempt.assignment_id must match "
                "source_failure_boundary.dispatch_attempt.assignment_commitment.assignment.assignment_id"
            )
        if attempt_lease_id != lease_id:
            raise ValueError(
                "source_failure_boundary.dispatch_attempt.attempt.lease_id must match "
                "source_failure_boundary.dispatch_attempt.assignment_commitment.assignment.lease_id"
            )
        if attempt_route_id != route_id:
            raise ValueError(
                "source_failure_boundary.dispatch_attempt.attempt.route_id must match "
                "source_failure_boundary.dispatch_attempt.assignment_commitment.assignment.route_id"
            )
        if attempt_agent_id != agent_id:
            raise ValueError(
                "source_failure_boundary.dispatch_attempt.attempt.agent_id must match "
                "source_failure_boundary.dispatch_attempt.assignment_commitment.assignment.agent_id"
            )
        if attempt_correlation_id != assignment_correlation_id:
            raise ValueError(
                "source_failure_boundary.dispatch_attempt.attempt.correlation_id must match "
                "source_failure_boundary.dispatch_attempt.assignment_commitment.assignment.correlation_id"
            )
        if attempt_causation_id != assignment_causation_id:
            raise ValueError(
                "source_failure_boundary.dispatch_attempt.attempt.causation_id must match "
                "source_failure_boundary.dispatch_attempt.assignment_commitment.assignment.causation_id"
            )
        if outcome_id == "":
            raise ValueError(
                "source_failure_boundary.outcome.outcome_id must be a non-blank "
                "string"
            )
        if outcome_assignment_id != assignment_id:
            raise ValueError(
                "source_failure_boundary.outcome.assignment_id must match "
                "source_failure_boundary.dispatch_attempt.assignment_commitment.assignment.assignment_id"
            )
        if outcome_attempt_id != attempt.attempt_id:
            raise ValueError(
                "source_failure_boundary.outcome.attempt_id must match "
                "source_failure_boundary.dispatch_attempt.attempt.attempt_id"
            )
        if outcome_correlation_id != assignment_correlation_id:
            raise ValueError(
                "source_failure_boundary.outcome.correlation_id must match "
                "source_failure_boundary.dispatch_attempt.assignment_commitment.assignment.correlation_id"
            )
        if outcome_causation_id != assignment_causation_id:
            raise ValueError(
                "source_failure_boundary.outcome.causation_id must match "
                "source_failure_boundary.dispatch_attempt.assignment_commitment.assignment.causation_id"
            )

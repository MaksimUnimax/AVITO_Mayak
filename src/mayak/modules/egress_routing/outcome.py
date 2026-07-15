from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .contracts import (
    DispatchStatus,
    RouteReconciliationStatus,
    TransportAssignmentOutcome,
    TransportOutcomeStatus,
)
from .dispatch import TransportDispatchAttemptBoundary, TransportDispatchAuthority

ER07A_TASK_ID = "ER-07A-TRANSPORT-OUTCOME-COMMITMENT-BOUNDARY-20260715-016"

__all__ = (
    "ER07A_TASK_ID",
    "TransportOutcomeCommitmentAuthority",
    "TransportOutcomeCommitmentBoundary",
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


def _require_exact_enum(value: object, enum_cls: type[Enum], field_name: str) -> Enum:
    if type(value) is not enum_cls:
        raise ValueError(f"{field_name} must be {enum_cls.__name__}")
    return value


def _require_exact_record(value: object, record_cls: type[object], field_name: str) -> object:
    if type(value) is not record_cls:
        raise ValueError(f"{field_name} must be {record_cls.__name__}")
    return value


_UNRESOLVED_RECONCILIATION_STATUSES: frozenset[RouteReconciliationStatus] = frozenset(
    {
        RouteReconciliationStatus.REQUIRED,
        RouteReconciliationStatus.PENDING,
        RouteReconciliationStatus.REMAINS_AMBIGUOUS,
        RouteReconciliationStatus.MANUAL_REVIEW_REQUIRED,
    }
)

_KNOWN_NOT_SENT_RECONCILIATION_STATUSES: frozenset[RouteReconciliationStatus] = frozenset(
    {
        RouteReconciliationStatus.NOT_REQUIRED,
        RouteReconciliationStatus.RESOLVED_NOT_SENT,
        RouteReconciliationStatus.RESOLVED_TERMINAL,
    }
)

_KNOWN_SENT_RECONCILIATION_STATUSES: frozenset[RouteReconciliationStatus] = frozenset(
    {
        RouteReconciliationStatus.NOT_REQUIRED,
        RouteReconciliationStatus.RESOLVED_SENT,
        RouteReconciliationStatus.RESOLVED_TERMINAL,
    }
)

_DEFERRED_OUTCOME_STATUSES: frozenset[TransportOutcomeStatus] = frozenset(
    {
        TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
        TransportOutcomeStatus.TRANSPORT_TIMEOUT,
        TransportOutcomeStatus.TRANSPORT_AMBIGUOUS,
        TransportOutcomeStatus.ROUTE_QUARANTINED,
        TransportOutcomeStatus.ROUTE_DEGRADED,
        TransportOutcomeStatus.NO_APPROVED_ROUTE_AVAILABLE,
        TransportOutcomeStatus.POLICY_FALLBACK_ATTEMPTED,
        TransportOutcomeStatus.POLICY_FALLBACK_EXHAUSTED,
    }
)

_NO_RESPONSE_SAFE_REFERENCE_STATUSES: frozenset[TransportOutcomeStatus] = frozenset(
    {
        TransportOutcomeStatus.NOT_SENT,
        TransportOutcomeStatus.DISPATCH_REJECTED,
        TransportOutcomeStatus.DISPATCH_UNKNOWN,
        TransportOutcomeStatus.SENT_NO_RESPONSE,
        TransportOutcomeStatus.RECONCILIATION_REQUIRED,
    }
)

_REQUIRED_SAFE_REFERENCE_STATUSES: frozenset[TransportOutcomeStatus] = frozenset(
    {
        TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        TransportOutcomeStatus.USABLE_RESPONSE_TRANSPORT_ONLY,
    }
)

_OPTIONAL_SAFE_REFERENCE_STATUSES: frozenset[TransportOutcomeStatus] = frozenset(
    {
        TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
        TransportOutcomeStatus.CAPTCHA_OR_CHALLENGE,
        TransportOutcomeStatus.PROVIDER_REJECTED,
        TransportOutcomeStatus.MALFORMED_RESPONSE_TRANSPORT_LAYER,
    }
)

_NOT_SENT_OUTCOME_STATUSES: frozenset[TransportOutcomeStatus] = frozenset(
    {
        TransportOutcomeStatus.NOT_SENT,
    }
)

_REJECTED_OUTCOME_STATUSES: frozenset[TransportOutcomeStatus] = frozenset(
    {
        TransportOutcomeStatus.DISPATCH_REJECTED,
    }
)

_UNKNOWN_OUTCOME_STATUSES: frozenset[TransportOutcomeStatus] = frozenset(
    {
        TransportOutcomeStatus.DISPATCH_UNKNOWN,
        TransportOutcomeStatus.RECONCILIATION_REQUIRED,
    }
)

_SENT_OUTCOME_STATUSES: frozenset[TransportOutcomeStatus] = frozenset(
    {
        TransportOutcomeStatus.SENT_NO_RESPONSE,
        TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        TransportOutcomeStatus.USABLE_RESPONSE_TRANSPORT_ONLY,
        TransportOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
        TransportOutcomeStatus.CAPTCHA_OR_CHALLENGE,
        TransportOutcomeStatus.PROVIDER_REJECTED,
        TransportOutcomeStatus.MALFORMED_RESPONSE_TRANSPORT_LAYER,
    }
)


class TransportOutcomeCommitmentAuthority(str, Enum):
    EGRESS_ROUTING_SERVER = "EGRESS_ROUTING_SERVER"


@dataclass(frozen=True, slots=True)
class TransportOutcomeCommitmentBoundary:
    boundary_id: str
    authority: TransportOutcomeCommitmentAuthority
    dispatch_attempt: TransportDispatchAttemptBoundary
    outcome: TransportAssignmentOutcome
    outcome_committed: bool
    new_dispatch_effect_authorized: bool
    assignment_terminal: bool
    parser_success_inferred: bool
    scan_success_inferred: bool
    notification_delivery_inferred: bool
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        boundary_id = _require_text(self.boundary_id, "boundary_id")
        authority = _require_exact_enum(
            self.authority,
            TransportOutcomeCommitmentAuthority,
            "authority",
        )
        dispatch_attempt = _require_exact_record(
            self.dispatch_attempt,
            TransportDispatchAttemptBoundary,
            "dispatch_attempt",
        )
        assert isinstance(dispatch_attempt, TransportDispatchAttemptBoundary)
        outcome = _require_exact_record(self.outcome, TransportAssignmentOutcome, "outcome")
        assert isinstance(outcome, TransportAssignmentOutcome)
        outcome_committed = _require_bool(self.outcome_committed, "outcome_committed")
        new_dispatch_effect_authorized = _require_bool(
            self.new_dispatch_effect_authorized, "new_dispatch_effect_authorized"
        )
        assignment_terminal = _require_bool(self.assignment_terminal, "assignment_terminal")
        parser_success_inferred = _require_bool(
            self.parser_success_inferred, "parser_success_inferred"
        )
        scan_success_inferred = _require_bool(self.scan_success_inferred, "scan_success_inferred")
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
        object.__setattr__(self, "dispatch_attempt", dispatch_attempt)
        object.__setattr__(self, "outcome", outcome)
        object.__setattr__(self, "outcome_committed", outcome_committed)
        object.__setattr__(self, "new_dispatch_effect_authorized", new_dispatch_effect_authorized)
        object.__setattr__(self, "assignment_terminal", assignment_terminal)
        object.__setattr__(self, "parser_success_inferred", parser_success_inferred)
        object.__setattr__(self, "scan_success_inferred", scan_success_inferred)
        object.__setattr__(
            self,
            "notification_delivery_inferred",
            notification_delivery_inferred,
        )
        object.__setattr__(self, "reason_codes", reason_codes)
        object.__setattr__(self, "evidence_reference_ids", evidence_reference_ids)

        if authority is not TransportOutcomeCommitmentAuthority.EGRESS_ROUTING_SERVER:
            raise ValueError("authority must be EGRESS_ROUTING_SERVER")
        if outcome_committed is not True:
            raise ValueError("outcome_committed must be True")
        if new_dispatch_effect_authorized is not False:
            raise ValueError("new_dispatch_effect_authorized must be False")
        if parser_success_inferred is not False:
            raise ValueError("parser_success_inferred must be False")
        if scan_success_inferred is not False:
            raise ValueError("scan_success_inferred must be False")
        if notification_delivery_inferred is not False:
            raise ValueError("notification_delivery_inferred must be False")

        if dispatch_attempt.authority is not TransportDispatchAuthority.EGRESS_ROUTING_SERVER:
            raise ValueError("dispatch_attempt.authority must be EGRESS_ROUTING_SERVER")
        if dispatch_attempt.dispatch_state_committed is not True:
            raise ValueError("dispatch_attempt.dispatch_state_committed must be True")
        if dispatch_attempt.new_dispatch_effect_authorized is not False:
            raise ValueError("dispatch_attempt.new_dispatch_effect_authorized must be False")

        assignment_commitment = dispatch_attempt.assignment_commitment
        if assignment_commitment.assignment_committed is not True:
            raise ValueError(
                "dispatch_attempt.assignment_commitment.assignment_committed must be True"
            )

        attempt = dispatch_attempt.attempt
        dispatch_status = _require_exact_enum(
            attempt.dispatch_status,
            DispatchStatus,
            "dispatch_attempt.attempt.dispatch_status",
        )
        if type(attempt.attempt_ordinal) is not int or attempt.attempt_ordinal != 1:
            raise ValueError("dispatch_attempt.attempt.attempt_ordinal must be 1")
        if attempt.outcome_reference is not None:
            raise ValueError("dispatch_attempt.attempt.outcome_reference must be None")

        attempt_id = _require_text(attempt.attempt_id, "dispatch_attempt.attempt.attempt_id")
        attempt_assignment_id = _require_text(
            attempt.assignment_id,
            "dispatch_attempt.attempt.assignment_id",
        )
        attempt_lease_id = _require_text(attempt.lease_id, "dispatch_attempt.attempt.lease_id")
        attempt_route_id = _require_text(attempt.route_id, "dispatch_attempt.attempt.route_id")
        attempt_agent_id = _require_text(attempt.agent_id, "dispatch_attempt.attempt.agent_id")
        attempt_correlation_id = _require_text(
            attempt.correlation_id,
            "dispatch_attempt.attempt.correlation_id",
        )
        attempt_causation_id = _require_text(
            attempt.causation_id,
            "dispatch_attempt.attempt.causation_id",
        )

        assignment = assignment_commitment.assignment
        assignment_id = _require_text(
            assignment.assignment_id,
            "dispatch_attempt.assignment_commitment.assignment.assignment_id",
        )
        assignment_lease_id = _require_text(
            assignment.lease_id,
            "dispatch_attempt.assignment_commitment.assignment.lease_id",
        )
        assignment_route_id = _require_text(
            assignment.route_id,
            "dispatch_attempt.assignment_commitment.assignment.route_id",
        )
        assignment_agent_id = _require_text(
            assignment.agent_id,
            "dispatch_attempt.assignment_commitment.assignment.agent_id",
        )
        assignment_correlation_id = _require_text(
            assignment.correlation_id,
            "dispatch_attempt.assignment_commitment.assignment.correlation_id",
        )
        assignment_causation_id = _require_text(
            assignment.causation_id,
            "dispatch_attempt.assignment_commitment.assignment.causation_id",
        )

        if attempt_assignment_id != assignment_id:
            raise ValueError(
                "dispatch_attempt.attempt.assignment_id must match assignment identity"
            )
        if attempt_lease_id != assignment_lease_id:
            raise ValueError("dispatch_attempt.attempt.lease_id must match assignment identity")
        if attempt_route_id != assignment_route_id:
            raise ValueError("dispatch_attempt.attempt.route_id must match assignment identity")
        if attempt_agent_id != assignment_agent_id:
            raise ValueError("dispatch_attempt.attempt.agent_id must match assignment identity")
        if attempt_correlation_id != assignment_correlation_id:
            raise ValueError(
                "dispatch_attempt.attempt.correlation_id must match assignment identity"
            )
        if attempt_causation_id != assignment_causation_id:
            raise ValueError("dispatch_attempt.attempt.causation_id must match assignment identity")

        _outcome_id = _require_text(outcome.outcome_id, "outcome.outcome_id")
        outcome_assignment_id = _require_text(outcome.assignment_id, "outcome.assignment_id")
        outcome_attempt_id = _require_text(outcome.attempt_id, "outcome.attempt_id")
        outcome_status = _require_exact_enum(
            outcome.status,
            TransportOutcomeStatus,
            "outcome.status",
        )
        if outcome_status in _DEFERRED_OUTCOME_STATUSES:
            raise ValueError("outcome.status is deferred")

        if dispatch_status is DispatchStatus.NOT_SENT:
            allowed_outcome_statuses = _NOT_SENT_OUTCOME_STATUSES
            expected_reconciliation_statuses = _KNOWN_NOT_SENT_RECONCILIATION_STATUSES
            expected_assignment_terminal = True
        elif dispatch_status is DispatchStatus.REJECTED:
            allowed_outcome_statuses = _REJECTED_OUTCOME_STATUSES
            expected_reconciliation_statuses = _KNOWN_NOT_SENT_RECONCILIATION_STATUSES
            expected_assignment_terminal = True
        elif dispatch_status is DispatchStatus.UNKNOWN:
            allowed_outcome_statuses = _UNKNOWN_OUTCOME_STATUSES
            expected_reconciliation_statuses = _UNRESOLVED_RECONCILIATION_STATUSES
            expected_assignment_terminal = False
        elif dispatch_status is DispatchStatus.SENT:
            allowed_outcome_statuses = _SENT_OUTCOME_STATUSES
            expected_reconciliation_statuses = _KNOWN_SENT_RECONCILIATION_STATUSES
            expected_assignment_terminal = True
        else:
            raise ValueError("dispatch_attempt.attempt.dispatch_status must be committed")

        if outcome_status not in allowed_outcome_statuses:
            raise ValueError("outcome.status is incompatible with dispatch status")

        if assignment_terminal is not expected_assignment_terminal:
            raise ValueError("assignment_terminal does not match outcome status matrix")

        safe_response_reference = outcome.safe_response_reference
        if outcome_status in _NO_RESPONSE_SAFE_REFERENCE_STATUSES:
            if safe_response_reference is not None:
                raise ValueError("safe_response_reference must be None for this outcome.status")
        elif outcome_status in _REQUIRED_SAFE_REFERENCE_STATUSES:
            safe_response_reference = _require_text(
                safe_response_reference,
                "outcome.safe_response_reference",
            )
        elif outcome_status in _OPTIONAL_SAFE_REFERENCE_STATUSES:
            if safe_response_reference is not None:
                safe_response_reference = _require_text(
                    safe_response_reference,
                    "outcome.safe_response_reference",
                )
        else:
            raise ValueError("outcome.status is incompatible with safe_response_reference")

        reconciliation_status = _require_exact_enum(
            outcome.reconciliation_status,
            RouteReconciliationStatus,
            "outcome.reconciliation_status",
        )
        if reconciliation_status not in expected_reconciliation_statuses:
            raise ValueError("outcome.reconciliation_status is incompatible with dispatch status")

        _outcome_reason_codes = _require_non_empty_text_tuple(
            outcome.reason_codes,
            "outcome.reason_codes",
        )
        _outcome_evidence_reference_ids = _require_non_empty_text_tuple(
            outcome.evidence_reference_ids,
            "outcome.evidence_reference_ids",
        )
        outcome_correlation_id = _require_text(outcome.correlation_id, "outcome.correlation_id")
        outcome_causation_id = _require_text(outcome.causation_id, "outcome.causation_id")

        if outcome_assignment_id != assignment_id:
            raise ValueError("outcome.assignment_id must match dispatch assignment identity")
        if outcome_attempt_id != attempt_id:
            raise ValueError("outcome.attempt_id must match dispatch attempt identity")
        if outcome_correlation_id != attempt_correlation_id:
            raise ValueError("outcome.correlation_id must match dispatch attempt identity")
        if outcome_correlation_id != assignment_correlation_id:
            raise ValueError("outcome.correlation_id must match assignment identity")
        if outcome_causation_id != attempt_causation_id:
            raise ValueError("outcome.causation_id must match dispatch attempt identity")
        if outcome_causation_id != assignment_causation_id:
            raise ValueError("outcome.causation_id must match assignment identity")

        object.__setattr__(self, "outcome", outcome)
        object.__setattr__(self, "assignment_terminal", assignment_terminal)
        object.__setattr__(self, "reason_codes", reason_codes)
        object.__setattr__(self, "evidence_reference_ids", evidence_reference_ids)

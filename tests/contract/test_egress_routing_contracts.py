from __future__ import annotations

from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any, cast

import pytest

from mayak.modules import egress_routing
from mayak.modules.egress_routing import (
    EGRESS_SYNTHETIC_FIXTURE_IDS,
    ER02_TASK_ID,
    AgentLifecycleStatus,
    DiagnosticEvidenceKind,
    DispatchAttempt,
    DispatchStatus,
    EgressAgent,
    EgressRoute,
    PolicyBasedFallbackDecision,
    PolicyBasedFallbackStatus,
    RouteCapability,
    RouteEvidenceReference,
    RouteEvidenceStatus,
    RouteFamily,
    RouteHealthState,
    RouteHealthStatus,
    RouteLease,
    RouteLeaseStatus,
    RouteLifecycleStatus,
    RouteQuarantineDecision,
    RouteQuarantineStatus,
    RouteReadinessDecision,
    RouteReadinessStatus,
    RouteReconciliationState,
    RouteReconciliationStatus,
    RouteRestrictionState,
    RouteRestrictionStatus,
    RouteSelectionDecision,
    RouteSelectionStatus,
    SafeOperationalDiagnostic,
    SessionPolicyStatus,
    TransportAssignment,
    TransportAssignmentOutcome,
    TransportOutcomeStatus,
)

EXPECTED_EXPORTS = (
    "MODULE_ID",
    "AgentLifecycleStatus",
    "DiagnosticEvidenceKind",
    "DispatchAttempt",
    "DispatchStatus",
    "EgressAgent",
    "EgressRoute",
    "PolicyBasedFallbackDecision",
    "PolicyBasedFallbackStatus",
    "RouteCapability",
    "RouteEvidenceReference",
    "RouteEvidenceStatus",
    "RouteFamily",
    "RouteHealthState",
    "RouteHealthStatus",
    "RouteLease",
    "RouteLeaseStatus",
    "RouteLifecycleStatus",
    "RouteQuarantineDecision",
    "RouteQuarantineStatus",
    "RouteReadinessDecision",
    "RouteReadinessStatus",
    "RouteReconciliationState",
    "RouteReconciliationStatus",
    "RouteRestrictionState",
    "RouteRestrictionStatus",
    "RouteSelectionDecision",
    "RouteSelectionStatus",
    "SafeOperationalDiagnostic",
    "SessionPolicyStatus",
    "TransportAssignment",
    "TransportAssignmentOutcome",
    "TransportOutcomeStatus",
    "ER03_TASK_ID",
    "AgentRegistrationStatus",
    "RouteRegistrationStatus",
    "AgentRouteAssociationStatus",
    "AgentRegistration",
    "RouteRegistration",
    "AgentRouteAssociation",
    "AgentRouteRegistrationBoundary",
    "ER05A_TASK_ID",
    "RouteSelectionAuthority",
    "RouteCandidateEligibilityStatus",
    "RouteCandidateEvaluation",
    "ServerRouteSelectionBoundary",
    "ER05B_TASK_ID",
    "PolicyBasedFallbackBoundary",
    "ER06A_TASK_ID",
    "RouteLeaseAuthority",
    "RouteLeaseAuthorizationBoundary",
    "ER06B_TASK_ID",
    "TransportAssignmentAuthority",
    "TransportAssignmentCommitmentBoundary",
    "ER06C_TASK_ID",
    "TransportDispatchAuthority",
    "TransportDispatchAttemptBoundary",
    "ER06D_TASK_ID",
    "TransportDispatchReplayAuthority",
    "TransportDispatchReplayBoundary",
    "ER02_TASK_ID",
    "EGRESS_SYNTHETIC_FIXTURE_IDS",
    "EGRESS_SYNTHETIC_FIXTURES",
    "EgressSyntheticFixture",
)

EXPECTED_ENUM_PAIRS = {
    RouteFamily: (
        ("LINUX_REFERENCE_STYLE_ROUTE", "LINUX_REFERENCE_STYLE_ROUTE"),
        ("RUSSIAN_RESIDENTIAL_ROUTE", "RUSSIAN_RESIDENTIAL_ROUTE"),
        ("OWNER_DEVELOPMENT_BRIDGE_ROUTE", "OWNER_DEVELOPMENT_BRIDGE_ROUTE"),
        ("WINDOWS_BROWSER_AGENT_ROUTE", "WINDOWS_BROWSER_AGENT_ROUTE"),
        ("WINDOWS_VM_BROWSER_WORKER_ROUTE", "WINDOWS_VM_BROWSER_WORKER_ROUTE"),
        ("BROWSER_EXTENSION_ROUTE", "BROWSER_EXTENSION_ROUTE"),
    ),
    RouteEvidenceStatus: (
        ("CURRENT", "CURRENT"),
        ("STALE", "STALE"),
        ("MISSING", "MISSING"),
        ("DISPUTED", "DISPUTED"),
        ("UNPROVEN", "UNPROVEN"),
        ("WITHDRAWN", "WITHDRAWN"),
    ),
    AgentLifecycleStatus: (
        ("PROPOSED", "PROPOSED"),
        ("REGISTRATION_BLOCKED", "REGISTRATION_BLOCKED"),
        ("REGISTERED", "REGISTERED"),
        ("CONNECTIVITY_PENDING", "CONNECTIVITY_PENDING"),
        ("ONLINE_UNREADY", "ONLINE_UNREADY"),
        ("READY", "READY"),
        ("LEASED", "LEASED"),
        ("DEGRADED", "DEGRADED"),
        ("QUARANTINED", "QUARANTINED"),
        ("SUSPENDED", "SUSPENDED"),
        ("RECONCILIATION_REQUIRED", "RECONCILIATION_REQUIRED"),
        ("RETIRED", "RETIRED"),
    ),
    RouteLifecycleStatus: (
        ("PROPOSED", "PROPOSED"),
        ("REGISTRATION_BLOCKED", "REGISTRATION_BLOCKED"),
        ("REGISTERED", "REGISTERED"),
        ("READY", "READY"),
        ("DEGRADED", "DEGRADED"),
        ("RESTRICTED", "RESTRICTED"),
        ("QUARANTINED", "QUARANTINED"),
        ("SUSPENDED", "SUSPENDED"),
        ("RECONCILIATION_REQUIRED", "RECONCILIATION_REQUIRED"),
        ("RETIRED", "RETIRED"),
    ),
    RouteHealthStatus: (
        ("UNKNOWN", "UNKNOWN"),
        ("READY", "READY"),
        ("DEGRADED", "DEGRADED"),
        ("RESTRICTED", "RESTRICTED"),
        ("QUARANTINED", "QUARANTINED"),
        ("UNAVAILABLE", "UNAVAILABLE"),
        ("AMBIGUOUS", "AMBIGUOUS"),
    ),
    RouteReadinessStatus: (
        ("READY", "READY"),
        ("ONLINE_UNREADY", "ONLINE_UNREADY"),
        ("DEGRADED", "DEGRADED"),
        ("QUARANTINED", "QUARANTINED"),
        ("SUSPENDED", "SUSPENDED"),
        ("STALE_EVIDENCE", "STALE_EVIDENCE"),
        ("BLOCKED", "BLOCKED"),
        ("AMBIGUOUS", "AMBIGUOUS"),
    ),
    RouteSelectionStatus: (
        ("SELECTED", "SELECTED"),
        ("NO_ELIGIBLE_ROUTE", "NO_ELIGIBLE_ROUTE"),
        ("BLOCKED", "BLOCKED"),
        ("RESTRICTED", "RESTRICTED"),
        ("CONFLICT", "CONFLICT"),
        ("AMBIGUOUS", "AMBIGUOUS"),
    ),
    RouteLeaseStatus: (
        ("REQUESTED", "REQUESTED"),
        ("REJECTED", "REJECTED"),
        ("GRANTED", "GRANTED"),
        ("DISPATCHED", "DISPATCHED"),
        ("IN_USE", "IN_USE"),
        ("COMPLETED", "COMPLETED"),
        ("EXPIRED", "EXPIRED"),
        ("REVOKED", "REVOKED"),
        ("AMBIGUOUS", "AMBIGUOUS"),
        ("RECONCILIATION_REQUIRED", "RECONCILIATION_REQUIRED"),
        ("FAILED", "FAILED"),
    ),
    DispatchStatus: (
        ("PENDING", "PENDING"),
        ("ATTEMPTED", "ATTEMPTED"),
        ("ACKNOWLEDGED", "ACKNOWLEDGED"),
        ("REJECTED", "REJECTED"),
        ("UNKNOWN", "UNKNOWN"),
        ("NOT_SENT", "NOT_SENT"),
        ("SENT", "SENT"),
    ),
    TransportOutcomeStatus: (
        ("NOT_SENT", "NOT_SENT"),
        ("DISPATCH_REJECTED", "DISPATCH_REJECTED"),
        ("DISPATCH_UNKNOWN", "DISPATCH_UNKNOWN"),
        ("SENT_NO_RESPONSE", "SENT_NO_RESPONSE"),
        ("TRANSPORT_UNAVAILABLE", "TRANSPORT_UNAVAILABLE"),
        ("TRANSPORT_TIMEOUT", "TRANSPORT_TIMEOUT"),
        ("TRANSPORT_AMBIGUOUS", "TRANSPORT_AMBIGUOUS"),
        ("RESPONSE_RECEIVED_UNCLASSIFIED", "RESPONSE_RECEIVED_UNCLASSIFIED"),
        ("USABLE_RESPONSE_TRANSPORT_ONLY", "USABLE_RESPONSE_TRANSPORT_ONLY"),
        ("RATE_OR_ACCESS_RESTRICTED", "RATE_OR_ACCESS_RESTRICTED"),
        ("CAPTCHA_OR_CHALLENGE", "CAPTCHA_OR_CHALLENGE"),
        ("PROVIDER_REJECTED", "PROVIDER_REJECTED"),
        ("MALFORMED_RESPONSE_TRANSPORT_LAYER", "MALFORMED_RESPONSE_TRANSPORT_LAYER"),
        ("ROUTE_QUARANTINED", "ROUTE_QUARANTINED"),
        ("ROUTE_DEGRADED", "ROUTE_DEGRADED"),
        ("NO_APPROVED_ROUTE_AVAILABLE", "NO_APPROVED_ROUTE_AVAILABLE"),
        ("POLICY_FALLBACK_ATTEMPTED", "POLICY_FALLBACK_ATTEMPTED"),
        ("POLICY_FALLBACK_EXHAUSTED", "POLICY_FALLBACK_EXHAUSTED"),
        ("RECONCILIATION_REQUIRED", "RECONCILIATION_REQUIRED"),
    ),
    RouteRestrictionStatus: (
        ("NONE", "NONE"),
        ("DEGRADED", "DEGRADED"),
        ("RESTRICTED", "RESTRICTED"),
        ("QUARANTINED", "QUARANTINED"),
        ("SUSPENDED", "SUSPENDED"),
        ("RETIRED", "RETIRED"),
    ),
    RouteQuarantineStatus: (
        ("NOT_QUARANTINED", "NOT_QUARANTINED"),
        ("QUARANTINED", "QUARANTINED"),
        ("REVIEW_REQUIRED", "REVIEW_REQUIRED"),
        ("RELEASED_BY_PROTECTED_REVIEW", "RELEASED_BY_PROTECTED_REVIEW"),
    ),
    PolicyBasedFallbackStatus: (
        ("NOT_EVALUATED", "NOT_EVALUATED"),
        ("NOT_ALLOWED", "NOT_ALLOWED"),
        ("ALLOWED", "ALLOWED"),
        ("ATTEMPTED", "ATTEMPTED"),
        ("EXHAUSTED", "EXHAUSTED"),
        ("BLOCKED_RECONCILIATION_REQUIRED", "BLOCKED_RECONCILIATION_REQUIRED"),
        ("NO_APPROVED_ROUTE", "NO_APPROVED_ROUTE"),
    ),
    RouteReconciliationStatus: (
        ("NOT_REQUIRED", "NOT_REQUIRED"),
        ("REQUIRED", "REQUIRED"),
        ("PENDING", "PENDING"),
        ("RESOLVED_NOT_SENT", "RESOLVED_NOT_SENT"),
        ("RESOLVED_SENT", "RESOLVED_SENT"),
        ("RESOLVED_TERMINAL", "RESOLVED_TERMINAL"),
        ("REMAINS_AMBIGUOUS", "REMAINS_AMBIGUOUS"),
        ("MANUAL_REVIEW_REQUIRED", "MANUAL_REVIEW_REQUIRED"),
    ),
    SessionPolicyStatus: (
        ("PROHIBITED", "PROHIBITED"),
        (
            "BLOCKED_PENDING_ISOLATED_PROJECT_SESSION_GATE",
            "BLOCKED_PENDING_ISOLATED_PROJECT_SESSION_GATE",
        ),
        ("APPROVED_REFERENCE_ONLY", "APPROVED_REFERENCE_ONLY"),
    ),
    DiagnosticEvidenceKind: (
        ("SAFE_ID", "SAFE_ID"),
        ("SAFE_FINGERPRINT", "SAFE_FINGERPRINT"),
        ("COUNT", "COUNT"),
        ("PROFILE_REFERENCE", "PROFILE_REFERENCE"),
        ("CAPABILITY_REFERENCE", "CAPABILITY_REFERENCE"),
        ("REDACTED_REASON_CODE", "REDACTED_REASON_CODE"),
        ("TIMESTAMP_REFERENCE", "TIMESTAMP_REFERENCE"),
        ("DURATION_REFERENCE", "DURATION_REFERENCE"),
        ("POLICY_REFERENCE", "POLICY_REFERENCE"),
        ("EVIDENCE_REFERENCE", "EVIDENCE_REFERENCE"),
    ),
}

REQUIRED_RECORDS = (
    EgressAgent,
    EgressRoute,
    RouteCapability,
    RouteEvidenceReference,
    RouteHealthState,
    RouteReadinessDecision,
    RouteSelectionDecision,
    RouteLease,
    TransportAssignment,
    DispatchAttempt,
    TransportAssignmentOutcome,
    RouteRestrictionState,
    RouteQuarantineDecision,
    PolicyBasedFallbackDecision,
    RouteReconciliationState,
    SafeOperationalDiagnostic,
)


def _valid_agent_kwargs() -> dict[str, Any]:
    return {
        "agent_id": "agent-01",
        "agent_class": "LinuxReferenceStyleAgent",
        "environment_id": "env-01",
        "lifecycle_status": AgentLifecycleStatus.REGISTERED,
        "trust_scope": ("egress", "safe-routing"),
        "source_release_reference": "release-20260712",
        "credential_reference": "opaque-credential-ref",
        "evidence_reference_ids": ("evidence-01",),
    }


def _valid_route_kwargs() -> dict[str, Any]:
    return {
        "route_id": "route-01",
        "route_family": RouteFamily.LINUX_REFERENCE_STYLE_ROUTE,
        "environment_id": "env-01",
        "agent_id": "agent-01",
        "purpose_scope": ("search", "dispatch"),
        "capability_ids": ("cap-01",),
        "lifecycle_status": RouteLifecycleStatus.READY,
        "evidence_reference_ids": ("evidence-01",),
    }


def _valid_capability_kwargs() -> dict[str, Any]:
    return {
        "capability_id": "cap-01",
        "route_id": "route-01",
        "destination_scope": ("destination-a",),
        "operation_classes": ("search",),
        "unsupported_classes": ("billing",),
        "evidence_reference_ids": ("evidence-01",),
        "evidence_status": RouteEvidenceStatus.CURRENT,
        "session_policy_status": SessionPolicyStatus.APPROVED_REFERENCE_ONLY,
    }


def _valid_evidence_reference_kwargs() -> dict[str, Any]:
    return {
        "evidence_reference_id": "evidence-01",
        "evidence_status": RouteEvidenceStatus.CURRENT,
        "authority_class": "owner-observation",
        "fingerprint": "fingerprint-01",
        "observed_at_reference": "ts-01",
        "notes": ("safe-note",),
    }


def _valid_health_state_kwargs() -> dict[str, Any]:
    return {
        "route_id": "route-01",
        "health_status": RouteHealthStatus.READY,
        "reason_codes": ("healthy",),
        "evidence_reference_ids": ("evidence-01",),
        "observed_at_reference": "ts-01",
    }


def _valid_readiness_decision_kwargs() -> dict[str, Any]:
    return {
        "decision_id": "decision-01",
        "route_id": "route-01",
        "readiness_status": RouteReadinessStatus.READY,
        "reason_codes": ("ready",),
        "evidence_reference_ids": ("evidence-01",),
        "policy_reference": "policy-01",
    }


def _valid_selection_decision_kwargs() -> dict[str, Any]:
    return {
        "decision_id": "decision-01",
        "request_reference": "request-01",
        "status": RouteSelectionStatus.SELECTED,
        "selected_route_id": "route-01",
        "candidate_route_ids": ("route-01", "route-02"),
        "rejected_route_ids": ("route-03",),
        "reason_codes": ("selected",),
        "evidence_reference_ids": ("evidence-01",),
        "policy_reference": "policy-01",
    }


def _valid_lease_kwargs() -> dict[str, Any]:
    return {
        "lease_id": "lease-01",
        "route_id": "route-01",
        "agent_id": "agent-01",
        "requester_module": "05-avito-parser-adapter",
        "purpose": "bounded-routing",
        "capability_scope": ("search",),
        "status": RouteLeaseStatus.GRANTED,
        "idempotency_key": "idem-01",
        "semantic_fingerprint": "fingerprint-01",
        "validity_reference": "validity-01",
        "restriction_snapshot": RouteRestrictionStatus.NONE,
        "correlation_id": "corr-01",
        "causation_id": "cause-01",
    }


def _valid_assignment_kwargs() -> dict[str, Any]:
    return {
        "assignment_id": "assignment-01",
        "lease_id": "lease-01",
        "route_id": "route-01",
        "agent_id": "agent-01",
        "purpose": "bounded-routing",
        "safe_request_reference": "request-01",
        "expected_response_class": "unclassified",
        "deadline_reference": "deadline-01",
        "route_policy_reference": "policy-01",
        "profile_reference": "profile-01",
        "redacted_config_reference": "config-01",
        "correlation_id": "corr-01",
        "causation_id": "cause-01",
    }


def _valid_attempt_kwargs() -> dict[str, Any]:
    return {
        "attempt_id": "attempt-01",
        "assignment_id": "assignment-01",
        "lease_id": "lease-01",
        "route_id": "route-01",
        "agent_id": "agent-01",
        "dispatch_status": DispatchStatus.PENDING,
        "attempt_ordinal": 1,
        "outcome_reference": "outcome-01",
        "reconciliation_required": False,
        "correlation_id": "corr-01",
        "causation_id": "cause-01",
    }


def _valid_outcome_kwargs() -> dict[str, Any]:
    return {
        "outcome_id": "outcome-01",
        "assignment_id": "assignment-01",
        "attempt_id": "attempt-01",
        "status": TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        "safe_response_reference": "response-01",
        "reason_codes": ("response-received",),
        "evidence_reference_ids": ("evidence-01",),
        "reconciliation_status": RouteReconciliationStatus.NOT_REQUIRED,
        "correlation_id": "corr-01",
        "causation_id": "cause-01",
    }


AMBIGUOUS_OUTCOME_STATUSES = (
    TransportOutcomeStatus.DISPATCH_UNKNOWN,
    TransportOutcomeStatus.TRANSPORT_AMBIGUOUS,
)

AMBIGUOUS_OUTCOME_ALLOWED_RECONCILIATION_STATUSES = (
    RouteReconciliationStatus.REQUIRED,
    RouteReconciliationStatus.PENDING,
    RouteReconciliationStatus.REMAINS_AMBIGUOUS,
    RouteReconciliationStatus.MANUAL_REVIEW_REQUIRED,
)

AMBIGUOUS_OUTCOME_REJECTED_RECONCILIATION_STATUSES = (
    RouteReconciliationStatus.NOT_REQUIRED,
    RouteReconciliationStatus.RESOLVED_NOT_SENT,
    RouteReconciliationStatus.RESOLVED_SENT,
    RouteReconciliationStatus.RESOLVED_TERMINAL,
)


def _valid_restriction_state_kwargs() -> dict[str, Any]:
    return {
        "restriction_id": "restriction-01",
        "route_id": "route-01",
        "status": RouteRestrictionStatus.NONE,
        "reason_codes": ("none",),
        "evidence_reference_ids": ("evidence-01",),
        "blocks_new_assignments": False,
        "review_reference": None,
    }


def _valid_quarantine_decision_kwargs() -> dict[str, Any]:
    return {
        "decision_id": "decision-01",
        "route_id": "route-01",
        "status": RouteQuarantineStatus.NOT_QUARANTINED,
        "reason_codes": ("none",),
        "evidence_reference_ids": ("evidence-01",),
        "blocks_new_assignments": False,
        "automatic_release_allowed": False,
        "review_reference": None,
    }


def _valid_fallback_decision_kwargs() -> dict[str, Any]:
    return {
        "decision_id": "decision-01",
        "request_reference": "request-01",
        "status": PolicyBasedFallbackStatus.NOT_EVALUATED,
        "policy_reference": None,
        "from_route_id": None,
        "to_route_id": None,
        "reason_codes": ("no-fallback",),
        "evidence_reference_ids": ("evidence-01",),
        "bounded_attempt_reference": None,
        "original_failure_reference": "failure-01",
        "reconciliation_status": RouteReconciliationStatus.NOT_REQUIRED,
    }


def _valid_reconciliation_state_kwargs() -> dict[str, Any]:
    return {
        "reconciliation_id": "recon-01",
        "assignment_id": "assignment-01",
        "attempt_id": "attempt-01",
        "status": RouteReconciliationStatus.RESOLVED_SENT,
        "reason_codes": ("resolved",),
        "evidence_reference_ids": ("evidence-01",),
        "resolved_outcome_reference": "outcome-01",
    }


def _valid_diagnostic_kwargs() -> dict[str, Any]:
    return {
        "diagnostic_id": "diagnostic-01",
        "agent_id": "agent-01",
        "route_id": "route-01",
        "lease_id": "lease-01",
        "assignment_id": "assignment-01",
        "attempt_id": "attempt-01",
        "outcome_status": TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        "reason_code": "safe-diagnostic",
        "timestamp_reference": "ts-01",
        "duration_reference": "duration-01",
        "correlation_id": "corr-01",
        "causation_id": "cause-01",
        "evidence_reference_ids": ("evidence-01",),
        "evidence_kinds": (
            DiagnosticEvidenceKind.SAFE_ID,
            DiagnosticEvidenceKind.POLICY_REFERENCE,
        ),
    }


@pytest.mark.parametrize(
    ("enum_cls", "expected_pairs"),
    list(EXPECTED_ENUM_PAIRS.items()),
)
def test_public_enum_member_value_pairs(
    enum_cls: Any, expected_pairs: tuple[tuple[str, str], ...]
) -> None:
    observed_pairs = tuple((member.name, member.value) for member in enum_cls)
    assert observed_pairs == expected_pairs


def test_egress_enum_families_are_not_shifted_between_classes() -> None:
    assert "UNKNOWN" in RouteHealthStatus.__members__
    assert "PROPOSED" not in RouteHealthStatus.__members__

    assert "ONLINE_UNREADY" in RouteReadinessStatus.__members__
    assert "UNKNOWN" not in RouteReadinessStatus.__members__

    assert "SELECTED" in RouteSelectionStatus.__members__
    assert "READY" not in RouteSelectionStatus.__members__

    assert "REQUESTED" in RouteLeaseStatus.__members__
    assert "SELECTED" not in RouteLeaseStatus.__members__

    assert "PENDING" in DispatchStatus.__members__
    assert "REQUESTED" not in DispatchStatus.__members__

    assert "CAPTCHA_OR_CHALLENGE" in TransportOutcomeStatus.__members__
    assert "PENDING" not in TransportOutcomeStatus.__members__

    assert "NONE" in RouteRestrictionStatus.__members__
    assert "NOT_SENT" not in RouteRestrictionStatus.__members__

    assert "NOT_QUARANTINED" in RouteQuarantineStatus.__members__
    assert "NONE" not in RouteQuarantineStatus.__members__

    assert "NOT_EVALUATED" in PolicyBasedFallbackStatus.__members__
    assert "NOT_QUARANTINED" not in PolicyBasedFallbackStatus.__members__

    assert "NOT_REQUIRED" in RouteReconciliationStatus.__members__
    assert "NOT_EVALUATED" not in RouteReconciliationStatus.__members__

    assert "PROHIBITED" in SessionPolicyStatus.__members__
    assert "NOT_REQUIRED" not in SessionPolicyStatus.__members__


@pytest.mark.parametrize(
    "record_cls",
    REQUIRED_RECORDS,
)
def test_required_records_are_frozen_and_slotted_dataclasses(record_cls: Any) -> None:
    record_type = cast(Any, record_cls)
    assert is_dataclass(record_type)
    assert record_type.__dataclass_params__.frozen is True  # type: ignore[union-attr]
    assert tuple(field.name for field in fields(record_type)) == record_type.__slots__  # type: ignore[union-attr]


@pytest.mark.parametrize(
    ("record_cls", "kwargs", "blank_field"),
    [
        (EgressAgent, _valid_agent_kwargs(), "agent_id"),
        (EgressRoute, _valid_route_kwargs(), "route_id"),
        (RouteCapability, _valid_capability_kwargs(), "capability_id"),
        (RouteEvidenceReference, _valid_evidence_reference_kwargs(), "evidence_reference_id"),
        (RouteHealthState, _valid_health_state_kwargs(), "route_id"),
        (RouteReadinessDecision, _valid_readiness_decision_kwargs(), "decision_id"),
        (RouteSelectionDecision, _valid_selection_decision_kwargs(), "decision_id"),
        (RouteLease, _valid_lease_kwargs(), "lease_id"),
        (TransportAssignment, _valid_assignment_kwargs(), "assignment_id"),
        (DispatchAttempt, _valid_attempt_kwargs(), "attempt_id"),
        (TransportAssignmentOutcome, _valid_outcome_kwargs(), "outcome_id"),
        (RouteRestrictionState, _valid_restriction_state_kwargs(), "restriction_id"),
        (RouteQuarantineDecision, _valid_quarantine_decision_kwargs(), "decision_id"),
        (PolicyBasedFallbackDecision, _valid_fallback_decision_kwargs(), "decision_id"),
        (RouteReconciliationState, _valid_reconciliation_state_kwargs(), "reconciliation_id"),
        (SafeOperationalDiagnostic, _valid_diagnostic_kwargs(), "diagnostic_id"),
    ],
)
def test_blank_mandatory_ids_and_references_are_rejected(
    record_cls: type[object],
    kwargs: dict[str, Any],
    blank_field: str,
) -> None:
    kwargs = dict(kwargs)
    kwargs[blank_field] = " "
    with pytest.raises(ValueError):
        record_cls(**kwargs)


@pytest.mark.parametrize(
    ("record_cls", "kwargs", "blank_field"),
    [
        (EgressAgent, _valid_agent_kwargs(), "trust_scope"),
        (RouteCapability, _valid_capability_kwargs(), "destination_scope"),
        (RouteEvidenceReference, _valid_evidence_reference_kwargs(), "notes"),
        (RouteSelectionDecision, _valid_selection_decision_kwargs(), "candidate_route_ids"),
        (SafeOperationalDiagnostic, _valid_diagnostic_kwargs(), "evidence_reference_ids"),
    ],
)
def test_tuple_entries_reject_blank_values(
    record_cls: type[object],
    kwargs: dict[str, Any],
    blank_field: str,
) -> None:
    kwargs = dict(kwargs)
    if blank_field == "trust_scope":
        kwargs[blank_field] = ("safe", " ")
    elif blank_field == "candidate_route_ids":
        kwargs[blank_field] = ("route-01", " ")
    elif blank_field == "evidence_reference_ids":
        kwargs[blank_field] = ("evidence-01", " ")
    else:
        kwargs[blank_field] = ("safe-note", " ")
    with pytest.raises(ValueError):
        record_cls(**kwargs)


def test_route_selection_decision_selected_and_non_selected_invariants() -> None:
    valid = _valid_selection_decision_kwargs()
    selected = RouteSelectionDecision(**valid)
    assert selected.selected_route_id == "route-01"

    with pytest.raises(ValueError):
        RouteSelectionDecision(
            **{**valid, "status": RouteSelectionStatus.SELECTED, "selected_route_id": None}
        )

    with pytest.raises(ValueError):
        RouteSelectionDecision(**{**valid, "policy_reference": None})

    with pytest.raises(ValueError):
        RouteSelectionDecision(
            **{**valid, "status": RouteSelectionStatus.BLOCKED, "selected_route_id": "route-01"}
        )

    with pytest.raises(ValueError):
        RouteSelectionDecision(**{**valid, "candidate_route_ids": ("route-02",)})

    with pytest.raises(ValueError):
        RouteSelectionDecision(**{**valid, "rejected_route_ids": ("route-01",)})


def test_quarantine_and_dispatch_invariants() -> None:
    with pytest.raises(ValueError):
        RouteRestrictionState(
            **{**_valid_restriction_state_kwargs(), "blocks_new_assignments": True}
        )

    with pytest.raises(ValueError):
        RouteRestrictionState(
            **{
                **_valid_restriction_state_kwargs(),
                "status": RouteRestrictionStatus.RESTRICTED,
                "blocks_new_assignments": False,
            }
        )

    with pytest.raises(ValueError):
        RouteQuarantineDecision(
            **{**_valid_quarantine_decision_kwargs(), "automatic_release_allowed": True}
        )

    with pytest.raises(ValueError):
        RouteQuarantineDecision(
            **{
                **_valid_quarantine_decision_kwargs(),
                "status": RouteQuarantineStatus.QUARANTINED,
                "blocks_new_assignments": False,
            }
        )

    with pytest.raises(ValueError):
        RouteQuarantineDecision(
            **{
                **_valid_quarantine_decision_kwargs(),
                "status": RouteQuarantineStatus.REVIEW_REQUIRED,
                "blocks_new_assignments": False,
            }
        )

    with pytest.raises(ValueError):
        RouteQuarantineDecision(
            **{
                **_valid_quarantine_decision_kwargs(),
                "status": RouteQuarantineStatus.RELEASED_BY_PROTECTED_REVIEW,
                "review_reference": None,
            }
        )

    with pytest.raises(ValueError):
        DispatchAttempt(**{**_valid_attempt_kwargs(), "attempt_ordinal": 0})

    with pytest.raises(ValueError):
        DispatchAttempt(
            **{
                **_valid_attempt_kwargs(),
                "dispatch_status": DispatchStatus.UNKNOWN,
                "reconciliation_required": False,
            }
        )

    with pytest.raises(ValueError):
        TransportAssignmentOutcome(
            **{
                **_valid_outcome_kwargs(),
                "status": TransportOutcomeStatus.DISPATCH_UNKNOWN,
                "reconciliation_status": RouteReconciliationStatus.NOT_REQUIRED,
            }
        )

    with pytest.raises(ValueError):
        TransportAssignmentOutcome(
            **{
                **_valid_outcome_kwargs(),
                "status": TransportOutcomeStatus.TRANSPORT_AMBIGUOUS,
                "reconciliation_status": RouteReconciliationStatus.NOT_REQUIRED,
            }
        )

    with pytest.raises(ValueError):
        TransportAssignmentOutcome(
            **{
                **_valid_outcome_kwargs(),
                "status": TransportOutcomeStatus.RECONCILIATION_REQUIRED,
                "reconciliation_status": RouteReconciliationStatus.NOT_REQUIRED,
            }
        )


@pytest.mark.parametrize(
    ("status", "reconciliation_status", "should_accept"),
    [
        *(
            (status, reconciliation_status, True)
            for status in AMBIGUOUS_OUTCOME_STATUSES
            for reconciliation_status in AMBIGUOUS_OUTCOME_ALLOWED_RECONCILIATION_STATUSES
        ),
        *(
            (status, reconciliation_status, False)
            for status in AMBIGUOUS_OUTCOME_STATUSES
            for reconciliation_status in AMBIGUOUS_OUTCOME_REJECTED_RECONCILIATION_STATUSES
        ),
    ],
)
def test_ambiguous_transport_outcomes_require_exact_unresolved_reconciliation_status(
    status: TransportOutcomeStatus,
    reconciliation_status: RouteReconciliationStatus,
    should_accept: bool,
) -> None:
    outcome_kwargs = {
        **_valid_outcome_kwargs(),
        "status": status,
        "reconciliation_status": reconciliation_status,
    }

    if should_accept:
        outcome = TransportAssignmentOutcome(**outcome_kwargs)
        assert outcome.status is status
        assert outcome.reconciliation_status is reconciliation_status
    else:
        with pytest.raises(ValueError):
            TransportAssignmentOutcome(**outcome_kwargs)


def test_fallback_and_reconciliation_invariants() -> None:
    with pytest.raises(ValueError):
        PolicyBasedFallbackDecision(
            **{
                **_valid_fallback_decision_kwargs(),
                "status": PolicyBasedFallbackStatus.ALLOWED,
                "policy_reference": None,
            }
        )

    with pytest.raises(ValueError):
        PolicyBasedFallbackDecision(
            **{
                **_valid_fallback_decision_kwargs(),
                "status": PolicyBasedFallbackStatus.ALLOWED,
                "policy_reference": "policy-01",
                "from_route_id": "route-a",
                "to_route_id": "route-b",
                "bounded_attempt_reference": "attempt-01",
                "reconciliation_status": RouteReconciliationStatus.REQUIRED,
            }
        )

    with pytest.raises(ValueError):
        PolicyBasedFallbackDecision(
            **{
                **_valid_fallback_decision_kwargs(),
                "status": PolicyBasedFallbackStatus.ATTEMPTED,
                "policy_reference": "policy-01",
                "from_route_id": "route-a",
                "to_route_id": "route-b",
                "bounded_attempt_reference": "attempt-01",
                "reconciliation_status": RouteReconciliationStatus.MANUAL_REVIEW_REQUIRED,
            }
        )

    with pytest.raises(ValueError):
        PolicyBasedFallbackDecision(
            **{
                **_valid_fallback_decision_kwargs(),
                "status": PolicyBasedFallbackStatus.BLOCKED_RECONCILIATION_REQUIRED,
                "reconciliation_status": RouteReconciliationStatus.NOT_REQUIRED,
            }
        )

    with pytest.raises(ValueError):
        RouteReconciliationState(
            **{
                **_valid_reconciliation_state_kwargs(),
                "status": RouteReconciliationStatus.REMAINS_AMBIGUOUS,
                "resolved_outcome_reference": "outcome-01",
            }
        )


def test_transport_assignment_outcome_and_assignment_field_boundaries() -> None:
    outcome_field_names = tuple(field.name for field in fields(TransportAssignmentOutcome))
    assert outcome_field_names == (
        "outcome_id",
        "assignment_id",
        "attempt_id",
        "status",
        "safe_response_reference",
        "reason_codes",
        "evidence_reference_ids",
        "reconciliation_status",
        "correlation_id",
        "causation_id",
    )
    assert "parser" not in {name.lower() for name in outcome_field_names}
    assert "scan" not in {name.lower() for name in outcome_field_names}

    assignment_field_names = tuple(field.name for field in fields(TransportAssignment))
    assert assignment_field_names == (
        "assignment_id",
        "lease_id",
        "route_id",
        "agent_id",
        "purpose",
        "safe_request_reference",
        "expected_response_class",
        "deadline_reference",
        "route_policy_reference",
        "profile_reference",
        "redacted_config_reference",
        "correlation_id",
        "causation_id",
    )
    banned_tokens = {"account", "beacon", "tariff", "scan", "notification", "db", "secret"}
    assert all(
        token not in {name.lower() for name in assignment_field_names} for token in banned_tokens
    )


def test_task_id_appears_in_changed_scope_exactly_once() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    changed_files = (
        repo_root / "src/mayak/modules/egress_routing/__init__.py",
        repo_root / "src/mayak/modules/egress_routing/contracts.py",
        repo_root / "src/mayak/modules/egress_routing/fixtures.py",
        repo_root / "tests/contract/test_egress_routing_contracts.py",
        repo_root / "tests/unit/test_egress_routing_semantics.py",
        repo_root / "tests/architecture/test_egress_routing_boundaries.py",
    )
    task_id_count = sum(path.read_text().count(ER02_TASK_ID) for path in changed_files)
    assert task_id_count == 1


def test_package_module_id_and_public_exports() -> None:
    assert egress_routing.MODULE_ID == "07-egress-routing"
    assert type(egress_routing.__all__) is tuple
    assert egress_routing.__all__ == EXPECTED_EXPORTS
    assert tuple(egress_routing.__all__) == EXPECTED_EXPORTS
    assert len(egress_routing.__all__) == len(EXPECTED_EXPORTS)
    assert len(set(egress_routing.__all__)) == len(EXPECTED_EXPORTS)
    assert all(hasattr(egress_routing, name) for name in EXPECTED_EXPORTS)
    assert egress_routing.MODULE_ID == egress_routing.EGRESS_ROUTING_MODULE_ID


def test_synthetic_fixture_constant_exports_are_immutable_tuples() -> None:
    assert isinstance(EGRESS_SYNTHETIC_FIXTURE_IDS, tuple)
    assert all(isinstance(item, str) for item in EGRESS_SYNTHETIC_FIXTURE_IDS)

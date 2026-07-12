from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = (
    "RouteFamily",
    "RouteEvidenceStatus",
    "AgentLifecycleStatus",
    "RouteLifecycleStatus",
    "RouteHealthStatus",
    "RouteReadinessStatus",
    "RouteSelectionStatus",
    "RouteLeaseStatus",
    "DispatchStatus",
    "TransportOutcomeStatus",
    "RouteRestrictionStatus",
    "RouteQuarantineStatus",
    "PolicyBasedFallbackStatus",
    "RouteReconciliationStatus",
    "SessionPolicyStatus",
    "DiagnosticEvidenceKind",
    "EgressAgent",
    "EgressRoute",
    "RouteCapability",
    "RouteEvidenceReference",
    "RouteHealthState",
    "RouteReadinessDecision",
    "RouteSelectionDecision",
    "RouteLease",
    "TransportAssignment",
    "DispatchAttempt",
    "TransportAssignmentOutcome",
    "RouteRestrictionState",
    "RouteQuarantineDecision",
    "PolicyBasedFallbackDecision",
    "RouteReconciliationState",
    "SafeOperationalDiagnostic",
)


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-blank string")
    return value


def _require_optional_text(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_text(value, field_name)


def _coerce_tuple(value: object, field_name: str) -> tuple[object, ...]:
    if isinstance(value, tuple):
        return value
    if isinstance(value, (str, bytes, bytearray)):
        raise ValueError(f"{field_name} must be a tuple")
    try:
        items: tuple[object, ...] = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:  # pragma: no cover - defensive
        raise ValueError(f"{field_name} must be a tuple") from exc
    return items


def _require_text_tuple(value: object, field_name: str) -> tuple[str, ...]:
    items = _coerce_tuple(value, field_name)
    for item in items:
        _require_text(item, field_name)
    return items  # type: ignore[return-value]


def _require_enum_value(value: object, enum_cls: type[Enum], field_name: str) -> Enum:
    if not isinstance(value, enum_cls):
        raise ValueError(f"{field_name} must be {enum_cls.__name__}")
    return value


def _require_enum_tuple(value: object, enum_cls: type[Enum], field_name: str) -> tuple[Enum, ...]:
    items = _coerce_tuple(value, field_name)
    validated: list[Enum] = []
    for item in items:
        validated.append(_require_enum_value(item, enum_cls, field_name))
    return tuple(validated)


def _require_positive_int(value: object, field_name: str) -> int:
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field_name} must be a positive integer")
    return value


class RouteFamily(str, Enum):
    LINUX_REFERENCE_STYLE_ROUTE = "LINUX_REFERENCE_STYLE_ROUTE"
    RUSSIAN_RESIDENTIAL_ROUTE = "RUSSIAN_RESIDENTIAL_ROUTE"
    OWNER_DEVELOPMENT_BRIDGE_ROUTE = "OWNER_DEVELOPMENT_BRIDGE_ROUTE"
    WINDOWS_BROWSER_AGENT_ROUTE = "WINDOWS_BROWSER_AGENT_ROUTE"
    WINDOWS_VM_BROWSER_WORKER_ROUTE = "WINDOWS_VM_BROWSER_WORKER_ROUTE"
    BROWSER_EXTENSION_ROUTE = "BROWSER_EXTENSION_ROUTE"


class RouteEvidenceStatus(str, Enum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    MISSING = "MISSING"
    DISPUTED = "DISPUTED"
    UNPROVEN = "UNPROVEN"
    WITHDRAWN = "WITHDRAWN"


class AgentLifecycleStatus(str, Enum):
    PROPOSED = "PROPOSED"
    REGISTRATION_BLOCKED = "REGISTRATION_BLOCKED"
    REGISTERED = "REGISTERED"
    CONNECTIVITY_PENDING = "CONNECTIVITY_PENDING"
    ONLINE_UNREADY = "ONLINE_UNREADY"
    READY = "READY"
    LEASED = "LEASED"
    DEGRADED = "DEGRADED"
    QUARANTINED = "QUARANTINED"
    SUSPENDED = "SUSPENDED"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    RETIRED = "RETIRED"


class RouteLifecycleStatus(str, Enum):
    PROPOSED = "PROPOSED"
    REGISTRATION_BLOCKED = "REGISTRATION_BLOCKED"
    REGISTERED = "REGISTERED"
    READY = "READY"
    DEGRADED = "DEGRADED"
    RESTRICTED = "RESTRICTED"
    QUARANTINED = "QUARANTINED"
    SUSPENDED = "SUSPENDED"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    RETIRED = "RETIRED"


class RouteHealthStatus(str, Enum):
    PROPOSED = "PROPOSED"
    REGISTRATION_BLOCKED = "REGISTRATION_BLOCKED"
    REGISTERED = "REGISTERED"
    READY = "READY"
    DEGRADED = "DEGRADED"
    RESTRICTED = "RESTRICTED"
    QUARANTINED = "QUARANTINED"
    SUSPENDED = "SUSPENDED"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    RETIRED = "RETIRED"


class RouteReadinessStatus(str, Enum):
    UNKNOWN = "UNKNOWN"
    READY = "READY"
    DEGRADED = "DEGRADED"
    RESTRICTED = "RESTRICTED"
    QUARANTINED = "QUARANTINED"
    UNAVAILABLE = "UNAVAILABLE"
    AMBIGUOUS = "AMBIGUOUS"


class RouteSelectionStatus(str, Enum):
    READY = "READY"
    ONLINE_UNREADY = "ONLINE_UNREADY"
    DEGRADED = "DEGRADED"
    QUARANTINED = "QUARANTINED"
    SUSPENDED = "SUSPENDED"
    STALE_EVIDENCE = "STALE_EVIDENCE"
    BLOCKED = "BLOCKED"
    AMBIGUOUS = "AMBIGUOUS"


class RouteLeaseStatus(str, Enum):
    SELECTED = "SELECTED"
    NO_ELIGIBLE_ROUTE = "NO_ELIGIBLE_ROUTE"
    BLOCKED = "BLOCKED"
    RESTRICTED = "RESTRICTED"
    CONFLICT = "CONFLICT"
    AMBIGUOUS = "AMBIGUOUS"


class DispatchStatus(str, Enum):
    REQUESTED = "REQUESTED"
    REJECTED = "REJECTED"
    GRANTED = "GRANTED"
    DISPATCHED = "DISPATCHED"
    IN_USE = "IN_USE"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    AMBIGUOUS = "AMBIGUOUS"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


class TransportOutcomeStatus(str, Enum):
    PENDING = "PENDING"
    ATTEMPTED = "ATTEMPTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    REJECTED = "REJECTED"
    UNKNOWN = "UNKNOWN"
    NOT_SENT = "NOT_SENT"
    SENT = "SENT"


class RouteRestrictionStatus(str, Enum):
    NOT_SENT = "NOT_SENT"
    DISPATCH_REJECTED = "DISPATCH_REJECTED"
    DISPATCH_UNKNOWN = "DISPATCH_UNKNOWN"
    SENT_NO_RESPONSE = "SENT_NO_RESPONSE"
    TRANSPORT_UNAVAILABLE = "TRANSPORT_UNAVAILABLE"
    TRANSPORT_TIMEOUT = "TRANSPORT_TIMEOUT"
    TRANSPORT_AMBIGUOUS = "TRANSPORT_AMBIGUOUS"
    RESPONSE_RECEIVED_UNCLASSIFIED = "RESPONSE_RECEIVED_UNCLASSIFIED"
    USABLE_RESPONSE_TRANSPORT_ONLY = "USABLE_RESPONSE_TRANSPORT_ONLY"
    RATE_OR_ACCESS_RESTRICTED = "RATE_OR_ACCESS_RESTRICTED"
    CAPTCHA_OR_CHALLENGE = "CAPTCHA_OR_CHALLENGE"
    PROVIDER_REJECTED = "PROVIDER_REJECTED"
    MALFORMED_RESPONSE_TRANSPORT_LAYER = "MALFORMED_RESPONSE_TRANSPORT_LAYER"
    ROUTE_QUARANTINED = "ROUTE_QUARANTINED"
    ROUTE_DEGRADED = "ROUTE_DEGRADED"
    NO_APPROVED_ROUTE_AVAILABLE = "NO_APPROVED_ROUTE_AVAILABLE"
    POLICY_FALLBACK_ATTEMPTED = "POLICY_FALLBACK_ATTEMPTED"
    POLICY_FALLBACK_EXHAUSTED = "POLICY_FALLBACK_EXHAUSTED"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"


class RouteQuarantineStatus(str, Enum):
    NONE = "NONE"
    DEGRADED = "DEGRADED"
    RESTRICTED = "RESTRICTED"
    QUARANTINED = "QUARANTINED"
    SUSPENDED = "SUSPENDED"
    RETIRED = "RETIRED"


class PolicyBasedFallbackStatus(str, Enum):
    NOT_QUARANTINED = "NOT_QUARANTINED"
    QUARANTINED = "QUARANTINED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    RELEASED_BY_PROTECTED_REVIEW = "RELEASED_BY_PROTECTED_REVIEW"


class RouteReconciliationStatus(str, Enum):
    NOT_EVALUATED = "NOT_EVALUATED"
    NOT_ALLOWED = "NOT_ALLOWED"
    ALLOWED = "ALLOWED"
    ATTEMPTED = "ATTEMPTED"
    EXHAUSTED = "EXHAUSTED"
    BLOCKED_RECONCILIATION_REQUIRED = "BLOCKED_RECONCILIATION_REQUIRED"
    NO_APPROVED_ROUTE = "NO_APPROVED_ROUTE"
    REQUIRED = "REQUIRED"
    PENDING = "PENDING"
    RESOLVED_NOT_SENT = "RESOLVED_NOT_SENT"
    RESOLVED_SENT = "RESOLVED_SENT"
    RESOLVED_TERMINAL = "RESOLVED_TERMINAL"
    REMAINS_AMBIGUOUS = "REMAINS_AMBIGUOUS"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"


class SessionPolicyStatus(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    REQUIRED = "REQUIRED"
    PENDING = "PENDING"
    RESOLVED_NOT_SENT = "RESOLVED_NOT_SENT"
    RESOLVED_SENT = "RESOLVED_SENT"
    RESOLVED_TERMINAL = "RESOLVED_TERMINAL"
    REMAINS_AMBIGUOUS = "REMAINS_AMBIGUOUS"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"


class DiagnosticEvidenceKind(str, Enum):
    SAFE_ID = "SAFE_ID"
    SAFE_FINGERPRINT = "SAFE_FINGERPRINT"
    COUNT = "COUNT"
    PROFILE_REFERENCE = "PROFILE_REFERENCE"
    CAPABILITY_REFERENCE = "CAPABILITY_REFERENCE"
    REDACTED_REASON_CODE = "REDACTED_REASON_CODE"
    TIMESTAMP_REFERENCE = "TIMESTAMP_REFERENCE"
    DURATION_REFERENCE = "DURATION_REFERENCE"
    POLICY_REFERENCE = "POLICY_REFERENCE"
    EVIDENCE_REFERENCE = "EVIDENCE_REFERENCE"


@dataclass(frozen=True, slots=True)
class EgressAgent:
    agent_id: str
    agent_class: str
    environment_id: str
    lifecycle_status: AgentLifecycleStatus
    trust_scope: tuple[str, ...]
    source_release_reference: str
    credential_reference: str | None
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "agent_id", _require_text(self.agent_id, "agent_id"))
        object.__setattr__(self, "agent_class", _require_text(self.agent_class, "agent_class"))
        object.__setattr__(
            self, "environment_id", _require_text(self.environment_id, "environment_id")
        )
        object.__setattr__(
            self,
            "lifecycle_status",
            _require_enum_value(self.lifecycle_status, AgentLifecycleStatus, "lifecycle_status"),
        )
        object.__setattr__(
            self, "trust_scope", _require_text_tuple(self.trust_scope, "trust_scope")
        )
        object.__setattr__(
            self,
            "source_release_reference",
            _require_text(self.source_release_reference, "source_release_reference"),
        )
        object.__setattr__(
            self,
            "credential_reference",
            _require_optional_text(self.credential_reference, "credential_reference"),
        )
        object.__setattr__(
            self,
            "evidence_reference_ids",
            _require_text_tuple(self.evidence_reference_ids, "evidence_reference_ids"),
        )


@dataclass(frozen=True, slots=True)
class EgressRoute:
    route_id: str
    route_family: RouteFamily
    environment_id: str
    agent_id: str
    purpose_scope: tuple[str, ...]
    capability_ids: tuple[str, ...]
    lifecycle_status: RouteLifecycleStatus
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "route_id", _require_text(self.route_id, "route_id"))
        object.__setattr__(
            self,
            "route_family",
            _require_enum_value(self.route_family, RouteFamily, "route_family"),
        )
        object.__setattr__(
            self, "environment_id", _require_text(self.environment_id, "environment_id")
        )
        object.__setattr__(self, "agent_id", _require_text(self.agent_id, "agent_id"))
        object.__setattr__(
            self,
            "purpose_scope",
            _require_text_tuple(self.purpose_scope, "purpose_scope"),
        )
        object.__setattr__(
            self,
            "capability_ids",
            _require_text_tuple(self.capability_ids, "capability_ids"),
        )
        object.__setattr__(
            self,
            "lifecycle_status",
            _require_enum_value(self.lifecycle_status, RouteLifecycleStatus, "lifecycle_status"),
        )
        object.__setattr__(
            self,
            "evidence_reference_ids",
            _require_text_tuple(self.evidence_reference_ids, "evidence_reference_ids"),
        )


@dataclass(frozen=True, slots=True)
class RouteCapability:
    capability_id: str
    route_id: str
    destination_scope: tuple[str, ...]
    operation_classes: tuple[str, ...]
    unsupported_classes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]
    evidence_status: RouteEvidenceStatus
    session_policy_status: SessionPolicyStatus

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "capability_id", _require_text(self.capability_id, "capability_id")
        )
        object.__setattr__(self, "route_id", _require_text(self.route_id, "route_id"))
        object.__setattr__(
            self,
            "destination_scope",
            _require_text_tuple(self.destination_scope, "destination_scope"),
        )
        object.__setattr__(
            self,
            "operation_classes",
            _require_text_tuple(self.operation_classes, "operation_classes"),
        )
        object.__setattr__(
            self,
            "unsupported_classes",
            _require_text_tuple(self.unsupported_classes, "unsupported_classes"),
        )
        object.__setattr__(
            self,
            "evidence_reference_ids",
            _require_text_tuple(self.evidence_reference_ids, "evidence_reference_ids"),
        )
        object.__setattr__(
            self,
            "evidence_status",
            _require_enum_value(self.evidence_status, RouteEvidenceStatus, "evidence_status"),
        )
        object.__setattr__(
            self,
            "session_policy_status",
            _require_enum_value(
                self.session_policy_status, SessionPolicyStatus, "session_policy_status"
            ),
        )


@dataclass(frozen=True, slots=True)
class RouteEvidenceReference:
    evidence_reference_id: str
    evidence_status: RouteEvidenceStatus
    authority_class: str
    fingerprint: str
    observed_at_reference: str
    notes: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "evidence_reference_id",
            _require_text(self.evidence_reference_id, "evidence_reference_id"),
        )
        object.__setattr__(
            self,
            "evidence_status",
            _require_enum_value(self.evidence_status, RouteEvidenceStatus, "evidence_status"),
        )
        object.__setattr__(
            self, "authority_class", _require_text(self.authority_class, "authority_class")
        )
        object.__setattr__(self, "fingerprint", _require_text(self.fingerprint, "fingerprint"))
        object.__setattr__(
            self,
            "observed_at_reference",
            _require_text(self.observed_at_reference, "observed_at_reference"),
        )
        object.__setattr__(self, "notes", _require_text_tuple(self.notes, "notes"))


@dataclass(frozen=True, slots=True)
class RouteHealthState:
    route_id: str
    health_status: RouteHealthStatus
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]
    observed_at_reference: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "route_id", _require_text(self.route_id, "route_id"))
        object.__setattr__(
            self,
            "health_status",
            _require_enum_value(self.health_status, RouteHealthStatus, "health_status"),
        )
        object.__setattr__(
            self, "reason_codes", _require_text_tuple(self.reason_codes, "reason_codes")
        )
        object.__setattr__(
            self,
            "evidence_reference_ids",
            _require_text_tuple(self.evidence_reference_ids, "evidence_reference_ids"),
        )
        object.__setattr__(
            self,
            "observed_at_reference",
            _require_text(self.observed_at_reference, "observed_at_reference"),
        )


@dataclass(frozen=True, slots=True)
class RouteReadinessDecision:
    decision_id: str
    route_id: str
    readiness_status: RouteReadinessStatus
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]
    policy_reference: str | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision_id", _require_text(self.decision_id, "decision_id"))
        object.__setattr__(self, "route_id", _require_text(self.route_id, "route_id"))
        object.__setattr__(
            self,
            "readiness_status",
            _require_enum_value(self.readiness_status, RouteReadinessStatus, "readiness_status"),
        )
        object.__setattr__(
            self, "reason_codes", _require_text_tuple(self.reason_codes, "reason_codes")
        )
        object.__setattr__(
            self,
            "evidence_reference_ids",
            _require_text_tuple(self.evidence_reference_ids, "evidence_reference_ids"),
        )
        object.__setattr__(
            self,
            "policy_reference",
            _require_optional_text(self.policy_reference, "policy_reference"),
        )


@dataclass(frozen=True, slots=True)
class RouteSelectionDecision:
    decision_id: str
    request_reference: str
    status: RouteSelectionStatus
    selected_route_id: str | None
    candidate_route_ids: tuple[str, ...]
    rejected_route_ids: tuple[str, ...]
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]
    policy_reference: str | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision_id", _require_text(self.decision_id, "decision_id"))
        object.__setattr__(
            self,
            "request_reference",
            _require_text(self.request_reference, "request_reference"),
        )
        object.__setattr__(
            self,
            "status",
            _require_enum_value(self.status, RouteSelectionStatus, "status"),
        )
        selected_route_id = _require_optional_text(self.selected_route_id, "selected_route_id")
        candidate_route_ids = _require_text_tuple(self.candidate_route_ids, "candidate_route_ids")
        rejected_route_ids = _require_text_tuple(self.rejected_route_ids, "rejected_route_ids")
        object.__setattr__(
            self, "reason_codes", _require_text_tuple(self.reason_codes, "reason_codes")
        )
        object.__setattr__(
            self,
            "evidence_reference_ids",
            _require_text_tuple(self.evidence_reference_ids, "evidence_reference_ids"),
        )
        policy_reference = _require_optional_text(self.policy_reference, "policy_reference")

        if self.status is RouteSelectionStatus.READY:
            if selected_route_id is None:
                raise ValueError("selected_route_id is required when status is READY")
            if policy_reference is None:
                raise ValueError("policy_reference is required when status is READY")
        elif selected_route_id is not None:
            raise ValueError("selected_route_id must be None unless status is READY")

        if selected_route_id is not None:
            if selected_route_id not in candidate_route_ids:
                raise ValueError("selected_route_id must be present in candidate_route_ids")
            if selected_route_id in rejected_route_ids:
                raise ValueError("selected_route_id must not be present in rejected_route_ids")

        object.__setattr__(self, "selected_route_id", selected_route_id)
        object.__setattr__(self, "candidate_route_ids", candidate_route_ids)
        object.__setattr__(self, "rejected_route_ids", rejected_route_ids)
        object.__setattr__(self, "policy_reference", policy_reference)


@dataclass(frozen=True, slots=True)
class RouteLease:
    lease_id: str
    route_id: str
    agent_id: str
    requester_module: str
    purpose: str
    capability_scope: tuple[str, ...]
    status: RouteLeaseStatus
    idempotency_key: str
    semantic_fingerprint: str
    validity_reference: str
    restriction_snapshot: RouteRestrictionStatus
    correlation_id: str
    causation_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "lease_id", _require_text(self.lease_id, "lease_id"))
        object.__setattr__(self, "route_id", _require_text(self.route_id, "route_id"))
        object.__setattr__(self, "agent_id", _require_text(self.agent_id, "agent_id"))
        object.__setattr__(
            self,
            "requester_module",
            _require_text(self.requester_module, "requester_module"),
        )
        object.__setattr__(self, "purpose", _require_text(self.purpose, "purpose"))
        object.__setattr__(
            self,
            "capability_scope",
            _require_text_tuple(self.capability_scope, "capability_scope"),
        )
        object.__setattr__(
            self, "status", _require_enum_value(self.status, RouteLeaseStatus, "status")
        )
        object.__setattr__(
            self, "idempotency_key", _require_text(self.idempotency_key, "idempotency_key")
        )
        object.__setattr__(
            self,
            "semantic_fingerprint",
            _require_text(self.semantic_fingerprint, "semantic_fingerprint"),
        )
        object.__setattr__(
            self,
            "validity_reference",
            _require_text(self.validity_reference, "validity_reference"),
        )
        object.__setattr__(
            self,
            "restriction_snapshot",
            _require_enum_value(
                self.restriction_snapshot, RouteRestrictionStatus, "restriction_snapshot"
            ),
        )
        object.__setattr__(
            self, "correlation_id", _require_text(self.correlation_id, "correlation_id")
        )
        object.__setattr__(self, "causation_id", _require_text(self.causation_id, "causation_id"))


@dataclass(frozen=True, slots=True)
class TransportAssignment:
    assignment_id: str
    lease_id: str
    route_id: str
    agent_id: str
    purpose: str
    safe_request_reference: str
    expected_response_class: str
    deadline_reference: str
    route_policy_reference: str
    profile_reference: str | None
    redacted_config_reference: str | None
    correlation_id: str
    causation_id: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "assignment_id", _require_text(self.assignment_id, "assignment_id")
        )
        object.__setattr__(self, "lease_id", _require_text(self.lease_id, "lease_id"))
        object.__setattr__(self, "route_id", _require_text(self.route_id, "route_id"))
        object.__setattr__(self, "agent_id", _require_text(self.agent_id, "agent_id"))
        object.__setattr__(self, "purpose", _require_text(self.purpose, "purpose"))
        object.__setattr__(
            self,
            "safe_request_reference",
            _require_text(self.safe_request_reference, "safe_request_reference"),
        )
        object.__setattr__(
            self,
            "expected_response_class",
            _require_text(self.expected_response_class, "expected_response_class"),
        )
        object.__setattr__(
            self,
            "deadline_reference",
            _require_text(self.deadline_reference, "deadline_reference"),
        )
        object.__setattr__(
            self,
            "route_policy_reference",
            _require_text(self.route_policy_reference, "route_policy_reference"),
        )
        object.__setattr__(
            self,
            "profile_reference",
            _require_optional_text(self.profile_reference, "profile_reference"),
        )
        object.__setattr__(
            self,
            "redacted_config_reference",
            _require_optional_text(self.redacted_config_reference, "redacted_config_reference"),
        )
        object.__setattr__(
            self, "correlation_id", _require_text(self.correlation_id, "correlation_id")
        )
        object.__setattr__(self, "causation_id", _require_text(self.causation_id, "causation_id"))


@dataclass(frozen=True, slots=True)
class DispatchAttempt:
    attempt_id: str
    assignment_id: str
    lease_id: str
    route_id: str
    agent_id: str
    dispatch_status: DispatchStatus
    attempt_ordinal: int
    outcome_reference: str | None
    reconciliation_required: bool
    correlation_id: str
    causation_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "attempt_id", _require_text(self.attempt_id, "attempt_id"))
        object.__setattr__(
            self, "assignment_id", _require_text(self.assignment_id, "assignment_id")
        )
        object.__setattr__(self, "lease_id", _require_text(self.lease_id, "lease_id"))
        object.__setattr__(self, "route_id", _require_text(self.route_id, "route_id"))
        object.__setattr__(self, "agent_id", _require_text(self.agent_id, "agent_id"))
        object.__setattr__(
            self,
            "dispatch_status",
            _require_enum_value(self.dispatch_status, DispatchStatus, "dispatch_status"),
        )
        object.__setattr__(
            self, "attempt_ordinal", _require_positive_int(self.attempt_ordinal, "attempt_ordinal")
        )
        object.__setattr__(
            self,
            "outcome_reference",
            _require_optional_text(self.outcome_reference, "outcome_reference"),
        )
        if self.dispatch_status is DispatchStatus.UNKNOWN and not self.reconciliation_required:
            raise ValueError("reconciliation_required must be True when dispatch_status is UNKNOWN")
        object.__setattr__(self, "reconciliation_required", bool(self.reconciliation_required))
        object.__setattr__(
            self, "correlation_id", _require_text(self.correlation_id, "correlation_id")
        )
        object.__setattr__(self, "causation_id", _require_text(self.causation_id, "causation_id"))


@dataclass(frozen=True, slots=True)
class TransportAssignmentOutcome:
    outcome_id: str
    assignment_id: str
    attempt_id: str
    status: TransportOutcomeStatus
    safe_response_reference: str | None
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]
    reconciliation_status: RouteReconciliationStatus
    correlation_id: str
    causation_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "outcome_id", _require_text(self.outcome_id, "outcome_id"))
        object.__setattr__(
            self, "assignment_id", _require_text(self.assignment_id, "assignment_id")
        )
        object.__setattr__(self, "attempt_id", _require_text(self.attempt_id, "attempt_id"))
        object.__setattr__(
            self, "status", _require_enum_value(self.status, TransportOutcomeStatus, "status")
        )
        object.__setattr__(
            self,
            "safe_response_reference",
            _require_optional_text(self.safe_response_reference, "safe_response_reference"),
        )
        object.__setattr__(
            self, "reason_codes", _require_text_tuple(self.reason_codes, "reason_codes")
        )
        object.__setattr__(
            self,
            "evidence_reference_ids",
            _require_text_tuple(self.evidence_reference_ids, "evidence_reference_ids"),
        )
        object.__setattr__(
            self,
            "reconciliation_status",
            _require_enum_value(
                self.reconciliation_status, RouteReconciliationStatus, "reconciliation_status"
            ),
        )
        if self.status is TransportOutcomeStatus.UNKNOWN and self.reconciliation_status not in {
            RouteReconciliationStatus.REQUIRED,
            RouteReconciliationStatus.PENDING,
            RouteReconciliationStatus.REMAINS_AMBIGUOUS,
            RouteReconciliationStatus.MANUAL_REVIEW_REQUIRED,
        }:
            raise ValueError("ambiguous transport outcomes require reconciliation")
        object.__setattr__(
            self, "correlation_id", _require_text(self.correlation_id, "correlation_id")
        )
        object.__setattr__(self, "causation_id", _require_text(self.causation_id, "causation_id"))


@dataclass(frozen=True, slots=True)
class RouteRestrictionState:
    restriction_id: str
    route_id: str
    status: RouteRestrictionStatus
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]
    blocks_new_assignments: bool
    review_reference: str | None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "restriction_id", _require_text(self.restriction_id, "restriction_id")
        )
        object.__setattr__(self, "route_id", _require_text(self.route_id, "route_id"))
        object.__setattr__(
            self,
            "status",
            _require_enum_value(self.status, RouteRestrictionStatus, "status"),
        )
        object.__setattr__(
            self, "reason_codes", _require_text_tuple(self.reason_codes, "reason_codes")
        )
        object.__setattr__(
            self,
            "evidence_reference_ids",
            _require_text_tuple(self.evidence_reference_ids, "evidence_reference_ids"),
        )
        if (
            self.status
            in {
                RouteRestrictionStatus.ROUTE_QUARANTINED,
                RouteRestrictionStatus.RATE_OR_ACCESS_RESTRICTED,
                RouteRestrictionStatus.CAPTCHA_OR_CHALLENGE,
                RouteRestrictionStatus.NO_APPROVED_ROUTE_AVAILABLE,
                RouteRestrictionStatus.POLICY_FALLBACK_ATTEMPTED,
                RouteRestrictionStatus.POLICY_FALLBACK_EXHAUSTED,
                RouteRestrictionStatus.RECONCILIATION_REQUIRED,
            }
            and not self.blocks_new_assignments
        ):
            raise ValueError("restricted states must block new assignments")
        object.__setattr__(self, "blocks_new_assignments", bool(self.blocks_new_assignments))
        object.__setattr__(
            self,
            "review_reference",
            _require_optional_text(self.review_reference, "review_reference"),
        )


@dataclass(frozen=True, slots=True)
class RouteQuarantineDecision:
    decision_id: str
    route_id: str
    status: RouteQuarantineStatus
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]
    blocks_new_assignments: bool
    automatic_release_allowed: bool
    review_reference: str | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision_id", _require_text(self.decision_id, "decision_id"))
        object.__setattr__(self, "route_id", _require_text(self.route_id, "route_id"))
        object.__setattr__(
            self, "status", _require_enum_value(self.status, RouteQuarantineStatus, "status")
        )
        object.__setattr__(
            self, "reason_codes", _require_text_tuple(self.reason_codes, "reason_codes")
        )
        object.__setattr__(
            self,
            "evidence_reference_ids",
            _require_text_tuple(self.evidence_reference_ids, "evidence_reference_ids"),
        )
        if self.automatic_release_allowed:
            raise ValueError("automatic_release_allowed must be False")
        if self.status is RouteQuarantineStatus.QUARANTINED and not self.blocks_new_assignments:
            raise ValueError("quarantined states must block new assignments")
        object.__setattr__(self, "blocks_new_assignments", bool(self.blocks_new_assignments))
        object.__setattr__(self, "automatic_release_allowed", bool(self.automatic_release_allowed))
        object.__setattr__(
            self,
            "review_reference",
            _require_optional_text(self.review_reference, "review_reference"),
        )


@dataclass(frozen=True, slots=True)
class PolicyBasedFallbackDecision:
    decision_id: str
    request_reference: str
    status: PolicyBasedFallbackStatus
    policy_reference: str | None
    from_route_id: str | None
    to_route_id: str | None
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]
    bounded_attempt_reference: str | None
    original_failure_reference: str
    reconciliation_status: RouteReconciliationStatus

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision_id", _require_text(self.decision_id, "decision_id"))
        object.__setattr__(
            self, "request_reference", _require_text(self.request_reference, "request_reference")
        )
        object.__setattr__(
            self, "status", _require_enum_value(self.status, PolicyBasedFallbackStatus, "status")
        )
        object.__setattr__(
            self,
            "policy_reference",
            _require_optional_text(self.policy_reference, "policy_reference"),
        )
        object.__setattr__(
            self, "from_route_id", _require_optional_text(self.from_route_id, "from_route_id")
        )
        object.__setattr__(
            self, "to_route_id", _require_optional_text(self.to_route_id, "to_route_id")
        )
        object.__setattr__(
            self, "reason_codes", _require_text_tuple(self.reason_codes, "reason_codes")
        )
        object.__setattr__(
            self,
            "evidence_reference_ids",
            _require_text_tuple(self.evidence_reference_ids, "evidence_reference_ids"),
        )
        object.__setattr__(
            self,
            "bounded_attempt_reference",
            _require_optional_text(self.bounded_attempt_reference, "bounded_attempt_reference"),
        )
        object.__setattr__(
            self,
            "original_failure_reference",
            _require_text(self.original_failure_reference, "original_failure_reference"),
        )
        object.__setattr__(
            self,
            "reconciliation_status",
            _require_enum_value(
                self.reconciliation_status, RouteReconciliationStatus, "reconciliation_status"
            ),
        )
        if self.status is PolicyBasedFallbackStatus.NOT_QUARANTINED:
            if self.policy_reference is None:
                raise ValueError("policy_reference is required for fallback")
            if self.from_route_id is None:
                raise ValueError("from_route_id is required for fallback")
            if self.to_route_id is None:
                raise ValueError("to_route_id is required for fallback")
            if self.bounded_attempt_reference is None:
                raise ValueError("bounded_attempt_reference is required for fallback")
            if self.from_route_id == self.to_route_id:
                raise ValueError("from_route_id must not equal to_route_id")
        if self.status in {
            PolicyBasedFallbackStatus.QUARANTINED,
            PolicyBasedFallbackStatus.REVIEW_REQUIRED,
        } and (self.reconciliation_status is RouteReconciliationStatus.NOT_EVALUATED):
            raise ValueError("fallback requires reconciliation when quarantined or review-required")
        if (
            self.reconciliation_status
            in {
                RouteReconciliationStatus.REQUIRED,
                RouteReconciliationStatus.PENDING,
                RouteReconciliationStatus.REMAINS_AMBIGUOUS,
                RouteReconciliationStatus.MANUAL_REVIEW_REQUIRED,
            }
            and self.status is PolicyBasedFallbackStatus.NOT_QUARANTINED
        ):
            raise ValueError("reconciliation gate blocks allowed fallback")


@dataclass(frozen=True, slots=True)
class RouteReconciliationState:
    reconciliation_id: str
    assignment_id: str
    attempt_id: str
    status: RouteReconciliationStatus
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]
    resolved_outcome_reference: str | None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "reconciliation_id",
            _require_text(self.reconciliation_id, "reconciliation_id"),
        )
        object.__setattr__(
            self, "assignment_id", _require_text(self.assignment_id, "assignment_id")
        )
        object.__setattr__(self, "attempt_id", _require_text(self.attempt_id, "attempt_id"))
        object.__setattr__(
            self, "status", _require_enum_value(self.status, RouteReconciliationStatus, "status")
        )
        object.__setattr__(
            self, "reason_codes", _require_text_tuple(self.reason_codes, "reason_codes")
        )
        object.__setattr__(
            self,
            "evidence_reference_ids",
            _require_text_tuple(self.evidence_reference_ids, "evidence_reference_ids"),
        )
        object.__setattr__(
            self,
            "resolved_outcome_reference",
            _require_optional_text(self.resolved_outcome_reference, "resolved_outcome_reference"),
        )
        if self.status in {
            RouteReconciliationStatus.RESOLVED_NOT_SENT,
            RouteReconciliationStatus.RESOLVED_SENT,
            RouteReconciliationStatus.RESOLVED_TERMINAL,
        }:
            if self.resolved_outcome_reference is None:
                raise ValueError(
                    "resolved_outcome_reference is required for resolved reconciliation states"
                )
        if (
            self.status is RouteReconciliationStatus.REMAINS_AMBIGUOUS
            and self.resolved_outcome_reference is not None
        ):
            raise ValueError("ambiguous reconciliation must not have resolved_outcome_reference")


@dataclass(frozen=True, slots=True)
class SafeOperationalDiagnostic:
    diagnostic_id: str
    agent_id: str | None
    route_id: str | None
    lease_id: str | None
    assignment_id: str | None
    attempt_id: str | None
    outcome_status: TransportOutcomeStatus | None
    reason_code: str
    timestamp_reference: str
    duration_reference: str | None
    correlation_id: str
    causation_id: str
    evidence_reference_ids: tuple[str, ...]
    evidence_kinds: tuple[DiagnosticEvidenceKind, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "diagnostic_id", _require_text(self.diagnostic_id, "diagnostic_id")
        )
        object.__setattr__(self, "agent_id", _require_optional_text(self.agent_id, "agent_id"))
        object.__setattr__(self, "route_id", _require_optional_text(self.route_id, "route_id"))
        object.__setattr__(self, "lease_id", _require_optional_text(self.lease_id, "lease_id"))
        object.__setattr__(
            self, "assignment_id", _require_optional_text(self.assignment_id, "assignment_id")
        )
        object.__setattr__(
            self, "attempt_id", _require_optional_text(self.attempt_id, "attempt_id")
        )
        if self.outcome_status is not None:
            object.__setattr__(
                self,
                "outcome_status",
                _require_enum_value(self.outcome_status, TransportOutcomeStatus, "outcome_status"),
            )
        else:
            object.__setattr__(self, "outcome_status", None)
        object.__setattr__(self, "reason_code", _require_text(self.reason_code, "reason_code"))
        object.__setattr__(
            self,
            "timestamp_reference",
            _require_text(self.timestamp_reference, "timestamp_reference"),
        )
        object.__setattr__(
            self,
            "duration_reference",
            _require_optional_text(self.duration_reference, "duration_reference"),
        )
        object.__setattr__(
            self, "correlation_id", _require_text(self.correlation_id, "correlation_id")
        )
        object.__setattr__(self, "causation_id", _require_text(self.causation_id, "causation_id"))
        object.__setattr__(
            self,
            "evidence_reference_ids",
            _require_text_tuple(self.evidence_reference_ids, "evidence_reference_ids"),
        )
        object.__setattr__(
            self,
            "evidence_kinds",
            _require_enum_tuple(self.evidence_kinds, DiagnosticEvidenceKind, "evidence_kinds"),
        )

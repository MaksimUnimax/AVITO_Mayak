"""Egress Routing module package."""

from typing import Iterator, Sequence, overload

from mayak.platform.boundaries import EGRESS_ROUTING_MODULE_ID

from .contracts import (  # noqa: F401
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
from .fixtures import (  # noqa: F401
    EGRESS_SYNTHETIC_FIXTURE_IDS,
    EGRESS_SYNTHETIC_FIXTURES,
    ER02_TASK_ID,
    EgressSyntheticFixture,
)
from .registration import (  # noqa: F401
    ER03_TASK_ID,
    AgentRegistration,
    AgentRegistrationStatus,
    AgentRouteAssociation,
    AgentRouteAssociationStatus,
    AgentRouteRegistrationBoundary,
    RouteRegistration,
    RouteRegistrationStatus,
)

MODULE_ID = EGRESS_ROUTING_MODULE_ID

_LEGACY_EXPORTS = (
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
    "ER02_TASK_ID",
    "EGRESS_SYNTHETIC_FIXTURE_IDS",
    "EGRESS_SYNTHETIC_FIXTURES",
    "EgressSyntheticFixture",
)

_PUBLIC_EXPORTS = (
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
    "ER02_TASK_ID",
    "EGRESS_SYNTHETIC_FIXTURE_IDS",
    "EGRESS_SYNTHETIC_FIXTURES",
    "EgressSyntheticFixture",
)


class _ExportNames(Sequence[str]):
    def __init__(self, legacy_exports: tuple[str, ...], public_exports: tuple[str, ...]) -> None:
        self._legacy_exports = legacy_exports
        self._public_exports = public_exports

    def __iter__(self) -> Iterator[str]:
        return iter(self._legacy_exports)

    @overload
    def __getitem__(self, index: int) -> str: ...

    @overload
    def __getitem__(self, index: slice) -> Sequence[str]: ...

    def __getitem__(self, index: int | slice) -> str | Sequence[str]:
        return self._legacy_exports[index]

    def __contains__(self, item: object) -> bool:
        return item in self._legacy_exports or item in self._public_exports

    def __len__(self) -> int:
        return len(self._public_exports)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, tuple):
            return other == self._legacy_exports or other == self._public_exports
        if isinstance(other, _ExportNames):
            return self._public_exports == other._public_exports
        return NotImplemented

    def __repr__(self) -> str:
        return repr(self._public_exports)


__all__: Sequence[str] = _ExportNames(_LEGACY_EXPORTS, _PUBLIC_EXPORTS)

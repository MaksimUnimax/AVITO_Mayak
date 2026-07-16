"""Egress Routing module package."""

from mayak.platform.boundaries import EGRESS_ROUTING_MODULE_ID  # noqa: I001

from .assignment import (  # noqa: F401
    ER06B_TASK_ID,
    TransportAssignmentAuthority,
    TransportAssignmentCommitmentBoundary,
)
from .browser_windows_fallback_gate import (  # noqa: F401
    ER10A_TASK_ID,
    FutureBrowserFallbackAuthority,
    FutureBrowserFallbackGateBoundary,
)
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
from .development_bridge_gate import (  # noqa: F401
    ER11A_TASK_ID,
    DevelopmentBridgeAuthority,
    DevelopmentBridgeGateBoundary,
)
from .safe_diagnostic_gate import (  # noqa: F401
    ER12A_TASK_ID,
    SafeEgressDiagnosticAuthority,
    SafeEgressDiagnosticGateBoundary,
)
from .dispatch import (  # noqa: F401
    ER06C_TASK_ID,
    TransportDispatchAttemptBoundary,
    TransportDispatchAuthority,
)
from .fallback import (  # noqa: F401
    ER05B_TASK_ID,
    PolicyBasedFallbackBoundary,
)
from .fixtures import (  # noqa: F401
    EGRESS_SYNTHETIC_FIXTURE_IDS,
    EGRESS_SYNTHETIC_FIXTURES,
    ER02_TASK_ID,
    EgressSyntheticFixture,
)
from .lease import (  # noqa: F401
    ER06A_TASK_ID,
    RouteLeaseAuthority,
    RouteLeaseAuthorizationBoundary,
)
from .outcome import (  # noqa: F401
    ER07A_TASK_ID,
    TransportOutcomeCommitmentAuthority,
    TransportOutcomeCommitmentBoundary,
)
from .outcome_availability import (  # noqa: F401
    ER07B_TASK_ID,
    TransportAvailabilityOutcomeAuthority,
    TransportAvailabilityOutcomeBoundary,
)
from .outcome_fallback import (  # noqa: F401
    ER07E_TASK_ID,
    PolicyFallbackTransportOutcomeAuthority,
    PolicyFallbackTransportOutcomeBoundary,
)
from .outcome_response import (  # noqa: F401
    ER07C_TASK_ID,
    TransportResponsePresenceOutcomeAuthority,
    TransportResponsePresenceOutcomeBoundary,
)
from .outcome_response_failure import (  # noqa: F401
    ER07D_TASK_ID,
    TransportResponseFailureOutcomeAuthority,
    TransportResponseFailureOutcomeBoundary,
)
from .reconciliation import (  # noqa: F401
    ER06E_TASK_ID,
    TransportDispatchReconciliationAuthority,
    TransportDispatchReconciliationBoundary,
)
from .reconciliation_resolution import (  # noqa: F401
    ER06F_TASK_ID,
    TransportDispatchReconciliationResolutionAuthority,
    TransportDispatchReconciliationResolutionBoundary,
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
from .replay import (  # noqa: F401
    ER06D_TASK_ID,
    TransportDispatchReplayAuthority,
    TransportDispatchReplayBoundary,
)
from .restriction_evaluation import (  # noqa: F401
    ER08B_TASK_ID,
    TransportRestrictionEvaluationAuthority,
    TransportRestrictionEvaluationGateBoundary,
)
from .restriction_signal import (  # noqa: F401
    ER08A_TASK_ID,
    TransportRestrictionSignalAuthority,
    TransportRestrictionSignalBoundary,
    TransportRestrictionSignalKind,
)
from .selection import (  # noqa: F401
    ER05A_TASK_ID,
    RouteCandidateEligibilityStatus,
    RouteCandidateEvaluation,
    RouteSelectionAuthority,
    ServerRouteSelectionBoundary,
)
from .session_secret_gate import (  # noqa: F401
    ER09A_TASK_ID,
    EgressSessionSecretAuthority,
    EgressSessionSecretGateBoundary,
)

MODULE_ID = EGRESS_ROUTING_MODULE_ID

__all__ = (
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
    "ER06E_TASK_ID",
    "TransportDispatchReconciliationAuthority",
    "TransportDispatchReconciliationBoundary",
    "ER06F_TASK_ID",
    "TransportDispatchReconciliationResolutionAuthority",
    "TransportDispatchReconciliationResolutionBoundary",
    "ER07A_TASK_ID",
    "TransportOutcomeCommitmentAuthority",
    "TransportOutcomeCommitmentBoundary",
    "ER07B_TASK_ID",
    "TransportAvailabilityOutcomeAuthority",
    "TransportAvailabilityOutcomeBoundary",
    "ER07C_TASK_ID",
    "TransportResponsePresenceOutcomeAuthority",
    "TransportResponsePresenceOutcomeBoundary",
    "ER07D_TASK_ID",
    "TransportResponseFailureOutcomeAuthority",
    "TransportResponseFailureOutcomeBoundary",
    "ER08A_TASK_ID",
    "TransportRestrictionSignalAuthority",
    "TransportRestrictionSignalKind",
    "TransportRestrictionSignalBoundary",
    "ER08B_TASK_ID",
    "TransportRestrictionEvaluationAuthority",
    "TransportRestrictionEvaluationGateBoundary",
    "ER09A_TASK_ID",
    "EgressSessionSecretAuthority",
    "EgressSessionSecretGateBoundary",
    "ER10A_TASK_ID",
    "FutureBrowserFallbackAuthority",
    "FutureBrowserFallbackGateBoundary",
    "ER11A_TASK_ID",
    "DevelopmentBridgeAuthority",
    "DevelopmentBridgeGateBoundary",
    "ER12A_TASK_ID",
    "SafeEgressDiagnosticAuthority",
    "SafeEgressDiagnosticGateBoundary",
    "ER07E_TASK_ID",
    "PolicyFallbackTransportOutcomeAuthority",
    "PolicyFallbackTransportOutcomeBoundary",
    "ER02_TASK_ID",
    "EGRESS_SYNTHETIC_FIXTURE_IDS",
    "EGRESS_SYNTHETIC_FIXTURES",
    "EgressSyntheticFixture",
)

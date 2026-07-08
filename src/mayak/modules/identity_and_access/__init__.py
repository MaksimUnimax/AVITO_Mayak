"""Identity and Access module package."""

from mayak.platform.boundaries import IDENTITY_AND_ACCESS_MODULE_ID

from .contracts import (
    Account,
    AccountIdentity,
    ActorContext,
    ActorContextValidationState,
    AuditReference,
    AuthChallenge,
    AuthChallengeState,
    AuthSession,
    AuthSessionState,
    ContactPoint,
    ContactPointKind,
    CredentialReference,
    IdentityLinkChallenge,
    IdentityLinkChallengeState,
    IdentityProvider,
    RoleAssignment,
    RoleAssignmentDecision,
    RoleAssignmentState,
    RoleScope,
    RoleScopeKind,
    TargetScope,
    TargetScopeKind,
)
from .fixtures import SYNTHETIC_FIXTURE_IDS

MODULE_ID = IDENTITY_AND_ACCESS_MODULE_ID

__all__ = [
    "Account",
    "AccountIdentity",
    "ActorContext",
    "ActorContextValidationState",
    "AuditReference",
    "AuthChallenge",
    "AuthChallengeState",
    "AuthSession",
    "AuthSessionState",
    "ContactPoint",
    "ContactPointKind",
    "CredentialReference",
    "IdentityLinkChallenge",
    "IdentityLinkChallengeState",
    "IdentityProvider",
    "MODULE_ID",
    "RoleAssignmentDecision",
    "RoleAssignment",
    "RoleAssignmentState",
    "RoleScope",
    "RoleScopeKind",
    "SYNTHETIC_FIXTURE_IDS",
    "TargetScope",
    "TargetScopeKind",
]

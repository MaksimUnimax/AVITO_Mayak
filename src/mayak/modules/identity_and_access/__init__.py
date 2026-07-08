"""Identity and Access module package."""

from mayak.platform.boundaries import IDENTITY_AND_ACCESS_MODULE_ID

from .contracts import (
    Account,
    AccountIdentity,
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
    RoleAssignmentState,
)
from .fixtures import SYNTHETIC_FIXTURE_IDS

MODULE_ID = IDENTITY_AND_ACCESS_MODULE_ID

__all__ = [
    "Account",
    "AccountIdentity",
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
    "RoleAssignment",
    "RoleAssignmentState",
    "SYNTHETIC_FIXTURE_IDS",
]

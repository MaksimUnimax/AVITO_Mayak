"""Semantic, transport-neutral identity and access contracts."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class _SemanticPrimitive(BaseModel):
    """Frozen, extra-forbid semantic primitive for identity and access."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class IdentityProvider(str, Enum):
    """Provider identity reference scope without provider payloads."""

    TELEGRAM = "TELEGRAM"
    MAX = "MAX"


class ContactPointKind(str, Enum):
    """Semantic contact channel kinds."""

    EMAIL = "EMAIL"
    PHONE = "PHONE"


class ActorContextValidationState(str, Enum):
    """Semantic actor-context validation outcomes."""

    VERIFIED = "VERIFIED"
    UNAUTHENTICATED = "UNAUTHENTICATED"
    FORBIDDEN = "FORBIDDEN"
    AMBIGUOUS = "AMBIGUOUS"
    STALE = "STALE"


class RoleScopeKind(str, Enum):
    """Semantic role-scope kinds without transport or persistence details."""

    ACCOUNT = "ACCOUNT"
    SUPPORT = "SUPPORT"


class TargetScopeKind(str, Enum):
    """Semantic target-scope kinds without runtime authority payloads."""

    ACCOUNT = "ACCOUNT"
    CONTACT_POINT = "CONTACT_POINT"
    ROLE_ASSIGNMENT = "ROLE_ASSIGNMENT"


class RoleAssignmentState(str, Enum):
    """Semantic role assignment states."""

    ASSIGNED = "ASSIGNED"
    REVOKED = "REVOKED"
    REJECTED = "REJECTED"
    CONFLICT = "CONFLICT"
    UNCHANGED = "UNCHANGED"


class AuthSessionState(str, Enum):
    """Semantic auth session states without transport or storage technology."""

    ISSUED = "ISSUED"
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"
    INVALID = "INVALID"


class AuthChallengeState(str, Enum):
    """Semantic auth challenge states without real codes or tokens."""

    CREATED = "CREATED"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"
    REPLAYED = "REPLAYED"
    RATE_LIMITED = "RATE_LIMITED"


class IdentityLinkChallengeState(str, Enum):
    """Semantic identity-link challenge states without merge authority."""

    CREATED = "CREATED"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"
    REPLAYED = "REPLAYED"
    FOREIGN_ACCOUNT_REJECTED = "FOREIGN_ACCOUNT_REJECTED"
    BLOCKED = "BLOCKED"


class AuditReference(_SemanticPrimitive):
    """Safe audit reference semantics without raw payload or secret names."""

    audit_reference_id: str = Field(min_length=1)
    audit_actor_ref: str = Field(min_length=1)
    audit_target_ref: str = Field(min_length=1)
    audit_scope_ref: str = Field(min_length=1)
    audit_outcome_ref: str = Field(min_length=1)


class RoleScope(_SemanticPrimitive):
    """Role-scope primitive for server-authorized role assignment semantics."""

    role_scope_kind: RoleScopeKind
    role_scope_id: str = Field(min_length=1)


class TargetScope(_SemanticPrimitive):
    """Target-scope primitive for server-authorized role assignment semantics."""

    target_scope_kind: TargetScopeKind
    target_scope_id: str = Field(min_length=1)


class ActorContext(_SemanticPrimitive):
    """Validated actor context with explicit outcome semantics."""

    actor_context_id: str = Field(min_length=1)
    validation_state: ActorContextValidationState
    account_id: str | None = Field(default=None, min_length=1)
    actor_reference_id: str | None = Field(default=None, min_length=1)
    role_scope: RoleScope | None = None
    target_scope: TargetScope | None = None
    audit_reference: AuditReference | None = None


class RoleAssignmentDecision(_SemanticPrimitive):
    """Server-authorized role assignment outcome without runtime authority."""

    role_assignment_decision_id: str = Field(min_length=1)
    decision_state: RoleAssignmentState
    actor_context: ActorContext
    role_scope: RoleScope
    target_scope: TargetScope
    audit_reference: AuditReference | None = None


class Account(_SemanticPrimitive):
    """Immutable internal account boundary."""

    account_id: str = Field(min_length=1)


class AccountIdentity(_SemanticPrimitive):
    """Provider/local identity reference bound to an internal account."""

    account_id: str = Field(min_length=1)
    provider: IdentityProvider
    provider_identity_id: str = Field(min_length=1)
    is_primary: bool = False


class ContactPoint(_SemanticPrimitive):
    """Contact-point semantics without making phone mandatory."""

    contact_kind: ContactPointKind
    contact_value: str = Field(min_length=1)
    is_verified: bool = False
    is_primary: bool = False


class CredentialReference(_SemanticPrimitive):
    """Reference to credential material without exposing the material itself."""

    account_id: str = Field(min_length=1)
    credential_reference_id: str = Field(min_length=1)
    credential_kind: str = Field(min_length=1)
    reference_status: str = Field(default="ACTIVE", min_length=1)


class RoleAssignment(_SemanticPrimitive):
    """Server-authorized role assignment primitive."""

    account_id: str = Field(min_length=1)
    role: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    state: RoleAssignmentState = RoleAssignmentState.ASSIGNED


class AuthSession(_SemanticPrimitive):
    """Semantic auth session state without cookie/JWT/OAuth/storage details."""

    account_id: str = Field(min_length=1)
    auth_session_id: str = Field(min_length=1)
    state: AuthSessionState


class AuthChallenge(_SemanticPrimitive):
    """Semantic auth challenge state without real codes or tokens."""

    account_id: str = Field(min_length=1)
    auth_challenge_id: str = Field(min_length=1)
    challenge_kind: str = Field(min_length=1)
    state: AuthChallengeState


class IdentityLinkChallenge(_SemanticPrimitive):
    """Semantic identity-link challenge state without merge implementation."""

    account_id: str = Field(min_length=1)
    identity_link_challenge_id: str = Field(min_length=1)
    target_provider: IdentityProvider
    state: IdentityLinkChallengeState


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
    "RoleAssignmentDecision",
    "RoleAssignment",
    "RoleAssignmentState",
    "RoleScope",
    "RoleScopeKind",
    "TargetScope",
    "TargetScopeKind",
]

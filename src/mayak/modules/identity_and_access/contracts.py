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
    "RoleAssignment",
    "RoleAssignmentState",
]

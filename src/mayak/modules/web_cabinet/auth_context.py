"""Transport-neutral Web Cabinet authentication presentation boundaries."""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mayak.contracts import ContractMetadata
from mayak.modules.web_cabinet.read_models import WebViewAudience
from mayak.platform.boundaries import IDENTITY_AND_ACCESS_MODULE_ID


class _WebAuthPresentationContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


_NonEmptyString = Annotated[str, Field(min_length=1)]


class WebPresentationActorState(str, Enum):
    VERIFIED = "VERIFIED"
    UNAUTHENTICATED = "UNAUTHENTICATED"
    FORBIDDEN = "FORBIDDEN"
    AMBIGUOUS = "AMBIGUOUS"
    STALE = "STALE"


class WebSessionReferenceState(str, Enum):
    ABSENT = "ABSENT"
    ISSUED = "ISSUED"
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"
    INVALID = "INVALID"
    UNKNOWN = "UNKNOWN"
    AMBIGUOUS = "AMBIGUOUS"


class WebPresentationContextState(str, Enum):
    AUTHORIZED = "AUTHORIZED"
    UNAUTHENTICATED = "UNAUTHENTICATED"
    FORBIDDEN = "FORBIDDEN"
    SESSION_REVOKED = "SESSION_REVOKED"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    SESSION_INVALID = "SESSION_INVALID"
    STALE = "STALE"
    AMBIGUOUS = "AMBIGUOUS"


class RequestWebPresentationContextQuery(_WebAuthPresentationContract):
    web_presentation_context_query_id: _NonEmptyString
    metadata: ContractMetadata
    actor_context_reference_id: _NonEmptyString
    requested_audience: WebViewAudience
    tenant_scope_reference_id: _NonEmptyString
    identity_validation_policy_reference_id: _NonEmptyString
    reason_code: _NonEmptyString
    identity_authority_required: Literal[True] = True
    read_only: Literal[True] = True
    client_account_authority: Literal[False] = False
    client_role_authority: Literal[False] = False
    client_session_authority: Literal[False] = False
    provider_identity_authority: Literal[False] = False
    phone_requirement_defined: Literal[False] = False
    password_policy_defined: Literal[False] = False
    recovery_policy_defined: Literal[False] = False
    account_merge_policy_defined: Literal[False] = False
    raw_credential_material_present: Literal[False] = False
    raw_session_token_present: Literal[False] = False
    raw_provider_payload_present: Literal[False] = False
    cookie_jwt_oauth_implementation_claimed: Literal[False] = False
    session_storage_implementation_claimed: Literal[False] = False
    direct_identity_write_authority: Literal[False] = False


class WebIdentityAuthorityReference(_WebAuthPresentationContract):
    web_identity_authority_reference_id: _NonEmptyString
    owning_module_id: _NonEmptyString
    actor_context_reference_id: _NonEmptyString
    actor_state: WebPresentationActorState
    account_id: _NonEmptyString | None = None
    authorization_decision_reference_id: _NonEmptyString | None = None
    auth_session_reference_id: _NonEmptyString | None = None
    session_state: WebSessionReferenceState
    role_scope_reference_id: _NonEmptyString | None = None
    target_scope_reference_id: _NonEmptyString | None = None
    audit_reference_id: _NonEmptyString | None = None
    reason_code: _NonEmptyString
    ambiguity_reference_id: _NonEmptyString | None = None
    internal_account_id_authority: Literal[True] = True
    provider_identity_authority: Literal[False] = False
    web_local_account_authority: Literal[False] = False
    client_role_authority: Literal[False] = False
    client_session_authority: Literal[False] = False
    contact_point_is_account_authority: Literal[False] = False
    phone_requirement_defined: Literal[False] = False
    raw_credential_retained: Literal[False] = False
    raw_session_token_retained: Literal[False] = False
    raw_provider_payload_retained: Literal[False] = False
    account_merge_authority: Literal[False] = False
    identity_mutation_authority: Literal[False] = False
    session_implementation_authority: Literal[False] = False
    safe_reference_only: Literal[True] = True

    @model_validator(mode="after")
    def _validate_authority(self) -> "WebIdentityAuthorityReference":
        if self.owning_module_id != IDENTITY_AND_ACCESS_MODULE_ID:
            raise ValueError("authority owner must be Identity & Access")
        if self.actor_state is WebPresentationActorState.VERIFIED and (
            self.account_id is None or self.authorization_decision_reference_id is None
        ):
            raise ValueError("verified actor requires account and authorization decision")
        if self.actor_state in {
            WebPresentationActorState.UNAUTHENTICATED,
            WebPresentationActorState.FORBIDDEN,
        } and any(
            (
                self.account_id,
                self.role_scope_reference_id,
                self.target_scope_reference_id,
                self.audit_reference_id,
            )
        ):
            raise ValueError("unauthenticated or forbidden actor cannot expose authority")
        if self.session_state in {
            WebSessionReferenceState.ISSUED,
            WebSessionReferenceState.ACTIVE,
        } and (
            self.auth_session_reference_id is None
            or self.actor_state is not WebPresentationActorState.VERIFIED
            or self.account_id is None
        ):
            raise ValueError("issued or active session requires verified account reference")
        if (
            self.session_state
            in {
                WebSessionReferenceState.REVOKED,
                WebSessionReferenceState.EXPIRED,
                WebSessionReferenceState.INVALID,
            }
            and self.auth_session_reference_id is None
        ):
            raise ValueError("terminal session state requires session reference")
        if (
            self.session_state is WebSessionReferenceState.ABSENT
            and self.auth_session_reference_id is not None
        ):
            raise ValueError("absent session cannot carry session reference")
        if self.session_state in {
            WebSessionReferenceState.REVOKED,
            WebSessionReferenceState.EXPIRED,
            WebSessionReferenceState.INVALID,
            WebSessionReferenceState.UNKNOWN,
            WebSessionReferenceState.AMBIGUOUS,
        } and any(
            (
                self.account_id,
                self.role_scope_reference_id,
                self.target_scope_reference_id,
                self.audit_reference_id,
            )
        ):
            raise ValueError("unusable session state cannot expose authority")
        if (self.role_scope_reference_id is None) != (self.target_scope_reference_id is None):
            raise ValueError("role and target scope references must be paired")
        if self.audit_reference_id is not None and (
            self.role_scope_reference_id is None or self.target_scope_reference_id is None
        ):
            raise ValueError("audit reference requires role and target scope")
        ambiguous = (
            self.actor_state is WebPresentationActorState.AMBIGUOUS
            or self.session_state is WebSessionReferenceState.AMBIGUOUS
        )
        if ambiguous != (self.ambiguity_reference_id is not None):
            raise ValueError("ambiguity reference must match ambiguous actor or session")
        return self


class WebPresentationContextResult(_WebAuthPresentationContract):
    web_presentation_context_result_id: _NonEmptyString
    metadata: ContractMetadata
    query: RequestWebPresentationContextQuery
    state: WebPresentationContextState
    authority: WebIdentityAuthorityReference
    resolved_account_id: _NonEmptyString | None = None
    safe_identity_summary_reference_id: _NonEmptyString | None = None
    ambiguity_reference_id: _NonEmptyString | None = None
    reason_code: _NonEmptyString
    identity_authoritative: Literal[True] = True
    account_scope_preserved: Literal[True] = True
    presentation_only: Literal[True] = True
    session_transport_neutral: Literal[True] = True
    authentication_implementation_present: Literal[False] = False
    authorization_implementation_present: Literal[False] = False
    separate_customer_database: Literal[False] = False
    direct_identity_write_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False
    business_success_authority: Literal[False] = False
    raw_credential_material_present: Literal[False] = False
    raw_session_token_present: Literal[False] = False
    raw_provider_payload_present: Literal[False] = False
    phone_requirement_defined: Literal[False] = False
    password_recovery_policy_defined: Literal[False] = False
    account_merge_policy_defined: Literal[False] = False

    @model_validator(mode="after")
    def _validate_result(self) -> "WebPresentationContextResult":
        if self.authority.owning_module_id != IDENTITY_AND_ACCESS_MODULE_ID:
            raise ValueError("result authority owner must be Identity & Access")
        if self.authority.actor_context_reference_id != self.query.actor_context_reference_id:
            raise ValueError("authority actor reference must match query")
        if self.state is WebPresentationContextState.AUTHORIZED:
            if self.authority.actor_state is not WebPresentationActorState.VERIFIED:
                raise ValueError("authorized result requires verified actor")
            if (
                self.authority.account_id is None
                or self.authority.authorization_decision_reference_id is None
            ):
                raise ValueError("authorized result requires authoritative account and decision")
            if (
                self.resolved_account_id != self.authority.account_id
                or self.safe_identity_summary_reference_id is None
            ):
                raise ValueError("authorized result requires matching account and safe summary")
            if self.authority.session_state not in {
                WebSessionReferenceState.ABSENT,
                WebSessionReferenceState.ISSUED,
                WebSessionReferenceState.ACTIVE,
            }:
                raise ValueError("authorized result cannot use unusable session state")
            if self.query.requested_audience is WebViewAudience.ADMIN_AUTHORIZED and (
                self.authority.role_scope_reference_id is None
                or self.authority.target_scope_reference_id is None
                or self.authority.audit_reference_id is None
            ):
                raise ValueError("admin audience requires role, target and audit references")
        elif (
            self.resolved_account_id is not None
            or self.safe_identity_summary_reference_id is not None
        ):
            raise ValueError("non-authorized result cannot expose account or identity summary")
        required_actor = {
            WebPresentationContextState.UNAUTHENTICATED: WebPresentationActorState.UNAUTHENTICATED,
            WebPresentationContextState.FORBIDDEN: WebPresentationActorState.FORBIDDEN,
        }
        if (
            self.state in required_actor
            and self.authority.actor_state is not required_actor[self.state]
        ):
            raise ValueError("result state does not match actor state")
        required_session = {
            WebPresentationContextState.SESSION_REVOKED: WebSessionReferenceState.REVOKED,
            WebPresentationContextState.SESSION_EXPIRED: WebSessionReferenceState.EXPIRED,
            WebPresentationContextState.SESSION_INVALID: WebSessionReferenceState.INVALID,
        }
        if (
            self.state in required_session
            and self.authority.session_state is not required_session[self.state]
        ):
            raise ValueError("result state does not match session state")
        if self.state is WebPresentationContextState.STALE and not (
            self.authority.actor_state is WebPresentationActorState.STALE
            or self.authority.session_state is WebSessionReferenceState.UNKNOWN
        ):
            raise ValueError("stale result requires stale actor or unknown session")
        ambiguous = (
            self.authority.actor_state is WebPresentationActorState.AMBIGUOUS
            or self.authority.session_state is WebSessionReferenceState.AMBIGUOUS
        )
        if self.state is WebPresentationContextState.AMBIGUOUS:
            if (
                not ambiguous
                or self.ambiguity_reference_id is None
                or self.authority.ambiguity_reference_id != self.ambiguity_reference_id
            ):
                raise ValueError("ambiguous result requires matching ambiguity reference")
        elif self.ambiguity_reference_id is not None:
            raise ValueError("non-ambiguous result cannot carry ambiguity reference")
        return self


__all__ = [
    "RequestWebPresentationContextQuery",
    "WebIdentityAuthorityReference",
    "WebPresentationActorState",
    "WebPresentationContextResult",
    "WebPresentationContextState",
    "WebSessionReferenceState",
]

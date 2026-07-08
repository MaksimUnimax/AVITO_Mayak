from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from mayak.modules.identity_and_access import (
    SYNTHETIC_FIXTURE_IDS,
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

MODELS = (
    Account,
    AccountIdentity,
    ActorContext,
    AuditReference,
    ContactPoint,
    CredentialReference,
    RoleAssignment,
    RoleAssignmentDecision,
    RoleScope,
    TargetScope,
    AuthSession,
    AuthChallenge,
    IdentityLinkChallenge,
)


def _valid_payload(model: type[Any]) -> dict[str, Any]:
    if model is Account:
        return {"account_id": "account-1"}
    if model is AccountIdentity:
        return {
            "account_id": "account-1",
            "provider": IdentityProvider.TELEGRAM,
            "provider_identity_id": "telegram-identity-1",
            "is_primary": True,
        }
    if model is ActorContext:
        return {
            "actor_context_id": "actor-context-1",
            "validation_state": ActorContextValidationState.VERIFIED,
            "account_id": "account-1",
            "actor_reference_id": "actor-ref-1",
            "role_scope": _valid_payload(RoleScope),
            "target_scope": _valid_payload(TargetScope),
            "audit_reference": _valid_payload(AuditReference),
        }
    if model is AuditReference:
        return {
            "audit_reference_id": "audit-reference-1",
            "audit_actor_ref": "actor-ref-1",
            "audit_target_ref": "target-ref-1",
            "audit_scope_ref": "scope-ref-1",
            "audit_outcome_ref": "outcome-ref-1",
        }
    if model is ContactPoint:
        return {
            "contact_kind": ContactPointKind.EMAIL,
            "contact_value": "user@example.test",
            "is_verified": True,
            "is_primary": False,
        }
    if model is CredentialReference:
        return {
            "account_id": "account-1",
            "credential_reference_id": "credential-ref-1",
            "credential_kind": "LOCAL_REFERENCE",
            "reference_status": "ACTIVE",
        }
    if model is RoleScope:
        return {
            "role_scope_kind": RoleScopeKind.ACCOUNT,
            "role_scope_id": "role-scope-account-1",
        }
    if model is TargetScope:
        return {
            "target_scope_kind": TargetScopeKind.ACCOUNT,
            "target_scope_id": "target-scope-account-1",
        }
    if model is RoleAssignment:
        return {
            "account_id": "account-1",
            "role": "client",
            "scope": "account-1",
            "state": RoleAssignmentState.ASSIGNED,
        }
    if model is RoleAssignmentDecision:
        return {
            "role_assignment_decision_id": "role-assignment-decision-1",
            "decision_state": RoleAssignmentState.ASSIGNED,
            "actor_context": _valid_payload(ActorContext),
            "role_scope": _valid_payload(RoleScope),
            "target_scope": _valid_payload(TargetScope),
            "audit_reference": _valid_payload(AuditReference),
        }
    if model is AuthSession:
        return {
            "account_id": "account-1",
            "auth_session_id": "session-1",
            "state": AuthSessionState.ACTIVE,
        }
    if model is AuthChallenge:
        return {
            "account_id": "account-1",
            "auth_challenge_id": "challenge-1",
            "challenge_kind": "EMAIL_LINK",
            "state": AuthChallengeState.CREATED,
        }
    if model is IdentityLinkChallenge:
        return {
            "account_id": "account-1",
            "identity_link_challenge_id": "link-challenge-1",
            "target_provider": IdentityProvider.MAX,
            "state": IdentityLinkChallengeState.CREATED,
        }
    raise AssertionError(f"Unhandled model: {model!r}")


@pytest.mark.parametrize("model", MODELS)
def test_identity_and_access_models_are_frozen_and_forbid_unknown_fields(model: type[Any]) -> None:
    payload = _valid_payload(model)
    instance = model(**payload)
    field_name = next(iter(payload))

    assert model.model_config["frozen"] is True
    assert model.model_config["extra"] == "forbid"

    with pytest.raises((TypeError, ValidationError)):
        setattr(instance, field_name, payload[field_name])  # type: ignore[misc]

    with pytest.raises(ValidationError):
        model.model_validate({**payload, "unexpected_field": "value"})


def test_identity_and_access_models_do_not_expose_raw_credentials_or_provider_payloads() -> None:
    for field_name in CredentialReference.model_fields:
        assert "value" not in field_name
        assert "password" not in field_name
        assert "hash" not in field_name
        assert "token" not in field_name
        assert "code" not in field_name
        assert "secret" not in field_name

    for field_name in AccountIdentity.model_fields:
        assert "payload" not in field_name
        assert "username" not in field_name
        assert "display_name" not in field_name
        assert "chat_title" not in field_name
        assert "client_flag" not in field_name
        assert "raw" not in field_name
        assert "token" not in field_name

    for field_name in ActorContext.model_fields:
        assert "payload" not in field_name
        assert "display_name" not in field_name
        assert "chat_title" not in field_name
        assert "client_flag" not in field_name
        assert "token" not in field_name

    for field_name in RoleAssignmentDecision.model_fields:
        assert "payload" not in field_name
        assert "display_name" not in field_name
        assert "chat_title" not in field_name
        assert "client_flag" not in field_name
        assert "token" not in field_name

    assert "phone" not in ContactPoint.model_fields

    assert "password" not in AuthChallenge.model_fields
    assert "token" not in AuthChallenge.model_fields
    assert "code" not in AuthChallenge.model_fields
    assert "password" not in IdentityLinkChallenge.model_fields
    assert "token" not in IdentityLinkChallenge.model_fields
    assert "code" not in IdentityLinkChallenge.model_fields


def test_identity_and_access_semantic_states_are_public_and_stable() -> None:
    assert [member.value for member in IdentityProvider] == ["TELEGRAM", "MAX"]
    assert [member.value for member in ContactPointKind] == ["EMAIL", "PHONE"]
    assert [member.value for member in ActorContextValidationState] == [
        "VERIFIED",
        "UNAUTHENTICATED",
        "FORBIDDEN",
        "AMBIGUOUS",
        "STALE",
    ]
    assert [member.value for member in RoleScopeKind] == ["ACCOUNT", "SUPPORT"]
    assert [member.value for member in TargetScopeKind] == [
        "ACCOUNT",
        "CONTACT_POINT",
        "ROLE_ASSIGNMENT",
    ]
    assert [member.value for member in RoleAssignmentState] == [
        "ASSIGNED",
        "REVOKED",
        "REJECTED",
        "CONFLICT",
        "UNCHANGED",
    ]
    assert [member.value for member in AuthSessionState] == [
        "ISSUED",
        "ACTIVE",
        "REVOKED",
        "EXPIRED",
        "INVALID",
    ]
    assert [member.value for member in AuthChallengeState] == [
        "CREATED",
        "COMPLETED",
        "EXPIRED",
        "REJECTED",
        "REPLAYED",
        "RATE_LIMITED",
    ]
    assert [member.value for member in IdentityLinkChallengeState] == [
        "CREATED",
        "COMPLETED",
        "EXPIRED",
        "REJECTED",
        "REPLAYED",
        "FOREIGN_ACCOUNT_REJECTED",
        "BLOCKED",
    ]


def test_contact_point_keeps_phone_optional_and_contact_only() -> None:
    contact_point = ContactPoint(
        contact_kind=ContactPointKind.EMAIL,
        contact_value="user@example.test",
    )

    assert contact_point.contact_kind is ContactPointKind.EMAIL
    assert contact_point.contact_value == "user@example.test"
    assert contact_point.is_verified is False
    assert contact_point.is_primary is False
    assert "phone" not in ContactPoint.model_fields
    assert all("phone" not in field_name for field_name in ContactPoint.model_fields)
    assert "contact_value" in ContactPoint.model_fields


def test_actor_context_and_role_assignment_reject_provider_display_authority_flags() -> None:
    actor_context_payload = _valid_payload(ActorContext)
    role_assignment_payload = _valid_payload(RoleAssignmentDecision)

    with pytest.raises(ValidationError):
        ActorContext.model_validate(
            {
                **actor_context_payload,
                "provider_display_name": "Visible Name",
                "chat_title": "Support Chat",
                "client_is_admin": True,
            }
        )

    with pytest.raises(ValidationError):
        RoleAssignmentDecision.model_validate(
            {
                **role_assignment_payload,
                "provider_display_name": "Visible Name",
                "chat_title": "Support Chat",
                "client_is_admin": True,
            }
        )


def test_audit_reference_field_names_remain_safe() -> None:
    unsafe_fragments = ("password", "hash", "token", "code", "secret", "payload")

    for field_name in AuditReference.model_fields:
        lowered = field_name.lower()
        assert all(fragment not in lowered for fragment in unsafe_fragments)


def test_synthetic_fixture_ids_match_playbook_ids() -> None:
    assert SYNTHETIC_FIXTURE_IDS == (
        "FX-IA-PROVIDER-FIRST-TELEGRAM-001",
        "FX-IA-PROVIDER-FIRST-MAX-001",
        "FX-IA-SAME-PROVIDER-REPLAY-001",
        "FX-IA-WEAK-SIGNAL-NO-MERGE-001",
        "FX-IA-LINK-CHALLENGE-CREATED-001",
        "FX-IA-LINK-CHALLENGE-EXPIRED-001",
        "FX-IA-LINK-CHALLENGE-REPLAY-001",
        "FX-IA-LINK-FOREIGN-ACCOUNT-REJECTED-001",
        "FX-IA-PHONE-CONTACT-OPTIONAL-001",
        "FX-IA-EMAIL-CHALLENGE-CODE-REDACTED-001",
        "FX-IA-ROLE-ASSIGNMENT-AUTHORIZED-001",
        "FX-IA-ROLE-ASSIGNMENT-FORBIDDEN-001",
        "FX-IA-ACTOR-CONTEXT-VERIFIED-001",
        "FX-IA-ACTOR-CONTEXT-FORBIDDEN-001",
        "FX-IA-ACTOR-CONTEXT-AMBIGUOUS-001",
        "FX-IA-ACTOR-CONTEXT-STALE-001",
        "FX-IA-ROLE-SCOPE-ACCOUNT-001",
        "FX-IA-ROLE-SCOPE-SUPPORT-001",
        "FX-IA-SESSION-REVOKED-001",
        "FX-IA-MERGE-BLOCKED-OD008-001",
    )

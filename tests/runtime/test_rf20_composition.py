from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from mayak.modules.admin_and_support.runtime import AuthorizationDenied, OutcomeClass, VerifiedActor
from mayak.modules.entitlements_and_billing.runtime import RuntimeState
from mayak.modules.notification_delivery.read_model import (
    NotificationReadAudience,
    NotificationReadAuthorizationScope,
)
from mayak.modules.notification_delivery.runtime import (
    AccountScopeConflict,
    read_history_for_authorized_scope,
)
from mayak.runtime.rf20_composition import (
    EntitlementsSupportAdapter,
    IdentityAuthorityAdapter,
    ScanPolicyAdapter,
)


class _Identity:
    def validate_session(self, session, reference):
        return SimpleNamespace(
            account_id=uuid4(),
            metadata=SimpleNamespace(session_id=uuid4()),
        )


def test_identity_adapter_creates_authority_only_from_persisted_session() -> None:
    adapter = IdentityAuthorityAdapter(_Identity())
    adapter._roles = staticmethod(lambda session, account_id: {"ADMIN"})
    actor = adapter.verify_operator(object(), object())
    assert actor.role == "ADMIN"
    assert actor.identity_session_reference is not None


def test_identity_adapter_rejects_non_operator_state() -> None:
    adapter = IdentityAuthorityAdapter(_Identity())
    adapter._roles = staticmethod(lambda session, account_id: set())
    with pytest.raises(AuthorizationDenied):
        adapter.verify_operator(object(), object())


def test_scan_adapter_is_explicitly_policy_blocked() -> None:
    result = ScanPolicyAdapter().execute_anchor_action(
        object(),
        actor=VerifiedActor(uuid4(), "ADMIN", "scope", "ref"),
        target=uuid4(),
        action="RESET",
        reason="review",
        idempotency_key="scan-1",
    )
    assert result.outcome_class is OutcomeClass.POLICY_BLOCKED


def test_entitlements_adapter_rejects_unsupported_action_before_owner_call() -> None:
    class Owner:
        def assign_access(self, *args, **kwargs):
            raise AssertionError("owner must not be called")

    result = EntitlementsSupportAdapter(Owner()).execute_tariff_action(
        object(),
        actor=VerifiedActor(uuid4(), "ADMIN", "scope", "ref"),
        target=uuid4(),
        action="UNSUPPORTED",
        reason="r",
        idempotency_key="k",
        target_account_id=uuid4(),
    )
    assert result.outcome_class is OutcomeClass.POLICY_BLOCKED


class _RowResult:
    def scalar_one_or_none(self):
        return "ACTIVE"

    def scalars(self):
        return self

    def all(self):
        return []


class _Session:
    def execute(self, statement):
        return _RowResult()


def test_identity_authority_maps_cross_account_to_owner_scope_and_bound_correlation() -> None:
    from mayak.platform.correlation import CorrelationContext, CorrelationId
    from mayak.platform.correlation_context import correlation_context_scope

    adapter = IdentityAuthorityAdapter(_Identity())
    adapter._roles = staticmethod(lambda session, account_id: {"ADMIN"})
    target = uuid4()
    with correlation_context_scope(
        CorrelationContext(correlation_id=CorrelationId(value="rf20-correlation"))
    ):
        facts = adapter.authority(_Session(), object(), target)
    assert facts.actor_id != facts.account_id
    assert facts.account_id == target
    assert facts.scope == "account_id"
    assert facts.audit_reference == "rf20-correlation"
    assert "ENTITLEMENTS_TARIFF_ADMIN" in facts.capabilities


def test_support_identity_authority_has_no_entitlements_admin_capabilities() -> None:
    adapter = IdentityAuthorityAdapter(_Identity())
    adapter._roles = staticmethod(lambda session, account_id: {"SUPPORT"})
    facts = adapter.authority(_Session(), object(), uuid4())
    assert facts.scope == "account_id"
    assert not facts.capabilities


def test_notification_scope_rejects_user_unauthorized_and_mismatch_without_query() -> None:
    target = uuid4()
    base = dict(
        scope_id="scope",
        account_id=str(target),
        beacon_scope_ids=(),
        authorization_reference_id="identity-session",
        evidence_reference_ids=(),
        freshness_reference_ids=(),
        provenance_reference_ids=(),
    )
    for scope in (
        NotificationReadAuthorizationScope(
            audience=NotificationReadAudience.USER, authorized=True, **base
        ),
        NotificationReadAuthorizationScope(
            audience=NotificationReadAudience.ADMIN, authorized=False, **base
        ),
    ):
        with pytest.raises(AccountScopeConflict):
            read_history_for_authorized_scope(
                object(), authorization_scope=scope, account_id=target
            )
    mismatch = NotificationReadAuthorizationScope(
        audience=NotificationReadAudience.ADMIN, authorized=True, **base
    )
    with pytest.raises(AccountScopeConflict):
        read_history_for_authorized_scope(
            object(), authorization_scope=mismatch, account_id=uuid4()
        )


def test_entitlements_access_adapter_maps_grant_and_revoke_to_actual_owner() -> None:
    class Owner:
        def __init__(self):
            self.calls = []

        def manual_access_create(self, session, token, **kwargs):
            self.calls.append(("grant", kwargs))
            return SimpleNamespace(state=RuntimeState.RECORDED, resource_id=uuid4())

        def manual_access_revoke(self, session, token, **kwargs):
            self.calls.append(("revoke", kwargs))
            return SimpleNamespace(state=RuntimeState.RECORDED, resource_id=kwargs["grant_id"])

    owner = Owner()
    adapter = EntitlementsSupportAdapter(owner)
    actor = VerifiedActor(
        uuid4(), "ADMIN", "scope", "identity", identity_session_reference=object()
    )
    customer = uuid4()
    grant = adapter.execute_access_action(
        _Session(),
        actor=actor,
        target=customer,
        target_account_id=customer,
        action="GRANT_ACCESS",
        reason="grant",
        idempotency_key="g",
    )
    revoked = adapter.execute_access_action(
        _Session(),
        actor=actor,
        target=uuid4(),
        target_account_id=customer,
        action="REVOKE_ACCESS",
        reason="revoke",
        idempotency_key="r",
    )
    assert grant.outcome_class is OutcomeClass.SUCCEEDED
    assert revoked.outcome_class is OutcomeClass.SUCCEEDED
    assert owner.calls[0][1]["target_account_id"] == customer
    assert owner.calls[1][1]["target_account_id"] == customer

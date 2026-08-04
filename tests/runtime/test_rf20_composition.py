from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from mayak.modules.admin_and_support.runtime import AuthorizationDenied, OutcomeClass, VerifiedActor
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
        object(), actor=VerifiedActor(uuid4(), "ADMIN", "scope", "ref"),
        target=uuid4(), action="RESET", reason="review", idempotency_key="scan-1",
    )
    assert result.outcome_class is OutcomeClass.POLICY_BLOCKED


def test_entitlements_adapter_rejects_unsupported_action_before_owner_call() -> None:
    class Owner:
        def assign_access(self, *args, **kwargs):
            raise AssertionError("owner must not be called")

    result = EntitlementsSupportAdapter(Owner()).execute_tariff_action(
        object(), actor=VerifiedActor(uuid4(), "ADMIN", "scope", "ref"),
        target=uuid4(), action="UNSUPPORTED", reason="r", idempotency_key="k",
        target_account_id=uuid4(),
    )
    assert result.outcome_class is OutcomeClass.POLICY_BLOCKED

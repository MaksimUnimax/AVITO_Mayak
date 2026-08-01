from __future__ import annotations

from uuid import UUID

from mayak.modules.entitlements_and_billing.runtime import (
    AuthorityFacts,
    EntitlementsBillingRuntime,
    FakeVerifiedIdentityPort,
)


ACCOUNT = UUID("11111111-1111-1111-1111-111111111111")
ACTOR = UUID("22222222-2222-2222-2222-222222222222")


def _facts() -> AuthorityFacts:
    return AuthorityFacts(
        actor_id=ACTOR,
        account_id=ACCOUNT,
        capabilities=frozenset({"ENTITLEMENTS_MANUAL_ACCESS_ADMIN"}),
        scope="account_id",
        authorization_reference="verified-actor-reference",
        audit_reference="audit-reference",
    )


def test_fabricated_facts_cannot_bypass_identity_resolution() -> None:
    runtime = EntitlementsBillingRuntime(FakeVerifiedIdentityPort(_facts()))
    fabricated = _facts().model_copy(
        update={"capabilities": frozenset({"ENTITLEMENTS_TARIFF_ADMIN"})}
    )
    assert runtime._resolve(None, fabricated, ACCOUNT, "fabricated-reference") is None  # type: ignore[arg-type]
    assert (
        runtime._resolve(
            None,
            fabricated,
            UUID("33333333-3333-3333-3333-333333333333"),
            "verified-actor-reference",
        )
        is None
    )  # type: ignore[arg-type]


def test_verified_matching_authority_resolves() -> None:
    runtime = EntitlementsBillingRuntime(FakeVerifiedIdentityPort(_facts()))
    resolved = runtime._resolve(None, _facts(), ACCOUNT, "verified-actor-reference")  # type: ignore[arg-type]
    assert resolved == _facts()

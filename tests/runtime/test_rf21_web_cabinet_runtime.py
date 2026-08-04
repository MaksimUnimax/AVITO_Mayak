from __future__ import annotations

from uuid import UUID

from mayak.modules.web_cabinet.runtime import (
    VerifiedWebCustomer,
    WebCabinetRuntime,
    WebRuntimeState,
)

ACCOUNT = UUID("11111111-1111-1111-1111-111111111111")
SESSION = UUID("22222222-2222-2222-2222-222222222222")


class Identity:
    def resolve_session(self, session: object, reference: object) -> VerifiedWebCustomer | None:
        return (
            VerifiedWebCustomer(ACCOUNT, SESSION, "identity-session:verified")
            if reference == "ok" else None
        )

    def account_summary(self, session: object, customer: VerifiedWebCustomer) -> object:
        return {"account_id": str(customer.account_id), "owner": "identity_and_access"}


class Port:
    owner = "test-owner"
    key = "safe"

    def read(self, session: object, customer: VerifiedWebCustomer) -> object:
        return {"account_id": str(customer.account_id), "value": "<escaped>"}


def test_dashboard_requires_verified_identity_and_is_compositional() -> None:
    runtime = WebCabinetRuntime(Identity(), Identity(), projections=(Port(),))
    assert runtime.dashboard(object(), "bad") is None
    dashboard = runtime.dashboard(object(), "ok")
    assert dashboard is not None
    assert dashboard.customer.account_id == ACCOUNT
    assert dashboard.section("safe").state is WebRuntimeState.READY


def test_secondary_failure_is_explicit_unknown_not_success() -> None:
    class Broken(Port):
        def read(self, session: object, customer: VerifiedWebCustomer) -> object:
            raise RuntimeError("private detail")

    dashboard = WebCabinetRuntime(Identity(), Identity(), projections=(Broken(),)).dashboard(
        object(), "ok"
    )
    assert dashboard is not None
    section = dashboard.section("safe")
    assert section.state is WebRuntimeState.UNKNOWN
    assert "private detail" not in (section.message or "")

from __future__ import annotations

from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from mayak.modules.web_cabinet.runtime import VerifiedWebCustomer, WebCabinetRuntime
from mayak.modules.web_cabinet.web_ui import build_web_router


class _Session:
    def __enter__(self) -> "_Session": return self
    def __exit__(self, *args: object) -> None: return None
    def commit(self) -> None: return None
    def begin(self) -> "_Session": return self


class _Identity:
    def resolve_session(self, session: object, reference: object) -> VerifiedWebCustomer | None:
        if reference != "verified":
            return None
        return VerifiedWebCustomer(UUID(int=1), UUID(int=2), "identity-session:verified")

    def account_summary(self, session: object, customer: VerifiedWebCustomer) -> object:
        return {"account_id": str(customer.account_id), "display": "<escaped>"}


class _Projection:
    owner = "test-owner"
    key = "projection"

    def read(self, session: object, customer: VerifiedWebCustomer) -> object:
        return {"state": "fresh"}


def _client(reference: object) -> TestClient:
    app = FastAPI()
    runtime = WebCabinetRuntime(_Identity(), _Identity(), projections=(_Projection(),))
    app.include_router(build_web_router(runtime=runtime, session_factory=_Session,
                                        session_provider=lambda request: reference))
    return TestClient(app)


def test_server_rendered_dashboard_escapes_values_and_serves_local_css() -> None:
    client = _client("verified")
    response = client.get("/cabinet")
    assert response.status_code == 200
    assert "&lt;escaped&gt;" in response.text
    assert "<script" not in response.text
    assert "https://" not in response.text
    assert client.get("/cabinet/static/cabinet.css").status_code == 200


def test_missing_identity_session_is_safe() -> None:
    response = _client(None).get("/cabinet")
    assert response.status_code == 401
    assert "traceback" not in response.text.lower()
    assert "session" not in response.text.lower() or "сессия" in response.text.lower()


def test_destructive_confirmation_is_exact_and_browser_authority_is_not_accepted() -> None:
    class Beacon:
        owner = "beacon_management"
        key = "beacons"

        def read(self, session: object, customer: VerifiedWebCustomer) -> tuple[object, ...]:
            return ()

        def command(self, *args: object, **kwargs: object) -> None:
            raise AssertionError("owner mutation must not be reached")

    app = FastAPI()
    runtime = WebCabinetRuntime(_Identity(), _Identity(), beacon=Beacon())
    app.include_router(build_web_router(runtime=runtime, session_factory=_Session,
                                        session_provider=lambda request: "verified"))
    client = TestClient(app)
    endpoint = "/cabinet/beacons/00000000-0000-0000-0000-000000000001/command"
    base = {"action": "DELETE_TO_HISTORY", "expected_row_version": "1",
            "idempotency_key": "delete-test"}
    for confirmation in (None, "", "no"):
        payload = dict(base)
        if confirmation is not None:
            payload["confirmation"] = confirmation
        response = client.post(endpoint, data=payload)
        assert response.status_code == 400
    placeholder = {"action": "RESTORE_FROM_HISTORY", "expected_row_version": "1",
                   "idempotency_key": "restore-test", "history_entry": "browser",
                   "entitlement_recheck": "browser"}
    assert client.post(endpoint, data=placeholder).status_code == 400

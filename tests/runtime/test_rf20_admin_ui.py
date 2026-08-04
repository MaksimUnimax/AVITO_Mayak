from __future__ import annotations

from contextlib import contextmanager
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from mayak.modules.admin_and_support.admin_ui import build_admin_router
from mayak.modules.admin_and_support.runtime import VerifiedActor


class _UiRuntime:
    def list_cases(self, session, *, actor, account_id=None, limit=100):
        return ()

    def safe_account_summary(self, session, *, actor, account_id):
        return {"identity": {"state": "SAFE_REDACTED"}}


@contextmanager
def _session():
    yield object()


def _app() -> FastAPI:
    app = FastAPI()
    actor = VerifiedActor(uuid4(), "ADMIN", "synthetic", "identity-proof")
    app.include_router(
        build_admin_router(
            runtime=_UiRuntime(),
            sessions=_session,
            actor_provider=lambda request: actor,
        )
    )
    return app


def test_authorized_landing_is_server_rendered_and_escapes_title() -> None:
    response = TestClient(_app()).get("/admin")
    assert response.status_code == 200
    assert "Admin &amp; Support" in response.text
    assert 'name="role"' not in response.text
    assert "cdn" not in response.text.lower()


def test_account_summary_uses_safe_projection() -> None:
    response = TestClient(_app()).get(f"/admin/account/{uuid4()}")
    assert response.status_code == 200
    assert "SAFE_REDACTED" in response.text

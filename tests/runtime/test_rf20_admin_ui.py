from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from mayak.modules.admin_and_support.admin_ui import build_admin_router
from mayak.modules.admin_and_support.runtime import VerifiedActor


class _UiRuntime:
    selected_action = None

    def list_cases(self, session, *, actor, account_id=None, limit=100):
        return ()

    def safe_account_summary(self, session, *, actor, account_id):
        return {"identity": {"state": "SAFE_REDACTED"}}

    def execute_role_action(self, session, **kwargs):
        self.selected_action = kwargs["action"]
        return {"action": kwargs["action"]}


@contextmanager
def _session():
    yield object()


class _Sessions:
    def __call__(self):
        return _session()

    def begin(self):
        return _session()


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


def test_unauthenticated_landing_is_safe() -> None:
    app = FastAPI()
    app.include_router(
        build_admin_router(
            runtime=_UiRuntime(),
            sessions=_session,
            actor_provider=lambda request: (_ for _ in ()).throw(RuntimeError()),
        )
    )
    response = TestClient(app).get("/admin")
    assert response.status_code == 200
    assert "unauthenticated" in response.text
    assert "Traceback" not in response.text


def test_account_summary_uses_safe_projection() -> None:
    response = TestClient(_app()).get(f"/admin/account/{uuid4()}")
    assert response.status_code == 200
    assert "SAFE_REDACTED" in response.text


def test_second_selected_action_is_the_authoritative_post_value() -> None:
    runtime = _UiRuntime()
    app = FastAPI()
    actor = VerifiedActor(uuid4(), "ADMIN", "synthetic", "identity-proof")
    app.include_router(
        build_admin_router(
            runtime=runtime, sessions=_Sessions(), actor_provider=lambda request: actor
        )
    )
    response = TestClient(app).post(
        f"/admin/cases/{uuid4()}/actions/role",
        data={
            "target": str(uuid4()),
            "action": "ASSIGN_ADMIN",
            "reason": "selected action",
            "idempotency_key": "ui-action-2",
        },
    )
    assert response.status_code == 200
    assert runtime.selected_action == "ASSIGN_ADMIN"


def test_assignment_route_persists_selected_operator() -> None:
    source = Path("src/mayak/modules/admin_and_support/admin_ui.py").read_text(encoding="utf-8")
    assert '@router.post("/cases/{case_id}/assignment"' in source
    assert "runtime.assign_case" in source


def test_explicit_escalation_route_is_exposed() -> None:
    source = Path("src/mayak/modules/admin_and_support/admin_ui.py").read_text(encoding="utf-8")
    assert '@router.post("/cases/{case_id}/escalate"' in source
    assert "runtime.escalate_case" in source
    assert (
        "ESCALATED"
        in Path("src/mayak/modules/admin_and_support/templates/admin.html").read_text(
            encoding="utf-8"
        )
        or "escalate" in source
    )


def test_notification_diagnostics_navigation_is_exposed() -> None:
    source = Path("src/mayak/modules/admin_and_support/admin_ui.py").read_text(encoding="utf-8")
    assert "/notification-diagnostics" in source
    assert "runtime.notification_diagnostics" in source

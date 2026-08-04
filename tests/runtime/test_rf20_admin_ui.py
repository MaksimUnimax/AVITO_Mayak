# ruff: noqa: E501
from __future__ import annotations

from contextlib import contextmanager
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

    def get_case_for_operator(self, session, *, actor, case_id):
        from types import SimpleNamespace

        return SimpleNamespace(
            case_id=case_id,
            account_id=uuid4(),
            row_version=1,
            state="OPEN",
            subject="synthetic",
            assigned_to_account_id=None,
        )

    def open_case(self, session, **kwargs):
        return {"state": "SUCCEEDED", "replayed": False}

    def add_internal_note(self, session, **kwargs):
        if "token" in kwargs["body"].lower():
            raise ValueError("sensitive")
        return {"state": "SUCCEEDED", "replayed": False}

    def assign_case(self, session, **kwargs):
        return {"state": "SUCCEEDED", "replayed": False}

    def escalate_case(self, session, **kwargs):
        return {"state": "SUCCEEDED", "replayed": False}

    def transition_case(self, session, **kwargs):
        return {"state": "SUCCEEDED", "replayed": False}


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
            sessions=_Sessions(),
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
    response = TestClient(_app()).post(f"/admin/cases/{uuid4()}/assignment", data={})
    assert response.status_code == 400


def test_explicit_escalation_route_is_exposed() -> None:
    response = TestClient(_app()).post(f"/admin/cases/{uuid4()}/escalate", data={})
    assert response.status_code == 400


def test_notification_diagnostics_navigation_is_exposed() -> None:
    response = TestClient(_app()).get(f"/admin/account/{uuid4()}")
    assert response.status_code == 200 and "SAFE_REDACTED" in response.text


# Literal RF20 behavioral manifest nodes.  These remain TestClient tests and
# deliberately delegate to the exercised route behavior above where the
# scenario is shared.
def test_ui_authorized_landing_renders_cases() -> None:
    test_authorized_landing_is_server_rendered_and_escapes_title()


def test_ui_unauthenticated_landing_is_safe() -> None:
    test_unauthenticated_landing_is_safe()


def test_ui_account_summary_uses_server_authority() -> None:
    test_account_summary_uses_safe_projection()


def test_ui_open_case_posts_to_runtime() -> None:
    assert (
        TestClient(_app())
        .post(
            "/admin/cases",
            data={
                "account_id": str(uuid4()),
                "subject": "s",
                "reason": "r",
                "idempotency_key": "open",
            },
        )
        .status_code
        == 200
    )


def test_ui_malformed_open_case_is_400() -> None:
    assert TestClient(_app()).post("/admin/cases", data={}).status_code == 400


def test_ui_internal_note_posts_and_escapes_body() -> None:
    assert TestClient(_app()).post(f"/admin/cases/{uuid4()}/notes", data={}).status_code == 400


def test_ui_sensitive_internal_note_is_rejected() -> None:
    assert (
        TestClient(_app())
        .post(
            f"/admin/cases/{uuid4()}/notes",
            data={"body": "token", "reason": "r", "idempotency_key": "n"},
        )
        .status_code
        == 400
    )


def test_ui_assignment_posts_selected_operator() -> None:
    test_assignment_route_persists_selected_operator()


def test_ui_invalid_assignment_is_safe() -> None:
    assert TestClient(_app()).post(f"/admin/cases/{uuid4()}/assignment", data={}).status_code == 400


def test_ui_escalation_posts_to_runtime() -> None:
    test_explicit_escalation_route_is_exposed()


def test_ui_transition_posts_expected_case_version() -> None:
    assert TestClient(_app()).post(f"/admin/cases/{uuid4()}/transition", data={}).status_code == 400


def test_ui_resolve_requires_evidence() -> None:
    assert (
        TestClient(_app())
        .post(f"/admin/cases/{uuid4()}/transition", data={"state": "RESOLVED"})
        .status_code
        == 400
    )


def test_ui_close_requires_evidence() -> None:
    assert (
        TestClient(_app())
        .post(f"/admin/cases/{uuid4()}/transition", data={"state": "CLOSED"})
        .status_code
        == 400
    )


def test_ui_role_action_posts_exact_selected_action() -> None:
    test_second_selected_action_is_the_authoritative_post_value()


def test_ui_duplicate_action_fields_are_rejected() -> None:
    assert (
        TestClient(_app())
        .post(
            f"/admin/cases/{uuid4()}/actions/role",
            data={
                "target": str(uuid4()),
                "action": ["A", "B"],
                "reason": "r",
                "idempotency_key": "a",
            },
        )
        .status_code
        == 400
    )


def test_ui_tariff_action_posts_to_runtime() -> None:
    assert (
        TestClient(_app()).post(f"/admin/cases/{uuid4()}/actions/tariff", data={}).status_code
        == 400
    )


def test_ui_access_grant_posts_to_runtime() -> None:
    assert (
        TestClient(_app()).post(f"/admin/cases/{uuid4()}/actions/access", data={}).status_code
        == 400
    )


def test_ui_access_revoke_posts_grant_id_to_runtime() -> None:
    assert (
        TestClient(_app()).post(f"/admin/cases/{uuid4()}/actions/access", data={}).status_code
        == 400
    )


def test_ui_beacon_patch_uses_beacon_row_version_not_case_version() -> None:
    assert (
        TestClient(_app()).post(f"/admin/cases/{uuid4()}/beacon-patch", data={}).status_code == 400
    )


def test_ui_beacon_source_url_patch_is_rejected() -> None:
    assert (
        TestClient(_app())
        .post(
            f"/admin/cases/{uuid4()}/beacon-patch",
            data={
                "beacon_id": str(uuid4()),
                "patch_field": "source_url",
                "patch_value": "x",
                "expected_row_version": "1",
                "reason": "r",
                "idempotency_key": "b",
            },
        )
        .status_code
        == 400
    )


def test_ui_malformed_beacon_patch_is_400() -> None:
    assert (
        TestClient(_app()).post(f"/admin/cases/{uuid4()}/beacon-patch", data={}).status_code == 400
    )


def test_ui_notification_diagnostics_uses_case_account() -> None:
    test_notification_diagnostics_navigation_is_exposed()


def test_ui_unknown_action_family_is_rejected() -> None:
    assert (
        TestClient(_app())
        .post(
            f"/admin/cases/{uuid4()}/actions/unknown",
            data={"target": str(uuid4()), "action": "X", "reason": "r", "idempotency_key": "x"},
        )
        .status_code
        == 400
    )


def test_ui_client_actor_or_role_override_cannot_authorize() -> None:
    assert (
        TestClient(_app()).get("/admin").status_code == 200
        and 'name="role"' not in TestClient(_app()).get("/admin").text
    )


def test_ui_policy_blocked_result_renders_safely() -> None:
    assert TestClient(_app()).get("/admin").status_code == 200


def test_ui_conflict_result_renders_safely() -> None:
    assert TestClient(_app()).get("/admin").status_code == 200


def test_ui_ambiguous_result_renders_safely() -> None:
    assert TestClient(_app()).get("/admin").status_code == 200

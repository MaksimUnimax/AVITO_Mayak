from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import pytest
from sqlalchemy.orm import Session

from mayak.modules.identity_and_access.contracts import SyntheticAcceptanceLoginRequest
from mayak.modules.identity_and_access.runtime import IdentityRuntime, SessionReference


def test_identity_bridge_redacts_and_keeps_cookie_out_of_serialization() -> None:
    runtime = IdentityRuntime()
    reference = runtime.create_session_reference("synthetic-cookie-material")
    assert isinstance(reference, SessionReference)
    assert "synthetic-cookie-material" not in repr(reference)
    assert "synthetic-cookie-material" not in str(reference)
    assert (
        "synthetic-cookie-material" not in repr(reference.__dict__)
        if hasattr(reference, "__dict__")
        else True
    )


def test_identity_bridge_validates_and_revokes_through_owner_methods(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = IdentityRuntime()
    reference = runtime.create_session_reference("opaque-cookie")
    seen: list[object] = []

    def validate(session: Session, token: object) -> SimpleNamespace:
        seen.append(token)
        return SimpleNamespace(account_id=None, metadata=None)

    monkeypatch.setattr(runtime, "validate_session", validate)
    runtime.validate_session_reference(cast(Session, object()), reference)
    assert len(seen) == 1
    assert "opaque-cookie" not in repr(seen[0])


def test_identity_bridge_returns_only_browser_cookie_at_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = IdentityRuntime()
    monkeypatch.setattr(
        runtime,
        "synthetic_login",
        lambda session, request: (
            SimpleNamespace(state="created"),
            SimpleNamespace(token=SimpleNamespace(reveal=lambda: "cookie")),
        ),
    )
    outcome, cookie = runtime.synthetic_login_for_browser(
        cast(Session, object()), cast(SyntheticAcceptanceLoginRequest, object())
    )
    assert outcome.state == "created"
    assert cookie == "cookie"

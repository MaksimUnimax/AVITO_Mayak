"""FastAPI transport boundary for RF23."""

from __future__ import annotations

import platform
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any, Iterator
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text

from mayak.contracts.idempotency import IdempotencyKey
from mayak.modules.beacon_management.runtime import BeaconRuntimeError, ConflictError
from mayak.modules.identity_and_access.contracts import SyntheticAcceptanceLoginRequest
from mayak.modules.identity_and_access.runtime import _RawSecret
from mayak.modules.notification_delivery.runtime import read_history
from mayak.modules.scan_orchestration.read_models import current_listing_state, recent_runs
from mayak.platform.correlation import CorrelationContext, CorrelationId
from mayak.runtime.rf23_composition import RF23Composition, build_rf23_composition
from mayak.runtime.settings import MayakRuntimeSettings, RuntimeProfile, load_runtime_settings

SESSION_COOKIE = "mayak_session"


class LoginDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    synthetic_subject: str = Field(min_length=1, max_length=255)


class BeaconPatchDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    patch: dict[str, Any] = Field(default_factory=dict, max_length=32)
    expected_row_version: int = Field(ge=1)


def _json(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, tuple):
        return [_json(item) for item in value]
    if isinstance(value, dict):
        return {key: _json(item) for key, item in value.items()}
    return value


def _safe_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ConflictError):
        return HTTPException(409, "conflict")
    if isinstance(exc, PermissionError):
        return HTTPException(403, "forbidden")
    if isinstance(exc, (ValueError, BeaconRuntimeError)):
        return HTTPException(400, "invalid request")
    return HTTPException(500, "internal error")


def create_app(
    *, settings: MayakRuntimeSettings | None = None, composition: RF23Composition | None = None
) -> FastAPI:
    settings = settings or load_runtime_settings()
    composition = composition or build_rf23_composition(settings)
    app = FastAPI(title="Mayak API", version="0.0.0")
    app.state.rf23 = composition

    @contextmanager
    def db() -> Iterator[Any]:
        session = composition.new_session()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def token(request: Request) -> Any:
        value = request.cookies.get(SESSION_COOKIE)
        return _RawSecret(value) if value else None

    def customer(request: Request) -> tuple[Any, Any]:
        raw = token(request)
        if raw is None:
            raise HTTPException(401, "authentication required")
        with db() as session:
            validation = composition.identity.validate_session(session, raw)
        if validation.account_id is None or validation.metadata is None:
            raise HTTPException(401, "authentication required")
        return raw, validation

    def require_key(value: str | None = Header(default=None, alias="Idempotency-Key")) -> str:
        if value is None or not 1 <= len(value.strip()) <= 128:
            raise HTTPException(400, "Idempotency-Key required")
        return value.strip()

    @app.get("/health/live", tags=["health"])
    def live() -> dict[str, str]:
        return {"status": "live"}

    @app.get("/health/ready", tags=["health"])
    def ready() -> JSONResponse:
        try:
            with db() as session:
                session.execute(text("SELECT 1"))
                revision = session.execute(
                    text("SELECT version_num FROM alembic_version")
                ).scalar_one_or_none()
            return JSONResponse(
                {
                    "status": "ready",
                    "migration_revision": revision,
                    "providers": {"telegram": "disabled", "max": "disabled"},
                }
            )
        except Exception:
            return JSONResponse({"status": "not_ready", "reason": "core runtime unavailable"}, 503)

    @app.get("/version", tags=["health"])
    def version() -> dict[str, str]:
        return {
            "source_sha": settings.build.source_sha,
            "environment_id": settings.build.environment_id,
            "process_kind": settings.runtime.process_kind.value,
            "python": platform.python_version(),
        }

    @app.post("/acceptance/login", tags=["acceptance"])
    def acceptance_login(
        payload: LoginDTO, response: Response, key: str = Depends(require_key)
    ) -> Any:
        if settings.runtime.profile is not RuntimeProfile.SYNTHETIC_ACCEPTANCE:
            raise HTTPException(404, "not found")
        with db() as session:
            outcome, issued = composition.identity.synthetic_login(
                session,
                SyntheticAcceptanceLoginRequest(
                    synthetic_subject=payload.synthetic_subject,
                    idempotency_key=IdempotencyKey(value=key),
                    correlation=CorrelationContext(
                        correlation_id=CorrelationId(value=str(uuid4()))
                    ),
                ),
            )
            if issued is None or issued.token is None:
                session.commit()
                if outcome.account_id is None:
                    raise HTTPException(409, "login conflict")
                raise HTTPException(409, "login replay requires existing session")
            response.set_cookie(
                SESSION_COOKIE,
                issued.token.reveal(),
                httponly=True,
                secure=settings.runtime.profile is not RuntimeProfile.SYNTHETIC_ACCEPTANCE,
                samesite="lax",
                max_age=settings.session.max_age_seconds,
                path="/",
            )
            session.commit()
            return {"account_id": str(outcome.account_id), "state": outcome.state.value}

    @app.post("/acceptance/logout", tags=["acceptance"])
    def acceptance_logout(
        request: Request, response: Response, key: str = Depends(require_key)
    ) -> dict[str, str]:
        raw = token(request)
        if raw is not None:
            with db() as session:
                composition.identity.revoke_my_session(
                    session,
                    raw,
                    idempotency_key=key,
                    correlation=CorrelationContext(
                        correlation_id=CorrelationId(value=str(uuid4()))
                    ),
                )
                session.commit()
        response.delete_cookie(SESSION_COOKIE, path="/")
        return {"status": "logged_out"}

    api = APIRouter(prefix="/api/v1")

    @api.get("/account")
    def account(request: Request) -> Any:
        _, validation = customer(request)
        with db() as session:
            return composition.identity.safe_account_summary(session, validation.account_id)

    @api.get("/tariffs")
    def tariffs(request: Request) -> Any:
        _, validation = customer(request)
        with db() as session:
            result = composition.entitlements.evaluate_effective(
                session, validation.account_id, at=datetime.now(UTC)
            )
            return _json(result)

    @api.get("/beacons")
    def beacons(request: Request) -> Any:
        raw, _ = customer(request)
        with db() as session:
            return _json(composition.beacon.list(session, actor_reference=raw))

    @api.get("/beacons/{beacon_id}")
    def beacon_detail(request: Request, beacon_id: UUID) -> Any:
        raw, _ = customer(request)
        try:
            with db() as session:
                return _json(
                    {
                        "beacon": composition.beacon.get(
                            session, actor_reference=raw, beacon_id=beacon_id
                        ),
                        "history": composition.beacon.history(
                            session, actor_reference=raw, beacon_id=beacon_id
                        ),
                    }
                )
        except Exception as exc:
            raise _safe_error(exc) from None

    @api.patch("/beacons/{beacon_id}")
    def beacon_patch(
        request: Request, beacon_id: UUID, payload: BeaconPatchDTO, key: str = Depends(require_key)
    ) -> Any:
        raw, _ = customer(request)
        try:
            with db() as session:
                result = composition.beacon.patch(
                    session,
                    actor_reference=raw,
                    beacon_id=beacon_id,
                    patch=payload.patch,
                    expected_row_version=payload.expected_row_version,
                    idempotency_key=key,
                    strict_expected_row_version=True,
                )
                session.commit()
                return _json(result)
        except Exception as exc:
            raise _safe_error(exc) from None

    @api.post("/beacons")
    def beacon_create(
        request: Request, payload: dict[str, Any], key: str = Depends(require_key)
    ) -> Any:
        raw, validation = customer(request)
        try:
            with db() as session:
                result = composition.beacon.create_preparation(
                    session,
                    actor_reference=raw,
                    account_id=validation.account_id,
                    source_url=str(payload.get("source_url", "")),
                    name=str(payload.get("name", "")),
                    idempotency_key=key,
                )
                session.commit()
                return _json(result)
        except Exception as exc:
            raise _safe_error(exc) from None

    @api.post("/beacons/{beacon_id}/{action}")
    def beacon_lifecycle(
        request: Request,
        beacon_id: UUID,
        action: str,
        expected_row_version: int,
        key: str = Depends(require_key),
    ) -> Any:
        raw, _ = customer(request)
        if action not in {
            "pause",
            "resume",
            "archive",
            "restore",
            "user_delete",
            "permanent_delete",
        }:
            raise HTTPException(400, "unsupported action")
        try:
            with db() as session:
                result = getattr(composition.beacon, action)(
                    session,
                    actor_reference=raw,
                    beacon_id=beacon_id,
                    expected_row_version=expected_row_version,
                    idempotency_key=key,
                )
                session.commit()
                return _json(result)
        except Exception as exc:
            raise _safe_error(exc) from None

    @api.get("/scans")
    def scans(request: Request) -> Any:
        raw, validation = customer(request)
        with db() as session:
            views = composition.beacon.list(session, actor_reference=raw)
            return [
                {
                    "beacon_id": str(view.beacon_id),
                    "listing_state": _json(current_listing_state(session, view.beacon_id)),
                    "recent_runs": _json(recent_runs(session, view.beacon_id)),
                }
                for view in views
            ]

    @api.get("/notifications")
    def notifications(request: Request) -> Any:
        raw, validation = customer(request)
        with db() as session:
            return _json(
                read_history(
                    session,
                    account_id=validation.account_id,
                    actor_account_id=validation.account_id,
                    limit=50,
                )
            )

    @api.get("/channels")
    def channels(request: Request) -> Any:
        customer(request)
        from mayak.modules.max_adapter.runtime import max_readiness
        from mayak.modules.telegram_adapter.runtime import telegram_readiness

        return {
            "telegram": _json(telegram_readiness(settings, credential_present=False)),
            "max": _json(max_readiness(settings, credential_present=False)),
        }

    @api.get("/support")
    def support(request: Request) -> Any:
        _, validation = customer(request)
        with db() as session:
            return _json(composition.admin.customer_visible_summary(session, validation.account_id))

    @api.get("/filter-catalog/{version_code}")
    def filter_catalog(request: Request, version_code: str) -> Any:
        customer(request)
        with db() as session:
            return _json(
                composition.filter_catalog_factory(session).load_catalog(
                    version_code, customer_editable=True
                )
            )

    app.include_router(api)
    # Existing RF21/RF20 routers remain the presentation implementations.
    from mayak.modules.admin_and_support.admin_ui import build_admin_router
    from mayak.modules.web_cabinet.web_ui import build_web_router

    app.include_router(
        build_web_router(
            runtime=composition.web,
            session_factory=composition.sessions,
            session_provider=lambda request: token(request),
            prefix="/web",
        )
    )

    def operator(request: Request) -> Any:
        raw = token(request)
        if raw is None:
            raise HTTPException(401, "authentication required")
        with db() as session:
            return composition.rf20.identity.verify_operator(session, raw)

    app.include_router(
        build_admin_router(
            runtime=composition.admin,
            sessions=composition.sessions,
            actor_provider=operator,
        ),
        prefix="",
    )
    return app


__all__ = ["create_app"]

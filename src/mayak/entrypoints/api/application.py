# ruff: noqa: E501
"""FastAPI transport boundary for RF23."""

from __future__ import annotations

import logging
import platform
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any, Iterator
from urllib.parse import urlsplit
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from mayak.contracts.idempotency import IdempotencyKey
from mayak.modules.identity_and_access.contracts import SyntheticAcceptanceLoginRequest
from mayak.platform.correlation import CorrelationContext, CorrelationId
from mayak.platform.correlation_context import correlation_context_scope
from mayak.platform.observability import correlation_id, emit
from mayak.runtime.rf23_composition import (
    CustomerSessionReference,
    RF23Composition,
    build_rf23_composition,
)
from mayak.runtime.settings import MayakRuntimeSettings, RuntimeProfile, load_runtime_settings

SESSION_COOKIE = "mayak_session"
LOGGER = logging.getLogger("mayak.api")


class LoginDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    synthetic_subject: str = Field(min_length=1, max_length=255)


class BeaconPatchDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    patch: dict[str, Any] = Field(default_factory=dict, max_length=32)
    expected_row_version: int = Field(ge=1)


class BeaconCreateDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    source_url: str = Field(min_length=1, max_length=4096)
    name: str = Field(min_length=1, max_length=255)


class ScanScheduleDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    interval_seconds: int = Field(gt=0)
    next_due_at: datetime


def _json(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, tuple):
        return [_json(item) for item in value]
    if isinstance(value, dict):
        return {key: _json(item) for key, item in value.items()}
    return value


def _safe_error(exc: Exception, composition: RF23Composition) -> HTTPException:
    status = composition.safe_error_status(exc)
    if status == 409:
        return HTTPException(409, "conflict")
    if isinstance(exc, PermissionError):
        return HTTPException(403, "forbidden")
    if status == 400:
        return HTTPException(400, "invalid request")
    return HTTPException(500, "internal error")


def create_app(
    *, settings: MayakRuntimeSettings | None = None, composition: RF23Composition | None = None
) -> FastAPI:
    settings = settings or load_runtime_settings()
    composition = composition or build_rf23_composition(settings)
    app = FastAPI(title="Mayak API", version="0.0.0")
    app.state.rf23 = composition

    @app.middleware("http")
    async def cookie_mutation_same_origin(request: Request, call_next: Any) -> Response:
        selected_correlation_id = correlation_id(request.headers.get("X-Correlation-ID"))
        request.state.correlation_id = selected_correlation_id
        started = time.monotonic()
        context = CorrelationContext(correlation_id=CorrelationId(value=selected_correlation_id))
        unsafe = request.method not in {"GET", "HEAD", "OPTIONS"}
        protected = (
            request.url.path.startswith("/api/v1/")
            or request.url.path == "/acceptance/logout"
            or request.url.path.startswith("/web/")
            or request.url.path == "/web"
            or request.url.path.startswith("/admin/")
            or request.url.path == "/admin"
        )
        if unsafe and protected and request.cookies.get(SESSION_COOKIE) is not None:
            origin = request.headers.get("origin")
            expected = f"{request.url.scheme}://{request.headers.get('host', '')}"
            parsed = urlsplit(origin or "")
            valid = (
                bool(origin)
                and parsed.scheme in {"http", "https"}
                and bool(parsed.netloc)
                and not parsed.path
                and not parsed.query
                and not parsed.fragment
                and parsed.username is None
                and parsed.password is None
                and origin == expected
            )
            if not valid:
                response = JSONResponse({"detail": "same-origin required"}, status_code=403)
                response.headers["X-Correlation-ID"] = selected_correlation_id
                emit(LOGGER, operation="http.request", outcome="rejected", reason_code="SAME_ORIGIN_REQUIRED", correlation_id=selected_correlation_id, latency_ms=round((time.monotonic() - started) * 1000, 3))
                return response
        with correlation_context_scope(context):
            try:
                response = await call_next(request)
            except Exception:
                emit(LOGGER, operation="http.request", outcome="failure", reason_code="UNHANDLED_EXCEPTION", correlation_id=selected_correlation_id, latency_ms=round((time.monotonic() - started) * 1000, 3))
                raise
        response.headers["X-Correlation-ID"] = selected_correlation_id
        emit(LOGGER, operation="http.request", outcome="success" if response.status_code < 400 else "rejected", reason_code="HTTP_COMPLETED", correlation_id=selected_correlation_id, latency_ms=round((time.monotonic() - started) * 1000, 3))
        return response

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

    def token(request: Request) -> str | None:
        return request.cookies.get(SESSION_COOKIE)

    def customer(request: Request) -> tuple[CustomerSessionReference, Any]:
        raw = token(request)
        if raw is None:
            raise HTTPException(401, "authentication required")
        with db() as session:
            validation = composition.validate_customer_session(session, raw)
        if validation.account_id is None or validation.metadata is None:
            raise HTTPException(401, "authentication required")
        return composition.customer_session(raw), validation

    def require_key(value: str | None = Header(default=None, alias="Idempotency-Key")) -> str:
        if value is None or not 1 <= len(value.strip()) <= 128:
            raise HTTPException(400, "Idempotency-Key required")
        return value.strip()

    @app.get("/health/live", tags=["health"])
    def live() -> dict[str, str]:
        return {"status": "live"}

    @app.get("/health/diagnostics", tags=["health"])
    def diagnostics() -> dict[str, Any]:
        migration_head = composition.expected_migration_head()
        observed: str | None = None
        readiness_state = "unknown"
        try:
            with db() as session:
                inspection = composition.migration_inspection(session)
            observed = inspection.observed_revision
            readiness_state = "ready" if inspection.structurally_valid and observed == migration_head else "not_ready"
        except Exception:
            readiness_state = "not_ready"
        return {
            "environment_id": settings.build.environment_id,
            "source_sha": settings.build.source_sha,
            "process_kind": settings.runtime.process_kind.value,
            "runtime_profile": settings.runtime.profile.value,
            "readiness_state": readiness_state,
            "migration_revision": observed,
            "migration_head": migration_head,
            "providers": {"telegram": "enabled" if settings.providers.telegram_enabled else "disabled", "max": "enabled" if settings.providers.max_enabled else "disabled"},
            "telemetry": "enabled" if settings.observability.otel_enabled else "disabled",
        }

    @app.get("/health/ready", tags=["health"])
    def ready() -> JSONResponse:
        try:
            with db() as session:
                migration = composition.readiness_inspection(session)
            if (
                not migration.structurally_valid
                or migration.expected_head != migration.observed_revision
            ):
                LOGGER.info("health readiness result=unhealthy category=schema_not_current")
                return JSONResponse({"status": "not_ready", "reason": "schema not current"}, 503)
            LOGGER.info("health readiness result=healthy category=database_current")
            return JSONResponse(
                {
                    "status": "ready",
                    "migration_revision": migration.observed_revision,
                    "migration_head": migration.expected_head,
                    "providers": {"telegram": "disabled", "max": "disabled"},
                }
            )
        except Exception as exc:
            LOGGER.info(
                "health readiness result=unhealthy category=db_connectivity exception_class=%s",
                type(exc).__name__,
            )
            return JSONResponse({"status": "not_ready", "reason": "core runtime unavailable"}, 503)

    @app.get("/version", tags=["health"])
    def version(request: Request) -> dict[str, Any]:
        observed: str | None = None
        migration_head = composition.expected_migration_head()
        try:
            with db() as session:
                migration = composition.migration_inspection(session)
            observed = migration.observed_revision
        except Exception:
            pass
        return {
            "source_sha": settings.build.source_sha,
            "environment_id": settings.build.environment_id,
            "process_kind": settings.runtime.process_kind.value,
            "python": platform.python_version(),
            "migration_head": migration_head,
            "migration_revision": observed,
        }

    @app.post("/acceptance/login", tags=["acceptance"])
    def acceptance_login(
        payload: LoginDTO, response: Response, key: str = Depends(require_key)
    ) -> Any:
        if settings.runtime.profile is not RuntimeProfile.SYNTHETIC_ACCEPTANCE:
            raise HTTPException(404, "not found")
        with db() as session:
            outcome, issued_token = composition.synthetic_login(
                session,
                SyntheticAcceptanceLoginRequest(
                    synthetic_subject=payload.synthetic_subject,
                    idempotency_key=IdempotencyKey(value=key),
                    correlation=CorrelationContext(
                        correlation_id=CorrelationId(value=str(uuid4()))
                    ),
                ),
            )
            if issued_token is None:
                session.commit()
                if outcome.account_id is None:
                    raise HTTPException(409, "login conflict")
                raise HTTPException(409, "login replay requires existing session")
            response.set_cookie(
                SESSION_COOKIE,
                issued_token,
                httponly=True,
                secure=settings.runtime.profile is not RuntimeProfile.SYNTHETIC_ACCEPTANCE,
                samesite="lax",
                max_age=settings.session.max_age_seconds,
                path="/",
            )
            session.commit()
            return {"account_id": str(outcome.account_id), "state": outcome.state.value}

    @app.post("/acceptance/admin/bootstrap", tags=["acceptance"])
    def acceptance_admin_bootstrap(
        request: Request, key: str = Depends(require_key)
    ) -> Any:
        if settings.runtime.profile is not RuntimeProfile.SYNTHETIC_ACCEPTANCE:
            raise HTTPException(404, "not found")
        raw = token(request)
        if raw is None:
            raise HTTPException(401, "authentication required")
        reference = composition.customer_session(raw)
        with db() as session:
            validation = composition.validate_session_reference(session, reference)
            if validation.account_id is None or validation.metadata is None:
                raise HTTPException(401, "authentication required")
            state = composition.bootstrap_admin(session, reference, idempotency_key=key)
            session.commit()
            return {"account_id": str(validation.account_id), "state": state.value}

    @app.post("/acceptance/logout", tags=["acceptance"])
    def acceptance_logout(
        request: Request, response: Response, key: str = Depends(require_key)
    ) -> dict[str, str]:
        raw = token(request)
        if raw is not None:
            reference = composition.customer_session(raw)
            with db() as session:
                composition.revoke_session(
                    session,
                    reference,
                    idempotency_key=key,
                    correlation=CorrelationContext(
                        correlation_id=CorrelationId(value=str(uuid4()))
                    ),
                )
                session.commit()
        response.delete_cookie(SESSION_COOKIE, path="/")
        return {"status": "logged_out"}

    @app.post("/acceptance/entitlement", tags=["acceptance"])
    def acceptance_entitlement(request: Request, key: str = Depends(require_key)) -> Any:
        if settings.runtime.profile is not RuntimeProfile.SYNTHETIC_ACCEPTANCE:
            raise HTTPException(404, "not found")
        raw, validation = customer(request)
        try:
            with db() as session:
                outcome = composition.establish_acceptance_access(
                    session, raw, validation.account_id
                )
                session.commit()
                return _json(outcome)
        except Exception as exc:
            LOGGER.exception("RF24 acceptance entitlement setup failed")
            raise _safe_error(exc, composition) from None

    api = APIRouter(prefix="/api/v1")

    @api.get("/account")
    def account(request: Request) -> Any:
        _, validation = customer(request)
        with db() as session:
            return composition.account_summary(session, validation.account_id)

    @api.get("/tariffs")
    def tariffs(request: Request) -> Any:
        _, validation = customer(request)
        with db() as session:
            result = composition.entitlement_summary(session, validation.account_id)
            return _json(result)

    @api.get("/beacons")
    def beacons(request: Request) -> Any:
        raw, _ = customer(request)
        with db() as session:
            return _json(composition.beacon_list(session, raw))

    @api.get("/beacons/{beacon_id}")
    def beacon_detail(request: Request, beacon_id: UUID) -> Any:
        raw, _ = customer(request)
        try:
            with db() as session:
                return _json(
                    {
                        "beacon": composition.beacon_get(session, raw, beacon_id),
                        "history": composition.beacon_history(session, raw, beacon_id),
                    }
                )
        except Exception as exc:
            raise _safe_error(exc, composition) from None

    @api.patch("/beacons/{beacon_id}")
    def beacon_patch(
        request: Request, beacon_id: UUID, payload: BeaconPatchDTO, key: str = Depends(require_key)
    ) -> Any:
        raw, _ = customer(request)
        try:
            with db() as session:
                result = composition.beacon_patch(
                    session,
                    raw,
                    beacon_id,
                    patch=payload.patch,
                    expected_row_version=payload.expected_row_version,
                    idempotency_key=key,
                )
                session.commit()
                return _json(result)
        except Exception as exc:
            raise _safe_error(exc, composition) from None

    @api.post("/beacons")
    def beacon_create(
        request: Request, payload: BeaconCreateDTO, key: str = Depends(require_key)
    ) -> Any:
        raw, validation = customer(request)
        try:
            with db() as session:
                result = composition.beacon_create(
                    session,
                    raw,
                    validation.account_id,
                    source_url=payload.source_url,
                    name=payload.name,
                    idempotency_key=key,
                )
                session.commit()
                return _json(result)
        except Exception as exc:
            raise _safe_error(exc, composition) from None

    @api.post("/beacons/{beacon_id}/scan-schedule")
    def scan_schedule(
        request: Request, beacon_id: UUID, payload: ScanScheduleDTO
    ) -> Any:
        if settings.runtime.profile is not RuntimeProfile.SYNTHETIC_ACCEPTANCE:
            raise HTTPException(404, "not found")
        customer(request)
        try:
            with db() as session:
                result = composition.scan_schedule_create_or_update(
                    session,
                    beacon_id,
                    interval_seconds=payload.interval_seconds,
                    next_due_at=payload.next_due_at.astimezone(UTC),
                )
                session.commit()
                return _json(result)
        except Exception as exc:
            LOGGER.exception("RF24 scan schedule setup failed")
            raise _safe_error(exc, composition) from None

    @api.post("/beacons/{beacon_id}/{action}")
    def beacon_lifecycle(
        request: Request,
        beacon_id: UUID,
        action: str,
        expected_row_version: int,
        key: str = Depends(require_key),
    ) -> Any:
        raw, _ = customer(request)
        if action == "accept-synthetic-snapshot":
            if settings.runtime.profile is not RuntimeProfile.SYNTHETIC_ACCEPTANCE:
                raise HTTPException(404, "not found")
            try:
                with db() as session:
                    result = composition.beacon_accept_snapshot(
                        session,
                        raw,
                        beacon_id,
                        expected_row_version=expected_row_version,
                        idempotency_key=key,
                    )
                    session.commit()
                    return _json(result)
            except Exception as exc:
                raise _safe_error(exc, composition) from None
        if action not in {
            "activate",
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
                result = composition.beacon_lifecycle(
                    session,
                    raw,
                    beacon_id,
                    action,
                    expected_row_version=expected_row_version,
                    idempotency_key=key,
                )
                session.commit()
                return _json(result)
        except Exception as exc:
            raise _safe_error(exc, composition) from None

    @api.get("/scans")
    def scans(request: Request) -> Any:
        raw, validation = customer(request)
        with db() as session:
            views = composition.scan_views(session, raw)
            return [
                {
                    "beacon_id": view["beacon_id"],
                    "listing_state": _json(view["listing_state"]),
                    "recent_runs": _json(view["recent_runs"]),
                }
                for view in views
            ]

    @api.get("/notifications")
    def notifications(request: Request) -> Any:
        raw, validation = customer(request)
        with db() as session:
            return _json(composition.notification_history(session, validation.account_id))

    @api.get("/channels")
    def channels(request: Request) -> Any:
        customer(request)
        return _json(composition.channel_readiness())

    @api.get("/support")
    def support(request: Request) -> Any:
        _, validation = customer(request)
        with db() as session:
            return _json(composition.admin.customer_visible_summary(session, validation.account_id))

    @api.get("/filter-catalog/{version_code}")
    def filter_catalog(request: Request, version_code: str) -> Any:
        customer(request)
        with db() as session:
            return _json(composition.filter_catalog(session, version_code))

    app.include_router(api)

    def operator(request: Request) -> Any:
        raw = token(request)
        if raw is None:
            raise HTTPException(401, "authentication required")
        with db() as session:
            return composition.operator_validation(session, raw)

    web_router, admin_router = composition.presentation_routers(
        session_provider=lambda request: (
            composition.customer_session(value) if (value := token(request)) is not None else None
        ),
        actor_provider=operator,
    )
    app.include_router(web_router)
    app.include_router(admin_router)
    return app


__all__ = ["create_app"]

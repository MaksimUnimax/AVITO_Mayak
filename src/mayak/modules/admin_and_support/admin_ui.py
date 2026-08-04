"""Small server-rendered operator surface for the RF20 runtime facade."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, sessionmaker

from .runtime import (
    AuthorizationDenied,
    SupportRuntime,
    SupportRuntimeError,
    TargetNotFound,
    VerifiedActor,
)

_TEMPLATES = Jinja2Templates(directory=str(Path(__file__).with_name("templates")))


def build_admin_router(
    *,
    runtime: SupportRuntime,
    sessions: sessionmaker[Session],
    actor_provider: Callable[[Request], VerifiedActor],
) -> APIRouter:
    """Build an isolated router; composition owns mounting and authentication."""

    router = APIRouter(prefix="/admin", tags=["admin-support"])
    router.mount(
        "/static",
        StaticFiles(directory=str(Path(__file__).with_name("static"))),
        name="admin-static",
    )

    def actor(request: Request) -> VerifiedActor:
        try:
            return actor_provider(request)
        except Exception as exc:
            raise HTTPException(status_code=401, detail="unauthenticated") from exc

    @router.get("", response_class=HTMLResponse)
    def landing(request: Request) -> Any:
        try:
            operator = actor(request)
        except HTTPException:
            return _TEMPLATES.TemplateResponse(
                request,
                "admin.html",
                {"title": "Admin", "error": "unauthenticated", "cases": (), "summary": None},
            )
        with sessions() as session:
            cases = runtime.list_cases(session, limit=20)
        return _TEMPLATES.TemplateResponse(
            request,
            "admin.html",
            {
                "title": "Admin & Support",
                "operator": operator,
                "cases": cases,
                "summary": None,
                "error": None,
            },
        )

    @router.get("/account/{account_id}", response_class=HTMLResponse)
    def account(request: Request, account_id: UUID) -> Any:
        try:
            operator = actor(request)
            with sessions() as session:
                summary = runtime.safe_account_summary(
                    session, actor=operator, account_id=account_id
                )
                cases = runtime.list_cases(session, account_id=account_id)
            return _TEMPLATES.TemplateResponse(
                request,
                "admin.html",
                {
                    "title": "Account summary",
                    "operator": operator,
                    "summary": summary,
                    "cases": cases,
                    "error": None,
                },
            )
        except AuthorizationDenied:
            raise HTTPException(status_code=403, detail="forbidden") from None
        except SupportRuntimeError as exc:
            return _TEMPLATES.TemplateResponse(
                request,
                "admin.html",
                {"title": "Account summary", "summary": None, "cases": (), "error": str(exc)},
            )

    @router.post("/cases", response_class=HTMLResponse)
    async def open_case(request: Request) -> Any:
        try:
            operator = actor(request)
            form = parse_qs((await request.body()).decode("utf-8"), strict_parsing=True)
            account_id = UUID(form["account_id"][0])
            subject, reason, idempotency_key = (
                form[name][0] for name in ("subject", "reason", "idempotency_key")
            )
            with sessions.begin() as session:
                result = runtime.open_case(
                    session,
                    actor=operator,
                    account_id=account_id,
                    subject=subject,
                    reason=reason,
                    idempotency_key=idempotency_key,
                )
            return _TEMPLATES.TemplateResponse(
                request,
                "admin.html",
                {
                    "title": "Case opened",
                    "operator": operator,
                    "cases": (),
                    "summary": {"result": result},
                    "error": None,
                },
            )
        except AuthorizationDenied:
            raise HTTPException(status_code=403, detail="forbidden") from None
        except SupportRuntimeError as exc:
            return _TEMPLATES.TemplateResponse(
                request,
                "admin.html",
                {"title": "Case error", "cases": (), "summary": None, "error": str(exc)},
            )

    @router.post("/cases/{case_id}/notes", response_class=HTMLResponse)
    async def note(request: Request, case_id: UUID) -> Any:
        try:
            operator = actor(request)
            form = parse_qs((await request.body()).decode("utf-8"), strict_parsing=True)
            body, reason, idempotency_key = (
                form[name][0] for name in ("body", "reason", "idempotency_key")
            )
            with sessions.begin() as session:
                case = runtime.get_case(session, case_id)
                result = runtime.add_internal_note(
                    session,
                    actor=operator,
                    case_id=case_id,
                    body=body,
                    reason=reason,
                    idempotency_key=idempotency_key,
                )
            return _TEMPLATES.TemplateResponse(
                request,
                "admin.html",
                {
                    "title": "Internal note recorded",
                    "operator": operator,
                    "cases": (case,),
                    "summary": {"result": result},
                    "error": None,
                },
            )
        except TargetNotFound:
            raise HTTPException(status_code=404, detail="not found") from None
        except AuthorizationDenied:
            raise HTTPException(status_code=403, detail="forbidden") from None
        except SupportRuntimeError as exc:
            return _TEMPLATES.TemplateResponse(
                request,
                "admin.html",
                {"title": "Case error", "cases": (), "summary": None, "error": str(exc)},
            )

    return router


__all__ = ["build_admin_router"]

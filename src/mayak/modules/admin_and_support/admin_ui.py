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

from .contracts import SupportCaseState
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
            cases = runtime.list_cases(session, actor=operator, limit=20)
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
                cases = runtime.list_cases(session, actor=operator, account_id=account_id)
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
        except (KeyError, ValueError, UnicodeDecodeError):
            raise HTTPException(status_code=400, detail="malformed form") from None
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
        except (KeyError, ValueError, UnicodeDecodeError):
            raise HTTPException(status_code=400, detail="malformed form") from None
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
                case = runtime.get_case_for_operator(session, actor=operator, case_id=case_id)
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
        except (KeyError, ValueError, UnicodeDecodeError):
            raise HTTPException(status_code=400, detail="malformed form") from None
        except SupportRuntimeError as exc:
            return _TEMPLATES.TemplateResponse(
                request,
                "admin.html",
                {"title": "Case error", "cases": (), "summary": None, "error": str(exc)},
            )

    @router.get("/cases/{case_id}", response_class=HTMLResponse)
    def case_detail(request: Request, case_id: UUID) -> Any:
        try:
            operator = actor(request)
            with sessions() as session:
                case = runtime.get_case_for_operator(session, actor=operator, case_id=case_id)
                notes = runtime.list_internal_notes(session, actor=operator, case_id=case_id)
                events = runtime.list_events(session, actor=operator, case_id=case_id)
            return _TEMPLATES.TemplateResponse(request, "admin.html", {
                "title": "Support case", "operator": operator, "cases": (case,),
                "case": case, "notes": notes, "events": events, "summary": None, "error": None,
            })
        except AuthorizationDenied:
            raise HTTPException(status_code=403, detail="forbidden") from None
        except TargetNotFound:
            raise HTTPException(status_code=404, detail="not found") from None

    @router.post("/cases/{case_id}/transition", response_class=HTMLResponse)
    async def transition(request: Request, case_id: UUID) -> Any:
        try:
            operator = actor(request)
            form = parse_qs((await request.body()).decode("utf-8"), strict_parsing=True)
            state = form["state"][0]
            evidence = form.get("evidence", [None])[0]
            with sessions.begin() as session:
                case = runtime.get_case_for_operator(session, actor=operator, case_id=case_id)
                result = runtime.transition_case(
                    session, actor=operator, case_id=case_id,
                    target_state=SupportCaseState(state),
                    expected_row_version=int(form["row_version"][0]), reason=form["reason"][0],
                    idempotency_key=form["idempotency_key"][0], evidence_reference=evidence,
                )
            return _TEMPLATES.TemplateResponse(request, "admin.html", {
                "title": "Case transition", "operator": operator, "cases": (case,),
                "summary": {"result": result}, "error": None,
            })
        except (KeyError, ValueError, UnicodeDecodeError):
            raise HTTPException(status_code=400, detail="malformed form") from None
        except AuthorizationDenied:
            raise HTTPException(status_code=403, detail="forbidden") from None
        except TargetNotFound:
            raise HTTPException(status_code=404, detail="not found") from None
        except SupportRuntimeError as exc:
            return _TEMPLATES.TemplateResponse(request, "admin.html", {
                "title": "Case error", "cases": (), "summary": None, "error": str(exc),
            })

    @router.post("/cases/{case_id}/actions/{family}", response_class=HTMLResponse)
    async def delegated_action(request: Request, case_id: UUID, family: str) -> Any:
        try:
            operator = actor(request)
            form = parse_qs((await request.body()).decode("utf-8"), strict_parsing=True)
            target = UUID(form["target"][0])
            if len(form.get("action", ())) != 1:
                raise ValueError("exactly one action is required")
            action = form["action"][0]
            reason = form["reason"][0]
            idempotency_key = form["idempotency_key"][0]
            if family == "role":
                handler = runtime.execute_role_action
            elif family == "tariff":
                handler = runtime.execute_tariff_action
            elif family == "access":
                handler = runtime.execute_access_action
            elif family == "beacon":
                handler = runtime.execute_beacon_action
            elif family == "anchor":
                handler = runtime.execute_anchor_action
            else:
                raise HTTPException(status_code=400, detail="unsupported action")
            with sessions.begin() as session:
                result = handler(
                    session,
                    actor=operator,
                    case_id=case_id,
                    target=target,
                    action=action,
                    reason=reason,
                    idempotency_key=idempotency_key,
                )
            return _TEMPLATES.TemplateResponse(request, "admin.html", {
                "title": "Owning-module action", "operator": operator, "cases": (),
                "summary": {"result": result}, "error": None,
            })
        except HTTPException:
            raise
        except (KeyError, ValueError, UnicodeDecodeError):
            raise HTTPException(status_code=400, detail="malformed form") from None
        except AuthorizationDenied:
            raise HTTPException(status_code=403, detail="forbidden") from None
        except TargetNotFound:
            raise HTTPException(status_code=404, detail="not found") from None
        except SupportRuntimeError as exc:
            return _TEMPLATES.TemplateResponse(request, "admin.html", {
                "title": "Action error", "cases": (), "summary": None, "error": str(exc),
            })

    @router.get("/cases/{case_id}/notification-diagnostics", response_class=HTMLResponse)
    def notification_diagnostics(request: Request, case_id: UUID) -> Any:
        try:
            operator = actor(request)
            with sessions() as session:
                case = runtime.get_case_for_operator(session, actor=operator, case_id=case_id)
                diagnostics = runtime.notification_diagnostics(
                    session, actor=operator, account_id=case.account_id
                )
            return _TEMPLATES.TemplateResponse(request, "admin.html", {
                "title": "Notification diagnostics", "operator": operator, "cases": (case,),
                "summary": diagnostics, "error": None,
            })
        except AuthorizationDenied:
            raise HTTPException(status_code=403, detail="forbidden") from None
        except TargetNotFound:
            raise HTTPException(status_code=404, detail="not found") from None

    return router


__all__ = ["build_admin_router"]

"""Isolated server-rendered customer Web Cabinet router."""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs
from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from .runtime import WebCabinetRuntime, WebDashboard, WebRuntimeError

_ROOT = Path(__file__).parent
_TEMPLATES = Jinja2Templates(directory=str(_ROOT / "templates"))


def build_web_router(*, runtime: WebCabinetRuntime, session_factory: Callable[[], Any],
                     session_provider: Callable[[Request], Any]) -> APIRouter:
    router = APIRouter(prefix="/cabinet", tags=["web-cabinet"])

    @router.get("/static/cabinet.css", include_in_schema=False)
    def cabinet_css() -> FileResponse:
        return FileResponse(_ROOT / "static" / "cabinet.css", media_type="text/css")

    def render(request: Request, *, dashboard: Any = None, error: str | None = None,
               status_code: int = 200) -> HTMLResponse:
        response = _TEMPLATES.TemplateResponse(request, "dashboard.html", {
            "title": "Web Cabinet", "dashboard": dashboard, "error": error,
        })
        response.status_code = status_code
        return response

    def get_dashboard(request: Request) -> Any:
        reference = session_provider(request)
        if reference is None:
            return None
        with session_factory() as session:
            return runtime.dashboard(session, reference)

    @router.get("", response_class=HTMLResponse)
    @router.get("/", response_class=HTMLResponse, include_in_schema=False)
    def dashboard(request: Request) -> HTMLResponse:
        try:
            value = get_dashboard(request)
        except Exception:
            return render(request, error="Временная ошибка. Попробуйте позже.", status_code=503)
        return render(request, dashboard=value,
                      error=None if value is not None else "Требуется проверенная сессия.",
                      status_code=200 if value is not None else 401)

    @router.get("/beacons", response_class=HTMLResponse)
    def beacons(request: Request) -> HTMLResponse:
        try:
            reference = session_provider(request)
            if reference is None:
                return render(request, error="Требуется проверенная сессия.", status_code=401)
            with session_factory() as session:
                customer = runtime.identity.resolve_session(session, reference)
                if customer is None:
                    return render(request, error="Требуется проверенная сессия.", status_code=401)
                beacon_section = runtime.beacon_views(session, customer)
            if beacon_section is None:
                return render(request, error="Требуется проверенная сессия.", status_code=401)
            return render(request, dashboard=WebDashboard(customer, (beacon_section,)))
        except Exception:
            return render(request, error="Состояние Beacon временно недоступно.", status_code=503)

    @router.get("/beacons/{beacon_id}", response_class=HTMLResponse)
    def beacon_detail(request: Request, beacon_id: UUID) -> HTMLResponse:
        try:
            reference = session_provider(request)
            if reference is None:
                return render(request, error="Требуется проверенная сессия.", status_code=401)
            with session_factory() as session:
                customer = runtime.identity.resolve_session(session, reference)
                if customer is None:
                    return render(request, error="Требуется проверенная сессия.", status_code=401)
                detail = runtime.beacon_detail(session, customer, beacon_id)
            return render(request, dashboard=WebDashboard(customer, (detail,)))
        except Exception:
            return render(request, error="Beacon недоступен.", status_code=404)

    @router.post("/beacons/{beacon_id}/command", response_class=HTMLResponse)
    async def beacon_command(request: Request, beacon_id: UUID) -> HTMLResponse:
        try:
            body = (await request.body()).decode("utf-8")
            form = parse_qs(body, strict_parsing=True, keep_blank_values=False)
            required = ("action", "expected_row_version", "idempotency_key")
            if any(len(form.get(name, ())) != 1 for name in required):
                raise ValueError("malformed form")
            allowed = {
                "action", "expected_row_version", "idempotency_key",
                "normalized_filter_values",
            }
            if set(form) - allowed or any(len(values) != 1 for values in form.values()):
                raise ValueError("malformed form")
            reference = session_provider(request)
            if reference is None:
                return render(request, error="Требуется проверенная сессия.", status_code=401)
            with session_factory() as session:
                customer = runtime.identity.resolve_session(session, reference)
                if customer is None:
                    return render(request, error="Требуется проверенная сессия.", status_code=401)
                with session.begin():
                    runtime.execute_beacon_command(
                        session, customer, beacon_id=beacon_id, action=form["action"][0],
                        expected_row_version=int(form["expected_row_version"][0]),
                        idempotency_key=form["idempotency_key"][0],
                        patch={"normalized_filter_values": form["normalized_filter_values"][0]}
                        if "normalized_filter_values" in form else None,
                    )
            with session_factory() as committed_session:
                dashboard = runtime.dashboard(committed_session, reference)
            return render(request, dashboard=dashboard, error="Команда обработана.")
        except (KeyError, ValueError, UnicodeDecodeError):
            return render(request, error="Некорректная форма.", status_code=400)
        except (PermissionError, WebRuntimeError):
            return render(request, error="Команда недоступна.", status_code=403)
        except Exception:
            return render(request, error="Не удалось обработать команду.", status_code=409)

    return router


__all__ = ["build_web_router"]

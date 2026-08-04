"""Executable RF21 acceptance observers and controlled negative canaries."""
from __future__ import annotations

import ast
import hashlib
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Any, Callable, ClassVar

from mayak.modules.max_adapter.transport import HttpxMaxTransport
from mayak.modules.telegram_adapter.transport import HttpxTelegramTransport


class ProviderTransportGuardViolation(RuntimeError):
    """A disabled-provider acceptance scenario reached a live boundary."""


PROVIDER_GUARD_VERSION = "rf21-production-transport-guard/v1"
PROVIDER_GUARDED_BOUNDARIES = (
    "mayak.modules.telegram_adapter.transport.HttpxTelegramTransport._request",
    "mayak.modules.max_adapter.transport.HttpxMaxTransport._request",
    "mayak.modules.max_adapter.transport.HttpxMaxTransport.get_updates",
)


@dataclass(frozen=True, slots=True)
class MeasuredObservation:
    name: str
    measured: int | bool
    method: str
    subject: str
    evidence: str
    source_sha256: str | None = None

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"name": self.name, "measured": self.measured,
                                  "method": self.method, "subject": self.subject,
                                  "evidence": self.evidence}
        if self.source_sha256:
            result["source_sha256"] = self.source_sha256
        return result


class ProviderTransportObserver:
    """Compatibility facade for the production-path guard."""

    def __init__(self, boundary: str | None = None) -> None:
        self.boundary = boundary or "|".join(PROVIDER_GUARDED_BOUNDARIES)
        self.calls = 0
        self.counts = {name: 0 for name in PROVIDER_GUARDED_BOUNDARIES}

    def call(self, operation: Callable[[], Any]) -> Any:
        self.calls += 1
        return operation()

    def observation(self) -> ProviderObservation:
        return ProviderObservation(
            measured=self.calls,
            counts=dict(self.counts),
        )


@dataclass(frozen=True, slots=True)
class ProviderObservation:
    measured: int
    counts: dict[str, int]

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": "provider_transport",
            "observer_version": PROVIDER_GUARD_VERSION,
            "method": "production-transport-guard",
            "guarded_boundaries": list(PROVIDER_GUARDED_BOUNDARIES),
            "telegram_request_calls": self.counts[PROVIDER_GUARDED_BOUNDARIES[0]],
            "max_request_calls": self.counts[PROVIDER_GUARDED_BOUNDARIES[1]],
            "max_get_updates_calls": self.counts[PROVIDER_GUARDED_BOUNDARIES[2]],
            "total_calls": self.measured,
            "measured": self.measured,
            "result": "PASS" if self.measured == 0 else "FAIL",
            "subject": "provider-disabled-customer-scenario",
        }


class ProductionProviderTransportGuard(AbstractContextManager[ProviderTransportObserver]):
    """Temporarily intercept the exact production transport boundaries."""

    _targets: ClassVar[tuple[tuple[type[Any], str, str], ...]] = (
        (HttpxTelegramTransport, "_request", PROVIDER_GUARDED_BOUNDARIES[0]),
        (HttpxMaxTransport, "_request", PROVIDER_GUARDED_BOUNDARIES[1]),
        (HttpxMaxTransport, "get_updates", PROVIDER_GUARDED_BOUNDARIES[2]),
    )

    def __init__(self) -> None:
        self.observer = ProviderTransportObserver()
        self._originals: list[tuple[type[Any], str, Any]] = []

    def __enter__(self) -> ProviderTransportObserver:
        try:
            for owner, name, boundary in self._targets:
                original = getattr(owner, name)
                self._originals.append((owner, name, original))

                def blocked(*args: Any, _boundary: str = boundary, **kwargs: Any) -> Any:
                    self.observer.calls += 1
                    self.observer.counts[_boundary] += 1
                    raise ProviderTransportGuardViolation(
                        f"guarded provider boundary invoked: {_boundary.rsplit('.', 1)[-1]}"
                    )

                setattr(owner, name, blocked)
        except Exception:
            self.__exit__(None, None, None)
            raise
        return self.observer

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        for owner, name, original in reversed(self._originals):
            setattr(owner, name, original)
        self._originals.clear()
        return None


def production_provider_transport_guard() -> ProductionProviderTransportGuard:
    return ProductionProviderTransportGuard()


def provider_guard_negative_canary() -> dict[str, Any]:
    """Exercise Telegram and both MAX boundaries without network I/O."""
    caught: list[str] = []
    with production_provider_transport_guard() as observed:
        telegram = HttpxTelegramTransport("synthetic-telegram-credential")
        maximum = HttpxMaxTransport("synthetic-max-credential")
        for name, operation in (
            ("telegram", lambda: telegram._request("getMe", {})),
            ("max_request", lambda: maximum._request("GET", "/me")),
            ("max_get_updates", lambda: maximum.get_updates(marker=None, limit=1, timeout=0)),
        ):
            try:
                operation()
            except ProviderTransportGuardViolation:
                caught.append(name)
    return {"caught": caught, "counts": observed.observation().as_dict()["total_calls"]}


def observe_support_projection(projection: Any, *, public_marker: str,
                               private_marker: str) -> dict[str, Any]:
    rendered = repr(projection)
    return {"ready": projection is not None, "public_marker_visible": public_marker in rendered,
            "private_marker_visible": private_marker in rendered}


def check_notification_isolation(projection: Any, *, own_account: str,
                                 foreign_account: str) -> MeasuredObservation:
    rendered = repr(projection)
    return MeasuredObservation("notification_tenant_isolation",
                               own_account in rendered and foreign_account not in rendered,
                               "adapter-projection-membership-check", own_account,
                               "notification-web-adapter-projection")


def scan_source_semantics(source: str, *, subject: str) -> dict[str, Any]:
    tree = ast.parse(source)
    imports = [ast.unparse(node) for node in ast.walk(tree)
               if isinstance(node, (ast.Import, ast.ImportFrom))]
    calls = [ast.unparse(node) for node in ast.walk(tree) if isinstance(node, ast.Call)]
    attributes = [ast.unparse(node) for node in ast.walk(tree) if isinstance(node, ast.Attribute)]
    return {"token_access": not any(
                ("credential" in value.lower() or "token" in value.lower())
                and "credential_present" not in value.lower() for value in calls
            ),
            "raw_provider_payload": not any(
                "response.text" in value or "provider_response.content" in value
                for value in attributes
            ),
            "direct_web_dml": not any("sqlalchemy" in value.lower() for value in imports),
            "external_assets": not any(
                "http://" in value or "https://" in value for value in calls
            ),
            "source_sha256": hashlib.sha256(source.encode()).hexdigest(), "subject": subject}


__all__ = ["MeasuredObservation", "ProviderObservation", "ProviderTransportObserver",
           "ProviderTransportGuardViolation",
           "ProductionProviderTransportGuard", "PROVIDER_GUARD_VERSION",
           "PROVIDER_GUARDED_BOUNDARIES", "production_provider_transport_guard",
           "provider_guard_negative_canary", "observe_support_projection",
           "check_notification_isolation", "scan_source_semantics"]

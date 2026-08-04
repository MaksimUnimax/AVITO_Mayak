"""Executable RF21 acceptance observers and controlled negative canaries."""
from __future__ import annotations

import ast
import hashlib
from dataclasses import dataclass
from typing import Any, Callable


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
    """Counts calls at an injected Telegram/MAX transport boundary only."""

    def __init__(self, boundary: str) -> None:
        self.boundary, self.calls = boundary, 0

    def call(self, operation: Callable[[], Any]) -> Any:
        self.calls += 1
        return operation()

    def observation(self) -> MeasuredObservation:
        return MeasuredObservation("provider_transport", self.calls,
                                   "provider-transport-boundary-counter", self.boundary,
                                   "provider-disabled-customer-scenario")


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


__all__ = ["MeasuredObservation", "ProviderTransportObserver", "observe_support_projection",
           "check_notification_isolation", "scan_source_semantics"]

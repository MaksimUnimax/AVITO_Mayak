"""Customer Web Cabinet runtime facade.

The facade owns presentation composition only.  All domain reads and writes
are supplied by typed ports, so this package has no database or foreign-module
implementation dependency.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol
from uuid import UUID

from .read_models import WebReadFreshness


class WebRuntimeState(StrEnum):
    READY = "READY"
    UNAUTHENTICATED = "UNAUTHENTICATED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"
    CONFLICT = "CONFLICT"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class VerifiedWebCustomer:
    account_id: UUID
    session_id: UUID
    authority_reference: str
    authority_context: Any = field(default=None, repr=False, compare=False)


@dataclass(frozen=True, slots=True)
class WebSection:
    key: str
    state: WebRuntimeState
    owner: str
    value: Any = None
    freshness: WebReadFreshness = WebReadFreshness.UNKNOWN
    provenance: tuple[str, ...] = ()
    message: str | None = None


@dataclass(frozen=True, slots=True)
class WebDashboard:
    customer: VerifiedWebCustomer
    sections: tuple[WebSection, ...]

    def section(self, key: str) -> WebSection:
        return next(section for section in self.sections if section.key == key)


class WebCustomerPort(Protocol):
    def resolve_session(
        self, session: Any, session_reference: Any
    ) -> VerifiedWebCustomer | None: ...
    def account_summary(self, session: Any, customer: VerifiedWebCustomer) -> Any: ...


class WebProjectionPort(Protocol):
    owner: str

    def read(self, session: Any, customer: VerifiedWebCustomer) -> Any: ...


class WebBeaconPort(WebProjectionPort, Protocol):
    def command(self, session: Any, customer: VerifiedWebCustomer, *, beacon_id: UUID,
                action: str, expected_row_version: int, idempotency_key: str,
                patch: dict[str, Any] | None = None) -> Any: ...


class WebRuntimeError(RuntimeError):
    """Safe boundary error; the router never exposes its text."""


@dataclass(slots=True)
class WebCabinetRuntime:
    identity: WebCustomerPort
    account: WebCustomerPort
    projections: tuple[WebProjectionPort, ...] = ()
    beacon: WebBeaconPort | None = None

    def dashboard(self, session: Any, session_reference: Any) -> WebDashboard | None:
        customer = self.identity.resolve_session(session, session_reference)
        if customer is None:
            return None
        sections: list[WebSection] = []
        try:
            value = self.account.account_summary(session, customer)
            sections.append(WebSection("account", WebRuntimeState.READY, "identity_and_access",
                                       value, WebReadFreshness.FRESH, ("identity_and_access",)))
        except Exception:
            sections.append(WebSection("account", WebRuntimeState.UNKNOWN,
                                       "identity_and_access", message="temporarily unavailable"))
        if self.beacon is not None:
            sections.append(self._read("beacons", self.beacon, session, customer))
        for port in self.projections:
            key = getattr(port, "key", getattr(port, "owner", "projection"))
            sections.append(self._read(key, port, session, customer))
        return WebDashboard(customer=customer, sections=tuple(sections))

    def beacon_views(self, session: Any, customer: VerifiedWebCustomer) -> WebSection:
        if self.beacon is None:
            return WebSection("beacons", WebRuntimeState.UNKNOWN, "beacon_management",
                              message="unavailable")
        return self._read("beacons", self.beacon, session, customer)

    def beacon_detail(
        self, session: Any, customer: VerifiedWebCustomer, beacon_id: UUID
    ) -> WebSection:
        if self.beacon is None or not hasattr(self.beacon, "detail"):
            return WebSection("beacon-detail", WebRuntimeState.UNKNOWN, "beacon_management",
                              message="unavailable")
        try:
            value = self.beacon.detail(session, customer, beacon_id)
            return WebSection("beacon-detail", WebRuntimeState.READY, self.beacon.owner, value,
                              WebReadFreshness.FRESH, (self.beacon.owner,))
        except PermissionError:
            return WebSection("beacon-detail", WebRuntimeState.FORBIDDEN, self.beacon.owner,
                              message="unavailable")
        except Exception:
            return WebSection("beacon-detail", WebRuntimeState.UNKNOWN, self.beacon.owner,
                              message="temporarily unavailable")

    def execute_beacon_command(
        self, session: Any, customer: VerifiedWebCustomer, **kwargs: Any
    ) -> Any:
        if self.beacon is None:
            raise WebRuntimeError("beacon command unavailable")
        return self.beacon.command(session, customer, **kwargs)

    @staticmethod
    def _read(key: str, port: WebProjectionPort, session: Any,
              customer: VerifiedWebCustomer) -> WebSection:
        try:
            result = port.read(session, customer)
            if isinstance(result, WebSection):
                return result
            return WebSection(key, WebRuntimeState.READY, port.owner, result,
                              WebReadFreshness.FRESH, (port.owner,))
        except PermissionError:
            return WebSection(key, WebRuntimeState.FORBIDDEN, port.owner,
                              freshness=WebReadFreshness.UNKNOWN, message="unavailable")
        except (KeyError, LookupError):
            return WebSection(key, WebRuntimeState.NOT_FOUND, port.owner,
                              freshness=WebReadFreshness.UNKNOWN, message="unavailable")
        except Exception:
            return WebSection(key, WebRuntimeState.UNKNOWN, port.owner,
                              freshness=WebReadFreshness.UNKNOWN, message="temporarily unavailable")


__all__ = ["VerifiedWebCustomer", "WebCabinetRuntime", "WebDashboard", "WebRuntimeState",
           "WebSection", "WebRuntimeError"]

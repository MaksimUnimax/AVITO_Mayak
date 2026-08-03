"""RF16 PostgreSQL-backed Egress Routing runtime boundary.

This adapter is the only runtime writer for the four Module-07 tables.  Agent
messages remain transport-neutral and are validated before they reach this
boundary; the agent never receives a database handle.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol, Sequence
from uuid import UUID, uuid4

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from mayak.persistence.metadata import metadata

AGENTS = metadata.tables["mayak.egress_agents"]
ROUTES = metadata.tables["mayak.egress_routes"]
HEARTBEATS = metadata.tables["mayak.egress_agent_heartbeats"]
LEASES = metadata.tables["mayak.egress_route_leases"]
_LEASE_NAMESPACE = UUID("8d143af1-4ad4-4c4e-9a25-6ec8a6dc5f16")


class RuntimeReason(StrEnum):
    NO_ELIGIBLE_ROUTE = "NO_ELIGIBLE_ROUTE"
    ROUTE_NOT_READY = "ROUTE_NOT_READY"
    AGENT_NOT_READY = "AGENT_NOT_READY"
    ROUTE_RESTRICTED = "ROUTE_RESTRICTED"
    ROUTE_UNAVAILABLE = "ROUTE_UNAVAILABLE"
    MULTIPLE_ROUTES_UNAPPROVED = "MULTIPLE_ROUTES_UNAPPROVED"
    LEASE_EXPIRED = "LEASE_EXPIRED"
    LEASE_REVOKED = "LEASE_REVOKED"
    LEASE_RECONCILIATION_REQUIRED = "LEASE_RECONCILIATION_REQUIRED"
    IDENTITY_MISMATCH = "IDENTITY_MISMATCH"
    SELECTION_POLICY_REQUIRED = "SELECTION_POLICY_REQUIRED"
    LEASE_CONFLICT = "LEASE_CONFLICT"


class LeaseState(StrEnum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    AMBIGUOUS = "AMBIGUOUS"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"


@dataclass(frozen=True, slots=True)
class RuntimeResult:
    ok: bool
    reason: str
    reference_id: UUID | None = None


class TrustedSelectionPolicyPort(Protocol):
    """Server-owned adapter to the accepted Module-07 selection boundary."""

    def select(
        self,
        *,
        route_facts: Sequence[tuple[UUID, UUID, str, str]],
        purpose: str,
        capability_scope: tuple[str, ...],
    ) -> RuntimeResult: ...


@dataclass(frozen=True, slots=True)
class AgentProjection:
    id: UUID
    agent_code: str
    state: str
    row_version: int


@dataclass(frozen=True, slots=True)
class RouteProjection:
    id: UUID
    agent_id: UUID
    route_code: str
    state: str
    readiness: str


@dataclass(frozen=True, slots=True)
class LeaseProjection:
    id: UUID
    route_id: UUID
    work_item_id: UUID
    lease_token: UUID
    state: str
    lease_expires_at: datetime


def _safe_text(value: str, field: str, limit: int) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f"{field} is blank or exceeds {limit} characters")
    return value.strip()


def _opaque_ref(value: str) -> str:
    value = _safe_text(value, "endpoint_ref", 255)
    lowered = value.lower()
    if "://" in lowered or any(part in lowered for part in ("proxy", "vpn", "tunnel", "cookie")):
        raise ValueError("endpoint_ref must be an opaque project-owned reference")
    return value


def _safe_metadata(value: dict[str, object]) -> dict[str, object]:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    lowered = encoded.lower()
    if len(encoded.encode()) > 8192:
        raise ValueError("safe metadata exceeds 8192 bytes")
    if any(
        word in lowered
        for word in ("secret", "token", "cookie", "authorization", "payload", "body")
    ):
        raise ValueError("unsafe diagnostic metadata")
    return value


class EgressRuntime:
    """Explicit server-side Module-07 authority; callers own the session lifecycle."""

    def register_agent(
        self,
        session: Session,
        *,
        agent_code: str,
        state: str = "REGISTERED",
        credential_fingerprint: str | None = None,
        agent_id: UUID | None = None,
    ) -> AgentProjection:
        code = _safe_text(agent_code, "agent_code", 128)
        if state not in {
            "REGISTERED",
            "ONLINE_UNREADY",
            "READY",
            "SUSPENDED",
            "QUARANTINED",
            "RETIRED",
        }:
            raise ValueError("unsupported agent state")
        if credential_fingerprint is not None and (
            len(credential_fingerprint) != 64
            or any(c not in "0123456789abcdef" for c in credential_fingerprint)
        ):
            raise ValueError("credential_fingerprint must be a lowercase SHA-256 reference")
        existing = (
            session.execute(select(AGENTS).where(AGENTS.c.agent_code == code))
            .mappings()
            .one_or_none()
        )
        if existing is not None:
            if (
                credential_fingerprint is not None
                and existing["credential_fingerprint"] != credential_fingerprint
            ):
                raise ValueError("agent identity mismatch")
            return AgentProjection(
                existing["id"], existing["agent_code"], existing["state"], existing["row_version"]
            )
        aid = agent_id or uuid4()
        now = func.now()
        session.execute(
            insert(AGENTS).values(
                id=aid,
                agent_code=code,
                credential_fingerprint=credential_fingerprint,
                state=state,
                created_at=now,
                updated_at=now,
                row_version=1,
            )
        )
        return AgentProjection(aid, code, state, 1)

    def register_route(
        self,
        session: Session,
        *,
        agent_id: UUID,
        route_code: str,
        endpoint_ref: str,
        state: str = "REGISTERED",
        route_id: UUID | None = None,
    ) -> RouteProjection:
        _safe_text(route_code, "route_code", 128)
        endpoint = _opaque_ref(endpoint_ref)
        if (
            session.execute(select(AGENTS.c.id).where(AGENTS.c.id == agent_id)).scalar_one_or_none()
            is None
        ):
            raise ValueError("route agent is not registered")
        if state not in {
            "REGISTERED",
            "READY",
            "DEGRADED",
            "RESTRICTED",
            "QUARANTINED",
            "SUSPENDED",
            "RETIRED",
        }:
            raise ValueError("unsupported route state")
        existing = (
            session.execute(
                select(ROUTES).where(
                    ROUTES.c.agent_id == agent_id, ROUTES.c.route_code == route_code
                )
            )
            .mappings()
            .one_or_none()
        )
        if existing is not None:
            if existing["endpoint_ref"] != endpoint:
                raise ValueError("route identity mismatch")
            return RouteProjection(
                existing["id"],
                existing["agent_id"],
                existing["route_code"],
                existing["state"],
                self._readiness(session, existing["id"], existing["state"]),
            )
        rid = route_id or uuid4()
        now = func.now()
        session.execute(
            insert(ROUTES).values(
                id=rid,
                agent_id=agent_id,
                route_code=route_code,
                endpoint_ref=endpoint,
                state=state,
                created_at=now,
                updated_at=now,
                row_version=1,
            )
        )
        return RouteProjection(
            rid, agent_id, route_code, state, self._readiness(session, rid, state)
        )

    def record_heartbeat(
        self,
        session: Session,
        *,
        agent_id: UUID,
        state: str = "ONLINE",
        safe_metadata: dict[str, object] | None = None,
    ) -> UUID:
        if (
            session.execute(select(AGENTS.c.id).where(AGENTS.c.id == agent_id)).scalar_one_or_none()
            is None
        ):
            raise ValueError("heartbeat agent is not registered")
        _safe_text(state, "heartbeat state", 64)
        metadata_value = _safe_metadata(safe_metadata or {})
        heartbeat_id = uuid4()
        session.execute(
            insert(HEARTBEATS).values(
                id=heartbeat_id,
                agent_id=agent_id,
                observed_at=func.now(),
                state=state,
                safe_metadata=metadata_value,
            )
        )
        return heartbeat_id

    def _readiness(self, session: Session, route_id: UUID, route_state: str) -> str:
        if route_state in {"SUSPENDED", "QUARANTINED", "RESTRICTED", "RETIRED"}:
            return route_state
        if route_state != "READY":
            return "ONLINE_UNREADY"
        return "READY"

    def select_route(
        self,
        session: Session,
        *,
        purpose: str,
        capability_scope: tuple[str, ...],
        selection_policy: TrustedSelectionPolicyPort | None = None,
    ) -> RuntimeResult:
        if selection_policy is None:
            return RuntimeResult(False, RuntimeReason.SELECTION_POLICY_REQUIRED)
        if (
            not isinstance(purpose, str)
            or not purpose.strip()
            or type(capability_scope) is not tuple
            or not capability_scope
        ):
            return RuntimeResult(False, RuntimeReason.SELECTION_POLICY_REQUIRED)
        rows = session.execute(
            select(
                ROUTES.c.id, ROUTES.c.agent_id, ROUTES.c.state, AGENTS.c.state.label("agent_state")
            )
            .join(AGENTS, AGENTS.c.id == ROUTES.c.agent_id)
            .order_by(ROUTES.c.id)
        ).all()
        physical_ids = tuple(row.id for row in rows)
        decision = selection_policy.select(
            route_facts=tuple((row.id, row.agent_id, row.state, row.agent_state) for row in rows),
            purpose=purpose,
            capability_scope=capability_scope,
        )
        if decision.ok and (decision.reference_id not in physical_ids):
            return RuntimeResult(False, RuntimeReason.NO_ELIGIBLE_ROUTE)
        return decision

    def acquire_lease(
        self,
        session: Session,
        *,
        route_id: UUID,
        work_item_id: UUID,
        lease_token: UUID,
        lease_validity_seconds: int,
    ) -> RuntimeResult:
        if (
            not isinstance(lease_token, UUID)
            or not isinstance(lease_validity_seconds, int)
            or lease_validity_seconds <= 0
        ):
            raise ValueError("lease duration must be positive")
        route = (
            session.execute(
                select(ROUTES.c.id, ROUTES.c.agent_id, ROUTES.c.state).where(
                    ROUTES.c.id == route_id
                )
            )
            .mappings()
            .one_or_none()
        )
        if route is None or route["state"] != "READY":
            return RuntimeResult(False, RuntimeReason.ROUTE_NOT_READY)
        agent_state = session.execute(
            select(AGENTS.c.state).where(AGENTS.c.id == route["agent_id"])
        ).scalar_one_or_none()
        if agent_state != "READY":
            return RuntimeResult(False, RuntimeReason.AGENT_NOT_READY)
        token = lease_token or uuid4()
        existing = (
            session.execute(select(LEASES).where(LEASES.c.lease_token == token))
            .mappings()
            .one_or_none()
        )
        if existing is not None:
            if existing["route_id"] != route_id or existing["work_item_id"] != work_item_id:
                return RuntimeResult(False, RuntimeReason.IDENTITY_MISMATCH, existing["id"])
            return RuntimeResult(
                existing["state"] == "ACTIVE", "REPLAY_" + existing["state"], existing["id"]
            )
        lease_id = uuid4()
        try:
            with session.begin_nested():
                session.execute(
                    insert(LEASES).values(
                        id=lease_id,
                        route_id=route_id,
                        work_item_id=work_item_id,
                        lease_token=token,
                        lease_started_at=func.now(),
                        lease_expires_at=func.now() + _seconds(lease_validity_seconds),
                        state="ACTIVE",
                    )
                )
        except IntegrityError:
            # The partial unique index is the final race protection.  The
            # savepoint keeps the caller's PostgreSQL transaction usable.
            protected = session.execute(
                select(LEASES.c.id).where(
                    LEASES.c.route_id == route_id,
                    LEASES.c.work_item_id == work_item_id,
                    LEASES.c.state == "ACTIVE",
                )
            ).scalar_one_or_none()
            if protected is not None:
                return RuntimeResult(False, RuntimeReason.LEASE_CONFLICT, protected)
            raise
        return RuntimeResult(True, "GRANTED", lease_id)

    def reconcile_expired(self, session: Session) -> int:
        result = session.execute(
            update(LEASES)
            # PostgreSQL ``now()`` is transaction-start time; expiry is a
            # database-time authority observed at reconciliation time.
            .where(
                LEASES.c.state == "ACTIVE",
                LEASES.c.lease_expires_at <= func.clock_timestamp(),
            )
            .values(state="EXPIRED")
        )
        return result.rowcount or 0

    def resolve_lease(
        self, session: Session, *, lease_id: UUID, lease_token: UUID, terminal_state: str
    ) -> RuntimeResult:
        row = (
            session.execute(select(LEASES).where(LEASES.c.id == lease_id)).mappings().one_or_none()
        )
        if row is None or row["lease_token"] != lease_token:
            return RuntimeResult(False, RuntimeReason.IDENTITY_MISMATCH, lease_id)
        if row["state"] != "ACTIVE":
            return RuntimeResult(False, "LEASE_" + row["state"], lease_id)
        database_now = session.execute(select(func.now())).scalar_one()
        if row["lease_expires_at"] <= database_now:
            session.execute(update(LEASES).where(LEASES.c.id == lease_id).values(state="EXPIRED"))
            return RuntimeResult(False, RuntimeReason.LEASE_EXPIRED, lease_id)
        if terminal_state not in {
            "COMPLETED",
            "RELEASED",
            "AMBIGUOUS",
            "RECONCILIATION_REQUIRED",
            "REVOKED",
        }:
            raise ValueError("unsupported terminal lease state")
        changed = session.execute(
            update(LEASES)
            .where(
                LEASES.c.id == lease_id,
                LEASES.c.lease_token == lease_token,
                LEASES.c.state == "ACTIVE",
                LEASES.c.lease_expires_at > database_now,
            )
            .values(state=terminal_state)
        )
        if changed.rowcount != 1:
            return RuntimeResult(False, "LEASE_STATE_CHANGED", lease_id)
        return RuntimeResult(True, terminal_state, lease_id)

    def safe_diagnostics(
        self, session: Session, *, route_id: UUID | None = None, lease_id: UUID | None = None
    ) -> dict[str, object]:
        result: dict[str, object] = {
            "source": "rf16",
            "protocol_version": "rf16-egress-v1",
            "correlation_id": hashlib.sha256(f"{route_id}:{lease_id}".encode()).hexdigest()[:16],
        }
        if route_id is not None:
            row = (
                session.execute(
                    select(
                        ROUTES.c.id, ROUTES.c.agent_id, ROUTES.c.route_code, ROUTES.c.state
                    ).where(ROUTES.c.id == route_id)
                )
                .mappings()
                .one_or_none()
            )
            if row:
                result.update(
                    {
                        "route_id": str(row["id"]),
                        "agent_id": str(row["agent_id"]),
                        "route_code": row["route_code"],
                        "readiness": self._readiness(session, row["id"], row["state"]),
                    }
                )
        if lease_id is not None:
            row = (
                session.execute(
                    select(LEASES.c.id, LEASES.c.state, LEASES.c.lease_expires_at).where(
                        LEASES.c.id == lease_id
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row:
                result.update(
                    {
                        "lease_id": str(row["id"]),
                        "lease_state": row["state"],
                        "lease_expires_at": row["lease_expires_at"].isoformat(),
                    }
                )
        return result


def _seconds(seconds: int) -> Any:
    from sqlalchemy import cast
    from sqlalchemy.dialects.postgresql import INTERVAL

    return cast(str(seconds) + " seconds", INTERVAL)


__all__ = [
    "AgentProjection",
    "EgressRuntime",
    "LeaseProjection",
    "LeaseState",
    "RouteProjection",
    "RuntimeReason",
    "RuntimeResult",
    "TrustedSelectionPolicyPort",
]

"""Safe Scan projections for future Web/Admin consumers."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from .repository import _table


def current_listing_state(session: Session, beacon_id: UUID) -> list[dict[str, object]]:
    t = _table("scan_beacon_listing_state")
    return [
        dict(r)
        for r in session.execute(
            select(t).where(t.c.beacon_id == beacon_id).order_by(t.c.first_seen_at)
        ).mappings()
    ]


def recent_runs(session: Session, beacon_id: UUID, limit: int = 20) -> list[dict[str, object]]:
    t = _table("scan_runs")
    return [
        dict(r)
        for r in session.execute(
            select(t).where(t.c.beacon_id == beacon_id).order_by(t.c.started_at.desc()).limit(limit)
        ).mappings()
    ]


__all__ = ["current_listing_state", "recent_runs"]

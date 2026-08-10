"""Safe Scan projections for future Web/Admin consumers."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from .repository import _table


def listing_identity_snapshot(session: Session, beacon_id: UUID) -> tuple[dict[str, object], ...]:
    """Return the bounded, identity-only listing projection for acceptance reads."""
    t = _table("scan_beacon_listing_state")
    return tuple(
        {
            "listing_id": str(row["id"]),
            "beacon_id": str(row["beacon_id"]),
            "external_listing_key": str(row["external_listing_key"]),
            "row_version": int(row["row_version"]),
        }
        for row in session.execute(
            select(
                t.c.id,
                t.c.beacon_id,
                t.c.external_listing_key,
                t.c.row_version,
            )
            .where(t.c.beacon_id == beacon_id)
            .order_by(t.c.external_listing_key)
        ).mappings()
    )


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


__all__ = ["current_listing_state", "listing_identity_snapshot", "recent_runs"]

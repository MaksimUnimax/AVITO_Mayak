"""Platform-owned transaction-safe publication of generic internal events."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from mayak.persistence.metadata import metadata

_TABLE = metadata.tables["mayak.platform_event_outbox"]
_MAX_PAYLOAD_BYTES = 65_536


def publish_event(
    session: Session,
    *,
    event_id: UUID,
    event_fingerprint: str,
    contract_name: str,
    contract_version: str,
    payload: dict[str, Any],
    available_at: datetime,
) -> UUID:
    """Insert or return the actual persisted event identity in the caller transaction."""
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    if len(encoded) > _MAX_PAYLOAD_BYTES:
        raise ValueError("event payload exceeds platform persistence bound")
    row = session.execute(
        insert(_TABLE)
        .values(
            id=event_id,
            event_fingerprint=event_fingerprint,
            contract_name=contract_name,
            contract_version=contract_version,
            payload=payload,
            state="PENDING",
            available_at=available_at,
            created_at=available_at,
            attempt_count=0,
            row_version=1,
        )
        .on_conflict_do_nothing(index_elements=["event_fingerprint"])
        .returning(_TABLE.c.id)
    ).scalar_one_or_none()
    if row is not None:
        return row
    return session.execute(
        _TABLE.select()
        .with_only_columns(_TABLE.c.id)
        .where(_TABLE.c.event_fingerprint == event_fingerprint)
    ).scalar_one()


__all__ = ["publish_event"]

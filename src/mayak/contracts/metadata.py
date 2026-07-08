"""Contract metadata primitives."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ContractMetadata(BaseModel):
    """Metadata envelope for a stable public contract message."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    contract_name: str = Field(min_length=1)
    contract_version: str = Field(min_length=1)
    message_id: UUID
    correlation_id: UUID
    causation_id: UUID | None = None
    producer: str = Field(min_length=1)
    account_scope: str | None = Field(default=None, min_length=1)
    beacon_scope: str | None = Field(default=None, min_length=1)
    actor_scope: str | None = Field(default=None, min_length=1)


__all__ = ["ContractMetadata"]

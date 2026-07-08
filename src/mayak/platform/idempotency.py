"""Idempotency primitives shared by the platform."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class _NonEmptyIdempotencyText(BaseModel):
    """Frozen non-empty text wrapper for idempotency primitives."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    value: str = Field(min_length=1)


class IdempotencyFingerprint(_NonEmptyIdempotencyText):
    """Transport-neutral fingerprint for idempotent replay comparison."""


class IdempotencyKey(_NonEmptyIdempotencyText):
    """Transport-neutral idempotency key."""


class IdempotencyScope(_NonEmptyIdempotencyText):
    """Transport-neutral idempotency scope."""


__all__ = ["IdempotencyFingerprint", "IdempotencyKey", "IdempotencyScope"]

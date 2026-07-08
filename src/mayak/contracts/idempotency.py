"""Idempotency decision primitives for public contracts."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from mayak.platform.idempotency import (
    IdempotencyFingerprint,
    IdempotencyKey,
    IdempotencyScope,
)


class IdempotencyDecision(str, Enum):
    NEW = "NEW"
    REPLAY_TERMINAL = "REPLAY_TERMINAL"
    PENDING = "PENDING"
    MISMATCH = "MISMATCH"
    RECONCILE_REQUIRED = "RECONCILE_REQUIRED"


class IdempotencyDecisionOutcome(BaseModel):
    """Safe decision envelope for transport-neutral idempotency handling."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    decision: IdempotencyDecision
    reason_code: str = Field(min_length=1)
    message: str | None = Field(default=None, min_length=1)
    details: tuple[str, ...] = Field(default_factory=tuple)

    @field_validator("details")
    @classmethod
    def _validate_details(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        cleaned_details = tuple(item.strip() for item in value)
        if any(not item for item in cleaned_details):
            raise ValueError("details entries must be non-empty")
        return cleaned_details

    @classmethod
    def new(
        cls,
        *,
        reason_code: str,
        message: str | None = None,
        details: tuple[str, ...] = (),
    ) -> "IdempotencyDecisionOutcome":
        return cls(
            decision=IdempotencyDecision.NEW,
            reason_code=reason_code,
            message=message,
            details=details,
        )

    @classmethod
    def replay_terminal(
        cls,
        *,
        reason_code: str,
        message: str | None = None,
        details: tuple[str, ...] = (),
    ) -> "IdempotencyDecisionOutcome":
        return cls(
            decision=IdempotencyDecision.REPLAY_TERMINAL,
            reason_code=reason_code,
            message=message,
            details=details,
        )

    @classmethod
    def pending(
        cls,
        *,
        reason_code: str,
        message: str | None = None,
        details: tuple[str, ...] = (),
    ) -> "IdempotencyDecisionOutcome":
        return cls(
            decision=IdempotencyDecision.PENDING,
            reason_code=reason_code,
            message=message,
            details=details,
        )

    @classmethod
    def mismatch(
        cls,
        *,
        reason_code: str,
        message: str | None = None,
        details: tuple[str, ...] = (),
    ) -> "IdempotencyDecisionOutcome":
        return cls(
            decision=IdempotencyDecision.MISMATCH,
            reason_code=reason_code,
            message=message,
            details=details,
        )

    @classmethod
    def reconcile_required(
        cls,
        *,
        reason_code: str,
        message: str | None = None,
        details: tuple[str, ...] = (),
    ) -> "IdempotencyDecisionOutcome":
        return cls(
            decision=IdempotencyDecision.RECONCILE_REQUIRED,
            reason_code=reason_code,
            message=message,
            details=details,
        )


__all__ = [
    "IdempotencyDecision",
    "IdempotencyDecisionOutcome",
    "IdempotencyFingerprint",
    "IdempotencyKey",
    "IdempotencyScope",
]

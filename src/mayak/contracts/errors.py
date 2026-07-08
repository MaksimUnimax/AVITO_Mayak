"""Error category primitives for public contracts."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ErrorCategory(str, Enum):
    INVALID_ARGUMENT = "INVALID_ARGUMENT"
    UNAUTHENTICATED = "UNAUTHENTICATED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    PRECONDITION_FAILED = "PRECONDITION_FAILED"
    CONFLICT = "CONFLICT"
    IDEMPOTENCY_MISMATCH = "IDEMPOTENCY_MISMATCH"
    RATE_LIMITED = "RATE_LIMITED"
    EXTERNAL_UNAVAILABLE = "EXTERNAL_UNAVAILABLE"
    EXTERNAL_REJECTED = "EXTERNAL_REJECTED"
    EXTERNAL_AMBIGUOUS = "EXTERNAL_AMBIGUOUS"
    TEMPORARY_FAILURE = "TEMPORARY_FAILURE"
    INTERNAL_FAILURE = "INTERNAL_FAILURE"


class RetryClass(str, Enum):
    NEVER = "NEVER"
    CONDITIONAL = "CONDITIONAL"
    RECONCILE_FIRST = "RECONCILE_FIRST"


class CommonErrorOutcome(BaseModel):
    """Safe outcome envelope for normalized contract errors."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    error_category: ErrorCategory
    retry_class: RetryClass
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


__all__ = ["CommonErrorOutcome", "ErrorCategory", "RetryClass"]

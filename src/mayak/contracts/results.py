"""Result primitives for public contracts."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Result(str, Enum):
    SUCCEEDED = "SUCCEEDED"
    REJECTED = "REJECTED"
    CONFLICT = "CONFLICT"
    FAILED_RETRYABLE = "FAILED_RETRYABLE"
    FAILED_NON_RETRYABLE = "FAILED_NON_RETRYABLE"
    AMBIGUOUS = "AMBIGUOUS"
    PARTIAL = "PARTIAL"


class CommonOutcome(BaseModel):
    """Safe outcome envelope for contract results."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    result: Result
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


# Backwards-compatible alias for callers that prefer a descriptive name.
ResultOutcome = CommonOutcome


__all__ = ["CommonOutcome", "Result", "ResultOutcome"]

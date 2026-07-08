"""Correlation and request/message/run/work identifier primitives."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class _NonEmptyCorrelationText(BaseModel):
    """Frozen non-empty text wrapper for correlation primitives."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    value: str = Field(min_length=1)


class CorrelationId(_NonEmptyCorrelationText):
    """Stable semantic correlation identifier."""


class RequestId(_NonEmptyCorrelationText):
    """Stable semantic request identifier."""


class MessageId(_NonEmptyCorrelationText):
    """Stable semantic message identifier."""


class RunId(_NonEmptyCorrelationText):
    """Stable semantic run identifier."""


class WorkId(_NonEmptyCorrelationText):
    """Stable semantic work identifier."""


class CorrelationContext(BaseModel):
    """Frozen correlation context with safe semantic identifiers."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    correlation_id: CorrelationId
    request_id: RequestId | None = None
    message_id: MessageId | None = None
    run_id: RunId | None = None
    work_id: WorkId | None = None


__all__ = [
    "CorrelationContext",
    "CorrelationId",
    "MessageId",
    "RequestId",
    "RunId",
    "WorkId",
]

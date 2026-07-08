"""Safe redaction helpers."""

from __future__ import annotations

from typing import Final

from pydantic import BaseModel, ConfigDict, Field

REDACTED_VALUE: Final[str] = "[REDACTED]"


class RedactedValue(BaseModel):
    """Stable safe placeholder for a redacted value."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    placeholder: str = Field(default=REDACTED_VALUE, min_length=1)
    is_redacted: bool = True


def redact_sensitive_value(_value: str | None) -> RedactedValue:
    """Replace a sensitive value with a stable placeholder object."""

    return RedactedValue()


__all__ = ["REDACTED_VALUE", "RedactedValue", "redact_sensitive_value"]

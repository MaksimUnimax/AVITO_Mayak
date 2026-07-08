"""Safe redaction helpers."""

from typing import Final

REDACTED_VALUE: Final[str] = "[REDACTED]"


def redact_sensitive_value(value: str | None) -> str:
    """Replace a sensitive value with a stable placeholder."""

    if not value:
        return REDACTED_VALUE
    return REDACTED_VALUE

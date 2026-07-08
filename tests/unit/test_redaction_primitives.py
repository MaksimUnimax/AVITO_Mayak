from __future__ import annotations

import pytest
from pydantic import ValidationError

from mayak.platform.redaction import REDACTED_VALUE, RedactedValue, redact_sensitive_value


def test_redaction_helper_returns_stable_safe_placeholder_object() -> None:
    redacted = redact_sensitive_value("super-secret-token")
    second_redacted = redact_sensitive_value("another-secret")

    assert redacted.placeholder == REDACTED_VALUE
    assert second_redacted.placeholder == REDACTED_VALUE
    assert redacted == second_redacted
    assert "super-secret-token" not in redacted.model_dump_json()
    assert "another-secret" not in second_redacted.model_dump_json()


def test_redacted_value_is_frozen_and_rejects_unknown_fields() -> None:
    redacted = RedactedValue()

    with pytest.raises((TypeError, ValidationError)):
        redacted.placeholder = "changed"  # type: ignore[misc]

    with pytest.raises(ValidationError):
        RedactedValue.model_validate(
            {
                "placeholder": REDACTED_VALUE,
                "unexpected_field": "value",
            }
        )

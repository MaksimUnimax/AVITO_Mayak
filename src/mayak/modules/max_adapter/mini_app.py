"""Server-side MAX WebAppData verification."""

# ruff: noqa: E501

from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl


@dataclass(frozen=True, slots=True)
class MaxMiniAppValidation:
    state: str
    max_user_ref: str | None = None
    reason_code: str = ""
    nonce_hash: str | None = None


def validate_webapp_data(
    data: str,
    *,
    bot_token: str,
    now: int | None = None,
    max_age_seconds: int | None = None,
    policy_reference: str | None = None,
) -> MaxMiniAppValidation:
    if not max_age_seconds or not policy_reference:
        return MaxMiniAppValidation("BLOCKED", reason_code="AUTH_DATE_POLICY_UNCONFIGURED")
    if not data or not bot_token:
        return MaxMiniAppValidation("MALFORMED", reason_code="missing_input")
    try:
        pairs = parse_qsl(data, keep_blank_values=True, strict_parsing=True)
    except ValueError:
        return MaxMiniAppValidation("MALFORMED", reason_code="invalid_encoding")
    if len({key for key, _ in pairs}) != len(pairs):
        return MaxMiniAppValidation("MALFORMED", reason_code="duplicate_parameter")
    values = dict(pairs)
    supplied = values.pop("hash", None)
    if not supplied:
        return MaxMiniAppValidation("MISSING_HASH", reason_code="missing_hash")
    canonical = "\n".join(f"{key}={value}" for key, value in sorted(values.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, canonical.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, supplied):
        return MaxMiniAppValidation("REJECTED", reason_code="invalid_signature")
    try:
        auth_date = int(values["auth_date"])
        if (
            auth_date > int(time.time() if now is None else now)
            or (int(time.time() if now is None else now) - auth_date) > max_age_seconds
        ):
            return MaxMiniAppValidation("STALE", reason_code="auth_date_outside_policy")
    except KeyError, ValueError:
        return MaxMiniAppValidation("MALFORMED", reason_code="invalid_auth_date")
    user = values.get("user")
    if not user:
        return MaxMiniAppValidation("MALFORMED", reason_code="missing_user")
    try:
        import json

        user_ref = str(json.loads(user)["id"])
    except KeyError, TypeError, ValueError, json.JSONDecodeError:
        return MaxMiniAppValidation("MALFORMED", reason_code="invalid_user")
    return MaxMiniAppValidation(
        "VERIFIED", user_ref, "verified", hashlib.sha256(data.encode()).hexdigest()
    )


__all__ = ["MaxMiniAppValidation", "validate_webapp_data"]

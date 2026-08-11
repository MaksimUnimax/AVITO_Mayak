# ruff: noqa: E501
"""Bounded, best-effort structured operational logging for the runtime."""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import time
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any, Iterator

from mayak.platform.correlation import CorrelationContext
from mayak.platform.correlation_context import (
    correlation_context_scope,
    current_correlation_context,
)

_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_CURRENT_FIELDS: ContextVar[dict[str, str] | None] = ContextVar("mayak_log_fields", default=None)
_SECRET_KEYS = {"authorization", "cookie", "password", "secret", "token", "dsn", "payload"}
_SECRET_MESSAGE = re.compile(
    r"(?:bearer\s+[^\s,;]+|password\s*[=:]\s*[^\s,;]+|(?:postgres(?:ql)?|mysql)://[^\s,;]+|"
    r"BEGIN\s+[A-Z ]*PRIVATE KEY|(?:cookie|session|provider[_ -]?token|authorization)\s*[=:]\s*[^\s,;]+|"
    r"raw[_ -]?provider[_ -]?payload\s*[=:]\s*[^\s,;]+)",
    re.IGNORECASE,
)


def safe_identifier(value: str | None) -> str | None:
    if value is None or not _SAFE_ID.fullmatch(value):
        return None
    return value


def correlation_id(value: str | None) -> str:
    return safe_identifier(value) or f"c-{os.urandom(16).hex()}"


def _safe_value(key: str, value: Any) -> Any:
    if key.lower() in _SECRET_KEYS:
        return None
    if isinstance(value, str):
        return value[:256]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return str(value)[:256]


def safe_message(value: str) -> str:
    """Redact secret-shaped legacy/library messages before structured output."""
    return _SECRET_MESSAGE.sub("[REDACTED]", value[:512])


class JsonOperationalFormatter(logging.Formatter):
    """Deterministic NDJSON formatter; formatting failures never escape logging."""

    def format(self, record: logging.LogRecord) -> str:
        data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "environment_id": os.getenv("MAYAK_ENVIRONMENT_ID"),
            "source_sha": os.getenv("MAYAK_SOURCE_SHA"),
            "process_kind": os.getenv("MAYAK_PROCESS_KIND"),
            "producer": record.name,
            "operation": getattr(record, "operation", record.funcName),
            "outcome": getattr(record, "outcome", "unknown"),
            "reason_code": getattr(record, "reason_code", "UNSPECIFIED"),
            "message": safe_message(record.getMessage()),
        }
        fields = _CURRENT_FIELDS.get() or {}
        current = current_correlation_context()
        if current is not None:
            fields = {"correlation_id": current.correlation_id.value, **fields}
        for key in ("correlation_id", "causation_id", "run_id", "work_item_id", "attempt_id", "latency_ms", "readiness_state", "migration_revision"):
            value = getattr(record, key, fields.get(key))
            if value is not None:
                data[key] = _safe_value(key, value)
        return json.dumps(data, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonOperationalFormatter())
    logging.basicConfig(level=getattr(logging, level, logging.INFO), handlers=[handler], force=True)


@contextmanager
def operational_context(context: CorrelationContext | None = None, **fields: str) -> Iterator[None]:
    token = _CURRENT_FIELDS.set({k: v for k, v in fields.items() if safe_identifier(v) is not None})
    try:
        if context is None:
            yield
        else:
            with correlation_context_scope(context):
                yield
    finally:
        _CURRENT_FIELDS.reset(token)


def emit(logger: logging.Logger, *, operation: str, outcome: str, reason_code: str, **fields: Any) -> None:
    """Emit one safe event. Telemetry/logging errors cannot change business flow."""
    try:
        extra = {"operation": operation, "outcome": outcome, "reason_code": reason_code}
        extra.update({key: _safe_value(key, value) for key, value in fields.items() if _safe_value(key, value) is not None})
        logger.info("operational event", extra=extra)
    except Exception:
        return


def monotonic_ms(start: float) -> float:
    return round((time.monotonic() - start) * 1000, 3)


__all__ = ["JsonOperationalFormatter", "configure_logging", "correlation_id", "emit", "monotonic_ms", "operational_context", "safe_identifier", "safe_message"]

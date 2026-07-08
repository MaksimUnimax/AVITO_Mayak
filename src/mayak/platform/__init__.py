"""Platform primitives for Mayak."""

from mayak.platform.boundaries import MODULE_IDS, PLATFORM_AND_CONTRACTS_MODULE_ID
from mayak.platform.config import (
    ConfigurationComponent,
    ConfigurationEnvironment,
    ConfigurationMetadata,
    ConfigurationPresence,
    ConfigurationProvenance,
    ConfigurationSchemaVersion,
    ConfigurationSourceCategory,
)
from mayak.platform.idempotency import (
    IdempotencyFingerprint,
    IdempotencyKey,
    IdempotencyScope,
)
from mayak.platform.redaction import REDACTED_VALUE, RedactedValue, redact_sensitive_value

MODULE_ID = PLATFORM_AND_CONTRACTS_MODULE_ID

__all__ = [
    "ConfigurationComponent",
    "ConfigurationEnvironment",
    "ConfigurationMetadata",
    "ConfigurationPresence",
    "ConfigurationProvenance",
    "ConfigurationSchemaVersion",
    "ConfigurationSourceCategory",
    "IdempotencyFingerprint",
    "IdempotencyKey",
    "IdempotencyScope",
    "REDACTED_VALUE",
    "MODULE_ID",
    "MODULE_IDS",
    "RedactedValue",
    "redact_sensitive_value",
]

"""Platform primitives for Mayak."""

from mayak.platform.audit import (
    AuditActorCategory,
    AuditContext,
    AuditModuleIdentifier,
    AuditOperation,
    AuditReason,
    AuditTargetScope,
)
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
from mayak.platform.correlation import (
    CorrelationContext,
    CorrelationId,
    MessageId,
    RequestId,
    RunId,
    WorkId,
)
from mayak.platform.idempotency import (
    IdempotencyFingerprint,
    IdempotencyKey,
    IdempotencyScope,
)
from mayak.platform.process import ProcessCompositionMetadata, ProcessRole
from mayak.platform.readiness import DependencyReadiness, DependencyReadinessStatus
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
    "CorrelationContext",
    "CorrelationId",
    "MessageId",
    "RequestId",
    "RunId",
    "WorkId",
    "AuditActorCategory",
    "AuditContext",
    "AuditModuleIdentifier",
    "AuditOperation",
    "AuditReason",
    "AuditTargetScope",
    "DependencyReadiness",
    "DependencyReadinessStatus",
    "IdempotencyFingerprint",
    "IdempotencyKey",
    "IdempotencyScope",
    "REDACTED_VALUE",
    "ProcessCompositionMetadata",
    "ProcessRole",
    "MODULE_ID",
    "MODULE_IDS",
    "RedactedValue",
    "redact_sensitive_value",
]

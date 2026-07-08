"""Public contract primitives for Mayak."""

from mayak.contracts.audit import (
    AuditActorCategory,
    AuditConfigurationReference,
    AuditContext,
    AuditContractReference,
    AuditErrorReference,
    AuditReadinessReference,
    AuditResultReference,
)
from mayak.contracts.configuration import (
    ConfigurationValidationOutcome,
    ConfigurationValidationStatus,
)
from mayak.contracts.errors import CommonErrorOutcome, ErrorCategory, RetryClass
from mayak.contracts.idempotency import (
    IdempotencyDecision,
    IdempotencyDecisionOutcome,
    IdempotencyFingerprint,
    IdempotencyKey,
    IdempotencyScope,
)
from mayak.contracts.metadata import ContractMetadata
from mayak.contracts.readiness import (
    ProcessReadinessOutcome,
    ProcessReadinessStatus,
)
from mayak.contracts.results import CommonOutcome, Result, ResultOutcome
from mayak.platform.audit import (
    AuditModuleIdentifier,
    AuditOperation,
    AuditReason,
    AuditTargetScope,
)
from mayak.platform.boundaries import PLATFORM_AND_CONTRACTS_MODULE_ID
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
from mayak.platform.process import ProcessCompositionMetadata, ProcessRole
from mayak.platform.readiness import DependencyReadiness, DependencyReadinessStatus

MODULE_ID = PLATFORM_AND_CONTRACTS_MODULE_ID

__all__ = [
    "AuditActorCategory",
    "AuditConfigurationReference",
    "AuditContext",
    "AuditContractReference",
    "AuditErrorReference",
    "AuditModuleIdentifier",
    "AuditOperation",
    "AuditReadinessReference",
    "AuditReason",
    "AuditResultReference",
    "AuditTargetScope",
    "CommonErrorOutcome",
    "CommonOutcome",
    "ConfigurationComponent",
    "ConfigurationEnvironment",
    "ConfigurationMetadata",
    "ConfigurationPresence",
    "ConfigurationProvenance",
    "ConfigurationSchemaVersion",
    "ConfigurationSourceCategory",
    "ConfigurationValidationOutcome",
    "ConfigurationValidationStatus",
    "CorrelationContext",
    "CorrelationId",
    "DependencyReadiness",
    "DependencyReadinessStatus",
    "ContractMetadata",
    "ErrorCategory",
    "MessageId",
    "IdempotencyDecision",
    "IdempotencyDecisionOutcome",
    "IdempotencyFingerprint",
    "IdempotencyKey",
    "IdempotencyScope",
    "MODULE_ID",
    "ProcessCompositionMetadata",
    "ProcessReadinessOutcome",
    "ProcessReadinessStatus",
    "ProcessRole",
    "RequestId",
    "Result",
    "ResultOutcome",
    "RetryClass",
    "RunId",
    "WorkId",
]

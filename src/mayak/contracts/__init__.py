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
from mayak.contracts.error_mapping import (
    ExceptionMapping,
    ExceptionNormalizationError,
    ExceptionNormalizer,
    build_platform_exception_normalizer,
)
from mayak.contracts.errors import CommonErrorOutcome, ErrorCategory, RetryClass
from mayak.contracts.health import (
    BuildVersionIdentity,
    BuildVersionInfo,
    HealthSnapshot,
    LivenessOutcome,
    LivenessStatus,
    SourceIdentityStatus,
)
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
    compose_process_readiness,
    compose_readiness,
)
from mayak.contracts.registry import (
    ContractRegistration,
    ContractRegistry,
    ContractRegistryError,
    ContractValidationOutcome,
    ContractValidationStatus,
)
from mayak.contracts.results import CommonOutcome, Result, ResultOutcome
from mayak.contracts.serialization import (
    ContractSerializationError,
    canonical_contract_bytes,
    canonical_contract_sha256,
    canonical_contract_text,
    decode_contract_json,
)
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
    "BuildVersionIdentity",
    "BuildVersionInfo",
    "CommonOutcome",
    "ContractSerializationError",
    "ContractRegistration",
    "ContractRegistry",
    "ContractRegistryError",
    "ContractValidationOutcome",
    "ContractValidationStatus",
    "ConfigurationComponent",
    "ConfigurationEnvironment",
    "ConfigurationMetadata",
    "ConfigurationPresence",
    "ConfigurationProvenance",
    "ConfigurationSchemaVersion",
    "ConfigurationSourceCategory",
    "ConfigurationValidationOutcome",
    "ConfigurationValidationStatus",
    "canonical_contract_bytes",
    "canonical_contract_sha256",
    "canonical_contract_text",
    "CorrelationContext",
    "CorrelationId",
    "DependencyReadiness",
    "DependencyReadinessStatus",
    "decode_contract_json",
    "ContractMetadata",
    "ErrorCategory",
    "ExceptionMapping",
    "ExceptionNormalizationError",
    "ExceptionNormalizer",
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
    "HealthSnapshot",
    "LivenessOutcome",
    "LivenessStatus",
    "SourceIdentityStatus",
    "compose_process_readiness",
    "compose_readiness",
    "ProcessRole",
    "RequestId",
    "Result",
    "ResultOutcome",
    "RetryClass",
    "RunId",
    "WorkId",
    "build_platform_exception_normalizer",
]

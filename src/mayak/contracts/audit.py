"""Public contract primitives for audit context references."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from mayak.contracts.configuration import ConfigurationValidationStatus
from mayak.contracts.errors import ErrorCategory
from mayak.contracts.readiness import ProcessReadinessStatus
from mayak.contracts.results import Result
from mayak.platform.audit import (
    AuditActorCategory,
    AuditModuleIdentifier,
    AuditOperation,
    AuditReason,
    AuditTargetScope,
)
from mayak.platform.audit import (
    AuditContext as AuditContextBase,
)
from mayak.platform.config import ConfigurationSchemaVersion
from mayak.platform.correlation import (
    CorrelationContext,
    CorrelationId,
    MessageId,
    RequestId,
    RunId,
    WorkId,
)


class AuditResultReference(BaseModel):
    """Transport-neutral reference to an audit result category."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    result: Result


class AuditErrorReference(BaseModel):
    """Transport-neutral reference to an audit error category."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    error_category: ErrorCategory


class AuditReadinessReference(BaseModel):
    """Transport-neutral reference to a readiness status."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    status: ProcessReadinessStatus


class AuditConfigurationReference(BaseModel):
    """Transport-neutral reference to a configuration validation state."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    status: ConfigurationValidationStatus
    schema_version: ConfigurationSchemaVersion | None = None


class AuditContractReference(BaseModel):
    """Transport-neutral reference to a contract version."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    contract_version: str = Field(min_length=1)


class AuditContext(AuditContextBase):
    """Public audit context with safe outcome references."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    result_reference: AuditResultReference | None = None
    error_reference: AuditErrorReference | None = None
    readiness_reference: AuditReadinessReference | None = None
    configuration_reference: AuditConfigurationReference | None = None
    contract_reference: AuditContractReference | None = None


__all__ = [
    "AuditActorCategory",
    "AuditConfigurationReference",
    "AuditContext",
    "AuditContractReference",
    "AuditErrorReference",
    "AuditModuleIdentifier",
    "AuditOperation",
    "AuditReason",
    "AuditReadinessReference",
    "AuditResultReference",
    "AuditTargetScope",
    "CorrelationContext",
    "CorrelationId",
    "MessageId",
    "RequestId",
    "RunId",
    "WorkId",
]

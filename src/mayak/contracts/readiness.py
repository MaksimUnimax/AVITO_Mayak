"""Public contract primitives for process readiness outcomes."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from mayak.contracts.configuration import (
    ConfigurationValidationOutcome,
    ConfigurationValidationStatus,
)
from mayak.platform.process import ProcessCompositionMetadata, ProcessRole
from mayak.platform.readiness import DependencyReadiness, DependencyReadinessStatus


class ProcessReadinessStatus(str, Enum):
    """Safe process readiness semantics."""

    READY = "READY"
    NOT_READY = "NOT_READY"
    BLOCKED = "BLOCKED"
    SOURCE_UNPROVEN = "SOURCE_UNPROVEN"


class ProcessReadinessOutcome(BaseModel):
    """Frozen outcome envelope for process composition readiness."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    role: ProcessRole
    composition: ProcessCompositionMetadata
    configuration_readiness: ConfigurationValidationOutcome
    dependency_readiness: tuple[DependencyReadiness, ...] = Field(default_factory=tuple)
    status: ProcessReadinessStatus
    reason_code: str = Field(min_length=1)
    message: str | None = Field(default=None, min_length=1)
    details: tuple[str, ...] = Field(default_factory=tuple)

    @field_validator("details")
    @classmethod
    def _validate_details(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        cleaned_details = tuple(item.strip() for item in value)
        if any(not item for item in cleaned_details):
            raise ValueError("details entries must be non-empty")
        return cleaned_details

    @classmethod
    def _create(
        cls,
        *,
        role: ProcessRole,
        composition: ProcessCompositionMetadata,
        configuration_readiness: ConfigurationValidationOutcome,
        dependency_readiness: tuple[DependencyReadiness, ...] = (),
        status: ProcessReadinessStatus,
        reason_code: str,
        message: str | None = None,
        details: tuple[str, ...] = (),
    ) -> "ProcessReadinessOutcome":
        return cls(
            role=role,
            composition=composition,
            configuration_readiness=configuration_readiness,
            dependency_readiness=dependency_readiness,
            status=status,
            reason_code=reason_code,
            message=message,
            details=details,
        )

    @classmethod
    def ready(
        cls,
        *,
        role: ProcessRole,
        composition: ProcessCompositionMetadata,
        configuration_readiness: ConfigurationValidationOutcome,
        dependency_readiness: tuple[DependencyReadiness, ...] = (),
        reason_code: str,
        message: str | None = None,
        details: tuple[str, ...] = (),
    ) -> "ProcessReadinessOutcome":
        return cls._create(
            role=role,
            composition=composition,
            configuration_readiness=configuration_readiness,
            dependency_readiness=dependency_readiness,
            status=ProcessReadinessStatus.READY,
            reason_code=reason_code,
            message=message,
            details=details,
        )


    @classmethod
    def not_ready(
        cls,
        *,
        role: ProcessRole,
        composition: ProcessCompositionMetadata,
        configuration_readiness: ConfigurationValidationOutcome,
        dependency_readiness: tuple[DependencyReadiness, ...] = (),
        reason_code: str,
        message: str | None = None,
        details: tuple[str, ...] = (),
    ) -> "ProcessReadinessOutcome":
        return cls._create(
            role=role,
            composition=composition,
            configuration_readiness=configuration_readiness,
            dependency_readiness=dependency_readiness,
            status=ProcessReadinessStatus.NOT_READY,
            reason_code=reason_code,
            message=message,
            details=details,
        )


    @classmethod
    def blocked(
        cls,
        *,
        role: ProcessRole,
        composition: ProcessCompositionMetadata,
        configuration_readiness: ConfigurationValidationOutcome,
        dependency_readiness: tuple[DependencyReadiness, ...] = (),
        reason_code: str,
        message: str | None = None,
        details: tuple[str, ...] = (),
    ) -> "ProcessReadinessOutcome":
        return cls._create(
            role=role,
            composition=composition,
            configuration_readiness=configuration_readiness,
            dependency_readiness=dependency_readiness,
            status=ProcessReadinessStatus.BLOCKED,
            reason_code=reason_code,
            message=message,
            details=details,
        )

    @classmethod
    def source_unproven(
        cls,
        *,
        role: ProcessRole,
        composition: ProcessCompositionMetadata,
        configuration_readiness: ConfigurationValidationOutcome,
        dependency_readiness: tuple[DependencyReadiness, ...] = (),
        reason_code: str,
        message: str | None = None,
        details: tuple[str, ...] = (),
    ) -> "ProcessReadinessOutcome":
        return cls._create(
            role=role,
            composition=composition,
            configuration_readiness=configuration_readiness,
            dependency_readiness=dependency_readiness,
            status=ProcessReadinessStatus.SOURCE_UNPROVEN,
            reason_code=reason_code,
            message=message,
            details=details,
        )

def compose_process_readiness(
    *,
    role: ProcessRole,
    composition: ProcessCompositionMetadata,
    configuration_readiness: ConfigurationValidationOutcome,
    dependency_readiness: tuple[DependencyReadiness, ...] = (),
) -> ProcessReadinessOutcome:
    """Compose readiness with stable precedence and sorted dependencies."""
    if not isinstance(role, ProcessRole):
        raise TypeError("role must be ProcessRole")
    if not isinstance(composition, ProcessCompositionMetadata):
        raise TypeError("composition must be ProcessCompositionMetadata")
    if not isinstance(configuration_readiness, ConfigurationValidationOutcome):
        raise TypeError("configuration_readiness must be ConfigurationValidationOutcome")
    if any(not isinstance(item, DependencyReadiness) for item in dependency_readiness):
        raise TypeError("dependency_readiness must contain DependencyReadiness values")
    dependencies = tuple(sorted(dependency_readiness, key=lambda item: item.dependency_name))
    if len({item.dependency_name for item in dependencies}) != len(dependencies):
        raise ValueError("dependency readiness names must be unique")
    statuses = [item.status for item in dependencies]
    config_status = configuration_readiness.status
    if config_status is ConfigurationValidationStatus.BLOCKED or (
        DependencyReadinessStatus.BLOCKED in statuses
    ):
        return ProcessReadinessOutcome.blocked(
            role=role, composition=composition, configuration_readiness=configuration_readiness,
            dependency_readiness=dependencies, reason_code="PROCESS_READINESS_BLOCKED",
        )
    if config_status in {
        ConfigurationValidationStatus.INVALID,
        ConfigurationValidationStatus.MISSING,
    } or DependencyReadinessStatus.NOT_READY in statuses:
        return ProcessReadinessOutcome.not_ready(
            role=role, composition=composition, configuration_readiness=configuration_readiness,
            dependency_readiness=dependencies, reason_code="PROCESS_READINESS_NOT_READY",
        )
    if config_status is ConfigurationValidationStatus.SOURCE_UNPROVEN or (
        DependencyReadinessStatus.SOURCE_UNPROVEN in statuses
    ):
        return ProcessReadinessOutcome.source_unproven(
            role=role, composition=composition, configuration_readiness=configuration_readiness,
            dependency_readiness=dependencies, reason_code="PROCESS_READINESS_SOURCE_UNPROVEN",
        )
    return ProcessReadinessOutcome.ready(
        role=role, composition=composition, configuration_readiness=configuration_readiness,
        dependency_readiness=dependencies, reason_code="PROCESS_READINESS_READY",
    )


compose_readiness = compose_process_readiness


__all__ = [
    "ConfigurationValidationOutcome",
    "DependencyReadiness",
    "DependencyReadinessStatus",
    "ProcessCompositionMetadata",
    "ProcessReadinessOutcome",
    "ProcessReadinessStatus",
    "ProcessRole",
    "compose_process_readiness",
    "compose_readiness",
]

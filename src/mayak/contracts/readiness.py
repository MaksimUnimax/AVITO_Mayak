"""Public contract primitives for process readiness outcomes."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from mayak.contracts.configuration import ConfigurationValidationOutcome
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


__all__ = [
    "ConfigurationValidationOutcome",
    "DependencyReadiness",
    "DependencyReadinessStatus",
    "ProcessCompositionMetadata",
    "ProcessReadinessOutcome",
    "ProcessReadinessStatus",
    "ProcessRole",
]

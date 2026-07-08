"""Public contract primitives for typed configuration validation."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from mayak.platform.config import ConfigurationMetadata


class ConfigurationValidationStatus(str, Enum):
    """Transport-neutral validation semantics for typed configuration."""

    READY = "READY"
    INVALID = "INVALID"
    MISSING = "MISSING"
    BLOCKED = "BLOCKED"
    SOURCE_UNPROVEN = "SOURCE_UNPROVEN"


class ConfigurationValidationOutcome(BaseModel):
    """Safe outcome envelope for typed configuration validation."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    status: ConfigurationValidationStatus
    metadata: ConfigurationMetadata
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
        status: ConfigurationValidationStatus,
        metadata: ConfigurationMetadata,
        reason_code: str,
        message: str | None = None,
        details: tuple[str, ...] = (),
    ) -> "ConfigurationValidationOutcome":
        return cls(
            status=status,
            metadata=metadata,
            reason_code=reason_code,
            message=message,
            details=details,
        )

    @classmethod
    def ready(
        cls,
        *,
        metadata: ConfigurationMetadata,
        reason_code: str,
        message: str | None = None,
        details: tuple[str, ...] = (),
    ) -> "ConfigurationValidationOutcome":
        return cls._create(
            status=ConfigurationValidationStatus.READY,
            metadata=metadata,
            reason_code=reason_code,
            message=message,
            details=details,
        )

    @classmethod
    def invalid(
        cls,
        *,
        metadata: ConfigurationMetadata,
        reason_code: str,
        message: str | None = None,
        details: tuple[str, ...] = (),
    ) -> "ConfigurationValidationOutcome":
        return cls._create(
            status=ConfigurationValidationStatus.INVALID,
            metadata=metadata,
            reason_code=reason_code,
            message=message,
            details=details,
        )

    @classmethod
    def missing(
        cls,
        *,
        metadata: ConfigurationMetadata,
        reason_code: str,
        message: str | None = None,
        details: tuple[str, ...] = (),
    ) -> "ConfigurationValidationOutcome":
        return cls._create(
            status=ConfigurationValidationStatus.MISSING,
            metadata=metadata,
            reason_code=reason_code,
            message=message,
            details=details,
        )

    @classmethod
    def blocked(
        cls,
        *,
        metadata: ConfigurationMetadata,
        reason_code: str,
        message: str | None = None,
        details: tuple[str, ...] = (),
    ) -> "ConfigurationValidationOutcome":
        return cls._create(
            status=ConfigurationValidationStatus.BLOCKED,
            metadata=metadata,
            reason_code=reason_code,
            message=message,
            details=details,
        )

    @classmethod
    def source_unproven(
        cls,
        *,
        metadata: ConfigurationMetadata,
        reason_code: str,
        message: str | None = None,
        details: tuple[str, ...] = (),
    ) -> "ConfigurationValidationOutcome":
        return cls._create(
            status=ConfigurationValidationStatus.SOURCE_UNPROVEN,
            metadata=metadata,
            reason_code=reason_code,
            message=message,
            details=details,
        )


__all__ = [
    "ConfigurationValidationOutcome",
    "ConfigurationValidationStatus",
    "ConfigurationMetadata",
]

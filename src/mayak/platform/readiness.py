"""Dependency readiness primitives for process composition."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DependencyReadinessStatus(str, Enum):
    """Safe readiness semantics for an individual dependency."""

    READY = "READY"
    NOT_READY = "NOT_READY"
    BLOCKED = "BLOCKED"
    SOURCE_UNPROVEN = "SOURCE_UNPROVEN"


class DependencyReadiness(BaseModel):
    """Frozen outcome envelope for a declared process dependency."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    dependency_name: str = Field(min_length=1)
    status: DependencyReadinessStatus
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
        dependency_name: str,
        status: DependencyReadinessStatus,
        reason_code: str,
        message: str | None = None,
        details: tuple[str, ...] = (),
    ) -> "DependencyReadiness":
        return cls(
            dependency_name=dependency_name,
            status=status,
            reason_code=reason_code,
            message=message,
            details=details,
        )

    @classmethod
    def ready(
        cls,
        *,
        dependency_name: str,
        reason_code: str,
        message: str | None = None,
        details: tuple[str, ...] = (),
    ) -> "DependencyReadiness":
        return cls._create(
            dependency_name=dependency_name,
            status=DependencyReadinessStatus.READY,
            reason_code=reason_code,
            message=message,
            details=details,
        )

    @classmethod
    def not_ready(
        cls,
        *,
        dependency_name: str,
        reason_code: str,
        message: str | None = None,
        details: tuple[str, ...] = (),
    ) -> "DependencyReadiness":
        return cls._create(
            dependency_name=dependency_name,
            status=DependencyReadinessStatus.NOT_READY,
            reason_code=reason_code,
            message=message,
            details=details,
        )

    @classmethod
    def blocked(
        cls,
        *,
        dependency_name: str,
        reason_code: str,
        message: str | None = None,
        details: tuple[str, ...] = (),
    ) -> "DependencyReadiness":
        return cls._create(
            dependency_name=dependency_name,
            status=DependencyReadinessStatus.BLOCKED,
            reason_code=reason_code,
            message=message,
            details=details,
        )

    @classmethod
    def source_unproven(
        cls,
        *,
        dependency_name: str,
        reason_code: str,
        message: str | None = None,
        details: tuple[str, ...] = (),
    ) -> "DependencyReadiness":
        return cls._create(
            dependency_name=dependency_name,
            status=DependencyReadinessStatus.SOURCE_UNPROVEN,
            reason_code=reason_code,
            message=message,
            details=details,
        )


__all__ = ["DependencyReadiness", "DependencyReadinessStatus"]

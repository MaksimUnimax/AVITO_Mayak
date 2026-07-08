"""Process role and composition primitives for Mayak."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProcessRole(str, Enum):
    """Transport-neutral process role identity."""

    API = "API"
    WORKER = "WORKER"
    SCHEDULER = "SCHEDULER"


class ProcessCompositionMetadata(BaseModel):
    """Frozen metadata describing a process composition surface."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    enabled_modules: tuple[str, ...] = Field(default_factory=tuple)

    @field_validator("enabled_modules")
    @classmethod
    def _validate_enabled_modules(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        cleaned_modules = tuple(item.strip() for item in value)
        if any(not item for item in cleaned_modules):
            raise ValueError("enabled_modules entries must be non-empty")
        return cleaned_modules


__all__ = ["ProcessCompositionMetadata", "ProcessRole"]

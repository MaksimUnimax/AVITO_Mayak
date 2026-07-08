"""Typed configuration metadata primitives shared by platform and contracts."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class _NonEmptyConfigurationText(BaseModel):
    """Frozen non-empty text wrapper for configuration identifiers."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    value: str = Field(min_length=1)


class ConfigurationComponent(_NonEmptyConfigurationText):
    """Logical component that owns the configuration schema."""


class ConfigurationEnvironment(_NonEmptyConfigurationText):
    """Logical environment for the typed configuration metadata."""


class ConfigurationSchemaVersion(_NonEmptyConfigurationText):
    """Stable version identifier for the configuration schema."""


class ConfigurationSourceCategory(str, Enum):
    """Safe provenance category for a configuration value."""

    DEFAULT = "DEFAULT"
    DECLARED = "DECLARED"
    DERIVED = "DERIVED"
    UNKNOWN = "UNKNOWN"


class ConfigurationPresence(str, Enum):
    """Safe presence marker for a configuration value."""

    PRESENT = "PRESENT"
    ABSENT = "ABSENT"


class ConfigurationProvenance(BaseModel):
    """Non-sensitive provenance metadata for a configuration value."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    source_category: ConfigurationSourceCategory
    presence: ConfigurationPresence
    is_proven: bool = True


class ConfigurationMetadata(BaseModel):
    """Typed configuration metadata without sensitive values."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    component: ConfigurationComponent
    environment: ConfigurationEnvironment
    schema_version: ConfigurationSchemaVersion
    provenance: ConfigurationProvenance


__all__ = [
    "ConfigurationComponent",
    "ConfigurationEnvironment",
    "ConfigurationMetadata",
    "ConfigurationPresence",
    "ConfigurationProvenance",
    "ConfigurationSchemaVersion",
    "ConfigurationSourceCategory",
]

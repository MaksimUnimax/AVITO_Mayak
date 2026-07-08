"""Safe audit context primitives."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from mayak.platform.correlation import CorrelationContext


class AuditActorCategory(str, Enum):
    """Redacted semantic actor categories for audit records."""

    REDACTED = "REDACTED"
    SYSTEM = "SYSTEM"
    SERVICE = "SERVICE"
    AUTOMATION = "AUTOMATION"
    OPERATOR = "OPERATOR"
    INTEGRATION = "INTEGRATION"
    UNKNOWN = "UNKNOWN"


class _NonEmptyAuditText(BaseModel):
    """Frozen non-empty text wrapper for audit primitives."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    value: str = Field(min_length=1)


class AuditOperation(_NonEmptyAuditText):
    """Semantic audit operation identifier."""


class AuditModuleIdentifier(_NonEmptyAuditText):
    """Semantic module identifier used by audit records."""


class AuditTargetScope(_NonEmptyAuditText):
    """Category-only target scope for audit records."""


class AuditReason(_NonEmptyAuditText):
    """Safe reason or short summary for an audit record."""


class AuditContext(BaseModel):
    """Frozen audit context with redacted actor and target semantics."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    actor_category: AuditActorCategory
    operation: AuditOperation
    module_id: AuditModuleIdentifier
    target_scope: AuditTargetScope
    reason: AuditReason
    details: tuple[str, ...] = Field(default_factory=tuple)
    correlation: CorrelationContext | None = None

    @field_validator("details")
    @classmethod
    def _validate_details(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        cleaned_details = tuple(item.strip() for item in value)
        if any(not item for item in cleaned_details):
            raise ValueError("details entries must be non-empty")
        return cleaned_details


__all__ = [
    "AuditActorCategory",
    "AuditContext",
    "AuditModuleIdentifier",
    "AuditOperation",
    "AuditReason",
    "AuditTargetScope",
]

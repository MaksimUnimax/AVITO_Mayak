"""Transport-neutral health, build identity and safe diagnostic contracts."""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Any, Mapping, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from mayak.contracts.readiness import ProcessReadinessOutcome, ProcessReadinessStatus
from mayak.platform.process import ProcessRole

_SHA40 = re.compile(r"[0-9a-f]{40}\Z")
_SHA64 = re.compile(r"[0-9a-f]{64}\Z")
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_SAFE_VERSION = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]{0,63}\Z")
_SAFE_IDENTIFIER = re.compile(r"[a-z0-9][a-z0-9_.-]{0,127}\Z")


class SourceIdentityStatus(StrEnum):
    """Whether the running source identity was proven by the build boundary."""

    PROVEN = "PROVEN"
    UNPROVEN = "UNPROVEN"


class LivenessStatus(StrEnum):
    """Process-local liveness, intentionally independent from dependencies."""

    ALIVE = "ALIVE"
    NOT_ALIVE = "NOT_ALIVE"


class BuildVersionIdentity(BaseModel):
    """Immutable, safe build identity with no environment or secret payload."""

    model_config = ConfigDict(
        extra="forbid", frozen=True, str_strip_whitespace=True, hide_input_in_errors=True
    )

    application_version: str = Field(min_length=1)
    environment_id: str = Field(min_length=1)
    source_sha: str | None = None
    lock_identity: str | None = None
    image_digest: str | None = None
    process_role: ProcessRole
    runtime_profile: str = Field(min_length=1)
    migration_revision: str | None = None
    source_status: SourceIdentityStatus

    def model_copy(
        self, *, update: Mapping[str, Any] | None = None, deep: bool = False
    ) -> Self:
        """Copy with Pydantic identity semantics and validated updates."""
        copied = super().model_copy(deep=deep)
        if update is None:
            return copied
        values = {field_name: getattr(copied, field_name) for field_name in type(self).model_fields}
        values.update(update)
        return type(self).model_validate(values)

    @field_validator("environment_id", "runtime_profile", mode="before")
    @classmethod
    def _safe_identifier(cls, value: object) -> object:
        if not isinstance(value, str) or _SAFE_IDENTIFIER.fullmatch(value) is None:
            raise ValueError("diagnostic identifier has an invalid format")
        return value

    @field_validator("application_version")
    @classmethod
    def _safe_application_version(cls, value: str) -> str:
        if _SAFE_VERSION.fullmatch(value) is None:
            raise ValueError("application_version has an unsafe format")
        return value

    @field_validator("source_sha")
    @classmethod
    def _source_sha(cls, value: str | None) -> str | None:
        if value is not None and _SHA40.fullmatch(value) is None:
            raise ValueError("source_sha has an invalid format")
        return value

    @field_validator("lock_identity")
    @classmethod
    def _lock_identity(cls, value: str | None) -> str | None:
        if value is not None and _SHA64.fullmatch(value) is None:
            raise ValueError("lock_identity has an invalid format")
        return value

    @field_validator("image_digest")
    @classmethod
    def _image_digest(cls, value: str | None) -> str | None:
        if value is not None and _DIGEST.fullmatch(value) is None:
            raise ValueError("image_digest has an invalid format")
        return value

    @field_validator("migration_revision")
    @classmethod
    def _migration_revision(cls, value: str | None) -> str | None:
        if value is not None and (not value or len(value) > 128 or any(c.isspace() for c in value)):
            raise ValueError("migration_revision has an invalid format")
        return value

    @model_validator(mode="after")
    def _validate_source_identity(self) -> "BuildVersionIdentity":
        proof_fields = (self.source_sha, self.lock_identity, self.image_digest)
        if self.source_status is SourceIdentityStatus.PROVEN and any(
            value is None for value in proof_fields
        ):
            raise ValueError("PROVEN source identity requires the complete proof triplet")
        if self.source_status is SourceIdentityStatus.UNPROVEN and any(
            value is not None for value in proof_fields
        ):
            raise ValueError("UNPROVEN source identity forbids the proof triplet")
        return self

    @classmethod
    def proven(
        cls,
        *,
        application_version: str,
        environment_id: str,
        source_sha: str,
        lock_identity: str,
        image_digest: str,
        process_role: ProcessRole,
        runtime_profile: str,
        migration_revision: str | None = None,
    ) -> "BuildVersionIdentity":
        return cls(
            application_version=application_version,
            environment_id=environment_id,
            source_sha=source_sha,
            lock_identity=lock_identity,
            image_digest=image_digest,
            process_role=process_role,
            runtime_profile=runtime_profile,
            migration_revision=migration_revision,
            source_status=SourceIdentityStatus.PROVEN,
        )

    @classmethod
    def unproven(
        cls,
        *,
        application_version: str,
        environment_id: str,
        process_role: ProcessRole,
        runtime_profile: str,
        migration_revision: str | None = None,
    ) -> "BuildVersionIdentity":
        return cls(
            application_version=application_version,
            environment_id=environment_id,
            process_role=process_role,
            runtime_profile=runtime_profile,
            migration_revision=migration_revision,
            source_status=SourceIdentityStatus.UNPROVEN,
        )


class LivenessOutcome(BaseModel):
    """Safe liveness result; it contains no dependency diagnostics."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    status: LivenessStatus
    reason_code: str = Field(min_length=1)

    @classmethod
    def alive(cls) -> "LivenessOutcome":
        return cls(status=LivenessStatus.ALIVE, reason_code="PROCESS_ALIVE")

    @classmethod
    def not_alive(cls, reason_code: str = "PROCESS_NOT_ALIVE") -> "LivenessOutcome":
        return cls(status=LivenessStatus.NOT_ALIVE, reason_code=reason_code)


class HealthSnapshot(BaseModel):
    """Safe immutable snapshot composed from identity, liveness and readiness."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    identity: BuildVersionIdentity
    liveness: LivenessOutcome
    readiness: ProcessReadinessOutcome

    def model_copy(
        self, *, update: Mapping[str, Any] | None = None, deep: bool = False
    ) -> Self:
        """Copy with Pydantic nested identity semantics and validated updates."""
        copied = super().model_copy(deep=deep)
        if update is None:
            return copied
        values = {field_name: getattr(copied, field_name) for field_name in type(self).model_fields}
        values.update(update)
        return type(self).model_validate(values)

    @model_validator(mode="after")
    def _validate_identity_readiness_consistency(self) -> "HealthSnapshot":
        if (
            self.identity.source_status is SourceIdentityStatus.UNPROVEN
            and self.readiness.status is ProcessReadinessStatus.READY
        ):
            raise ValueError("UNPROVEN source identity cannot have READY readiness")
        return self

    @property
    def readiness_status(self) -> ProcessReadinessStatus:
        return self.readiness.status


# Descriptive compatibility name used by health consumers.
BuildVersionInfo = BuildVersionIdentity


__all__ = [
    "BuildVersionIdentity",
    "BuildVersionInfo",
    "HealthSnapshot",
    "LivenessOutcome",
    "LivenessStatus",
    "SourceIdentityStatus",
]

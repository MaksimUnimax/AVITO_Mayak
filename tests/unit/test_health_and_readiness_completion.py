from __future__ import annotations

from typing import Any, cast

import pytest
from pydantic import ValidationError

from mayak.contracts.configuration import (
    ConfigurationValidationOutcome,
    ConfigurationValidationStatus,
)
from mayak.contracts.health import (
    BuildVersionIdentity,
    BuildVersionInfo,
    HealthSnapshot,
    LivenessOutcome,
    LivenessStatus,
    SourceIdentityStatus,
)
from mayak.contracts.readiness import (
    ProcessReadinessOutcome,
    ProcessReadinessStatus,
    compose_process_readiness,
)
from mayak.platform.config import (
    ConfigurationComponent,
    ConfigurationEnvironment,
    ConfigurationMetadata,
    ConfigurationPresence,
    ConfigurationProvenance,
    ConfigurationSchemaVersion,
    ConfigurationSourceCategory,
)
from mayak.platform.process import ProcessCompositionMetadata, ProcessRole
from mayak.platform.readiness import DependencyReadiness


def _metadata() -> ConfigurationMetadata:
    return ConfigurationMetadata(
        component=ConfigurationComponent(value="runtime"),
        environment=ConfigurationEnvironment(value="acceptance"),
        schema_version=ConfigurationSchemaVersion(value="1"),
        provenance=ConfigurationProvenance(
            source_category=ConfigurationSourceCategory.DECLARED,
            presence=ConfigurationPresence.PRESENT,
        ),
    )


def _configuration(status: ConfigurationValidationStatus) -> ConfigurationValidationOutcome:
    return ConfigurationValidationOutcome(
        status=status,
        metadata=_metadata(),
        reason_code=f"CONFIGURATION_{status.value}",
    )


def test_readiness_precedence_and_dependency_serialization_are_deterministic() -> None:
    result = compose_process_readiness(
        role=ProcessRole.API,
        composition=ProcessCompositionMetadata(enabled_modules=("mayak.platform",)),
        configuration_readiness=_configuration(ConfigurationValidationStatus.READY),
        dependency_readiness=(
            DependencyReadiness.not_ready(
                dependency_name="database", reason_code="DATABASE_NOT_READY"
            ),
            DependencyReadiness.source_unproven(
                dependency_name="build", reason_code="BUILD_UNPROVEN"
            ),
        ),
    )
    assert result.status is ProcessReadinessStatus.NOT_READY
    assert [item.dependency_name for item in result.dependency_readiness] == ["build", "database"]


def test_blocked_dependency_wins_over_source_unproven() -> None:
    result = compose_process_readiness(
        role=ProcessRole.WORKER,
        composition=ProcessCompositionMetadata(),
        configuration_readiness=_configuration(ConfigurationValidationStatus.SOURCE_UNPROVEN),
        dependency_readiness=(
            DependencyReadiness.blocked(
                dependency_name="database", reason_code="DATABASE_BLOCKED"
            ),
        ),
    )
    assert result.status is ProcessReadinessStatus.BLOCKED


def test_build_identity_can_explicitly_prove_or_withhold_source_identity() -> None:
    proven = BuildVersionIdentity.proven(
        application_version="0.0.0",
        environment_id="acceptance",
        source_sha="a" * 40,
        lock_identity="b" * 64,
        image_digest="sha256:" + "c" * 64,
        process_role=ProcessRole.SCHEDULER,
        runtime_profile="synthetic_acceptance",
    )
    unproven = BuildVersionIdentity.unproven(
        application_version="0.0.0",
        environment_id="acceptance",
        process_role=ProcessRole.API,
        runtime_profile="test",
    )
    assert proven.source_status is SourceIdentityStatus.PROVEN
    assert unproven.source_status is SourceIdentityStatus.UNPROVEN
    assert LivenessOutcome.alive().status is LivenessStatus.ALIVE
    assert "secret" not in repr(proven).lower()


def _identity(status: SourceIdentityStatus, **overrides: object) -> BuildVersionIdentity:
    values: dict[str, object] = {
        "application_version": "0.0.0",
        "environment_id": "acceptance",
        "process_role": ProcessRole.API,
        "runtime_profile": "synthetic_acceptance",
        "source_status": status,
    }
    if status is SourceIdentityStatus.PROVEN:
        values.update(
            source_sha="a" * 40,
            lock_identity="b" * 64,
            image_digest="sha256:" + "c" * 64,
        )
    values.update(overrides)
    return BuildVersionIdentity(**cast(Any, values))


def _readiness(status: ProcessReadinessStatus) -> ProcessReadinessOutcome:
    if status is ProcessReadinessStatus.READY:
        configuration_status = ConfigurationValidationStatus.READY
        dependencies: tuple[DependencyReadiness, ...] = ()
    elif status is ProcessReadinessStatus.SOURCE_UNPROVEN:
        configuration_status = ConfigurationValidationStatus.SOURCE_UNPROVEN
        dependencies = ()
    else:
        configuration_status = (
            ConfigurationValidationStatus.BLOCKED
            if status is ProcessReadinessStatus.BLOCKED
            else ConfigurationValidationStatus.INVALID
        )
        dependencies = ()
    result = compose_process_readiness(
        role=ProcessRole.API,
        composition=ProcessCompositionMetadata(),
        configuration_readiness=_configuration(configuration_status),
        dependency_readiness=dependencies,
    )
    assert result.status is status
    return result


def test_direct_valid_identity_states_are_frozen_and_alias_is_compatible() -> None:
    proven = _identity(SourceIdentityStatus.PROVEN)
    unproven = _identity(SourceIdentityStatus.UNPROVEN)
    assert isinstance(proven, BuildVersionInfo)
    assert proven.model_dump() == {
        "application_version": "0.0.0",
        "environment_id": "acceptance",
        "source_sha": "a" * 40,
        "lock_identity": "b" * 64,
        "image_digest": "sha256:" + "c" * 64,
        "process_role": ProcessRole.API,
        "runtime_profile": "synthetic_acceptance",
        "migration_revision": None,
        "source_status": SourceIdentityStatus.PROVEN,
    }
    assert unproven.source_sha is None
    with pytest.raises(ValidationError):
        proven.application_version = "other"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("status", "overrides"),
    [
        (
            SourceIdentityStatus.PROVEN,
            {"source_sha": None, "lock_identity": None, "image_digest": None},
        ),
        (
            SourceIdentityStatus.PROVEN,
            {"source_sha": "a" * 40, "lock_identity": None, "image_digest": None},
        ),
        (
            SourceIdentityStatus.PROVEN,
            {"source_sha": "a" * 40, "lock_identity": "b" * 64, "image_digest": None},
        ),
        (
            SourceIdentityStatus.PROVEN,
            {
                "source_sha": "a" * 40,
                "lock_identity": None,
                "image_digest": "sha256:" + "c" * 64,
            },
        ),
        (
            SourceIdentityStatus.UNPROVEN,
            {
                "source_sha": "a" * 40,
                "lock_identity": "b" * 64,
                "image_digest": "sha256:" + "c" * 64,
            },
        ),
        (SourceIdentityStatus.UNPROVEN, {"source_sha": "a" * 40}),
        (SourceIdentityStatus.UNPROVEN, {"lock_identity": "b" * 64}),
        (SourceIdentityStatus.UNPROVEN, {"image_digest": "sha256:" + "c" * 64}),
    ],
)
def test_direct_construction_rejects_inconsistent_proof_states(
    status: SourceIdentityStatus, overrides: dict[str, object]
) -> None:
    with pytest.raises(ValidationError, match="source identity|proof triplet"):
        _identity(status, **overrides)


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_sha", "opaque-invalid-source"),
        ("lock_identity", "opaque-invalid-lock"),
        ("image_digest", "opaque-invalid-digest"),
    ],
)
def test_invalid_identity_values_fail_without_echoing_values(field: str, value: str) -> None:
    with pytest.raises(ValidationError) as error:
        _identity(SourceIdentityStatus.PROVEN, **{field: value})
    message = str(error.value)
    assert field in message
    assert value not in message


@pytest.mark.parametrize(
    "value",
    ["acceptance", "synthetic_acceptance", "example-acceptance-01", "mayak.api_01"],
)
def test_safe_diagnostic_identifiers_accept_canonical_values(value: str) -> None:
    assert _identity(SourceIdentityStatus.UNPROVEN, environment_id=value, runtime_profile=value)


@pytest.mark.parametrize(
    "value",
    [" leading", "trailing ", "embedded space", "tab\tvalue", "line\nvalue", "UPPER", "", "shell;", "https://x"],
)
def test_safe_diagnostic_identifiers_reject_unsafe_values(value: str) -> None:
    with pytest.raises(ValidationError):
        _identity(SourceIdentityStatus.UNPROVEN, environment_id=value)
    with pytest.raises(ValidationError):
        _identity(SourceIdentityStatus.UNPROVEN, runtime_profile=value)
    with pytest.raises(ValidationError):
        _identity(SourceIdentityStatus.UNPROVEN, environment_id="a" * 129)


@pytest.mark.parametrize(
    "identity_status,readiness_status",
    [
        (SourceIdentityStatus.PROVEN, ProcessReadinessStatus.READY),
        (SourceIdentityStatus.PROVEN, ProcessReadinessStatus.NOT_READY),
        (SourceIdentityStatus.UNPROVEN, ProcessReadinessStatus.SOURCE_UNPROVEN),
        (SourceIdentityStatus.UNPROVEN, ProcessReadinessStatus.NOT_READY),
        (SourceIdentityStatus.UNPROVEN, ProcessReadinessStatus.BLOCKED),
    ],
)
def test_health_snapshot_accepts_consistent_identity_and_readiness(
    identity_status: SourceIdentityStatus, readiness_status: ProcessReadinessStatus
) -> None:
    snapshot = HealthSnapshot(
        identity=_identity(identity_status),
        liveness=LivenessOutcome.alive(),
        readiness=_readiness(readiness_status),
    )
    assert snapshot.readiness_status is readiness_status


def test_health_snapshot_rejects_unproven_ready_but_liveness_is_independent() -> None:
    with pytest.raises(ValidationError, match="UNPROVEN|READY"):
        HealthSnapshot(
            identity=_identity(SourceIdentityStatus.UNPROVEN),
            liveness=LivenessOutcome.alive(),
            readiness=_readiness(ProcessReadinessStatus.READY),
        )
    alive = HealthSnapshot(
        identity=_identity(SourceIdentityStatus.PROVEN),
        liveness=LivenessOutcome.alive(),
        readiness=_readiness(ProcessReadinessStatus.NOT_READY),
    )
    not_alive = alive.model_copy(update={"liveness": LivenessOutcome.not_alive()})
    assert alive.readiness_status is not_alive.readiness_status is ProcessReadinessStatus.NOT_READY


def test_readiness_precedence_duplicate_types_and_safe_public_exports() -> None:
    blocked = compose_process_readiness(
        role=ProcessRole.API,
        composition=ProcessCompositionMetadata(),
        configuration_readiness=_configuration(ConfigurationValidationStatus.READY),
        dependency_readiness=(
            DependencyReadiness.ready(dependency_name="optional-provider", reason_code="DISABLED"),
            DependencyReadiness.blocked(dependency_name="db", reason_code="BLOCKED"),
            DependencyReadiness.source_unproven(dependency_name="build", reason_code="UNPROVEN"),
        ),
    )
    assert blocked.status is ProcessReadinessStatus.BLOCKED
    assert [item.dependency_name for item in blocked.dependency_readiness] == [
        "build",
        "db",
        "optional-provider",
    ]
    with pytest.raises(ValueError, match="unique"):
        compose_process_readiness(
            role=ProcessRole.API,
            composition=ProcessCompositionMetadata(),
            configuration_readiness=_configuration(ConfigurationValidationStatus.READY),
            dependency_readiness=(
                DependencyReadiness.ready(dependency_name="db", reason_code="A"),
                DependencyReadiness.ready(dependency_name="db", reason_code="B"),
            ),
        )


def test_source_unproven_precedes_ready_and_invalid_dependency_types_are_rejected() -> None:
    source_unproven = compose_process_readiness(
        role=ProcessRole.API,
        composition=ProcessCompositionMetadata(),
        configuration_readiness=_configuration(ConfigurationValidationStatus.SOURCE_UNPROVEN),
    )
    assert source_unproven.status is ProcessReadinessStatus.SOURCE_UNPROVEN
    with pytest.raises(TypeError, match="DependencyReadiness"):
        compose_process_readiness(
            role=ProcessRole.API,
            composition=ProcessCompositionMetadata(),
            configuration_readiness=_configuration(ConfigurationValidationStatus.READY),
            dependency_readiness=(object(),),  # type: ignore[arg-type]
        )

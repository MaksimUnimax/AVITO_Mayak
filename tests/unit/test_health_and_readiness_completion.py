from __future__ import annotations

from mayak.contracts.configuration import (
    ConfigurationValidationOutcome,
    ConfigurationValidationStatus,
)
from mayak.contracts.health import (
    BuildVersionIdentity,
    LivenessOutcome,
    LivenessStatus,
    SourceIdentityStatus,
)
from mayak.contracts.readiness import (
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

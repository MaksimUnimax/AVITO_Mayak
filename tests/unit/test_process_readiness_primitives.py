from __future__ import annotations

from collections.abc import Callable

import pytest
from pydantic import ValidationError

from mayak.contracts.configuration import (
    ConfigurationValidationOutcome,
    ConfigurationValidationStatus,
)
from mayak.contracts.readiness import (
    ProcessReadinessOutcome,
    ProcessReadinessStatus,
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
from mayak.platform.readiness import (
    DependencyReadiness,
    DependencyReadinessStatus,
)


def _build_configuration_metadata() -> ConfigurationMetadata:
    return ConfigurationMetadata(
        component=ConfigurationComponent(value="mayak.platform"),
        environment=ConfigurationEnvironment(value="test"),
        schema_version=ConfigurationSchemaVersion(value="2026.07"),
        provenance=ConfigurationProvenance(
            source_category=ConfigurationSourceCategory.DEFAULT,
            presence=ConfigurationPresence.PRESENT,
            is_proven=True,
        ),
    )


def _build_configuration_validation_outcome(
    builder: Callable[..., ConfigurationValidationOutcome],
    reason_code: str,
) -> ConfigurationValidationOutcome:
    return builder(
        metadata=_build_configuration_metadata(),
        reason_code=reason_code,
        message="safe summary",
        details=("configuration-metadata-only",),
    )


def test_process_role_enum_values_exist() -> None:
    assert [member.name for member in ProcessRole] == [
        "API",
        "WORKER",
        "SCHEDULER",
    ]


def test_process_composition_metadata_can_be_created() -> None:
    composition = ProcessCompositionMetadata(
        enabled_modules=(
            "mayak.platform",
            "mayak.contracts",
        ),
    )

    assert composition.enabled_modules == (
        "mayak.platform",
        "mayak.contracts",
    )
    assert composition.model_dump(mode="json") == {
        "enabled_modules": [
            "mayak.platform",
            "mayak.contracts",
        ]
    }


def test_process_composition_metadata_rejects_unknown_fields_and_is_frozen() -> None:
    composition = ProcessCompositionMetadata(enabled_modules=("mayak.platform",))

    with pytest.raises((TypeError, ValidationError)):
        composition.enabled_modules = ("changed",)  # type: ignore[misc]

    with pytest.raises(ValidationError):
        ProcessCompositionMetadata.model_validate(
            {
                "enabled_modules": ("mayak.platform",),
                "unexpected_field": "value",
            }
        )


def test_dependency_readiness_factories_cover_all_statuses() -> None:
    ready = DependencyReadiness.ready(
        dependency_name="mayak.platform.config",
        reason_code="DEPENDENCY_READY",
        message="safe summary",
        details=("dependency-metadata-only",),
    )
    not_ready = DependencyReadiness.not_ready(
        dependency_name="mayak.platform.cache",
        reason_code="DEPENDENCY_NOT_READY",
    )
    blocked = DependencyReadiness.blocked(
        dependency_name="mayak.platform.scheduler",
        reason_code="DEPENDENCY_BLOCKED",
    )
    source_unproven = DependencyReadiness.source_unproven(
        dependency_name="mayak.platform.source",
        reason_code="DEPENDENCY_SOURCE_UNPROVEN",
    )

    assert ready.status is DependencyReadinessStatus.READY
    assert not_ready.status is DependencyReadinessStatus.NOT_READY
    assert blocked.status is DependencyReadinessStatus.BLOCKED
    assert source_unproven.status is DependencyReadinessStatus.SOURCE_UNPROVEN


def test_dependency_readiness_rejects_unknown_fields_and_is_frozen() -> None:
    dependency = DependencyReadiness.ready(
        dependency_name="mayak.platform.config",
        reason_code="DEPENDENCY_READY",
    )

    with pytest.raises((TypeError, ValidationError)):
        dependency.reason_code = "CHANGED"  # type: ignore[misc]

    with pytest.raises(ValidationError):
        DependencyReadiness.model_validate(
            {
                "dependency_name": "mayak.platform.config",
                "status": "READY",
                "reason_code": "DEPENDENCY_READY",
                "unexpected": "value",
            }
        )


@pytest.mark.parametrize(
    (
        "builder",
        "process_status",
        "configuration_builder",
        "configuration_status",
        "dependency_builder",
        "dependency_status",
        "reason_code",
    ),
    [
        (
            ProcessReadinessOutcome.ready,
            ProcessReadinessStatus.READY,
            ConfigurationValidationOutcome.ready,
            ConfigurationValidationStatus.READY,
            DependencyReadiness.ready,
            DependencyReadinessStatus.READY,
            "PROCESS_READY",
        ),
        (
            ProcessReadinessOutcome.not_ready,
            ProcessReadinessStatus.NOT_READY,
            ConfigurationValidationOutcome.invalid,
            ConfigurationValidationStatus.INVALID,
            DependencyReadiness.not_ready,
            DependencyReadinessStatus.NOT_READY,
            "PROCESS_NOT_READY",
        ),
        (
            ProcessReadinessOutcome.blocked,
            ProcessReadinessStatus.BLOCKED,
            ConfigurationValidationOutcome.blocked,
            ConfigurationValidationStatus.BLOCKED,
            DependencyReadiness.blocked,
            DependencyReadinessStatus.BLOCKED,
            "PROCESS_BLOCKED",
        ),
        (
            ProcessReadinessOutcome.source_unproven,
            ProcessReadinessStatus.SOURCE_UNPROVEN,
            ConfigurationValidationOutcome.source_unproven,
            ConfigurationValidationStatus.SOURCE_UNPROVEN,
            DependencyReadiness.source_unproven,
            DependencyReadinessStatus.SOURCE_UNPROVEN,
            "PROCESS_SOURCE_UNPROVEN",
        ),
    ],
)
def test_process_readiness_outcome_factories(
    builder: Callable[..., ProcessReadinessOutcome],
    process_status: ProcessReadinessStatus,
    configuration_builder: Callable[..., ConfigurationValidationOutcome],
    configuration_status: ConfigurationValidationStatus,
    dependency_builder: Callable[..., DependencyReadiness],
    dependency_status: DependencyReadinessStatus,
    reason_code: str,
) -> None:
    composition = ProcessCompositionMetadata(enabled_modules=("mayak.platform",))
    configuration_readiness = _build_configuration_validation_outcome(
        configuration_builder,
        reason_code=f"CONFIG_{configuration_status.name}",
    )
    dependency_readiness = dependency_builder(
        dependency_name="mayak.platform.config",
        reason_code=f"DEPENDENCY_{dependency_status.name}",
        message="safe summary",
        details=("dependency-metadata-only",),
    )
    outcome = builder(
        role=ProcessRole.API,
        composition=composition,
        configuration_readiness=configuration_readiness,
        dependency_readiness=(dependency_readiness,),
        reason_code=reason_code,
        message="safe summary",
        details=("process-metadata-only",),
    )

    assert outcome.status is process_status
    assert outcome.role is ProcessRole.API
    assert outcome.composition is composition
    assert outcome.configuration_readiness is configuration_readiness
    assert outcome.dependency_readiness == (dependency_readiness,)
    assert outcome.reason_code == reason_code
    assert outcome.message == "safe summary"
    assert outcome.details == ("process-metadata-only",)
    assert set(outcome.model_dump().keys()) == {
        "role",
        "composition",
        "configuration_readiness",
        "dependency_readiness",
        "status",
        "reason_code",
        "message",
        "details",
    }


def test_process_readiness_outcome_rejects_unknown_fields_and_is_frozen() -> None:
    composition = ProcessCompositionMetadata(enabled_modules=("mayak.platform",))
    configuration_readiness = _build_configuration_validation_outcome(
        ConfigurationValidationOutcome.ready,
        reason_code="CONFIG_READY",
    )
    outcome = ProcessReadinessOutcome.ready(
        role=ProcessRole.API,
        composition=composition,
        configuration_readiness=configuration_readiness,
        dependency_readiness=(),
        reason_code="PROCESS_READY",
        message="safe summary",
        details=("process-ready",),
    )

    with pytest.raises((TypeError, ValidationError)):
        outcome.reason_code = "CHANGED"  # type: ignore[misc]

    with pytest.raises(ValidationError):
        ProcessReadinessOutcome.model_validate(
            {
                "role": "API",
                "composition": {"enabled_modules": ("mayak.platform",)},
                "configuration_readiness": {
                    "status": "READY",
                    "metadata": {
                        "component": {"value": "mayak.platform"},
                        "environment": {"value": "test"},
                        "schema_version": {"value": "2026.07"},
                        "provenance": {
                            "source_category": "DEFAULT",
                            "presence": "PRESENT",
                            "is_proven": True,
                        },
                    },
                    "reason_code": "CONFIG_READY",
                    "message": "safe summary",
                    "details": ("configuration-ready",),
                },
                "dependency_readiness": (),
                "status": "READY",
                "reason_code": "PROCESS_READY",
                "message": "safe summary",
                "details": ("process-ready",),
                "unexpected": "value",
            }
        )

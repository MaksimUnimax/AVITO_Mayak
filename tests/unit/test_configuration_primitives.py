from __future__ import annotations

from collections.abc import Callable

import pytest
from pydantic import ValidationError

from mayak.contracts.configuration import (
    ConfigurationValidationOutcome,
    ConfigurationValidationStatus,
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


def _build_configuration_metadata(
    *,
    source_category: ConfigurationSourceCategory = ConfigurationSourceCategory.DEFAULT,
    presence: ConfigurationPresence = ConfigurationPresence.PRESENT,
    is_proven: bool = True,
) -> ConfigurationMetadata:
    return ConfigurationMetadata(
        component=ConfigurationComponent(value="mayak.platform"),
        environment=ConfigurationEnvironment(value="test"),
        schema_version=ConfigurationSchemaVersion(value="2026.07"),
        provenance=ConfigurationProvenance(
            source_category=source_category,
            presence=presence,
            is_proven=is_proven,
        ),
    )


def test_configuration_metadata_can_be_created() -> None:
    metadata = _build_configuration_metadata()

    assert metadata.component.value == "mayak.platform"
    assert metadata.environment.value == "test"
    assert metadata.schema_version.value == "2026.07"
    assert metadata.provenance.source_category is ConfigurationSourceCategory.DEFAULT
    assert metadata.provenance.presence is ConfigurationPresence.PRESENT
    assert metadata.provenance.is_proven is True
    assert metadata.model_dump(mode="json") == {
        "component": {"value": "mayak.platform"},
        "environment": {"value": "test"},
        "schema_version": {"value": "2026.07"},
        "provenance": {
            "source_category": "DEFAULT",
            "presence": "PRESENT",
            "is_proven": True,
        },
    }


def test_configuration_metadata_rejects_unknown_fields_and_is_frozen() -> None:
    metadata = _build_configuration_metadata()

    with pytest.raises((TypeError, ValidationError)):
        metadata.environment = ConfigurationEnvironment(value="prod")  # type: ignore[misc]

    with pytest.raises(ValidationError):
        ConfigurationMetadata.model_validate(
            {
                "component": {"value": "mayak.platform"},
                "environment": {"value": "test"},
                "schema_version": {"value": "2026.07"},
                "provenance": {
                    "source_category": "DEFAULT",
                    "presence": "PRESENT",
                    "is_proven": True,
                },
                "unexpected_field": "value",
            }
        )


@pytest.mark.parametrize(
    ("builder", "status", "source_category", "presence", "is_proven"),
    [
        (
            ConfigurationValidationOutcome.ready,
            ConfigurationValidationStatus.READY,
            ConfigurationSourceCategory.DEFAULT,
            ConfigurationPresence.PRESENT,
            True,
        ),
        (
            ConfigurationValidationOutcome.invalid,
            ConfigurationValidationStatus.INVALID,
            ConfigurationSourceCategory.DECLARED,
            ConfigurationPresence.PRESENT,
            True,
        ),
        (
            ConfigurationValidationOutcome.missing,
            ConfigurationValidationStatus.MISSING,
            ConfigurationSourceCategory.UNKNOWN,
            ConfigurationPresence.ABSENT,
            True,
        ),
        (
            ConfigurationValidationOutcome.blocked,
            ConfigurationValidationStatus.BLOCKED,
            ConfigurationSourceCategory.DERIVED,
            ConfigurationPresence.PRESENT,
            False,
        ),
        (
            ConfigurationValidationOutcome.source_unproven,
            ConfigurationValidationStatus.SOURCE_UNPROVEN,
            ConfigurationSourceCategory.UNKNOWN,
            ConfigurationPresence.PRESENT,
            False,
        ),
    ],
)
def test_configuration_validation_outcome_factories(
    builder: Callable[..., ConfigurationValidationOutcome],
    status: ConfigurationValidationStatus,
    source_category: ConfigurationSourceCategory,
    presence: ConfigurationPresence,
    is_proven: bool,
) -> None:
    metadata = _build_configuration_metadata(
        source_category=source_category,
        presence=presence,
        is_proven=is_proven,
    )
    outcome = builder(
        metadata=metadata,
        reason_code="CONFIG_VALIDATION",
        message="safe summary",
        details=("configuration-metadata-only",),
    )

    assert outcome.status is status
    assert outcome.metadata == metadata
    assert outcome.reason_code == "CONFIG_VALIDATION"
    assert outcome.message == "safe summary"
    assert outcome.details == ("configuration-metadata-only",)
    assert set(outcome.model_dump().keys()) == {
        "status",
        "metadata",
        "reason_code",
        "message",
        "details",
    }


def test_configuration_validation_outcome_is_frozen_and_forbids_extra_fields() -> None:
    metadata = _build_configuration_metadata()
    outcome = ConfigurationValidationOutcome.ready(
        metadata=metadata,
        reason_code="CONFIG_READY",
        message="safe summary",
        details=("configuration-ready",),
    )

    with pytest.raises((TypeError, ValidationError)):
        outcome.reason_code = "CHANGED"  # type: ignore[misc]

    with pytest.raises(ValidationError):
        ConfigurationValidationOutcome.model_validate(
            {
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
                "unexpected": "value",
            }
        )


def test_configuration_value_wrappers_reject_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        ConfigurationComponent.model_validate(
            {
                "value": "mayak.platform",
                "unexpected": "value",
            }
        )

    with pytest.raises(ValidationError):
        ConfigurationProvenance.model_validate(
            {
                "source_category": "DEFAULT",
                "presence": "PRESENT",
                "unexpected": "value",
            }
        )


def test_configuration_provenance_records_source_category_without_values() -> None:
    provenance = ConfigurationProvenance(
        source_category=ConfigurationSourceCategory.DECLARED,
        presence=ConfigurationPresence.PRESENT,
        is_proven=False,
    )

    assert provenance.source_category is ConfigurationSourceCategory.DECLARED
    assert provenance.presence is ConfigurationPresence.PRESENT
    assert provenance.is_proven is False
    assert provenance.model_dump(mode="json") == {
        "source_category": "DECLARED",
        "presence": "PRESENT",
        "is_proven": False,
    }


def test_configuration_wrappers_reject_blank_values() -> None:
    with pytest.raises(ValidationError):
        ConfigurationComponent.model_validate({"value": "   "})

    with pytest.raises(ValidationError):
        ConfigurationEnvironment.model_validate({"value": "   "})

    with pytest.raises(ValidationError):
        ConfigurationSchemaVersion.model_validate({"value": "   "})

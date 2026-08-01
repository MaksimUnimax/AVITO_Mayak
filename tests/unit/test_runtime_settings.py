"""RF-10-08 typed runtime settings tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from mayak.runtime import (
    CANONICAL_NON_SECRET_ENV_KEYS,
    MayakRuntimeSettings,
    RuntimeConfigurationError,
    compose_runtime_settings,
    load_runtime_settings,
)
from mayak.runtime.settings import ProcessKind, ProviderUpdateMode, RuntimeProfile

ROOT = Path(__file__).parents[2]


def base_values() -> dict[str, str]:
    return {
        "MAYAK_ENVIRONMENT_ID": "example-acceptance-01",
        "MAYAK_RUNTIME_PROFILE": "synthetic_acceptance",
        "MAYAK_SOURCE_SHA": "0" * 40,
        "MAYAK_LOCK_IDENTITY": "0" * 64,
        "MAYAK_IMAGE_DIGEST": "sha256:" + "0" * 64,
        "MAYAK_PROCESS_KIND": "mayak-api",
        "MAYAK_DATABASE_APPLICATION_USER": "mayak_app",
        "MAYAK_DATABASE_MIGRATION_USER": "mayak_migration",
    }


def invalid(**changes: str) -> RuntimeConfigurationError:
    values = base_values()
    values.update(changes)
    with pytest.raises(RuntimeConfigurationError) as caught:
        compose_runtime_settings(values)
    return caught.value


def test_public_runtime_package_exports_settings_api() -> None:
    import mayak.runtime as runtime

    assert runtime.__all__ == [
        "CANONICAL_NON_SECRET_ENV_KEYS",
        "DatabaseSSLMode",
        "LogLevel",
        "MayakRuntimeSettings",
        "ProcessKind",
        "ProviderUpdateMode",
        "RuntimeConfigurationError",
        "RuntimeProfile",
        "compose_runtime_settings",
        "load_runtime_settings",
    ]


def test_canonical_non_secret_environment_keys_are_exact_and_ordered() -> None:
    assert len(CANONICAL_NON_SECRET_ENV_KEYS) == 44
    assert len(set(CANONICAL_NON_SECRET_ENV_KEYS)) == 44
    assert CANONICAL_NON_SECRET_ENV_KEYS[0] == "MAYAK_ENVIRONMENT_ID"
    assert CANONICAL_NON_SECRET_ENV_KEYS[-1] == "MAYAK_SECRETS_DIR"


def test_env_example_contains_each_canonical_non_secret_key_once() -> None:
    text = (ROOT / ".env.example").read_text()
    keys = [line.split("=", 1)[0] for line in text.splitlines() if line.startswith("MAYAK_")]
    assert keys == list(CANONICAL_NON_SECRET_ENV_KEYS)


def test_env_example_contains_no_secret_catalog_field_or_filename() -> None:
    text = (ROOT / ".env.example").read_text().lower()
    assert not any(
        word in text for word in ("password", "token", "cookie", "private_key", "webhook_secret")
    )


def test_compose_runtime_settings_builds_exact_nested_groups() -> None:
    settings = compose_runtime_settings(base_values())
    assert list(settings.model_dump().keys()) == [
        "build",
        "runtime",
        "api",
        "database",
        "worker",
        "scheduler",
        "http",
        "session",
        "providers",
        "observability",
        "retention",
        "backup",
    ]


def test_runtime_settings_and_nested_groups_are_frozen() -> None:
    settings = compose_runtime_settings(base_values())
    with pytest.raises((TypeError, ValidationError)):
        settings.api = settings.api
    with pytest.raises((TypeError, ValueError)):
        settings.api.bind_host = "0.0.0.0"


def test_compose_runtime_settings_copies_input_mapping() -> None:
    values = base_values()
    settings = compose_runtime_settings(values)
    values["MAYAK_API_BIND_HOST"] = "0.0.0.0"
    assert settings.api.bind_host == "127.0.0.1"


def test_load_runtime_settings_reads_supplied_mapping_only() -> None:
    values = base_values()
    values["MAYAK_ENVIRONMENT_ID"] = "supplied-only"
    assert load_runtime_settings(values).build.environment_id == "supplied-only"


def test_load_runtime_settings_ignores_non_mayak_environment_keys() -> None:
    values = base_values()
    values["PATH"] = "rejected-if-read"
    assert load_runtime_settings(values).build.environment_id == values["MAYAK_ENVIRONMENT_ID"]


def test_dotenv_files_are_never_loaded() -> None:
    assert MayakRuntimeSettings.model_config["env_prefix"] == ""
    assert load_runtime_settings(base_values()).build.environment_id.startswith("example")


def test_unknown_mayak_key_is_rejected_safely() -> None:
    error = invalid(MAYAK_UNKNOWN="do-not-show")
    assert error.reason_code == "UNKNOWN_MAYAK_KEYS"
    assert error.fields == ("MAYAK_UNKNOWN",)


def test_unknown_key_error_does_not_include_values() -> None:
    error = invalid(MAYAK_UNKNOWN="top-secret-value")
    assert "top-secret-value" not in str(error)
    assert "top-secret-value" not in repr(error)


def test_missing_required_keys_are_reported_without_values() -> None:
    values = base_values()
    del values["MAYAK_SOURCE_SHA"]
    with pytest.raises(RuntimeConfigurationError) as caught:
        compose_runtime_settings(values)
    assert caught.value.reason_code == "MISSING_REQUIRED_KEYS"


def test_invalid_value_error_does_not_expose_rejected_value() -> None:
    error = invalid(MAYAK_SOURCE_SHA="bad-secret-value")
    assert "bad-secret-value" not in repr(error)
    assert error.__cause__ is None
    assert error.__context__ is None


def test_required_build_identifiers_validate_exact_formats() -> None:
    assert invalid(MAYAK_ENVIRONMENT_ID="").reason_code == "INVALID_CONFIGURATION"
    assert invalid(MAYAK_SOURCE_SHA="A" * 40).reason_code == "INVALID_CONFIGURATION"
    assert invalid(MAYAK_LOCK_IDENTITY="1" * 63).reason_code == "INVALID_CONFIGURATION"
    assert invalid(MAYAK_IMAGE_DIGEST="sha256:" + "z" * 64).reason_code == "INVALID_CONFIGURATION"


def test_process_kind_accepts_only_declared_processes() -> None:
    assert invalid(MAYAK_PROCESS_KIND="api").reason_code == "INVALID_CONFIGURATION"
    assert ProcessKind.API.value == "mayak-api"


def test_boolean_parser_accepts_only_lowercase_true_false() -> None:
    assert invalid(MAYAK_SYNTHETIC_IDENTITY_ENABLED="TRUE").reason_code == "INVALID_CONFIGURATION"
    assert not compose_runtime_settings(
        {**base_values(), "MAYAK_SYNTHETIC_IDENTITY_ENABLED": "false"}
    ).session.synthetic_identity_enabled
    assert compose_runtime_settings(
        {**base_values(), "MAYAK_SYNTHETIC_IDENTITY_ENABLED": "true"}
    ).session.synthetic_identity_enabled


def test_integer_parser_rejects_sign_whitespace_and_non_decimal() -> None:
    for value in ("+2", " 2", "2 ", "1e2", "1,2", ""):
        assert (
            invalid(MAYAK_WORKER_POLL_INTERVAL_SECONDS=value).reason_code == "INVALID_CONFIGURATION"
        )


def test_api_defaults_are_local_only() -> None:
    settings = compose_runtime_settings(base_values())
    assert settings.api.bind_host == "127.0.0.1"
    assert settings.api.internal_port == 8000
    assert invalid(MAYAK_API_INTERNAL_PORT="0").reason_code == "INVALID_CONFIGURATION"
    assert invalid(MAYAK_API_BIND_HOST="0.0.0.0").reason_code == "INVALID_CONFIGURATION"
    assert (
        compose_runtime_settings({**base_values(), "MAYAK_RUNTIME_PROFILE": "test"}).runtime.profile
        is RuntimeProfile.TEST
    )


def test_api_host_port_is_disabled_or_in_acceptance_range() -> None:
    assert (
        compose_runtime_settings({**base_values(), "MAYAK_API_HOST_PORT": "18085"}).api.host_port
        == 18085
    )
    assert invalid(MAYAK_API_HOST_PORT="18000").reason_code == "INVALID_CONFIGURATION"
    assert invalid(MAYAK_API_HOST_PORT="abc").reason_code == "INVALID_CONFIGURATION"
    assert invalid(MAYAK_API_HOST_PORT=" abc ").reason_code == "INVALID_CONFIGURATION"


def test_database_defaults_use_internal_postgres_boundary() -> None:
    settings = compose_runtime_settings(base_values())
    assert settings.database.host == "mayak-postgres"
    assert settings.database.port == 5432
    assert invalid(MAYAK_SECRETS_DIR="relative").reason_code == "INVALID_CONFIGURATION"


def test_database_application_and_migration_users_must_differ() -> None:
    assert invalid(MAYAK_DATABASE_MIGRATION_USER="mayak_app").reason_code == "INVALID_CONFIGURATION"
    assert (
        invalid(MAYAK_DATABASE_APPLICATION_USER="bad role").reason_code == "INVALID_CONFIGURATION"
    )
    settings = compose_runtime_settings(base_values())
    duplicate = settings.database.model_copy(update={"migration_user": "mayak_app"})
    with pytest.raises(ValueError):
        settings.model_copy(update={"database": duplicate})._validate_invariants()  # type: ignore[operator]


def test_worker_lease_must_exceed_poll_interval() -> None:
    assert (
        invalid(
            MAYAK_WORKER_POLL_INTERVAL_SECONDS="30", MAYAK_WORKER_LEASE_SECONDS="30"
        ).reason_code
        == "INVALID_CONFIGURATION"
    )


def test_all_duration_batch_and_size_bounds_are_enforced() -> None:
    assert invalid(MAYAK_HTTP_MAX_RESPONSE_BYTES="0").reason_code == "INVALID_CONFIGURATION"
    assert invalid(MAYAK_WORKER_BATCH_SIZE="1001").reason_code == "INVALID_CONFIGURATION"
    assert (
        invalid(MAYAK_DATABASE_CONNECT_TIMEOUT_SECONDS="0").reason_code == "INVALID_CONFIGURATION"
    )
    assert invalid(MAYAK_DATABASE_PORT="0").reason_code == "INVALID_CONFIGURATION"


def test_session_max_age_is_bounded_for_acceptance_profiles() -> None:
    assert invalid(MAYAK_SESSION_MAX_AGE_SECONDS="86401").reason_code == "INVALID_CONFIGURATION"


def test_synthetic_identity_is_rejected_in_production() -> None:
    assert (
        invalid(
            MAYAK_RUNTIME_PROFILE="production", MAYAK_SYNTHETIC_IDENTITY_ENABLED="true"
        ).reason_code
        == "INVALID_CONFIGURATION"
    )


def test_provider_enable_flags_default_false() -> None:
    settings = compose_runtime_settings(base_values())
    assert not settings.providers.avito_live_enabled
    assert not settings.providers.telegram_enabled
    assert not settings.providers.max_enabled


def test_live_provider_enablement_is_rejected_outside_operator_acceptance() -> None:
    assert invalid(MAYAK_AVITO_LIVE_ENABLED="true").reason_code == "INVALID_CONFIGURATION"
    assert (
        invalid(
            MAYAK_RUNTIME_PROFILE="operator_acceptance",
            MAYAK_TELEGRAM_ENABLED="true",
        ).reason_code
        == "INVALID_CONFIGURATION"
    )


def test_disabled_provider_requires_disabled_update_mode() -> None:
    assert invalid(MAYAK_TELEGRAM_UPDATE_MODE="webhook").reason_code == "INVALID_CONFIGURATION"
    assert invalid(MAYAK_LOG_FORMAT="plain").reason_code == "INVALID_CONFIGURATION"


def test_long_polling_test_mode_is_limited_to_test_profiles() -> None:
    assert (
        invalid(
            MAYAK_TELEGRAM_UPDATE_MODE="long_polling_test",
            MAYAK_RUNTIME_PROFILE="operator_acceptance",
        ).reason_code
        == "INVALID_CONFIGURATION"
    )
    settings = compose_runtime_settings(
        {**base_values(), "MAYAK_TELEGRAM_UPDATE_MODE": "long_polling_test"}
    )
    assert settings.providers.telegram_update_mode is ProviderUpdateMode.LONG_POLLING_TEST


def test_otel_enablement_and_endpoint_must_be_consistent() -> None:
    assert invalid(MAYAK_OTEL_ENABLED="true").reason_code == "INVALID_CONFIGURATION"
    values = {
        **base_values(),
        "MAYAK_OTEL_ENABLED": "true",
        "MAYAK_OTEL_EXPORTER_ENDPOINT": "https://otel.example.test",
    }
    assert compose_runtime_settings(values).observability.otel_enabled


def test_model_dump_repr_and_error_surfaces_contain_no_secret_material() -> None:
    secret = "super-secret-not-a-setting"
    error = invalid(MAYAK_UNKNOWN=secret)
    settings = compose_runtime_settings(base_values())
    assert secret not in repr(settings.model_dump())
    assert secret not in repr(error)
    assert not any(
        "password" in field.lower() or "token" in field.lower()
        for field in MayakRuntimeSettings.model_fields
    )

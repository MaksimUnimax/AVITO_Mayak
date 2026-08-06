"""Strict, non-secret runtime configuration composition."""

# ruff: noqa: E501

from __future__ import annotations

import ipaddress
import os
import re
from enum import StrEnum
from pathlib import Path
from typing import Mapping, Self, cast

from pydantic import BaseModel, ConfigDict, HttpUrl, ValidationError, model_validator
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

CANONICAL_NON_SECRET_ENV_KEYS = (
    "MAYAK_ENVIRONMENT_ID",
    "MAYAK_RUNTIME_PROFILE",
    "MAYAK_SOURCE_SHA",
    "MAYAK_LOCK_IDENTITY",
    "MAYAK_IMAGE_DIGEST",
    "MAYAK_PROCESS_KIND",
    "MAYAK_LOG_LEVEL",
    "MAYAK_LOG_FORMAT",
    "MAYAK_API_BIND_HOST",
    "MAYAK_API_INTERNAL_PORT",
    "MAYAK_API_HOST_PORT",
    "MAYAK_DATABASE_HOST",
    "MAYAK_DATABASE_PORT",
    "MAYAK_DATABASE_NAME",
    "MAYAK_DATABASE_APPLICATION_USER",
    "MAYAK_DATABASE_MIGRATION_USER",
    "MAYAK_DATABASE_SSLMODE",
    "MAYAK_DATABASE_CONNECT_TIMEOUT_SECONDS",
    "MAYAK_WORKER_POLL_INTERVAL_SECONDS",
    "MAYAK_WORKER_LEASE_SECONDS",
    "MAYAK_WORKER_BATCH_SIZE",
    "MAYAK_SCHEDULER_POLL_INTERVAL_SECONDS",
    "MAYAK_OUTBOX_BATCH_SIZE",
    "MAYAK_HTTP_CONNECT_TIMEOUT_SECONDS",
    "MAYAK_HTTP_READ_TIMEOUT_SECONDS",
    "MAYAK_HTTP_WRITE_TIMEOUT_SECONDS",
    "MAYAK_HTTP_POOL_TIMEOUT_SECONDS",
    "MAYAK_HTTP_MAX_RESPONSE_BYTES",
    "MAYAK_SESSION_MAX_AGE_SECONDS",
    "MAYAK_SYNTHETIC_IDENTITY_ENABLED",
    "MAYAK_AVITO_LIVE_ENABLED",
    "MAYAK_TELEGRAM_ENABLED",
    "MAYAK_TELEGRAM_UPDATE_MODE",
    "MAYAK_MAX_ENABLED",
    "MAYAK_MAX_UPDATE_MODE",
    "MAYAK_YOOKASSA_ENABLED",
    "MAYAK_YOOKASSA_SHOP_ID",
    "MAYAK_YOOKASSA_SECRET_FILE",
    "MAYAK_EGRESS_AGENT_ENABLED",
    "MAYAK_OTEL_ENABLED",
    "MAYAK_OTEL_EXPORTER_ENDPOINT",
    "MAYAK_BACKUP_ROOT",
    "MAYAK_BACKUP_RETENTION_DAYS",
    "MAYAK_SECRETS_DIR",
    "MAYAK_SYNTHETIC_SCENARIO",
    "MAYAK_SYNTHETIC_SCENARIO_RUN_ID",
)


class RuntimeProfile(StrEnum):
    TEST = "test"
    SYNTHETIC_ACCEPTANCE = "synthetic_acceptance"
    OPERATOR_ACCEPTANCE = "operator_acceptance"
    PRODUCTION = "production"


class ProcessKind(StrEnum):
    API = "mayak-api"
    WORKER = "mayak-worker"
    SCHEDULER = "mayak-scheduler"
    DB_BOOTSTRAP = "mayak-db-bootstrap"
    MIGRATE = "mayak-migrate"
    POSTGRES = "mayak-postgres"
    BACKUP = "mayak-backup"
    RESTORE_CHECK = "mayak-restore-check"


class ProviderUpdateMode(StrEnum):
    DISABLED = "disabled"
    WEBHOOK = "webhook"
    LONG_POLLING_TEST = "long_polling_test"


class DatabaseSSLMode(StrEnum):
    DISABLE = "disable"


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class RuntimeConfigurationError(ValueError):
    """Safe configuration failure that retains only canonical field names."""

    def __init__(self, reason_code: str, fields: tuple[str, ...]) -> None:
        self.reason_code = reason_code
        self.fields = tuple(sorted(set(fields)))
        super().__init__("runtime configuration is invalid")


_CONFIG = ConfigDict(extra="forbid", frozen=True)
_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
_ROLE = re.compile(r"^[a-z_][a-z0-9_$]{0,62}$")
_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_DIGITS = re.compile(r"^[0-9]+$")


class _Build(BaseModel):
    model_config = _CONFIG
    environment_id: str
    source_sha: str
    lock_identity: str
    image_digest: str


class _Runtime(BaseModel):
    model_config = _CONFIG
    profile: RuntimeProfile
    process_kind: ProcessKind
    secrets_dir: Path = Path("/run/secrets")


class _API(BaseModel):
    model_config = _CONFIG
    bind_host: str = "127.0.0.1"
    internal_port: int = 8000
    host_port: int | None = None


class _Database(BaseModel):
    model_config = _CONFIG
    host: str = "mayak-postgres"
    port: int = 5432
    name: str = "mayak"
    application_user: str
    migration_user: str
    sslmode: DatabaseSSLMode = DatabaseSSLMode.DISABLE
    connect_timeout_seconds: int = 10


class _Worker(BaseModel):
    model_config = _CONFIG
    poll_interval_seconds: int = 2
    lease_seconds: int = 30
    batch_size: int = 50
    outbox_batch_size: int = 50


class _Scheduler(BaseModel):
    model_config = _CONFIG
    poll_interval_seconds: int = 30


class _HTTP(BaseModel):
    model_config = _CONFIG
    connect_timeout_seconds: int = 5
    read_timeout_seconds: int = 30
    write_timeout_seconds: int = 30
    pool_timeout_seconds: int = 5
    max_response_bytes: int = 2_097_152


class _Session(BaseModel):
    model_config = _CONFIG
    max_age_seconds: int = 86_400
    synthetic_identity_enabled: bool = False
    link_challenge_ttl_seconds: int = 900
    admin_bootstrap_enabled: bool = False


class _Providers(BaseModel):
    model_config = _CONFIG
    avito_live_enabled: bool = False
    telegram_enabled: bool = False
    telegram_update_mode: ProviderUpdateMode = ProviderUpdateMode.DISABLED
    max_enabled: bool = False
    max_update_mode: ProviderUpdateMode = ProviderUpdateMode.DISABLED
    yookassa_enabled: bool = False
    yookassa_shop_id: str | None = None
    yookassa_api_base: HttpUrl = HttpUrl("https://api.yookassa.ru/v3")
    yookassa_secret_file: Path = Path("/run/secrets/mayak_yookassa_secret")
    egress_agent_enabled: bool = False


class _Observability(BaseModel):
    model_config = _CONFIG
    log_level: LogLevel = LogLevel.INFO
    log_format: str = "json"
    otel_enabled: bool = False
    otel_exporter_endpoint: HttpUrl | None = None


class _Retention(BaseModel):
    model_config = _CONFIG
    backup_retention_days: int = 7


class _Backup(BaseModel):
    model_config = _CONFIG
    backup_root: Path = Path("/var/backups/avito-mayak")


class MayakRuntimeSettings(BaseSettings):
    """Immutable runtime settings assembled exclusively from explicit init data."""

    model_config = SettingsConfigDict(
        extra="forbid", frozen=True, env_prefix="", case_sensitive=True
    )
    build: _Build
    runtime: _Runtime
    api: _API
    database: _Database
    worker: _Worker
    scheduler: _Scheduler
    http: _HTTP
    session: _Session
    providers: _Providers
    observability: _Observability
    retention: _Retention
    backup: _Backup

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (init_settings,)

    @model_validator(mode="after")
    def _validate_invariants(self) -> Self:
        if self.worker.lease_seconds <= self.worker.poll_interval_seconds:
            raise ValueError("worker lease must exceed poll interval")
        if self.database.application_user == self.database.migration_user:
            raise ValueError("database roles must differ")
        if self.api.internal_port not in range(1, 65_536):
            raise ValueError("invalid port")
        if self.database.port not in range(1, 65_536):
            raise ValueError("invalid port")
        if self.api.host_port is not None and self.api.host_port not in range(18_080, 18_100):
            raise ValueError("invalid host port")
        if self.runtime.profile in {
            RuntimeProfile.SYNTHETIC_ACCEPTANCE,
            RuntimeProfile.OPERATOR_ACCEPTANCE,
            RuntimeProfile.PRODUCTION,
        }:
            if (
                self.api.bind_host != "127.0.0.1"
                and not (self.api.bind_host == "0.0.0.0" and self.api.host_port is not None)
            ) or (
                self.database.host != "mayak-postgres"
                and not (
                    self.runtime.profile is RuntimeProfile.SYNTHETIC_ACCEPTANCE
                    and ipaddress.ip_address(self.database.host).is_private
                )
            ):
                raise ValueError("acceptance boundary violation")
        if (
            self.runtime.profile is RuntimeProfile.PRODUCTION
            and self.session.synthetic_identity_enabled
        ):
            raise ValueError("synthetic identity is not allowed")
        if (
            self.session.synthetic_identity_enabled
            and self.runtime.profile is not RuntimeProfile.SYNTHETIC_ACCEPTANCE
        ):
            raise ValueError("synthetic identity is acceptance-only")
        if (
            self.session.admin_bootstrap_enabled
            and self.runtime.profile is not RuntimeProfile.SYNTHETIC_ACCEPTANCE
        ):
            raise ValueError("admin bootstrap is acceptance-only")
        if not 1 <= self.session.max_age_seconds <= 86_400:
            raise ValueError("session ttl out of bounds")
        if not 1 <= self.session.link_challenge_ttl_seconds <= 900:
            raise ValueError("link challenge ttl out of bounds")
        if self.runtime.profile is not RuntimeProfile.OPERATOR_ACCEPTANCE and any(
            (
                self.providers.avito_live_enabled,
                self.providers.telegram_enabled,
                self.providers.max_enabled,
                self.providers.yookassa_enabled,
                self.providers.egress_agent_enabled,
            )
        ):
            raise ValueError("live provider enablement is restricted")
        for enabled, mode in (
            (self.providers.telegram_enabled, self.providers.telegram_update_mode),
            (self.providers.max_enabled, self.providers.max_update_mode),
        ):
            if enabled and mode is not ProviderUpdateMode.WEBHOOK:
                raise ValueError("enabled provider requires webhook")
            if not enabled and mode is ProviderUpdateMode.WEBHOOK:
                raise ValueError("disabled provider requires disabled mode")
            if mode is ProviderUpdateMode.LONG_POLLING_TEST and self.runtime.profile not in {
                RuntimeProfile.TEST,
                RuntimeProfile.SYNTHETIC_ACCEPTANCE,
            }:
                raise ValueError("long polling is test-only")
        if self.observability.log_format != "json":
            raise ValueError("invalid log format")
        if self.observability.otel_enabled != (
            self.observability.otel_exporter_endpoint is not None
        ):
            raise ValueError("otel endpoint and enablement must agree")
        return self


_REQUIRED = {
    "MAYAK_ENVIRONMENT_ID",
    "MAYAK_RUNTIME_PROFILE",
    "MAYAK_SOURCE_SHA",
    "MAYAK_LOCK_IDENTITY",
    "MAYAK_IMAGE_DIGEST",
    "MAYAK_PROCESS_KIND",
    "MAYAK_DATABASE_APPLICATION_USER",
    "MAYAK_DATABASE_MIGRATION_USER",
}

_IDENTITY_RUNTIME_ENV_KEYS = {
    "MAYAK_IDENTITY_LINK_CHALLENGE_TTL_SECONDS",
    "MAYAK_IDENTITY_ADMIN_BOOTSTRAP_ENABLED",
}

_RF12_PROVIDER_ENV_KEYS = {
    "MAYAK_YOOKASSA_API_BASE",
    "MAYAK_YOOKASSA_SECRET_FILE",
}


def _error(reason: str, fields: list[str]) -> RuntimeConfigurationError:
    return RuntimeConfigurationError(reason, tuple(fields))


def _text(values: Mapping[str, str], key: str, default: str | None = None) -> str:
    value = values.get(key, default)
    if value is None or not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(key)
    return value


def _optional_text(values: Mapping[str, str], key: str) -> str | None:
    value = values.get(key, "").strip()
    return value or None


def _int(values: Mapping[str, str], key: str, default: int) -> int:
    value = values.get(key)
    if value is None:
        return default
    if not isinstance(value, str) or not _DIGITS.fullmatch(value):
        raise ValueError(key)
    return int(value)


def _bool(values: Mapping[str, str], key: str, default: bool) -> bool:
    value = values.get(key)
    if value is None:
        return default
    if value == "true":
        return True
    if value == "false":
        return False
    raise ValueError(key)


def _optional_disabled(values: Mapping[str, str], key: str) -> str | None:
    value = values.get(key)
    if value is None or value == "disabled":
        return None
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(key)
    return value


def _host_port(values: Mapping[str, str]) -> int | None:
    value = _optional_disabled(values, "MAYAK_API_HOST_PORT")
    if value is None:
        return None
    if not _DIGITS.fullmatch(value):
        raise ValueError("MAYAK_API_HOST_PORT")
    return int(value)


def _path(values: Mapping[str, str], key: str, default: str) -> Path:
    value = values.get(key, default)
    if not isinstance(value, str) or not value.startswith("/") or value != value.strip():
        raise ValueError(key)
    return Path(value)


def compose_runtime_settings(values: Mapping[str, str]) -> MayakRuntimeSettings:
    """Compose a new immutable settings object from a caller-owned mapping."""
    copied = dict(values)
    unknown = sorted(
        key
        for key in copied
        if key.startswith("MAYAK_")
        and key not in CANONICAL_NON_SECRET_ENV_KEYS
        and key not in _IDENTITY_RUNTIME_ENV_KEYS
        and key not in _RF12_PROVIDER_ENV_KEYS
    )
    if unknown:
        raise _error("UNKNOWN_MAYAK_KEYS", unknown)
    missing = sorted(_REQUIRED - copied.keys())
    if missing:
        raise _error("MISSING_REQUIRED_KEYS", missing)
    try:
        profile = RuntimeProfile(_text(copied, "MAYAK_RUNTIME_PROFILE"))
        process = ProcessKind(_text(copied, "MAYAK_PROCESS_KIND"))
        environment_id = _text(copied, "MAYAK_ENVIRONMENT_ID")
        source_sha = _text(copied, "MAYAK_SOURCE_SHA")
        lock_identity = _text(copied, "MAYAK_LOCK_IDENTITY")
        image_digest = _text(copied, "MAYAK_IMAGE_DIGEST")
        if (
            not _IDENTIFIER.fullmatch(environment_id)
            or not _HEX40.fullmatch(source_sha)
            or not _HEX64.fullmatch(lock_identity)
            or not re.fullmatch(r"sha256:[0-9a-f]{64}", image_digest)
        ):
            raise ValueError("build")
        app_user = _text(copied, "MAYAK_DATABASE_APPLICATION_USER")
        migration_user = _text(copied, "MAYAK_DATABASE_MIGRATION_USER")
        if not _ROLE.fullmatch(app_user) or not _ROLE.fullmatch(migration_user):
            raise ValueError("database")
        if app_user == migration_user:
            raise ValueError("database")

        def positive(key: str, default: int) -> int:
            value = _int(copied, key, default)
            if not 1 <= value <= 86_400:
                raise ValueError(key)
            return value

        api_host_port = _host_port(copied)
        settings = MayakRuntimeSettings(
            build=cast(
                _Build,
                {
                    "environment_id": environment_id,
                    "source_sha": source_sha,
                    "lock_identity": lock_identity,
                    "image_digest": image_digest,
                },
            ),
            runtime=cast(
                _Runtime,
                {
                    "profile": profile,
                    "process_kind": process,
                    "secrets_dir": _path(copied, "MAYAK_SECRETS_DIR", "/run/secrets"),
                },
            ),
            api=cast(
                _API,
                {
                    "bind_host": _text(copied, "MAYAK_API_BIND_HOST", "127.0.0.1"),
                    "internal_port": _int(copied, "MAYAK_API_INTERNAL_PORT", 8000),
                    "host_port": api_host_port,
                },
            ),
            database=cast(
                _Database,
                {
                    "host": _text(copied, "MAYAK_DATABASE_HOST", "mayak-postgres"),
                    "port": _int(copied, "MAYAK_DATABASE_PORT", 5432),
                    "name": _text(copied, "MAYAK_DATABASE_NAME", "mayak"),
                    "application_user": app_user,
                    "migration_user": migration_user,
                    "sslmode": DatabaseSSLMode(_text(copied, "MAYAK_DATABASE_SSLMODE", "disable")),
                    "connect_timeout_seconds": positive(
                        "MAYAK_DATABASE_CONNECT_TIMEOUT_SECONDS", 10
                    ),
                },
            ),
            worker=cast(
                _Worker,
                {
                    "poll_interval_seconds": positive("MAYAK_WORKER_POLL_INTERVAL_SECONDS", 2),
                    "lease_seconds": positive("MAYAK_WORKER_LEASE_SECONDS", 30),
                    "batch_size": _int(copied, "MAYAK_WORKER_BATCH_SIZE", 50),
                    "outbox_batch_size": _int(copied, "MAYAK_OUTBOX_BATCH_SIZE", 50),
                },
            ),
            scheduler=cast(
                _Scheduler,
                {"poll_interval_seconds": positive("MAYAK_SCHEDULER_POLL_INTERVAL_SECONDS", 30)},
            ),
            http=cast(
                _HTTP,
                {
                    "connect_timeout_seconds": positive("MAYAK_HTTP_CONNECT_TIMEOUT_SECONDS", 5),
                    "read_timeout_seconds": positive("MAYAK_HTTP_READ_TIMEOUT_SECONDS", 30),
                    "write_timeout_seconds": positive("MAYAK_HTTP_WRITE_TIMEOUT_SECONDS", 30),
                    "pool_timeout_seconds": positive("MAYAK_HTTP_POOL_TIMEOUT_SECONDS", 5),
                    "max_response_bytes": _int(copied, "MAYAK_HTTP_MAX_RESPONSE_BYTES", 2_097_152),
                },
            ),
            session=cast(
                _Session,
                {
                    "max_age_seconds": positive("MAYAK_SESSION_MAX_AGE_SECONDS", 86_400),
                    "synthetic_identity_enabled": _bool(
                        copied, "MAYAK_SYNTHETIC_IDENTITY_ENABLED", False
                    ),
                    "link_challenge_ttl_seconds": positive(
                        "MAYAK_IDENTITY_LINK_CHALLENGE_TTL_SECONDS", 900
                    ),
                    "admin_bootstrap_enabled": _bool(
                        copied, "MAYAK_IDENTITY_ADMIN_BOOTSTRAP_ENABLED", False
                    ),
                },
            ),
            providers=cast(
                _Providers,
                {
                    "avito_live_enabled": _bool(copied, "MAYAK_AVITO_LIVE_ENABLED", False),
                    "telegram_enabled": _bool(copied, "MAYAK_TELEGRAM_ENABLED", False),
                    "telegram_update_mode": ProviderUpdateMode(
                        _text(copied, "MAYAK_TELEGRAM_UPDATE_MODE", "disabled")
                    ),
                    "max_enabled": _bool(copied, "MAYAK_MAX_ENABLED", False),
                    "max_update_mode": ProviderUpdateMode(
                        _text(copied, "MAYAK_MAX_UPDATE_MODE", "disabled")
                    ),
                    "yookassa_enabled": _bool(copied, "MAYAK_YOOKASSA_ENABLED", False),
                    "yookassa_shop_id": _optional_text(copied, "MAYAK_YOOKASSA_SHOP_ID"),
                    "yookassa_api_base": _text(
                        copied, "MAYAK_YOOKASSA_API_BASE", "https://api.yookassa.ru/v3"
                    ),
                    "yookassa_secret_file": _path(
                        copied, "MAYAK_YOOKASSA_SECRET_FILE", "/run/secrets/mayak_yookassa_secret"
                    ),
                    "egress_agent_enabled": _bool(copied, "MAYAK_EGRESS_AGENT_ENABLED", False),
                },
            ),
            observability=cast(
                _Observability,
                {
                    "log_level": LogLevel(_text(copied, "MAYAK_LOG_LEVEL", "INFO")),
                    "log_format": _text(copied, "MAYAK_LOG_FORMAT", "json"),
                    "otel_enabled": _bool(copied, "MAYAK_OTEL_ENABLED", False),
                    "otel_exporter_endpoint": _optional_disabled(
                        copied, "MAYAK_OTEL_EXPORTER_ENDPOINT"
                    ),
                },
            ),
            retention=cast(
                _Retention, {"backup_retention_days": positive("MAYAK_BACKUP_RETENTION_DAYS", 7)}
            ),
            backup=cast(
                _Backup,
                {"backup_root": _path(copied, "MAYAK_BACKUP_ROOT", "/var/backups/avito-mayak")},
            ),
        )
        if (
            not 1 <= settings.worker.batch_size <= 1000
            or not 1 <= settings.worker.outbox_batch_size <= 1000
        ):
            raise ValueError("batch")
        if not 1 <= settings.http.max_response_bytes <= 10_485_760:
            raise ValueError("MAYAK_HTTP_MAX_RESPONSE_BYTES")
        return settings
    except (ValueError, TypeError, ValidationError) as exc:
        field = (
            str(exc)
            if isinstance(exc, ValueError) and str(exc).startswith("MAYAK_")
            else "configuration"
        )
    raise _error("INVALID_CONFIGURATION", [field])


def load_runtime_settings(
    environ: Mapping[str, str] | None = None,
) -> MayakRuntimeSettings:
    """Snapshot supplied environment, or os.environ once, then compose."""
    snapshot = dict(os.environ if environ is None else environ)
    return compose_runtime_settings(snapshot)


__all__ = [
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

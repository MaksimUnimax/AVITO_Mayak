"""The narrow, secret-file-backed PostgreSQL configuration boundary."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from sqlalchemy.engine import URL

DATABASE_NAME: Final = "mayak"
DATABASE_SCHEMA: Final = "mayak"
DATABASE_HOST: Final = "mayak-postgres"
DATABASE_PORT: Final = 5432
DATABASE_APPLICATION_USER: Final = "mayak_application"
DATABASE_MIGRATION_USER: Final = "mayak_migration"
DATABASE_BOOTSTRAP_USER: Final = "mayak"
APPLICATION_SECRET_PATH: Final = Path("/run/secrets/mayak_database_application_password")
MIGRATION_SECRET_PATH: Final = Path("/run/secrets/mayak_database_migration_password")
BOOTSTRAP_SECRET_PATH: Final = Path("/run/secrets/mayak_postgres_bootstrap_password")
DRIVER_NAME: Final = "postgresql+psycopg"
_IDENTIFIER = re.compile(r"^[a-z_][a-z0-9_]*$", re.ASCII)


def _validate_identifier(value: str, name: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise ValueError(f"{name} must match lowercase SQL identifier grammar")
    return value


class SecretValue:
    """A deliberately non-printable wrapper around a resolved secret."""

    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        self._value = value

    def __repr__(self) -> str:
        return "SecretValue(<redacted>)"

    def __str__(self) -> str:
        return "<redacted>"

    def as_text(self) -> str:
        """Return the value only at the URL-construction boundary."""
        return self._value


@dataclass(frozen=True, slots=True)
class DatabaseEndpoint:
    database: str = DATABASE_NAME
    schema: str = DATABASE_SCHEMA
    host: str = DATABASE_HOST
    port: int = DATABASE_PORT

    def __post_init__(self) -> None:
        _validate_identifier(self.database, "database")
        _validate_identifier(self.schema, "schema")
        if (
            not isinstance(self.port, int)
            or isinstance(self.port, bool)
            or not 1 <= self.port <= 65535
        ):
            raise ValueError("port must be an integer between 1 and 65535")
        if not self.host or any(char.isspace() for char in self.host):
            raise ValueError("host must be non-empty and contain no whitespace")


@dataclass(frozen=True, slots=True)
class ApplicationDatabaseSettings:
    endpoint: DatabaseEndpoint = DatabaseEndpoint()
    user: str = DATABASE_APPLICATION_USER
    secret_path: Path = APPLICATION_SECRET_PATH

    def __post_init__(self) -> None:
        _validate_identifier(self.user, "user")


@dataclass(frozen=True, slots=True)
class MigrationDatabaseSettings:
    endpoint: DatabaseEndpoint = DatabaseEndpoint()
    user: str = DATABASE_MIGRATION_USER
    secret_path: Path = MIGRATION_SECRET_PATH

    def __post_init__(self) -> None:
        _validate_identifier(self.user, "user")


@dataclass(frozen=True, slots=True)
class BootstrapDatabaseSettings:
    endpoint: DatabaseEndpoint = DatabaseEndpoint()
    user: str = DATABASE_BOOTSTRAP_USER
    secret_path: Path = BOOTSTRAP_SECRET_PATH
    connect_timeout: int = 5
    application_name: str = "mayak-rf09-bootstrap"

    def __post_init__(self) -> None:
        _validate_identifier(self.user, "user")
        if (
            not isinstance(self.connect_timeout, int)
            or isinstance(self.connect_timeout, bool)
            or not 1 <= self.connect_timeout <= 60
        ):
            raise ValueError("connect_timeout must be an integer between 1 and 60")
        if not self.application_name or any(char.isspace() for char in self.application_name):
            raise ValueError("application_name must be non-empty and contain no whitespace")


def resolve_secret_file(path: Path) -> SecretValue:
    """Resolve one UTF-8 secret file without ever putting its value in errors."""
    path = Path(path)
    if not path.is_absolute():
        raise ValueError("secret path must be absolute")
    if path.is_symlink():
        raise ValueError(f"secret path rejected: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"secret path is not a regular file: {path}")
    value = path.read_text(encoding="utf-8")
    if value.endswith("\n"):
        value = value[:-1]
        if value.endswith("\r"):
            value = value[:-1]
    if not value or value.strip() == "" or "\n" in value or "\r" in value:
        raise ValueError(f"secret file contains an invalid value: {path}")
    return SecretValue(value)


def build_bootstrap_connect_kwargs(
    settings: BootstrapDatabaseSettings | None = None,
    *,
    endpoint: DatabaseEndpoint | None = None,
    user: str | None = None,
    secret_path: Path | None = None,
    connect_timeout: int = 5,
    application_name: str = "mayak-rf09-bootstrap",
) -> dict[str, object]:
    """Build psycopg.connect keyword arguments at the explicit secret boundary."""
    if settings is None:
        settings = BootstrapDatabaseSettings(
            endpoint=endpoint or DatabaseEndpoint(),
            user=user or DATABASE_BOOTSTRAP_USER,
            secret_path=secret_path or BOOTSTRAP_SECRET_PATH,
            connect_timeout=connect_timeout,
            application_name=application_name,
        )
    secret = resolve_secret_file(settings.secret_path)
    return {
        "host": settings.endpoint.host,
        "port": settings.endpoint.port,
        "dbname": settings.endpoint.database,
        "user": settings.user,
        "password": secret.as_text(),
        "connect_timeout": settings.connect_timeout,
        "application_name": settings.application_name,
    }


def _url(
    settings: ApplicationDatabaseSettings | MigrationDatabaseSettings,
    *,
    search_path: str,
    require_secret: bool = True,
) -> URL:
    password = resolve_secret_file(settings.secret_path).as_text() if require_secret else None
    endpoint = settings.endpoint
    return URL.create(
        DRIVER_NAME,
        username=settings.user,
        password=password,
        host=endpoint.host,
        port=endpoint.port,
        database=endpoint.database,
        query={"options": f"-csearch_path={search_path}"},
    )


def build_application_url(
    settings: ApplicationDatabaseSettings | None = None,
    *,
    secret_path: Path | None = None,
) -> URL:
    settings = settings or ApplicationDatabaseSettings(
        secret_path=secret_path or APPLICATION_SECRET_PATH
    )
    return _url(settings, search_path=settings.endpoint.schema)


def build_migration_url(
    settings: MigrationDatabaseSettings | None = None,
    *,
    secret_path: Path | None = None,
    require_secret: bool = True,
) -> URL:
    settings = settings or MigrationDatabaseSettings(
        secret_path=secret_path or MIGRATION_SECRET_PATH
    )
    schema = settings.endpoint.schema
    search_path = "public" if schema == "public" else f"public,{schema}"
    return _url(settings, search_path=search_path, require_secret=require_secret)

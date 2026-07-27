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
APPLICATION_SECRET_PATH: Final = Path("/run/secrets/mayak_database_application_password")
MIGRATION_SECRET_PATH: Final = Path("/run/secrets/mayak_database_migration_password")
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


def _url(
    settings: ApplicationDatabaseSettings | MigrationDatabaseSettings,
    *,
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
        query={"options": f"-csearch_path={endpoint.schema}"},
    )


def build_application_url(
    settings: ApplicationDatabaseSettings | None = None,
    *,
    secret_path: Path | None = None,
) -> URL:
    settings = settings or ApplicationDatabaseSettings(
        secret_path=secret_path or APPLICATION_SECRET_PATH
    )
    return _url(settings)


def build_migration_url(
    settings: MigrationDatabaseSettings | None = None,
    *,
    secret_path: Path | None = None,
    require_secret: bool = True,
) -> URL:
    settings = settings or MigrationDatabaseSettings(
        secret_path=secret_path or MIGRATION_SECRET_PATH
    )
    return _url(settings, require_secret=require_secret)

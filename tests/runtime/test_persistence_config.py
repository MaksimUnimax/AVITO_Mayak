from pathlib import Path

import pytest
from sqlalchemy.engine import URL

from mayak.persistence.config import (
    APPLICATION_SECRET_PATH,
    DATABASE_APPLICATION_USER,
    DATABASE_HOST,
    DATABASE_MIGRATION_USER,
    DATABASE_NAME,
    DATABASE_PORT,
    DATABASE_SCHEMA,
    MIGRATION_SECRET_PATH,
    ApplicationDatabaseSettings,
    DatabaseEndpoint,
    MigrationDatabaseSettings,
    build_application_url,
    build_migration_url,
    resolve_secret_file,
)


def test_constants_and_separate_roles() -> None:
    assert (DATABASE_NAME, DATABASE_SCHEMA, DATABASE_HOST, DATABASE_PORT) == (
        "mayak", "mayak", "mayak-postgres", 5432
    )
    assert DATABASE_APPLICATION_USER != DATABASE_MIGRATION_USER
    assert APPLICATION_SECRET_PATH.is_absolute()
    assert MIGRATION_SECRET_PATH.is_absolute()


def test_secret_file_rules(tmp_path: Path) -> None:
    secret = tmp_path / "secret"
    secret.write_text("synthetic-value\n", encoding="utf-8")
    resolved = resolve_secret_file(secret)
    assert str(resolved) == "<redacted>"
    assert resolved.as_text() == "synthetic-value"
    with pytest.raises(ValueError, match="absolute"):
        resolve_secret_file(Path("relative-secret"))
    with pytest.raises(FileNotFoundError):
        resolve_secret_file(tmp_path / "missing")
    empty = tmp_path / "empty"
    empty.write_text(" \n", encoding="utf-8")
    with pytest.raises(ValueError):
        resolve_secret_file(empty)
    if hasattr(secret, "symlink_to"):
        link = tmp_path / "link"
        link.symlink_to(secret)
        with pytest.raises(ValueError):
            resolve_secret_file(link)


@pytest.mark.parametrize("value", ["Upper", "white space", "semi;colon", "x' OR '1'='1", ""])
def test_identifier_validation(value: str) -> None:
    with pytest.raises(ValueError):
        DatabaseEndpoint(database=value)


def test_urls_are_driver_correct_and_redacted(tmp_path: Path) -> None:
    app_secret = tmp_path / "app"
    migration_secret = tmp_path / "migration"
    app_secret.write_text("app-only-synthetic\n", encoding="utf-8")
    migration_secret.write_text("migration-only-synthetic\n", encoding="utf-8")
    application = build_application_url(ApplicationDatabaseSettings(secret_path=app_secret))
    migration = build_migration_url(MigrationDatabaseSettings(secret_path=migration_secret))
    assert isinstance(application, URL)
    assert application.drivername == "postgresql+psycopg"
    assert (application.host, application.port, application.database, application.username) == (
        DATABASE_HOST, DATABASE_PORT, DATABASE_NAME, DATABASE_APPLICATION_USER
    )
    assert migration.username == DATABASE_MIGRATION_USER
    assert "synthetic" not in repr(application)
    assert "synthetic" not in str(application)

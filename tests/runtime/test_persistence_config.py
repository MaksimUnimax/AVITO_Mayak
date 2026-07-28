from pathlib import Path

import pytest
from sqlalchemy.engine import URL

from mayak.persistence.config import (
    APPLICATION_SECRET_PATH,
    BOOTSTRAP_SECRET_PATH,
    DATABASE_APPLICATION_USER,
    DATABASE_BOOTSTRAP_USER,
    DATABASE_HOST,
    DATABASE_MIGRATION_USER,
    DATABASE_NAME,
    DATABASE_PORT,
    DATABASE_SCHEMA,
    MIGRATION_SECRET_PATH,
    ApplicationDatabaseSettings,
    BootstrapDatabaseSettings,
    DatabaseEndpoint,
    MigrationDatabaseSettings,
    build_application_url,
    build_bootstrap_connect_kwargs,
    build_migration_url,
    resolve_secret_file,
)


def test_constants_and_separate_roles() -> None:
    assert (DATABASE_NAME, DATABASE_SCHEMA, DATABASE_HOST, DATABASE_PORT) == (
        "mayak",
        "mayak",
        "mayak-postgres",
        5432,
    )
    assert DATABASE_APPLICATION_USER != DATABASE_MIGRATION_USER
    assert APPLICATION_SECRET_PATH.is_absolute()
    assert MIGRATION_SECRET_PATH.is_absolute()
    assert DATABASE_BOOTSTRAP_USER == "mayak"
    assert BOOTSTRAP_SECRET_PATH == Path("/run/secrets/mayak_postgres_bootstrap_password")


def test_bootstrap_settings_and_kwargs_are_safe_and_lazy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "bootstrap"
    path.write_text("synthetic-bootstrap-only\n", encoding="utf-8")
    settings = BootstrapDatabaseSettings(secret_path=path)
    assert settings.user == DATABASE_BOOTSTRAP_USER
    assert "synthetic-bootstrap-only" not in repr(settings)
    monkeypatch.setattr(
        "mayak.persistence.config.resolve_secret_file", lambda _: pytest.fail("eager")
    )
    with pytest.raises(pytest.fail.Exception):
        build_bootstrap_connect_kwargs(settings)


def test_bootstrap_kwargs_exact_keys_and_timeout_validation(tmp_path: Path) -> None:
    path = tmp_path / "bootstrap"
    path.write_text("synthetic-bootstrap-only\n", encoding="utf-8")
    kwargs = build_bootstrap_connect_kwargs(BootstrapDatabaseSettings(secret_path=path))
    assert set(kwargs) == {
        "host",
        "port",
        "dbname",
        "user",
        "password",
        "connect_timeout",
        "application_name",
    }
    assert kwargs["connect_timeout"] == 5
    assert kwargs["application_name"] == "mayak-rf09-bootstrap"
    assert kwargs["password"] == "synthetic-bootstrap-only"
    for timeout in (True, False, 0, -1, 61):
        with pytest.raises(ValueError):
            BootstrapDatabaseSettings(secret_path=path, connect_timeout=timeout)  # type: ignore[arg-type]


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
        DATABASE_HOST,
        DATABASE_PORT,
        DATABASE_NAME,
        DATABASE_APPLICATION_USER,
    )
    assert migration.username == DATABASE_MIGRATION_USER
    assert application.query["options"] == "-csearch_path=mayak"
    assert migration.query["options"] == "-csearch_path=public"
    assert "synthetic" not in repr(application)
    assert "synthetic" not in str(application)

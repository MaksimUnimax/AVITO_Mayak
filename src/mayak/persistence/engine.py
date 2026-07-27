"""Explicit synchronous SQLAlchemy engine construction and disposal."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import URL
from sqlalchemy.pool import NullPool

from mayak.persistence.config import (
    ApplicationDatabaseSettings,
    MigrationDatabaseSettings,
    build_application_url,
    build_migration_url,
)


def create_application_engine(
    url: URL | str | None = None,
    *,
    settings: ApplicationDatabaseSettings | None = None,
    secret_path: Path | None = None,
    pool_size: int = 5,
    max_overflow: int = 10,
    pool_timeout: float = 30.0,
    pool_recycle: int = 1800,
    **overrides: Any,
) -> Engine:
    """Build a finite application pool; construction itself never connects."""
    target = url if url is not None else build_application_url(settings, secret_path=secret_path)
    return create_engine(
        target,
        pool_pre_ping=True,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_recycle=pool_recycle,
        future=True,
        **overrides,
    )


def create_migration_engine(
    url: URL | str | None = None,
    *,
    settings: MigrationDatabaseSettings | None = None,
    secret_path: Path | None = None,
    **overrides: Any,
) -> Engine:
    """Build a one-shot migration engine with no long-lived pool."""
    target = url if url is not None else build_migration_url(settings, secret_path=secret_path)
    return create_engine(target, poolclass=NullPool, future=True, **overrides)


def dispose_engine(engine: Engine) -> None:
    engine.dispose()

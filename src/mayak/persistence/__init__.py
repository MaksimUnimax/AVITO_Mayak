"""Stable persistence primitives for the RF-09 runtime foundation."""

from mayak.persistence.audit import (
    AuditPersistenceError,
    PersistedAuditEntry,
    PostgresAuditRepository,
)
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
    SecretValue,
    build_application_url,
    build_bootstrap_connect_kwargs,
    build_migration_url,
    resolve_secret_file,
)
from mayak.persistence.engine import (
    create_application_engine,
    create_migration_engine,
    dispose_engine,
)
from mayak.persistence.metadata import Base, metadata
from mayak.persistence.session import (
    TransactionBoundaryError,
    caller_owned_transaction,
    create_session_factory,
    session_scope,
)

__all__ = [
    "APPLICATION_SECRET_PATH",
    "AuditPersistenceError",
    "BOOTSTRAP_SECRET_PATH",
    "DATABASE_APPLICATION_USER",
    "DATABASE_BOOTSTRAP_USER",
    "DATABASE_HOST",
    "DATABASE_MIGRATION_USER",
    "DATABASE_NAME",
    "DATABASE_PORT",
    "DATABASE_SCHEMA",
    "MIGRATION_SECRET_PATH",
    "ApplicationDatabaseSettings",
    "BootstrapDatabaseSettings",
    "Base",
    "DatabaseEndpoint",
    "MigrationDatabaseSettings",
    "SecretValue",
    "PersistedAuditEntry",
    "PostgresAuditRepository",
    "build_application_url",
    "build_bootstrap_connect_kwargs",
    "build_migration_url",
    "caller_owned_transaction",
    "create_application_engine",
    "create_migration_engine",
    "create_session_factory",
    "dispose_engine",
    "metadata",
    "resolve_secret_file",
    "session_scope",
    "TransactionBoundaryError",
]

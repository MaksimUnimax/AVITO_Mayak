"""Database-independent Alembic bootstrap for the future linear migration chain."""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from mayak.persistence.config import build_migration_url
from mayak.persistence.engine import create_migration_engine, dispose_engine
from mayak.persistence.metadata import metadata
from mayak.persistence.migration import serialized_migration

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = metadata


class RF26SyntheticMigrationInterrupted(RuntimeError):
    """Deterministic, task-local interruption used only by RF26 acceptance."""


def _rf26_interrupt_hook(
    ctx: object, step: object, heads: object, run_args: dict[str, object]
) -> None:
    # Alembic invokes on_version_apply with all four keyword arguments.
    del ctx, step, heads, run_args
    if (
        os.environ.get("MAYAK_RUNTIME_PROFILE") == "synthetic_acceptance"
        and os.environ.get("MAYAK_TECHNICAL_ID") == "RF26-OBSERVABILITY-BACKUP-RECOVERY-01"
        and os.environ.get("RF26_SYNTHETIC_MIGRATION_INTERRUPT") == "1"
        and os.environ.get("RF26_TASK_OWNED_DATABASE") == "1"
        and os.environ.get("RF26_MIGRATION_INTERRUPT_BOUNDARY") == "after_first_revision"
    ):
        raise RF26SyntheticMigrationInterrupted(
            "RF26 deterministic interruption after_first_revision"
        )


def _configure_kwargs() -> dict[str, object]:
    return {
        "target_metadata": target_metadata,
        "include_schemas": True,
        "version_table": "alembic_version",
        "version_table_schema": "mayak",
        "compare_type": True,
        "compare_server_default": True,
        "transaction_per_migration": True,
        "on_version_apply": _rf26_interrupt_hook,
    }


def run_migrations_offline() -> None:
    url = build_migration_url(require_secret=False)
    context.configure(
        url=url,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        **_configure_kwargs(),
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    injected = config.attributes.get("connection")
    if injected is not None:
        with serialized_migration(injected):
            context.configure(connection=injected, **_configure_kwargs())
            with context.begin_transaction():
                context.run_migrations()
        return
    engine = create_migration_engine()
    try:
        with engine.connect() as connection:
            with serialized_migration(connection):
                context.configure(connection=connection, **_configure_kwargs())
                with context.begin_transaction():
                    context.run_migrations()
    finally:
        dispose_engine(engine)


def run_migrations() -> None:
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()


# Alembic supplies cmd_opts for an actual command invocation.  Keeping direct
# module imports inert makes inspection and static tooling database-independent.
if getattr(config, "cmd_opts", None) is not None:
    run_migrations()

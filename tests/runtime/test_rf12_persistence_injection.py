"""Focused tests for the RF-12 acceptance migration boundary."""

# ruff: noqa: E501

from __future__ import annotations

import ast
from pathlib import Path

from sqlalchemy.engine import URL

from mayak.persistence.config import redacted_database_url


def test_production_migration_config_has_no_rf12_environment_override() -> None:
    source = Path("src/mayak/persistence/config.py").read_text(encoding="utf-8")
    assert "RF12_ACCEPTANCE_DSN" not in source
    assert "import os" not in source
    assert "build_migration_url" in source


def test_alembic_online_path_accepts_explicit_connection_and_keeps_default_path() -> None:
    source = Path("alembic/env.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert 'config.attributes.get("connection")' in source
    assert "context.configure(connection=injected" in source
    assert "create_migration_engine()" in source
    assert any(isinstance(node, ast.FunctionDef) and node.name == "run_migrations_online" for node in ast.walk(tree))


def test_producer_uses_alembic_connection_injection() -> None:
    source = Path("scripts/runtime/run_rf12_postgres_acceptance.py").read_text(encoding="utf-8")
    assert 'cfg.attributes["connection"] = connection' in source
    assert "command.upgrade(cfg, revision)" in source
    assert "rf12-postgres-acceptance-v2" in source


def test_redacted_database_url_string_runtime_regression() -> None:
    rendered = redacted_database_url("postgresql+psycopg://user:secret@example.test/db")
    assert "secret" not in rendered
    assert "user:" in rendered
    assert "secret" not in redacted_database_url(URL.create("postgresql+psycopg", username="user", password="secret", host="example.test", database="db"))

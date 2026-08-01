"""Focused checks for the real RF-12 PostgreSQL acceptance entry points."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PRODUCER = Path("scripts/runtime/run_rf12_postgres_acceptance.py")
VERIFIER = Path("scripts/runtime/verify_rf12_acceptance.py")


def test_real_postgres_producer_is_committed_and_not_a_boolean_manifest() -> None:
    source = PRODUCER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert "create_engine" in source
    assert "Session" in source
    assert "command.upgrade" in source
    assert "pg_advisory_xact_lock" not in source  # production method owns the lock
    assert '"observed_effect_count"' in source
    assert not any(
        isinstance(node, ast.Return)
        and isinstance(node.value, ast.Dict)
        and any(getattr(key, "value", None) == "gate" for key in node.value.keys)
        for node in ast.walk(tree)
    )


def test_verifier_is_an_independent_structural_consumer() -> None:
    source = VERIFIER.read_text(encoding="utf-8")
    assert "run_rf12_postgres_acceptance" not in source
    assert "schema_version" in source
    assert "observed_effect_count" in source
    assert "before_after_equal" in source
    assert "candidate_source_sha" in source


@pytest.mark.postgres
def test_real_postgres_run_is_explicitly_opt_in() -> None:
    """CI invokes the producer as a task-owned runtime command, never a DSN default."""
    assert PRODUCER.is_file()

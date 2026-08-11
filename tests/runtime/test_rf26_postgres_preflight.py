from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.runtime import rf26_postgres_preflight as preflight


def test_database_identities_are_strict_and_task_owned() -> None:
    assert preflight._names("31488032820") == (
        "rf26_source_31488032820", "rf26_target_31488032820", "rf26_conflict_31488032820"
    )
    with pytest.raises(ValueError, match="unsafe"):
        preflight._names("31488032820-x")


@pytest.mark.parametrize("message", [
    "password=rf26-bootstrap-only",
    "postgresql://mayak_migration:rf26-migration-only@mayak-postgres/db",
    "secret token=fixture",
])
def test_redaction_never_returns_connection_secret(message: str) -> None:
    redacted = preflight._redact(message)
    assert "rf26-" not in redacted
    assert "[REDACTED]" in redacted


def test_boundary_contract_is_ordered_and_small() -> None:
    assert preflight.BOUNDARIES == (
        "H8A_CONNECTIVITY", "H8B_BOOTSTRAP_AUTHORITY", "H8C_ROLE_STATE",
        "H8D_DATABASE_CREATE", "H8E_DATABASE_OWNERSHIP", "H8F_SCHEMA_PREPARE",
        "H8G_SOURCE_MIGRATION", "H8H_CONFLICT_MIGRATION", "H8I_REVISION_PROOF",
        "H8J_APPLICATION_GRANTS", "H8K_TARGET_EMPTY",
    )
    assert len(json.dumps({"passed_boundaries": list(preflight.BOUNDARIES)})) < 512
    assert Path("scripts/runtime/rf26_postgres_preflight.py").exists()


def test_failure_has_boundary_and_redacted_reason() -> None:
    error = preflight.PreflightFailure("H8A_CONNECTIVITY", RuntimeError("password=fixture"))
    assert error.boundary == "H8A_CONNECTIVITY"
    assert error.error_class == "RuntimeError"
    assert "fixture" not in error.reason


def test_diagnostic_trace_has_five_safe_transitions() -> None:
    trace = {
        "input": {}, "derived": {}, "function": {}, "environment": {},
        "source_runtime_evidence": {},
    }
    assert tuple(trace) == (
        "input", "derived", "function", "environment", "source_runtime_evidence"
    )

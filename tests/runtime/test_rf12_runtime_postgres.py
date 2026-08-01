"""Real-PostgreSQL RF-12 acceptance entry point.

The harness is intentionally fail-closed: a DSN is supplied only by the
task-owned RF-08 acceptance environment, never by a repository default.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest


@pytest.mark.postgres
def test_rf12_postgres_acceptance_environment_is_explicit() -> None:
    dsn = os.environ.get("RF12_ACCEPTANCE_DSN")
    if not dsn:
        pytest.fail("RF12_ACCEPTANCE_DSN is required; self-provision the task-owned PostgreSQL 18 environment")
    assert "localhost" not in dsn and "127.0.0.1" not in dsn


def test_rf12_acceptance_artifact_path_is_task_owned() -> None:
    path = Path(os.environ.get("RF12_ACCEPTANCE_ARTIFACT", "/opt/avito-mayak-runtime"))
    assert str(path).startswith("/opt/avito-mayak-runtime/") or str(path) == "/opt/avito-mayak-runtime"

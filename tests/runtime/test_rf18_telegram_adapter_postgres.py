from __future__ import annotations

# ruff: noqa: E501, I001

import os

import pytest


pytestmark = pytest.mark.skipif(not os.getenv("RF18_DATABASE_URL"), reason="RF18_DATABASE_URL not provided")


def test_rf18_postgres_gate_requires_explicit_task_database() -> None:
    assert os.getenv("RF18_DATABASE_URL", "").startswith("postgresql")

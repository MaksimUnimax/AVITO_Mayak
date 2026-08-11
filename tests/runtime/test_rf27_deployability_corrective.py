from __future__ import annotations

from pathlib import Path

import pytest

from scripts.runtime.rf08_docker_context import (
    COPY_PLAN,
    dockerfile_copy_contract,
    validate_copy_contract,
    validate_copy_root,
)
from mayak.runtime.settings import compose_runtime_settings


ROOT = Path(__file__).parents[2]


def test_dockerfile_copy_contract_is_complete_and_single_source() -> None:
    assert validate_copy_contract(ROOT / "Dockerfile") == COPY_PLAN
    assert ("src", "src") in COPY_PLAN
    assert (
        "scripts/runtime/rf26_operability.py",
        "scripts/runtime/rf26_operability.py",
    ) in COPY_PLAN


def test_security_term_source_is_not_ignored() -> None:
    ignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")
    assert "**/*secret*" not in ignore
    assert "**/*token*" not in ignore
    assert "**/*password*" not in ignore
    assert "**/*credential*" not in ignore
    assert (ROOT / "src/mayak/modules/egress_routing/session_secret_gate.py").is_file()


def test_copy_root_rejects_untracked_extra_and_unsafe_input(tmp_path: Path) -> None:
    root = tmp_path / "src"
    root.mkdir()
    (root / "legitimate_session_secret_gate.py").write_text("SAFE = True\n", encoding="utf-8")
    (root / "unexpected.py").write_text("UNTRACKED = True\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected untracked"):
        validate_copy_root(
            root,
            {"legitimate_session_secret_gate.py"},
            tracked_files={"legitimate_session_secret_gate.py"},
        )
    (root / "unexpected.py").unlink()
    (root / ".env").write_text("synthetic_only=1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="classified secret"):
        validate_copy_root(root, {".env"})


def test_compose_environment_is_complete_and_nondefault_port_is_truthful() -> None:
    compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
    for key in (
        "MAYAK_ENVIRONMENT_ID",
        "MAYAK_RUNTIME_PROFILE",
        "MAYAK_SOURCE_SHA",
        "MAYAK_LOCK_IDENTITY",
        "MAYAK_IMAGE_DIGEST",
        "MAYAK_PROCESS_KIND",
        "MAYAK_DATABASE_APPLICATION_USER",
        "MAYAK_DATABASE_MIGRATION_USER",
    ):
        assert key in compose
    assert 'MAYAK_API_HOST_PORT: "${MAYAK_API_HOST_PORT:-18085}"' in compose
    values = {
        "MAYAK_ENVIRONMENT_ID": "rf27-test",
        "MAYAK_RUNTIME_PROFILE": "synthetic_acceptance",
        "MAYAK_SOURCE_SHA": "6ba49dc6bf039e25d7f36f5f89176e0b94d521e7",
        "MAYAK_LOCK_IDENTITY": "e1faff1ce0f4d5dfd35480ab59d5d599fddf05c38fcd16a26c52098511476ab6",
        "MAYAK_IMAGE_DIGEST": "sha256:" + "a" * 64,
        "MAYAK_PROCESS_KIND": "mayak-api",
        "MAYAK_DATABASE_APPLICATION_USER": "mayak_application",
        "MAYAK_DATABASE_MIGRATION_USER": "mayak_migration",
        "MAYAK_API_BIND_HOST": "0.0.0.0",
        "MAYAK_API_HOST_PORT": "18086",
    }
    settings = compose_runtime_settings(values)
    assert settings.database.name == "mayak"
    assert settings.database.application_user != settings.database.migration_user
    assert settings.api.host_port == 18086

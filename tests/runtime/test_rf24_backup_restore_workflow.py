import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
WORKFLOW = ROOT / ".github/workflows/ci-rf24-backup-restore.yml"

RF24_MODULES = (
    "run_rf24_vertical_spine",
    "run_rf24_backup_restore",
    "verify_rf24_backup_restore",
    "check_rf24_backup_restore_artifact_safety",
    "build_rf24_backup_restore_manifest",
    "check_rf24_backup_restore_workflow",
    "check_rf24_backup_restore_ownership",
)


def test_workflow_is_exact_candidate_and_pg18_safe() -> None:
    text = WORKFLOW.read_text()
    for marker in (
        "postgres:18-bookworm",
        "github.sha",
        "uv sync --frozen",
        "pg_dump",
        "pg_restore",
        "pytest -q",
        "upload-artifact",
        "RF25",
    ):
        assert marker in text
    assert "*.dump" not in text
    assert "postgresql" not in text.split("upload-artifact", 1)[-1]
    assert "mayak-postgres:" in text
    assert "MAYAK_DATABASE_HOST: mayak-postgres" in text
    assert "@postgres:" not in text
    assert "host=postgres" not in text


def test_workflow_validator_accepts_canonical_service_identity() -> None:
    from scripts.runtime.check_rf24_backup_restore_workflow import validate

    validate(WORKFLOW)


def test_workflow_archive_transport_attaches_docker_stdin() -> None:
    text = WORKFLOW.read_text()
    binding = next(line for line in text.splitlines() if "RF24_PG_TOOL_PREFIX=docker exec" in line)
    assert " -i " in binding


def test_workflow_validator_rejects_detached_archive_transport(tmp_path: Path) -> None:
    from scripts.runtime.check_rf24_backup_restore_workflow import validate

    text = WORKFLOW.read_text().replace("docker exec -i -u postgres", "docker exec -u postgres")
    broken = tmp_path / "workflow.yml"
    broken.write_text(text)
    import pytest
    with pytest.raises(ValueError, match="stdin-attached"):
        validate(broken)


@pytest.mark.parametrize(
    ("needle", "replacement", "message"),
    (
        (
            "docker info",
            "test \"$(docker version --format '{{.Server.Version}}')\" = '29.2.1'",
            "server/client equality",
        ),
        (
            "echo h26-docker-api=PASS",
            "test -d /opt/avito-mayak-runtime\necho h26-docker-api=PASS",
            "server runtime path",
        ),
        (
            "printf '%s' 'migration-only'",
            "printf '%s' 'host:port:db:user:password'",
            "raw password",
        ),
        (
            "export GIT_CONFIG_COUNT=1",
            "export GIT_CONFIG_GLOBAL=/dev/null\n          export GIT_CONFIG_COUNT=1",
            "GIT_CONFIG_GLOBAL",
        ),
        ("--output \"type=local", "--output \"type=cache", "local-export"),
    ),
)
def test_workflow_validator_rejects_known_h26_regressions(
    tmp_path: Path, needle: str, replacement: str, message: str
) -> None:
    from scripts.runtime.check_rf24_backup_restore_workflow import validate

    broken = tmp_path / "workflow.yml"
    broken.write_text(WORKFLOW.read_text().replace(needle, replacement, 1))
    with pytest.raises(ValueError, match=message):
        validate(broken)


def test_workflow_uses_one_module_execution_contract() -> None:
    text = WORKFLOW.read_text()
    for module in RF24_MODULES:
        assert f"uv run python -m scripts.runtime.{module}" in text
        assert f"uv run python scripts/runtime/{module}.py" not in text


def test_rf24_entrypoints_start_under_exact_workflow_invocation() -> None:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    for module in RF24_MODULES:
        result = subprocess.run(
            ["uv", "run", "python", "-m", f"scripts.runtime.{module}", "--help"],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, (module, result.stdout, result.stderr)
        assert "password" not in (result.stdout + result.stderr).lower()


def test_module_contract_does_not_mutate_sys_path_or_require_pythonpath() -> None:
    for path in (ROOT / "scripts/runtime").glob("*rf24_backup_restore*.py"):
        text = path.read_text()
        assert "sys.path" not in text
        assert "PYTHONPATH" not in text
    assert "PYTHONPATH" not in (ROOT / "scripts/runtime/run_rf24_vertical_spine.py").read_text()


def test_acceptance_scripts_have_no_business_table_dml() -> None:
    for path in (ROOT / "scripts/runtime").glob("*rf24_backup_restore*.py"):
        if path.name == "check_rf24_backup_restore_ownership.py":
            continue
        text = path.read_text()
        assert "INSERT INTO mayak." not in text
        assert "UPDATE mayak." not in text
        assert "DELETE FROM mayak." not in text

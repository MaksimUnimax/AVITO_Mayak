# ruff: noqa: E501, I001
import subprocess
from pathlib import Path

import pytest

from scripts.runtime.check_rf26_workflow_contract import validate


WORKFLOW = Path(__file__).parents[2] / ".github/workflows/ci-rf26-operability.yml"


def test_rf26_complete_substrate_contract_passes() -> None:
    validate(WORKFLOW)


def test_compose_plugin_is_separately_pinned_and_interface_validated() -> None:
    text = WORKFLOW.read_text()
    assert "docker-compose-linux-x86_64" in text
    assert "2d880f723d3da7c779c54fdaea91a842fca8af55d1397f1ed8d7cbab3dd7af67" in text
    assert "compose_plugin_dir=\"$docker_config/cli-plugins\"" in text
    assert "docker compose version --short" not in text
    assert "Docker Compose version v5.0.2" in text


def test_known_c358_workflow_is_rejected() -> None:
    old = subprocess.check_output(
        ["git", "show", "c358ff9ab9e3d515e4381018121bee45d0d33659:.github/workflows/ci-rf26-operability.yml"],
        text=True,
    )
    path = WORKFLOW.with_name(".rf26-c358-workflow-fixture.yml")
    try:
        path.write_text(old, encoding="utf-8")
        with pytest.raises(ValueError):
            validate(path)
    finally:
        path.unlink(missing_ok=True)


@pytest.mark.parametrize(
    ("needle", "replacement"),
    [
        ("python:3.14.6-bookworm@sha256:", "python:3.14.6-bookworm"),
        ("postgres:18-bookworm@sha256:", "postgres:18-bookworm"),
        ("actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1", "actions/checkout@v4"),
        ("docker image inspect", "docker inspect"),
        ("docker-29.2.1.tgz", "docker.tgz"),
    ],
)
def test_rf26_contract_rejects_known_substrate_regression(tmp_path: Path, needle: str, replacement: str) -> None:
    broken = tmp_path / "workflow.yml"
    broken.write_text(WORKFLOW.read_text().replace(needle, replacement), encoding="utf-8")
    with pytest.raises(ValueError):
        validate(broken)

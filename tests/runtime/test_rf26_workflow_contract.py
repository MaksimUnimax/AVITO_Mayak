# ruff: noqa: E501, I001
import json
import subprocess
from pathlib import Path

import pytest

from scripts.runtime.check_rf26_workflow_contract import validate
from scripts.runtime.rf26_docker_discovery import DiscoveryError, prove_match


WORKFLOW = Path(__file__).parents[2] / ".github/workflows/ci-rf26-operability.yml"


def test_rf26_complete_substrate_contract_passes() -> None:
    validate(WORKFLOW)


def test_rf26_target_is_not_prepopulated_before_restore() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    boundary = text.split("H8 task-owned PostgreSQL databases", 1)[1].split("H8 actual rebuild-from-zero stage", 1)[0]
    assert 'for db in "$source_db" "$conflict_db"' in boundary
    assert "target must remain schema-empty before restore" in boundary
    assert "target emptiness proof" in boundary


def _inspect(**overrides: object) -> str:
    value = {
        "Image": "sha256:container",
        "Config": {"Image": "postgres:18-bookworm@sha256:882236b897e39051d2368c5ccc6cda944904723506b2dfc97f2a8f5bc9afa382"},
        "State": {"Health": {"Status": "healthy"}},
        "NetworkSettings": {"Networks": {"bridge": {"Aliases": ["mayak-postgres"]}}},
    }
    value.update(overrides)
    return json.dumps([value])


REPO_DIGESTS = json.dumps(["postgres@sha256:882236b897e39051d2368c5ccc6cda944904723506b2dfc97f2a8f5bc9afa382"])


def test_rf26_h1f_stdlib_parser_accepts_one_exact_match() -> None:
    assert prove_match(_inspect(), REPO_DIGESTS) == "sha256:container"


@pytest.mark.parametrize(
    "payload",
    [
        "[]",
        json.dumps([{}, {}]),
        "not-json",
    ],
)
def test_rf26_h1f_parser_rejects_zero_multiple_or_malformed_inspect(payload: str) -> None:
    with pytest.raises(DiscoveryError):
        prove_match(payload, REPO_DIGESTS)


@pytest.mark.parametrize(
    "change",
    [
        {"Config": {"Image": "postgres:wrong"}},
        {"State": {"Health": {"Status": "unhealthy"}}},
        {"NetworkSettings": {"Networks": {"bridge": {"Aliases": []}}}},
    ],
)
def test_rf26_h1f_parser_rejects_identity_health_and_alias_failures(change: dict[str, object]) -> None:
    with pytest.raises(DiscoveryError):
        prove_match(_inspect(**change), REPO_DIGESTS)


def test_rf26_h1f_parser_rejects_wrong_or_malformed_digest() -> None:
    with pytest.raises(DiscoveryError):
        prove_match(_inspect(), json.dumps(["postgres@sha256:wrong"]))
    with pytest.raises(DiscoveryError):
        prove_match(_inspect(), "{}")


def test_rf26_h1f_has_no_jq_dependency() -> None:
    h1f = WORKFLOW.read_text().split("H1f deterministic service discovery and identity", 1)[1].split("H2 Python", 1)[0]
    assert "jq" not in h1f


def test_rf26_h1f_rejects_compose_label_service_discovery() -> None:
    broken = WORKFLOW.with_name(".rf26-compose-label-fixture.yml")
    broken.write_text(WORKFLOW.read_text().replace('ps --format', 'ps --filter label=com.docker.compose.service=mayak-postgres --format'), encoding="utf-8")
    try:
        with pytest.raises(ValueError, match="Compose labels"):
            validate(broken)
    finally:
        broken.unlink(missing_ok=True)


def test_compose_plugin_is_separately_pinned_and_interface_validated() -> None:
    text = WORKFLOW.read_text()
    assert "docker-compose-linux-x86_64" in text
    assert "2d880f723d3da7c779c54fdaea91a842fca8af55d1397f1ed8d7cbab3dd7af67" in text
    assert "compose_plugin_dir=\"$docker_config/cli-plugins\"" in text
    assert "docker compose version --short" not in text
    assert "Docker Compose version v5.0.2" in text


def test_rf26_docker_client_contract_covers_all_downstream_consumers() -> None:
    text = WORKFLOW.read_text()
    assert 'DOCKER_CONFIG=%s\\nRF26_DOCKER_BIN=%s' in text
    assert '"$RF26_DOCKER_BIN" compose config' in text
    assert '"$RF26_DOCKER_BIN" exec' in text
    assert 'RF24_PG_TOOL_PREFIX=%s exec' in text


@pytest.mark.parametrize(
    ("needle", "replacement"),
    [
        ('"$RF26_DOCKER_BIN" compose config', "docker compose config"),
        ('"$RF26_DOCKER_BIN" exec', "docker exec"),
    ],
)
def test_rf26_contract_rejects_downstream_ambient_docker_regression(
    tmp_path: Path, needle: str, replacement: str
) -> None:
    broken = WORKFLOW.with_name(f".rf26-ambient-{len(list(tmp_path.iterdir()))}.yml")
    broken.write_text(WORKFLOW.read_text().replace(needle, replacement, 1), encoding="utf-8")
    try:
        with pytest.raises(ValueError, match="ambient bare client"):
            validate(broken)
    finally:
        broken.unlink(missing_ok=True)


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

"""Fail-closed static contract for the complete RF26 H0/H1 substrate."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

PYTHON_DIGEST = "sha256:ec1b01f92099324b965a51c8547d9a3b71fedc99f6991a89662e7358f9b167c9"
POSTGRES_DIGEST = "sha256:882236b897e39051d2368c5ccc6cda944904723506b2dfc97f2a8f5bc9afa382"
STAGES = ("H8", "H9", "H10", "H11", "H12", "H13", "H14", "H15", "H16")


def validate(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    runner = path.parents[2] / "scripts/runtime/run_rf26_operability_acceptance.py"
    runner_text = runner.read_text(encoding="utf-8") if runner.exists() else ""
    required = (
        f"python:3.14.6-bookworm@{PYTHON_DIGEST}",
        f"postgres:18-bookworm@{POSTGRES_DIGEST}",
        "actions/checkout@", "astral-sh/setup-uv@", "actions/upload-artifact@",
        "GIT_CONFIG_COUNT=1", "GIT_CONFIG_KEY_0=safe.directory",
        "GIT_CONFIG_VALUE_0=%s\\n' \"$workspace\"", "$GITHUB_ENV",
        "git rev-parse --show-toplevel", "git rev-parse HEAD", "git merge-base",
        "docker image inspect", "NetworkSettings.Networks", "mayak-postgres",
        "python -m scripts.runtime.rf26_docker_discovery", "Config.Image",
        "docker-29.2.1.tgz", "995b1d0b51e96d551a3b49c552c0170bc6ce9f8b9e0866b8c15bbc67d1cf93a3",
        "docker-compose-linux-x86_64", "v5.0.2",
        "2d880f723d3da7c779c54fdaea91a842fca8af55d1397f1ed8d7cbab3dd7af67",
        "DOCKER_CONFIG", '"$docker_cli_dir/docker" compose version',
        "test \"$(\"$docker_cli_dir/docker\" compose version)\" = 'Docker Compose version v5.0.2'",
        "H0c", "H0d", "H0e", "H1a", "H1b", "H1c", "H1d", "H1e", "H1f",
    )
    for marker in required:
        if marker not in text:
            raise ValueError(f"RF26 substrate marker missing: {marker}")
    for action in ("actions/checkout", "astral-sh/setup-uv", "actions/upload-artifact"):
        if not re.search(rf"{re.escape(action)}@[0-9a-f]{{40}}", text):
            raise ValueError(f"{action} is not pinned to a full SHA")
    if re.search(r"(?:python|postgres):[\w.\-]+\s*(?:\n|$)", text):
        raise ValueError("mutable job/service image authority")
    if "docker compose version --short" in text:
        raise ValueError("unsupported Compose version interface")
    if "_real_process_pair" in runner_text or '"-c"' in runner_text:
        raise ValueError("generic process surrogate is present in mandatory RF26 runner")
    if "mayak.runtime.api" not in runner_text or "mayak.runtime.scheduler" not in runner_text:
        raise ValueError("owning runtime entrypoint provenance is missing")
    h1e = text.index("H1e deterministic Docker and Compose client identity")
    h19 = text.index("H19 full repository pytest exactly once")
    docker_contract = text[h1e:h19]
    if 'DOCKER_CONFIG=%s\\nRF26_DOCKER_BIN=%s' not in docker_contract:
        raise ValueError("RF26 Docker client identity is not persisted")
    if re.search(r"(?m)^\s*docker(?:\s|$)", docker_contract) or "=docker exec" in docker_contract:
        raise ValueError("RF26 hosted Docker consumers use an ambient bare client")
    for marker in (
        'test -x "$RF26_DOCKER_BIN"',
        '"$RF26_DOCKER_BIN" compose config',
        '"$RF26_DOCKER_BIN" exec',
        '"$docker_cli_dir/docker" version',
        '"$docker_cli_dir/docker" compose version',
    ):
        if marker not in docker_contract:
            raise ValueError(f"RF26 deterministic Docker contract missing: {marker}")
    if (
        "compose_plugin_dir=\"$docker_config/cli-plugins\"" not in text
        or "$compose_plugin_dir/docker-compose" not in text
    ):
        raise ValueError("Compose plugin location is not explicit")
    if "sha256sum -c" not in text or "chmod 0755" not in text:
        raise ValueError("immutable Compose installation is incomplete")
    if (
        "apt-get install -y --no-install-recommends git docker.io" in text
        or "apt-get install docker.io" in text
        or re.search(r"apt-get install[^\n]*docker-compose", text)
    ):
        raise ValueError("apt-installed docker.io is forbidden")
    if re.search(r"upload-artifact[\s\S]{0,500}backup\.dump", text):
        raise ValueError("raw backup upload is forbidden")
    if re.search(r"safe\.directory\s*[:=]\s*['\"]?\*", text) or "git config --global" in text:
        raise ValueError("global or wildcard Git trust")
    checkout = text.index("actions/checkout")
    trust = text.index("H0b establish persistent cross-step Git trust")
    candidate = text.index("H0d candidate SHA identity")
    ancestor = text.index("H0e authoritative base identity")
    if not checkout < trust < candidate < ancestor:
        raise ValueError("H0 trust/identity ordering is invalid")
    h0 = text.index("H0e authoritative base identity")
    h2 = text.index("H2 Python 3.14")
    if h0 > h2:
        raise ValueError("H0/H1 must precede H2")
    for stage in STAGES:
        if stage not in text:
            raise ValueError(f"mandatory stage missing: {stage}")
        if not re.search(rf"--stage\s+{re.escape(stage)}", text):
            raise ValueError(f"stage does not have a separate workflow executor: {stage}")
    if "H19 full repository pytest exactly once" not in text:
        raise ValueError("H19 is missing")
    if text.index("H19 full repository pytest exactly once") < text.index(
        "H18 exact artifact pre-scan"
    ):
        raise ValueError("H19 precedes H18")
    if "--aggregate" in text and text.index("--aggregate") < text.index(
        "H18 aggregate actual stage receipts"
    ):
        raise ValueError("aggregate is not after mandatory stages")
    h8 = text.index("H8")
    h16 = text.index("H16")
    h17 = text.index("H17")
    if not h8 < h16 < h17:
        raise ValueError("stage order is not monotonic")
    if "continue-on-error" in text:
        raise ValueError("mandatory RF26 steps may not continue on error")
    if "ancestor=postgres:18-bookworm" in text:
        raise ValueError("mutable ancestor filter is forbidden")
    if "head -n1" in text:
        raise ValueError("arbitrary first-container discovery is forbidden")
    h1f = text.index("H1f deterministic service discovery and identity")
    h2 = text.index("H2 Python 3.14")
    discovery = text[h1f:h2]
    if "com.docker.compose.service" in discovery or "label=" in discovery:
        raise ValueError("GitHub Actions service discovery may not use Compose labels")
    for marker in ("ps --format", "RepoDigests", "healthy", POSTGRES_DIGEST,
                   "mayak-postgres", "matching", "RF26_POSTGRES_CONTAINER"):
        if marker not in discovery:
            raise ValueError(f"H1f topology proof missing: {marker}")
    if "RF26_DOCKER_BIN" not in discovery:
        raise ValueError("H1f must use task-local pinned Docker client")
    if "jq" in discovery:
        raise ValueError("H1f has undeclared jq dependency")
    if "rf26_docker_discovery" not in discovery:
        raise ValueError("H1f must use the Python stdlib discovery parser")
    h14 = runner_text[runner_text.index("def _h14"):runner_text.index("def _h15")]
    if any(marker in h14 for marker in ("time.sleep", ".05", "terminate()", "kill()")):
        raise ValueError("H14 timing-race interruption is forbidden")
    for marker in (
        "RF26_SYNTHETIC_MIGRATION_INTERRUPT", "RF26_MIGRATION_INTERRUPT_BOUNDARY",
        "alembic_version", "recovered_revision",
    ):
        if marker not in h14:
            raise ValueError(f"H14 deterministic contract missing: {marker}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("workflow", type=Path)
    validate(parser.parse_args().workflow)

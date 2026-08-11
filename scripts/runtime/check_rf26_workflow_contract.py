"""Fail-closed static contract for the complete RF26 H0/H1 substrate."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

PYTHON_DIGEST = "sha256:ec1b01f92099324b965a51c8547d9a3b71fedc99f6991a89662e7358f9b167c9"
POSTGRES_DIGEST = "sha256:882236b897e39051d2368c5ccc6cda944904723506b2dfc97f2a8f5bc9afa382"
BUILDX_VERSION = "v0.34.1"
BUILDX_SHA256 = "f1332ddb9010bd0b72628266c3a906d9a6979848033df4c8d9bd2cd113bae12b"
STAGES = ("H8", "H9", "H10", "H11", "H12", "H13", "H14", "H15", "H16")
H19_REQUIRED_ENV = (
    "MAYAK_RF10_POSTGRES_DSN", "MAYAK_RF11_POSTGRES_PASSWORD_FILE",
    "MAYAK_RF11_POSTGRES_USER", "MAYAK_RF11_POSTGRES_HOST",
    "MAYAK_RF11_POSTGRES_PORT", "MAYAK_RF11_POSTGRES_DB",
)
H19_REMOVED_ENV = (
    "MAYAK_SECRETS_DIR", "RF26_SOURCE_DB", "RF26_TARGET_DB", "RF26_CONFLICT_DB",
    "RF26_SOURCE_DSN", "RF26_TARGET_DSN", "RF26_CONFLICT_DSN", "RF24_PG_TOOL_PREFIX",
)


def validate(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    runner = path.parents[2] / "scripts/runtime/run_rf26_operability_acceptance.py"
    runner_text = runner.read_text(encoding="utf-8") if runner.exists() else ""
    preflight = path.parents[2] / "scripts/runtime/rf26_postgres_preflight.py"
    preflight_text = preflight.read_text(encoding="utf-8") if preflight.exists() else ""
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
        "docker-compose-linux-x86_64", "v5.0.2", "buildx-v0.34.1.linux-amd64",
        BUILDX_VERSION, BUILDX_SHA256, "RF26_BUILDX_PLUGIN", "--buildx-plugin",
        "2d880f723d3da7c779c54fdaea91a842fca8af55d1397f1ed8d7cbab3dd7af67",
        "DOCKER_CONFIG", '"$docker_cli_dir/docker" compose version',
        'printf \'%s\\n\' "$docker_cli_dir" >> "$GITHUB_PATH"',
        "test \"$(\"$docker_cli_dir/docker\" compose version)\" = 'Docker Compose version v5.0.2'",
        "H0c", "H0d", "H0e", "H1a", "H1b", "H1c", "H1d", "H1e", "H1f",
        "scripts.runtime.rf26_postgres_preflight",
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
    h1e = text.index("H1e deterministic Docker, Compose and Buildx client identity")
    h19 = text.index("H19 full repository pytest exactly once")
    docker_contract = text[h1e:h19]
    if 'DOCKER_CONFIG=%s\\nRF26_DOCKER_BIN=%s' not in docker_contract:
        raise ValueError("RF26 Docker client identity is not persisted")
    if 'printf \'%s\\n\' "$docker_cli_dir" >> "$GITHUB_PATH"' not in docker_contract:
        raise ValueError("RF26 Docker client path is not persisted through GITHUB_PATH")
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
    if f"{BUILDX_SHA256}  docker-buildx" not in text:
        raise ValueError("immutable Buildx installation is incomplete")
    if BUILDX_VERSION not in docker_contract or "buildx version" not in docker_contract:
        raise ValueError("exact Buildx version proof is missing")
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
    h17_start = text.index("H17 security and redaction scan")
    h18_start = text.index("H18 aggregate actual stage receipts")
    h17_block = text[h17_start:h18_start]
    if (
        "check_rf24_backup_restore_artifact_safety" not in h17_block
        or "--root rf26-receipts" not in h17_block
        or "--result rf26-receipts/rf26-H17-scan.json" not in h17_block
    ):
        raise ValueError("H17 must use the project-owned fail-closed scanner")
    if re.search(r"(^|\s)!\s*rg\b|\brg\s", h17_block):
        raise ValueError("H17 may not use fail-open or undeclared rg authority")
    if "H19 full repository pytest exactly once" not in text:
        raise ValueError("H19 is missing")
    if "H18b H19 prerequisite provisioning and execution contract" not in text:
        raise ValueError("H19 preflight gate is missing")
    preflight_start = text.index("H18b H19 prerequisite provisioning and execution contract")
    h19_start = text.index("H19 full repository pytest exactly once")
    h20_start = text.index("H20-H22 verifier and final safe manifest")
    h19_block = text[h19_start:h20_start]
    if not text.index("H18 exact artifact pre-scan") < preflight_start < h19_start:
        raise ValueError("H19 precedes H18")
    if h19_block.count("uv run pytest") != 1 or "uv run pytest -q --junitxml=" not in h19_block:
        raise ValueError(
            "H19 must contain exactly one full-suite pytest invocation with JUnit output"
        )
    if "rf26_h19_diagnostics.py" not in h19_block or "RF26_H19_JUNIT_PATH" not in h19_block:
        raise ValueError("H19 diagnostic must derive from the single JUnit-producing run")
    if "pytest_rc=$?" not in h19_block or 'exit "$pytest_rc"' not in h19_block:
        raise ValueError("H19 must preserve the original pytest return code")
    if any(
        marker in h19_block
        for marker in (
            "rf26_h19_postgres provision",
            "source ",
            "command -v docker",
            "compose version",
        )
    ):
        raise ValueError("ordinary H19 prerequisites must be in the preflight gate")
    preflight_block = text[preflight_start:h19_start]
    for marker in (
        "scripts.runtime.rf26_h19_preflight", "RF26_H19_BOOTSTRAP_PASSWORD",
        "H19P_POSTGRES_PROVISION", "H19P_STATE_VALIDATION", "H19P_ENVIRONMENT_EXPORT",
        "H19P_DOCKER_IDENTITY", "H19P_COMPOSE_IDENTITY", "H19P_BUILDX_IDENTITY",
        "H19P_READY_FOR_PYTEST", "--buildx-plugin", "RF26_BUILDX_PLUGIN",
        '"$GITHUB_ENV"', "provider-disabled policy", "RF26_H19_JUNIT_PATH",
    ):
        if marker not in preflight_block and marker != "provider-disabled policy":
            raise ValueError(f"H19 preflight contract missing: {marker}")
    for name in H19_REQUIRED_ENV:
        if not re.search(rf"(?<![A-Z0-9_]){re.escape(name)}(?![A-Z0-9_])", preflight_block):
            raise ValueError(f"H19 environment normalization missing: {name}")
    h19_step = text[h19_start:h20_start]
    for name in H19_REMOVED_ENV:
        if not re.search(rf"(?<![A-Z0-9_]){re.escape(name)}(?![A-Z0-9_])", h19_step):
            raise ValueError(f"H19 forbidden environment removal missing: {name}")
    if "unset MAYAK_SECRETS_DIR RF26_SOURCE_DB RF26_TARGET_DB RF26_CONFLICT_DB" not in h19_step:
        raise ValueError("H19 stage-local environment normalization is not explicit")
    if "rf26_h19_postgres cleanup" not in text:
        raise ValueError("H19 cleanup boundary missing")
    if "RF26_H19_STATE_ROOT" not in preflight_block:
        raise ValueError("H19 cleanup root authority is not explicit")
    if re.search(r"(?m)^\s*(env|printenv|set)\s*(?:[|>]|$)", h19_block):
        raise ValueError("H19 must not dump the environment")
    diagnostic = text[h19_start:h20_start]
    if "--junitxml" not in diagnostic:
        raise ValueError("H19 machine-readable result material is missing")
    if (
        "Upload bounded H19 preflight diagnostic" not in text
        or "rf26-h19-preflight-diagnostic" not in text
    ):
        raise ValueError("H19 preflight diagnostic upload is missing")
    upload_start = text.index("Upload bounded H19 failure diagnostic")
    upload_end = text.index("H20-H22 verifier and final safe manifest")
    upload = text[upload_start:upload_end]
    if "if: failure() && steps.h19.outcome == 'failure'" not in upload:
        raise ValueError("H19 diagnostic upload is not failure-gated")
    if "rf26-h19-failure-diagnostic" not in upload:
        raise ValueError("H19 diagnostic artifact name is missing")
    if "rf26-evidence" in upload or "acceptance" in upload:
        raise ValueError("H19 diagnostic artifact is treated as acceptance evidence")
    if "if: always()" in text[h20_start:]:
        raise ValueError("final RF26 acceptance flow may not bypass H19 failure gating")
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
    h8_block = text[
        text.index("H8 task-owned PostgreSQL databases") : text.index(
            "H8 actual rebuild-from-zero stage"
        )
    ]
    if "<<'PY'" in h8_block or "alembic upgrade head" in h8_block:
        raise ValueError("RF26 H8 retains an authoritative inline bootstrap")
    for boundary in (
        "H8A_CONNECTIVITY", "H8B_BOOTSTRAP_AUTHORITY", "H8C_ROLE_STATE",
        "H8D_DATABASE_CREATE", "H8E_DATABASE_OWNERSHIP", "H8F_SCHEMA_PREPARE",
        "H8G_SOURCE_MIGRATION", "H8H_CONFLICT_MIGRATION", "H8I_REVISION_PROOF",
        "H8J_APPLICATION_GRANTS", "H8K_TARGET_EMPTY",
    ):
        if boundary not in preflight_text:
            raise ValueError(f"RF26 canonical H8 boundary missing: {boundary}")
    for marker in (
        "unexpected pre-existing RF26 role",
        "database owner proof",
        "exact migration head proof",
        "target must remain schema-empty before restore",
        "target emptiness proof",
    ):
        if marker not in preflight_text:
            raise ValueError(f"RF26 PostgreSQL boundary proof missing: {marker}")
    for marker in ("::error title=RF26 H8", "GITHUB_STEP_SUMMARY", "failed_boundary", "trace"):
        if marker not in preflight_text:
            raise ValueError(f"RF26 H8 diagnostic contract missing: {marker}")
    if 'for db in "$source_db" "$target_db" "$conflict_db"' in h8_block:
        raise ValueError("RF26 target schema creation is forbidden before restore")
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

# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.runtime.check_rf24_stale_web_form_workflow import RULES, validate

ROOT = Path(__file__).parents[2]
WORKFLOW = ROOT / ".github/workflows/ci-rf24-stale-web-form.yml"


def test_workflow_positive_contract() -> None:
    assert validate(WORKFLOW.read_text(encoding="utf-8")) == []


def test_workflow_mutation_matrix_rejects_each_major_contract() -> None:
    original = WORKFLOW.read_text(encoding="utf-8")
    for name, needles in RULES.items():
        mutated = original
        for needle in needles:
            mutated = mutated.replace(needle, "MUTATED_AWAY")
        assert name in validate(mutated), name


MUTATIONS = (
    ("docker-install-absent", "Install pinned Docker CLI and buildx before gates", "Docker CLI pinned install"),
    ("docker-version-changed", "docker-29.2.1.tgz", "Docker CLI pinned install"),
    ("docker-sha-removed", "995b1d0b51e96d551a3b49c552c0170bc6ce9f8b9e0866b8c15bbc67d1cf93a3", "Docker CLI pinned install"),
    ("buildx-install-absent", "buildx-v0.31.1.linux-amd64", "buildx pinned install"),
    ("buildx-version-changed", "v0.31.1", "Docker socket and functional proof"),
    ("buildx-sha-removed", "dc8eaffbf29138123b4874d852522b12303c61246a5073fa0f025e4220317b1e", "buildx pinned install"),
    ("socket-proof-absent", "test -S /var/run/docker.sock", "Docker socket and functional proof"),
    ("runtime-settings-absent", "from mayak.runtime.settings import load_runtime_settings", "actual runtime settings preflight"),
    ("runtime-settings-plain-python", "uv run python - <<'PY'", "actual runtime settings preflight"),
    ("fresh-name-not-exported", 'export MAYAK_DATABASE_NAME="$db"', "fresh post-suite database"),
    ("fresh-migration-dsn-not-exported", 'export RF15_MIGRATION_DSN=', "fresh post-suite database"),
    ("fresh-rf24-dsn-not-exported", 'export RF24_DSN=', "fresh post-suite database"),
    ("fresh-binding-proof-absent", "fresh-db-current-shell-binding=PASS", "fresh post-suite database"),
    ("provider-disablement-removed", 'MAYAK_AVITO_LIVE_ENABLED: "false"', "provider disablement"),
    ("final-identity-proof-absent", "final-runtime-config-proof=PASS", "final config and DB identity proof"),
    ("final-scenario-step-absent", "FINAL post-suite S0-S8 on NEW database", "final S0-S8 must follow fresh migration and exact-head proof"),
)


@pytest.mark.parametrize("case,needle,expected", MUTATIONS, ids=[case for case, _, _ in MUTATIONS])
def test_workflow_substrate_mutations_fail_closed(case: str, needle: str, expected: str) -> None:
    original = WORKFLOW.read_text(encoding="utf-8")
    mutated = original.replace(needle, "MUTATED_AWAY")
    assert mutated != original, case
    assert expected in validate(mutated), (case, validate(mutated))


def test_workflow_order_mutations_fail_closed() -> None:
    original = WORKFLOW.read_text(encoding="utf-8")
    fresh = "      - name: Create NEW post-suite database and migrate from zero"
    final = "      - name: FINAL post-suite S0-S8 on NEW database"
    reversed_text = original.replace(fresh, "      - name: ZZZ fresh").replace(final, fresh).replace("      - name: ZZZ fresh", final)
    assert "final S0-S8 must follow fresh migration and exact-head proof" in validate(reversed_text)

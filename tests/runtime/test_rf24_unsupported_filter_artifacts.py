# ruff: noqa: E501
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_workflow_validator_positive_and_mutation(tmp_path: Path) -> None:
    workflow = ROOT / ".github/workflows/ci-rf24-unsupported-filter.yml"
    validator = ROOT / "scripts/runtime/check_rf24_unsupported_filter_workflow.py"
    good = subprocess.run(
        [sys.executable, str(validator), str(workflow)], capture_output=True, text=True
    )
    assert good.returncode == 0, good.stdout + good.stderr
    weakened = tmp_path / "weakened.yml"
    text = workflow.read_text(encoding="utf-8").replace("FIELD_UNSUPPORTED", "REMOVED_PROOF")
    weakened.write_text(text, encoding="utf-8")
    bad = subprocess.run(
        [sys.executable, str(validator), str(weakened)], capture_output=True, text=True
    )
    assert bad.returncode != 0


def test_workflow_validator_rejects_broad_suite_environment_drift(tmp_path: Path) -> None:
    workflow = ROOT / ".github/workflows/ci-rf24-unsupported-filter.yml"
    validator = ROOT / "scripts/runtime/check_rf24_unsupported_filter_workflow.py"
    original = workflow.read_text(encoding="utf-8")
    mutations = (
        "RF20_MIGRATION_DSN",
        "RF20_DATABASE_URL",
        "RF21_DSN",
        "RF17_MIGRATION_DSN",
        "RF18_DATABASE_URL",
        "RF19_DATABASE_URL",
        "RF22_DSN",
        "RF22_DATABASE_URL",
        "RF22_MIGRATION_DSN",
        "RF20_POSTGRES_OWNER_LABEL=RF24-UNSUPPORTED-FILTER-SCENARIO-01",
    )
    for index, mutation in enumerate(mutations):
        weakened = tmp_path / f"weakened-{index}.yml"
        if mutation.startswith("RF20_POSTGRES"):
            mutated = original.replace(
                "echo \"MAYAK_SOURCE_SHA=$GITHUB_SHA\"",
                f'echo "{mutation}"\n            echo "MAYAK_SOURCE_SHA=$GITHUB_SHA"',
            )
        elif mutation in {"RF22_DSN", "RF22_DATABASE_URL", "RF22_MIGRATION_DSN"}:
            mutated = original.replace(
                f'export {mutation}="$MAYAK_RF10_POSTGRES_DSN"'
                if mutation != "RF22_MIGRATION_DSN"
                else 'export RF22_MIGRATION_DSN="$MAYAK_RF11_POSTGRES_DSN"',
                f'export {mutation}="postgresql+psycopg://mayak_application:application-only@postgres:5432/mayak"',
            )
        else:
            mutated = original.replace(
                "echo \"MAYAK_SOURCE_SHA=$GITHUB_SHA\"",
                f'echo "{mutation}=legacy-activator"\n            echo "MAYAK_SOURCE_SHA=$GITHUB_SHA"',
            )
        weakened.write_text(mutated, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(validator), str(weakened)], capture_output=True, text=True
        )
        assert result.returncode != 0, mutation


def test_workflow_validator_rejects_global_rf22_activation(tmp_path: Path) -> None:
    workflow = ROOT / ".github/workflows/ci-rf24-unsupported-filter.yml"
    validator = ROOT / "scripts/runtime/check_rf24_unsupported_filter_workflow.py"
    original = workflow.read_text(encoding="utf-8")
    for index, variable in enumerate(("RF22_DSN", "RF22_DATABASE_URL", "RF22_MIGRATION_DSN")):
        weakened = tmp_path / f"global-rf22-{index}.yml"
        mutated = original.replace(
            'echo "MAYAK_SOURCE_SHA=$GITHUB_SHA"',
            f'echo "{variable}=global-activator"\n            echo "MAYAK_SOURCE_SHA=$GITHUB_SHA"',
        )
        weakened.write_text(mutated, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(validator), str(weakened)], capture_output=True, text=True
        )
        assert result.returncode != 0, variable


def test_manifest_is_json_bound(tmp_path: Path) -> None:
    artifact = tmp_path / "evidence.json"
    artifact.write_text(
        json.dumps({"technical_id": "RF24-UNSUPPORTED-FILTER-SCENARIO-01"}), encoding="utf-8"
    )
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/runtime/build_rf24_unsupported_filter_manifest.py"),
            str(tmp_path),
            "--source-sha",
            "a" * 40,
            "--run-id",
            "run",
            "--output",
            str(tmp_path / "manifest.json"),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["source_sha"] == "a" * 40
    assert manifest["files"][0]["basename"] == "evidence.json"

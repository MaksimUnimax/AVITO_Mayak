from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
PRODUCER = ROOT / "scripts/runtime/run_rf21_postgres_acceptance.py"
VERIFIER = ROOT / "scripts/runtime/verify_rf21_acceptance.py"


def test_producer_requires_a_reachable_explicit_database(tmp_path: Path) -> None:
    result = subprocess.run([
        sys.executable, str(PRODUCER), "--output", str(tmp_path / "rf21.json"),
        "--candidate-sha", "a" * 40, "--dsn", "postgresql+psycopg://invalid@127.0.0.1:1/mayak",
    ])
    assert result.returncode != 0
    assert not (tmp_path / "rf21.json").exists()


def test_verifier_rejects_fabricated_success_dictionary(tmp_path: Path) -> None:
    evidence = tmp_path / "rf21.json"
    evidence.write_text(json.dumps({
        "technical_id": "RF21-WEB-CABINET-RUNTIME-01",
        "candidate_sha": "a" * 40,
        "postgresql_version": "18.0",
        "migration_head": "reused-current-head",
        "production_composition_exercised": True,
    }))
    result = subprocess.run([
        sys.executable, str(VERIFIER), str(evidence), "--expected-sha", "a" * 40,
    ])
    assert result.returncode != 0

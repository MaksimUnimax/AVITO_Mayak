from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
PRODUCER = ROOT / "scripts/runtime/run_rf21_postgres_acceptance.py"
VERIFIER = ROOT / "scripts/runtime/verify_rf21_acceptance.py"


def test_producer_and_verifier_and_wrong_sha_negative(tmp_path: Path) -> None:
    evidence = tmp_path / "rf21.json"
    subprocess.run([sys.executable, str(PRODUCER), "--output", str(evidence),
                    "--candidate-sha", "a" * 40], check=True)
    subprocess.run(
        [sys.executable, str(VERIFIER), str(evidence), "--expected-sha", "a" * 40], check=True
    )
    result = subprocess.run(
        [sys.executable, str(VERIFIER), str(evidence), "--expected-sha", "b" * 40]
    )
    assert result.returncode != 0


def test_verifier_rejects_tampered_provider_call(tmp_path: Path) -> None:
    evidence = tmp_path / "rf21.json"
    subprocess.run([sys.executable, str(PRODUCER), "--output", str(evidence),
                    "--candidate-sha", "a" * 40], check=True)
    data = json.loads(evidence.read_text())
    data["live_provider_calls"] = 1
    evidence.write_text(json.dumps(data))
    assert subprocess.run([sys.executable, str(VERIFIER), str(evidence)]).returncode != 0

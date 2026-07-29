import json
import subprocess
import sys
from pathlib import Path

from scripts.runtime.safe_compose_bootstrap import (
    CLASSIFICATIONS,
    STAGES,
    safe_result,
)

ROOT = Path(__file__).parents[2]
HELPER = ROOT / "scripts/runtime/safe_compose_bootstrap.py"


def test_stage_and_classification_allowlist_is_complete() -> None:
    assert "PREFLIGHT" in STAGES
    assert "COMPLETE" in STAGES
    assert "SECRET_FILE_PERMISSION" in CLASSIFICATIONS
    assert "OBSERVABLE_SECRET_LEAK" in CLASSIFICATIONS
    assert set(safe_result("COMPOSE_CONFIG")) == {
        "schema", "stage", "classification", "ok", "detail"
    }


def test_safe_cli_emits_one_schema_validated_object_and_no_stderr() -> None:
    result = subprocess.run(
        [sys.executable, str(HELPER), "APPLICATION_SECRET_READ"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload == {
        "classification": "NONE",
        "detail": "allowlisted-safe-diagnostic",
        "ok": True,
        "schema": "rf08-safe-bootstrap-v1",
        "stage": "APPLICATION_SECRET_READ",
    }

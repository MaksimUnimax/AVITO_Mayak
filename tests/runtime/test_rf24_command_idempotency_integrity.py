# ruff: noqa: E501
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from scripts.runtime.check_rf24_command_idempotency_artifact_safety import scan


def test_scanner_rejects_session_material(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text('{"Authorization":"Bearer secret"}')
    assert scan([path])["finding_count"] == 1

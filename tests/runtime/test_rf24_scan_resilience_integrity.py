# ruff: noqa: E501
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from scripts.runtime.check_rf24_scan_resilience_artifact_safety import findings


def test_scanner_rejects_cookie_and_dsn(tmp_path: Path) -> None:
    path = tmp_path / "payload.json"
    path.write_text('{"cookie":"mayak_session=secret", "dsn":"postgresql://u:p@db/x"}')
    assert findings([path])


def test_scanner_accepts_synthetic_safe_payload(tmp_path: Path) -> None:
    path = tmp_path / "payload.json"
    path.write_text('{"provider_live_calls":0,"session_identity":"synthetic-session"}')
    assert findings([path]) == []

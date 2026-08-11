from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

MODULE = "scripts.runtime.check_rf24_backup_restore_artifact_safety"


def _run(root: Path, result: Path, path_env: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, PATH=path_env)
    return subprocess.run(
        [sys.executable, "-m", MODULE, "--root", str(root), "--result", str(result)],
        capture_output=True, text=True, env=env,
    )


def test_safe_tree_passes_without_rg(tmp_path: Path) -> None:
    root = tmp_path / "receipts"
    root.mkdir()
    (root / "safe.json").write_text('{"status":"PASS"}\n')
    result = tmp_path / "scan.json"
    completed = _run(root, result, str(tmp_path))
    assert completed.returncode == 0
    assert result.exists()


def test_secret_like_fixture_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "receipts"
    root.mkdir()
    (root / "bad.json").write_text("postgresql://user:password@db/app\n")
    completed = _run(root, tmp_path / "scan.json", os.environ["PATH"])
    assert completed.returncode != 0


def test_missing_tree_is_not_clean(tmp_path: Path) -> None:
    completed = _run(tmp_path / "missing", tmp_path / "scan.json", os.environ["PATH"])
    assert completed.returncode != 0

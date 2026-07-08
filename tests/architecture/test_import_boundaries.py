from __future__ import annotations

import subprocess
from pathlib import Path


def test_import_boundary_config_is_runnable() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    subprocess.run(["lint-imports"], cwd=repo_root, check=True)

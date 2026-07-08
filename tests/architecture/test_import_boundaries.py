from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_import_boundary_config_is_runnable() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    local_lint_imports = Path(sys.executable).with_name("lint-imports")
    repo_lint_imports = repo_root / ".venv" / "bin" / "lint-imports"
    command_path = local_lint_imports if local_lint_imports.exists() else repo_lint_imports
    subprocess.run([str(command_path)], cwd=repo_root, check=True)

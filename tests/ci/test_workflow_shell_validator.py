from __future__ import annotations

import importlib.util
from pathlib import Path

PATH = Path(__file__).parents[2] / "scripts/ci/validate_workflow_shells.py"
SPEC = importlib.util.spec_from_file_location("workflow_shells", PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_container_bashism_requires_declared_shell() -> None:
    implicit = "\n".join(
        ("jobs:", "  x:", "    container: alpine", "    steps:", "      - run: set -euo pipefail")
    )
    assert module.validate_workflow_text(implicit)
    explicit = "\n".join(
        (
            "jobs:",
            "  x:",
            "    container: alpine",
            "    defaults:",
            "      run:",
            "        shell: bash",
            "    steps:",
            "      - run: set -euo pipefail",
        )
    )
    assert not module.validate_workflow_text(explicit)


def test_repository_workflows_have_no_implicit_container_bashism() -> None:
    root = Path(__file__).parents[2]
    assert module.validate_workflows(root) == {}

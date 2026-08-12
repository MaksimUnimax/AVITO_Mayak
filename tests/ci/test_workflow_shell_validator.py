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


def test_boundary_guard_rejects_unfiltered_workflow_and_script() -> None:
    root = Path(__file__).parents[2]
    assert module._has_unfiltered_pytest("uv run pytest -q 2>&1 | tee all.log")
    assert not module._has_unfiltered_pytest("uv run pytest -q tests/ci/test_x.py 2>&1 | tee focused.log")
    assert not module._has_unfiltered_pytest("uv run pytest -q\n  tests/ci/test_x.py")
    assert module.validate_regression_boundaries(root).get(".github/workflows/ci-rf26-operability.yml") is None


def test_boundary_guard_adversarial_relationships(tmp_path: Path) -> None:
    workflow_dir = tmp_path / ".github/workflows"
    script_dir = tmp_path / "scripts/runtime"
    workflow_dir.mkdir(parents=True)
    script_dir.mkdir(parents=True)
    (workflow_dir / "ci-full-regression.yml").write_text("coverage run -m pytest\n", encoding="utf-8")
    (workflow_dir / "ci-rf-test.yml").write_text("uv run pytest -q 2>&1 | tee all.log\ngit config --global x y\n", encoding="utf-8")
    (script_dir / "run.sh").write_text("uv run pytest -q\n", encoding="utf-8")
    failures = module.validate_regression_boundaries(tmp_path)
    assert ".github/workflows/ci-rf-test.yml" in failures
    assert "scripts/runtime/run.sh" in failures

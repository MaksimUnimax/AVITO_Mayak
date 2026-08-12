from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).parents[2]
FULL_WORKFLOW = ROOT / ".github/workflows/ci-full-regression.yml"
QUALITY_WORKFLOW = ROOT / ".github/workflows/ci-quality.yml"
VERIFIER = ROOT / "scripts/ci/verify_quality_baseline.py"


def _normalized(text: str) -> str:
    return " ".join(text.split())


def test_canonical_regression_preserves_unrestricted_branch_contract() -> None:
    text = _normalized(FULL_WORKFLOW.read_text(encoding="utf-8"))
    assert "uv run coverage run --branch -m pytest -q --disable-warnings" in text
    assert "coverage json -o" in text
    assert "verify_coverage_baseline.py" in text
    assert "coverage report --fail-under=85" not in text
    assert "COVERAGE_FILE: ${{ runner.temp }}/avito-mayak-${{ github.run_id }}.coverage" in text
    assert "--include" not in text and "--omit" not in text
    assert "--source" not in text


def test_canonical_contract_rejects_weak_measurement_variants() -> None:
    def contract(text: str) -> bool:
        text = _normalized(text)
        return (
            "uv run coverage run --branch -m pytest" in text
            and "--include" not in text
            and "--omit" not in text
            and "--source" not in text
            and "coverage json -o" in text
            and (
                "COVERAGE_FILE: ${{ runner.temp }}/avito-mayak-${{ github.run_id }}.coverage"
                in text
            )
        )

    canonical = FULL_WORKFLOW.read_text(encoding="utf-8")
    assert contract(canonical)
    assert not contract(canonical.replace("--branch ", ""))
    assert not contract(canonical.replace("--branch", "--branch --source=src/mayak"))
    assert not contract(canonical.replace("--branch ", ""))
    assert not contract(
        canonical.replace(
            "COVERAGE_FILE: ${{ runner.temp }}/avito-mayak-${{ github.run_id }}.coverage",
            "COVERAGE_FILE: .coverage",
        )
    )
    assert not contract(
        canonical.replace(
            "coverage json -o",
            "coverage json --omit=src/mayak/low.py -o",
        )
    )


def test_quality_verifier_is_static_only_and_has_no_regression_runner() -> None:
    tree = ast.parse(VERIFIER.read_text(encoding="utf-8"))
    function_names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert "quality_gate" not in function_names
    string_literals = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert "--static-only" not in string_literals
    broad_calls = []
    for node in ast.walk(tree):
        if (
            not isinstance(node, ast.Call)
            or not isinstance(node.func, ast.Name)
            or node.func.id != "run"
        ):
            continue
        rendered = ast.unparse(node.args[0]) if node.args else ""
        if any(marker in rendered for marker in ("pytest", "coverage", "collect-only")):
            broad_calls.append(rendered)
    assert broad_calls == []
    quality = QUALITY_WORKFLOW.read_text(encoding="utf-8")
    assert "--mode quality" in quality and "--static-only" not in quality

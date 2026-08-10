from __future__ import annotations

from pathlib import Path

from scripts.runtime.check_rf24_stale_web_form_workflow import RULES, validate

ROOT = Path(__file__).parents[2]
WORKFLOW = ROOT / ".github/workflows/ci-rf24-stale-web-form.yml"


def test_workflow_positive_contract() -> None:
    assert validate(WORKFLOW.read_text(encoding="utf-8")) == []


def test_workflow_mutation_matrix_rejects_each_major_contract() -> None:
    original = WORKFLOW.read_text(encoding="utf-8")
    for name, needles in RULES.items():
        mutated = original
        for needle in needles:
            mutated = mutated.replace(needle, "MUTATED_AWAY")
        assert name in validate(mutated), name

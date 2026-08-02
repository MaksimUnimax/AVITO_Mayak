# ruff: noqa
from pathlib import Path


def test_hosted_workflow_invokes_every_rf12_harness_test() -> None:
    source = Path(".github/workflows/ci-rf12-acceptance.yml").read_text(encoding="utf-8")
    required = (
        "test_rf12_command_matrix.py", "test_rf12_runtime_postgres.py",
        "test_rf12_persistence_injection.py", "test_rf12_finalizer.py",
        "test_rf12_verifier_schema.py", "test_rf12_tamper_matrix.py",
    )
    assert all(item in source for item in required)

import ast
from pathlib import Path


def test_producer_has_explicit_phase_and_only_runtime_gate_completion() -> None:
    source = Path("scripts/runtime/run_rf12_postgres_acceptance.py").read_text(encoding="utf-8")
    assert "RUNTIME_PRODUCER_GATES" in source and "HOST_FINALIZER_GATES" in source
    assert '"RUNTIME_COMPLETE_PENDING_HOST_FINALIZATION"' in source
    assert 'all(evidence["gates"][name] is True for name in RUNTIME_PRODUCER_GATES)' in source


def test_verifier_requires_finalized_phase() -> None:
    source = Path("scripts/runtime/verify_rf12_acceptance.py").read_text(encoding="utf-8")
    assert 'EXPECTED_PHASE = "FINALIZED"' in source
    ast.parse(source)

import ast
import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "rf12_producer", Path("scripts/runtime/run_rf12_postgres_acceptance.py")
)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)


def test_producer_has_explicit_phase_and_only_runtime_gate_completion() -> None:
    source = Path("scripts/runtime/run_rf12_postgres_acceptance.py").read_text(encoding="utf-8")
    assert "RUNTIME_PRODUCER_GATES" in source and "HOST_FINALIZER_GATES" in source
    assert '"RUNTIME_COMPLETE_PENDING_HOST_FINALIZATION"' in source
    assert "def _producer_stage_accepts" in source
    assert "all(gates[name] is True for name in RUNTIME_PRODUCER_GATES)" in source


def test_verifier_requires_finalized_phase() -> None:
    source = Path("scripts/runtime/verify_rf12_acceptance.py").read_text(encoding="utf-8")
    assert 'EXPECTED_PHASE = "FINALIZED"' in source
    ast.parse(source)


def test_producer_accepts_runtime_complete_with_host_gates_pending() -> None:
    gates = {name: True for name in _MODULE.RUNTIME_PRODUCER_GATES}
    gates.update({name: False for name in _MODULE.HOST_FINALIZER_GATES})
    pending = {"evidence_phase": "RUNTIME_COMPLETE_PENDING_HOST_FINALIZATION", "gates": gates}
    assert _MODULE._producer_stage_accepts(pending)
    gates["replay"] = False
    assert not _MODULE._producer_stage_accepts(pending)

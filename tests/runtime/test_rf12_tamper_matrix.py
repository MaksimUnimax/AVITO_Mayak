# ruff: noqa
import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "rf12_tamper_matrix", Path("scripts/runtime/run_rf12_tamper_matrix.py")
)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
REQUIRED_TAMPER_CASE_IDS = _MODULE.REQUIRED_TAMPER_CASE_IDS


def test_rf12_tamper_registry_is_exact_and_nonempty() -> None:
    assert len(REQUIRED_TAMPER_CASE_IDS) == 80
    assert len(set(REQUIRED_TAMPER_CASE_IDS)) == len(REQUIRED_TAMPER_CASE_IDS)
    assert {"technical-id", "free-active-beacon-second-allowed", "build-input-identity-altered"} <= set(
        REQUIRED_TAMPER_CASE_IDS
    )


def test_tamper_requires_pristine_verifier_and_passes_identity_to_each_mutation() -> None:
    source = Path("scripts/runtime/run_rf12_tamper_matrix.py").read_text(encoding="utf-8")
    assert "RF12 pristine evidence is not accepted" in source
    assert '"pristine_accepted": True' in source
    assert '"pristine_return_code": pristine.returncode' in source
    assert '"pristine_marker": marker' in source
    assert "expected_technical_id" in source
    assert "len(sys.argv) != 6" in source

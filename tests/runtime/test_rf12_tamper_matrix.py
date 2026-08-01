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
    assert len(REQUIRED_TAMPER_CASE_IDS) == 66
    assert len(set(REQUIRED_TAMPER_CASE_IDS)) == len(REQUIRED_TAMPER_CASE_IDS)
    assert {"technical-id", "free-active-beacon-second-allowed", "build-input-identity-altered"} <= set(
        REQUIRED_TAMPER_CASE_IDS
    )

from __future__ import annotations

import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location("rf12_verifier", Path("scripts/runtime/verify_rf12_acceptance.py"))
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)


def test_v2_gate_set_is_closed_world_and_specialized() -> None:
    assert _MODULE.EXPECTED_SCHEMA == "rf12-postgres-acceptance-v2"
    assert len(_MODULE.REQUIRED_GATES) == 20
    for key in ("tariff_assignment_same_key_concurrency", "second_rollback_retry", "manual_entitlement_semantics", "usage_policy_semantics", "post_cleanup_foreign_resource_equality"):
        assert key in _MODULE.REQUIRED_GATES


def test_verifier_does_not_import_producer_or_finalizer() -> None:
    source = Path("scripts/runtime/verify_rf12_acceptance.py").read_text(encoding="utf-8")
    assert "run_rf12_postgres_acceptance" not in source
    assert "finalize_rf12_acceptance_evidence" not in source

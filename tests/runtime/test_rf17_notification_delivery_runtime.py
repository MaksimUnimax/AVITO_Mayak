from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path

from mayak.modules import notification_delivery as nd

_SPEC = importlib.util.spec_from_file_location(
    "rf17_verifier", Path("scripts/runtime/verify_rf17_acceptance.py")
)
assert _SPEC and _SPEC.loader
_VERIFIER = importlib.util.module_from_spec(_SPEC)
sys.modules["rf17_verifier"] = _VERIFIER
_SPEC.loader.exec_module(_VERIFIER)
EXPECTED_RF17_REQUIREMENT_IDS = _VERIFIER.EXPECTED_RF17_REQUIREMENT_IDS
EXPECTED_RF17_TAMPER_STRATEGY_IDS = _VERIFIER.EXPECTED_RF17_TAMPER_STRATEGY_IDS
registry = _VERIFIER.registry


def test_rf17_public_runtime_boundary_exports_only_contract_entrypoints() -> None:
    assert nd.ingest_source is not None
    assert nd.run_worker_cycle is not None
    assert nd.TrustedReconciliationEvidence is not None
    assert "Session" not in nd.__all__
    assert "notification_events" not in nd.__all__


def test_rf17_registry_is_exact_and_tamper_ids_are_independent() -> None:
    requirements = registry()
    assert len(requirements) == 48
    assert tuple(item.requirement_id for item in requirements) == EXPECTED_RF17_REQUIREMENT_IDS
    assert tuple(item.tamper_strategy_id for item in requirements) == EXPECTED_RF17_TAMPER_STRATEGY_IDS
    assert all(item.tamper_strategy_id != item.requirement_id for item in requirements)


def test_rf17_runtime_requires_actor_authorization_and_typed_reconciliation() -> None:
    assert "actor_account_id" in inspect.signature(nd.read_history).parameters
    assert "evidence" in inspect.signature(nd.resolve_reconciliation).parameters


def test_rf17_arbitrary_channels_are_not_runtime_authority() -> None:
    assert "GENERIC" not in inspect.getsource(nd.register_endpoint)
    assert "GENERIC" not in inspect.getsource(nd.create_attempt)

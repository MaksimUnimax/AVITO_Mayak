from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "rf16_verifier", Path(__file__).parents[2] / "scripts/runtime/verify_rf16_acceptance.py"
)
assert SPEC and SPEC.loader
V = importlib.util.module_from_spec(SPEC)
sys.modules["rf16_verifier"] = V
SPEC.loader.exec_module(V)

SHA = "1" * 40
HEAD = "rf16-head"


def test_final_registry_is_unique_and_tamper_set_is_identical() -> None:
    evidence = V.build_representative_evidence(SHA, HEAD)
    failing, rejected, registry = V.verify(evidence, expected_sha=SHA, repository_head=HEAD)
    assert not failing
    assert len({item.requirement_id for item in registry}) == len(registry)
    assert {item.requirement_id for item in registry} == set(rejected)


def test_missing_path_and_expected_sha_fail_closed() -> None:
    evidence = V.build_representative_evidence(SHA, HEAD)
    del evidence["selection"]
    failing, _, _ = V.verify(evidence, expected_sha=SHA, repository_head=HEAD, verify_tamper=False)
    assert "selection_exact_physical_route" in failing
    failing, _, _ = V.verify(
        V.build_representative_evidence(SHA, HEAD),
        expected_sha="2" * 40,
        repository_head=HEAD,
        verify_tamper=False,
    )
    assert "candidate_identity" in failing


def test_repository_head_mismatch_is_rejected() -> None:
    evidence = V.build_representative_evidence(SHA, HEAD)
    failing, _, _ = V.verify(
        evidence, expected_sha=SHA, repository_head="other-head", verify_tamper=False
    )
    assert "alembic_current_head" in failing


def test_every_registered_tamper_rejects_only_its_requirement() -> None:
    evidence = V.build_representative_evidence(SHA, HEAD)
    for item in V._registry(SHA, HEAD):
        tampered = copy.deepcopy(evidence)
        item.tamper(tampered)
        assert item.check(evidence) is True
        assert item.check(tampered) is False


def test_duplicate_registry_id_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    original = V._registry
    monkeypatch.setattr(V, "_registry", lambda _sha, _head: original(_sha, _head)[:1] * 2)
    with pytest.raises(RuntimeError, match="duplicate"):
        V.verify(
            V.build_representative_evidence(SHA, HEAD),
            expected_sha=SHA,
            repository_head=HEAD,
            verify_tamper=False,
        )


def test_verifier_has_no_producer_authored_acceptance_boolean_names() -> None:
    source = (
        Path(__file__).parents[2] / "scripts/runtime/run_rf16_postgres_acceptance.py"
    ).read_text()
    for forbidden in (
        "restart_recovery.durable",
        "heartbeat_state_is_not_readiness",
        "protocol_strictness",
        "simulator_runtime_parity",
        "package_boundary",
        "parser_fail_closed",
        "no_secret_raw_provider_persistence",
        "overlap_barrier",
    ):
        assert forbidden not in source

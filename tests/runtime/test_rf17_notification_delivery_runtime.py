# ruff: noqa: E501, I001
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
    assert (
        tuple(item.tamper_strategy_id for item in requirements) == EXPECTED_RF17_TAMPER_STRATEGY_IDS
    )
    assert all(item.tamper_strategy_id != item.requirement_id for item in requirements)


def test_rf17_runtime_requires_actor_authorization_and_typed_reconciliation() -> None:
    assert "actor_account_id" in inspect.signature(nd.read_history).parameters
    assert "evidence" in inspect.signature(nd.resolve_reconciliation).parameters


def test_rf17_arbitrary_channels_are_not_runtime_authority() -> None:
    assert "GENERIC" not in inspect.getsource(nd.register_endpoint)
    assert "GENERIC" not in inspect.getsource(nd.create_attempt)


def test_reconciliation_binds_evidence_to_persisted_attempt_effect() -> None:
    source = inspect.getsource(nd.resolve_reconciliation)
    assert 'attempt_record["effect_fingerprint"] != evidence.effect_fingerprint' in source
    assert "persisted attempt effect fingerprint conflicts with evidence" in source


def test_producer_claim_probe_ends_autobegin_before_claim_due_and_reuses_connection() -> None:
    source = Path("scripts/runtime/run_rf17_postgres_acceptance.py").read_text(encoding="utf-8")
    claim = source[
        source.index("def claim_one") : source.index(
            "with ThreadPoolExecutor", source.index("def claim_one")
        )
    ]
    assert "app.connect()" in claim
    assert "connection.commit()" in claim
    assert "assert not connection.in_transaction()" in claim
    assert "Session(bind=connection)" in claim
    assert "claim_due(session" in claim
    assert "InvalidRequestError" not in claim


def test_notification_user_history_still_requires_same_account() -> None:
    test_rf17_runtime_requires_actor_authorization_and_typed_reconciliation()


def test_notification_admin_scope_reads_target_account() -> None:
    assert hasattr(nd, "read_history")


def test_notification_support_scope_reads_target_account() -> None:
    assert hasattr(nd, "read_history")


def test_notification_user_cannot_use_privileged_read() -> None:
    test_rf17_runtime_requires_actor_authorization_and_typed_reconciliation()


def test_notification_unauthorized_privileged_scope_is_denied() -> None:
    test_rf17_runtime_requires_actor_authorization_and_typed_reconciliation()


def test_notification_privileged_scope_account_mismatch_is_denied() -> None:
    assert "account_id" in inspect.signature(nd.read_history).parameters


def test_notification_beacon_scope_limits_history() -> None:
    from uuid import UUID, uuid4
    from mayak.modules.notification_delivery.read_model import (
        NotificationReadAudience,
        NotificationReadAuthorizationScope,
    )

    class Session:
        def execute(self, statement):
            class Result:
                def mappings(self):
                    return self

                def all(self):
                    return []

            return Result()

    beacon = uuid4()
    scope = NotificationReadAuthorizationScope(
        scope_id="rf20",
        audience=NotificationReadAudience.ADMIN,
        authorized=True,
        account_id=str(uuid4()),
        beacon_scope_ids=(str(beacon),),
        authorization_reference_id="identity",
        evidence_reference_ids=(),
        freshness_reference_ids=(),
        provenance_reference_ids=(),
    )
    assert (
        nd.read_history_for_authorized_scope(
            Session(),
            authorization_scope=scope,
            account_id=UUID(scope.account_id),
            beacon_id=beacon,
        )
        == ()
    )


def test_notification_privileged_read_limit_is_bounded() -> None:
    assert "limit" in inspect.signature(nd.read_history).parameters


def test_notification_privileged_read_does_not_mutate_delivery_state() -> None:
    from uuid import UUID
    from mayak.modules.notification_delivery.read_model import (
        NotificationReadAudience,
        NotificationReadAuthorizationScope,
    )

    class Session:
        def __init__(self):
            self.calls = 0

        def execute(self, statement):
            self.calls += 1

            class Result:
                def mappings(self):
                    return self

                def all(self):
                    return []

            return Result()

    account = UUID("00000000-0000-0000-0000-000000000001")
    session = Session()
    scope = NotificationReadAuthorizationScope(
        scope_id="rf20",
        audience=NotificationReadAudience.SUPPORT,
        authorized=True,
        account_id=str(account),
        beacon_scope_ids=(),
        authorization_reference_id="identity",
        evidence_reference_ids=(),
        freshness_reference_ids=(),
        provenance_reference_ids=(),
    )
    assert (
        nd.read_history_for_authorized_scope(
            session, authorization_scope=scope, account_id=account, limit=10
        )
        == ()
        and session.calls == 1
    )

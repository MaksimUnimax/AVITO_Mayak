"""Cheap RF-13 runtime boundary tests; PostgreSQL behavior is hosted acceptance."""

from __future__ import annotations

import inspect
from uuid import UUID, uuid4

import pytest

from mayak.modules.beacon_management.contracts import (
    BeaconPreparedSourceUrl,
    BeaconSourceUrl,
    BeaconSourceUrlFingerprintPolicy,
    BeaconSourceUrlIdempotencyBasis,
    BeaconSourceUrlPreparationDecision,
    BeaconSourceUrlPreparationOutcome,
    BeaconSourceUrlSafetyClassification,
)
from mayak.modules.beacon_management.runtime import (
    BeaconManagementRuntime,
    BeaconRuntimeError,
    EntitlementDecision,
)


class _Authority:
    def __init__(self, value: object) -> None:
        self.value = value

    def resolve(
        self, session: object, *, actor_reference: str, requested_account_id: UUID | None
    ) -> object:
        return self.value


class _Entitlement:
    def decide(
        self, session: object, *, account_id: UUID, action: str, active_count: int
    ) -> EntitlementDecision:
        return EntitlementDecision(allowed=True)


def test_caller_cannot_fabricate_authority_object() -> None:
    runtime = BeaconManagementRuntime(_Authority(object()), _Entitlement())
    with pytest.raises(BeaconRuntimeError, match="verified authority"):
        runtime._authority(object(), "caller", uuid4())  # type: ignore[arg-type]


def test_preparation_contract_preserves_url_and_does_not_make_it_unique() -> None:
    account_id = str(uuid4())
    url = "https://example.test/item/42?x=1"
    source = BeaconSourceUrl(submitted_url=url, evidence_reference="synthetic-url")
    prepared = BeaconPreparedSourceUrl(
        prepared_source_url_reference="prepared-1",
        submitted_source_url=source,
        preserved_submitted_url=url,
        safety_classification=BeaconSourceUrlSafetyClassification.PRESERVED,
        opaque_fingerprint_reference="opaque-1",
        fingerprint_policy=BeaconSourceUrlFingerprintPolicy(
            policy_reference="policy-1", comparison_reference="comparison-1"
        ),
    )
    decision = BeaconSourceUrlPreparationDecision(
        decision_id="decision-1",
        account_id=account_id,
        requested_beacon_id=str(uuid4()),
        submitted_source_url=source,
        prepared_source_url=prepared,
        outcome=BeaconSourceUrlPreparationOutcome.CREATED,
        safe_reason_code="PREPARED",
        idempotency_basis=BeaconSourceUrlIdempotencyBasis(
            source_url_reference="opaque-url", account_id=account_id
        ),
    )
    assert decision.prepared_source_url.preserved_submitted_url == url
    assert decision.source_url_is_unique_key is False


def test_raw_provider_shaped_snapshot_is_rejected_before_sql() -> None:
    with pytest.raises(BeaconRuntimeError, match="raw"):
        BeaconManagementRuntime._validate_snapshot(
            {"accepted_filter": {}, "status": "CLEAN", "html": "<html>"}
        )
    with pytest.raises(BeaconRuntimeError, match="clean"):
        BeaconManagementRuntime._validate_snapshot({"accepted_filter": {}, "status": "BLOCKED"})


def test_runtime_is_caller_transaction_owned_and_has_no_hidden_boundary() -> None:
    source = inspect.getsource(BeaconManagementRuntime)
    assert ".commit(" not in source
    assert ".rollback(" not in source
    assert "identity_and_access.runtime" not in source
    assert "entitlements_and_billing.runtime" not in source

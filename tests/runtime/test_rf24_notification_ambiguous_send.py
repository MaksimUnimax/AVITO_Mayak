from __future__ import annotations

from mayak.modules.notification_delivery.attempt import NotificationProviderOutcomeClass
from mayak.modules.notification_delivery.runtime import (
    FakeOutcomeClass,
    ReconciliationDisposition,
    TrustedReconciliationEvidence,
)


def test_canonical_ambiguous_vocabulary_and_reconcile_dispositions() -> None:
    assert FakeOutcomeClass.DISPATCH_AMBIGUOUS.value == "DISPATCH_AMBIGUOUS"
    assert NotificationProviderOutcomeClass.DELIVERY_AMBIGUOUS.value == "DELIVERY_AMBIGUOUS"
    assert ReconciliationDisposition.NO_EFFECT_RETRY.value == "RESOLVED_NO_EFFECT_RETRY"


def test_trusted_evidence_is_committed_and_referenced() -> None:
    evidence = TrustedReconciliationEvidence(
        __import__("uuid").uuid4(),
        "a" * 64,
        "resolution-rf24",
        ReconciliationDisposition.NO_EFFECT_RETRY,
        True,
        ("evidence-rf24",),
    )
    assert evidence.committed and evidence.evidence_reference_ids == ("evidence-rf24",)

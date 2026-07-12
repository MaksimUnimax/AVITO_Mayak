from __future__ import annotations

from dataclasses import fields

import pytest

from mayak.modules.egress_routing import (
    EGRESS_SYNTHETIC_FIXTURE_IDS,
    EGRESS_SYNTHETIC_FIXTURES,
    DispatchAttempt,
    DispatchStatus,
    EgressAgent,
    PolicyBasedFallbackDecision,
    PolicyBasedFallbackStatus,
    RouteEvidenceReference,
    RouteEvidenceStatus,
    RouteFamily,
    RouteLease,
    RouteLeaseStatus,
    RouteQuarantineDecision,
    RouteQuarantineStatus,
    RouteReadinessDecision,
    RouteReadinessStatus,
    RouteReconciliationStatus,
    RouteRestrictionState,
    RouteRestrictionStatus,
    RouteSelectionDecision,
    RouteSelectionStatus,
    TransportAssignment,
    TransportAssignmentOutcome,
    TransportOutcomeStatus,
)


def test_heartbeat_and_stale_evidence_do_not_imply_readiness() -> None:
    stale_evidence = RouteEvidenceReference(
        evidence_reference_id="evidence-stale",
        evidence_status=RouteEvidenceStatus.STALE,
        authority_class="owner-observation",
        fingerprint="fingerprint-stale",
        observed_at_reference="ts-stale",
        notes=("stale",),
    )
    missing_evidence = RouteEvidenceReference(
        evidence_reference_id="evidence-missing",
        evidence_status=RouteEvidenceStatus.MISSING,
        authority_class="owner-observation",
        fingerprint="fingerprint-missing",
        observed_at_reference="ts-missing",
        notes=("missing",),
    )
    readiness = RouteReadinessDecision(
        decision_id="decision-readiness",
        route_id="route-01",
        readiness_status=RouteReadinessStatus.STALE_EVIDENCE,
        reason_codes=("evidence-not-ready",),
        evidence_reference_ids=(
            stale_evidence.evidence_reference_id,
            missing_evidence.evidence_reference_id,
        ),
        policy_reference=None,
    )

    assert readiness.readiness_status is RouteReadinessStatus.STALE_EVIDENCE
    assert stale_evidence.evidence_status is RouteEvidenceStatus.STALE
    assert missing_evidence.evidence_status is RouteEvidenceStatus.MISSING


def test_absence_of_policy_does_not_create_arbitrary_selected_route() -> None:
    decision = RouteSelectionDecision(
        decision_id="decision-selection",
        request_reference="request-selection",
        status=RouteSelectionStatus.NO_ELIGIBLE_ROUTE,
        selected_route_id=None,
        candidate_route_ids=("route-01", "route-02"),
        rejected_route_ids=("route-03",),
        reason_codes=("no-policy",),
        evidence_reference_ids=("evidence-01",),
        policy_reference=None,
    )

    assert decision.selected_route_id is None
    assert decision.status is RouteSelectionStatus.NO_ELIGIBLE_ROUTE


def test_lease_is_bounded_semantic_authorization() -> None:
    lease = RouteLease(
        lease_id="lease-01",
        route_id="route-01",
        agent_id="agent-01",
        requester_module="07-egress-routing",
        purpose="bounded-routing",
        capability_scope=("search",),
        status=RouteLeaseStatus.GRANTED,
        idempotency_key="idem-01",
        semantic_fingerprint="fingerprint-01",
        validity_reference="validity-01",
        restriction_snapshot=RouteRestrictionStatus.NONE,
        correlation_id="corr-01",
        causation_id="cause-01",
    )

    lease_field_names = {field.name for field in fields(RouteLease)}
    assert {"duration", "ttl", "expires_at"}.isdisjoint(lease_field_names)
    assert lease.validity_reference == "validity-01"


def test_assignment_contains_only_minimal_safe_references() -> None:
    assignment = TransportAssignment(
        assignment_id="assignment-01",
        lease_id="lease-01",
        route_id="route-01",
        agent_id="agent-01",
        purpose="bounded-routing",
        safe_request_reference="request-01",
        expected_response_class="unclassified",
        deadline_reference="deadline-01",
        route_policy_reference="policy-01",
        profile_reference="profile-01",
        redacted_config_reference="config-01",
        correlation_id="corr-01",
        causation_id="cause-01",
    )

    assert assignment.safe_request_reference == "request-01"
    assert assignment.profile_reference == "profile-01"
    assert assignment.redacted_config_reference == "config-01"

    field_names = {field.name for field in fields(TransportAssignment)}
    assert field_names == {
        "assignment_id",
        "lease_id",
        "route_id",
        "agent_id",
        "purpose",
        "safe_request_reference",
        "expected_response_class",
        "deadline_reference",
        "route_policy_reference",
        "profile_reference",
        "redacted_config_reference",
        "correlation_id",
        "causation_id",
    }


def test_assignment_has_no_account_beacon_tariff_scan_notification_db_or_secret_fields() -> None:
    field_names = {field.name for field in fields(TransportAssignment)}
    banned_tokens = {"account", "beacon", "tariff", "scan", "notification", "db", "secret"}
    assert all(token not in {name.lower() for name in field_names} for token in banned_tokens)


def test_explicit_restriction_and_captcha_are_not_empty_success_markers() -> None:
    restriction = RouteRestrictionState(
        restriction_id="restriction-01",
        route_id="route-01",
        status=RouteRestrictionStatus.RESTRICTED,
        reason_codes=("captcha", "explicit"),
        evidence_reference_ids=("evidence-01",),
        blocks_new_assignments=True,
        review_reference=None,
    )
    outcome = TransportAssignmentOutcome(
        outcome_id="outcome-01",
        assignment_id="assignment-01",
        attempt_id="attempt-01",
        status=TransportOutcomeStatus.CAPTCHA_OR_CHALLENGE,
        safe_response_reference=None,
        reason_codes=("captcha", "explicit"),
        evidence_reference_ids=("evidence-01",),
        reconciliation_status=RouteReconciliationStatus.NOT_REQUIRED,
        correlation_id="corr-01",
        causation_id="cause-01",
    )

    assert restriction.status is RouteRestrictionStatus.RESTRICTED
    assert restriction.blocks_new_assignments is True
    assert outcome.status is TransportOutcomeStatus.CAPTCHA_OR_CHALLENGE
    assert outcome.safe_response_reference is None


def test_transport_response_is_not_parser_success() -> None:
    outcome = TransportAssignmentOutcome(
        outcome_id="outcome-02",
        assignment_id="assignment-02",
        attempt_id="attempt-02",
        status=TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
        safe_response_reference="response-02",
        reason_codes=("transport-only",),
        evidence_reference_ids=("evidence-02",),
        reconciliation_status=RouteReconciliationStatus.NOT_REQUIRED,
        correlation_id="corr-02",
        causation_id="cause-02",
    )

    outcome_field_names = {field.name for field in fields(TransportAssignmentOutcome)}
    assert "parser_success" not in outcome_field_names
    assert "scan_success" not in outcome_field_names
    assert outcome.status is TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED
    assert outcome.safe_response_reference == "response-02"


def test_transport_outcomes_requiring_reconciliation_reject_not_required_state() -> None:
    with pytest.raises(ValueError):
        TransportAssignmentOutcome(
            outcome_id="outcome-03",
            assignment_id="assignment-03",
            attempt_id="attempt-03",
            status=TransportOutcomeStatus.DISPATCH_UNKNOWN,
            safe_response_reference=None,
            reason_codes=("dispatch-unknown",),
            evidence_reference_ids=("evidence-03",),
            reconciliation_status=RouteReconciliationStatus.NOT_REQUIRED,
            correlation_id="corr-03",
            causation_id="cause-03",
        )

    with pytest.raises(ValueError):
        TransportAssignmentOutcome(
            outcome_id="outcome-04",
            assignment_id="assignment-04",
            attempt_id="attempt-04",
            status=TransportOutcomeStatus.TRANSPORT_AMBIGUOUS,
            safe_response_reference=None,
            reason_codes=("transport-ambiguous",),
            evidence_reference_ids=("evidence-04",),
            reconciliation_status=RouteReconciliationStatus.NOT_REQUIRED,
            correlation_id="corr-04",
            causation_id="cause-04",
        )

    with pytest.raises(ValueError):
        TransportAssignmentOutcome(
            outcome_id="outcome-05",
            assignment_id="assignment-05",
            attempt_id="attempt-05",
            status=TransportOutcomeStatus.RECONCILIATION_REQUIRED,
            safe_response_reference=None,
            reason_codes=("reconciliation-required",),
            evidence_reference_ids=("evidence-05",),
            reconciliation_status=RouteReconciliationStatus.NOT_REQUIRED,
            correlation_id="corr-05",
            causation_id="cause-05",
        )


def test_resolved_transport_state_cannot_masquerade_as_unresolved_ambiguous_dispatch() -> None:
    with pytest.raises(ValueError):
        TransportAssignmentOutcome(
            outcome_id="outcome-06",
            assignment_id="assignment-06",
            attempt_id="attempt-06",
            status=TransportOutcomeStatus.DISPATCH_UNKNOWN,
            safe_response_reference=None,
            reason_codes=("dispatch-resolved",),
            evidence_reference_ids=("evidence-06",),
            reconciliation_status=RouteReconciliationStatus.RESOLVED_SENT,
            correlation_id="corr-06",
            causation_id="cause-06",
        )

    with pytest.raises(ValueError):
        TransportAssignmentOutcome(
            outcome_id="outcome-07",
            assignment_id="assignment-07",
            attempt_id="attempt-07",
            status=TransportOutcomeStatus.TRANSPORT_AMBIGUOUS,
            safe_response_reference=None,
            reason_codes=("transport-resolved",),
            evidence_reference_ids=("evidence-07",),
            reconciliation_status=RouteReconciliationStatus.RESOLVED_NOT_SENT,
            correlation_id="corr-07",
            causation_id="cause-07",
        )

    accepted_dispatch_unknown = TransportAssignmentOutcome(
        outcome_id="outcome-08",
        assignment_id="assignment-08",
        attempt_id="attempt-08",
        status=TransportOutcomeStatus.DISPATCH_UNKNOWN,
        safe_response_reference=None,
        reason_codes=("dispatch-unresolved",),
        evidence_reference_ids=("evidence-08",),
        reconciliation_status=RouteReconciliationStatus.REQUIRED,
        correlation_id="corr-08",
        causation_id="cause-08",
    )
    accepted_transport_ambiguous = TransportAssignmentOutcome(
        outcome_id="outcome-09",
        assignment_id="assignment-09",
        attempt_id="attempt-09",
        status=TransportOutcomeStatus.TRANSPORT_AMBIGUOUS,
        safe_response_reference=None,
        reason_codes=("transport-unresolved",),
        evidence_reference_ids=("evidence-09",),
        reconciliation_status=RouteReconciliationStatus.REMAINS_AMBIGUOUS,
        correlation_id="corr-09",
        causation_id="cause-09",
    )

    assert accepted_dispatch_unknown.reconciliation_status is RouteReconciliationStatus.REQUIRED
    assert (
        accepted_transport_ambiguous.reconciliation_status
        is RouteReconciliationStatus.REMAINS_AMBIGUOUS
    )


def test_ambiguous_dispatch_requires_reconciliation_and_does_not_enable_fallback() -> None:
    attempt = DispatchAttempt(
        attempt_id="attempt-01",
        assignment_id="assignment-01",
        lease_id="lease-01",
        route_id="route-01",
        agent_id="agent-01",
        dispatch_status=DispatchStatus.UNKNOWN,
        attempt_ordinal=1,
        outcome_reference=None,
        reconciliation_required=True,
        correlation_id="corr-01",
        causation_id="cause-01",
    )

    with pytest.raises(ValueError):
        DispatchAttempt(
            attempt_id="attempt-02",
            assignment_id="assignment-01",
            lease_id="lease-01",
            route_id="route-01",
            agent_id="agent-01",
            dispatch_status=DispatchStatus.UNKNOWN,
            attempt_ordinal=1,
            outcome_reference=None,
            reconciliation_required=False,
            correlation_id="corr-01",
            causation_id="cause-01",
        )

    with pytest.raises(ValueError):
        PolicyBasedFallbackDecision(
            decision_id="decision-fallback",
            request_reference="request-01",
            status=PolicyBasedFallbackStatus.ALLOWED,
            policy_reference="policy-01",
            from_route_id="route-a",
            to_route_id="route-b",
            reason_codes=("ambiguous",),
            evidence_reference_ids=("evidence-01",),
            bounded_attempt_reference="attempt-01",
            original_failure_reference="failure-01",
            reconciliation_status=RouteReconciliationStatus.REQUIRED,
        )

    assert attempt.reconciliation_required is True


def test_quarantine_blocks_new_assignments_and_auto_unquarantine_is_impossible() -> None:
    restriction = RouteRestrictionState(
        restriction_id="restriction-02",
        route_id="route-02",
        status=RouteRestrictionStatus.QUARANTINED,
        reason_codes=("quarantined",),
        evidence_reference_ids=("evidence-02",),
        blocks_new_assignments=True,
        review_reference=None,
    )
    decision = RouteQuarantineDecision(
        decision_id="decision-quarantine",
        route_id="route-02",
        status=RouteQuarantineStatus.QUARANTINED,
        reason_codes=("quarantined",),
        evidence_reference_ids=("evidence-02",),
        blocks_new_assignments=True,
        automatic_release_allowed=False,
        review_reference=None,
    )

    with pytest.raises(ValueError):
        RouteQuarantineDecision(
            decision_id="decision-quarantine-bad",
            route_id="route-02",
            status=RouteQuarantineStatus.QUARANTINED,
            reason_codes=("quarantined",),
            evidence_reference_ids=("evidence-02",),
            blocks_new_assignments=True,
            automatic_release_allowed=True,
            review_reference=None,
        )

    assert restriction.blocks_new_assignments is True
    assert decision.automatic_release_allowed is False


def test_agent_has_no_primary_db_access_field() -> None:
    field_names = {field.name for field in fields(EgressAgent)}
    assert "primary_db" not in field_names
    assert "primary_database" not in field_names


def test_route_selection_authority_remains_egress_only() -> None:
    selected = RouteSelectionDecision(
        decision_id="decision-egress",
        request_reference="request-egress",
        status=RouteSelectionStatus.SELECTED,
        selected_route_id="route-01",
        candidate_route_ids=("route-01",),
        rejected_route_ids=(),
        reason_codes=("policy-approved",),
        evidence_reference_ids=("evidence-01",),
        policy_reference="policy-01",
    )

    assert selected.policy_reference == "policy-01"
    assert selected.selected_route_id == "route-01"


def test_fixture_ids_are_exact_order_and_unique() -> None:
    assert EGRESS_SYNTHETIC_FIXTURE_IDS == (
        "FX-ER-AGENT-REGISTRATION-BLOCKED-001",
        "FX-ER-REGISTERED-NOT-READY-001",
        "FX-ER-HEARTBEAT-NOT-READINESS-001",
        "FX-ER-RELEASE-MISMATCH-BLOCKS-001",
        "FX-ER-CAPABILITY-UNSUPPORTED-001",
        "FX-ER-CAPABILITY-EVIDENCE-STALE-001",
        "FX-ER-NO-POLICY-NO-ARBITRARY-SELECTION-001",
        "FX-ER-LEASE-GRANTED-001",
        "FX-ER-LEASE-REPLAY-NO-EXTENSION-001",
        "FX-ER-LEASE-IDEMPOTENCY-MISMATCH-001",
        "FX-ER-LEASE-EXPIRED-NO-DISPATCH-001",
        "FX-ER-LEASE-REVOKED-NO-DISPATCH-001",
        "FX-ER-DISPATCH-NOT-SENT-001",
        "FX-ER-DISPATCH-AMBIGUOUS-RECONCILE-001",
        "FX-ER-RECEIVED-NOT-SENT-001",
        "FX-ER-SENT-RESPONSE-NOT-PARSER-SUCCESS-001",
        "FX-ER-EXPLICIT-REJECTION-NOT-EMPTY-001",
        "FX-ER-CAPTCHA-NOT-EMPTY-001",
        "FX-ER-MALFORMED-NOT-PARSER-SUCCESS-001",
        "FX-ER-ROUTE-FAILURE-NOT-PARSER-SUCCESS-001",
        "FX-ER-QUARANTINE-BLOCKS-NEW-LEASE-001",
        "FX-ER-NO-AUTO-UNQUARANTINE-001",
        "FX-ER-NO-AGENT-FALLBACK-001",
        "FX-ER-AMBIGUOUS-NO-FALLBACK-001",
        "FX-ER-CROSS-ENVIRONMENT-REJECT-001",
        "FX-ER-FOREIGN-RESOURCE-REJECT-001",
        "FX-ER-NO-PUBLIC-INBOUND-001",
        "FX-ER-NO-PRIMARY-DATABASE-001",
        "FX-ER-MINIMUM-ASSIGNMENT-PAYLOAD-001",
        "FX-ER-SECRET-REFERENCE-ONLY-001",
        "FX-ER-BATCH-PER-ASSIGNMENT-OUTCOME-001",
        "FX-ER-RECONCILIATION-REMAINS-AMBIGUOUS-001",
        "FX-ER-OD011-NO-CADENCE-DEFAULT-001",
        "FX-ER-OD013-RETENTION-BLOCKED-001",
    )
    assert len(EGRESS_SYNTHETIC_FIXTURE_IDS) == len(set(EGRESS_SYNTHETIC_FIXTURE_IDS))


def test_all_fixtures_are_synthetic_and_cover_required_semantics() -> None:
    assert len(EGRESS_SYNTHETIC_FIXTURES) == 34
    fixture_map = {fixture.fixture_id: fixture for fixture in EGRESS_SYNTHETIC_FIXTURES}
    assert set(fixture_map) == set(EGRESS_SYNTHETIC_FIXTURE_IDS)
    assert all(
        fixture.fixture_id in EGRESS_SYNTHETIC_FIXTURE_IDS for fixture in EGRESS_SYNTHETIC_FIXTURES
    )
    assert all(
        fixture.route_family in {None, *RouteFamily} for fixture in EGRESS_SYNTHETIC_FIXTURES
    )
    assert all(
        ref.startswith("SAFE-ER-")
        for fixture in EGRESS_SYNTHETIC_FIXTURES
        for ref in fixture.safe_reference_ids
    )
    assert all(
        "avito.ru" not in fixture.summary.lower()
        and "http://" not in fixture.summary.lower()
        and "https://" not in fixture.summary.lower()
        for fixture in EGRESS_SYNTHETIC_FIXTURES
    )

    assert "proof-gated" in fixture_map["FX-ER-AGENT-REGISTRATION-BLOCKED-001"].summary.lower()
    assert "provider-unselected" in fixture_map["FX-ER-REGISTERED-NOT-READY-001"].summary.lower()
    assert "development-only" in fixture_map["FX-ER-HEARTBEAT-NOT-READINESS-001"].summary.lower()
    assert "proof-gated" in fixture_map["FX-ER-RELEASE-MISMATCH-BLOCKS-001"].summary.lower()
    assert "proof-gated" in fixture_map["FX-ER-CAPABILITY-UNSUPPORTED-001"].summary.lower()
    assert (
        "owner-evidence-only" in fixture_map["FX-ER-CAPABILITY-EVIDENCE-STALE-001"].summary.lower()
    )
    assert (
        "no arbitrary selection"
        in fixture_map["FX-ER-NO-POLICY-NO-ARBITRARY-SELECTION-001"].summary.lower()
    )
    assert (
        "unavailable outcome" in fixture_map["FX-ER-LEASE-EXPIRED-NO-DISPATCH-001"].summary.lower()
    )
    assert (
        "restricted outcome" in fixture_map["FX-ER-LEASE-REVOKED-NO-DISPATCH-001"].summary.lower()
    )
    assert (
        "ambiguous outcome" in fixture_map["FX-ER-DISPATCH-AMBIGUOUS-RECONCILE-001"].summary.lower()
    )
    assert "captcha" in fixture_map["FX-ER-CAPTCHA-NOT-EMPTY-001"].summary.lower()
    assert "no auto-unquarantine" in fixture_map["FX-ER-NO-AUTO-UNQUARANTINE-001"].summary.lower()
    assert (
        "no primary database access" in fixture_map["FX-ER-NO-PRIMARY-DATABASE-001"].summary.lower()
    )
    assert (
        "minimum bounded assignment"
        in fixture_map["FX-ER-MINIMUM-ASSIGNMENT-PAYLOAD-001"].summary.lower()
    )
    assert "no cadence value" in fixture_map["FX-ER-OD011-NO-CADENCE-DEFAULT-001"].summary.lower()
    assert "no retention value" in fixture_map["FX-ER-OD013-RETENTION-BLOCKED-001"].summary.lower()

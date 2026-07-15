from __future__ import annotations

from dataclasses import fields
from typing import Any

from mayak.modules.egress_routing import (
    RouteLease,
    RouteLeaseAuthority,
    RouteLeaseAuthorizationBoundary,
    RouteLeaseStatus,
    RouteReconciliationStatus,
    RouteRestrictionStatus,
)
from mayak.modules.egress_routing.lease import (
    _RESOLVED_RECONCILIATION_STATUSES,
    _RESTRICTION_STATUSES_BLOCKING_DISPATCH,
    _UNRESOLVED_RECONCILIATION_STATUSES,
)


def _lease_kwargs(
    *,
    lease_id: str = "lease-01",
    route_id: str = "route-01",
    agent_id: str = "agent-01",
    requester_module: str = "07-egress-routing",
    purpose: str = "search",
    capability_scope: tuple[str, ...] = ("search",),
    status: RouteLeaseStatus = RouteLeaseStatus.GRANTED,
    restriction_snapshot: RouteRestrictionStatus = RouteRestrictionStatus.NONE,
    idempotency_key: str = "idempotency-01",
    semantic_fingerprint: str = "fingerprint-01",
    validity_reference: str = "validity-01",
    correlation_id: str = "correlation-01",
    causation_id: str = "causation-01",
) -> RouteLease:
    return RouteLease(
        lease_id=lease_id,
        route_id=route_id,
        agent_id=agent_id,
        requester_module=requester_module,
        purpose=purpose,
        capability_scope=capability_scope,
        status=status,
        idempotency_key=idempotency_key,
        semantic_fingerprint=semantic_fingerprint,
        validity_reference=validity_reference,
        restriction_snapshot=restriction_snapshot,
        correlation_id=correlation_id,
        causation_id=causation_id,
    )


def _mock_selection_boundary(**kwargs: Any) -> Any:
    from mayak.modules.egress_routing.selection import ServerRouteSelectionBoundary
    return ServerRouteSelectionBoundary(**kwargs)


def _mock_candidate(**kwargs: Any) -> Any:
    from mayak.modules.egress_routing.selection import RouteCandidateEvaluation
    return RouteCandidateEvaluation(**kwargs)


def test_only_egress_server_is_lease_authority() -> None:
    assert len(RouteLeaseAuthority) == 1
    assert RouteLeaseAuthority.EGRESS_ROUTING_SERVER.value == "EGRESS_ROUTING_SERVER"


def test_requested_does_not_authorize_route_use() -> None:
    lease = _lease_kwargs(status=RouteLeaseStatus.REQUESTED)
    assert lease.status is RouteLeaseStatus.REQUESTED
    assert lease.status is not RouteLeaseStatus.GRANTED


def test_rejected_has_no_dispatch_authorization() -> None:
    lease = _lease_kwargs(status=RouteLeaseStatus.REJECTED)
    assert lease.status is RouteLeaseStatus.REJECTED
    assert lease.status is not RouteLeaseStatus.GRANTED


def test_granted_semantically_authorizes_one_dispatch() -> None:
    lease = _lease_kwargs(status=RouteLeaseStatus.GRANTED)
    assert lease.status is RouteLeaseStatus.GRANTED


def test_granted_does_not_create_assignment() -> None:
    lease = _lease_kwargs(status=RouteLeaseStatus.GRANTED)
    field_names = {f.name for f in fields(lease)}
    assert "assignment_id" not in field_names


def test_granted_does_not_prove_dispatch() -> None:
    lease = _lease_kwargs(status=RouteLeaseStatus.GRANTED)
    assert lease.status is not RouteLeaseStatus.DISPATCHED


def test_granted_does_not_prove_send() -> None:
    lease = _lease_kwargs(status=RouteLeaseStatus.GRANTED)
    assert lease.status is not RouteLeaseStatus.IN_USE


def test_granted_does_not_prove_response() -> None:
    lease = _lease_kwargs(status=RouteLeaseStatus.GRANTED)
    assert lease.status is not RouteLeaseStatus.COMPLETED


def test_granted_does_not_prove_parser_success() -> None:
    lease = _lease_kwargs(status=RouteLeaseStatus.GRANTED)
    assert lease.status is not RouteLeaseStatus.COMPLETED


def test_granted_does_not_prove_scan_success() -> None:
    lease = _lease_kwargs(status=RouteLeaseStatus.GRANTED)
    assert lease.status is not RouteLeaseStatus.COMPLETED


def test_dispatched_does_not_authorize_second_new_dispatch() -> None:
    lease = _lease_kwargs(status=RouteLeaseStatus.DISPATCHED)
    assert lease.status is RouteLeaseStatus.DISPATCHED
    assert lease.status is not RouteLeaseStatus.GRANTED


def test_in_use_does_not_authorize_second_new_dispatch() -> None:
    lease = _lease_kwargs(status=RouteLeaseStatus.IN_USE)
    assert lease.status is RouteLeaseStatus.IN_USE
    assert lease.status is not RouteLeaseStatus.GRANTED


def test_completed_does_not_authorize_another_dispatch() -> None:
    lease = _lease_kwargs(status=RouteLeaseStatus.COMPLETED)
    assert lease.status is RouteLeaseStatus.COMPLETED
    assert lease.status is not RouteLeaseStatus.GRANTED


def test_expired_blocks_dispatch() -> None:
    lease = _lease_kwargs(status=RouteLeaseStatus.EXPIRED)
    assert lease.status is RouteLeaseStatus.EXPIRED
    assert lease.status is not RouteLeaseStatus.GRANTED


def test_revoked_blocks_dispatch() -> None:
    lease = _lease_kwargs(status=RouteLeaseStatus.REVOKED)
    assert lease.status is RouteLeaseStatus.REVOKED
    assert lease.status is not RouteLeaseStatus.GRANTED


def test_failed_blocks_dispatch() -> None:
    lease = _lease_kwargs(status=RouteLeaseStatus.FAILED)
    assert lease.status is RouteLeaseStatus.FAILED
    assert lease.status is not RouteLeaseStatus.GRANTED


def test_ambiguous_is_reconcile_first() -> None:
    lease = _lease_kwargs(status=RouteLeaseStatus.AMBIGUOUS)
    assert lease.status is RouteLeaseStatus.AMBIGUOUS
    assert lease.status is not RouteLeaseStatus.GRANTED


def test_reconciliation_required_is_reconcile_first() -> None:
    lease = _lease_kwargs(status=RouteLeaseStatus.RECONCILIATION_REQUIRED)
    assert lease.status is RouteLeaseStatus.RECONCILIATION_REQUIRED
    assert lease.status is not RouteLeaseStatus.GRANTED


def test_restricted_snapshot_blocks_active_use() -> None:
    for status in _RESTRICTION_STATUSES_BLOCKING_DISPATCH:
        lease = _lease_kwargs(
            status=RouteLeaseStatus.GRANTED,
            restriction_snapshot=status,
        )
        assert lease.restriction_snapshot is status
        assert lease.restriction_snapshot is not RouteRestrictionStatus.NONE


def test_lease_preserves_selected_route_identity() -> None:
    lease = _lease_kwargs(route_id="selected-route-42")
    assert lease.route_id == "selected-route-42"


def test_lease_preserves_selected_agent_identity() -> None:
    lease = _lease_kwargs(agent_id="agent-42")
    assert lease.agent_id == "agent-42"


def test_lease_preserves_request_context() -> None:
    lease = _lease_kwargs(
        requester_module="07-egress-routing",
        purpose="search",
        capability_scope=("search", "dispatch"),
    )
    assert lease.requester_module == "07-egress-routing"
    assert lease.purpose == "search"
    assert lease.capability_scope == ("search", "dispatch")


def test_lease_contains_no_account_beacon_state() -> None:
    lease = _lease_kwargs()
    field_names = {f.name for f in fields(lease)}
    forbidden_fields = {"account", "beacon", "tariff", "payment", "listing", "notification"}
    assert field_names.isdisjoint(forbidden_fields)


def test_lease_contains_no_raw_credential_cookie_session() -> None:
    lease = _lease_kwargs()
    field_names = {f.name for f in fields(lease)}
    forbidden_fields = {"cookie", "session_value", "credential_value"}
    assert field_names.isdisjoint(forbidden_fields)


def test_lease_does_not_choose_provider_proxy_vpn() -> None:
    lease = _lease_kwargs()
    field_names = {f.name for f in fields(lease)}
    forbidden_fields = {"provider", "proxy", "vpn", "tunnel"}
    assert field_names.isdisjoint(forbidden_fields)


def test_lease_does_not_implement_duration_renewal_retry() -> None:
    lease = _lease_kwargs()
    field_names = {f.name for f in fields(lease)}
    forbidden_fields = {"duration", "renewal", "retry_count", "retry_delay", "backoff"}
    assert field_names.isdisjoint(forbidden_fields)


def test_lease_does_not_mutate_selection_or_candidate_records() -> None:
    lease = _lease_kwargs()
    field_names = {f.name for f in fields(lease)}
    forbidden_fields = {"selection", "selected_candidate"}
    assert field_names.isdisjoint(forbidden_fields)


class TestBoundarySemantics:
    def test_granted_authorizes_one_new_dispatch(self) -> None:
        assert RouteLeaseStatus.GRANTED is not RouteLeaseStatus.DISPATCHED
        assert RouteLeaseStatus.GRANTED is not RouteLeaseStatus.IN_USE
        assert RouteLeaseStatus.GRANTED is not RouteLeaseStatus.COMPLETED

    def test_dispatched_prevents_second_new_dispatch(self) -> None:
        assert RouteLeaseStatus.DISPATCHED is not RouteLeaseStatus.GRANTED

    def test_in_use_prevents_second_new_dispatch(self) -> None:
        assert RouteLeaseStatus.IN_USE is not RouteLeaseStatus.GRANTED

    def test_completed_prevents_another_dispatch(self) -> None:
        assert RouteLeaseStatus.COMPLETED is not RouteLeaseStatus.GRANTED

    def test_expired_prevents_dispatch(self) -> None:
        assert RouteLeaseStatus.EXPIRED is not RouteLeaseStatus.GRANTED

    def test_revoked_prevents_dispatch(self) -> None:
        assert RouteLeaseStatus.REVOKED is not RouteLeaseStatus.GRANTED

    def test_failed_prevents_dispatch(self) -> None:
        assert RouteLeaseStatus.FAILED is not RouteLeaseStatus.GRANTED

    def test_ambiguous_prevents_dispatch(self) -> None:
        assert RouteLeaseStatus.AMBIGUOUS is not RouteLeaseStatus.GRANTED

    def test_reconciliation_required_prevents_dispatch(self) -> None:
        assert RouteLeaseStatus.RECONCILIATION_REQUIRED is not RouteLeaseStatus.GRANTED


class TestReconciliationStatusSets:
    def test_resolved_statuses_defined(self) -> None:
        assert RouteReconciliationStatus.NOT_REQUIRED in _RESOLVED_RECONCILIATION_STATUSES
        assert RouteReconciliationStatus.RESOLVED_NOT_SENT in _RESOLVED_RECONCILIATION_STATUSES
        assert RouteReconciliationStatus.RESOLVED_SENT in _RESOLVED_RECONCILIATION_STATUSES
        assert RouteReconciliationStatus.RESOLVED_TERMINAL in _RESOLVED_RECONCILIATION_STATUSES

    def test_unresolved_statuses_defined(self) -> None:
        assert RouteReconciliationStatus.REQUIRED in _UNRESOLVED_RECONCILIATION_STATUSES
        assert RouteReconciliationStatus.PENDING in _UNRESOLVED_RECONCILIATION_STATUSES
        assert RouteReconciliationStatus.REMAINS_AMBIGUOUS in _UNRESOLVED_RECONCILIATION_STATUSES
        assert (
            RouteReconciliationStatus.MANUAL_REVIEW_REQUIRED
            in _UNRESOLVED_RECONCILIATION_STATUSES
        )

    def test_resolved_and_unresolved_are_disjoint(self) -> None:
        assert _RESOLVED_RECONCILIATION_STATUSES.isdisjoint(_UNRESOLVED_RECONCILIATION_STATUSES)


class TestRestrictionBlocking:
    def test_degraded_blocks_dispatch(self) -> None:
        assert RouteRestrictionStatus.DEGRADED in _RESTRICTION_STATUSES_BLOCKING_DISPATCH

    def test_restricted_blocks_dispatch(self) -> None:
        assert RouteRestrictionStatus.RESTRICTED in _RESTRICTION_STATUSES_BLOCKING_DISPATCH

    def test_quarantined_blocks_dispatch(self) -> None:
        assert RouteRestrictionStatus.QUARANTINED in _RESTRICTION_STATUSES_BLOCKING_DISPATCH

    def test_suspended_blocks_dispatch(self) -> None:
        assert RouteRestrictionStatus.SUSPENDED in _RESTRICTION_STATUSES_BLOCKING_DISPATCH

    def test_retired_blocks_dispatch(self) -> None:
        assert RouteRestrictionStatus.RETIRED in _RESTRICTION_STATUSES_BLOCKING_DISPATCH

    def test_none_does_not_block_dispatch(self) -> None:
        assert RouteRestrictionStatus.NONE not in _RESTRICTION_STATUSES_BLOCKING_DISPATCH


class TestBoundaryRecordInvariants:
    def test_boundary_has_no_assignment_id(self) -> None:
        field_names = tuple(f.name for f in fields(RouteLeaseAuthorizationBoundary))
        assert "assignment_id" not in field_names

    def test_boundary_has_no_attempt_id(self) -> None:
        field_names = tuple(f.name for f in fields(RouteLeaseAuthorizationBoundary))
        assert "attempt_id" not in field_names

    def test_boundary_has_no_dispatch_status(self) -> None:
        field_names = tuple(f.name for f in fields(RouteLeaseAuthorizationBoundary))
        assert "dispatch_status" not in field_names

    def test_boundary_has_no_transport_outcome(self) -> None:
        field_names = tuple(f.name for f in fields(RouteLeaseAuthorizationBoundary))
        assert "transport_outcome" not in field_names

    def test_boundary_has_no_duration(self) -> None:
        field_names = tuple(f.name for f in fields(RouteLeaseAuthorizationBoundary))
        assert "duration" not in field_names

    def test_boundary_has_no_renewal(self) -> None:
        field_names = tuple(f.name for f in fields(RouteLeaseAuthorizationBoundary))
        assert "renewal" not in field_names

    def test_boundary_has_no_retry(self) -> None:
        field_names = tuple(f.name for f in fields(RouteLeaseAuthorizationBoundary))
        assert "retry_count" not in field_names
        assert "retry_delay" not in field_names
        assert "backoff" not in field_names

    def test_boundary_has_no_provider(self) -> None:
        field_names = tuple(f.name for f in fields(RouteLeaseAuthorizationBoundary))
        assert "provider" not in field_names

    def test_boundary_has_no_host_ip_port(self) -> None:
        field_names = tuple(f.name for f in fields(RouteLeaseAuthorizationBoundary))
        assert "host" not in field_names
        assert "ip" not in field_names
        assert "port" not in field_names

    def test_boundary_has_no_proxy_vpn_tunnel(self) -> None:
        field_names = tuple(f.name for f in fields(RouteLeaseAuthorizationBoundary))
        assert "proxy" not in field_names
        assert "vpn" not in field_names
        assert "tunnel" not in field_names


class TestIdempotencyPreservation:
    def test_lease_preserves_idempotency_key(self) -> None:
        lease = _lease_kwargs(idempotency_key="idem-42")
        assert lease.idempotency_key == "idem-42"

    def test_lease_preserves_semantic_fingerprint(self) -> None:
        lease = _lease_kwargs(semantic_fingerprint="fp-42")
        assert lease.semantic_fingerprint == "fp-42"

    def test_lease_preserves_validity_reference(self) -> None:
        lease = _lease_kwargs(validity_reference="validity-42")
        assert lease.validity_reference == "validity-42"


class TestRouteLeaseStatusUnchanged:
    def test_all_statuses_present(self) -> None:
        expected_names = {
            "REQUESTED", "REJECTED", "GRANTED", "DISPATCHED", "IN_USE",
            "COMPLETED", "EXPIRED", "REVOKED", "AMBIGUOUS",
            "RECONCILIATION_REQUIRED", "FAILED",
        }
        actual_names = {m.name for m in RouteLeaseStatus}
        assert actual_names == expected_names

    def test_status_count(self) -> None:
        assert len(RouteLeaseStatus) == 11

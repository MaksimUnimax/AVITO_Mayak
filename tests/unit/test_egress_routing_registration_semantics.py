from __future__ import annotations

from dataclasses import fields, replace
from typing import Any

import pytest

from mayak.modules.egress_routing import (
    AgentLifecycleStatus,
    EgressAgent,
    EgressRoute,
    RouteEvidenceStatus,
    RouteFamily,
    RouteLifecycleStatus,
    SessionPolicyStatus,
)
from mayak.modules.egress_routing.registration import (
    AgentRegistration,
    AgentRegistrationStatus,
    AgentRouteAssociation,
    AgentRouteAssociationStatus,
    AgentRouteRegistrationBoundary,
    RouteRegistration,
    RouteRegistrationStatus,
)


def _agent_kwargs() -> dict[str, Any]:
    return {
        "agent_id": "agent-01",
        "agent_class": "LinuxReferenceStyleAgent",
        "environment_id": "env-01",
        "lifecycle_status": AgentLifecycleStatus.ONLINE_UNREADY,
        "trust_scope": ("egress", "safe-routing"),
        "source_release_reference": "release-20260712",
        "credential_reference": "opaque-credential-ref",
        "evidence_reference_ids": ("evidence-agent-01",),
    }


def _route_kwargs() -> dict[str, Any]:
    return {
        "route_id": "route-01",
        "route_family": RouteFamily.LINUX_REFERENCE_STYLE_ROUTE,
        "environment_id": "env-01",
        "agent_id": "agent-01",
        "purpose_scope": ("search", "dispatch"),
        "capability_ids": ("cap-01",),
        "lifecycle_status": RouteLifecycleStatus.REGISTERED,
        "evidence_reference_ids": ("evidence-route-01",),
    }


def _agent_registration_kwargs(
    *,
    status: AgentRegistrationStatus = AgentRegistrationStatus.REGISTERED,
    purpose_scope: tuple[str, ...] = ("egress", "safe-routing"),
    trust_scope: tuple[str, ...] = ("egress", "safe-routing"),
    credential_reference: str | None = "opaque-credential-ref",
    reason_codes: tuple[str, ...] = (),
    evidence_reference_ids: tuple[str, ...] = ("evidence-agent-registration-01",),
) -> dict[str, Any]:
    return {
        "registration_id": "agent-registration-01",
        "agent_id": "agent-01",
        "environment_id": "env-01",
        "agent_class": "LinuxReferenceStyleAgent",
        "accountable_owner_reference": "owner-01",
        "purpose_scope": purpose_scope,
        "trust_scope": trust_scope,
        "source_release_reference": "release-20260712",
        "credential_reference": credential_reference,
        "connectivity_boundary_reference": "connectivity-boundary-01",
        "isolation_boundary_reference": "isolation-boundary-01",
        "privacy_boundary_reference": "privacy-boundary-01",
        "replaceable_execution_dependency": True,
        "primary_database_access_allowed": False,
        "business_state_ownership_allowed": False,
        "public_unauthenticated_inbound_allowed": False,
        "foreign_resource_reuse_allowed": False,
        "arbitrary_command_execution_allowed": False,
        "status": status,
        "reason_codes": reason_codes,
        "evidence_reference_ids": evidence_reference_ids,
    }


def _route_registration_kwargs(
    *,
    status: RouteRegistrationStatus = RouteRegistrationStatus.REGISTERED,
    route_family: RouteFamily = RouteFamily.LINUX_REFERENCE_STYLE_ROUTE,
    purpose_scope: tuple[str, ...] = ("search", "dispatch"),
    capability_ids: tuple[str, ...] = ("cap-01",),
    unsupported_classes: tuple[str, ...] = (),
    evidence_status: RouteEvidenceStatus = RouteEvidenceStatus.CURRENT,
    session_policy_status: SessionPolicyStatus = SessionPolicyStatus.APPROVED_REFERENCE_ONLY,
    restriction_reference: str | None = None,
    selection_policy_reference: str | None = None,
    reason_codes: tuple[str, ...] = (),
    evidence_reference_ids: tuple[str, ...] = ("evidence-route-registration-01",),
) -> dict[str, Any]:
    return {
        "registration_id": "route-registration-01",
        "route_id": "route-01",
        "agent_id": "agent-01",
        "agent_registration_id": "agent-registration-01",
        "environment_id": "env-01",
        "source_release_reference": "release-20260712",
        "route_family": route_family,
        "purpose_scope": purpose_scope,
        "capability_ids": capability_ids,
        "unsupported_classes": unsupported_classes,
        "evidence_status": evidence_status,
        "session_policy_status": session_policy_status,
        "restriction_reference": restriction_reference,
        "selection_policy_reference": selection_policy_reference,
        "privacy_boundary_reference": "privacy-boundary-01",
        "status": status,
        "reason_codes": reason_codes,
        "evidence_reference_ids": evidence_reference_ids,
    }


def _association_kwargs(
    *,
    status: AgentRouteAssociationStatus = AgentRouteAssociationStatus.ACTIVE,
    purpose_scope: tuple[str, ...] = ("search", "dispatch"),
    reason_codes: tuple[str, ...] = (),
    evidence_reference_ids: tuple[str, ...] = ("evidence-association-01",),
) -> dict[str, Any]:
    return {
        "association_id": "association-01",
        "agent_id": "agent-01",
        "route_id": "route-01",
        "environment_id": "env-01",
        "agent_registration_id": "agent-registration-01",
        "route_registration_id": "route-registration-01",
        "purpose_scope": purpose_scope,
        "status": status,
        "reason_codes": reason_codes,
        "evidence_reference_ids": evidence_reference_ids,
    }


def _boundary_kwargs() -> dict[str, Any]:
    return {
        "boundary_id": "boundary-01",
        "agent": EgressAgent(**_agent_kwargs()),
        "agent_registration": AgentRegistration(**_agent_registration_kwargs()),
        "route": EgressRoute(**_route_kwargs()),
        "route_registration": RouteRegistration(**_route_registration_kwargs()),
        "association": AgentRouteAssociation(**_association_kwargs()),
    }


def test_logical_registration_does_not_mean_connectivity_or_readiness() -> None:
    boundary = AgentRouteRegistrationBoundary(**_boundary_kwargs())

    assert boundary.agent.lifecycle_status is AgentLifecycleStatus.ONLINE_UNREADY
    assert boundary.route.lifecycle_status is RouteLifecycleStatus.REGISTERED
    assert boundary.agent_registration.status is AgentRegistrationStatus.REGISTERED
    assert boundary.route_registration.status is RouteRegistrationStatus.REGISTERED
    assert "connectivity_status" not in {field.name for field in fields(AgentRegistration)}
    assert "readiness_status" not in {field.name for field in fields(RouteRegistration)}
    assert "selected_route_id" not in {field.name for field in fields(RouteRegistration)}


def test_agent_is_replaceable_and_cannot_own_business_state() -> None:
    agent_registration = AgentRegistration(**_agent_registration_kwargs())

    assert agent_registration.replaceable_execution_dependency is True
    assert agent_registration.primary_database_access_allowed is False
    assert agent_registration.business_state_ownership_allowed is False
    assert agent_registration.public_unauthenticated_inbound_allowed is False
    assert agent_registration.foreign_resource_reuse_allowed is False
    assert agent_registration.arbitrary_command_execution_allowed is False

    field_names = {field.name for field in fields(AgentRegistration)}
    assert "account" not in {name.lower() for name in field_names}
    assert "beacon" not in {name.lower() for name in field_names}
    assert "scan" not in {name.lower() for name in field_names}
    assert "notification" not in {name.lower() for name in field_names}
    assert "database" not in {name.lower() for name in field_names}


def test_registered_route_without_selection_policy_is_not_selected_route() -> None:
    route_registration = RouteRegistration(
        **{**_route_registration_kwargs(selection_policy_reference=None)}
    )

    assert route_registration.selection_policy_reference is None
    assert "selected_route_id" not in {field.name for field in fields(RouteRegistration)}
    assert "fallback_order" not in {field.name for field in fields(RouteRegistration)}


@pytest.mark.parametrize(
    "evidence_status",
    (
        RouteEvidenceStatus.STALE,
        RouteEvidenceStatus.MISSING,
        RouteEvidenceStatus.DISPUTED,
        RouteEvidenceStatus.UNPROVEN,
        RouteEvidenceStatus.WITHDRAWN,
    ),
)
def test_stale_missing_disputed_unproven_withdrawn_evidence_does_not_create_registered_route(
    evidence_status: RouteEvidenceStatus,
) -> None:
    with pytest.raises(ValueError):
        RouteRegistration(**{**_route_registration_kwargs(evidence_status=evidence_status)})


def test_unsupported_route_stays_explicit_not_capability_success() -> None:
    route_registration = RouteRegistration(
        **{
            **_route_registration_kwargs(
                status=RouteRegistrationStatus.UNSUPPORTED,
                unsupported_classes=("billing",),
                reason_codes=("unsupported",),
            )
        }
    )

    assert route_registration.status is RouteRegistrationStatus.UNSUPPORTED
    assert route_registration.unsupported_classes == ("billing",)
    assert route_registration.evidence_status is RouteEvidenceStatus.CURRENT


def test_route_registration_does_not_create_lease_or_assignment() -> None:
    route_registration = RouteRegistration(**_route_registration_kwargs())

    field_names = {field.name for field in fields(RouteRegistration)}
    assert "lease_id" not in field_names
    assert "assignment_id" not in field_names
    assert "lease" not in field_names
    assert "assignment" not in field_names
    assert route_registration.registration_id == "route-registration-01"


def test_windows_and_extension_route_families_do_not_own_business_state() -> None:
    windows_route = RouteRegistration(
        **{**_route_registration_kwargs(route_family=RouteFamily.WINDOWS_VM_BROWSER_WORKER_ROUTE)}
    )
    extension_route = RouteRegistration(
        **{**_route_registration_kwargs(route_family=RouteFamily.BROWSER_EXTENSION_ROUTE)}
    )

    field_names = {field.name for field in fields(RouteRegistration)}
    assert "parser" not in {name.lower() for name in field_names}
    assert "beacon" not in {name.lower() for name in field_names}
    assert "notification" not in {name.lower() for name in field_names}
    assert "database" not in {name.lower() for name in field_names}
    assert windows_route.route_family is RouteFamily.WINDOWS_VM_BROWSER_WORKER_ROUTE
    assert extension_route.route_family is RouteFamily.BROWSER_EXTENSION_ROUTE


def test_owner_development_bridge_registration_remains_semantic_only() -> None:
    route_registration = RouteRegistration(
        **{**_route_registration_kwargs(route_family=RouteFamily.OWNER_DEVELOPMENT_BRIDGE_ROUTE)}
    )

    field_names = {field.name for field in fields(RouteRegistration)}
    assert "throughput" not in field_names
    assert "concurrency" not in field_names
    assert "scale" not in field_names
    assert "capacity" not in field_names
    assert route_registration.route_family is RouteFamily.OWNER_DEVELOPMENT_BRIDGE_ROUTE


def test_linux_reference_style_route_with_unproven_evidence_cannot_be_registered() -> None:
    with pytest.raises(ValueError):
        RouteRegistration(
            **{**_route_registration_kwargs(evidence_status=RouteEvidenceStatus.UNPROVEN)}
        )


def test_russian_residential_route_has_no_provider_configuration_or_credentials() -> None:
    route_registration = RouteRegistration(
        **{**_route_registration_kwargs(route_family=RouteFamily.RUSSIAN_RESIDENTIAL_ROUTE)}
    )

    field_names = {field.name for field in fields(RouteRegistration)}
    assert "provider" not in {name.lower() for name in field_names}
    assert "proxy" not in {name.lower() for name in field_names}
    assert "vpn" not in {name.lower() for name in field_names}
    assert "tunnel" not in {name.lower() for name in field_names}
    assert "credential" not in {name.lower() for name in field_names}
    assert "password" not in {name.lower() for name in field_names}
    assert "token" not in {name.lower() for name in field_names}
    assert route_registration.route_family is RouteFamily.RUSSIAN_RESIDENTIAL_ROUTE


def test_agent_and_route_ids_are_not_host_ip_or_port_aliases() -> None:
    agent_registration = AgentRegistration(**_agent_registration_kwargs())
    route_registration = RouteRegistration(**_route_registration_kwargs())

    assert agent_registration.agent_id == "agent-01"
    assert route_registration.route_id == "route-01"
    field_names = {field.name for field in fields(AgentRegistration)} | {
        field.name for field in fields(RouteRegistration)
    }
    assert "host" not in {name.lower() for name in field_names}
    assert "hostname" not in {name.lower() for name in field_names}
    assert "ip" not in {name.lower() for name in field_names}
    assert "port" not in {name.lower() for name in field_names}


def test_cross_environment_association_and_foreign_agent_rejection() -> None:
    boundary = _boundary_kwargs()
    boundary["route"] = replace(boundary["route"], environment_id="env-foreign")
    with pytest.raises(ValueError):
        AgentRouteRegistrationBoundary(**boundary)

    boundary = _boundary_kwargs()
    boundary["association"] = replace(boundary["association"], agent_id="agent-foreign")
    with pytest.raises(ValueError):
        AgentRouteRegistrationBoundary(**boundary)


def test_active_association_rejects_blocked_registrations() -> None:
    boundary = _boundary_kwargs()
    boundary["agent_registration"] = replace(
        boundary["agent_registration"],
        status=AgentRegistrationStatus.REGISTRATION_BLOCKED,
        reason_codes=("blocked",),
    )
    with pytest.raises(ValueError):
        AgentRouteRegistrationBoundary(**boundary)

    boundary = _boundary_kwargs()
    boundary["route_registration"] = replace(
        boundary["route_registration"],
        status=RouteRegistrationStatus.REGISTRATION_BLOCKED,
        reason_codes=("blocked",),
    )
    with pytest.raises(ValueError):
        AgentRouteRegistrationBoundary(**boundary)


def test_active_association_accepts_online_unready_agent_and_registered_route() -> None:
    boundary = AgentRouteRegistrationBoundary(**_boundary_kwargs())

    assert boundary.association.status is AgentRouteAssociationStatus.ACTIVE
    assert boundary.agent.lifecycle_status is AgentLifecycleStatus.ONLINE_UNREADY
    assert boundary.route.lifecycle_status is RouteLifecycleStatus.REGISTERED
    assert boundary.route_registration.status is RouteRegistrationStatus.REGISTERED
    assert boundary.agent_registration.status is AgentRegistrationStatus.REGISTERED

from __future__ import annotations

from dataclasses import fields, is_dataclass, replace
from pathlib import Path
from typing import Any

import pytest

from mayak.modules import egress_routing
from mayak.modules.egress_routing import (
    AgentLifecycleStatus,
    EgressAgent,
    EgressRoute,
    RouteEvidenceStatus,
    RouteFamily,
    RouteLifecycleStatus,
    SessionPolicyStatus,
)
from mayak.modules.egress_routing import (
    registration as registration_module,
)
from mayak.modules.egress_routing.registration import (
    ER03_TASK_ID,
    AgentRegistration,
    AgentRegistrationStatus,
    AgentRouteAssociation,
    AgentRouteAssociationStatus,
    AgentRouteRegistrationBoundary,
    RouteRegistration,
    RouteRegistrationStatus,
)

EXPECTED_TASK_ID = "".join(("ER-03-", "AGENT-ROUTE-REGISTRATION-", "20260712-004"))

EXPECTED_PACKAGE_EXPORTS = (
    "MODULE_ID",
    "AgentLifecycleStatus",
    "DiagnosticEvidenceKind",
    "DispatchAttempt",
    "DispatchStatus",
    "EgressAgent",
    "EgressRoute",
    "PolicyBasedFallbackDecision",
    "PolicyBasedFallbackStatus",
    "RouteCapability",
    "RouteEvidenceReference",
    "RouteEvidenceStatus",
    "RouteFamily",
    "RouteHealthState",
    "RouteHealthStatus",
    "RouteLease",
    "RouteLeaseStatus",
    "RouteLifecycleStatus",
    "RouteQuarantineDecision",
    "RouteQuarantineStatus",
    "RouteReadinessDecision",
    "RouteReadinessStatus",
    "RouteReconciliationState",
    "RouteReconciliationStatus",
    "RouteRestrictionState",
    "RouteRestrictionStatus",
    "RouteSelectionDecision",
    "RouteSelectionStatus",
    "SafeOperationalDiagnostic",
    "SessionPolicyStatus",
    "TransportAssignment",
    "TransportAssignmentOutcome",
    "TransportOutcomeStatus",
    "ER03_TASK_ID",
    "AgentRegistrationStatus",
    "RouteRegistrationStatus",
    "AgentRouteAssociationStatus",
    "AgentRegistration",
    "RouteRegistration",
    "AgentRouteAssociation",
    "AgentRouteRegistrationBoundary",
    "ER05A_TASK_ID",
    "RouteSelectionAuthority",
    "RouteCandidateEligibilityStatus",
    "RouteCandidateEvaluation",
    "ServerRouteSelectionBoundary",
    "ER05B_TASK_ID",
    "PolicyBasedFallbackBoundary",
    "ER06A_TASK_ID",
    "RouteLeaseAuthority",
    "RouteLeaseAuthorizationBoundary",
    "ER06B_TASK_ID",
    "TransportAssignmentAuthority",
    "TransportAssignmentCommitmentBoundary",
    "ER06C_TASK_ID",
    "TransportDispatchAuthority",
    "TransportDispatchAttemptBoundary",
    "ER06D_TASK_ID",
    "TransportDispatchReplayAuthority",
    "TransportDispatchReplayBoundary",
    "ER06E_TASK_ID",
    "TransportDispatchReconciliationAuthority",
    "TransportDispatchReconciliationBoundary",
    "ER06F_TASK_ID",
    "TransportDispatchReconciliationResolutionAuthority",
    "TransportDispatchReconciliationResolutionBoundary",
    "ER07A_TASK_ID",
    "TransportOutcomeCommitmentAuthority",
    "TransportOutcomeCommitmentBoundary",
    "ER02_TASK_ID",
    "EGRESS_SYNTHETIC_FIXTURE_IDS",
    "EGRESS_SYNTHETIC_FIXTURES",
    "EgressSyntheticFixture",
)

EXPECTED_REGISTRATION_EXPORTS = (
    "ER03_TASK_ID",
    "AgentRegistrationStatus",
    "RouteRegistrationStatus",
    "AgentRouteAssociationStatus",
    "AgentRegistration",
    "RouteRegistration",
    "AgentRouteAssociation",
    "AgentRouteRegistrationBoundary",
)

EXPECTED_ENUM_PAIRS = {
    AgentRegistrationStatus: (
        ("REGISTERED", "REGISTERED"),
        ("REGISTRATION_BLOCKED", "REGISTRATION_BLOCKED"),
        ("CONFLICT", "CONFLICT"),
        ("REJECTED", "REJECTED"),
        ("SUSPENDED", "SUSPENDED"),
        ("RETIRED", "RETIRED"),
    ),
    RouteRegistrationStatus: (
        ("REGISTERED", "REGISTERED"),
        ("REGISTRATION_BLOCKED", "REGISTRATION_BLOCKED"),
        ("UNSUPPORTED", "UNSUPPORTED"),
        ("CONFLICT", "CONFLICT"),
        ("REJECTED", "REJECTED"),
        ("SUSPENDED", "SUSPENDED"),
        ("RETIRED", "RETIRED"),
    ),
    AgentRouteAssociationStatus: (
        ("ACTIVE", "ACTIVE"),
        ("REGISTRATION_BLOCKED", "REGISTRATION_BLOCKED"),
        ("CONFLICT", "CONFLICT"),
        ("SUSPENDED", "SUSPENDED"),
        ("RETIRED", "RETIRED"),
    ),
}

EXPECTED_FIELD_NAMES = {
    AgentRegistration: (
        "registration_id",
        "agent_id",
        "environment_id",
        "agent_class",
        "accountable_owner_reference",
        "purpose_scope",
        "trust_scope",
        "source_release_reference",
        "credential_reference",
        "connectivity_boundary_reference",
        "isolation_boundary_reference",
        "privacy_boundary_reference",
        "replaceable_execution_dependency",
        "primary_database_access_allowed",
        "business_state_ownership_allowed",
        "public_unauthenticated_inbound_allowed",
        "foreign_resource_reuse_allowed",
        "arbitrary_command_execution_allowed",
        "status",
        "reason_codes",
        "evidence_reference_ids",
    ),
    RouteRegistration: (
        "registration_id",
        "route_id",
        "agent_id",
        "agent_registration_id",
        "environment_id",
        "source_release_reference",
        "route_family",
        "purpose_scope",
        "capability_ids",
        "unsupported_classes",
        "evidence_status",
        "session_policy_status",
        "restriction_reference",
        "selection_policy_reference",
        "privacy_boundary_reference",
        "status",
        "reason_codes",
        "evidence_reference_ids",
    ),
    AgentRouteAssociation: (
        "association_id",
        "agent_id",
        "route_id",
        "environment_id",
        "agent_registration_id",
        "route_registration_id",
        "purpose_scope",
        "status",
        "reason_codes",
        "evidence_reference_ids",
    ),
    AgentRouteRegistrationBoundary: (
        "boundary_id",
        "agent",
        "agent_registration",
        "route",
        "route_registration",
        "association",
    ),
}

REQUIRED_RECORDS = (
    AgentRegistration,
    RouteRegistration,
    AgentRouteAssociation,
    AgentRouteRegistrationBoundary,
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
    agent = EgressAgent(**_agent_kwargs())
    route = EgressRoute(**_route_kwargs())
    agent_registration = AgentRegistration(**_agent_registration_kwargs())
    route_registration = RouteRegistration(**_route_registration_kwargs())
    association = AgentRouteAssociation(**_association_kwargs())
    return {
        "boundary_id": "boundary-01",
        "agent": agent,
        "agent_registration": agent_registration,
        "route": route,
        "route_registration": route_registration,
        "association": association,
    }


def test_registration_task_id_and_package_exports_are_exact() -> None:
    assert ER03_TASK_ID == EXPECTED_TASK_ID
    assert registration_module.ER03_TASK_ID == EXPECTED_TASK_ID
    assert type(egress_routing.__all__) is tuple
    assert egress_routing.__all__ == EXPECTED_PACKAGE_EXPORTS
    assert tuple(egress_routing.__all__) == EXPECTED_PACKAGE_EXPORTS
    assert len(egress_routing.__all__) == len(EXPECTED_PACKAGE_EXPORTS)
    assert len(set(egress_routing.__all__)) == len(EXPECTED_PACKAGE_EXPORTS)
    assert all(hasattr(egress_routing, name) for name in EXPECTED_PACKAGE_EXPORTS)
    assert registration_module.__all__ == EXPECTED_REGISTRATION_EXPORTS


def test_package_all_is_one_canonical_builtin_tuple() -> None:
    observed_exports = tuple(egress_routing.__all__)
    assert type(egress_routing.__all__) is tuple
    assert observed_exports == EXPECTED_PACKAGE_EXPORTS
    assert tuple(egress_routing.__all__) == EXPECTED_PACKAGE_EXPORTS
    assert len(observed_exports) == len(EXPECTED_PACKAGE_EXPORTS)
    assert len(set(observed_exports)) == len(EXPECTED_PACKAGE_EXPORTS)
    assert all(hasattr(egress_routing, name) for name in EXPECTED_PACKAGE_EXPORTS)
    assert all(
        name in observed_exports
        for name in (
            "ER03_TASK_ID",
            "AgentRegistrationStatus",
            "RouteRegistrationStatus",
            "AgentRouteAssociationStatus",
            "AgentRegistration",
            "RouteRegistration",
            "AgentRouteAssociation",
            "AgentRouteRegistrationBoundary",
        )
    )


def test_registration_task_id_occurs_exactly_once_in_changed_scope() -> None:
    changed_paths = (
        Path("src/mayak/modules/egress_routing/__init__.py"),
        Path("src/mayak/modules/egress_routing/registration.py"),
        Path("tests/contract/test_egress_routing_registration_contracts.py"),
        Path("tests/unit/test_egress_routing_registration_semantics.py"),
        Path("tests/architecture/test_egress_routing_boundaries.py"),
    )
    count = sum(
        (Path(__file__).resolve().parents[2] / relative_path).read_text().count(EXPECTED_TASK_ID)
        for relative_path in changed_paths
    )
    assert count == 1


@pytest.mark.parametrize(
    ("enum_cls", "expected_pairs"),
    list(EXPECTED_ENUM_PAIRS.items()),
)
def test_public_registration_enum_member_value_pairs(
    enum_cls: Any, expected_pairs: tuple[tuple[str, str], ...]
) -> None:
    observed_pairs = tuple((member.name, member.value) for member in enum_cls)
    assert observed_pairs == expected_pairs


@pytest.mark.parametrize(
    ("record_cls", "expected_field_names"),
    list(EXPECTED_FIELD_NAMES.items()),
)
def test_registration_records_are_frozen_and_slotted_dataclasses(
    record_cls: Any, expected_field_names: tuple[str, ...]
) -> None:
    assert is_dataclass(record_cls)
    assert record_cls.__dataclass_params__.frozen is True  # type: ignore[union-attr]
    assert tuple(field.name for field in fields(record_cls)) == expected_field_names
    assert tuple(record_cls.__slots__) == expected_field_names  # type: ignore[union-attr]


def test_registration_records_do_not_expose_forbidden_runtime_configuration_fields() -> None:
    forbidden_tokens = {
        "host",
        "hostname",
        "ip",
        "port",
        "provider",
        "proxy",
        "vpn",
        "tunnel",
        "password",
        "token",
        "secret_value",
        "raw_credentials",
        "primary_database_credentials",
        "account",
        "beacon",
        "tariff",
        "scan_history",
        "notification_history",
        "selected_route",
        "fallback_order",
    }
    field_names = {
        field.name.lower() for record_cls in REQUIRED_RECORDS for field in fields(record_cls)
    }
    assert field_names.isdisjoint(forbidden_tokens)


@pytest.mark.parametrize(
    ("record_cls", "kwargs", "blank_field"),
    [
        (AgentRegistration, _agent_registration_kwargs(), "registration_id"),
        (AgentRegistration, _agent_registration_kwargs(), "agent_id"),
        (AgentRegistration, _agent_registration_kwargs(), "environment_id"),
        (AgentRegistration, _agent_registration_kwargs(), "agent_class"),
        (AgentRegistration, _agent_registration_kwargs(), "accountable_owner_reference"),
        (AgentRegistration, _agent_registration_kwargs(), "source_release_reference"),
        (AgentRegistration, _agent_registration_kwargs(), "connectivity_boundary_reference"),
        (AgentRegistration, _agent_registration_kwargs(), "isolation_boundary_reference"),
        (AgentRegistration, _agent_registration_kwargs(), "privacy_boundary_reference"),
        (RouteRegistration, _route_registration_kwargs(), "registration_id"),
        (RouteRegistration, _route_registration_kwargs(), "route_id"),
        (RouteRegistration, _route_registration_kwargs(), "agent_id"),
        (RouteRegistration, _route_registration_kwargs(), "agent_registration_id"),
        (RouteRegistration, _route_registration_kwargs(), "environment_id"),
        (RouteRegistration, _route_registration_kwargs(), "source_release_reference"),
        (RouteRegistration, _route_registration_kwargs(), "privacy_boundary_reference"),
        (AgentRouteAssociation, _association_kwargs(), "association_id"),
        (AgentRouteAssociation, _association_kwargs(), "agent_id"),
        (AgentRouteAssociation, _association_kwargs(), "route_id"),
        (AgentRouteAssociation, _association_kwargs(), "environment_id"),
        (AgentRouteAssociation, _association_kwargs(), "agent_registration_id"),
        (AgentRouteAssociation, _association_kwargs(), "route_registration_id"),
        (AgentRouteRegistrationBoundary, _boundary_kwargs(), "boundary_id"),
    ],
)
def test_blank_mandatory_text_fields_are_rejected(
    record_cls: type[object],
    kwargs: dict[str, Any],
    blank_field: str,
) -> None:
    kwargs = dict(kwargs)
    kwargs[blank_field] = " "
    with pytest.raises(ValueError):
        record_cls(**kwargs)


@pytest.mark.parametrize(
    ("record_cls", "kwargs", "blank_field"),
    [
        (AgentRegistration, _agent_registration_kwargs(), "credential_reference"),
        (RouteRegistration, _route_registration_kwargs(), "restriction_reference"),
        (RouteRegistration, _route_registration_kwargs(), "selection_policy_reference"),
    ],
)
def test_blank_optional_text_fields_are_rejected_when_present(
    record_cls: type[object],
    kwargs: dict[str, Any],
    blank_field: str,
) -> None:
    kwargs = dict(kwargs)
    kwargs[blank_field] = " "
    with pytest.raises(ValueError):
        record_cls(**kwargs)


@pytest.mark.parametrize(
    ("record_cls", "kwargs", "blank_field"),
    [
        (AgentRegistration, _agent_registration_kwargs(), "purpose_scope"),
        (AgentRegistration, _agent_registration_kwargs(), "trust_scope"),
        (RouteRegistration, _route_registration_kwargs(), "purpose_scope"),
        (RouteRegistration, _route_registration_kwargs(), "capability_ids"),
        (RouteRegistration, _route_registration_kwargs(), "unsupported_classes"),
        (RouteRegistration, _route_registration_kwargs(), "reason_codes"),
        (RouteRegistration, _route_registration_kwargs(), "evidence_reference_ids"),
        (AgentRouteAssociation, _association_kwargs(), "purpose_scope"),
        (AgentRouteAssociation, _association_kwargs(), "reason_codes"),
        (AgentRouteAssociation, _association_kwargs(), "evidence_reference_ids"),
    ],
)
def test_blank_tuple_entries_are_rejected(
    record_cls: type[object],
    kwargs: dict[str, Any],
    blank_field: str,
) -> None:
    kwargs = dict(kwargs)
    kwargs[blank_field] = ("safe", " ")
    with pytest.raises(ValueError):
        record_cls(**kwargs)


@pytest.mark.parametrize(
    ("record_cls", "kwargs", "field_name"),
    [
        (AgentRegistration, _agent_registration_kwargs(), "replaceable_execution_dependency"),
        (AgentRegistration, _agent_registration_kwargs(), "primary_database_access_allowed"),
        (AgentRegistration, _agent_registration_kwargs(), "business_state_ownership_allowed"),
        (AgentRegistration, _agent_registration_kwargs(), "public_unauthenticated_inbound_allowed"),
        (AgentRegistration, _agent_registration_kwargs(), "foreign_resource_reuse_allowed"),
        (AgentRegistration, _agent_registration_kwargs(), "arbitrary_command_execution_allowed"),
    ],
)
def test_bool_fields_reject_non_bool_values(
    record_cls: type[object],
    kwargs: dict[str, Any],
    field_name: str,
) -> None:
    kwargs = dict(kwargs)
    kwargs[field_name] = 1
    with pytest.raises(ValueError):
        record_cls(**kwargs)


def test_replaceable_dependency_must_be_true_and_other_flags_must_be_false() -> None:
    kwargs = _agent_registration_kwargs()
    kwargs["replaceable_execution_dependency"] = False
    with pytest.raises(ValueError):
        AgentRegistration(**kwargs)

    for field_name in (
        "primary_database_access_allowed",
        "business_state_ownership_allowed",
        "public_unauthenticated_inbound_allowed",
        "foreign_resource_reuse_allowed",
        "arbitrary_command_execution_allowed",
    ):
        with pytest.raises(ValueError):
            AgentRegistration(**{**_agent_registration_kwargs(), field_name: True})


def test_registered_agent_requires_credential_reference_and_evidence() -> None:
    with pytest.raises(ValueError):
        AgentRegistration(**{**_agent_registration_kwargs(), "credential_reference": None})

    with pytest.raises(ValueError):
        AgentRegistration(**{**_agent_registration_kwargs(), "evidence_reference_ids": ()})


@pytest.mark.parametrize(
    "field_name",
    ("purpose_scope", "trust_scope"),
)
def test_registered_agent_requires_non_empty_scopes(field_name: str) -> None:
    with pytest.raises(ValueError):
        AgentRegistration(**{**_agent_registration_kwargs(), field_name: ()})


@pytest.mark.parametrize(
    "status",
    (
        AgentRegistrationStatus.REGISTRATION_BLOCKED,
        AgentRegistrationStatus.CONFLICT,
        AgentRegistrationStatus.REJECTED,
        AgentRegistrationStatus.SUSPENDED,
        AgentRegistrationStatus.RETIRED,
    ),
)
def test_non_registered_agent_statuses_require_reason_codes(
    status: AgentRegistrationStatus,
) -> None:
    with pytest.raises(ValueError):
        AgentRegistration(**{**_agent_registration_kwargs(status=status), "reason_codes": ()})


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
def test_registered_route_rejects_non_current_evidence(
    evidence_status: RouteEvidenceStatus,
) -> None:
    with pytest.raises(ValueError):
        RouteRegistration(**{**_route_registration_kwargs(evidence_status=evidence_status)})


def test_registered_route_requires_capability_and_evidence_and_purpose_scopes() -> None:
    with pytest.raises(ValueError):
        RouteRegistration(**{**_route_registration_kwargs(capability_ids=())})

    with pytest.raises(ValueError):
        RouteRegistration(**{**_route_registration_kwargs(evidence_reference_ids=())})

    with pytest.raises(ValueError):
        RouteRegistration(**{**_route_registration_kwargs(purpose_scope=())})


def test_unsupported_route_requires_unsupported_classes() -> None:
    with pytest.raises(ValueError):
        RouteRegistration(
            **{
                **_route_registration_kwargs(
                    status=RouteRegistrationStatus.UNSUPPORTED,
                    unsupported_classes=(),
                    reason_codes=("unsupported",),
                    evidence_reference_ids=("evidence-route-registration-01",),
                )
            }
        )


@pytest.mark.parametrize(
    "status",
    (
        RouteRegistrationStatus.REGISTRATION_BLOCKED,
        RouteRegistrationStatus.UNSUPPORTED,
        RouteRegistrationStatus.CONFLICT,
        RouteRegistrationStatus.REJECTED,
        RouteRegistrationStatus.SUSPENDED,
        RouteRegistrationStatus.RETIRED,
    ),
)
def test_non_registered_route_statuses_require_reason_codes(
    status: RouteRegistrationStatus,
) -> None:
    kwargs = _route_registration_kwargs(status=status)
    if status is RouteRegistrationStatus.UNSUPPORTED:
        kwargs["unsupported_classes"] = ("unsupported-capability",)
    with pytest.raises(ValueError):
        RouteRegistration(**{**kwargs, "reason_codes": ()})


@pytest.mark.parametrize(
    "status",
    (
        AgentRouteAssociationStatus.REGISTRATION_BLOCKED,
        AgentRouteAssociationStatus.CONFLICT,
        AgentRouteAssociationStatus.SUSPENDED,
        AgentRouteAssociationStatus.RETIRED,
    ),
)
def test_non_active_association_statuses_require_reason_codes(
    status: AgentRouteAssociationStatus,
) -> None:
    with pytest.raises(ValueError):
        AgentRouteAssociation(**{**_association_kwargs(status=status), "reason_codes": ()})


def test_active_association_requires_evidence_and_purpose() -> None:
    with pytest.raises(ValueError):
        AgentRouteAssociation(**{**_association_kwargs(purpose_scope=())})

    with pytest.raises(ValueError):
        AgentRouteAssociation(**{**_association_kwargs(evidence_reference_ids=())})


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("agent_id", "foreign-agent"),
        ("environment_id", "foreign-env"),
        ("agent_class", "ForeignAgentClass"),
        ("trust_scope", ("foreign-trust",)),
        ("source_release_reference", "foreign-release"),
        ("credential_reference", "foreign-credential"),
    ),
)
def test_boundary_rejects_agent_mismatches(field_name: str, value: Any) -> None:
    kwargs = _boundary_kwargs()
    kwargs["agent"] = replace(kwargs["agent"], **{field_name: value})
    with pytest.raises(ValueError):
        AgentRouteRegistrationBoundary(**kwargs)


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("route_id", "foreign-route"),
        ("agent_id", "foreign-agent"),
        ("environment_id", "foreign-env"),
        ("route_family", RouteFamily.BROWSER_EXTENSION_ROUTE),
        ("purpose_scope", ("foreign-purpose",)),
        ("capability_ids", ("foreign-capability",)),
    ),
)
def test_boundary_rejects_route_mismatches(field_name: str, value: Any) -> None:
    kwargs = _boundary_kwargs()
    kwargs["route"] = replace(kwargs["route"], **{field_name: value})
    with pytest.raises(ValueError):
        AgentRouteRegistrationBoundary(**kwargs)


@pytest.mark.parametrize(
    ("field_name", "value"),
    (("agent_registration_id", "foreign-agent-registration"),),
)
def test_boundary_rejects_route_registration_mismatches(field_name: str, value: Any) -> None:
    kwargs = _boundary_kwargs()
    kwargs["route_registration"] = replace(kwargs["route_registration"], **{field_name: value})
    with pytest.raises(ValueError):
        AgentRouteRegistrationBoundary(**kwargs)


def test_boundary_rejects_coordinated_foreign_route_agent_ownership() -> None:
    kwargs = _boundary_kwargs()
    kwargs["route"] = replace(kwargs["route"], agent_id="foreign-agent")
    kwargs["route_registration"] = replace(kwargs["route_registration"], agent_id="foreign-agent")

    with pytest.raises(ValueError, match="route.agent_id must match agent.agent_id"):
        AgentRouteRegistrationBoundary(**kwargs)


def test_boundary_rejects_foreign_route_agent_id() -> None:
    kwargs = _boundary_kwargs()
    kwargs["route"] = replace(kwargs["route"], agent_id="foreign-agent")

    with pytest.raises(ValueError, match="route.agent_id must match agent.agent_id"):
        AgentRouteRegistrationBoundary(**kwargs)


def test_boundary_rejects_foreign_route_registration_agent_id() -> None:
    kwargs = _boundary_kwargs()
    kwargs["route_registration"] = replace(kwargs["route_registration"], agent_id="foreign-agent")

    with pytest.raises(
        ValueError,
        match="route_registration.agent_id must match agent_registration.agent_id",
    ):
        AgentRouteRegistrationBoundary(**kwargs)


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("agent_id", "foreign-agent"),
        ("route_id", "foreign-route"),
        ("environment_id", "foreign-env"),
        ("agent_registration_id", "foreign-agent-registration"),
        ("route_registration_id", "foreign-route-registration"),
        ("purpose_scope", ("foreign-purpose",)),
    ),
)
def test_boundary_rejects_association_mismatches(field_name: str, value: Any) -> None:
    kwargs = _boundary_kwargs()
    kwargs["association"] = replace(kwargs["association"], **{field_name: value})
    with pytest.raises(ValueError):
        AgentRouteRegistrationBoundary(**kwargs)


@pytest.mark.parametrize(
    ("registration_field", "registration_status"),
    (
        ("agent_registration", AgentRegistrationStatus.REGISTRATION_BLOCKED),
        ("route_registration", RouteRegistrationStatus.REGISTRATION_BLOCKED),
    ),
)
def test_active_association_rejects_blocked_registrations(
    registration_field: str, registration_status: Any
) -> None:
    kwargs = _boundary_kwargs()
    kwargs[registration_field] = replace(
        kwargs[registration_field], status=registration_status, reason_codes=("blocked",)
    )
    with pytest.raises(ValueError):
        AgentRouteRegistrationBoundary(**kwargs)


@pytest.mark.parametrize(
    ("agent_status", "route_status"),
    (
        (AgentLifecycleStatus.PROPOSED, RouteLifecycleStatus.REGISTERED),
        (AgentLifecycleStatus.REGISTRATION_BLOCKED, RouteLifecycleStatus.REGISTERED),
        (AgentLifecycleStatus.SUSPENDED, RouteLifecycleStatus.REGISTERED),
        (AgentLifecycleStatus.RETIRED, RouteLifecycleStatus.REGISTERED),
        (AgentLifecycleStatus.ONLINE_UNREADY, RouteLifecycleStatus.PROPOSED),
        (AgentLifecycleStatus.ONLINE_UNREADY, RouteLifecycleStatus.REGISTRATION_BLOCKED),
        (AgentLifecycleStatus.ONLINE_UNREADY, RouteLifecycleStatus.SUSPENDED),
        (AgentLifecycleStatus.ONLINE_UNREADY, RouteLifecycleStatus.RETIRED),
    ),
)
def test_active_association_rejects_blocked_and_prohibited_lifecycles(
    agent_status: AgentLifecycleStatus,
    route_status: RouteLifecycleStatus,
) -> None:
    kwargs = _boundary_kwargs()
    kwargs["agent"] = replace(kwargs["agent"], lifecycle_status=agent_status)
    kwargs["route"] = replace(kwargs["route"], lifecycle_status=route_status)
    with pytest.raises(ValueError):
        AgentRouteRegistrationBoundary(**kwargs)


def test_active_association_accepts_online_unready_agent_and_registered_route() -> None:
    boundary = AgentRouteRegistrationBoundary(**_boundary_kwargs())

    assert boundary.association.status is AgentRouteAssociationStatus.ACTIVE
    assert boundary.agent.lifecycle_status is AgentLifecycleStatus.ONLINE_UNREADY
    assert boundary.route.lifecycle_status is RouteLifecycleStatus.REGISTERED
    assert boundary.route_registration.status is RouteRegistrationStatus.REGISTERED
    assert boundary.agent_registration.status is AgentRegistrationStatus.REGISTERED


def test_registration_records_have_no_host_ip_port_or_ownership_state_fields() -> None:
    field_names = {field.name for record_cls in REQUIRED_RECORDS for field in fields(record_cls)}
    assert "host" not in field_names
    assert "hostname" not in field_names
    assert "ip" not in field_names
    assert "port" not in field_names
    assert "provider" not in field_names
    assert "proxy" not in field_names
    assert "vpn" not in field_names
    assert "tunnel" not in field_names
    assert "password" not in field_names
    assert "token" not in field_names
    assert "secret_value" not in field_names
    assert "raw_credentials" not in field_names
    assert "primary_database_credentials" not in field_names
    assert "account" not in field_names
    assert "beacon" not in field_names
    assert "tariff" not in field_names
    assert "scan_history" not in field_names
    assert "notification_history" not in field_names
    assert "selected_route" not in field_names
    assert "fallback_order" not in field_names

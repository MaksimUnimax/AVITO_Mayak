from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass
from enum import Enum
from types import SimpleNamespace
from typing import Any, cast

import pytest

import mayak.modules.egress_routing as egress_routing
import mayak.modules.egress_routing.development_bridge_gate as development_bridge_gate_module
import tests.contract.test_egress_routing_session_secret_gate_contracts as session_contracts
from mayak.modules.egress_routing import (
    ER11A_TASK_ID,
    DevelopmentBridgeAuthority,
    DevelopmentBridgeGateBoundary,
    EgressSessionSecretAuthority,
    EgressSessionSecretGateBoundary,
    RouteCapability,
    RouteFamily,
    SessionPolicyStatus,
)

EXPECTED_TASK_ID = "ER-11A-DEVELOPMENT-BRIDGE-FAIL-CLOSED-GATE-20260716-048"

EXPECTED_MODULE_EXPORTS = (
    "ER11A_TASK_ID",
    "DevelopmentBridgeAuthority",
    "DevelopmentBridgeGateBoundary",
)

EXPECTED_PACKAGE_EXPORT_SLICE = (
    "ER08B_TASK_ID",
    "TransportRestrictionEvaluationAuthority",
    "TransportRestrictionEvaluationGateBoundary",
    "ER09A_TASK_ID",
    "EgressSessionSecretAuthority",
    "EgressSessionSecretGateBoundary",
    "ER10A_TASK_ID",
    "FutureBrowserFallbackAuthority",
    "FutureBrowserFallbackGateBoundary",
    "ER11A_TASK_ID",
    "DevelopmentBridgeAuthority",
    "DevelopmentBridgeGateBoundary",
    "ER12A_TASK_ID",
    "SafeEgressDiagnosticAuthority",
    "SafeEgressDiagnosticGateBoundary",
    "ER13A_TASK_ID",
    "EgressProofOnlyAuthority",
    "EgressProofOnlyGateBoundary",
    "ER14A_TASK_ID",
    "EgressPersistenceRuntimeAuthority",
    "EgressPersistenceRuntimeGateBoundary",
    "ER07E_TASK_ID",
)

EXPECTED_FIELD_NAMES = (
    "boundary_id",
    "authority",
    "route_capability",
    "session_secret_gate",
    "route_family",
    "route_id",
    "owner_development_bridge_direction_acknowledged",
    "owner_consent_required_for_each_use_scope",
    "development_only_required",
    "explicit_owner_use_scope_approved",
    "development_proof_scope_defined",
    "manual_owner_assisted_transport_semantic_candidate",
    "bounded_proof_assignment_required",
    "clear_evidence_report_required",
    "replaceable_by_production_route_required",
    "no_secrets_policy_required",
    "no_raw_payload_retention_required",
    "production_dependency_authorized",
    "unbounded_owner_machine_dependency_authorized",
    "silent_use_authorized",
    "owner_private_data_storage_authorized",
    "scalability_proof_inferred",
    "permanent_architecture_authorized",
    "live_proof_execution_authorized",
    "route_registration_authorized",
    "route_selection_authorized",
    "fallback_execution_authorized",
    "lease_or_assignment_commit_authorized",
    "provider_access_permission_inferred",
    "parser_success_inferred",
    "scan_success_inferred",
    "notification_delivery_inferred",
    "reason_codes",
    "evidence_reference_ids",
)

EXPECTED_TRUE_BOOLEAN_FIELDS = (
    "owner_development_bridge_direction_acknowledged",
    "owner_consent_required_for_each_use_scope",
    "development_only_required",
    "manual_owner_assisted_transport_semantic_candidate",
    "bounded_proof_assignment_required",
    "clear_evidence_report_required",
    "replaceable_by_production_route_required",
    "no_secrets_policy_required",
    "no_raw_payload_retention_required",
)

EXPECTED_FALSE_BOOLEAN_FIELDS = (
    "explicit_owner_use_scope_approved",
    "development_proof_scope_defined",
    "production_dependency_authorized",
    "unbounded_owner_machine_dependency_authorized",
    "silent_use_authorized",
    "owner_private_data_storage_authorized",
    "scalability_proof_inferred",
    "permanent_architecture_authorized",
    "live_proof_execution_authorized",
    "route_registration_authorized",
    "route_selection_authorized",
    "fallback_execution_authorized",
    "lease_or_assignment_commit_authorized",
    "provider_access_permission_inferred",
    "parser_success_inferred",
    "scan_success_inferred",
    "notification_delivery_inferred",
)

EXPECTED_ER09A_FALSE_BOOLEAN_FIELDS = (
    "isolated_project_session_gate_satisfied",
    "project_owned_session_authorized",
    "project_owned_cookie_profile_authorized",
    "personal_browser_profile_access_authorized",
    "browser_password_access_authorized",
    "owner_private_session_default_authorized",
    "foreign_or_unrelated_cookie_reuse_authorized",
    "raw_cookie_material_authorized",
    "raw_session_token_material_authorized",
    "raw_credential_material_authorized",
    "secret_logging_authorized",
    "secret_report_authorized",
    "secret_git_storage_authorized",
    "runtime_session_creation_authorized",
    "provider_access_permission_inferred",
    "parser_success_inferred",
    "scan_success_inferred",
    "notification_delivery_inferred",
)

EXPECTED_ER09A_TRUE_BOOLEAN_FIELDS = (
    "safe_reference_only",
    "rotation_required",
    "revocation_required",
    "redacted_diagnostics_required",
)

EXPECTED_REASON_CODES = (
    "owner-development-bridge-fail-closed",
    "explicit-owner-consent-required",
)

EXPECTED_EVIDENCE_REFERENCE_IDS = ("DEV-BRIDGE-EVIDENCE-001", "DEV-BRIDGE-EVIDENCE-002")
EXPECTED_CAPABILITY_ID = "cap-development-bridge-01"
EXPECTED_ROUTE_ID = "route-development-bridge-01"
EXPECTED_ALLOWED_ROUTE_FAMILY = RouteFamily.OWNER_DEVELOPMENT_BRIDGE_ROUTE
EXPECTED_REJECTED_ROUTE_FAMILIES = tuple(
    family for family in RouteFamily if family is not EXPECTED_ALLOWED_ROUTE_FAMILY
)


class TextLike(str):
    pass


class TupleLike(tuple):
    pass


class BoolLike(int):
    pass


class RouteFamilyLookalike(str, Enum):
    OWNER_DEVELOPMENT_BRIDGE_ROUTE = "OWNER_DEVELOPMENT_BRIDGE_ROUTE"


class DevelopmentBridgeAuthorityLookalike(str, Enum):
    EGRESS_ROUTING_SERVER = "EGRESS_ROUTING_SERVER"


class RouteCapabilitySubclass(RouteCapability):
    pass


class EgressSessionSecretGateSubclass(EgressSessionSecretGateBoundary):
    pass


def _mutate(record: object, **changes: object) -> None:
    for field_name, value in changes.items():
        object.__setattr__(record, field_name, value)


def _snapshot(record: object) -> tuple[object, ...]:
    return tuple(getattr(record, field.name) for field in fields(cast(Any, record)))


def _build_capability(
    *,
    session_policy_status: SessionPolicyStatus = SessionPolicyStatus.PROHIBITED,
    capability_id: str = EXPECTED_CAPABILITY_ID,
    route_id: str = EXPECTED_ROUTE_ID,
    evidence_reference_ids: tuple[str, ...] = EXPECTED_EVIDENCE_REFERENCE_IDS,
) -> RouteCapability:
    capability = session_contracts._build_capability(  # type: ignore[attr-defined]
        capability_id=capability_id,
        route_id=route_id,
        destination_scope=("owner-development-bridge",),
        operation_classes=("development-only",),
        unsupported_classes=("live-proof", "production-route", "secret-retention"),
        evidence_reference_ids=evidence_reference_ids,
        session_policy_status=session_policy_status,
    )
    assert type(capability) is RouteCapability
    return capability


def _build_session_secret_gate(
    capability: RouteCapability,
    *,
    boundary_id: str = "session-secret-gate-boundary-01",
    session_policy_status: SessionPolicyStatus = SessionPolicyStatus.PROHIBITED,
    reason_codes: tuple[str, ...] = ("session-bridge-safe-reference-only",),
) -> EgressSessionSecretGateBoundary:
    boundary = session_contracts._build_boundary(  # type: ignore[attr-defined]
        capability=capability,
        boundary_id=boundary_id,
        route_id=capability.route_id,
        session_policy_status=session_policy_status,
        reason_codes=reason_codes,
        evidence_reference_ids=capability.evidence_reference_ids,
    )
    assert type(boundary) is EgressSessionSecretGateBoundary
    return boundary


def _build_boundary(
    *,
    capability: RouteCapability,
    session_secret_gate: EgressSessionSecretGateBoundary,
    route_family: RouteFamily = EXPECTED_ALLOWED_ROUTE_FAMILY,
    boundary_id: str = "development-bridge-gate-boundary-01",
    authority: DevelopmentBridgeAuthority = DevelopmentBridgeAuthority.EGRESS_ROUTING_SERVER,
    route_id: str = EXPECTED_ROUTE_ID,
    owner_development_bridge_direction_acknowledged: bool = True,
    owner_consent_required_for_each_use_scope: bool = True,
    development_only_required: bool = True,
    explicit_owner_use_scope_approved: bool = False,
    development_proof_scope_defined: bool = False,
    manual_owner_assisted_transport_semantic_candidate: bool = True,
    bounded_proof_assignment_required: bool = True,
    clear_evidence_report_required: bool = True,
    replaceable_by_production_route_required: bool = True,
    no_secrets_policy_required: bool = True,
    no_raw_payload_retention_required: bool = True,
    production_dependency_authorized: bool = False,
    unbounded_owner_machine_dependency_authorized: bool = False,
    silent_use_authorized: bool = False,
    owner_private_data_storage_authorized: bool = False,
    scalability_proof_inferred: bool = False,
    permanent_architecture_authorized: bool = False,
    live_proof_execution_authorized: bool = False,
    route_registration_authorized: bool = False,
    route_selection_authorized: bool = False,
    fallback_execution_authorized: bool = False,
    lease_or_assignment_commit_authorized: bool = False,
    provider_access_permission_inferred: bool = False,
    parser_success_inferred: bool = False,
    scan_success_inferred: bool = False,
    notification_delivery_inferred: bool = False,
    reason_codes: tuple[str, ...] = EXPECTED_REASON_CODES,
    evidence_reference_ids: tuple[str, ...] = EXPECTED_EVIDENCE_REFERENCE_IDS,
) -> DevelopmentBridgeGateBoundary:
    kwargs: dict[str, object] = {
        "boundary_id": boundary_id,
        "authority": authority,
        "route_capability": capability,
        "session_secret_gate": session_secret_gate,
        "route_family": route_family,
        "route_id": route_id,
        "owner_development_bridge_direction_acknowledged": (
            owner_development_bridge_direction_acknowledged
        ),
        "owner_consent_required_for_each_use_scope": (
            owner_consent_required_for_each_use_scope
        ),
        "development_only_required": development_only_required,
        "explicit_owner_use_scope_approved": explicit_owner_use_scope_approved,
        "development_proof_scope_defined": development_proof_scope_defined,
        "manual_owner_assisted_transport_semantic_candidate": (
            manual_owner_assisted_transport_semantic_candidate
        ),
        "bounded_proof_assignment_required": bounded_proof_assignment_required,
        "clear_evidence_report_required": clear_evidence_report_required,
        "replaceable_by_production_route_required": replaceable_by_production_route_required,
        "no_secrets_policy_required": no_secrets_policy_required,
        "no_raw_payload_retention_required": no_raw_payload_retention_required,
        "production_dependency_authorized": production_dependency_authorized,
        "unbounded_owner_machine_dependency_authorized": (
            unbounded_owner_machine_dependency_authorized
        ),
        "silent_use_authorized": silent_use_authorized,
        "owner_private_data_storage_authorized": owner_private_data_storage_authorized,
        "scalability_proof_inferred": scalability_proof_inferred,
        "permanent_architecture_authorized": permanent_architecture_authorized,
        "live_proof_execution_authorized": live_proof_execution_authorized,
        "route_registration_authorized": route_registration_authorized,
        "route_selection_authorized": route_selection_authorized,
        "fallback_execution_authorized": fallback_execution_authorized,
        "lease_or_assignment_commit_authorized": lease_or_assignment_commit_authorized,
        "provider_access_permission_inferred": provider_access_permission_inferred,
        "parser_success_inferred": parser_success_inferred,
        "scan_success_inferred": scan_success_inferred,
        "notification_delivery_inferred": notification_delivery_inferred,
        "reason_codes": reason_codes,
        "evidence_reference_ids": evidence_reference_ids,
    }
    boundary = cast(Any, DevelopmentBridgeGateBoundary)(**kwargs)
    assert type(boundary) is DevelopmentBridgeGateBoundary
    return boundary


def test_module_exports_are_exact_and_ordered() -> None:
    assert ER11A_TASK_ID == EXPECTED_TASK_ID
    assert development_bridge_gate_module.ER11A_TASK_ID == EXPECTED_TASK_ID
    assert type(development_bridge_gate_module.__all__) is tuple
    assert development_bridge_gate_module.__all__ == EXPECTED_MODULE_EXPORTS
    assert tuple(development_bridge_gate_module.__all__) == EXPECTED_MODULE_EXPORTS
    assert len(development_bridge_gate_module.__all__) == len(
        set(development_bridge_gate_module.__all__)
    )
    assert all(hasattr(development_bridge_gate_module, name) for name in EXPECTED_MODULE_EXPORTS)


def test_package_export_slice_includes_er11a() -> None:
    exports = tuple(egress_routing.__all__)
    start = exports.index("ER08B_TASK_ID")

    assert (
        exports[start : start + len(EXPECTED_PACKAGE_EXPORT_SLICE)]
        == EXPECTED_PACKAGE_EXPORT_SLICE
    )
    assert hasattr(egress_routing, "ER11A_TASK_ID")
    assert hasattr(egress_routing, "DevelopmentBridgeAuthority")
    assert hasattr(egress_routing, "DevelopmentBridgeGateBoundary")


def test_exact_owner_development_bridge_route_boundary_accepts_and_preserves_identity() -> None:
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)
    boundary = _build_boundary(capability=capability, session_secret_gate=session_secret_gate)

    assert is_dataclass(boundary) is True
    assert type(boundary) is DevelopmentBridgeGateBoundary
    assert type(boundary).__slots__ == EXPECTED_FIELD_NAMES
    assert tuple(field.name for field in fields(boundary)) == EXPECTED_FIELD_NAMES
    assert len(fields(boundary)) == 34
    assert boundary.boundary_id == "development-bridge-gate-boundary-01"
    assert boundary.authority is DevelopmentBridgeAuthority.EGRESS_ROUTING_SERVER
    assert boundary.route_capability is capability
    assert type(boundary.route_capability) is RouteCapability
    assert boundary.session_secret_gate is session_secret_gate
    assert type(boundary.session_secret_gate) is EgressSessionSecretGateBoundary
    assert (
        boundary.session_secret_gate.authority
        is EgressSessionSecretAuthority.EGRESS_ROUTING_SERVER
    )
    assert boundary.route_family is EXPECTED_ALLOWED_ROUTE_FAMILY
    assert boundary.route_id == capability.route_id == session_secret_gate.route_id
    assert boundary.session_secret_gate.route_capability is capability
    assert boundary.session_secret_gate.session_policy_status is capability.session_policy_status
    assert boundary.session_secret_gate.evidence_reference_ids == capability.evidence_reference_ids
    assert boundary.evidence_reference_ids == capability.evidence_reference_ids
    assert boundary.evidence_reference_ids is capability.evidence_reference_ids
    assert boundary.reason_codes is EXPECTED_REASON_CODES
    assert type(boundary.reason_codes) is tuple
    assert type(boundary.evidence_reference_ids) is tuple
    assert _snapshot(capability) == _snapshot(capability)
    assert _snapshot(session_secret_gate) == _snapshot(session_secret_gate)
    assert _snapshot(capability) == _snapshot(capability)
    assert _snapshot(session_secret_gate) == _snapshot(session_secret_gate)
    for field_name in EXPECTED_TRUE_BOOLEAN_FIELDS:
        value = getattr(boundary, field_name)
        assert type(value) is bool
        assert value is True
    for field_name in EXPECTED_FALSE_BOOLEAN_FIELDS:
        value = getattr(boundary, field_name)
        assert type(value) is bool
        assert value is False


@pytest.mark.parametrize("route_family", EXPECTED_REJECTED_ROUTE_FAMILIES)
def test_only_owner_development_bridge_route_is_accepted(route_family: RouteFamily) -> None:
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)

    with pytest.raises(
        ValueError,
        match="route_family must be OWNER_DEVELOPMENT_BRIDGE_ROUTE",
    ):
        _build_boundary(
            capability=capability,
            session_secret_gate=session_secret_gate,
            route_family=route_family,
        )


@pytest.mark.parametrize("field_name", EXPECTED_TRUE_BOOLEAN_FIELDS)
def test_boundary_true_boolean_fields_are_revalidated(field_name: str) -> None:
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)

    with pytest.raises(ValueError, match=rf"{field_name} must be True"):
        cast(Any, _build_boundary)(
            capability=capability,
            session_secret_gate=session_secret_gate,
            **{field_name: False},
        )


@pytest.mark.parametrize("field_name", EXPECTED_FALSE_BOOLEAN_FIELDS)
def test_boundary_false_boolean_fields_are_revalidated(field_name: str) -> None:
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)

    with pytest.raises(ValueError, match=rf"{field_name} must be False"):
        cast(Any, _build_boundary)(
            capability=capability,
            session_secret_gate=session_secret_gate,
            **{field_name: True},
        )


def test_text_subclasses_tuple_subclasses_bool_lookalikes_and_enum_lookalikes_are_rejected() -> (
    None
):
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)

    with pytest.raises(ValueError, match="boundary_id must be a non-blank string"):
        _build_boundary(
            capability=capability,
            session_secret_gate=session_secret_gate,
            boundary_id=TextLike("development-bridge-gate-boundary-01"),
        )

    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        _build_boundary(
            capability=capability,
            session_secret_gate=session_secret_gate,
            reason_codes=TupleLike(EXPECTED_REASON_CODES),
        )

    with pytest.raises(
        ValueError,
        match="owner_development_bridge_direction_acknowledged must be a bool",
    ):
        _build_boundary(
            capability=capability,
            session_secret_gate=session_secret_gate,
            owner_development_bridge_direction_acknowledged=cast(Any, BoolLike(1)),
        )

    with pytest.raises(ValueError, match="authority must be DevelopmentBridgeAuthority"):
        _build_boundary(
            capability=capability,
            session_secret_gate=session_secret_gate,
            authority=cast(
                Any,
                DevelopmentBridgeAuthorityLookalike.EGRESS_ROUTING_SERVER,
            ),
        )

    with pytest.raises(ValueError, match="route_family must be RouteFamily"):
        _build_boundary(
            capability=capability,
            session_secret_gate=session_secret_gate,
            route_family=cast(
                Any,
                RouteFamilyLookalike.OWNER_DEVELOPMENT_BRIDGE_ROUTE,
            ),
        )


def test_route_capability_exact_record_rejections_cover_subclasses_and_duck_typing() -> None:
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)

    with pytest.raises(ValueError, match="route_capability must be RouteCapability"):
        _build_boundary(
            capability=RouteCapabilitySubclass(
                capability_id=capability.capability_id,
                route_id=capability.route_id,
                destination_scope=capability.destination_scope,
                operation_classes=capability.operation_classes,
                unsupported_classes=capability.unsupported_classes,
                evidence_reference_ids=capability.evidence_reference_ids,
                evidence_status=capability.evidence_status,
                session_policy_status=capability.session_policy_status,
            ),
            session_secret_gate=session_secret_gate,
        )

    with pytest.raises(ValueError, match="route_capability must be RouteCapability"):
        capability_like = cast(
            Any,
            SimpleNamespace(
                **{
                    field.name: getattr(capability, field.name)
                    for field in fields(capability)
                }
            ),
        )
        _build_boundary(capability=capability_like, session_secret_gate=session_secret_gate)


def test_session_secret_gate_exact_record_rejections_cover_subclasses_and_duck_typing() -> None:
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)

    with pytest.raises(
        ValueError,
        match="session_secret_gate must be EgressSessionSecretGateBoundary",
    ):
        _build_boundary(
            capability=capability,
            session_secret_gate=EgressSessionSecretGateSubclass(
                boundary_id=session_secret_gate.boundary_id,
                authority=session_secret_gate.authority,
                route_capability=session_secret_gate.route_capability,
                route_id=session_secret_gate.route_id,
                session_policy_status=session_secret_gate.session_policy_status,
                isolated_project_session_gate_satisfied=session_secret_gate.isolated_project_session_gate_satisfied,
                project_owned_session_authorized=session_secret_gate.project_owned_session_authorized,
                project_owned_cookie_profile_authorized=session_secret_gate.project_owned_cookie_profile_authorized,
                personal_browser_profile_access_authorized=session_secret_gate.personal_browser_profile_access_authorized,
                browser_password_access_authorized=session_secret_gate.browser_password_access_authorized,
                owner_private_session_default_authorized=session_secret_gate.owner_private_session_default_authorized,
                foreign_or_unrelated_cookie_reuse_authorized=session_secret_gate.foreign_or_unrelated_cookie_reuse_authorized,
                raw_cookie_material_authorized=session_secret_gate.raw_cookie_material_authorized,
                raw_session_token_material_authorized=session_secret_gate.raw_session_token_material_authorized,
                raw_credential_material_authorized=session_secret_gate.raw_credential_material_authorized,
                safe_reference_only=session_secret_gate.safe_reference_only,
                rotation_required=session_secret_gate.rotation_required,
                revocation_required=session_secret_gate.revocation_required,
                redacted_diagnostics_required=session_secret_gate.redacted_diagnostics_required,
                secret_logging_authorized=session_secret_gate.secret_logging_authorized,
                secret_report_authorized=session_secret_gate.secret_report_authorized,
                secret_git_storage_authorized=session_secret_gate.secret_git_storage_authorized,
                runtime_session_creation_authorized=session_secret_gate.runtime_session_creation_authorized,
                provider_access_permission_inferred=session_secret_gate.provider_access_permission_inferred,
                parser_success_inferred=session_secret_gate.parser_success_inferred,
                scan_success_inferred=session_secret_gate.scan_success_inferred,
                notification_delivery_inferred=session_secret_gate.notification_delivery_inferred,
                reason_codes=session_secret_gate.reason_codes,
                evidence_reference_ids=session_secret_gate.evidence_reference_ids,
            ),
        )

    with pytest.raises(
        ValueError,
        match="session_secret_gate must be EgressSessionSecretGateBoundary",
    ):
        session_secret_gate_like = cast(
            Any,
            SimpleNamespace(
                **{
                    field.name: getattr(session_secret_gate, field.name)
                    for field in fields(session_secret_gate)
                }
            ),
        )
        _build_boundary(capability=capability, session_secret_gate=session_secret_gate_like)


@pytest.mark.parametrize("field_name", EXPECTED_ER09A_FALSE_BOOLEAN_FIELDS)
def test_nested_session_secret_gate_false_boolean_fields_are_revalidated(field_name: str) -> None:
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)
    _mutate(session_secret_gate, **{field_name: True})

    with pytest.raises(ValueError, match=rf"session_secret_gate\.{field_name} must be False"):
        _build_boundary(capability=capability, session_secret_gate=session_secret_gate)


@pytest.mark.parametrize("field_name", EXPECTED_ER09A_TRUE_BOOLEAN_FIELDS)
def test_nested_session_secret_gate_true_boolean_fields_are_revalidated(field_name: str) -> None:
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)
    _mutate(session_secret_gate, **{field_name: False})

    with pytest.raises(ValueError, match=rf"session_secret_gate\.{field_name} must be True"):
        _build_boundary(capability=capability, session_secret_gate=session_secret_gate)


@pytest.mark.parametrize(
    "field_name, mutation, expected_message",
    [
        (
            "authority",
            DevelopmentBridgeAuthorityLookalike.EGRESS_ROUTING_SERVER,
            "session_secret_gate.authority must be EGRESS_ROUTING_SERVER",
        ),
        (
            "session_policy_status",
            SessionPolicyStatus.APPROVED_REFERENCE_ONLY,
            (
                "session_secret_gate.session_policy_status must be PROHIBITED or "
                "BLOCKED_PENDING_ISOLATED_PROJECT_SESSION_GATE"
            ),
        ),
        (
            "evidence_reference_ids",
            ("DEV-BRIDGE-EVIDENCE-001", "MUTATED-EVIDENCE"),
            (
                "session_secret_gate.evidence_reference_ids must match "
                "route_capability.evidence_reference_ids"
            ),
        ),
    ],
)
def test_nested_session_secret_gate_linkages_are_revalidated(
    field_name: str,
    mutation: object,
    expected_message: str,
) -> None:
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)
    _mutate(session_secret_gate, **{field_name: mutation})

    with pytest.raises(ValueError, match=expected_message):
        _build_boundary(capability=capability, session_secret_gate=session_secret_gate)


def test_route_capability_and_session_secret_gate_identity_linkage_is_required() -> None:
    capability = _build_capability()
    other_capability = _build_capability()
    other_gate = _build_session_secret_gate(other_capability)

    with pytest.raises(
        ValueError,
        match="session_secret_gate.route_capability must match route_capability",
    ):
        _build_boundary(capability=capability, session_secret_gate=other_gate)


def test_route_id_and_evidence_linkages_are_required() -> None:
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)

    with pytest.raises(ValueError, match="route_id must match route_capability.route_id"):
        _build_boundary(
            capability=capability,
            session_secret_gate=session_secret_gate,
            route_id="route-development-bridge-02",
        )

    _mutate(session_secret_gate, route_id="route-development-bridge-02")

    with pytest.raises(
        ValueError,
        match="session_secret_gate.route_id must match route_capability.route_id",
    ):
        _build_boundary(capability=capability, session_secret_gate=session_secret_gate)

    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)

    with pytest.raises(
        ValueError,
        match="evidence_reference_ids must match route_capability.evidence_reference_ids",
    ):
        _build_boundary(
            capability=capability,
            session_secret_gate=session_secret_gate,
            evidence_reference_ids=("DEV-BRIDGE-EVIDENCE-001", "MUTATED-EVIDENCE"),
        )


def test_blank_ids_and_evidence_are_rejected() -> None:
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)

    with pytest.raises(ValueError, match="boundary_id must be a non-blank string"):
        _build_boundary(
            capability=capability,
            session_secret_gate=session_secret_gate,
            boundary_id=" ",
        )

    with pytest.raises(ValueError, match="route_id must be a non-blank string"):
        _build_boundary(capability=capability, session_secret_gate=session_secret_gate, route_id="")

    with pytest.raises(ValueError, match="reason_codes must be a non-blank string"):
        _build_boundary(
            capability=capability,
            session_secret_gate=session_secret_gate,
            reason_codes=("",),
        )

    with pytest.raises(ValueError, match="evidence_reference_ids must be a non-blank string"):
        _build_boundary(
            capability=capability,
            session_secret_gate=session_secret_gate,
            evidence_reference_ids=("",),
        )


def test_inputs_are_not_mutated_and_equality_is_deterministic() -> None:
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)
    capability_snapshot = _snapshot(capability)
    gate_snapshot = _snapshot(session_secret_gate)

    boundary_a = _build_boundary(capability=capability, session_secret_gate=session_secret_gate)
    boundary_b = _build_boundary(capability=capability, session_secret_gate=session_secret_gate)

    assert _snapshot(capability) == capability_snapshot
    assert _snapshot(session_secret_gate) == gate_snapshot
    assert boundary_a == boundary_b
    assert hash(boundary_a) == hash(boundary_b)


def test_boundary_is_frozen_and_slots_based() -> None:
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)
    boundary = _build_boundary(capability=capability, session_secret_gate=session_secret_gate)

    with pytest.raises(FrozenInstanceError):
        boundary.boundary_id = "mutated"  # type: ignore[misc]


def test_schema_does_not_expose_runtime_network_secret_fields() -> None:
    field_names = tuple(field.name for field in fields(DevelopmentBridgeGateBoundary))
    forbidden_names = {
        "url",
        "host",
        "hostname",
        "ip",
        "ip_address",
        "port",
        "cookie",
        "cookies",
        "token",
        "credentials",
        "runtime_config",
        "executable_path",
        "owner_profile_path",
        "payload",
        "body",
        "private_key",
        "secret_value",
    }

    assert field_names == EXPECTED_FIELD_NAMES
    assert forbidden_names.isdisjoint({name.lower() for name in field_names})

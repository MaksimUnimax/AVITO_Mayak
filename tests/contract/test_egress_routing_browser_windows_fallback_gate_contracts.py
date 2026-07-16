from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass
from types import SimpleNamespace
from typing import Any, cast

import pytest

import mayak.modules.egress_routing as egress_routing
import tests.contract.test_egress_routing_session_secret_gate_contracts as session_contracts
from mayak.modules.egress_routing import (
    ER10A_TASK_ID,
    EgressSessionSecretAuthority,
    EgressSessionSecretGateBoundary,
    FutureBrowserFallbackAuthority,
    FutureBrowserFallbackGateBoundary,
    RouteCapability,
    RouteFamily,
    SessionPolicyStatus,
)
from mayak.modules.egress_routing import (
    browser_windows_fallback_gate as browser_windows_fallback_gate_module,
)

EXPECTED_TASK_ID = "ER-10A-BROWSER-WINDOWS-FALLBACK-FAIL-CLOSED-GATE-20260716-046"

EXPECTED_MODULE_EXPORTS = (
    "ER10A_TASK_ID",
    "FutureBrowserFallbackAuthority",
    "FutureBrowserFallbackGateBoundary",
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
    "ER07E_TASK_ID",
)

EXPECTED_FIELD_NAMES = (
    "boundary_id",
    "authority",
    "route_capability",
    "session_secret_gate",
    "route_family",
    "route_id",
    "owner_fallback_direction_acknowledged",
    "owner_browser_extension_avito_evidence_acknowledged",
    "owner_evidence_production_scale_proof",
    "route_proof_gate_satisfied",
    "windows_operations_security_gate_satisfied",
    "extension_scope_reduction_required",
    "avito_only_automation_scope_required",
    "bounded_assignment_required",
    "safe_result_return_required",
    "browser_worker_pool_preferred",
    "browser_per_beacon_primary_authorized",
    "full_saas_on_windows_authorized",
    "self_editing_extension_authorized",
    "developer_control_editing_authorized",
    "unrelated_automation_targets_authorized",
    "broad_site_permissions_authorized",
    "native_host_implementation_authorized",
    "installer_implementation_authorized",
    "browser_runtime_authorized",
    "windows_agent_runtime_authorized",
    "production_route_authorized",
    "automatic_route_selection_authorized",
    "primary_database_access_authorized",
    "business_state_ownership_authorized",
    "live_avito_traffic_authorized",
    "provider_access_permission_inferred",
    "parser_success_inferred",
    "scan_success_inferred",
    "notification_delivery_inferred",
    "reason_codes",
    "evidence_reference_ids",
)

EXPECTED_TRUE_BOOLEAN_FIELDS = (
    "owner_fallback_direction_acknowledged",
    "extension_scope_reduction_required",
    "avito_only_automation_scope_required",
    "bounded_assignment_required",
    "safe_result_return_required",
    "browser_worker_pool_preferred",
)

EXPECTED_FALSE_BOOLEAN_FIELDS = (
    "owner_evidence_production_scale_proof",
    "route_proof_gate_satisfied",
    "windows_operations_security_gate_satisfied",
    "browser_per_beacon_primary_authorized",
    "full_saas_on_windows_authorized",
    "self_editing_extension_authorized",
    "developer_control_editing_authorized",
    "unrelated_automation_targets_authorized",
    "broad_site_permissions_authorized",
    "native_host_implementation_authorized",
    "installer_implementation_authorized",
    "browser_runtime_authorized",
    "windows_agent_runtime_authorized",
    "production_route_authorized",
    "automatic_route_selection_authorized",
    "primary_database_access_authorized",
    "business_state_ownership_authorized",
    "live_avito_traffic_authorized",
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
    "owner-fallback-direction-acknowledged",
    "browser-windows-fail-closed",
)

EXPECTED_ROUTE_ID = "route-browser-windows-fallback-01"
EXPECTED_CAPABILITY_ID = "cap-browser-windows-fallback-01"
EXPECTED_BOUNDARY_ID = "browser-windows-fallback-boundary-01"
EXPECTED_EVIDENCE_REFERENCE_IDS = session_contracts.EXPECTED_EVIDENCE_REFERENCE_IDS
EXPECTED_ALLOWED_ROUTE_FAMILIES = (
    RouteFamily.BROWSER_EXTENSION_ROUTE,
    RouteFamily.WINDOWS_BROWSER_AGENT_ROUTE,
    RouteFamily.WINDOWS_VM_BROWSER_WORKER_ROUTE,
)
EXPECTED_WINDOWS_FAMILIES = (
    RouteFamily.WINDOWS_BROWSER_AGENT_ROUTE,
    RouteFamily.WINDOWS_VM_BROWSER_WORKER_ROUTE,
)
EXPECTED_BROWSER_EXTENSION_EVIDENCE_MATRIX = {
    RouteFamily.BROWSER_EXTENSION_ROUTE: True,
    RouteFamily.WINDOWS_BROWSER_AGENT_ROUTE: False,
    RouteFamily.WINDOWS_VM_BROWSER_WORKER_ROUTE: False,
}


class TextLike(str):
    pass


class TupleLike(tuple):
    pass


class BoolLike(int):
    pass


def _mutate(record: object, **changes: object) -> None:
    for field_name, value in changes.items():
        object.__setattr__(record, field_name, value)


def _snapshot(record: object) -> tuple[object, ...]:
    return tuple(getattr(record, field.name) for field in fields(cast(Any, record)))


def _build_capability(
    *,
    route_id: str = EXPECTED_ROUTE_ID,
    capability_id: str = EXPECTED_CAPABILITY_ID,
    evidence_reference_ids: tuple[str, ...] = EXPECTED_EVIDENCE_REFERENCE_IDS,
) -> RouteCapability:
    capability = session_contracts._build_capability(  # type: ignore[attr-defined]
        route_id=route_id,
        capability_id=capability_id,
        evidence_reference_ids=evidence_reference_ids,
    )
    assert type(capability) is RouteCapability
    return capability


def _build_session_secret_gate(
    capability: RouteCapability,
    *,
    boundary_id: str = "session-secret-gate-boundary-01",
    session_policy_status: SessionPolicyStatus = SessionPolicyStatus.PROHIBITED,
) -> EgressSessionSecretGateBoundary:
    boundary = session_contracts._build_boundary(  # type: ignore[attr-defined]
        capability=capability,
        boundary_id=boundary_id,
        route_id=capability.route_id,
        session_policy_status=session_policy_status,
    )
    assert type(boundary) is EgressSessionSecretGateBoundary
    return boundary


def _build_boundary(
    *,
    capability: RouteCapability,
    session_secret_gate: EgressSessionSecretGateBoundary,
    route_family: RouteFamily = RouteFamily.BROWSER_EXTENSION_ROUTE,
    boundary_id: str = EXPECTED_BOUNDARY_ID,
    authority: FutureBrowserFallbackAuthority = (
        FutureBrowserFallbackAuthority.EGRESS_ROUTING_SERVER
    ),
    route_id: str = EXPECTED_ROUTE_ID,
    owner_fallback_direction_acknowledged: bool = True,
    owner_browser_extension_avito_evidence_acknowledged: bool = True,
    owner_evidence_production_scale_proof: bool = False,
    route_proof_gate_satisfied: bool = False,
    windows_operations_security_gate_satisfied: bool = False,
    extension_scope_reduction_required: bool = True,
    avito_only_automation_scope_required: bool = True,
    bounded_assignment_required: bool = True,
    safe_result_return_required: bool = True,
    browser_worker_pool_preferred: bool = True,
    browser_per_beacon_primary_authorized: bool = False,
    full_saas_on_windows_authorized: bool = False,
    self_editing_extension_authorized: bool = False,
    developer_control_editing_authorized: bool = False,
    unrelated_automation_targets_authorized: bool = False,
    broad_site_permissions_authorized: bool = False,
    native_host_implementation_authorized: bool = False,
    installer_implementation_authorized: bool = False,
    browser_runtime_authorized: bool = False,
    windows_agent_runtime_authorized: bool = False,
    production_route_authorized: bool = False,
    automatic_route_selection_authorized: bool = False,
    primary_database_access_authorized: bool = False,
    business_state_ownership_authorized: bool = False,
    live_avito_traffic_authorized: bool = False,
    provider_access_permission_inferred: bool = False,
    parser_success_inferred: bool = False,
    scan_success_inferred: bool = False,
    notification_delivery_inferred: bool = False,
    reason_codes: tuple[str, ...] = EXPECTED_REASON_CODES,
    evidence_reference_ids: tuple[str, ...] = EXPECTED_EVIDENCE_REFERENCE_IDS,
) -> FutureBrowserFallbackGateBoundary:
    boundary = FutureBrowserFallbackGateBoundary(
        boundary_id=boundary_id,
        authority=authority,
        route_capability=capability,
        session_secret_gate=session_secret_gate,
        route_family=route_family,
        route_id=route_id,
        owner_fallback_direction_acknowledged=owner_fallback_direction_acknowledged,
        owner_browser_extension_avito_evidence_acknowledged=owner_browser_extension_avito_evidence_acknowledged,
        owner_evidence_production_scale_proof=owner_evidence_production_scale_proof,
        route_proof_gate_satisfied=route_proof_gate_satisfied,
        windows_operations_security_gate_satisfied=windows_operations_security_gate_satisfied,
        extension_scope_reduction_required=extension_scope_reduction_required,
        avito_only_automation_scope_required=avito_only_automation_scope_required,
        bounded_assignment_required=bounded_assignment_required,
        safe_result_return_required=safe_result_return_required,
        browser_worker_pool_preferred=browser_worker_pool_preferred,
        browser_per_beacon_primary_authorized=browser_per_beacon_primary_authorized,
        full_saas_on_windows_authorized=full_saas_on_windows_authorized,
        self_editing_extension_authorized=self_editing_extension_authorized,
        developer_control_editing_authorized=developer_control_editing_authorized,
        unrelated_automation_targets_authorized=unrelated_automation_targets_authorized,
        broad_site_permissions_authorized=broad_site_permissions_authorized,
        native_host_implementation_authorized=native_host_implementation_authorized,
        installer_implementation_authorized=installer_implementation_authorized,
        browser_runtime_authorized=browser_runtime_authorized,
        windows_agent_runtime_authorized=windows_agent_runtime_authorized,
        production_route_authorized=production_route_authorized,
        automatic_route_selection_authorized=automatic_route_selection_authorized,
        primary_database_access_authorized=primary_database_access_authorized,
        business_state_ownership_authorized=business_state_ownership_authorized,
        live_avito_traffic_authorized=live_avito_traffic_authorized,
        provider_access_permission_inferred=provider_access_permission_inferred,
        parser_success_inferred=parser_success_inferred,
        scan_success_inferred=scan_success_inferred,
        notification_delivery_inferred=notification_delivery_inferred,
        reason_codes=reason_codes,
        evidence_reference_ids=evidence_reference_ids,
    )
    assert type(boundary) is FutureBrowserFallbackGateBoundary
    return boundary


def test_module_exports_are_exact_and_ordered() -> None:
    assert ER10A_TASK_ID == EXPECTED_TASK_ID
    assert browser_windows_fallback_gate_module.ER10A_TASK_ID == EXPECTED_TASK_ID
    assert type(browser_windows_fallback_gate_module.__all__) is tuple
    assert browser_windows_fallback_gate_module.__all__ == EXPECTED_MODULE_EXPORTS
    assert tuple(browser_windows_fallback_gate_module.__all__) == EXPECTED_MODULE_EXPORTS
    assert len(browser_windows_fallback_gate_module.__all__) == len(
        set(browser_windows_fallback_gate_module.__all__)
    )
    assert all(
        hasattr(browser_windows_fallback_gate_module, name)
        for name in EXPECTED_MODULE_EXPORTS
    )


@pytest.mark.parametrize(
    ("route_family", "browser_extension_evidence"),
    [
        (RouteFamily.BROWSER_EXTENSION_ROUTE, True),
        (RouteFamily.WINDOWS_BROWSER_AGENT_ROUTE, False),
        (RouteFamily.WINDOWS_VM_BROWSER_WORKER_ROUTE, False),
    ],
)
def test_allowed_route_families_are_accepted(
    route_family: RouteFamily,
    browser_extension_evidence: bool,
) -> None:
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)
    before_capability = _snapshot(capability)
    before_gate = _snapshot(session_secret_gate)

    boundary = _build_boundary(
        capability=capability,
        session_secret_gate=session_secret_gate,
        route_family=route_family,
        owner_browser_extension_avito_evidence_acknowledged=browser_extension_evidence,
    )

    assert is_dataclass(boundary) is True
    assert type(boundary) is FutureBrowserFallbackGateBoundary
    assert boundary.authority is FutureBrowserFallbackAuthority.EGRESS_ROUTING_SERVER
    assert boundary.route_capability is capability
    assert boundary.session_secret_gate is session_secret_gate
    assert boundary.session_secret_gate.route_capability is capability
    assert boundary.session_secret_gate.session_policy_status is capability.session_policy_status
    assert boundary.route_family is route_family
    assert boundary.route_id == capability.route_id
    assert boundary.route_id == session_secret_gate.route_id
    assert boundary.evidence_reference_ids == capability.evidence_reference_ids
    assert boundary.evidence_reference_ids == session_secret_gate.evidence_reference_ids
    assert boundary.evidence_reference_ids is capability.evidence_reference_ids
    assert tuple(field.name for field in fields(boundary)) == EXPECTED_FIELD_NAMES
    assert type(boundary).__slots__ == EXPECTED_FIELD_NAMES
    assert tuple(field.name for field in fields(boundary)) == EXPECTED_FIELD_NAMES
    assert _snapshot(capability) == before_capability
    assert _snapshot(session_secret_gate) == before_gate

    assert boundary.owner_fallback_direction_acknowledged is True
    assert (
        boundary.owner_browser_extension_avito_evidence_acknowledged
        is browser_extension_evidence
    )
    assert boundary.owner_evidence_production_scale_proof is False
    for field_name in EXPECTED_TRUE_BOOLEAN_FIELDS:
        value = getattr(boundary, field_name)
        assert type(value) is bool
        assert value is True
    for field_name in EXPECTED_FALSE_BOOLEAN_FIELDS:
        value = getattr(boundary, field_name)
        assert type(value) is bool
        assert value is False


@pytest.mark.parametrize(
    "route_family",
    [
        RouteFamily.LINUX_REFERENCE_STYLE_ROUTE,
        RouteFamily.RUSSIAN_RESIDENTIAL_ROUTE,
        RouteFamily.OWNER_DEVELOPMENT_BRIDGE_ROUTE,
    ],
)
def test_all_other_route_families_are_rejected(route_family: RouteFamily) -> None:
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)

    with pytest.raises(ValueError, match="route_family"):
        _build_boundary(
            capability=capability,
            session_secret_gate=session_secret_gate,
            route_family=route_family,
            owner_browser_extension_avito_evidence_acknowledged=False,
        )


@pytest.mark.parametrize("route_family", EXPECTED_WINDOWS_FAMILIES)
def test_browser_extension_evidence_does_not_transfer_to_windows_families(
    route_family: RouteFamily,
) -> None:
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)

    with pytest.raises(ValueError, match="owner_browser_extension_avito_evidence_acknowledged"):
        _build_boundary(
            capability=capability,
            session_secret_gate=session_secret_gate,
            route_family=route_family,
            owner_browser_extension_avito_evidence_acknowledged=True,
        )


def test_browser_extension_family_requires_owner_evidence_flag_true() -> None:
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)

    with pytest.raises(ValueError, match="owner_browser_extension_avito_evidence_acknowledged"):
        _build_boundary(
            capability=capability,
            session_secret_gate=session_secret_gate,
            route_family=RouteFamily.BROWSER_EXTENSION_ROUTE,
            owner_browser_extension_avito_evidence_acknowledged=False,
        )


def test_valid_er09a_source_is_accepted_and_inputs_remain_exact() -> None:
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)
    capability_before = _snapshot(capability)
    session_secret_gate_before = _snapshot(session_secret_gate)
    boundary = _build_boundary(
        capability=capability,
        session_secret_gate=session_secret_gate,
        route_family=RouteFamily.BROWSER_EXTENSION_ROUTE,
    )

    assert type(boundary.session_secret_gate.authority) is EgressSessionSecretAuthority
    assert (
        boundary.session_secret_gate.authority
        is EgressSessionSecretAuthority.EGRESS_ROUTING_SERVER
    )
    assert boundary.route_capability is capability
    assert boundary.session_secret_gate is session_secret_gate
    assert boundary.session_secret_gate.route_capability is capability
    assert boundary.session_secret_gate.route_id == EXPECTED_ROUTE_ID
    assert boundary.route_id == capability.route_id
    assert boundary.route_id == session_secret_gate.route_id
    assert boundary.session_secret_gate.session_policy_status is SessionPolicyStatus.PROHIBITED
    assert boundary.session_secret_gate.session_policy_status is capability.session_policy_status
    assert boundary.evidence_reference_ids is capability.evidence_reference_ids
    assert boundary.evidence_reference_ids == session_secret_gate.evidence_reference_ids
    assert boundary.session_secret_gate.evidence_reference_ids == EXPECTED_EVIDENCE_REFERENCE_IDS
    assert boundary.session_secret_gate.reason_codes == session_contracts.EXPECTED_REASON_CODES
    assert _snapshot(capability) == capability_before
    assert _snapshot(session_secret_gate) == session_secret_gate_before

    for field_name in EXPECTED_ER09A_TRUE_BOOLEAN_FIELDS:
        value = getattr(boundary.session_secret_gate, field_name)
        assert type(value) is bool
        assert value is True

    for field_name in EXPECTED_ER09A_FALSE_BOOLEAN_FIELDS:
        value = getattr(boundary.session_secret_gate, field_name)
        assert type(value) is bool
        assert value is False


@pytest.mark.parametrize("field_name", EXPECTED_ER09A_FALSE_BOOLEAN_FIELDS)
def test_er09a_false_boolean_fields_reject_true_tampering(field_name: str) -> None:
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)
    _mutate(session_secret_gate, **{field_name: True})

    with pytest.raises(ValueError, match=field_name):
        _build_boundary(
            capability=capability,
            session_secret_gate=session_secret_gate,
            route_family=RouteFamily.BROWSER_EXTENSION_ROUTE,
        )


@pytest.mark.parametrize("field_name", EXPECTED_ER09A_TRUE_BOOLEAN_FIELDS)
def test_er09a_true_boolean_fields_reject_false_tampering(field_name: str) -> None:
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)
    _mutate(session_secret_gate, **{field_name: False})

    with pytest.raises(ValueError, match=field_name):
        _build_boundary(
            capability=capability,
            session_secret_gate=session_secret_gate,
            route_family=RouteFamily.BROWSER_EXTENSION_ROUTE,
        )


def test_er09a_authority_lookalike_is_rejected() -> None:
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)
    _mutate(
        session_secret_gate,
        authority=SimpleNamespace(name="EGRESS_ROUTING_SERVER", value="EGRESS_ROUTING_SERVER"),
    )

    with pytest.raises(ValueError, match="authority"):
        _build_boundary(
            capability=capability,
            session_secret_gate=session_secret_gate,
            route_family=RouteFamily.BROWSER_EXTENSION_ROUTE,
        )


def test_er09a_route_id_tampering_is_rejected() -> None:
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)
    _mutate(session_secret_gate, route_id="route-browser-windows-fallback-02")

    with pytest.raises(ValueError, match="route_id"):
        _build_boundary(
            capability=capability,
            session_secret_gate=session_secret_gate,
            route_family=RouteFamily.BROWSER_EXTENSION_ROUTE,
        )


def test_er09a_approved_reference_only_session_policy_is_rejected() -> None:
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)
    _mutate(
        session_secret_gate,
        session_policy_status=SessionPolicyStatus.APPROVED_REFERENCE_ONLY,
    )

    with pytest.raises(ValueError, match="session_policy_status"):
        _build_boundary(
            capability=capability,
            session_secret_gate=session_secret_gate,
            route_family=RouteFamily.BROWSER_EXTENSION_ROUTE,
        )


def test_er09a_session_policy_mismatch_is_rejected() -> None:
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)
    _mutate(
        session_secret_gate,
        session_policy_status=SessionPolicyStatus.BLOCKED_PENDING_ISOLATED_PROJECT_SESSION_GATE,
    )

    with pytest.raises(ValueError, match="session_policy_status"):
        _build_boundary(
            capability=capability,
            session_secret_gate=session_secret_gate,
            route_family=RouteFamily.BROWSER_EXTENSION_ROUTE,
        )


def test_er09a_evidence_reference_ids_tampering_is_rejected() -> None:
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)
    _mutate(session_secret_gate, evidence_reference_ids=("tampered-evidence-reference",))

    with pytest.raises(ValueError, match="evidence_reference_ids"):
        _build_boundary(
            capability=capability,
            session_secret_gate=session_secret_gate,
            route_family=RouteFamily.BROWSER_EXTENSION_ROUTE,
        )


def test_er09a_route_capability_identity_tampering_is_rejected() -> None:
    capability = _build_capability()
    other_capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)
    _mutate(session_secret_gate, route_capability=other_capability)

    with pytest.raises(ValueError, match="route_capability"):
        _build_boundary(
            capability=capability,
            session_secret_gate=session_secret_gate,
            route_family=RouteFamily.BROWSER_EXTENSION_ROUTE,
        )


def test_er09a_bool_like_value_inside_tampered_gate_is_rejected() -> None:
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)
    _mutate(session_secret_gate, runtime_session_creation_authorized=BoolLike(1))

    with pytest.raises(ValueError, match="runtime_session_creation_authorized"):
        _build_boundary(
            capability=capability,
            session_secret_gate=session_secret_gate,
            route_family=RouteFamily.BROWSER_EXTENSION_ROUTE,
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("boundary_id", " "),
        ("route_id", " "),
        ("reason_codes", (" ",)),
        ("evidence_reference_ids", (" ",)),
    ],
)
def test_blank_text_inputs_are_rejected(field_name: str, value: object) -> None:
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)
    kwargs = {
        "capability": capability,
        "session_secret_gate": session_secret_gate,
        "route_family": RouteFamily.BROWSER_EXTENSION_ROUTE,
    }
    kwargs[field_name] = value

    with pytest.raises(ValueError):
        _build_boundary(**cast(Any, kwargs))


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("boundary_id", TextLike("boundary-01")),
        ("route_id", TextLike("route-01")),
        ("reason_codes", TupleLike(("reason-01",))),
        ("evidence_reference_ids", TupleLike(EXPECTED_EVIDENCE_REFERENCE_IDS)),
    ],
)
def test_text_and_tuple_subclasses_are_rejected(field_name: str, value: object) -> None:
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)
    kwargs = {
        "capability": capability,
        "session_secret_gate": session_secret_gate,
        "route_family": RouteFamily.BROWSER_EXTENSION_ROUTE,
    }
    kwargs[field_name] = value

    with pytest.raises(ValueError):
        _build_boundary(**cast(Any, kwargs))


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("authority", SimpleNamespace(name="EGRESS_ROUTING_SERVER", value="EGRESS_ROUTING_SERVER")),
        (
            "route_family",
            SimpleNamespace(name="BROWSER_EXTENSION_ROUTE", value="BROWSER_EXTENSION_ROUTE"),
        ),
    ],
)
def test_enum_lookalikes_are_rejected(field_name: str, value: object) -> None:
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)
    kwargs = {
        "capability": capability,
        "session_secret_gate": session_secret_gate,
        "route_family": RouteFamily.BROWSER_EXTENSION_ROUTE,
    }
    kwargs[field_name] = value

    with pytest.raises(ValueError):
        _build_boundary(**cast(Any, kwargs))


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("owner_fallback_direction_acknowledged", BoolLike(1)),
        ("browser_runtime_authorized", BoolLike(0)),
        ("provider_access_permission_inferred", 1),
    ],
)
def test_bool_lookalikes_are_rejected(field_name: str, value: object) -> None:
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)
    kwargs = {
        "capability": capability,
        "session_secret_gate": session_secret_gate,
        "route_family": RouteFamily.BROWSER_EXTENSION_ROUTE,
    }
    kwargs[field_name] = value

    with pytest.raises(ValueError):
        _build_boundary(**cast(Any, kwargs))


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("route_proof_gate_satisfied", True),
        ("windows_operations_security_gate_satisfied", True),
        ("owner_evidence_production_scale_proof", True),
        ("browser_per_beacon_primary_authorized", True),
        ("full_saas_on_windows_authorized", True),
        ("browser_runtime_authorized", True),
        ("production_route_authorized", True),
        ("live_avito_traffic_authorized", True),
        ("parser_success_inferred", True),
        ("scan_success_inferred", True),
        ("notification_delivery_inferred", True),
    ],
)
def test_fail_closed_flags_reject_wrong_values(field_name: str, value: object) -> None:
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)
    kwargs = {
        "capability": capability,
        "session_secret_gate": session_secret_gate,
        "route_family": RouteFamily.BROWSER_EXTENSION_ROUTE,
    }
    kwargs[field_name] = value

    with pytest.raises(ValueError):
        _build_boundary(**cast(Any, kwargs))


def test_frozen_and_slotted_behavior_is_exact() -> None:
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)
    boundary = _build_boundary(
        capability=capability,
        session_secret_gate=session_secret_gate,
        route_family=RouteFamily.BROWSER_EXTENSION_ROUTE,
    )

    assert is_dataclass(boundary) is True
    assert boundary.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
    assert boundary.__dataclass_params__.slots is True  # type: ignore[attr-defined]
    assert not hasattr(boundary, "__dict__")
    with pytest.raises(FrozenInstanceError):
        boundary.boundary_id = "other-boundary"  # type: ignore[misc]


def test_deterministic_equality_and_hash_are_value_based() -> None:
    capability_a = _build_capability()
    gate_a = _build_session_secret_gate(capability_a)
    boundary_a = _build_boundary(
        capability=capability_a,
        session_secret_gate=gate_a,
        route_family=RouteFamily.BROWSER_EXTENSION_ROUTE,
    )

    capability_b = _build_capability()
    gate_b = _build_session_secret_gate(capability_b)
    boundary_b = _build_boundary(
        capability=capability_b,
        session_secret_gate=gate_b,
        route_family=RouteFamily.BROWSER_EXTENSION_ROUTE,
    )
    boundary_c = _build_boundary(
        capability=capability_b,
        session_secret_gate=gate_b,
        route_family=RouteFamily.WINDOWS_BROWSER_AGENT_ROUTE,
        owner_browser_extension_avito_evidence_acknowledged=False,
    )

    assert boundary_a == boundary_b
    assert hash(boundary_a) == hash(boundary_b)
    assert boundary_a != boundary_c


def test_inputs_are_not_mutated_during_construction() -> None:
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)
    capability_before = _snapshot(capability)
    gate_before = _snapshot(session_secret_gate)

    _build_boundary(
        capability=capability,
        session_secret_gate=session_secret_gate,
        route_family=RouteFamily.BROWSER_EXTENSION_ROUTE,
    )

    assert _snapshot(capability) == capability_before
    assert _snapshot(session_secret_gate) == gate_before


def test_boundary_schema_excludes_runtime_and_secret_fields() -> None:
    capability = _build_capability()
    session_secret_gate = _build_session_secret_gate(capability)
    boundary = _build_boundary(
        capability=capability,
        session_secret_gate=session_secret_gate,
        route_family=RouteFamily.BROWSER_EXTENSION_ROUTE,
    )
    field_names = tuple(field.name for field in fields(boundary))

    assert field_names == EXPECTED_FIELD_NAMES
    assert len(field_names) == 37
    assert {
        "url",
        "host",
        "hostname",
        "ip",
        "port",
        "cookie",
        "cookies",
        "session",
        "token",
        "private_key",
        "secret_value",
        "runtime_configuration",
        "browser_profile_path",
        "executable_path",
    }.isdisjoint(field_names)


def test_package_exports_include_er10a_in_expected_position() -> None:
    exports = tuple(egress_routing.__all__)
    start = exports.index("ER08B_TASK_ID")

    assert (
        exports[start : start + len(EXPECTED_PACKAGE_EXPORT_SLICE)]
        == EXPECTED_PACKAGE_EXPORT_SLICE
    )
    assert hasattr(egress_routing, "ER10A_TASK_ID")
    assert hasattr(egress_routing, "FutureBrowserFallbackAuthority")
    assert hasattr(egress_routing, "FutureBrowserFallbackGateBoundary")

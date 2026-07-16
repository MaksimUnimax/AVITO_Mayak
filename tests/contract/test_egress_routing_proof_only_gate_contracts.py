from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass
from types import SimpleNamespace
from typing import Any, cast

import pytest

import mayak.modules.egress_routing as egress_routing
import mayak.modules.egress_routing.proof_only_gate as proof_only_gate_module
import mayak.modules.egress_routing.session_secret_gate as session_secret_gate_module
from mayak.modules.egress_routing import (
    ER13A_TASK_ID,
    EgressProofOnlyAuthority,
    EgressProofOnlyGateBoundary,
    EgressSessionSecretAuthority,
    EgressSessionSecretGateBoundary,
    RouteCapability,
    RouteEvidenceStatus,
    RouteFamily,
    SessionPolicyStatus,
)

EXPECTED_TASK_ID = "ER-13A-PROOF-ONLY-FAIL-CLOSED-GATE-20260716-051"

EXPECTED_MODULE_EXPORTS = (
    "ER13A_TASK_ID",
    "EgressProofOnlyAuthority",
    "EgressProofOnlyGateBoundary",
)

EXPECTED_PACKAGE_EXPORT_SLICE = (
    "ER12A_TASK_ID",
    "SafeEgressDiagnosticAuthority",
    "SafeEgressDiagnosticGateBoundary",
    "ER13A_TASK_ID",
    "EgressProofOnlyAuthority",
    "EgressProofOnlyGateBoundary",
    "ER07E_TASK_ID",
)

EXPECTED_CAPABILITY_FIELD_NAMES = (
    "capability_id",
    "route_id",
    "destination_scope",
    "operation_classes",
    "unsupported_classes",
    "evidence_reference_ids",
    "evidence_status",
    "session_policy_status",
)

EXPECTED_SESSION_FIELD_NAMES = (
    "boundary_id",
    "authority",
    "route_capability",
    "route_id",
    "session_policy_status",
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
    "safe_reference_only",
    "rotation_required",
    "revocation_required",
    "redacted_diagnostics_required",
    "secret_logging_authorized",
    "secret_report_authorized",
    "secret_git_storage_authorized",
    "runtime_session_creation_authorized",
    "provider_access_permission_inferred",
    "parser_success_inferred",
    "scan_success_inferred",
    "notification_delivery_inferred",
    "reason_codes",
    "evidence_reference_ids",
)

EXPECTED_FIELD_NAMES = (
    "boundary_id",
    "authority",
    "route_capability",
    "session_secret_gate",
    "route_family",
    "route_id",
    "primary_linux_reference_style_direction_acknowledged",
    "russian_residential_future_route_direction_acknowledged",
    "owner_development_bridge_direction_acknowledged",
    "browser_extension_owner_avito_evidence_acknowledged",
    "windows_vm_browser_worker_fallback_direction_acknowledged",
    "separate_explicit_owner_proof_task_required",
    "legal_and_access_gate_required",
    "exact_source_scope_required",
    "maximum_attempts_required",
    "maximum_duration_required",
    "route_identity_required",
    "no_secrets_logging_required",
    "no_raw_payload_retention_required",
    "no_captcha_solving_required",
    "bounded_repeatability_check_required",
    "explicit_stop_conditions_required",
    "clear_evidence_report_required",
    "current_explicit_owner_proof_scope_approved",
    "legal_and_access_gate_satisfied",
    "exact_source_scope_defined",
    "attempt_bound_defined",
    "duration_bound_defined",
    "proof_execution_authorized",
    "live_provider_traffic_authorized",
    "mass_requests_authorized",
    "production_scheduler_integration_authorized",
    "database_persistence_authorized",
    "notification_delivery_authorized",
    "unbounded_retry_authorized",
    "uncontrolled_fallback_authorized",
    "captcha_solving_authorized",
    "raw_payload_retention_authorized",
    "secret_or_cookie_disclosure_authorized",
    "provider_access_permission_inferred",
    "parser_success_inferred",
    "scan_success_inferred",
    "notification_delivery_inferred",
    "production_readiness_inferred",
    "scalability_proof_inferred",
    "reason_codes",
    "evidence_reference_ids",
)

EXPECTED_FALSE_BOOLEAN_FIELDS = (
    "current_explicit_owner_proof_scope_approved",
    "legal_and_access_gate_satisfied",
    "exact_source_scope_defined",
    "attempt_bound_defined",
    "duration_bound_defined",
    "proof_execution_authorized",
    "live_provider_traffic_authorized",
    "mass_requests_authorized",
    "production_scheduler_integration_authorized",
    "database_persistence_authorized",
    "notification_delivery_authorized",
    "unbounded_retry_authorized",
    "uncontrolled_fallback_authorized",
    "captcha_solving_authorized",
    "raw_payload_retention_authorized",
    "secret_or_cookie_disclosure_authorized",
    "provider_access_permission_inferred",
    "parser_success_inferred",
    "scan_success_inferred",
    "notification_delivery_inferred",
    "production_readiness_inferred",
    "scalability_proof_inferred",
)

EXPECTED_DIRECTION_FIELDS = (
    "primary_linux_reference_style_direction_acknowledged",
    "russian_residential_future_route_direction_acknowledged",
    "owner_development_bridge_direction_acknowledged",
    "browser_extension_owner_avito_evidence_acknowledged",
    "windows_vm_browser_worker_fallback_direction_acknowledged",
)

EXPECTED_TRUE_BOOLEAN_FIELDS = (
    "separate_explicit_owner_proof_task_required",
    "legal_and_access_gate_required",
    "exact_source_scope_required",
    "maximum_attempts_required",
    "maximum_duration_required",
    "route_identity_required",
    "no_secrets_logging_required",
    "no_raw_payload_retention_required",
    "no_captcha_solving_required",
    "bounded_repeatability_check_required",
    "explicit_stop_conditions_required",
    "clear_evidence_report_required",
)

EXPECTED_REASON_CODES = (
    "proof-only-execution-blocked",
    "explicit-owner-proof-task-required",
    "legal-access-and-scope-gates-unsatisfied",
)

EXPECTED_EVIDENCE_REFERENCE_IDS = ("proof-only-evidence-01", "proof-only-evidence-02")
EXPECTED_CAPABILITY_ID = "cap-proof-only-01"
EXPECTED_ROUTE_ID = "route-proof-only-01"
EXPECTED_BOUNDARY_ID = "proof-only-boundary-01"
EXPECTED_SESSION_BOUNDARY_ID = "session-secret-boundary-01"

EXPECTED_SESSION_FALSE_FIELDS = (
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

EXPECTED_SESSION_TRUE_FIELDS = (
    "safe_reference_only",
    "rotation_required",
    "revocation_required",
    "redacted_diagnostics_required",
)

EXPECTED_ALLOWED_FAMILY_MATRIX = (
    (
        RouteFamily.LINUX_REFERENCE_STYLE_ROUTE,
        "primary_linux_reference_style_direction_acknowledged",
    ),
    (
        RouteFamily.RUSSIAN_RESIDENTIAL_ROUTE,
        "russian_residential_future_route_direction_acknowledged",
    ),
    (
        RouteFamily.OWNER_DEVELOPMENT_BRIDGE_ROUTE,
        "owner_development_bridge_direction_acknowledged",
    ),
    (
        RouteFamily.BROWSER_EXTENSION_ROUTE,
        "browser_extension_owner_avito_evidence_acknowledged",
    ),
    (
        RouteFamily.WINDOWS_VM_BROWSER_WORKER_ROUTE,
        "windows_vm_browser_worker_fallback_direction_acknowledged",
    ),
)

EXPECTED_BOOLEANS_FOR_LOOKALIKE_GUARD = (
    EXPECTED_DIRECTION_FIELDS + EXPECTED_FALSE_BOOLEAN_FIELDS + EXPECTED_TRUE_BOOLEAN_FIELDS
)


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
    capability_id: str = EXPECTED_CAPABILITY_ID,
    route_id: str = EXPECTED_ROUTE_ID,
    destination_scope: tuple[str, ...] = ("proof-only-destination",),
    operation_classes: tuple[str, ...] = ("proof-only-execution",),
    unsupported_classes: tuple[str, ...] = ("browser-agent-runtime",),
    evidence_reference_ids: tuple[str, ...] = EXPECTED_EVIDENCE_REFERENCE_IDS,
    evidence_status: RouteEvidenceStatus = RouteEvidenceStatus.CURRENT,
    session_policy_status: SessionPolicyStatus = SessionPolicyStatus.PROHIBITED,
) -> RouteCapability:
    capability = RouteCapability(
        capability_id=capability_id,
        route_id=route_id,
        destination_scope=destination_scope,
        operation_classes=operation_classes,
        unsupported_classes=unsupported_classes,
        evidence_reference_ids=evidence_reference_ids,
        evidence_status=evidence_status,
        session_policy_status=session_policy_status,
    )
    assert type(capability) is RouteCapability
    assert tuple(field.name for field in fields(capability)) == EXPECTED_CAPABILITY_FIELD_NAMES
    return capability


def _build_session_gate(
    capability: RouteCapability,
    *,
    boundary_id: str = EXPECTED_SESSION_BOUNDARY_ID,
    authority: EgressSessionSecretAuthority = EgressSessionSecretAuthority.EGRESS_ROUTING_SERVER,
    route_id: str = EXPECTED_ROUTE_ID,
    session_policy_status: SessionPolicyStatus = SessionPolicyStatus.PROHIBITED,
    **overrides: object,
) -> EgressSessionSecretGateBoundary:
    kwargs: dict[str, object] = {
        "boundary_id": boundary_id,
        "authority": authority,
        "route_capability": capability,
        "route_id": route_id,
        "session_policy_status": session_policy_status,
        "isolated_project_session_gate_satisfied": False,
        "project_owned_session_authorized": False,
        "project_owned_cookie_profile_authorized": False,
        "personal_browser_profile_access_authorized": False,
        "browser_password_access_authorized": False,
        "owner_private_session_default_authorized": False,
        "foreign_or_unrelated_cookie_reuse_authorized": False,
        "raw_cookie_material_authorized": False,
        "raw_session_token_material_authorized": False,
        "raw_credential_material_authorized": False,
        "safe_reference_only": True,
        "rotation_required": True,
        "revocation_required": True,
        "redacted_diagnostics_required": True,
        "secret_logging_authorized": False,
        "secret_report_authorized": False,
        "secret_git_storage_authorized": False,
        "runtime_session_creation_authorized": False,
        "provider_access_permission_inferred": False,
        "parser_success_inferred": False,
        "scan_success_inferred": False,
        "notification_delivery_inferred": False,
        "reason_codes": ("safe-reference-only",),
        "evidence_reference_ids": capability.evidence_reference_ids,
    }
    kwargs.update(overrides)
    gate = cast(Any, EgressSessionSecretGateBoundary)(**kwargs)
    assert type(gate) is EgressSessionSecretGateBoundary
    assert tuple(field.name for field in fields(gate)) == EXPECTED_SESSION_FIELD_NAMES
    return gate


def _build_boundary(
    capability: RouteCapability,
    session_gate: EgressSessionSecretGateBoundary,
    *,
    route_family: RouteFamily = RouteFamily.LINUX_REFERENCE_STYLE_ROUTE,
    boundary_id: str = EXPECTED_BOUNDARY_ID,
    authority: EgressProofOnlyAuthority = EgressProofOnlyAuthority.EGRESS_ROUTING_SERVER,
    route_id: str = EXPECTED_ROUTE_ID,
    **overrides: object,
) -> EgressProofOnlyGateBoundary:
    direction_flags = {
        "primary_linux_reference_style_direction_acknowledged": False,
        "russian_residential_future_route_direction_acknowledged": False,
        "owner_development_bridge_direction_acknowledged": False,
        "browser_extension_owner_avito_evidence_acknowledged": False,
        "windows_vm_browser_worker_fallback_direction_acknowledged": False,
    }
    direction_field = {
        RouteFamily.LINUX_REFERENCE_STYLE_ROUTE: (
            "primary_linux_reference_style_direction_acknowledged"
        ),
        RouteFamily.RUSSIAN_RESIDENTIAL_ROUTE: (
            "russian_residential_future_route_direction_acknowledged"
        ),
        RouteFamily.OWNER_DEVELOPMENT_BRIDGE_ROUTE: (
            "owner_development_bridge_direction_acknowledged"
        ),
        RouteFamily.BROWSER_EXTENSION_ROUTE: (
            "browser_extension_owner_avito_evidence_acknowledged"
        ),
        RouteFamily.WINDOWS_VM_BROWSER_WORKER_ROUTE: (
            "windows_vm_browser_worker_fallback_direction_acknowledged"
        ),
    }.get(route_family)
    if direction_field is not None:
        direction_flags[direction_field] = True

    kwargs: dict[str, object] = {
        "boundary_id": boundary_id,
        "authority": authority,
        "route_capability": capability,
        "session_secret_gate": session_gate,
        "route_family": route_family,
        "route_id": route_id,
        **direction_flags,
        "separate_explicit_owner_proof_task_required": True,
        "legal_and_access_gate_required": True,
        "exact_source_scope_required": True,
        "maximum_attempts_required": True,
        "maximum_duration_required": True,
        "route_identity_required": True,
        "no_secrets_logging_required": True,
        "no_raw_payload_retention_required": True,
        "no_captcha_solving_required": True,
        "bounded_repeatability_check_required": True,
        "explicit_stop_conditions_required": True,
        "clear_evidence_report_required": True,
        "current_explicit_owner_proof_scope_approved": False,
        "legal_and_access_gate_satisfied": False,
        "exact_source_scope_defined": False,
        "attempt_bound_defined": False,
        "duration_bound_defined": False,
        "proof_execution_authorized": False,
        "live_provider_traffic_authorized": False,
        "mass_requests_authorized": False,
        "production_scheduler_integration_authorized": False,
        "database_persistence_authorized": False,
        "notification_delivery_authorized": False,
        "unbounded_retry_authorized": False,
        "uncontrolled_fallback_authorized": False,
        "captcha_solving_authorized": False,
        "raw_payload_retention_authorized": False,
        "secret_or_cookie_disclosure_authorized": False,
        "provider_access_permission_inferred": False,
        "parser_success_inferred": False,
        "scan_success_inferred": False,
        "notification_delivery_inferred": False,
        "production_readiness_inferred": False,
        "scalability_proof_inferred": False,
        "reason_codes": EXPECTED_REASON_CODES,
        "evidence_reference_ids": capability.evidence_reference_ids,
    }
    kwargs.update(overrides)
    boundary = cast(Any, EgressProofOnlyGateBoundary)(**kwargs)
    assert type(boundary) is EgressProofOnlyGateBoundary
    return boundary


def _build_valid_triplet(
    route_family: RouteFamily = RouteFamily.LINUX_REFERENCE_STYLE_ROUTE,
) -> tuple[RouteCapability, EgressSessionSecretGateBoundary, EgressProofOnlyGateBoundary]:
    capability = _build_capability()
    session_gate = _build_session_gate(capability)
    boundary = _build_boundary(capability, session_gate, route_family=route_family)
    return capability, session_gate, boundary


def _boundary_kwargs(boundary: EgressProofOnlyGateBoundary) -> dict[str, object]:
    kwargs = {field.name: getattr(boundary, field.name) for field in fields(boundary)}
    kwargs["route_capability"] = boundary.route_capability
    kwargs["session_secret_gate"] = boundary.session_secret_gate
    return kwargs


def test_exact_task_id_and_exports() -> None:
    assert ER13A_TASK_ID == EXPECTED_TASK_ID
    assert proof_only_gate_module.ER13A_TASK_ID == EXPECTED_TASK_ID
    assert proof_only_gate_module.__all__ == EXPECTED_MODULE_EXPORTS
    assert tuple(proof_only_gate_module.__all__) == EXPECTED_MODULE_EXPORTS
    assert len(set(proof_only_gate_module.__all__)) == len(EXPECTED_MODULE_EXPORTS)
    assert all(hasattr(proof_only_gate_module, name) for name in EXPECTED_MODULE_EXPORTS)
    assert tuple((member.name, member.value) for member in EgressProofOnlyAuthority) == (
        ("EGRESS_ROUTING_SERVER", "EGRESS_ROUTING_SERVER"),
    )
    assert (
        session_secret_gate_module.ER09A_TASK_ID
        == "ER-09A-SESSION-SECRET-FAIL-CLOSED-BOUNDARY-20260716-044"
    )
    assert session_secret_gate_module.__all__ == (
        "ER09A_TASK_ID",
        "EgressSessionSecretAuthority",
        "EgressSessionSecretGateBoundary",
    )
    start = egress_routing.__all__.index("ER12A_TASK_ID")
    assert egress_routing.__all__[start : start + len(EXPECTED_PACKAGE_EXPORT_SLICE)] == (
        EXPECTED_PACKAGE_EXPORT_SLICE
    )


def test_exact_field_count_and_order() -> None:
    _, _, boundary = _build_valid_triplet()
    assert is_dataclass(boundary)
    assert len(fields(boundary)) == 47
    assert tuple(field.name for field in fields(boundary)) == EXPECTED_FIELD_NAMES
    assert type(boundary).__slots__ == EXPECTED_FIELD_NAMES
    assert not hasattr(boundary, "__dict__")


def test_boundary_is_frozen_and_slots() -> None:
    _, _, boundary = _build_valid_triplet()
    with pytest.raises(FrozenInstanceError):
        boundary.boundary_id = "changed"  # type: ignore[misc]


def test_exact_source_records_and_identities_are_preserved() -> None:
    capability, session_gate, boundary = _build_valid_triplet()

    assert tuple(field.name for field in fields(capability)) == EXPECTED_CAPABILITY_FIELD_NAMES
    assert capability.evidence_status is RouteEvidenceStatus.CURRENT
    assert capability.session_policy_status is SessionPolicyStatus.PROHIBITED
    assert tuple(field.name for field in fields(session_gate)) == EXPECTED_SESSION_FIELD_NAMES
    assert session_gate.boundary_id == EXPECTED_SESSION_BOUNDARY_ID
    assert session_gate.authority is EgressSessionSecretAuthority.EGRESS_ROUTING_SERVER
    assert session_gate.route_capability is capability
    assert session_gate.route_id == EXPECTED_ROUTE_ID
    assert session_gate.session_policy_status is SessionPolicyStatus.PROHIBITED
    for field_name in EXPECTED_SESSION_FALSE_FIELDS:
        value = getattr(session_gate, field_name)
        assert type(value) is bool
        assert value is False
    for field_name in EXPECTED_SESSION_TRUE_FIELDS:
        value = getattr(session_gate, field_name)
        assert type(value) is bool
        assert value is True

    assert boundary.route_capability is capability
    assert boundary.session_secret_gate is session_gate
    assert boundary.session_secret_gate.route_capability is capability
    assert boundary.route_id == capability.route_id == session_gate.route_id
    assert boundary.evidence_reference_ids == capability.evidence_reference_ids
    assert session_gate.evidence_reference_ids == capability.evidence_reference_ids
    assert session_gate.session_policy_status is capability.session_policy_status
    assert boundary.session_secret_gate.session_policy_status is capability.session_policy_status
    assert boundary.authority is EgressProofOnlyAuthority.EGRESS_ROUTING_SERVER
    assert session_gate.authority is EgressSessionSecretAuthority.EGRESS_ROUTING_SERVER


def test_source_capability_exact_record_is_required() -> None:
    capability = _build_capability()

    class CapabilitySubclass(RouteCapability):
        pass

    subclass_capability = CapabilitySubclass(
        capability_id=EXPECTED_CAPABILITY_ID,
        route_id=EXPECTED_ROUTE_ID,
        destination_scope=("proof-only-destination",),
        operation_classes=("proof-only-execution",),
        unsupported_classes=("browser-agent-runtime",),
        evidence_reference_ids=EXPECTED_EVIDENCE_REFERENCE_IDS,
        evidence_status=RouteEvidenceStatus.CURRENT,
        session_policy_status=SessionPolicyStatus.PROHIBITED,
    )
    duck_capability = SimpleNamespace(
        capability_id=EXPECTED_CAPABILITY_ID,
        route_id=EXPECTED_ROUTE_ID,
        destination_scope=("proof-only-destination",),
        operation_classes=("proof-only-execution",),
        unsupported_classes=("browser-agent-runtime",),
        evidence_reference_ids=EXPECTED_EVIDENCE_REFERENCE_IDS,
        evidence_status=RouteEvidenceStatus.CURRENT,
        session_policy_status=SessionPolicyStatus.PROHIBITED,
    )
    session_gate = _build_session_gate(capability)

    with pytest.raises(ValueError, match="route_capability must be RouteCapability"):
        _build_boundary(cast(RouteCapability, subclass_capability), session_gate)
    with pytest.raises(ValueError, match="route_capability must be RouteCapability"):
        _build_boundary(cast(RouteCapability, duck_capability), session_gate)

    assert capability == _build_capability()


def test_session_secret_gate_exact_record_is_required() -> None:
    capability = _build_capability()
    session_gate = _build_session_gate(capability)

    class GateSubclass(EgressSessionSecretGateBoundary):
        pass

    subclass_gate = GateSubclass(
        boundary_id=EXPECTED_SESSION_BOUNDARY_ID,
        authority=EgressSessionSecretAuthority.EGRESS_ROUTING_SERVER,
        route_capability=capability,
        route_id=EXPECTED_ROUTE_ID,
        session_policy_status=SessionPolicyStatus.PROHIBITED,
        isolated_project_session_gate_satisfied=False,
        project_owned_session_authorized=False,
        project_owned_cookie_profile_authorized=False,
        personal_browser_profile_access_authorized=False,
        browser_password_access_authorized=False,
        owner_private_session_default_authorized=False,
        foreign_or_unrelated_cookie_reuse_authorized=False,
        raw_cookie_material_authorized=False,
        raw_session_token_material_authorized=False,
        raw_credential_material_authorized=False,
        safe_reference_only=True,
        rotation_required=True,
        revocation_required=True,
        redacted_diagnostics_required=True,
        secret_logging_authorized=False,
        secret_report_authorized=False,
        secret_git_storage_authorized=False,
        runtime_session_creation_authorized=False,
        provider_access_permission_inferred=False,
        parser_success_inferred=False,
        scan_success_inferred=False,
        notification_delivery_inferred=False,
        reason_codes=("safe-reference-only",),
        evidence_reference_ids=EXPECTED_EVIDENCE_REFERENCE_IDS,
    )
    duck_gate = SimpleNamespace(
        **{field.name: getattr(session_gate, field.name) for field in fields(session_gate)}
    )

    with pytest.raises(
        ValueError, match="session_secret_gate must be EgressSessionSecretGateBoundary"
    ):
        _build_boundary(capability, subclass_gate)
    with pytest.raises(
        ValueError, match="session_secret_gate must be EgressSessionSecretGateBoundary"
    ):
        _build_boundary(capability, cast(EgressSessionSecretGateBoundary, duck_gate))

    assert session_gate == _build_session_gate(capability)


@pytest.mark.parametrize(
    ("session_policy_status", "expected_result"),
    [
        (SessionPolicyStatus.PROHIBITED, True),
        (SessionPolicyStatus.BLOCKED_PENDING_ISOLATED_PROJECT_SESSION_GATE, True),
    ],
)
def test_allowed_session_policy_statuses_are_accepted(
    session_policy_status: SessionPolicyStatus,
    expected_result: bool,
) -> None:
    capability = _build_capability(session_policy_status=session_policy_status)
    session_gate = _build_session_gate(capability, session_policy_status=session_policy_status)
    boundary = _build_boundary(capability, session_gate)

    assert expected_result is True
    assert boundary.session_secret_gate.session_policy_status is session_policy_status
    assert boundary.route_capability.session_policy_status is session_policy_status


def test_approved_reference_only_is_rejected() -> None:
    capability = _build_capability(
        session_policy_status=SessionPolicyStatus.APPROVED_REFERENCE_ONLY
    )

    with pytest.raises(ValueError, match="isolated project session gate not open"):
        _build_session_gate(
            capability,
            session_policy_status=SessionPolicyStatus.APPROVED_REFERENCE_ONLY,
        )


@pytest.mark.parametrize(
    ("route_family", "expected_true_field"),
    EXPECTED_ALLOWED_FAMILY_MATRIX,
)
def test_allowed_route_family_matrix_is_exact(
    route_family: RouteFamily, expected_true_field: str
) -> None:
    capability, session_gate, boundary = _build_valid_triplet(route_family)

    assert boundary.route_family is route_family
    for field_name in (
        "primary_linux_reference_style_direction_acknowledged",
        "russian_residential_future_route_direction_acknowledged",
        "owner_development_bridge_direction_acknowledged",
        "browser_extension_owner_avito_evidence_acknowledged",
        "windows_vm_browser_worker_fallback_direction_acknowledged",
    ):
        value = getattr(boundary, field_name)
        assert type(value) is bool
        assert value is (field_name == expected_true_field)

    assert boundary.route_capability is capability
    assert boundary.session_secret_gate is session_gate


def test_windows_browser_agent_route_is_rejected() -> None:
    capability = _build_capability()
    session_gate = _build_session_gate(capability)

    with pytest.raises(ValueError, match="route_family is not allowed in current ER-13A scope"):
        _build_boundary(
            capability,
            session_gate,
            route_family=RouteFamily.WINDOWS_BROWSER_AGENT_ROUTE,
        )


@pytest.mark.parametrize("field_name", EXPECTED_BOOLEANS_FOR_LOOKALIKE_GUARD)
def test_bool_lookalikes_are_rejected(field_name: str) -> None:
    _, _, boundary = _build_valid_triplet()
    expected_value = getattr(boundary, field_name)
    lookalike = BoolLike(1 if expected_value is True else 0)
    kwargs = _boundary_kwargs(boundary)
    kwargs[field_name] = lookalike

    with pytest.raises(ValueError, match=f"{field_name} must be a bool"):
        cast(Any, EgressProofOnlyGateBoundary)(**kwargs)


def test_mandatory_requirements_are_true() -> None:
    _, _, boundary = _build_valid_triplet()

    for field_name in EXPECTED_TRUE_BOOLEAN_FIELDS:
        value = getattr(boundary, field_name)
        assert type(value) is bool
        assert value is True


def test_fail_closed_fields_are_false() -> None:
    _, _, boundary = _build_valid_triplet()

    for field_name in EXPECTED_FALSE_BOOLEAN_FIELDS:
        value = getattr(boundary, field_name)
        assert type(value) is bool
        assert value is False


def test_linkage_and_reason_codes_are_exact() -> None:
    capability, session_gate, boundary = _build_valid_triplet()

    assert boundary.route_id == capability.route_id
    assert boundary.route_id == session_gate.route_id
    assert session_gate.route_capability is capability
    assert session_gate.session_policy_status is capability.session_policy_status
    assert session_gate.evidence_reference_ids == capability.evidence_reference_ids
    assert boundary.evidence_reference_ids == capability.evidence_reference_ids
    assert boundary.reason_codes == EXPECTED_REASON_CODES
    assert "proof-only-execution-blocked" in boundary.reason_codes
    assert "explicit-owner-proof-task-required" in boundary.reason_codes
    assert "legal-access-and-scope-gates-unsatisfied" in boundary.reason_codes


def test_text_and_tuple_subclasses_are_rejected() -> None:
    capability = _build_capability()
    session_gate = _build_session_gate(capability)

    with pytest.raises(ValueError, match="boundary_id must be a non-blank string"):
        _build_boundary(
            capability,
            session_gate,
            boundary_id=TextLike(EXPECTED_BOUNDARY_ID),
        )

    with pytest.raises(
        ValueError, match="route_capability\\.capability_id must be a non-blank string"
    ):
        _build_boundary(
            _build_capability(capability_id=TextLike(EXPECTED_CAPABILITY_ID)),
            session_gate,
        )

    with pytest.raises(ValueError, match="route_capability\\.destination_scope must be a tuple"):
        _build_boundary(
            _build_capability(destination_scope=TupleLike(("proof-only-destination",))),
            session_gate,
        )

    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        _build_boundary(
            capability,
            session_gate,
            reason_codes=TupleLike(EXPECTED_REASON_CODES),
        )

    with pytest.raises(ValueError, match="boundary_id must be a non-blank string"):
        _build_boundary(
            capability,
            _build_session_gate(capability, boundary_id=TextLike(EXPECTED_SESSION_BOUNDARY_ID)),
        )

    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        _build_boundary(
            capability,
            _build_session_gate(capability, reason_codes=TupleLike(("safe-reference-only",))),
        )


def test_duplicate_and_blank_tuple_values_are_rejected() -> None:
    capability = _build_capability(
        destination_scope=("proof-only-destination",),
        operation_classes=("proof-only-execution",),
    )
    session_gate = _build_session_gate(capability)

    with pytest.raises(
        ValueError, match="route_capability\\.destination_scope must not contain duplicates"
    ):
        _build_boundary(
            _build_capability(
                destination_scope=("proof-only-destination", "proof-only-destination")
            ),
            session_gate,
        )

    with pytest.raises(ValueError, match="reason_codes must not contain duplicates"):
        _build_boundary(
            capability,
            session_gate,
            reason_codes=(
                "proof-only-execution-blocked",
                "proof-only-execution-blocked",
            ),
        )

    with pytest.raises(ValueError, match="route_capability\\.operation_classes must not be empty"):
        _build_boundary(
            _build_capability(operation_classes=()),
            session_gate,
        )

    with pytest.raises(ValueError, match="reason_codes must not be empty"):
        _build_boundary(
            capability,
            session_gate,
            reason_codes=(),
        )


def test_source_records_are_not_mutated_and_equality_is_deterministic() -> None:
    capability, session_gate, boundary = _build_valid_triplet()
    capability_before = _snapshot(capability)
    session_gate_before = _snapshot(session_gate)
    boundary_before = _snapshot(boundary)

    duplicate_boundary = _build_boundary(capability, session_gate)
    alternate_capability = _build_capability(capability_id="cap-proof-only-02")
    alternate_session_gate = _build_session_gate(alternate_capability)
    alternate_boundary = _build_boundary(
        alternate_capability,
        alternate_session_gate,
    )

    assert _snapshot(capability) == capability_before
    assert _snapshot(session_gate) == session_gate_before
    assert _snapshot(boundary) == boundary_before
    assert boundary == duplicate_boundary
    assert hash(boundary) == hash(duplicate_boundary)
    assert boundary is not duplicate_boundary
    assert boundary != alternate_boundary
    assert "route_capability=" in repr(boundary)


def test_schema_excludes_raw_runtime_and_secret_fields() -> None:
    _, _, boundary = _build_valid_triplet()
    field_names = tuple(field.name for field in fields(boundary))

    assert field_names == EXPECTED_FIELD_NAMES
    assert {
        "url",
        "host",
        "hostname",
        "ip",
        "port",
        "payload",
        "body",
        "cookie",
        "cookies",
        "session",
        "token",
        "credential",
        "browser_profile",
        "browser_profile_path",
        "executable_path",
        "runtime_config",
        "proxy",
        "vpn",
        "tunnel",
    }.isdisjoint(field_names)


@pytest.mark.parametrize(
    ("mutation", "expected_message"),
    [
        (
            lambda capability, session_gate: (
                capability,
                session_gate,
                {"proof_execution_authorized": True},
            ),
            "proof_execution_authorized must be False",
        ),
        (
            lambda capability, session_gate: (
                capability,
                session_gate,
                {"live_provider_traffic_authorized": True},
            ),
            "live_provider_traffic_authorized must be False",
        ),
        (
            lambda capability, session_gate: (
                capability,
                session_gate,
                {"captcha_solving_authorized": True},
            ),
            "captcha_solving_authorized must be False",
        ),
        (
            lambda capability, session_gate: (
                capability,
                session_gate,
                {"separate_explicit_owner_proof_task_required": False},
            ),
            "separate_explicit_owner_proof_task_required must be True",
        ),
        (
            lambda capability, session_gate: (
                capability,
                session_gate,
                {"route_family": RouteFamily.WINDOWS_BROWSER_AGENT_ROUTE},
            ),
            "route_family is not allowed in current ER-13A scope",
        ),
    ],
)
def test_mutation_sensitivity_gate_fails(mutation: Any, expected_message: str) -> None:
    capability, session_gate, _ = _build_valid_triplet()
    _, _, overrides = mutation(capability, session_gate)
    kwargs = {
        **_boundary_kwargs(_build_boundary(capability, session_gate)),
        **overrides,
    }
    with pytest.raises(ValueError, match=expected_message):
        cast(Any, EgressProofOnlyGateBoundary)(**kwargs)

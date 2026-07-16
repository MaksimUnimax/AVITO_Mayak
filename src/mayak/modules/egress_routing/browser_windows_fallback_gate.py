from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeVar, cast

from .contracts import RouteCapability, RouteEvidenceStatus, RouteFamily, SessionPolicyStatus
from .session_secret_gate import (
    EgressSessionSecretAuthority,
    EgressSessionSecretGateBoundary,
)

ER10A_TASK_ID = "ER-10A-BROWSER-WINDOWS-FALLBACK-FAIL-CLOSED-GATE-20260716-046"

__all__ = (
    "ER10A_TASK_ID",
    "FutureBrowserFallbackAuthority",
    "FutureBrowserFallbackGateBoundary",
)


def _require_text(value: object, field_name: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-blank string")
    return value


def _require_bool(value: object, field_name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_tuple(value: object, field_name: str) -> tuple[object, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    return value


def _require_text_tuple(value: object, field_name: str) -> tuple[str, ...]:
    items = _require_tuple(value, field_name)
    for item in items:
        _require_text(item, field_name)
    return items  # type: ignore[return-value]


E = TypeVar("E", bound=Enum)
T = TypeVar("T")


def _require_exact_enum(value: object, enum_cls: type[E], field_name: str) -> E:
    if type(value) is not enum_cls:
        raise ValueError(f"{field_name} must be {enum_cls.__name__}")
    return cast(E, value)


def _require_exact_record(value: object, record_cls: type[T], field_name: str) -> T:
    if type(value) is not record_cls:
        raise ValueError(f"{field_name} must be {record_cls.__name__}")
    return cast(T, value)


_ALLOWED_SESSION_POLICY_STATUSES = frozenset(
    {
        SessionPolicyStatus.PROHIBITED,
        SessionPolicyStatus.BLOCKED_PENDING_ISOLATED_PROJECT_SESSION_GATE,
    }
)

_ALLOWED_ROUTE_FAMILY_BROWSER_EVIDENCE = {
    RouteFamily.BROWSER_EXTENSION_ROUTE: True,
    RouteFamily.WINDOWS_BROWSER_AGENT_ROUTE: False,
    RouteFamily.WINDOWS_VM_BROWSER_WORKER_ROUTE: False,
}


def _require_route_capability(value: object) -> RouteCapability:
    capability = _require_exact_record(value, RouteCapability, "route_capability")

    _require_text(capability.capability_id, "route_capability.capability_id")
    _require_text(capability.route_id, "route_capability.route_id")
    _require_text_tuple(capability.destination_scope, "route_capability.destination_scope")
    _require_text_tuple(capability.operation_classes, "route_capability.operation_classes")
    _require_text_tuple(capability.unsupported_classes, "route_capability.unsupported_classes")
    _require_text_tuple(
        capability.evidence_reference_ids,
        "route_capability.evidence_reference_ids",
    )
    _require_exact_enum(
        capability.evidence_status,
        RouteEvidenceStatus,
        "route_capability.evidence_status",
    )
    _require_exact_enum(
        capability.session_policy_status,
        SessionPolicyStatus,
        "route_capability.session_policy_status",
    )
    return capability


def _require_session_secret_gate(value: object) -> EgressSessionSecretGateBoundary:
    gate = _require_exact_record(value, EgressSessionSecretGateBoundary, "session_secret_gate")

    _require_text(gate.boundary_id, "session_secret_gate.boundary_id")
    _require_exact_enum(
        gate.authority,
        EgressSessionSecretAuthority,
        "session_secret_gate.authority",
    )
    capability = _require_route_capability(gate.route_capability)
    _require_text(gate.route_id, "session_secret_gate.route_id")
    _require_exact_enum(
        gate.session_policy_status,
        SessionPolicyStatus,
        "session_secret_gate.session_policy_status",
    )
    if gate.session_policy_status is not capability.session_policy_status:
        raise ValueError(
            "session_secret_gate.session_policy_status must match "
            "route_capability.session_policy_status"
        )
    _require_bool(
        gate.isolated_project_session_gate_satisfied,
        "session_secret_gate.isolated_project_session_gate_satisfied",
    )
    _require_bool(
        gate.project_owned_session_authorized,
        "session_secret_gate.project_owned_session_authorized",
    )
    _require_bool(
        gate.project_owned_cookie_profile_authorized,
        "session_secret_gate.project_owned_cookie_profile_authorized",
    )
    _require_bool(
        gate.personal_browser_profile_access_authorized,
        "session_secret_gate.personal_browser_profile_access_authorized",
    )
    _require_bool(
        gate.browser_password_access_authorized,
        "session_secret_gate.browser_password_access_authorized",
    )
    _require_bool(
        gate.owner_private_session_default_authorized,
        "session_secret_gate.owner_private_session_default_authorized",
    )
    _require_bool(
        gate.foreign_or_unrelated_cookie_reuse_authorized,
        "session_secret_gate.foreign_or_unrelated_cookie_reuse_authorized",
    )
    _require_bool(
        gate.raw_cookie_material_authorized,
        "session_secret_gate.raw_cookie_material_authorized",
    )
    _require_bool(
        gate.raw_session_token_material_authorized,
        "session_secret_gate.raw_session_token_material_authorized",
    )
    _require_bool(
        gate.raw_credential_material_authorized,
        "session_secret_gate.raw_credential_material_authorized",
    )
    _require_bool(gate.safe_reference_only, "session_secret_gate.safe_reference_only")
    _require_bool(gate.rotation_required, "session_secret_gate.rotation_required")
    _require_bool(gate.revocation_required, "session_secret_gate.revocation_required")
    _require_bool(
        gate.redacted_diagnostics_required,
        "session_secret_gate.redacted_diagnostics_required",
    )
    _require_bool(gate.secret_logging_authorized, "session_secret_gate.secret_logging_authorized")
    _require_bool(gate.secret_report_authorized, "session_secret_gate.secret_report_authorized")
    _require_bool(
        gate.secret_git_storage_authorized,
        "session_secret_gate.secret_git_storage_authorized",
    )
    _require_bool(
        gate.runtime_session_creation_authorized,
        "session_secret_gate.runtime_session_creation_authorized",
    )
    _require_bool(
        gate.provider_access_permission_inferred,
        "session_secret_gate.provider_access_permission_inferred",
    )
    _require_bool(gate.parser_success_inferred, "session_secret_gate.parser_success_inferred")
    _require_bool(gate.scan_success_inferred, "session_secret_gate.scan_success_inferred")
    _require_bool(
        gate.notification_delivery_inferred,
        "session_secret_gate.notification_delivery_inferred",
    )
    _require_text_tuple(gate.reason_codes, "session_secret_gate.reason_codes")
    _require_text_tuple(
        gate.evidence_reference_ids,
        "session_secret_gate.evidence_reference_ids",
    )

    false_bool_fields = (
        (
            "isolated_project_session_gate_satisfied",
            gate.isolated_project_session_gate_satisfied,
        ),
        ("project_owned_session_authorized", gate.project_owned_session_authorized),
        (
            "project_owned_cookie_profile_authorized",
            gate.project_owned_cookie_profile_authorized,
        ),
        (
            "personal_browser_profile_access_authorized",
            gate.personal_browser_profile_access_authorized,
        ),
        ("browser_password_access_authorized", gate.browser_password_access_authorized),
        ("owner_private_session_default_authorized", gate.owner_private_session_default_authorized),
        (
            "foreign_or_unrelated_cookie_reuse_authorized",
            gate.foreign_or_unrelated_cookie_reuse_authorized,
        ),
        ("raw_cookie_material_authorized", gate.raw_cookie_material_authorized),
        ("raw_session_token_material_authorized", gate.raw_session_token_material_authorized),
        ("raw_credential_material_authorized", gate.raw_credential_material_authorized),
        ("secret_logging_authorized", gate.secret_logging_authorized),
        ("secret_report_authorized", gate.secret_report_authorized),
        ("secret_git_storage_authorized", gate.secret_git_storage_authorized),
        ("runtime_session_creation_authorized", gate.runtime_session_creation_authorized),
        ("provider_access_permission_inferred", gate.provider_access_permission_inferred),
        ("parser_success_inferred", gate.parser_success_inferred),
        ("scan_success_inferred", gate.scan_success_inferred),
        ("notification_delivery_inferred", gate.notification_delivery_inferred),
    )
    true_bool_fields = (
        ("safe_reference_only", gate.safe_reference_only),
        ("rotation_required", gate.rotation_required),
        ("revocation_required", gate.revocation_required),
        ("redacted_diagnostics_required", gate.redacted_diagnostics_required),
    )

    for field_name, field_value in false_bool_fields + true_bool_fields:
        _require_bool(field_value, f"session_secret_gate.{field_name}")

    for field_name, field_value in false_bool_fields:
        if field_value is not False:
            raise ValueError(f"session_secret_gate.{field_name} must be False")

    for field_name, field_value in true_bool_fields:
        if field_value is not True:
            raise ValueError(f"session_secret_gate.{field_name} must be True")

    return gate


class FutureBrowserFallbackAuthority(str, Enum):
    EGRESS_ROUTING_SERVER = "EGRESS_ROUTING_SERVER"


@dataclass(frozen=True, slots=True)
class FutureBrowserFallbackGateBoundary:
    boundary_id: str
    authority: FutureBrowserFallbackAuthority
    route_capability: RouteCapability
    session_secret_gate: EgressSessionSecretGateBoundary
    route_family: RouteFamily
    route_id: str
    owner_fallback_direction_acknowledged: bool
    owner_browser_extension_avito_evidence_acknowledged: bool
    owner_evidence_production_scale_proof: bool
    route_proof_gate_satisfied: bool
    windows_operations_security_gate_satisfied: bool
    extension_scope_reduction_required: bool
    avito_only_automation_scope_required: bool
    bounded_assignment_required: bool
    safe_result_return_required: bool
    browser_worker_pool_preferred: bool
    browser_per_beacon_primary_authorized: bool
    full_saas_on_windows_authorized: bool
    self_editing_extension_authorized: bool
    developer_control_editing_authorized: bool
    unrelated_automation_targets_authorized: bool
    broad_site_permissions_authorized: bool
    native_host_implementation_authorized: bool
    installer_implementation_authorized: bool
    browser_runtime_authorized: bool
    windows_agent_runtime_authorized: bool
    production_route_authorized: bool
    automatic_route_selection_authorized: bool
    primary_database_access_authorized: bool
    business_state_ownership_authorized: bool
    live_avito_traffic_authorized: bool
    provider_access_permission_inferred: bool
    parser_success_inferred: bool
    scan_success_inferred: bool
    notification_delivery_inferred: bool
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        boundary_id = _require_text(self.boundary_id, "boundary_id")
        authority = _require_exact_enum(
            self.authority,
            FutureBrowserFallbackAuthority,
            "authority",
        )
        route_capability = _require_route_capability(self.route_capability)
        session_secret_gate = _require_session_secret_gate(self.session_secret_gate)
        route_family = _require_exact_enum(self.route_family, RouteFamily, "route_family")
        route_id = _require_text(self.route_id, "route_id")
        owner_fallback_direction_acknowledged = _require_bool(
            self.owner_fallback_direction_acknowledged,
            "owner_fallback_direction_acknowledged",
        )
        owner_browser_extension_avito_evidence_acknowledged = _require_bool(
            self.owner_browser_extension_avito_evidence_acknowledged,
            "owner_browser_extension_avito_evidence_acknowledged",
        )
        owner_evidence_production_scale_proof = _require_bool(
            self.owner_evidence_production_scale_proof,
            "owner_evidence_production_scale_proof",
        )
        route_proof_gate_satisfied = _require_bool(
            self.route_proof_gate_satisfied,
            "route_proof_gate_satisfied",
        )
        windows_operations_security_gate_satisfied = _require_bool(
            self.windows_operations_security_gate_satisfied,
            "windows_operations_security_gate_satisfied",
        )
        extension_scope_reduction_required = _require_bool(
            self.extension_scope_reduction_required,
            "extension_scope_reduction_required",
        )
        avito_only_automation_scope_required = _require_bool(
            self.avito_only_automation_scope_required,
            "avito_only_automation_scope_required",
        )
        bounded_assignment_required = _require_bool(
            self.bounded_assignment_required,
            "bounded_assignment_required",
        )
        safe_result_return_required = _require_bool(
            self.safe_result_return_required,
            "safe_result_return_required",
        )
        browser_worker_pool_preferred = _require_bool(
            self.browser_worker_pool_preferred,
            "browser_worker_pool_preferred",
        )
        browser_per_beacon_primary_authorized = _require_bool(
            self.browser_per_beacon_primary_authorized,
            "browser_per_beacon_primary_authorized",
        )
        full_saas_on_windows_authorized = _require_bool(
            self.full_saas_on_windows_authorized,
            "full_saas_on_windows_authorized",
        )
        self_editing_extension_authorized = _require_bool(
            self.self_editing_extension_authorized,
            "self_editing_extension_authorized",
        )
        developer_control_editing_authorized = _require_bool(
            self.developer_control_editing_authorized,
            "developer_control_editing_authorized",
        )
        unrelated_automation_targets_authorized = _require_bool(
            self.unrelated_automation_targets_authorized,
            "unrelated_automation_targets_authorized",
        )
        broad_site_permissions_authorized = _require_bool(
            self.broad_site_permissions_authorized,
            "broad_site_permissions_authorized",
        )
        native_host_implementation_authorized = _require_bool(
            self.native_host_implementation_authorized,
            "native_host_implementation_authorized",
        )
        installer_implementation_authorized = _require_bool(
            self.installer_implementation_authorized,
            "installer_implementation_authorized",
        )
        browser_runtime_authorized = _require_bool(
            self.browser_runtime_authorized,
            "browser_runtime_authorized",
        )
        windows_agent_runtime_authorized = _require_bool(
            self.windows_agent_runtime_authorized,
            "windows_agent_runtime_authorized",
        )
        production_route_authorized = _require_bool(
            self.production_route_authorized,
            "production_route_authorized",
        )
        automatic_route_selection_authorized = _require_bool(
            self.automatic_route_selection_authorized,
            "automatic_route_selection_authorized",
        )
        primary_database_access_authorized = _require_bool(
            self.primary_database_access_authorized,
            "primary_database_access_authorized",
        )
        business_state_ownership_authorized = _require_bool(
            self.business_state_ownership_authorized,
            "business_state_ownership_authorized",
        )
        live_avito_traffic_authorized = _require_bool(
            self.live_avito_traffic_authorized,
            "live_avito_traffic_authorized",
        )
        provider_access_permission_inferred = _require_bool(
            self.provider_access_permission_inferred,
            "provider_access_permission_inferred",
        )
        parser_success_inferred = _require_bool(
            self.parser_success_inferred,
            "parser_success_inferred",
        )
        scan_success_inferred = _require_bool(self.scan_success_inferred, "scan_success_inferred")
        notification_delivery_inferred = _require_bool(
            self.notification_delivery_inferred,
            "notification_delivery_inferred",
        )
        reason_codes = _require_text_tuple(self.reason_codes, "reason_codes")
        evidence_reference_ids = _require_text_tuple(
            self.evidence_reference_ids,
            "evidence_reference_ids",
        )
        if not reason_codes:
            raise ValueError("reason_codes must not be empty")
        if not evidence_reference_ids:
            raise ValueError("evidence_reference_ids must not be empty")

        object.__setattr__(self, "boundary_id", boundary_id)
        object.__setattr__(self, "authority", authority)
        object.__setattr__(self, "route_capability", route_capability)
        object.__setattr__(self, "session_secret_gate", session_secret_gate)
        object.__setattr__(self, "route_family", route_family)
        object.__setattr__(self, "route_id", route_id)
        object.__setattr__(
            self,
            "owner_fallback_direction_acknowledged",
            owner_fallback_direction_acknowledged,
        )
        object.__setattr__(
            self,
            "owner_browser_extension_avito_evidence_acknowledged",
            owner_browser_extension_avito_evidence_acknowledged,
        )
        object.__setattr__(
            self,
            "owner_evidence_production_scale_proof",
            owner_evidence_production_scale_proof,
        )
        object.__setattr__(self, "route_proof_gate_satisfied", route_proof_gate_satisfied)
        object.__setattr__(
            self,
            "windows_operations_security_gate_satisfied",
            windows_operations_security_gate_satisfied,
        )
        object.__setattr__(
            self,
            "extension_scope_reduction_required",
            extension_scope_reduction_required,
        )
        object.__setattr__(
            self,
            "avito_only_automation_scope_required",
            avito_only_automation_scope_required,
        )
        object.__setattr__(self, "bounded_assignment_required", bounded_assignment_required)
        object.__setattr__(self, "safe_result_return_required", safe_result_return_required)
        object.__setattr__(self, "browser_worker_pool_preferred", browser_worker_pool_preferred)
        object.__setattr__(
            self,
            "browser_per_beacon_primary_authorized",
            browser_per_beacon_primary_authorized,
        )
        object.__setattr__(
            self,
            "full_saas_on_windows_authorized",
            full_saas_on_windows_authorized,
        )
        object.__setattr__(
            self,
            "self_editing_extension_authorized",
            self_editing_extension_authorized,
        )
        object.__setattr__(
            self,
            "developer_control_editing_authorized",
            developer_control_editing_authorized,
        )
        object.__setattr__(
            self,
            "unrelated_automation_targets_authorized",
            unrelated_automation_targets_authorized,
        )
        object.__setattr__(
            self,
            "broad_site_permissions_authorized",
            broad_site_permissions_authorized,
        )
        object.__setattr__(
            self,
            "native_host_implementation_authorized",
            native_host_implementation_authorized,
        )
        object.__setattr__(
            self,
            "installer_implementation_authorized",
            installer_implementation_authorized,
        )
        object.__setattr__(self, "browser_runtime_authorized", browser_runtime_authorized)
        object.__setattr__(
            self,
            "windows_agent_runtime_authorized",
            windows_agent_runtime_authorized,
        )
        object.__setattr__(self, "production_route_authorized", production_route_authorized)
        object.__setattr__(
            self,
            "automatic_route_selection_authorized",
            automatic_route_selection_authorized,
        )
        object.__setattr__(
            self,
            "primary_database_access_authorized",
            primary_database_access_authorized,
        )
        object.__setattr__(
            self,
            "business_state_ownership_authorized",
            business_state_ownership_authorized,
        )
        object.__setattr__(self, "live_avito_traffic_authorized", live_avito_traffic_authorized)
        object.__setattr__(
            self,
            "provider_access_permission_inferred",
            provider_access_permission_inferred,
        )
        object.__setattr__(self, "parser_success_inferred", parser_success_inferred)
        object.__setattr__(self, "scan_success_inferred", scan_success_inferred)
        object.__setattr__(
            self,
            "notification_delivery_inferred",
            notification_delivery_inferred,
        )
        object.__setattr__(self, "reason_codes", reason_codes)
        object.__setattr__(
            self,
            "evidence_reference_ids",
            route_capability.evidence_reference_ids,
        )

        if authority is not FutureBrowserFallbackAuthority.EGRESS_ROUTING_SERVER:
            raise ValueError("authority must be EGRESS_ROUTING_SERVER")
        if route_family not in _ALLOWED_ROUTE_FAMILY_BROWSER_EVIDENCE:
            raise ValueError("route_family must be a supported browser or Windows fallback route")
        if owner_fallback_direction_acknowledged is not True:
            raise ValueError("owner_fallback_direction_acknowledged must be True")
        if owner_evidence_production_scale_proof is not False:
            raise ValueError("owner_evidence_production_scale_proof must be False")
        if route_proof_gate_satisfied is not False:
            raise ValueError("route_proof_gate_satisfied must be False")
        if windows_operations_security_gate_satisfied is not False:
            raise ValueError("windows_operations_security_gate_satisfied must be False")
        if extension_scope_reduction_required is not True:
            raise ValueError("extension_scope_reduction_required must be True")
        if avito_only_automation_scope_required is not True:
            raise ValueError("avito_only_automation_scope_required must be True")
        if bounded_assignment_required is not True:
            raise ValueError("bounded_assignment_required must be True")
        if safe_result_return_required is not True:
            raise ValueError("safe_result_return_required must be True")
        if browser_worker_pool_preferred is not True:
            raise ValueError("browser_worker_pool_preferred must be True")
        if browser_per_beacon_primary_authorized is not False:
            raise ValueError("browser_per_beacon_primary_authorized must be False")
        if full_saas_on_windows_authorized is not False:
            raise ValueError("full_saas_on_windows_authorized must be False")
        if self_editing_extension_authorized is not False:
            raise ValueError("self_editing_extension_authorized must be False")
        if developer_control_editing_authorized is not False:
            raise ValueError("developer_control_editing_authorized must be False")
        if unrelated_automation_targets_authorized is not False:
            raise ValueError("unrelated_automation_targets_authorized must be False")
        if broad_site_permissions_authorized is not False:
            raise ValueError("broad_site_permissions_authorized must be False")
        if native_host_implementation_authorized is not False:
            raise ValueError("native_host_implementation_authorized must be False")
        if installer_implementation_authorized is not False:
            raise ValueError("installer_implementation_authorized must be False")
        if browser_runtime_authorized is not False:
            raise ValueError("browser_runtime_authorized must be False")
        if windows_agent_runtime_authorized is not False:
            raise ValueError("windows_agent_runtime_authorized must be False")
        if production_route_authorized is not False:
            raise ValueError("production_route_authorized must be False")
        if automatic_route_selection_authorized is not False:
            raise ValueError("automatic_route_selection_authorized must be False")
        if primary_database_access_authorized is not False:
            raise ValueError("primary_database_access_authorized must be False")
        if business_state_ownership_authorized is not False:
            raise ValueError("business_state_ownership_authorized must be False")
        if live_avito_traffic_authorized is not False:
            raise ValueError("live_avito_traffic_authorized must be False")
        if provider_access_permission_inferred is not False:
            raise ValueError("provider_access_permission_inferred must be False")
        if parser_success_inferred is not False:
            raise ValueError("parser_success_inferred must be False")
        if scan_success_inferred is not False:
            raise ValueError("scan_success_inferred must be False")
        if notification_delivery_inferred is not False:
            raise ValueError("notification_delivery_inferred must be False")
        if route_id != route_capability.route_id:
            raise ValueError("route_id must match route_capability.route_id")
        if route_id != session_secret_gate.route_id:
            raise ValueError("route_id must match session_secret_gate.route_id")
        if route_capability.session_policy_status not in _ALLOWED_SESSION_POLICY_STATUSES:
            raise ValueError("route_capability.session_policy_status must remain fail-closed")
        if session_secret_gate.session_policy_status not in _ALLOWED_SESSION_POLICY_STATUSES:
            raise ValueError("session_secret_gate.session_policy_status must remain fail-closed")
        if session_secret_gate.route_capability is not route_capability:
            raise ValueError("session_secret_gate.route_capability must be route_capability")
        if session_secret_gate.route_id != route_capability.route_id:
            raise ValueError("session_secret_gate.route_id must match route_capability.route_id")
        if session_secret_gate.evidence_reference_ids != route_capability.evidence_reference_ids:
            raise ValueError(
                "session_secret_gate.evidence_reference_ids must match "
                "route_capability.evidence_reference_ids"
            )
        if evidence_reference_ids != route_capability.evidence_reference_ids:
            raise ValueError(
                "evidence_reference_ids must match "
                "route_capability.evidence_reference_ids"
            )
        expected_browser_evidence = _ALLOWED_ROUTE_FAMILY_BROWSER_EVIDENCE[route_family]
        if owner_browser_extension_avito_evidence_acknowledged is not expected_browser_evidence:
            raise ValueError(
                "owner_browser_extension_avito_evidence_acknowledged must match route_family"
            )

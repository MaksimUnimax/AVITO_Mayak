from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeVar, cast

from .contracts import RouteCapability, RouteEvidenceStatus, RouteFamily, SessionPolicyStatus
from .session_secret_gate import (
    EgressSessionSecretAuthority,
    EgressSessionSecretGateBoundary,
)

ER11A_TASK_ID = "ER-11A-DEVELOPMENT-BRIDGE-FAIL-CLOSED-GATE-20260716-048"

__all__ = (
    "ER11A_TASK_ID",
    "DevelopmentBridgeAuthority",
    "DevelopmentBridgeGateBoundary",
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
    if gate.authority is not EgressSessionSecretAuthority.EGRESS_ROUTING_SERVER:
        raise ValueError("session_secret_gate.authority must be EGRESS_ROUTING_SERVER")
    capability = _require_route_capability(gate.route_capability)
    route_id = _require_text(gate.route_id, "session_secret_gate.route_id")
    session_policy_status = _require_exact_enum(
        gate.session_policy_status,
        SessionPolicyStatus,
        "session_secret_gate.session_policy_status",
    )
    if session_policy_status not in {
        SessionPolicyStatus.PROHIBITED,
        SessionPolicyStatus.BLOCKED_PENDING_ISOLATED_PROJECT_SESSION_GATE,
    }:
        raise ValueError(
            "session_secret_gate.session_policy_status must be PROHIBITED or "
            "BLOCKED_PENDING_ISOLATED_PROJECT_SESSION_GATE"
        )
    if session_policy_status is not capability.session_policy_status:
        raise ValueError(
            "session_secret_gate.session_policy_status must match "
            "route_capability.session_policy_status"
        )
    if route_id != capability.route_id:
        raise ValueError("session_secret_gate.route_id must match route_capability.route_id")
    if gate.route_capability is not capability:
        raise ValueError("session_secret_gate.route_capability must match route_capability")
    if gate.evidence_reference_ids != capability.evidence_reference_ids:
        raise ValueError(
            "session_secret_gate.evidence_reference_ids must match "
            "route_capability.evidence_reference_ids"
        )

    false_bool_fields = (
        ("isolated_project_session_gate_satisfied", gate.isolated_project_session_gate_satisfied),
        ("project_owned_session_authorized", gate.project_owned_session_authorized),
        ("project_owned_cookie_profile_authorized", gate.project_owned_cookie_profile_authorized),
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

    reason_codes = _require_text_tuple(gate.reason_codes, "session_secret_gate.reason_codes")
    evidence_reference_ids = _require_text_tuple(
        gate.evidence_reference_ids,
        "session_secret_gate.evidence_reference_ids",
    )
    if not reason_codes:
        raise ValueError("session_secret_gate.reason_codes must not be empty")
    if not evidence_reference_ids:
        raise ValueError("session_secret_gate.evidence_reference_ids must not be empty")
    return gate


class DevelopmentBridgeAuthority(str, Enum):
    EGRESS_ROUTING_SERVER = "EGRESS_ROUTING_SERVER"


@dataclass(frozen=True, slots=True)
class DevelopmentBridgeGateBoundary:
    boundary_id: str
    authority: DevelopmentBridgeAuthority
    route_capability: RouteCapability
    session_secret_gate: EgressSessionSecretGateBoundary
    route_family: RouteFamily
    route_id: str
    owner_development_bridge_direction_acknowledged: bool
    owner_consent_required_for_each_use_scope: bool
    development_only_required: bool
    explicit_owner_use_scope_approved: bool
    development_proof_scope_defined: bool
    manual_owner_assisted_transport_semantic_candidate: bool
    bounded_proof_assignment_required: bool
    clear_evidence_report_required: bool
    replaceable_by_production_route_required: bool
    no_secrets_policy_required: bool
    no_raw_payload_retention_required: bool
    production_dependency_authorized: bool
    unbounded_owner_machine_dependency_authorized: bool
    silent_use_authorized: bool
    owner_private_data_storage_authorized: bool
    scalability_proof_inferred: bool
    permanent_architecture_authorized: bool
    live_proof_execution_authorized: bool
    route_registration_authorized: bool
    route_selection_authorized: bool
    fallback_execution_authorized: bool
    lease_or_assignment_commit_authorized: bool
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
            DevelopmentBridgeAuthority,
            "authority",
        )
        route_capability = _require_route_capability(self.route_capability)
        session_secret_gate = _require_session_secret_gate(self.session_secret_gate)
        route_family = _require_exact_enum(self.route_family, RouteFamily, "route_family")
        route_id = _require_text(self.route_id, "route_id")
        owner_development_bridge_direction_acknowledged = _require_bool(
            self.owner_development_bridge_direction_acknowledged,
            "owner_development_bridge_direction_acknowledged",
        )
        owner_consent_required_for_each_use_scope = _require_bool(
            self.owner_consent_required_for_each_use_scope,
            "owner_consent_required_for_each_use_scope",
        )
        development_only_required = _require_bool(
            self.development_only_required,
            "development_only_required",
        )
        explicit_owner_use_scope_approved = _require_bool(
            self.explicit_owner_use_scope_approved,
            "explicit_owner_use_scope_approved",
        )
        development_proof_scope_defined = _require_bool(
            self.development_proof_scope_defined,
            "development_proof_scope_defined",
        )
        manual_owner_assisted_transport_semantic_candidate = _require_bool(
            self.manual_owner_assisted_transport_semantic_candidate,
            "manual_owner_assisted_transport_semantic_candidate",
        )
        bounded_proof_assignment_required = _require_bool(
            self.bounded_proof_assignment_required,
            "bounded_proof_assignment_required",
        )
        clear_evidence_report_required = _require_bool(
            self.clear_evidence_report_required,
            "clear_evidence_report_required",
        )
        replaceable_by_production_route_required = _require_bool(
            self.replaceable_by_production_route_required,
            "replaceable_by_production_route_required",
        )
        no_secrets_policy_required = _require_bool(
            self.no_secrets_policy_required,
            "no_secrets_policy_required",
        )
        no_raw_payload_retention_required = _require_bool(
            self.no_raw_payload_retention_required,
            "no_raw_payload_retention_required",
        )
        production_dependency_authorized = _require_bool(
            self.production_dependency_authorized,
            "production_dependency_authorized",
        )
        unbounded_owner_machine_dependency_authorized = _require_bool(
            self.unbounded_owner_machine_dependency_authorized,
            "unbounded_owner_machine_dependency_authorized",
        )
        silent_use_authorized = _require_bool(
            self.silent_use_authorized,
            "silent_use_authorized",
        )
        owner_private_data_storage_authorized = _require_bool(
            self.owner_private_data_storage_authorized,
            "owner_private_data_storage_authorized",
        )
        scalability_proof_inferred = _require_bool(
            self.scalability_proof_inferred,
            "scalability_proof_inferred",
        )
        permanent_architecture_authorized = _require_bool(
            self.permanent_architecture_authorized,
            "permanent_architecture_authorized",
        )
        live_proof_execution_authorized = _require_bool(
            self.live_proof_execution_authorized,
            "live_proof_execution_authorized",
        )
        route_registration_authorized = _require_bool(
            self.route_registration_authorized,
            "route_registration_authorized",
        )
        route_selection_authorized = _require_bool(
            self.route_selection_authorized,
            "route_selection_authorized",
        )
        fallback_execution_authorized = _require_bool(
            self.fallback_execution_authorized,
            "fallback_execution_authorized",
        )
        lease_or_assignment_commit_authorized = _require_bool(
            self.lease_or_assignment_commit_authorized,
            "lease_or_assignment_commit_authorized",
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
            "owner_development_bridge_direction_acknowledged",
            owner_development_bridge_direction_acknowledged,
        )
        object.__setattr__(
            self,
            "owner_consent_required_for_each_use_scope",
            owner_consent_required_for_each_use_scope,
        )
        object.__setattr__(self, "development_only_required", development_only_required)
        object.__setattr__(
            self,
            "explicit_owner_use_scope_approved",
            explicit_owner_use_scope_approved,
        )
        object.__setattr__(
            self,
            "development_proof_scope_defined",
            development_proof_scope_defined,
        )
        object.__setattr__(
            self,
            "manual_owner_assisted_transport_semantic_candidate",
            manual_owner_assisted_transport_semantic_candidate,
        )
        object.__setattr__(
            self,
            "bounded_proof_assignment_required",
            bounded_proof_assignment_required,
        )
        object.__setattr__(self, "clear_evidence_report_required", clear_evidence_report_required)
        object.__setattr__(
            self,
            "replaceable_by_production_route_required",
            replaceable_by_production_route_required,
        )
        object.__setattr__(self, "no_secrets_policy_required", no_secrets_policy_required)
        object.__setattr__(
            self,
            "no_raw_payload_retention_required",
            no_raw_payload_retention_required,
        )
        object.__setattr__(
            self,
            "production_dependency_authorized",
            production_dependency_authorized,
        )
        object.__setattr__(
            self,
            "unbounded_owner_machine_dependency_authorized",
            unbounded_owner_machine_dependency_authorized,
        )
        object.__setattr__(self, "silent_use_authorized", silent_use_authorized)
        object.__setattr__(
            self,
            "owner_private_data_storage_authorized",
            owner_private_data_storage_authorized,
        )
        object.__setattr__(self, "scalability_proof_inferred", scalability_proof_inferred)
        object.__setattr__(
            self,
            "permanent_architecture_authorized",
            permanent_architecture_authorized,
        )
        object.__setattr__(
            self,
            "live_proof_execution_authorized",
            live_proof_execution_authorized,
        )
        object.__setattr__(self, "route_registration_authorized", route_registration_authorized)
        object.__setattr__(self, "route_selection_authorized", route_selection_authorized)
        object.__setattr__(self, "fallback_execution_authorized", fallback_execution_authorized)
        object.__setattr__(
            self,
            "lease_or_assignment_commit_authorized",
            lease_or_assignment_commit_authorized,
        )
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
        object.__setattr__(self, "evidence_reference_ids", evidence_reference_ids)

        false_bool_fields = (
            ("explicit_owner_use_scope_approved", explicit_owner_use_scope_approved),
            ("development_proof_scope_defined", development_proof_scope_defined),
            ("production_dependency_authorized", production_dependency_authorized),
            (
                "unbounded_owner_machine_dependency_authorized",
                unbounded_owner_machine_dependency_authorized,
            ),
            ("silent_use_authorized", silent_use_authorized),
            ("owner_private_data_storage_authorized", owner_private_data_storage_authorized),
            ("scalability_proof_inferred", scalability_proof_inferred),
            ("permanent_architecture_authorized", permanent_architecture_authorized),
            ("live_proof_execution_authorized", live_proof_execution_authorized),
            ("route_registration_authorized", route_registration_authorized),
            ("route_selection_authorized", route_selection_authorized),
            ("fallback_execution_authorized", fallback_execution_authorized),
            ("lease_or_assignment_commit_authorized", lease_or_assignment_commit_authorized),
            ("provider_access_permission_inferred", provider_access_permission_inferred),
            ("parser_success_inferred", parser_success_inferred),
            ("scan_success_inferred", scan_success_inferred),
            ("notification_delivery_inferred", notification_delivery_inferred),
        )
        true_bool_fields = (
            (
                "owner_development_bridge_direction_acknowledged",
                owner_development_bridge_direction_acknowledged,
            ),
            (
                "owner_consent_required_for_each_use_scope",
                owner_consent_required_for_each_use_scope,
            ),
            ("development_only_required", development_only_required),
            (
                "manual_owner_assisted_transport_semantic_candidate",
                manual_owner_assisted_transport_semantic_candidate,
            ),
            ("bounded_proof_assignment_required", bounded_proof_assignment_required),
            ("clear_evidence_report_required", clear_evidence_report_required),
            ("replaceable_by_production_route_required", replaceable_by_production_route_required),
            ("no_secrets_policy_required", no_secrets_policy_required),
            ("no_raw_payload_retention_required", no_raw_payload_retention_required),
        )

        for field_name, field_value in false_bool_fields + true_bool_fields:
            if type(field_value) is not bool:
                raise ValueError(f"{field_name} must be a bool")

        for field_name, field_value in false_bool_fields:
            if field_value is not False:
                raise ValueError(f"{field_name} must be False")

        for field_name, field_value in true_bool_fields:
            if field_value is not True:
                raise ValueError(f"{field_name} must be True")

        if authority is not DevelopmentBridgeAuthority.EGRESS_ROUTING_SERVER:
            raise ValueError("authority must be EGRESS_ROUTING_SERVER")
        if route_family is not RouteFamily.OWNER_DEVELOPMENT_BRIDGE_ROUTE:
            raise ValueError("route_family must be OWNER_DEVELOPMENT_BRIDGE_ROUTE")
        if route_id != route_capability.route_id:
            raise ValueError("route_id must match route_capability.route_id")
        if route_id != session_secret_gate.route_id:
            raise ValueError("route_id must match session_secret_gate.route_id")
        if route_capability is not session_secret_gate.route_capability:
            raise ValueError("session_secret_gate.route_capability must match route_capability")
        if evidence_reference_ids != route_capability.evidence_reference_ids:
            raise ValueError(
                "evidence_reference_ids must match route_capability.evidence_reference_ids"
            )
        if session_secret_gate.evidence_reference_ids != route_capability.evidence_reference_ids:
            raise ValueError(
                "session_secret_gate.evidence_reference_ids must match "
                "route_capability.evidence_reference_ids"
            )
        if session_secret_gate.session_policy_status is not route_capability.session_policy_status:
            raise ValueError(
                "session_secret_gate.session_policy_status must match "
                "route_capability.session_policy_status"
            )

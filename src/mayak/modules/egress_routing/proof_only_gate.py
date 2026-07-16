from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeVar, cast

from .contracts import RouteCapability, RouteEvidenceStatus, RouteFamily, SessionPolicyStatus
from .session_secret_gate import EgressSessionSecretAuthority, EgressSessionSecretGateBoundary

ER13A_TASK_ID = "ER-13A-PROOF-ONLY-FAIL-CLOSED-GATE-20260716-051"

__all__ = (
    "ER13A_TASK_ID",
    "EgressProofOnlyAuthority",
    "EgressProofOnlyGateBoundary",
)

_ALLOWED_SESSION_POLICY_STATUSES = frozenset(
    {
        SessionPolicyStatus.PROHIBITED,
        SessionPolicyStatus.BLOCKED_PENDING_ISOLATED_PROJECT_SESSION_GATE,
    }
)

_ALLOWED_PROOF_ROUTE_FAMILIES = frozenset(
    {
        RouteFamily.LINUX_REFERENCE_STYLE_ROUTE,
        RouteFamily.RUSSIAN_RESIDENTIAL_ROUTE,
        RouteFamily.OWNER_DEVELOPMENT_BRIDGE_ROUTE,
        RouteFamily.BROWSER_EXTENSION_ROUTE,
        RouteFamily.WINDOWS_VM_BROWSER_WORKER_ROUTE,
    }
)

_ROUTE_FAMILY_ACKNOWLEDGEMENT_FIELDS = {
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
}

_ROUTE_FAMILY_ACKNOWLEDGEMENT_FIELDS_ORDER = (
    "primary_linux_reference_style_direction_acknowledged",
    "russian_residential_future_route_direction_acknowledged",
    "owner_development_bridge_direction_acknowledged",
    "browser_extension_owner_avito_evidence_acknowledged",
    "windows_vm_browser_worker_fallback_direction_acknowledged",
)

_MANDATORY_TRUE_FIELDS = (
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

_FAIL_CLOSED_FALSE_FIELDS = (
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

_REQUIRED_REASON_CODES = (
    "proof-only-execution-blocked",
    "explicit-owner-proof-task-required",
    "legal-access-and-scope-gates-unsatisfied",
)

E = TypeVar("E", bound=Enum)
T = TypeVar("T")


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


def _require_exact_enum(value: object, enum_cls: type[E], field_name: str) -> E:
    if type(value) is not enum_cls:
        raise ValueError(f"{field_name} must be {enum_cls.__name__}")
    return cast(E, value)


def _require_exact_record(value: object, record_cls: type[T], field_name: str) -> T:
    if type(value) is not record_cls:
        raise ValueError(f"{field_name} must be {record_cls.__name__}")
    return cast(T, value)


def _require_text_tuple(
    value: object,
    field_name: str,
    *,
    non_empty: bool = False,
    require_unique: bool = False,
) -> tuple[str, ...]:
    items = _require_tuple(value, field_name)
    if non_empty and not items:
        raise ValueError(f"{field_name} must not be empty")

    validated: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = _require_text(item, field_name)
        if require_unique and text in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(text)
        validated.append(text)
    return tuple(validated)


def _require_route_capability(value: object) -> RouteCapability:
    capability = _require_exact_record(value, RouteCapability, "route_capability")

    _require_text(capability.capability_id, "route_capability.capability_id")
    _require_text(capability.route_id, "route_capability.route_id")
    _require_text_tuple(
        capability.destination_scope,
        "route_capability.destination_scope",
        non_empty=True,
        require_unique=True,
    )
    _require_text_tuple(
        capability.operation_classes,
        "route_capability.operation_classes",
        non_empty=True,
        require_unique=True,
    )
    _require_text_tuple(
        capability.unsupported_classes,
        "route_capability.unsupported_classes",
        require_unique=True,
    )
    _require_text_tuple(
        capability.evidence_reference_ids,
        "route_capability.evidence_reference_ids",
        non_empty=True,
        require_unique=True,
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


def _require_session_secret_gate(
    value: object,
    route_capability: RouteCapability,
) -> EgressSessionSecretGateBoundary:
    gate = _require_exact_record(value, EgressSessionSecretGateBoundary, "session_secret_gate")

    _require_text(gate.boundary_id, "session_secret_gate.boundary_id")
    authority = _require_exact_enum(
        gate.authority,
        EgressSessionSecretAuthority,
        "session_secret_gate.authority",
    )
    _require_text(gate.route_id, "session_secret_gate.route_id")
    session_policy_status = _require_exact_enum(
        gate.session_policy_status,
        SessionPolicyStatus,
        "session_secret_gate.session_policy_status",
    )
    isolated_project_session_gate_satisfied = _require_bool(
        gate.isolated_project_session_gate_satisfied,
        "session_secret_gate.isolated_project_session_gate_satisfied",
    )
    project_owned_session_authorized = _require_bool(
        gate.project_owned_session_authorized,
        "session_secret_gate.project_owned_session_authorized",
    )
    project_owned_cookie_profile_authorized = _require_bool(
        gate.project_owned_cookie_profile_authorized,
        "session_secret_gate.project_owned_cookie_profile_authorized",
    )
    personal_browser_profile_access_authorized = _require_bool(
        gate.personal_browser_profile_access_authorized,
        "session_secret_gate.personal_browser_profile_access_authorized",
    )
    browser_password_access_authorized = _require_bool(
        gate.browser_password_access_authorized,
        "session_secret_gate.browser_password_access_authorized",
    )
    owner_private_session_default_authorized = _require_bool(
        gate.owner_private_session_default_authorized,
        "session_secret_gate.owner_private_session_default_authorized",
    )
    foreign_or_unrelated_cookie_reuse_authorized = _require_bool(
        gate.foreign_or_unrelated_cookie_reuse_authorized,
        "session_secret_gate.foreign_or_unrelated_cookie_reuse_authorized",
    )
    raw_cookie_material_authorized = _require_bool(
        gate.raw_cookie_material_authorized,
        "session_secret_gate.raw_cookie_material_authorized",
    )
    raw_session_token_material_authorized = _require_bool(
        gate.raw_session_token_material_authorized,
        "session_secret_gate.raw_session_token_material_authorized",
    )
    raw_credential_material_authorized = _require_bool(
        gate.raw_credential_material_authorized,
        "session_secret_gate.raw_credential_material_authorized",
    )
    safe_reference_only = _require_bool(
        gate.safe_reference_only,
        "session_secret_gate.safe_reference_only",
    )
    rotation_required = _require_bool(
        gate.rotation_required,
        "session_secret_gate.rotation_required",
    )
    revocation_required = _require_bool(
        gate.revocation_required,
        "session_secret_gate.revocation_required",
    )
    redacted_diagnostics_required = _require_bool(
        gate.redacted_diagnostics_required,
        "session_secret_gate.redacted_diagnostics_required",
    )
    secret_logging_authorized = _require_bool(
        gate.secret_logging_authorized,
        "session_secret_gate.secret_logging_authorized",
    )
    secret_report_authorized = _require_bool(
        gate.secret_report_authorized,
        "session_secret_gate.secret_report_authorized",
    )
    secret_git_storage_authorized = _require_bool(
        gate.secret_git_storage_authorized,
        "session_secret_gate.secret_git_storage_authorized",
    )
    runtime_session_creation_authorized = _require_bool(
        gate.runtime_session_creation_authorized,
        "session_secret_gate.runtime_session_creation_authorized",
    )
    provider_access_permission_inferred = _require_bool(
        gate.provider_access_permission_inferred,
        "session_secret_gate.provider_access_permission_inferred",
    )
    parser_success_inferred = _require_bool(
        gate.parser_success_inferred,
        "session_secret_gate.parser_success_inferred",
    )
    scan_success_inferred = _require_bool(
        gate.scan_success_inferred,
        "session_secret_gate.scan_success_inferred",
    )
    notification_delivery_inferred = _require_bool(
        gate.notification_delivery_inferred,
        "session_secret_gate.notification_delivery_inferred",
    )
    _require_text_tuple(
        gate.reason_codes,
        "session_secret_gate.reason_codes",
        non_empty=True,
        require_unique=True,
    )
    _require_text_tuple(
        gate.evidence_reference_ids,
        "session_secret_gate.evidence_reference_ids",
        non_empty=True,
        require_unique=True,
    )

    if authority is not EgressSessionSecretAuthority.EGRESS_ROUTING_SERVER:
        raise ValueError("session_secret_gate.authority must be EGRESS_ROUTING_SERVER")
    if gate.route_capability is not route_capability:
        raise ValueError("session_secret_gate.route_capability must be route_capability")
    if gate.route_id != route_capability.route_id:
        raise ValueError("session_secret_gate.route_id must match route_capability.route_id")
    if session_policy_status is not route_capability.session_policy_status:
        raise ValueError(
            "session_secret_gate.session_policy_status must match "
            "route_capability.session_policy_status"
        )
    if session_policy_status not in _ALLOWED_SESSION_POLICY_STATUSES:
        raise ValueError("session_secret_gate.session_policy_status is not allowed in ER-13A")
    if route_capability.session_policy_status not in _ALLOWED_SESSION_POLICY_STATUSES:
        raise ValueError("route_capability.session_policy_status is not allowed in ER-13A")
    if gate.evidence_reference_ids != route_capability.evidence_reference_ids:
        raise ValueError(
            "session_secret_gate.evidence_reference_ids must match "
            "route_capability.evidence_reference_ids"
        )
    if isolated_project_session_gate_satisfied is not False:
        raise ValueError(
            "session_secret_gate.isolated_project_session_gate_satisfied "
            "must be False"
        )
    if project_owned_session_authorized is not False:
        raise ValueError("session_secret_gate.project_owned_session_authorized must be False")
    if project_owned_cookie_profile_authorized is not False:
        raise ValueError(
            "session_secret_gate.project_owned_cookie_profile_authorized "
            "must be False"
        )
    if personal_browser_profile_access_authorized is not False:
        raise ValueError(
            "session_secret_gate.personal_browser_profile_access_authorized "
            "must be False"
        )
    if browser_password_access_authorized is not False:
        raise ValueError(
            "session_secret_gate.browser_password_access_authorized must be False"
        )
    if owner_private_session_default_authorized is not False:
        raise ValueError(
            "session_secret_gate.owner_private_session_default_authorized "
            "must be False"
        )
    if foreign_or_unrelated_cookie_reuse_authorized is not False:
        raise ValueError(
            "session_secret_gate.foreign_or_unrelated_cookie_reuse_authorized "
            "must be False"
        )
    if raw_cookie_material_authorized is not False:
        raise ValueError(
            "session_secret_gate.raw_cookie_material_authorized must be False"
        )
    if raw_session_token_material_authorized is not False:
        raise ValueError(
            "session_secret_gate.raw_session_token_material_authorized must be False"
        )
    if raw_credential_material_authorized is not False:
        raise ValueError(
            "session_secret_gate.raw_credential_material_authorized must be False"
        )
    if safe_reference_only is not True:
        raise ValueError("session_secret_gate.safe_reference_only must be True")
    if rotation_required is not True:
        raise ValueError("session_secret_gate.rotation_required must be True")
    if revocation_required is not True:
        raise ValueError("session_secret_gate.revocation_required must be True")
    if redacted_diagnostics_required is not True:
        raise ValueError("session_secret_gate.redacted_diagnostics_required must be True")
    if secret_logging_authorized is not False:
        raise ValueError("session_secret_gate.secret_logging_authorized must be False")
    if secret_report_authorized is not False:
        raise ValueError("session_secret_gate.secret_report_authorized must be False")
    if secret_git_storage_authorized is not False:
        raise ValueError("session_secret_gate.secret_git_storage_authorized must be False")
    if runtime_session_creation_authorized is not False:
        raise ValueError("session_secret_gate.runtime_session_creation_authorized must be False")
    if provider_access_permission_inferred is not False:
        raise ValueError("session_secret_gate.provider_access_permission_inferred must be False")
    if parser_success_inferred is not False:
        raise ValueError("session_secret_gate.parser_success_inferred must be False")
    if scan_success_inferred is not False:
        raise ValueError("session_secret_gate.scan_success_inferred must be False")
    if notification_delivery_inferred is not False:
        raise ValueError("session_secret_gate.notification_delivery_inferred must be False")

    return gate


class EgressProofOnlyAuthority(str, Enum):
    EGRESS_ROUTING_SERVER = "EGRESS_ROUTING_SERVER"


@dataclass(frozen=True, slots=True)
class EgressProofOnlyGateBoundary:
    boundary_id: str
    authority: EgressProofOnlyAuthority
    route_capability: RouteCapability
    session_secret_gate: EgressSessionSecretGateBoundary
    route_family: RouteFamily
    route_id: str
    primary_linux_reference_style_direction_acknowledged: bool
    russian_residential_future_route_direction_acknowledged: bool
    owner_development_bridge_direction_acknowledged: bool
    browser_extension_owner_avito_evidence_acknowledged: bool
    windows_vm_browser_worker_fallback_direction_acknowledged: bool
    separate_explicit_owner_proof_task_required: bool
    legal_and_access_gate_required: bool
    exact_source_scope_required: bool
    maximum_attempts_required: bool
    maximum_duration_required: bool
    route_identity_required: bool
    no_secrets_logging_required: bool
    no_raw_payload_retention_required: bool
    no_captcha_solving_required: bool
    bounded_repeatability_check_required: bool
    explicit_stop_conditions_required: bool
    clear_evidence_report_required: bool
    current_explicit_owner_proof_scope_approved: bool
    legal_and_access_gate_satisfied: bool
    exact_source_scope_defined: bool
    attempt_bound_defined: bool
    duration_bound_defined: bool
    proof_execution_authorized: bool
    live_provider_traffic_authorized: bool
    mass_requests_authorized: bool
    production_scheduler_integration_authorized: bool
    database_persistence_authorized: bool
    notification_delivery_authorized: bool
    unbounded_retry_authorized: bool
    uncontrolled_fallback_authorized: bool
    captcha_solving_authorized: bool
    raw_payload_retention_authorized: bool
    secret_or_cookie_disclosure_authorized: bool
    provider_access_permission_inferred: bool
    parser_success_inferred: bool
    scan_success_inferred: bool
    notification_delivery_inferred: bool
    production_readiness_inferred: bool
    scalability_proof_inferred: bool
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        capability = _require_route_capability(self.route_capability)
        object.__setattr__(self, "route_capability", capability)

        session_secret_gate = _require_session_secret_gate(self.session_secret_gate, capability)
        object.__setattr__(self, "session_secret_gate", session_secret_gate)

        boundary_id = _require_text(self.boundary_id, "boundary_id")
        authority = _require_exact_enum(
            self.authority,
            EgressProofOnlyAuthority,
            "authority",
        )
        route_family = _require_exact_enum(self.route_family, RouteFamily, "route_family")
        route_id = _require_text(self.route_id, "route_id")

        if route_family not in _ALLOWED_PROOF_ROUTE_FAMILIES:
            raise ValueError("route_family is not allowed in current ER-13A scope")

        primary_linux_reference_style_direction_acknowledged = _require_bool(
            self.primary_linux_reference_style_direction_acknowledged,
            "primary_linux_reference_style_direction_acknowledged",
        )
        russian_residential_future_route_direction_acknowledged = _require_bool(
            self.russian_residential_future_route_direction_acknowledged,
            "russian_residential_future_route_direction_acknowledged",
        )
        owner_development_bridge_direction_acknowledged = _require_bool(
            self.owner_development_bridge_direction_acknowledged,
            "owner_development_bridge_direction_acknowledged",
        )
        browser_extension_owner_avito_evidence_acknowledged = _require_bool(
            self.browser_extension_owner_avito_evidence_acknowledged,
            "browser_extension_owner_avito_evidence_acknowledged",
        )
        windows_vm_browser_worker_fallback_direction_acknowledged = _require_bool(
            self.windows_vm_browser_worker_fallback_direction_acknowledged,
            "windows_vm_browser_worker_fallback_direction_acknowledged",
        )
        separate_explicit_owner_proof_task_required = _require_bool(
            self.separate_explicit_owner_proof_task_required,
            "separate_explicit_owner_proof_task_required",
        )
        legal_and_access_gate_required = _require_bool(
            self.legal_and_access_gate_required,
            "legal_and_access_gate_required",
        )
        exact_source_scope_required = _require_bool(
            self.exact_source_scope_required,
            "exact_source_scope_required",
        )
        maximum_attempts_required = _require_bool(
            self.maximum_attempts_required,
            "maximum_attempts_required",
        )
        maximum_duration_required = _require_bool(
            self.maximum_duration_required,
            "maximum_duration_required",
        )
        route_identity_required = _require_bool(
            self.route_identity_required,
            "route_identity_required",
        )
        no_secrets_logging_required = _require_bool(
            self.no_secrets_logging_required,
            "no_secrets_logging_required",
        )
        no_raw_payload_retention_required = _require_bool(
            self.no_raw_payload_retention_required,
            "no_raw_payload_retention_required",
        )
        no_captcha_solving_required = _require_bool(
            self.no_captcha_solving_required,
            "no_captcha_solving_required",
        )
        bounded_repeatability_check_required = _require_bool(
            self.bounded_repeatability_check_required,
            "bounded_repeatability_check_required",
        )
        explicit_stop_conditions_required = _require_bool(
            self.explicit_stop_conditions_required,
            "explicit_stop_conditions_required",
        )
        clear_evidence_report_required = _require_bool(
            self.clear_evidence_report_required,
            "clear_evidence_report_required",
        )
        current_explicit_owner_proof_scope_approved = _require_bool(
            self.current_explicit_owner_proof_scope_approved,
            "current_explicit_owner_proof_scope_approved",
        )
        legal_and_access_gate_satisfied = _require_bool(
            self.legal_and_access_gate_satisfied,
            "legal_and_access_gate_satisfied",
        )
        exact_source_scope_defined = _require_bool(
            self.exact_source_scope_defined,
            "exact_source_scope_defined",
        )
        attempt_bound_defined = _require_bool(
            self.attempt_bound_defined,
            "attempt_bound_defined",
        )
        duration_bound_defined = _require_bool(
            self.duration_bound_defined, "duration_bound_defined"
        )
        proof_execution_authorized = _require_bool(
            self.proof_execution_authorized,
            "proof_execution_authorized",
        )
        live_provider_traffic_authorized = _require_bool(
            self.live_provider_traffic_authorized,
            "live_provider_traffic_authorized",
        )
        mass_requests_authorized = _require_bool(
            self.mass_requests_authorized,
            "mass_requests_authorized",
        )
        production_scheduler_integration_authorized = _require_bool(
            self.production_scheduler_integration_authorized,
            "production_scheduler_integration_authorized",
        )
        database_persistence_authorized = _require_bool(
            self.database_persistence_authorized,
            "database_persistence_authorized",
        )
        notification_delivery_authorized = _require_bool(
            self.notification_delivery_authorized,
            "notification_delivery_authorized",
        )
        unbounded_retry_authorized = _require_bool(
            self.unbounded_retry_authorized,
            "unbounded_retry_authorized",
        )
        uncontrolled_fallback_authorized = _require_bool(
            self.uncontrolled_fallback_authorized,
            "uncontrolled_fallback_authorized",
        )
        captcha_solving_authorized = _require_bool(
            self.captcha_solving_authorized,
            "captcha_solving_authorized",
        )
        raw_payload_retention_authorized = _require_bool(
            self.raw_payload_retention_authorized,
            "raw_payload_retention_authorized",
        )
        secret_or_cookie_disclosure_authorized = _require_bool(
            self.secret_or_cookie_disclosure_authorized,
            "secret_or_cookie_disclosure_authorized",
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
        production_readiness_inferred = _require_bool(
            self.production_readiness_inferred,
            "production_readiness_inferred",
        )
        scalability_proof_inferred = _require_bool(
            self.scalability_proof_inferred,
            "scalability_proof_inferred",
        )
        reason_codes = _require_text_tuple(
            self.reason_codes,
            "reason_codes",
            non_empty=True,
            require_unique=True,
        )
        evidence_reference_ids = _require_text_tuple(
            self.evidence_reference_ids,
            "evidence_reference_ids",
            non_empty=True,
            require_unique=True,
        )

        direction_values = {
            "primary_linux_reference_style_direction_acknowledged": (
                primary_linux_reference_style_direction_acknowledged
            ),
            "russian_residential_future_route_direction_acknowledged": (
                russian_residential_future_route_direction_acknowledged
            ),
            "owner_development_bridge_direction_acknowledged": (
                owner_development_bridge_direction_acknowledged
            ),
            "browser_extension_owner_avito_evidence_acknowledged": (
                browser_extension_owner_avito_evidence_acknowledged
            ),
            "windows_vm_browser_worker_fallback_direction_acknowledged": (
                windows_vm_browser_worker_fallback_direction_acknowledged
            ),
        }
        expected_true_field = _ROUTE_FAMILY_ACKNOWLEDGEMENT_FIELDS[route_family]
        for field_name in _ROUTE_FAMILY_ACKNOWLEDGEMENT_FIELDS_ORDER:
            expected_value = field_name == expected_true_field
            if direction_values[field_name] is not expected_value:
                raise ValueError(f"{field_name} must be {expected_value}")

        for field_name in _MANDATORY_TRUE_FIELDS:
            if getattr(self, field_name) is not True:
                raise ValueError(f"{field_name} must be True")
        for field_name in _FAIL_CLOSED_FALSE_FIELDS:
            if getattr(self, field_name) is not False:
                raise ValueError(f"{field_name} must be False")

        if authority is not EgressProofOnlyAuthority.EGRESS_ROUTING_SERVER:
            raise ValueError("authority must be EGRESS_ROUTING_SERVER")
        if route_id != capability.route_id:
            raise ValueError("route_id must match route_capability.route_id")
        if route_id != session_secret_gate.route_id:
            raise ValueError("route_id must match session_secret_gate.route_id")
        if session_secret_gate.route_capability is not capability:
            raise ValueError("session_secret_gate.route_capability must be route_capability")
        if session_secret_gate.session_policy_status is not capability.session_policy_status:
            raise ValueError(
                "session_secret_gate.session_policy_status must match "
                "route_capability.session_policy_status"
            )
        if session_secret_gate.evidence_reference_ids != capability.evidence_reference_ids:
            raise ValueError(
                "session_secret_gate.evidence_reference_ids must match "
                "route_capability.evidence_reference_ids"
            )
        if capability.route_id != route_id:
            raise ValueError("route_capability.route_id must match route_id")
        if evidence_reference_ids != capability.evidence_reference_ids:
            raise ValueError(
                "evidence_reference_ids must match "
                "route_capability.evidence_reference_ids"
            )
        if reason_codes != _REQUIRED_REASON_CODES:
            raise ValueError("reason_codes must contain the required ER-13A codes")
        if current_explicit_owner_proof_scope_approved is not False:
            raise ValueError("current_explicit_owner_proof_scope_approved must be False")
        if legal_and_access_gate_satisfied is not False:
            raise ValueError("legal_and_access_gate_satisfied must be False")
        if exact_source_scope_defined is not False:
            raise ValueError("exact_source_scope_defined must be False")
        if attempt_bound_defined is not False:
            raise ValueError("attempt_bound_defined must be False")
        if duration_bound_defined is not False:
            raise ValueError("duration_bound_defined must be False")
        if proof_execution_authorized is not False:
            raise ValueError("proof_execution_authorized must be False")
        if live_provider_traffic_authorized is not False:
            raise ValueError("live_provider_traffic_authorized must be False")
        if mass_requests_authorized is not False:
            raise ValueError("mass_requests_authorized must be False")
        if production_scheduler_integration_authorized is not False:
            raise ValueError("production_scheduler_integration_authorized must be False")
        if database_persistence_authorized is not False:
            raise ValueError("database_persistence_authorized must be False")
        if notification_delivery_authorized is not False:
            raise ValueError("notification_delivery_authorized must be False")
        if unbounded_retry_authorized is not False:
            raise ValueError("unbounded_retry_authorized must be False")
        if uncontrolled_fallback_authorized is not False:
            raise ValueError("uncontrolled_fallback_authorized must be False")
        if captcha_solving_authorized is not False:
            raise ValueError("captcha_solving_authorized must be False")
        if raw_payload_retention_authorized is not False:
            raise ValueError("raw_payload_retention_authorized must be False")
        if secret_or_cookie_disclosure_authorized is not False:
            raise ValueError("secret_or_cookie_disclosure_authorized must be False")
        if provider_access_permission_inferred is not False:
            raise ValueError("provider_access_permission_inferred must be False")
        if parser_success_inferred is not False:
            raise ValueError("parser_success_inferred must be False")
        if scan_success_inferred is not False:
            raise ValueError("scan_success_inferred must be False")
        if notification_delivery_inferred is not False:
            raise ValueError("notification_delivery_inferred must be False")
        if production_readiness_inferred is not False:
            raise ValueError("production_readiness_inferred must be False")
        if scalability_proof_inferred is not False:
            raise ValueError("scalability_proof_inferred must be False")

        object.__setattr__(self, "boundary_id", boundary_id)
        object.__setattr__(self, "authority", authority)
        object.__setattr__(self, "route_capability", capability)
        object.__setattr__(self, "session_secret_gate", session_secret_gate)
        object.__setattr__(self, "route_family", route_family)
        object.__setattr__(self, "route_id", route_id)
        object.__setattr__(
            self,
            "primary_linux_reference_style_direction_acknowledged",
            primary_linux_reference_style_direction_acknowledged,
        )
        object.__setattr__(
            self,
            "russian_residential_future_route_direction_acknowledged",
            russian_residential_future_route_direction_acknowledged,
        )
        object.__setattr__(
            self,
            "owner_development_bridge_direction_acknowledged",
            owner_development_bridge_direction_acknowledged,
        )
        object.__setattr__(
            self,
            "browser_extension_owner_avito_evidence_acknowledged",
            browser_extension_owner_avito_evidence_acknowledged,
        )
        object.__setattr__(
            self,
            "windows_vm_browser_worker_fallback_direction_acknowledged",
            windows_vm_browser_worker_fallback_direction_acknowledged,
        )
        object.__setattr__(
            self,
            "separate_explicit_owner_proof_task_required",
            separate_explicit_owner_proof_task_required,
        )
        object.__setattr__(self, "legal_and_access_gate_required", legal_and_access_gate_required)
        object.__setattr__(self, "exact_source_scope_required", exact_source_scope_required)
        object.__setattr__(self, "maximum_attempts_required", maximum_attempts_required)
        object.__setattr__(self, "maximum_duration_required", maximum_duration_required)
        object.__setattr__(self, "route_identity_required", route_identity_required)
        object.__setattr__(self, "no_secrets_logging_required", no_secrets_logging_required)
        object.__setattr__(
            self,
            "no_raw_payload_retention_required",
            no_raw_payload_retention_required,
        )
        object.__setattr__(self, "no_captcha_solving_required", no_captcha_solving_required)
        object.__setattr__(
            self,
            "bounded_repeatability_check_required",
            bounded_repeatability_check_required,
        )
        object.__setattr__(
            self,
            "explicit_stop_conditions_required",
            explicit_stop_conditions_required,
        )
        object.__setattr__(self, "clear_evidence_report_required", clear_evidence_report_required)
        object.__setattr__(
            self,
            "current_explicit_owner_proof_scope_approved",
            current_explicit_owner_proof_scope_approved,
        )
        object.__setattr__(self, "legal_and_access_gate_satisfied", legal_and_access_gate_satisfied)
        object.__setattr__(self, "exact_source_scope_defined", exact_source_scope_defined)
        object.__setattr__(self, "attempt_bound_defined", attempt_bound_defined)
        object.__setattr__(self, "duration_bound_defined", duration_bound_defined)
        object.__setattr__(self, "proof_execution_authorized", proof_execution_authorized)
        object.__setattr__(
            self,
            "live_provider_traffic_authorized",
            live_provider_traffic_authorized,
        )
        object.__setattr__(self, "mass_requests_authorized", mass_requests_authorized)
        object.__setattr__(
            self,
            "production_scheduler_integration_authorized",
            production_scheduler_integration_authorized,
        )
        object.__setattr__(
            self,
            "database_persistence_authorized",
            database_persistence_authorized,
        )
        object.__setattr__(
            self,
            "notification_delivery_authorized",
            notification_delivery_authorized,
        )
        object.__setattr__(
            self,
            "unbounded_retry_authorized",
            unbounded_retry_authorized,
        )
        object.__setattr__(
            self,
            "uncontrolled_fallback_authorized",
            uncontrolled_fallback_authorized,
        )
        object.__setattr__(self, "captcha_solving_authorized", captcha_solving_authorized)
        object.__setattr__(
            self,
            "raw_payload_retention_authorized",
            raw_payload_retention_authorized,
        )
        object.__setattr__(
            self,
            "secret_or_cookie_disclosure_authorized",
            secret_or_cookie_disclosure_authorized,
        )
        object.__setattr__(
            self,
            "provider_access_permission_inferred",
            provider_access_permission_inferred,
        )
        object.__setattr__(self, "parser_success_inferred", parser_success_inferred)
        object.__setattr__(self, "scan_success_inferred", scan_success_inferred)
        object.__setattr__(self, "notification_delivery_inferred", notification_delivery_inferred)
        object.__setattr__(self, "production_readiness_inferred", production_readiness_inferred)
        object.__setattr__(self, "scalability_proof_inferred", scalability_proof_inferred)
        object.__setattr__(self, "reason_codes", reason_codes)
        object.__setattr__(self, "evidence_reference_ids", evidence_reference_ids)

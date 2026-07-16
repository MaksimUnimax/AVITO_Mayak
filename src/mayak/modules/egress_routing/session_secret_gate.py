from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeVar, cast

from .contracts import RouteCapability, RouteEvidenceStatus, SessionPolicyStatus

ER09A_TASK_ID = "ER-09A-SESSION-SECRET-FAIL-CLOSED-BOUNDARY-20260716-044"

__all__ = (
    "ER09A_TASK_ID",
    "EgressSessionSecretAuthority",
    "EgressSessionSecretGateBoundary",
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


class EgressSessionSecretAuthority(str, Enum):
    EGRESS_ROUTING_SERVER = "EGRESS_ROUTING_SERVER"


_ALLOWED_SESSION_POLICY_STATUSES = frozenset(
    {
        SessionPolicyStatus.PROHIBITED,
        SessionPolicyStatus.BLOCKED_PENDING_ISOLATED_PROJECT_SESSION_GATE,
    }
)


@dataclass(frozen=True, slots=True)
class EgressSessionSecretGateBoundary:
    boundary_id: str
    authority: EgressSessionSecretAuthority
    route_capability: RouteCapability
    route_id: str
    session_policy_status: SessionPolicyStatus
    isolated_project_session_gate_satisfied: bool
    project_owned_session_authorized: bool
    project_owned_cookie_profile_authorized: bool
    personal_browser_profile_access_authorized: bool
    browser_password_access_authorized: bool
    owner_private_session_default_authorized: bool
    foreign_or_unrelated_cookie_reuse_authorized: bool
    raw_cookie_material_authorized: bool
    raw_session_token_material_authorized: bool
    raw_credential_material_authorized: bool
    safe_reference_only: bool
    rotation_required: bool
    revocation_required: bool
    redacted_diagnostics_required: bool
    secret_logging_authorized: bool
    secret_report_authorized: bool
    secret_git_storage_authorized: bool
    runtime_session_creation_authorized: bool
    provider_access_permission_inferred: bool
    parser_success_inferred: bool
    scan_success_inferred: bool
    notification_delivery_inferred: bool
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        capability = _require_route_capability(self.route_capability)
        object.__setattr__(self, "route_capability", capability)
        boundary_id = _require_text(self.boundary_id, "boundary_id")
        authority = _require_exact_enum(
            self.authority,
            EgressSessionSecretAuthority,
            "authority",
        )
        route_id = _require_text(self.route_id, "route_id")
        session_policy_status = _require_exact_enum(
            self.session_policy_status,
            SessionPolicyStatus,
            "session_policy_status",
        )
        isolated_project_session_gate_satisfied = _require_bool(
            self.isolated_project_session_gate_satisfied,
            "isolated_project_session_gate_satisfied",
        )
        project_owned_session_authorized = _require_bool(
            self.project_owned_session_authorized,
            "project_owned_session_authorized",
        )
        project_owned_cookie_profile_authorized = _require_bool(
            self.project_owned_cookie_profile_authorized,
            "project_owned_cookie_profile_authorized",
        )
        personal_browser_profile_access_authorized = _require_bool(
            self.personal_browser_profile_access_authorized,
            "personal_browser_profile_access_authorized",
        )
        browser_password_access_authorized = _require_bool(
            self.browser_password_access_authorized,
            "browser_password_access_authorized",
        )
        owner_private_session_default_authorized = _require_bool(
            self.owner_private_session_default_authorized,
            "owner_private_session_default_authorized",
        )
        foreign_or_unrelated_cookie_reuse_authorized = _require_bool(
            self.foreign_or_unrelated_cookie_reuse_authorized,
            "foreign_or_unrelated_cookie_reuse_authorized",
        )
        raw_cookie_material_authorized = _require_bool(
            self.raw_cookie_material_authorized,
            "raw_cookie_material_authorized",
        )
        raw_session_token_material_authorized = _require_bool(
            self.raw_session_token_material_authorized,
            "raw_session_token_material_authorized",
        )
        raw_credential_material_authorized = _require_bool(
            self.raw_credential_material_authorized,
            "raw_credential_material_authorized",
        )
        safe_reference_only = _require_bool(self.safe_reference_only, "safe_reference_only")
        rotation_required = _require_bool(self.rotation_required, "rotation_required")
        revocation_required = _require_bool(self.revocation_required, "revocation_required")
        redacted_diagnostics_required = _require_bool(
            self.redacted_diagnostics_required,
            "redacted_diagnostics_required",
        )
        secret_logging_authorized = _require_bool(
            self.secret_logging_authorized,
            "secret_logging_authorized",
        )
        secret_report_authorized = _require_bool(
            self.secret_report_authorized,
            "secret_report_authorized",
        )
        secret_git_storage_authorized = _require_bool(
            self.secret_git_storage_authorized,
            "secret_git_storage_authorized",
        )
        runtime_session_creation_authorized = _require_bool(
            self.runtime_session_creation_authorized,
            "runtime_session_creation_authorized",
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

        object.__setattr__(self, "boundary_id", boundary_id)
        object.__setattr__(self, "authority", authority)
        object.__setattr__(self, "route_id", route_id)
        object.__setattr__(self, "session_policy_status", session_policy_status)
        object.__setattr__(
            self,
            "isolated_project_session_gate_satisfied",
            isolated_project_session_gate_satisfied,
        )
        object.__setattr__(
            self,
            "project_owned_session_authorized",
            project_owned_session_authorized,
        )
        object.__setattr__(
            self,
            "project_owned_cookie_profile_authorized",
            project_owned_cookie_profile_authorized,
        )
        object.__setattr__(
            self,
            "personal_browser_profile_access_authorized",
            personal_browser_profile_access_authorized,
        )
        object.__setattr__(
            self,
            "browser_password_access_authorized",
            browser_password_access_authorized,
        )
        object.__setattr__(
            self,
            "owner_private_session_default_authorized",
            owner_private_session_default_authorized,
        )
        object.__setattr__(
            self,
            "foreign_or_unrelated_cookie_reuse_authorized",
            foreign_or_unrelated_cookie_reuse_authorized,
        )
        object.__setattr__(self, "raw_cookie_material_authorized", raw_cookie_material_authorized)
        object.__setattr__(
            self,
            "raw_session_token_material_authorized",
            raw_session_token_material_authorized,
        )
        object.__setattr__(
            self,
            "raw_credential_material_authorized",
            raw_credential_material_authorized,
        )
        object.__setattr__(self, "safe_reference_only", safe_reference_only)
        object.__setattr__(self, "rotation_required", rotation_required)
        object.__setattr__(self, "revocation_required", revocation_required)
        object.__setattr__(
            self,
            "redacted_diagnostics_required",
            redacted_diagnostics_required,
        )
        object.__setattr__(self, "secret_logging_authorized", secret_logging_authorized)
        object.__setattr__(self, "secret_report_authorized", secret_report_authorized)
        object.__setattr__(self, "secret_git_storage_authorized", secret_git_storage_authorized)
        object.__setattr__(
            self,
            "runtime_session_creation_authorized",
            runtime_session_creation_authorized,
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

        if authority is not EgressSessionSecretAuthority.EGRESS_ROUTING_SERVER:
            raise ValueError("authority must be EGRESS_ROUTING_SERVER")
        if route_id != capability.route_id:
            raise ValueError("route_id must match route_capability.route_id")
        if session_policy_status is not capability.session_policy_status:
            raise ValueError(
                "session_policy_status must match route_capability.session_policy_status"
            )
        if session_policy_status not in _ALLOWED_SESSION_POLICY_STATUSES:
            raise ValueError("isolated project session gate not open in current scope")
        if capability.session_policy_status not in _ALLOWED_SESSION_POLICY_STATUSES:
            raise ValueError("isolated project session gate not open in current scope")
        if evidence_reference_ids != capability.evidence_reference_ids:
            raise ValueError(
                "evidence_reference_ids must match route_capability.evidence_reference_ids"
            )
        if isolated_project_session_gate_satisfied is not False:
            raise ValueError("isolated_project_session_gate_satisfied must be False")
        if project_owned_session_authorized is not False:
            raise ValueError("project_owned_session_authorized must be False")
        if project_owned_cookie_profile_authorized is not False:
            raise ValueError("project_owned_cookie_profile_authorized must be False")
        if personal_browser_profile_access_authorized is not False:
            raise ValueError("personal_browser_profile_access_authorized must be False")
        if browser_password_access_authorized is not False:
            raise ValueError("browser_password_access_authorized must be False")
        if owner_private_session_default_authorized is not False:
            raise ValueError("owner_private_session_default_authorized must be False")
        if foreign_or_unrelated_cookie_reuse_authorized is not False:
            raise ValueError("foreign_or_unrelated_cookie_reuse_authorized must be False")
        if raw_cookie_material_authorized is not False:
            raise ValueError("raw_cookie_material_authorized must be False")
        if raw_session_token_material_authorized is not False:
            raise ValueError("raw_session_token_material_authorized must be False")
        if raw_credential_material_authorized is not False:
            raise ValueError("raw_credential_material_authorized must be False")
        if safe_reference_only is not True:
            raise ValueError("safe_reference_only must be True")
        if rotation_required is not True:
            raise ValueError("rotation_required must be True")
        if revocation_required is not True:
            raise ValueError("revocation_required must be True")
        if redacted_diagnostics_required is not True:
            raise ValueError("redacted_diagnostics_required must be True")
        if secret_logging_authorized is not False:
            raise ValueError("secret_logging_authorized must be False")
        if secret_report_authorized is not False:
            raise ValueError("secret_report_authorized must be False")
        if secret_git_storage_authorized is not False:
            raise ValueError("secret_git_storage_authorized must be False")
        if runtime_session_creation_authorized is not False:
            raise ValueError("runtime_session_creation_authorized must be False")
        if provider_access_permission_inferred is not False:
            raise ValueError("provider_access_permission_inferred must be False")
        if parser_success_inferred is not False:
            raise ValueError("parser_success_inferred must be False")
        if scan_success_inferred is not False:
            raise ValueError("scan_success_inferred must be False")
        if notification_delivery_inferred is not False:
            raise ValueError("notification_delivery_inferred must be False")

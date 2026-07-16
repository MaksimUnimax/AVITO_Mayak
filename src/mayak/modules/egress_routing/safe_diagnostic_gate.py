from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeVar, cast

from .contracts import (
    DiagnosticEvidenceKind,
    RouteFamily,
    RouteHealthStatus,
    SafeOperationalDiagnostic,
    TransportOutcomeStatus,
)

ER12A_TASK_ID = "ER-12A-SAFE-OPERATIONAL-DIAGNOSTIC-GATE-20260716-049"

__all__ = (
    "ER12A_TASK_ID",
    "SafeEgressDiagnosticAuthority",
    "SafeEgressDiagnosticGateBoundary",
)


def _require_exact_text(value: object, field_name: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-blank string")
    return value


def _require_exact_optional_text(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_exact_text(value, field_name)


def _require_exact_bool(value: object, field_name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_exact_int(value: object, field_name: str) -> int:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    return value


def _require_exact_non_negative_int(value: object, field_name: str) -> int:
    integer_value = _require_exact_int(value, field_name)
    if integer_value < 0:
        raise ValueError(f"{field_name} must be greater than or equal to zero")
    return integer_value


def _require_exact_tuple(value: object, field_name: str) -> tuple[object, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    return value


def _require_exact_text_tuple(value: object, field_name: str) -> tuple[str, ...]:
    items = _require_exact_tuple(value, field_name)
    for item in items:
        _require_exact_text(item, field_name)
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must not contain duplicates")
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


def _validate_evidence_kinds(
    diagnostic: SafeOperationalDiagnostic,
    attempt_count: int,
    profile_reference_id: str | None,
    fallback_policy_reference: str | None,
) -> tuple[DiagnosticEvidenceKind, ...]:
    expected = {
        DiagnosticEvidenceKind.SAFE_ID,
        DiagnosticEvidenceKind.CAPABILITY_REFERENCE,
        DiagnosticEvidenceKind.REDACTED_REASON_CODE,
        DiagnosticEvidenceKind.TIMESTAMP_REFERENCE,
        DiagnosticEvidenceKind.EVIDENCE_REFERENCE,
    }
    if diagnostic.duration_reference is not None:
        expected.add(DiagnosticEvidenceKind.DURATION_REFERENCE)
    if attempt_count > 0:
        expected.add(DiagnosticEvidenceKind.COUNT)
    if profile_reference_id is not None:
        expected.add(DiagnosticEvidenceKind.PROFILE_REFERENCE)
    if fallback_policy_reference is not None:
        expected.add(DiagnosticEvidenceKind.POLICY_REFERENCE)

    actual = _require_exact_tuple(diagnostic.evidence_kinds, "diagnostic.evidence_kinds")
    actual_set: set[DiagnosticEvidenceKind] = set()
    for item in actual:
        actual_set.add(
            _require_exact_enum(item, DiagnosticEvidenceKind, "diagnostic.evidence_kinds")
        )
    if len(actual_set) != len(actual):
        raise ValueError("diagnostic.evidence_kinds must not contain duplicates")
    if actual_set != expected:
        raise ValueError("diagnostic.evidence_kinds must match the expected ER-12A matrix")
    if DiagnosticEvidenceKind.SAFE_FINGERPRINT in actual_set:
        raise ValueError("diagnostic.evidence_kinds must not include SAFE_FINGERPRINT")
    return actual  # type: ignore[return-value]


class SafeEgressDiagnosticAuthority(str, Enum):
    EGRESS_ROUTING_SERVER = "EGRESS_ROUTING_SERVER"


@dataclass(frozen=True, slots=True)
class SafeEgressDiagnosticGateBoundary:
    boundary_id: str
    authority: SafeEgressDiagnosticAuthority
    diagnostic: SafeOperationalDiagnostic
    route_family: RouteFamily
    route_id: str
    capability_reference_id: str
    selection_decision_id: str | None
    fallback_policy_reference: str | None
    route_health_status: RouteHealthStatus
    fallback_attempted: bool
    attempt_count: int
    profile_reference_id: str | None
    safe_reference_only: bool
    redacted_reason_required: bool
    redacted_profile_reference_required: bool
    raw_provider_payload_authorized: bool
    full_html_or_json_authorized: bool
    cookie_or_session_material_authorized: bool
    proxy_credential_material_authorized: bool
    private_key_material_authorized: bool
    personal_browser_profile_data_authorized: bool
    full_account_or_beacon_data_authorized: bool
    raw_listing_content_authorized: bool
    secret_logging_authorized: bool
    durable_diagnostic_persistence_authorized: bool
    runtime_log_emission_authorized: bool
    provider_access_permission_inferred: bool
    parser_success_inferred: bool
    scan_success_inferred: bool
    notification_delivery_inferred: bool
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        boundary_id = _require_exact_text(self.boundary_id, "boundary_id")
        authority = _require_exact_enum(self.authority, SafeEgressDiagnosticAuthority, "authority")
        diagnostic = _require_exact_record(self.diagnostic, SafeOperationalDiagnostic, "diagnostic")
        route_family = _require_exact_enum(self.route_family, RouteFamily, "route_family")
        route_id = _require_exact_text(self.route_id, "route_id")
        capability_reference_id = _require_exact_text(
            self.capability_reference_id, "capability_reference_id"
        )
        selection_decision_id = _require_exact_optional_text(
            self.selection_decision_id, "selection_decision_id"
        )
        fallback_policy_reference = _require_exact_optional_text(
            self.fallback_policy_reference, "fallback_policy_reference"
        )
        route_health_status = _require_exact_enum(
            self.route_health_status,
            RouteHealthStatus,
            "route_health_status",
        )
        fallback_attempted = _require_exact_bool(self.fallback_attempted, "fallback_attempted")
        attempt_count = _require_exact_non_negative_int(self.attempt_count, "attempt_count")
        profile_reference_id = _require_exact_optional_text(
            self.profile_reference_id, "profile_reference_id"
        )

        safe_reference_only = _require_exact_bool(self.safe_reference_only, "safe_reference_only")
        redacted_reason_required = _require_exact_bool(
            self.redacted_reason_required,
            "redacted_reason_required",
        )
        redacted_profile_reference_required = _require_exact_bool(
            self.redacted_profile_reference_required,
            "redacted_profile_reference_required",
        )
        raw_provider_payload_authorized = _require_exact_bool(
            self.raw_provider_payload_authorized,
            "raw_provider_payload_authorized",
        )
        full_html_or_json_authorized = _require_exact_bool(
            self.full_html_or_json_authorized,
            "full_html_or_json_authorized",
        )
        cookie_or_session_material_authorized = _require_exact_bool(
            self.cookie_or_session_material_authorized,
            "cookie_or_session_material_authorized",
        )
        proxy_credential_material_authorized = _require_exact_bool(
            self.proxy_credential_material_authorized,
            "proxy_credential_material_authorized",
        )
        private_key_material_authorized = _require_exact_bool(
            self.private_key_material_authorized,
            "private_key_material_authorized",
        )
        personal_browser_profile_data_authorized = _require_exact_bool(
            self.personal_browser_profile_data_authorized,
            "personal_browser_profile_data_authorized",
        )
        full_account_or_beacon_data_authorized = _require_exact_bool(
            self.full_account_or_beacon_data_authorized,
            "full_account_or_beacon_data_authorized",
        )
        raw_listing_content_authorized = _require_exact_bool(
            self.raw_listing_content_authorized,
            "raw_listing_content_authorized",
        )
        secret_logging_authorized = _require_exact_bool(
            self.secret_logging_authorized,
            "secret_logging_authorized",
        )
        durable_diagnostic_persistence_authorized = _require_exact_bool(
            self.durable_diagnostic_persistence_authorized,
            "durable_diagnostic_persistence_authorized",
        )
        runtime_log_emission_authorized = _require_exact_bool(
            self.runtime_log_emission_authorized,
            "runtime_log_emission_authorized",
        )
        provider_access_permission_inferred = _require_exact_bool(
            self.provider_access_permission_inferred,
            "provider_access_permission_inferred",
        )
        parser_success_inferred = _require_exact_bool(
            self.parser_success_inferred,
            "parser_success_inferred",
        )
        scan_success_inferred = _require_exact_bool(
            self.scan_success_inferred,
            "scan_success_inferred",
        )
        notification_delivery_inferred = _require_exact_bool(
            self.notification_delivery_inferred,
            "notification_delivery_inferred",
        )
        reason_codes = _require_exact_text_tuple(self.reason_codes, "reason_codes")
        evidence_reference_ids = _require_exact_text_tuple(
            self.evidence_reference_ids,
            "evidence_reference_ids",
        )
        if not reason_codes:
            raise ValueError("reason_codes must not be empty")
        if not evidence_reference_ids:
            raise ValueError("evidence_reference_ids must not be empty")

        if diagnostic.route_id is None:
            raise ValueError("diagnostic.route_id must be a non-blank string")
        if diagnostic.route_id != route_id:
            raise ValueError("diagnostic.route_id must match route_id")
        if diagnostic.reason_code not in reason_codes:
            raise ValueError("diagnostic.reason_code must be included in reason_codes")
        diagnostic_evidence_reference_ids = _require_exact_text_tuple(
            diagnostic.evidence_reference_ids,
            "diagnostic.evidence_reference_ids",
        )
        if not diagnostic_evidence_reference_ids:
            raise ValueError("diagnostic.evidence_reference_ids must not be empty")
        if diagnostic_evidence_reference_ids != evidence_reference_ids:
            raise ValueError("evidence_reference_ids must match diagnostic.evidence_reference_ids")
        _require_exact_text(diagnostic.diagnostic_id, "diagnostic.diagnostic_id")
        _require_exact_text(diagnostic.reason_code, "diagnostic.reason_code")
        _require_exact_text(diagnostic.timestamp_reference, "diagnostic.timestamp_reference")
        _require_exact_text(diagnostic.correlation_id, "diagnostic.correlation_id")
        _require_exact_text(diagnostic.causation_id, "diagnostic.causation_id")
        _require_exact_optional_text(diagnostic.agent_id, "diagnostic.agent_id")
        _require_exact_optional_text(diagnostic.route_id, "diagnostic.route_id")
        _require_exact_optional_text(diagnostic.lease_id, "diagnostic.lease_id")
        _require_exact_optional_text(diagnostic.assignment_id, "diagnostic.assignment_id")
        _require_exact_optional_text(diagnostic.attempt_id, "diagnostic.attempt_id")
        if diagnostic.outcome_status is not None:
            _require_exact_enum(
                diagnostic.outcome_status,
                TransportOutcomeStatus,
                "diagnostic.outcome_status",
            )
        if fallback_attempted:
            if fallback_policy_reference is None:
                raise ValueError(
                    "fallback_policy_reference is required when fallback_attempted is True"
                )
            if attempt_count <= 0:
                raise ValueError(
                    "attempt_count must be greater than zero when fallback_attempted is True"
                )
        if not safe_reference_only:
            raise ValueError("safe_reference_only must be True")
        if not redacted_reason_required:
            raise ValueError("redacted_reason_required must be True")
        if not redacted_profile_reference_required:
            raise ValueError("redacted_profile_reference_required must be True")
        for field_name, field_value in (
            ("raw_provider_payload_authorized", raw_provider_payload_authorized),
            ("full_html_or_json_authorized", full_html_or_json_authorized),
            ("cookie_or_session_material_authorized", cookie_or_session_material_authorized),
            ("proxy_credential_material_authorized", proxy_credential_material_authorized),
            ("private_key_material_authorized", private_key_material_authorized),
            ("personal_browser_profile_data_authorized", personal_browser_profile_data_authorized),
            ("full_account_or_beacon_data_authorized", full_account_or_beacon_data_authorized),
            ("raw_listing_content_authorized", raw_listing_content_authorized),
            ("secret_logging_authorized", secret_logging_authorized),
            (
                "durable_diagnostic_persistence_authorized",
                durable_diagnostic_persistence_authorized,
            ),
            ("runtime_log_emission_authorized", runtime_log_emission_authorized),
            ("provider_access_permission_inferred", provider_access_permission_inferred),
            ("parser_success_inferred", parser_success_inferred),
            ("scan_success_inferred", scan_success_inferred),
            ("notification_delivery_inferred", notification_delivery_inferred),
        ):
            if field_value is not False:
                raise ValueError(f"{field_name} must be False")

        if selection_decision_id is not None:
            _require_exact_text(selection_decision_id, "selection_decision_id")
        if fallback_policy_reference is not None:
            _require_exact_text(fallback_policy_reference, "fallback_policy_reference")
        if profile_reference_id is not None:
            _require_exact_text(profile_reference_id, "profile_reference_id")

        _validate_evidence_kinds(
            diagnostic,
            attempt_count,
            profile_reference_id,
            fallback_policy_reference,
        )

        object.__setattr__(self, "boundary_id", boundary_id)
        object.__setattr__(self, "authority", authority)
        object.__setattr__(self, "diagnostic", diagnostic)
        object.__setattr__(self, "route_family", route_family)
        object.__setattr__(self, "route_id", route_id)
        object.__setattr__(self, "capability_reference_id", capability_reference_id)
        object.__setattr__(self, "selection_decision_id", selection_decision_id)
        object.__setattr__(self, "fallback_policy_reference", fallback_policy_reference)
        object.__setattr__(self, "route_health_status", route_health_status)
        object.__setattr__(self, "fallback_attempted", fallback_attempted)
        object.__setattr__(self, "attempt_count", attempt_count)
        object.__setattr__(self, "profile_reference_id", profile_reference_id)
        object.__setattr__(self, "safe_reference_only", safe_reference_only)
        object.__setattr__(self, "redacted_reason_required", redacted_reason_required)
        object.__setattr__(
            self,
            "redacted_profile_reference_required",
            redacted_profile_reference_required,
        )
        object.__setattr__(
            self, "raw_provider_payload_authorized", raw_provider_payload_authorized
        )
        object.__setattr__(self, "full_html_or_json_authorized", full_html_or_json_authorized)
        object.__setattr__(
            self,
            "cookie_or_session_material_authorized",
            cookie_or_session_material_authorized,
        )
        object.__setattr__(
            self,
            "proxy_credential_material_authorized",
            proxy_credential_material_authorized,
        )
        object.__setattr__(
            self, "private_key_material_authorized", private_key_material_authorized
        )
        object.__setattr__(
            self,
            "personal_browser_profile_data_authorized",
            personal_browser_profile_data_authorized,
        )
        object.__setattr__(
            self,
            "full_account_or_beacon_data_authorized",
            full_account_or_beacon_data_authorized,
        )
        object.__setattr__(self, "raw_listing_content_authorized", raw_listing_content_authorized)
        object.__setattr__(self, "secret_logging_authorized", secret_logging_authorized)
        object.__setattr__(
            self,
            "durable_diagnostic_persistence_authorized",
            durable_diagnostic_persistence_authorized,
        )
        object.__setattr__(self, "runtime_log_emission_authorized", runtime_log_emission_authorized)
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

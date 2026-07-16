from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass
from enum import Enum
from types import SimpleNamespace
from typing import Any, cast

import pytest

import mayak.modules.egress_routing.safe_diagnostic_gate as safe_diagnostic_gate_module
from mayak.modules import egress_routing
from mayak.modules.egress_routing import (
    ER12A_TASK_ID,
    DiagnosticEvidenceKind,
    RouteFamily,
    RouteHealthStatus,
    SafeEgressDiagnosticAuthority,
    SafeEgressDiagnosticGateBoundary,
    SafeOperationalDiagnostic,
    TransportOutcomeStatus,
)

EXPECTED_MODULE_EXPORTS = (
    "ER12A_TASK_ID",
    "SafeEgressDiagnosticAuthority",
    "SafeEgressDiagnosticGateBoundary",
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
    "ER07E_TASK_ID",
    "PolicyFallbackTransportOutcomeAuthority",
    "PolicyFallbackTransportOutcomeBoundary",
)

EXPECTED_FIELD_NAMES = (
    "boundary_id",
    "authority",
    "diagnostic",
    "route_family",
    "route_id",
    "capability_reference_id",
    "selection_decision_id",
    "fallback_policy_reference",
    "route_health_status",
    "fallback_attempted",
    "attempt_count",
    "profile_reference_id",
    "safe_reference_only",
    "redacted_reason_required",
    "redacted_profile_reference_required",
    "raw_provider_payload_authorized",
    "full_html_or_json_authorized",
    "cookie_or_session_material_authorized",
    "proxy_credential_material_authorized",
    "private_key_material_authorized",
    "personal_browser_profile_data_authorized",
    "full_account_or_beacon_data_authorized",
    "raw_listing_content_authorized",
    "secret_logging_authorized",
    "durable_diagnostic_persistence_authorized",
    "runtime_log_emission_authorized",
    "provider_access_permission_inferred",
    "parser_success_inferred",
    "scan_success_inferred",
    "notification_delivery_inferred",
    "reason_codes",
    "evidence_reference_ids",
)

EXPECTED_BOUNDARY_ID = "safe-diagnostic-boundary-01"
EXPECTED_ROUTE_ID = "route-safe-diagnostic-01"
EXPECTED_CAPABILITY_REFERENCE_ID = "capability-safe-diagnostic-01"
EXPECTED_SELECTION_DECISION_ID = "selection-decision-safe-diagnostic-01"
EXPECTED_FALLBACK_POLICY_REFERENCE = "fallback-policy-safe-diagnostic-01"
EXPECTED_PROFILE_REFERENCE_ID = "profile-safe-diagnostic-01"
EXPECTED_REASON_CODES = ("safe-diagnostic-reason-01",)
EXPECTED_EVIDENCE_REFERENCE_IDS = ("safe-diagnostic-evidence-01", "safe-diagnostic-evidence-02")
EXPECTED_DIAGNOSTIC_ID = "diagnostic-safe-01"
EXPECTED_TIMESTAMP_REFERENCE = "timestamp-safe-01"
EXPECTED_CORRELATION_ID = "correlation-safe-01"
EXPECTED_CAUSATION_ID = "causation-safe-01"
EXPECTED_DIAGNOSTIC_ROUTE_ID = EXPECTED_ROUTE_ID
EXPECTED_ROUTE_FAMILY = RouteFamily.LINUX_REFERENCE_STYLE_ROUTE
EXPECTED_ROUTE_HEALTH_STATUS = RouteHealthStatus.READY

EXPECTED_FALSE_BOOLEAN_FIELDS = (
    "raw_provider_payload_authorized",
    "full_html_or_json_authorized",
    "cookie_or_session_material_authorized",
    "proxy_credential_material_authorized",
    "private_key_material_authorized",
    "personal_browser_profile_data_authorized",
    "full_account_or_beacon_data_authorized",
    "raw_listing_content_authorized",
    "secret_logging_authorized",
    "durable_diagnostic_persistence_authorized",
    "runtime_log_emission_authorized",
    "provider_access_permission_inferred",
    "parser_success_inferred",
    "scan_success_inferred",
    "notification_delivery_inferred",
)

EXPECTED_TRUE_BOOLEAN_FIELDS = (
    "safe_reference_only",
    "redacted_reason_required",
    "redacted_profile_reference_required",
)

EXPECTED_DIAGNOSTIC_TEXT_FIELDS = (
    "diagnostic_id",
    "agent_id",
    "route_id",
    "lease_id",
    "assignment_id",
    "attempt_id",
    "reason_code",
    "timestamp_reference",
    "duration_reference",
    "correlation_id",
    "causation_id",
)

EXPECTED_BOUNDARY_TEXT_FIELDS = (
    "boundary_id",
    "route_id",
    "capability_reference_id",
    "selection_decision_id",
    "fallback_policy_reference",
    "profile_reference_id",
)

EXPECTED_OPTIONAL_DIAGNOSTIC_TEXT_FIELDS = (
    "agent_id",
    "route_id",
    "lease_id",
    "assignment_id",
    "attempt_id",
    "duration_reference",
)

EXPECTED_ALWAYS_REQUIRED_EVIDENCE_KINDS = (
    DiagnosticEvidenceKind.SAFE_ID,
    DiagnosticEvidenceKind.CAPABILITY_REFERENCE,
    DiagnosticEvidenceKind.REDACTED_REASON_CODE,
    DiagnosticEvidenceKind.TIMESTAMP_REFERENCE,
    DiagnosticEvidenceKind.EVIDENCE_REFERENCE,
)

EXPECTED_FORBIDDEN_FIELD_NAMES = {
    "payload",
    "body",
    "html",
    "json",
    "cookie",
    "cookies",
    "token",
    "tokens",
    "private_key",
    "profile_data",
    "account",
    "beacon",
    "listing_content",
    "runtime_sink",
    "database",
}


class TextLike(str):
    pass


class TupleLike(tuple):
    pass


class BoolLike(int):
    pass


class RouteFamilyLike(str, Enum):
    LINUX_REFERENCE_STYLE_ROUTE = "LINUX_REFERENCE_STYLE_ROUTE"


class RouteHealthStatusLike(str, Enum):
    READY = "READY"


class TransportOutcomeStatusLike(str, Enum):
    USABLE_RESPONSE_TRANSPORT_ONLY = "USABLE_RESPONSE_TRANSPORT_ONLY"


class SafeOperationalDiagnosticSubclass(SafeOperationalDiagnostic):
    pass


def _expected_evidence_kinds(
    *,
    duration_reference: str | None,
    attempt_count: int,
    profile_reference_id: str | None,
    fallback_policy_reference: str | None,
) -> tuple[DiagnosticEvidenceKind, ...]:
    kinds = [
        DiagnosticEvidenceKind.SAFE_ID,
        DiagnosticEvidenceKind.CAPABILITY_REFERENCE,
        DiagnosticEvidenceKind.REDACTED_REASON_CODE,
        DiagnosticEvidenceKind.TIMESTAMP_REFERENCE,
        DiagnosticEvidenceKind.EVIDENCE_REFERENCE,
    ]
    if duration_reference is not None:
        kinds.append(DiagnosticEvidenceKind.DURATION_REFERENCE)
    if attempt_count > 0:
        kinds.append(DiagnosticEvidenceKind.COUNT)
    if profile_reference_id is not None:
        kinds.append(DiagnosticEvidenceKind.PROFILE_REFERENCE)
    if fallback_policy_reference is not None:
        kinds.append(DiagnosticEvidenceKind.POLICY_REFERENCE)
    return tuple(kinds)


def _diagnostic_kwargs(
    *,
    diagnostic_id: str = EXPECTED_DIAGNOSTIC_ID,
    agent_id: str | None = None,
    route_id: str | None = EXPECTED_DIAGNOSTIC_ROUTE_ID,
    lease_id: str | None = None,
    assignment_id: str | None = None,
    attempt_id: str | None = None,
    outcome_status: TransportOutcomeStatus | None = None,
    reason_code: str = EXPECTED_REASON_CODES[0],
    timestamp_reference: str = EXPECTED_TIMESTAMP_REFERENCE,
    duration_reference: str | None = None,
    correlation_id: str = EXPECTED_CORRELATION_ID,
    causation_id: str = EXPECTED_CAUSATION_ID,
    evidence_reference_ids: tuple[str, ...] = EXPECTED_EVIDENCE_REFERENCE_IDS,
    attempt_count: int = 0,
    profile_reference_id: str | None = None,
    fallback_policy_reference: str | None = None,
) -> dict[str, Any]:
    return {
        "diagnostic_id": diagnostic_id,
        "agent_id": agent_id,
        "route_id": route_id,
        "lease_id": lease_id,
        "assignment_id": assignment_id,
        "attempt_id": attempt_id,
        "outcome_status": outcome_status,
        "reason_code": reason_code,
        "timestamp_reference": timestamp_reference,
        "duration_reference": duration_reference,
        "correlation_id": correlation_id,
        "causation_id": causation_id,
        "evidence_reference_ids": evidence_reference_ids,
        "evidence_kinds": _expected_evidence_kinds(
            duration_reference=duration_reference,
            attempt_count=attempt_count,
            profile_reference_id=profile_reference_id,
            fallback_policy_reference=fallback_policy_reference,
        ),
    }


def _make_diagnostic(**kwargs: Any) -> SafeOperationalDiagnostic:
    return SafeOperationalDiagnostic(**_diagnostic_kwargs(**kwargs))


def _make_boundary(
    *,
    diagnostic: SafeOperationalDiagnostic | None = None,
    boundary_id: str = EXPECTED_BOUNDARY_ID,
    authority: SafeEgressDiagnosticAuthority = SafeEgressDiagnosticAuthority.EGRESS_ROUTING_SERVER,
    route_family: RouteFamily = EXPECTED_ROUTE_FAMILY,
    route_id: str = EXPECTED_ROUTE_ID,
    capability_reference_id: str = EXPECTED_CAPABILITY_REFERENCE_ID,
    selection_decision_id: str | None = EXPECTED_SELECTION_DECISION_ID,
    fallback_policy_reference: str | None = None,
    route_health_status: RouteHealthStatus = EXPECTED_ROUTE_HEALTH_STATUS,
    fallback_attempted: bool = False,
    attempt_count: int = 0,
    profile_reference_id: str | None = None,
    safe_reference_only: bool = True,
    redacted_reason_required: bool = True,
    redacted_profile_reference_required: bool = True,
    raw_provider_payload_authorized: bool = False,
    full_html_or_json_authorized: bool = False,
    cookie_or_session_material_authorized: bool = False,
    proxy_credential_material_authorized: bool = False,
    private_key_material_authorized: bool = False,
    personal_browser_profile_data_authorized: bool = False,
    full_account_or_beacon_data_authorized: bool = False,
    raw_listing_content_authorized: bool = False,
    secret_logging_authorized: bool = False,
    durable_diagnostic_persistence_authorized: bool = False,
    runtime_log_emission_authorized: bool = False,
    provider_access_permission_inferred: bool = False,
    parser_success_inferred: bool = False,
    scan_success_inferred: bool = False,
    notification_delivery_inferred: bool = False,
    reason_codes: tuple[str, ...] = EXPECTED_REASON_CODES,
    evidence_reference_ids: tuple[str, ...] = EXPECTED_EVIDENCE_REFERENCE_IDS,
    diagnostic_id: str = EXPECTED_DIAGNOSTIC_ID,
    diagnostic_route_id: str | None = EXPECTED_DIAGNOSTIC_ROUTE_ID,
    diagnostic_reason_code: str = EXPECTED_REASON_CODES[0],
    diagnostic_evidence_reference_ids: tuple[str, ...] = EXPECTED_EVIDENCE_REFERENCE_IDS,
    diagnostic_outcome_status: TransportOutcomeStatus | None = None,
    diagnostic_duration_reference: str | None = None,
) -> SafeEgressDiagnosticGateBoundary:
    if diagnostic is None:
        diagnostic = _make_diagnostic(
            diagnostic_id=diagnostic_id,
            route_id=diagnostic_route_id,
            outcome_status=diagnostic_outcome_status,
            reason_code=diagnostic_reason_code,
            duration_reference=diagnostic_duration_reference,
            attempt_count=attempt_count,
            profile_reference_id=profile_reference_id,
            fallback_policy_reference=fallback_policy_reference,
            evidence_reference_ids=diagnostic_evidence_reference_ids,
        )
    return SafeEgressDiagnosticGateBoundary(
        boundary_id=boundary_id,
        authority=authority,
        diagnostic=diagnostic,
        route_family=route_family,
        route_id=route_id,
        capability_reference_id=capability_reference_id,
        selection_decision_id=selection_decision_id,
        fallback_policy_reference=fallback_policy_reference,
        route_health_status=route_health_status,
        fallback_attempted=fallback_attempted,
        attempt_count=attempt_count,
        profile_reference_id=profile_reference_id,
        safe_reference_only=safe_reference_only,
        redacted_reason_required=redacted_reason_required,
        redacted_profile_reference_required=redacted_profile_reference_required,
        raw_provider_payload_authorized=raw_provider_payload_authorized,
        full_html_or_json_authorized=full_html_or_json_authorized,
        cookie_or_session_material_authorized=cookie_or_session_material_authorized,
        proxy_credential_material_authorized=proxy_credential_material_authorized,
        private_key_material_authorized=private_key_material_authorized,
        personal_browser_profile_data_authorized=personal_browser_profile_data_authorized,
        full_account_or_beacon_data_authorized=full_account_or_beacon_data_authorized,
        raw_listing_content_authorized=raw_listing_content_authorized,
        secret_logging_authorized=secret_logging_authorized,
        durable_diagnostic_persistence_authorized=durable_diagnostic_persistence_authorized,
        runtime_log_emission_authorized=runtime_log_emission_authorized,
        provider_access_permission_inferred=provider_access_permission_inferred,
        parser_success_inferred=parser_success_inferred,
        scan_success_inferred=scan_success_inferred,
        notification_delivery_inferred=notification_delivery_inferred,
        reason_codes=reason_codes,
        evidence_reference_ids=evidence_reference_ids,
    )


_BOUNDARY_FACTORY: Any = _make_boundary


def _field_names(value: SafeEgressDiagnosticGateBoundary) -> tuple[str, ...]:
    return tuple(field.name for field in fields(value))


def test_exact_task_id_and_exports() -> None:
    assert ER12A_TASK_ID == "ER-12A-SAFE-OPERATIONAL-DIAGNOSTIC-GATE-20260716-049"
    assert safe_diagnostic_gate_module.__all__ == EXPECTED_MODULE_EXPORTS
    assert tuple(safe_diagnostic_gate_module.__all__) == EXPECTED_MODULE_EXPORTS
    assert len(set(safe_diagnostic_gate_module.__all__)) == len(EXPECTED_MODULE_EXPORTS)
    assert all(hasattr(safe_diagnostic_gate_module, name) for name in EXPECTED_MODULE_EXPORTS)
    start = egress_routing.__all__.index("ER08B_TASK_ID")
    assert egress_routing.__all__[start : start + len(EXPECTED_PACKAGE_EXPORT_SLICE)] == (
        EXPECTED_PACKAGE_EXPORT_SLICE
    )


def test_exact_field_count_and_order() -> None:
    boundary = _make_boundary()
    assert is_dataclass(boundary)
    assert len(fields(boundary)) == 32
    assert _field_names(boundary) == EXPECTED_FIELD_NAMES


def test_boundary_is_frozen_and_slots() -> None:
    boundary = _make_boundary()
    assert hasattr(type(boundary), "__slots__")
    assert not hasattr(boundary, "__dict__")
    boundary_any = cast(Any, boundary)
    with pytest.raises(FrozenInstanceError):
        boundary_any.boundary_id = "changed"


def test_exact_source_diagnostic_record_is_accepted_and_identity_is_preserved() -> None:
    diagnostic = _make_diagnostic()
    boundary = _make_boundary(diagnostic=diagnostic)
    assert boundary.diagnostic is diagnostic


def test_source_diagnostic_subclass_is_rejected() -> None:
    diagnostic = SafeOperationalDiagnosticSubclass(**_diagnostic_kwargs())
    with pytest.raises(ValueError):
        _make_boundary(diagnostic=diagnostic)


def test_source_diagnostic_duck_typing_is_rejected() -> None:
    diagnostic = SimpleNamespace(
        diagnostic_id=EXPECTED_DIAGNOSTIC_ID,
        agent_id=None,
        route_id=EXPECTED_ROUTE_ID,
        lease_id=None,
        assignment_id=None,
        attempt_id=None,
        outcome_status=None,
        reason_code=EXPECTED_REASON_CODES[0],
        timestamp_reference=EXPECTED_TIMESTAMP_REFERENCE,
        duration_reference=None,
        correlation_id=EXPECTED_CORRELATION_ID,
        causation_id=EXPECTED_CAUSATION_ID,
        evidence_reference_ids=EXPECTED_EVIDENCE_REFERENCE_IDS,
        evidence_kinds=_expected_evidence_kinds(
            duration_reference=None,
            attempt_count=0,
            profile_reference_id=None,
            fallback_policy_reference=None,
        ),
    )
    with pytest.raises(ValueError):
        _make_boundary(diagnostic=diagnostic)  # type: ignore[arg-type]


@pytest.mark.parametrize("route_family", tuple(RouteFamily))
def test_all_route_families_are_accepted(route_family: RouteFamily) -> None:
    boundary = _make_boundary(route_family=route_family)
    assert boundary.route_family is route_family


def test_route_family_lookalike_is_rejected() -> None:
    with pytest.raises(ValueError):
        _make_boundary(route_family=RouteFamilyLike.LINUX_REFERENCE_STYLE_ROUTE)  # type: ignore[arg-type]


@pytest.mark.parametrize("route_health_status", tuple(RouteHealthStatus))
def test_all_route_health_statuses_are_accepted(
    route_health_status: RouteHealthStatus,
) -> None:
    boundary = _make_boundary(route_health_status=route_health_status)
    assert boundary.route_health_status is route_health_status


def test_route_health_status_lookalike_is_rejected() -> None:
    with pytest.raises(ValueError):
        _make_boundary(
            route_health_status=RouteHealthStatusLike.READY,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "field_name, field_value",
    (
        ("boundary_id", TextLike(EXPECTED_BOUNDARY_ID)),
        ("route_id", TextLike(EXPECTED_ROUTE_ID)),
        ("capability_reference_id", TextLike(EXPECTED_CAPABILITY_REFERENCE_ID)),
        ("selection_decision_id", TextLike(EXPECTED_SELECTION_DECISION_ID)),
        ("fallback_policy_reference", TextLike(EXPECTED_FALLBACK_POLICY_REFERENCE)),
        ("profile_reference_id", TextLike(EXPECTED_PROFILE_REFERENCE_ID)),
    ),
)
def test_boundary_text_subclasses_are_rejected(field_name: str, field_value: str) -> None:
    kwargs: dict[str, Any] = {field_name: field_value}
    with pytest.raises(ValueError):
        _BOUNDARY_FACTORY(**kwargs)


@pytest.mark.parametrize(
    "field_name, field_value",
    (
        ("diagnostic_id", TextLike(EXPECTED_DIAGNOSTIC_ID)),
        ("agent_id", TextLike("agent-safe-01")),
        ("route_id", TextLike(EXPECTED_ROUTE_ID)),
        ("lease_id", TextLike("lease-safe-01")),
        ("assignment_id", TextLike("assignment-safe-01")),
        ("attempt_id", TextLike("attempt-safe-01")),
        ("reason_code", TextLike(EXPECTED_REASON_CODES[0])),
        ("timestamp_reference", TextLike(EXPECTED_TIMESTAMP_REFERENCE)),
        ("duration_reference", TextLike("duration-safe-01")),
        ("correlation_id", TextLike(EXPECTED_CORRELATION_ID)),
        ("causation_id", TextLike(EXPECTED_CAUSATION_ID)),
    ),
)
def test_diagnostic_text_subclasses_are_revalidated(
    field_name: str,
    field_value: str,
) -> None:
    diagnostic = _make_diagnostic()
    object.__setattr__(diagnostic, field_name, field_value)
    with pytest.raises(ValueError):
        _BOUNDARY_FACTORY(diagnostic=diagnostic)


@pytest.mark.parametrize(
    "field_name, field_value",
    (
        ("reason_codes", TupleLike((EXPECTED_REASON_CODES[0],))),
        ("evidence_reference_ids", TupleLike(EXPECTED_EVIDENCE_REFERENCE_IDS)),
        (
            "diagnostic_evidence_reference_ids",
            TupleLike(EXPECTED_EVIDENCE_REFERENCE_IDS),
        ),
        (
            "diagnostic_evidence_kinds",
            TupleLike(
                _expected_evidence_kinds(
                    duration_reference=None,
                    attempt_count=0,
                    profile_reference_id=None,
                    fallback_policy_reference=None,
                )
            ),
        ),
    ),
)
def test_tuple_subclasses_are_rejected(field_name: str, field_value: tuple[object, ...]) -> None:
    if field_name.startswith("diagnostic_"):
        diagnostic = _make_diagnostic()
        object.__setattr__(diagnostic, field_name.removeprefix("diagnostic_"), field_value)
        with pytest.raises(ValueError):
            _BOUNDARY_FACTORY(diagnostic=diagnostic)
        return
    with pytest.raises(ValueError):
        _BOUNDARY_FACTORY(**{field_name: field_value})


@pytest.mark.parametrize(
    "field_name",
    EXPECTED_TRUE_BOOLEAN_FIELDS,
)
def test_required_true_flags_reject_false(field_name: str) -> None:
    with pytest.raises(ValueError):
        _BOUNDARY_FACTORY(**{field_name: False})


@pytest.mark.parametrize(
    "field_name",
    EXPECTED_FALSE_BOOLEAN_FIELDS,
)
def test_required_false_flags_reject_true(field_name: str) -> None:
    with pytest.raises(ValueError):
        _BOUNDARY_FACTORY(**{field_name: True})


@pytest.mark.parametrize(
    "field_name",
    (
        "fallback_attempted",
        *EXPECTED_TRUE_BOOLEAN_FIELDS,
        *EXPECTED_FALSE_BOOLEAN_FIELDS,
    ),
)
def test_bool_lookalikes_are_rejected(field_name: str) -> None:
    with pytest.raises(ValueError):
        _BOUNDARY_FACTORY(**{field_name: BoolLike(1)})


def test_attempt_count_bool_is_rejected() -> None:
    with pytest.raises(ValueError):
        _make_boundary(attempt_count=True)  # type: ignore[arg-type]


def test_attempt_count_negative_is_rejected() -> None:
    with pytest.raises(ValueError):
        _make_boundary(attempt_count=-1)


@pytest.mark.parametrize("attempt_count", (0, 1, 3))
def test_zero_and_positive_attempt_counts_are_accepted(attempt_count: int) -> None:
    boundary = _make_boundary(
        attempt_count=attempt_count,
        diagnostic_duration_reference=None,
    )
    assert boundary.attempt_count == attempt_count


def test_required_route_id_linkage_is_enforced() -> None:
    with pytest.raises(ValueError):
        _make_boundary(route_id="route-safe-diagnostic-02")


def test_diagnostic_route_id_cannot_be_none() -> None:
    with pytest.raises(ValueError):
        _make_boundary(diagnostic_route_id=None)


def test_reason_and_evidence_linkage_are_enforced() -> None:
    with pytest.raises(ValueError):
        _make_boundary(
            reason_codes=("other-reason",),
            diagnostic_reason_code=EXPECTED_REASON_CODES[0],
        )
    with pytest.raises(ValueError):
        _make_boundary(
            evidence_reference_ids=("other-evidence",),
            diagnostic_evidence_reference_ids=EXPECTED_EVIDENCE_REFERENCE_IDS,
        )


def test_duplicate_reason_codes_are_rejected() -> None:
    diagnostic = _make_diagnostic()
    with pytest.raises(ValueError):
        SafeEgressDiagnosticGateBoundary(
            boundary_id=EXPECTED_BOUNDARY_ID,
            authority=SafeEgressDiagnosticAuthority.EGRESS_ROUTING_SERVER,
            diagnostic=diagnostic,
            route_family=EXPECTED_ROUTE_FAMILY,
            route_id=EXPECTED_ROUTE_ID,
            capability_reference_id=EXPECTED_CAPABILITY_REFERENCE_ID,
            selection_decision_id=EXPECTED_SELECTION_DECISION_ID,
            fallback_policy_reference=None,
            route_health_status=EXPECTED_ROUTE_HEALTH_STATUS,
            fallback_attempted=False,
            attempt_count=0,
            profile_reference_id=None,
            safe_reference_only=True,
            redacted_reason_required=True,
            redacted_profile_reference_required=True,
            raw_provider_payload_authorized=False,
            full_html_or_json_authorized=False,
            cookie_or_session_material_authorized=False,
            proxy_credential_material_authorized=False,
            private_key_material_authorized=False,
            personal_browser_profile_data_authorized=False,
            full_account_or_beacon_data_authorized=False,
            raw_listing_content_authorized=False,
            secret_logging_authorized=False,
            durable_diagnostic_persistence_authorized=False,
            runtime_log_emission_authorized=False,
            provider_access_permission_inferred=False,
            parser_success_inferred=False,
            scan_success_inferred=False,
            notification_delivery_inferred=False,
            reason_codes=(EXPECTED_REASON_CODES[0], EXPECTED_REASON_CODES[0]),
            evidence_reference_ids=EXPECTED_EVIDENCE_REFERENCE_IDS,
        )


def test_duplicate_evidence_reference_ids_are_rejected() -> None:
    with pytest.raises(ValueError):
        _make_boundary(
            evidence_reference_ids=(
                EXPECTED_EVIDENCE_REFERENCE_IDS[0],
                EXPECTED_EVIDENCE_REFERENCE_IDS[0],
            ),
            diagnostic_evidence_reference_ids=(
                EXPECTED_EVIDENCE_REFERENCE_IDS[0],
                EXPECTED_EVIDENCE_REFERENCE_IDS[0],
            ),
        )


def test_duplicate_evidence_kinds_are_rejected() -> None:
    diagnostic = _make_diagnostic(
        evidence_reference_ids=EXPECTED_EVIDENCE_REFERENCE_IDS,
    )
    object.__setattr__(
        diagnostic,
        "evidence_kinds",
        TupleLike(
            (
                DiagnosticEvidenceKind.SAFE_ID,
                DiagnosticEvidenceKind.SAFE_ID,
                DiagnosticEvidenceKind.CAPABILITY_REFERENCE,
                DiagnosticEvidenceKind.REDACTED_REASON_CODE,
                DiagnosticEvidenceKind.TIMESTAMP_REFERENCE,
                DiagnosticEvidenceKind.EVIDENCE_REFERENCE,
            )
        ),
    )
    with pytest.raises(ValueError):
        _make_boundary(diagnostic=diagnostic)


@pytest.mark.parametrize(
    "missing_kind",
    EXPECTED_ALWAYS_REQUIRED_EVIDENCE_KINDS,
)
def test_missing_required_evidence_kind_is_rejected(
    missing_kind: DiagnosticEvidenceKind,
) -> None:
    diagnostic = _make_diagnostic()
    kinds = tuple(kind for kind in _expected_evidence_kinds(
        duration_reference=None,
        attempt_count=0,
        profile_reference_id=None,
        fallback_policy_reference=None,
    ) if kind is not missing_kind)
    object.__setattr__(diagnostic, "evidence_kinds", kinds)
    with pytest.raises(ValueError):
        _make_boundary(diagnostic=diagnostic)


def test_extra_unlinked_evidence_kind_is_rejected() -> None:
    diagnostic = _make_diagnostic()
    object.__setattr__(
        diagnostic,
        "evidence_kinds",
        TupleLike(
            _expected_evidence_kinds(
                duration_reference=None,
                attempt_count=0,
                profile_reference_id=None,
                fallback_policy_reference=None,
            )
            + (DiagnosticEvidenceKind.SAFE_FINGERPRINT,)
        ),
    )
    with pytest.raises(ValueError):
        _make_boundary(diagnostic=diagnostic)


@pytest.mark.parametrize(
    "duration_reference, expected_kind",
    ((None, False), ("duration-safe-01", True)),
)
def test_duration_kind_matrix(
    duration_reference: str | None,
    expected_kind: bool,
) -> None:
    boundary = _make_boundary(
        diagnostic_duration_reference=duration_reference,
    )
    contains_kind = DiagnosticEvidenceKind.DURATION_REFERENCE in boundary.diagnostic.evidence_kinds
    assert contains_kind is expected_kind


@pytest.mark.parametrize(
    "attempt_count, expected_kind",
    ((0, False), (2, True)),
)
def test_count_kind_matrix(attempt_count: int, expected_kind: bool) -> None:
    boundary = _make_boundary(
        attempt_count=attempt_count,
        diagnostic_duration_reference=None,
    )
    contains_kind = DiagnosticEvidenceKind.COUNT in boundary.diagnostic.evidence_kinds
    assert contains_kind is expected_kind


@pytest.mark.parametrize(
    "profile_reference_id, expected_kind",
    ((None, False), (EXPECTED_PROFILE_REFERENCE_ID, True)),
)
def test_profile_kind_matrix(
    profile_reference_id: str | None,
    expected_kind: bool,
) -> None:
    boundary = _make_boundary(
        profile_reference_id=profile_reference_id,
        diagnostic_reason_code=EXPECTED_REASON_CODES[0],
        diagnostic_duration_reference=None,
    )
    contains_kind = DiagnosticEvidenceKind.PROFILE_REFERENCE in boundary.diagnostic.evidence_kinds
    assert contains_kind is expected_kind


@pytest.mark.parametrize(
    "fallback_policy_reference, expected_kind",
    ((None, False), (EXPECTED_FALLBACK_POLICY_REFERENCE, True)),
)
def test_policy_kind_matrix(
    fallback_policy_reference: str | None,
    expected_kind: bool,
) -> None:
    boundary = _make_boundary(
        fallback_policy_reference=fallback_policy_reference,
        diagnostic_duration_reference=None,
    )
    contains_kind = DiagnosticEvidenceKind.POLICY_REFERENCE in boundary.diagnostic.evidence_kinds
    assert contains_kind is expected_kind


def test_safe_fingerprint_is_blocked() -> None:
    diagnostic = _make_diagnostic()
    object.__setattr__(
        diagnostic,
        "evidence_kinds",
        TupleLike(
            _expected_evidence_kinds(
                duration_reference=None,
                attempt_count=0,
                profile_reference_id=None,
                fallback_policy_reference=None,
            )
            + (DiagnosticEvidenceKind.SAFE_FINGERPRINT,)
        ),
    )
    with pytest.raises(ValueError):
        _make_boundary(diagnostic=diagnostic)


def test_fallback_attempted_requires_policy_reference() -> None:
    with pytest.raises(ValueError):
        _make_boundary(fallback_attempted=True, fallback_policy_reference=None, attempt_count=1)


def test_fallback_attempted_requires_positive_count() -> None:
    with pytest.raises(ValueError):
        _make_boundary(
            fallback_attempted=True,
            fallback_policy_reference=EXPECTED_FALLBACK_POLICY_REFERENCE,
            attempt_count=0,
        )


def test_fallback_false_does_not_infer_authorization() -> None:
    boundary = _make_boundary(
        fallback_attempted=False,
        fallback_policy_reference=EXPECTED_FALLBACK_POLICY_REFERENCE,
        attempt_count=3,
    )
    assert boundary.fallback_attempted is False
    assert boundary.fallback_policy_reference == EXPECTED_FALLBACK_POLICY_REFERENCE
    assert boundary.attempt_count == 3


@pytest.mark.parametrize("outcome_status", (None, *tuple(TransportOutcomeStatus)))
def test_outcome_status_exact_enum_or_none(
    outcome_status: TransportOutcomeStatus | None,
) -> None:
    diagnostic = _make_diagnostic(outcome_status=outcome_status)
    boundary = _make_boundary(diagnostic=diagnostic)
    assert boundary.diagnostic.outcome_status is outcome_status


def test_outcome_status_lookalike_is_rejected() -> None:
    diagnostic = _make_diagnostic(outcome_status=None)
    object.__setattr__(
        diagnostic,
        "outcome_status",
        TransportOutcomeStatusLike.USABLE_RESPONSE_TRANSPORT_ONLY,  # type: ignore[assignment]
    )
    with pytest.raises(ValueError):
        _make_boundary(diagnostic=diagnostic)


def test_inputs_are_not_mutated() -> None:
    diagnostic = _make_diagnostic(
        profile_reference_id=EXPECTED_PROFILE_REFERENCE_ID,
        fallback_policy_reference=EXPECTED_FALLBACK_POLICY_REFERENCE,
        attempt_count=2,
        duration_reference="duration-safe-01",
    )
    before = tuple((field.name, getattr(diagnostic, field.name)) for field in fields(diagnostic))
    boundary = _make_boundary(
        diagnostic=diagnostic,
        profile_reference_id=EXPECTED_PROFILE_REFERENCE_ID,
        fallback_policy_reference=EXPECTED_FALLBACK_POLICY_REFERENCE,
        attempt_count=2,
        diagnostic_duration_reference="duration-safe-01",
    )
    after = tuple((field.name, getattr(diagnostic, field.name)) for field in fields(diagnostic))
    assert before == after
    assert boundary.diagnostic is diagnostic


def test_equality_and_hash_are_deterministic() -> None:
    left = _make_boundary()
    right = _make_boundary()
    assert left == right
    assert hash(left) == hash(right)


def test_schema_has_no_forbidden_runtime_or_secret_fields() -> None:
    field_names = {field.name for field in fields(SafeEgressDiagnosticGateBoundary)}
    assert field_names.isdisjoint(EXPECTED_FORBIDDEN_FIELD_NAMES)


def test_route_family_and_health_state_remain_diagnostic_facts() -> None:
    boundary = _make_boundary()
    assert boundary.route_family is EXPECTED_ROUTE_FAMILY
    assert boundary.route_health_status is EXPECTED_ROUTE_HEALTH_STATUS
    assert boundary.fallback_attempted is False

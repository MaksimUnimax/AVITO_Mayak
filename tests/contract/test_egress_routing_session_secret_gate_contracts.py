from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass
from enum import Enum
from types import SimpleNamespace
from typing import Any, cast

import pytest

import mayak.modules.egress_routing as egress_routing
import mayak.modules.egress_routing.session_secret_gate as session_secret_gate_module
from mayak.modules.egress_routing import (
    ER09A_TASK_ID,
    EgressSessionSecretAuthority,
    EgressSessionSecretGateBoundary,
    RouteCapability,
    RouteEvidenceStatus,
    SessionPolicyStatus,
)

EXPECTED_TASK_ID = "ER-09A-SESSION-SECRET-FAIL-CLOSED-BOUNDARY-20260716-044"

EXPECTED_MODULE_EXPORTS = (
    "ER09A_TASK_ID",
    "EgressSessionSecretAuthority",
    "EgressSessionSecretGateBoundary",
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

EXPECTED_FALSE_BOOLEAN_FIELDS = (
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

EXPECTED_TRUE_BOOLEAN_FIELDS = (
    "safe_reference_only",
    "rotation_required",
    "revocation_required",
    "redacted_diagnostics_required",
)

EXPECTED_REASON_CODES = ("safe-reference-only",)
EXPECTED_EVIDENCE_REFERENCE_IDS = ("SAFE-ER-OPAQUE-001", "SAFE-ER-OPAQUE-002")
EXPECTED_CAPABILITY_ID = "cap-session-secret-01"
EXPECTED_ROUTE_ID = "route-session-secret-01"


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
    session_policy_status: SessionPolicyStatus = SessionPolicyStatus.PROHIBITED,
    evidence_status: RouteEvidenceStatus = RouteEvidenceStatus.CURRENT,
    capability_id: str = EXPECTED_CAPABILITY_ID,
    route_id: str = EXPECTED_ROUTE_ID,
    destination_scope: tuple[str, ...] = ("opaque-reference",),
    operation_classes: tuple[str, ...] = ("egress-routing",),
    unsupported_classes: tuple[str, ...] = ("unselected",),
    evidence_reference_ids: tuple[str, ...] = EXPECTED_EVIDENCE_REFERENCE_IDS,
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
    return capability


def _build_boundary(
    *,
    capability: RouteCapability,
    boundary_id: str = "session-secret-gate-boundary-01",
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
        "reason_codes": EXPECTED_REASON_CODES,
        "evidence_reference_ids": capability.evidence_reference_ids,
    }
    kwargs.update(overrides)
    boundary = cast(Any, EgressSessionSecretGateBoundary)(**kwargs)
    assert type(boundary) is EgressSessionSecretGateBoundary
    return boundary


def test_module_exports_are_exact_and_ordered() -> None:
    assert ER09A_TASK_ID == EXPECTED_TASK_ID
    assert session_secret_gate_module.ER09A_TASK_ID == EXPECTED_TASK_ID
    assert type(session_secret_gate_module.__all__) is tuple
    assert session_secret_gate_module.__all__ == EXPECTED_MODULE_EXPORTS
    assert tuple(session_secret_gate_module.__all__) == EXPECTED_MODULE_EXPORTS
    assert len(session_secret_gate_module.__all__) == len(set(session_secret_gate_module.__all__))
    assert all(hasattr(session_secret_gate_module, name) for name in EXPECTED_MODULE_EXPORTS)


@pytest.mark.parametrize(
    "session_policy_status",
    [
        SessionPolicyStatus.PROHIBITED,
        SessionPolicyStatus.BLOCKED_PENDING_ISOLATED_PROJECT_SESSION_GATE,
    ],
)
def test_two_allowed_session_policy_statuses_are_accepted(
    session_policy_status: SessionPolicyStatus,
) -> None:
    capability = _build_capability(session_policy_status=session_policy_status)
    boundary = _build_boundary(capability=capability, session_policy_status=session_policy_status)

    assert is_dataclass(boundary) is True
    assert type(boundary) is EgressSessionSecretGateBoundary
    assert boundary.authority is EgressSessionSecretAuthority.EGRESS_ROUTING_SERVER
    assert boundary.route_id == capability.route_id
    assert boundary.session_policy_status is session_policy_status
    assert boundary.evidence_reference_ids == capability.evidence_reference_ids
    assert boundary.route_capability is capability
    assert type(boundary.route_capability) is RouteCapability
    assert tuple(field.name for field in fields(boundary)) == EXPECTED_FIELD_NAMES
    assert type(boundary).__slots__ == EXPECTED_FIELD_NAMES


def test_approved_reference_only_is_rejected() -> None:
    capability = _build_capability(
        session_policy_status=SessionPolicyStatus.APPROVED_REFERENCE_ONLY
    )

    with pytest.raises(ValueError, match="isolated project session gate not open in current scope"):
        _build_boundary(
            capability=capability,
            session_policy_status=SessionPolicyStatus.APPROVED_REFERENCE_ONLY,
        )


def test_status_mismatch_between_boundary_and_source_capability_is_rejected() -> None:
    capability = _build_capability(session_policy_status=SessionPolicyStatus.PROHIBITED)

    with pytest.raises(
        ValueError,
        match="session_policy_status must match route_capability\\.session_policy_status",
    ):
        _build_boundary(
            capability=capability,
            session_policy_status=SessionPolicyStatus.BLOCKED_PENDING_ISOLATED_PROJECT_SESSION_GATE,
        )


def test_route_id_mismatch_is_rejected() -> None:
    capability = _build_capability()

    with pytest.raises(ValueError, match="route_id must match route_capability\\.route_id"):
        _build_boundary(capability=capability, route_id="route-session-secret-02")


def test_wrong_authority_is_rejected() -> None:
    capability = _build_capability()

    class ForeignAuthority(str, Enum):
        EGRESS_ROUTING_SERVER = "EGRESS_ROUTING_SERVER"

    with pytest.raises(
        ValueError,
        match="authority must be EgressSessionSecretAuthority",
    ):
        _build_boundary(
            capability=capability,
            authority=cast(Any, ForeignAuthority.EGRESS_ROUTING_SERVER),
        )


def test_source_capability_exact_record_is_required() -> None:
    capability = _build_capability()

    class CapabilitySubclass(RouteCapability):
        pass

    subclass_capability = CapabilitySubclass(
        capability_id=EXPECTED_CAPABILITY_ID,
        route_id=EXPECTED_ROUTE_ID,
        destination_scope=("opaque-reference",),
        operation_classes=("egress-routing",),
        unsupported_classes=("unselected",),
        evidence_reference_ids=EXPECTED_EVIDENCE_REFERENCE_IDS,
        evidence_status=RouteEvidenceStatus.CURRENT,
        session_policy_status=SessionPolicyStatus.PROHIBITED,
    )
    foreign_capability = SimpleNamespace(
        capability_id=EXPECTED_CAPABILITY_ID,
        route_id=EXPECTED_ROUTE_ID,
        destination_scope=("opaque-reference",),
        operation_classes=("egress-routing",),
        unsupported_classes=("unselected",),
        evidence_reference_ids=EXPECTED_EVIDENCE_REFERENCE_IDS,
        evidence_status=RouteEvidenceStatus.CURRENT,
        session_policy_status=SessionPolicyStatus.PROHIBITED,
    )

    with pytest.raises(ValueError, match="route_capability must be RouteCapability"):
        _build_boundary(capability=subclass_capability)
    with pytest.raises(ValueError, match="route_capability must be RouteCapability"):
        _build_boundary(capability=cast(RouteCapability, foreign_capability))

    assert capability == _build_capability()


@pytest.mark.parametrize(
    ("mutator", "expected_message"),
    [
        (
            lambda capability: _mutate(
                capability,
                evidence_status=SimpleNamespace(name="CURRENT", value="CURRENT"),
            ),
            "route_capability\\.evidence_status must be RouteEvidenceStatus",
        ),
        (
            lambda capability: _mutate(
                capability,
                session_policy_status=SimpleNamespace(name="PROHIBITED", value="PROHIBITED"),
            ),
            "route_capability\\.session_policy_status must be SessionPolicyStatus",
        ),
    ],
)
def test_enum_lookalikes_are_rejected(mutator: Any, expected_message: str) -> None:
    capability = _build_capability()
    mutator(capability)

    with pytest.raises(ValueError, match=expected_message):
        _build_boundary(capability=capability)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("boundary_id", TextLike("boundary-session-secret-01")),
        ("route_id", TextLike(EXPECTED_ROUTE_ID)),
    ],
)
def test_text_subclasses_on_boundary_fields_are_rejected(field_name: str, value: str) -> None:
    capability = _build_capability()
    kwargs: dict[str, object] = {
        "capability": capability,
        "boundary_id": "session-secret-gate-boundary-01",
        "route_id": EXPECTED_ROUTE_ID,
    }
    kwargs[field_name] = value

    with pytest.raises(ValueError, match=f"{field_name} must be a non-blank string"):
        cast(Any, _build_boundary)(**kwargs)


@pytest.mark.parametrize(
    ("mutator", "expected_message"),
    [
        (
            lambda capability: _mutate(capability, capability_id=TextLike(EXPECTED_CAPABILITY_ID)),
            "route_capability\\.capability_id must be a non-blank string",
        ),
        (
            lambda capability: _mutate(capability, route_id=TextLike(EXPECTED_ROUTE_ID)),
            "route_capability\\.route_id must be a non-blank string",
        ),
        (
            lambda capability: _mutate(
                capability,
                destination_scope=TupleLike(("opaque-reference",)),
            ),
            "route_capability\\.destination_scope must be a tuple",
        ),
        (
            lambda capability: _mutate(
                capability,
                operation_classes=TupleLike(("egress-routing",)),
            ),
            "route_capability\\.operation_classes must be a tuple",
        ),
        (
            lambda capability: _mutate(
                capability,
                unsupported_classes=TupleLike(("unselected",)),
            ),
            "route_capability\\.unsupported_classes must be a tuple",
        ),
        (
            lambda capability: _mutate(
                capability,
                evidence_reference_ids=TupleLike(EXPECTED_EVIDENCE_REFERENCE_IDS),
            ),
            "route_capability\\.evidence_reference_ids must be a tuple",
        ),
    ],
)
def test_source_capability_text_and_tuple_subclasses_are_rejected(
    mutator: Any,
    expected_message: str,
) -> None:
    capability = _build_capability()
    mutator(capability)

    with pytest.raises(ValueError, match=expected_message):
        _build_boundary(capability=capability)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("boundary_id", " "),
        ("route_id", ""),
        ("route_id", "   "),
    ],
)
def test_blank_ids_are_rejected(field_name: str, value: str) -> None:
    capability = _build_capability()
    kwargs: dict[str, object] = {
        "capability": capability,
        "boundary_id": "session-secret-gate-boundary-01",
        "route_id": EXPECTED_ROUTE_ID,
    }
    kwargs[field_name] = value

    with pytest.raises(ValueError, match=f"{field_name} must be a non-blank string"):
        cast(Any, _build_boundary)(**kwargs)


@pytest.mark.parametrize("field_name", EXPECTED_FALSE_BOOLEAN_FIELDS + EXPECTED_TRUE_BOOLEAN_FIELDS)
def test_bool_lookalikes_are_rejected(field_name: str) -> None:
    capability = _build_capability()
    boundary = _build_boundary(capability=capability)
    expected_value = getattr(boundary, field_name)
    lookalike = BoolLike(1 if expected_value is True else 0)
    kwargs = {
        "capability": capability,
        "boundary_id": boundary.boundary_id,
        "authority": boundary.authority,
        "route_id": boundary.route_id,
        "session_policy_status": boundary.session_policy_status,
        "isolated_project_session_gate_satisfied": boundary.isolated_project_session_gate_satisfied,
        "project_owned_session_authorized": boundary.project_owned_session_authorized,
        "project_owned_cookie_profile_authorized": (
            boundary.project_owned_cookie_profile_authorized
        ),
        "personal_browser_profile_access_authorized": (
            boundary.personal_browser_profile_access_authorized
        ),
        "browser_password_access_authorized": boundary.browser_password_access_authorized,
        "owner_private_session_default_authorized": (
            boundary.owner_private_session_default_authorized
        ),
        "foreign_or_unrelated_cookie_reuse_authorized": (
            boundary.foreign_or_unrelated_cookie_reuse_authorized
        ),
        "raw_cookie_material_authorized": boundary.raw_cookie_material_authorized,
        "raw_session_token_material_authorized": boundary.raw_session_token_material_authorized,
        "raw_credential_material_authorized": boundary.raw_credential_material_authorized,
        "safe_reference_only": boundary.safe_reference_only,
        "rotation_required": boundary.rotation_required,
        "revocation_required": boundary.revocation_required,
        "redacted_diagnostics_required": boundary.redacted_diagnostics_required,
        "secret_logging_authorized": boundary.secret_logging_authorized,
        "secret_report_authorized": boundary.secret_report_authorized,
        "secret_git_storage_authorized": boundary.secret_git_storage_authorized,
        "runtime_session_creation_authorized": boundary.runtime_session_creation_authorized,
        "provider_access_permission_inferred": boundary.provider_access_permission_inferred,
        "parser_success_inferred": boundary.parser_success_inferred,
        "scan_success_inferred": boundary.scan_success_inferred,
        "notification_delivery_inferred": boundary.notification_delivery_inferred,
        "reason_codes": boundary.reason_codes,
        "evidence_reference_ids": boundary.evidence_reference_ids,
    }
    kwargs[field_name] = lookalike

    with pytest.raises(ValueError, match=f"{field_name} must be a bool"):
        cast(Any, _build_boundary)(**kwargs)


def test_boundary_is_frozen_slots_dataclass_with_exact_field_order() -> None:
    boundary = _build_boundary(capability=_build_capability())

    assert is_dataclass(boundary) is True
    assert type(boundary) is EgressSessionSecretGateBoundary
    assert type(boundary).__slots__ == EXPECTED_FIELD_NAMES
    assert tuple(field.name for field in fields(boundary)) == EXPECTED_FIELD_NAMES
    assert boundary.__slots__ == EXPECTED_FIELD_NAMES
    assert not hasattr(boundary, "__dict__")

    with pytest.raises(FrozenInstanceError):
        boundary.boundary_id = "mutation-blocked"  # type: ignore[misc]


def test_boundary_source_capability_is_public_frozen_exact_and_deterministic() -> None:
    capability = _build_capability()
    before = _snapshot(capability)
    first = _build_boundary(capability=capability)
    alternate_capability = _build_capability(
        capability_id="cap-session-secret-02",
    )
    alternate_boundary = _build_boundary(capability=alternate_capability)
    after = _snapshot(capability)
    second = _build_boundary(capability=capability)

    assert before == after
    assert first == second
    assert first != alternate_boundary
    assert hash(first) == hash(second)
    assert first is not second
    assert first.route_capability is capability
    assert type(first.route_capability) is RouteCapability
    assert "route_capability=" in repr(first)
    assert first != alternate_boundary
    with pytest.raises(FrozenInstanceError):
        first.route_capability = alternate_capability  # type: ignore[misc]
    assert _snapshot(capability) == before


def test_boundary_schema_excludes_raw_secret_fields() -> None:
    boundary = _build_boundary(capability=_build_capability())
    field_names = tuple(field.name for field in fields(boundary))

    assert field_names == EXPECTED_FIELD_NAMES
    assert "route_capability" in field_names
    assert {
        "cookie",
        "cookies",
        "session",
        "sessions",
        "token",
        "private_key",
        "secret_value",
        "browser_profile_path",
        "filesystem_path",
        "provider_endpoint",
        "storage_location",
    }.isdisjoint(field_names)


def test_boundary_expected_boolean_matrix_is_exact() -> None:
    boundary = _build_boundary(capability=_build_capability())

    for field_name in EXPECTED_FALSE_BOOLEAN_FIELDS:
        value = getattr(boundary, field_name)
        assert type(value) is bool
        assert value is False

    for field_name in EXPECTED_TRUE_BOOLEAN_FIELDS:
        value = getattr(boundary, field_name)
        assert type(value) is bool
        assert value is True

    assert boundary.safe_reference_only is True
    assert boundary.rotation_required is True
    assert boundary.revocation_required is True
    assert boundary.redacted_diagnostics_required is True


def test_package_exports_include_er09a_in_expected_position() -> None:
    exports = tuple(egress_routing.__all__)
    start = exports.index("ER08B_TASK_ID")

    assert (
        exports[start : start + len(EXPECTED_PACKAGE_EXPORT_SLICE)]
        == EXPECTED_PACKAGE_EXPORT_SLICE
    )
    assert hasattr(egress_routing, "ER09A_TASK_ID")
    assert hasattr(egress_routing, "EgressSessionSecretAuthority")
    assert hasattr(egress_routing, "EgressSessionSecretGateBoundary")

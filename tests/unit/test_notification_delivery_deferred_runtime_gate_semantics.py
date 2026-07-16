from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from mayak.modules import notification_delivery
from mayak.modules.egress_routing import (
    persistence_runtime_gate as egress_persistence_runtime_gate,
)
from mayak.modules.notification_delivery.deferred_runtime_gate import (
    ND14_TASK_ID,
    NotificationDeferredRuntimeAuthority,
    NotificationDeferredRuntimeCapability,
    NotificationDeferredRuntimeGateBoundary,
    NotificationDeferredRuntimeGateStatus,
    NotificationDeferredRuntimeRequirement,
    NotificationPreRuntimeAllowedWork,
    build_notification_deferred_runtime_gate,
)

BOUNDARY_ID = "nd14-deferred-runtime-boundary-1"
EVIDENCE_IDS = ("evidence-1", "evidence-2")

EXPECTED_REQUIRED_GATE_CLASSES = (
    NotificationDeferredRuntimeRequirement.PHYSICAL_SCHEMA_AND_MIGRATIONS,
    NotificationDeferredRuntimeRequirement.QUEUE_WORKER_BROKER,
    NotificationDeferredRuntimeRequirement.PROVIDER_ADAPTER_PLAYBOOKS,
    NotificationDeferredRuntimeRequirement.PROVIDER_CREDENTIALS_POLICY,
    NotificationDeferredRuntimeRequirement.RETRY_RATE_TIME_POLICY,
    NotificationDeferredRuntimeRequirement.OPERATIONS_DEPLOY_RUNTIME_TOPOLOGY,
    NotificationDeferredRuntimeRequirement.EXACT_IMPLEMENTATION_TASK,
)

EXPECTED_ALLOWED_PRE_RUNTIME_WORK = (
    NotificationPreRuntimeAllowedWork.SEMANTIC_CONTRACTS,
    NotificationPreRuntimeAllowedWork.SYNTHETIC_DETERMINISTIC_FAKES,
    NotificationPreRuntimeAllowedWork.ARCHITECTURE_STATIC_CHECKS,
    NotificationPreRuntimeAllowedWork.DOCS_ONLY_DECISIONS,
    NotificationPreRuntimeAllowedWork.EVIDENCE_HANDOFF,
)

EXPECTED_BLOCKED_RUNTIME_CAPABILITIES = (
    NotificationDeferredRuntimeCapability.POSTGRESQL_TABLES,
    NotificationDeferredRuntimeCapability.SQLALCHEMY_MODELS,
    NotificationDeferredRuntimeCapability.PSYCOPG_USAGE,
    NotificationDeferredRuntimeCapability.ALEMBIC_MIGRATIONS,
    NotificationDeferredRuntimeCapability.QUEUE,
    NotificationDeferredRuntimeCapability.WORKER,
    NotificationDeferredRuntimeCapability.BROKER_OR_CACHE,
    NotificationDeferredRuntimeCapability.SCHEDULER_OR_POLLING,
    NotificationDeferredRuntimeCapability.TELEGRAM_PROVIDER_ADAPTER,
    NotificationDeferredRuntimeCapability.MAX_PROVIDER_ADAPTER,
    NotificationDeferredRuntimeCapability.WEB_PUSH_DELIVERY,
    NotificationDeferredRuntimeCapability.WEBHOOK,
    NotificationDeferredRuntimeCapability.MINI_APP,
    NotificationDeferredRuntimeCapability.PROVIDER_API_CALLS,
    NotificationDeferredRuntimeCapability.MESSAGE_TEMPLATES,
    NotificationDeferredRuntimeCapability.PROVIDER_CREDENTIALS,
    NotificationDeferredRuntimeCapability.PROVIDER_RETRY_OR_BACKOFF,
    NotificationDeferredRuntimeCapability.PROVIDER_RATE_LIMITS,
    NotificationDeferredRuntimeCapability.QUIET_HOURS,
    NotificationDeferredRuntimeCapability.DIGEST_OR_TIME_BATCHING,
    NotificationDeferredRuntimeCapability.RETENTION_TOOLING,
    NotificationDeferredRuntimeCapability.RUNTIME_SERVICES,
    NotificationDeferredRuntimeCapability.DOCKER_CICD_DEPLOY,
    NotificationDeferredRuntimeCapability.LIVE_DELIVERY,
)

EXPECTED_REASON_CODES = (
    "notification-runtime-implementation-blocked",
    "required-decisions-unsatisfied",
    "exact-implementation-task-required",
    "semantic-only-work-allowed",
    "od-013-remains-open",
)


def _build_boundary(
    *,
    boundary_id: str = BOUNDARY_ID,
    evidence_reference_ids: tuple[str, ...] = EVIDENCE_IDS,
    authority: NotificationDeferredRuntimeAuthority = (
        NotificationDeferredRuntimeAuthority.NOTIFICATION_DELIVERY_SERVER
    ),
    status: NotificationDeferredRuntimeGateStatus = (
        NotificationDeferredRuntimeGateStatus.BLOCKED_PENDING_EXPLICIT_GATES
    ),
    required_gate_classes: tuple[
        NotificationDeferredRuntimeRequirement, ...
    ] = EXPECTED_REQUIRED_GATE_CLASSES,
    satisfied_gate_classes: tuple[NotificationDeferredRuntimeRequirement, ...] = (),
    allowed_pre_runtime_work: tuple[
        NotificationPreRuntimeAllowedWork, ...
    ] = EXPECTED_ALLOWED_PRE_RUNTIME_WORK,
    blocked_runtime_capabilities: tuple[
        NotificationDeferredRuntimeCapability, ...
    ] = EXPECTED_BLOCKED_RUNTIME_CAPABILITIES,
    runtime_execution_authorized: bool = False,
    persistence_implementation_authorized: bool = False,
    provider_adapter_implementation_authorized: bool = False,
    production_readiness_inferred: bool = False,
    provider_permission_inferred: bool = False,
    retention_policy_resolved: bool = False,
    od013_closed: bool = False,
    reason_codes: tuple[str, ...] = EXPECTED_REASON_CODES,
) -> NotificationDeferredRuntimeGateBoundary:
    return NotificationDeferredRuntimeGateBoundary(
        boundary_id=boundary_id,
        authority=authority,
        status=status,
        required_gate_classes=required_gate_classes,
        satisfied_gate_classes=satisfied_gate_classes,
        allowed_pre_runtime_work=allowed_pre_runtime_work,
        blocked_runtime_capabilities=blocked_runtime_capabilities,
        runtime_execution_authorized=runtime_execution_authorized,
        persistence_implementation_authorized=persistence_implementation_authorized,
        provider_adapter_implementation_authorized=provider_adapter_implementation_authorized,
        production_readiness_inferred=production_readiness_inferred,
        provider_permission_inferred=provider_permission_inferred,
        retention_policy_resolved=retention_policy_resolved,
        od013_closed=od013_closed,
        reason_codes=reason_codes,
        evidence_reference_ids=evidence_reference_ids,
    )


def test_canonical_boundary_creation_is_deterministic_and_fail_closed() -> None:
    boundary = build_notification_deferred_runtime_gate(
        boundary_id=BOUNDARY_ID,
        evidence_reference_ids=EVIDENCE_IDS,
    )

    assert boundary == build_notification_deferred_runtime_gate(
        boundary_id=BOUNDARY_ID,
        evidence_reference_ids=EVIDENCE_IDS,
    )
    assert boundary.boundary_id == BOUNDARY_ID
    assert boundary.authority is NotificationDeferredRuntimeAuthority.NOTIFICATION_DELIVERY_SERVER
    assert boundary.status is NotificationDeferredRuntimeGateStatus.BLOCKED_PENDING_EXPLICIT_GATES
    assert boundary.required_gate_classes == EXPECTED_REQUIRED_GATE_CLASSES
    assert boundary.satisfied_gate_classes == ()
    assert boundary.allowed_pre_runtime_work == EXPECTED_ALLOWED_PRE_RUNTIME_WORK
    assert boundary.blocked_runtime_capabilities == EXPECTED_BLOCKED_RUNTIME_CAPABILITIES
    assert boundary.runtime_execution_authorized is False
    assert boundary.persistence_implementation_authorized is False
    assert boundary.provider_adapter_implementation_authorized is False
    assert boundary.production_readiness_inferred is False
    assert boundary.provider_permission_inferred is False
    assert boundary.retention_policy_resolved is False
    assert boundary.od013_closed is False
    assert boundary.reason_codes == EXPECTED_REASON_CODES
    assert boundary.evidence_reference_ids == EVIDENCE_IDS


def test_dataclass_is_frozen_and_tuple_fields_are_immutable() -> None:
    boundary = _build_boundary()

    with pytest.raises(FrozenInstanceError):
        boundary.boundary_id = "changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        boundary.required_gate_classes[0] = (
            NotificationDeferredRuntimeRequirement.EXACT_IMPLEMENTATION_TASK
        )  # type: ignore[index]
    with pytest.raises(TypeError):
        boundary.allowed_pre_runtime_work[0] = NotificationPreRuntimeAllowedWork.DOCS_ONLY_DECISIONS  # type: ignore[index]


@pytest.mark.parametrize(
    "field_name, value",
    (
        ("authority", NotificationDeferredRuntimeAuthority.NOTIFICATION_DELIVERY_SERVER.value),
        ("status", NotificationDeferredRuntimeGateStatus.BLOCKED_PENDING_EXPLICIT_GATES.value),
        ("runtime_execution_authorized", True),
        ("persistence_implementation_authorized", True),
        ("provider_adapter_implementation_authorized", True),
        ("production_readiness_inferred", True),
        ("provider_permission_inferred", True),
        ("retention_policy_resolved", True),
        ("od013_closed", True),
    ),
)
def test_wrong_authority_status_and_true_flags_are_rejected(field_name: str, value: object) -> None:
    kwargs: dict[str, object] = {
        "boundary_id": BOUNDARY_ID,
        "evidence_reference_ids": EVIDENCE_IDS,
    }
    kwargs[field_name] = value
    with pytest.raises(ValueError):
        _build_boundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "field_name, value",
    (
        ("authority", NotificationDeferredRuntimeAuthority.NOTIFICATION_DELIVERY_SERVER.value),
        ("status", NotificationDeferredRuntimeGateStatus.BLOCKED_PENDING_EXPLICIT_GATES.value),
    ),
)
def test_exact_enum_instances_are_required(field_name: str, value: object) -> None:
    kwargs: dict[str, object] = {
        "boundary_id": BOUNDARY_ID,
        "evidence_reference_ids": EVIDENCE_IDS,
    }
    kwargs[field_name] = value
    with pytest.raises(ValueError):
        _build_boundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "required_gate_classes",
    (
        (),
        EXPECTED_REQUIRED_GATE_CLASSES[:-1],
        EXPECTED_REQUIRED_GATE_CLASSES
        + (NotificationDeferredRuntimeRequirement.EXACT_IMPLEMENTATION_TASK,),
        tuple(reversed(EXPECTED_REQUIRED_GATE_CLASSES)),
    ),
)
def test_required_gate_classes_must_match_canonical_tuple(
    required_gate_classes: tuple[NotificationDeferredRuntimeRequirement, ...],
) -> None:
    with pytest.raises(ValueError):
        _build_boundary(required_gate_classes=required_gate_classes)


def test_non_empty_satisfied_gate_classes_are_rejected() -> None:
    with pytest.raises(ValueError):
        _build_boundary(
            satisfied_gate_classes=(
                NotificationDeferredRuntimeRequirement.EXACT_IMPLEMENTATION_TASK,
            ),
        )


@pytest.mark.parametrize(
    "allowed_pre_runtime_work",
    (
        (),
        EXPECTED_ALLOWED_PRE_RUNTIME_WORK[:-1],
        EXPECTED_ALLOWED_PRE_RUNTIME_WORK + (NotificationPreRuntimeAllowedWork.SEMANTIC_CONTRACTS,),
        tuple(reversed(EXPECTED_ALLOWED_PRE_RUNTIME_WORK)),
    ),
)
def test_allowed_pre_runtime_work_must_match_canonical_tuple(
    allowed_pre_runtime_work: tuple[NotificationPreRuntimeAllowedWork, ...],
) -> None:
    with pytest.raises(ValueError):
        _build_boundary(allowed_pre_runtime_work=allowed_pre_runtime_work)


@pytest.mark.parametrize(
    "blocked_runtime_capabilities",
    (
        (),
        EXPECTED_BLOCKED_RUNTIME_CAPABILITIES[:-1],
        EXPECTED_BLOCKED_RUNTIME_CAPABILITIES
        + (NotificationDeferredRuntimeCapability.LIVE_DELIVERY,),
        tuple(reversed(EXPECTED_BLOCKED_RUNTIME_CAPABILITIES)),
    ),
)
def test_blocked_runtime_capabilities_must_match_canonical_tuple(
    blocked_runtime_capabilities: tuple[NotificationDeferredRuntimeCapability, ...],
) -> None:
    with pytest.raises(ValueError):
        _build_boundary(blocked_runtime_capabilities=blocked_runtime_capabilities)


@pytest.mark.parametrize(
    "field_name",
    (
        "runtime_execution_authorized",
        "persistence_implementation_authorized",
        "provider_adapter_implementation_authorized",
        "production_readiness_inferred",
        "provider_permission_inferred",
        "retention_policy_resolved",
        "od013_closed",
    ),
)
def test_any_true_authorization_or_inference_flag_is_rejected(field_name: str) -> None:
    kwargs = {
        "runtime_execution_authorized": False,
        "persistence_implementation_authorized": False,
        "provider_adapter_implementation_authorized": False,
        "production_readiness_inferred": False,
        "provider_permission_inferred": False,
        "retention_policy_resolved": False,
        "od013_closed": False,
    }
    kwargs[field_name] = True
    with pytest.raises(ValueError):
        _build_boundary(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "reason_codes",
    (
        (),
        EXPECTED_REASON_CODES[:-1],
        EXPECTED_REASON_CODES + ("unexpected-reason",),
        tuple(reversed(EXPECTED_REASON_CODES)),
    ),
)
def test_reason_codes_must_match_canonical_tuple(reason_codes: tuple[str, ...]) -> None:
    with pytest.raises(ValueError):
        _build_boundary(reason_codes=reason_codes)


@pytest.mark.parametrize(
    "evidence_reference_ids",
    (
        (),
        ("evidence-1", "evidence-1"),
        (" ",),
        ("https://example.com",),
        ("provider-cookie",),
        ("provider-token",),
        ("provider-secret",),
        ("provider-credential",),
        ("private key reference",),
        ("session-reference",),
        ("one-time code reference",),
    ),
)
def test_evidence_reference_validation_is_safe_and_deterministic(
    evidence_reference_ids: tuple[str, ...],
) -> None:
    with pytest.raises(ValueError):
        _build_boundary(evidence_reference_ids=evidence_reference_ids)


def test_safe_evidence_ids_are_preserved_in_order() -> None:
    evidence_reference_ids = ("safe-ref-1", "safe-ref-2", "safe-ref-3")
    boundary = _build_boundary(evidence_reference_ids=evidence_reference_ids)
    assert boundary.evidence_reference_ids == evidence_reference_ids


def test_builder_signature_is_keyword_only_and_rejects_unexpected_runtime_arguments() -> None:
    with pytest.raises(TypeError):
        build_notification_deferred_runtime_gate("boundary-1", EVIDENCE_IDS)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        build_notification_deferred_runtime_gate(
            boundary_id=BOUNDARY_ID,
            evidence_reference_ids=EVIDENCE_IDS,
            runtime_execution_authorized=True,  # type: ignore[call-arg]
        )
    with pytest.raises(TypeError):
        build_notification_deferred_runtime_gate(
            boundary_id=BOUNDARY_ID,
            evidence_reference_ids=EVIDENCE_IDS,
            enable_runtime=True,  # type: ignore[call-arg]
        )
    with pytest.raises(TypeError):
        build_notification_deferred_runtime_gate(
            boundary_id=BOUNDARY_ID,
            evidence_reference_ids=EVIDENCE_IDS,
            unlock=True,  # type: ignore[call-arg]
        )


def test_repeated_builder_calls_are_deterministic() -> None:
    first = build_notification_deferred_runtime_gate(
        boundary_id=BOUNDARY_ID,
        evidence_reference_ids=EVIDENCE_IDS,
    )
    second = build_notification_deferred_runtime_gate(
        boundary_id=BOUNDARY_ID,
        evidence_reference_ids=EVIDENCE_IDS,
    )
    assert first == second
    assert first is not second


def test_package_import_has_no_effect_on_blocked_state() -> None:
    boundary_before = build_notification_deferred_runtime_gate(
        boundary_id=BOUNDARY_ID,
        evidence_reference_ids=EVIDENCE_IDS,
    )
    imported_package = notification_delivery
    assert imported_package.ND14_TASK_ID is ND14_TASK_ID
    boundary_after = build_notification_deferred_runtime_gate(
        boundary_id=BOUNDARY_ID,
        evidence_reference_ids=EVIDENCE_IDS,
    )
    assert boundary_before == boundary_after


def test_nd13_and_egress_existence_do_not_open_the_boundary() -> None:
    boundary = build_notification_deferred_runtime_gate(
        boundary_id=BOUNDARY_ID,
        evidence_reference_ids=EVIDENCE_IDS,
    )
    source = Path("src/mayak/modules/notification_delivery/deferred_runtime_gate.py").read_text()
    assert "egress_routing" not in source.lower()
    assert (
        notification_delivery.ND13_TASK_ID
        == "MAYAK-ND-13-SECURITY-PRIVACY-SUPPRESSION-20260716-008"
    )

    assert egress_persistence_runtime_gate is not None
    assert boundary.status is NotificationDeferredRuntimeGateStatus.BLOCKED_PENDING_EXPLICIT_GATES
    assert boundary.runtime_execution_authorized is False
    assert boundary.persistence_implementation_authorized is False
    assert boundary.provider_adapter_implementation_authorized is False

from __future__ import annotations

# ruff: noqa: E501
from uuid import uuid4

import pytest

from mayak.contracts import ContractMetadata
from mayak.modules.telegram_adapter.contracts import (
    TelegramPreGateAllowedSurface,
    TelegramRuntimeBoundaryOutcome,
    TelegramRuntimeBoundaryRequest,
    TelegramRuntimeCapability,
    TelegramRuntimeGateKind,
    TelegramRuntimeGateReasonCode,
    TelegramRuntimeGateReference,
    TelegramRuntimeGateState,
)


def metadata() -> ContractMetadata:
    return ContractMetadata(
        contract_name="telegram-runtime-gate-boundary",
        contract_version="1.0",
        message_id=uuid4(),
        correlation_id=uuid4(),
        producer="unit-test",
    )


def reference(
    meta: ContractMetadata,
    kind: TelegramRuntimeGateKind,
    *,
    accepted: bool = True,
    suffix: str = "",
) -> TelegramRuntimeGateReference:
    return TelegramRuntimeGateReference(
        telegram_runtime_gate_reference_id=f"gate:{kind.value}:{suffix or '1'}",
        metadata=meta,
        gate_kind=kind,
        exact_decision_task_reference_id="TG-15-GATE-001",
        safe_evidence_reference_ids=(f"evidence:{kind.value}:{suffix or '1'}",),
        accepted=accepted,
        verified_in_exact_owner_task=True,
    )


def request(
    meta: ContractMetadata,
    *,
    capability: TelegramRuntimeCapability | None = None,
    surface: TelegramPreGateAllowedSurface | None = None,
    refs: tuple[TelegramRuntimeGateReference, ...] = (),
) -> TelegramRuntimeBoundaryRequest:
    return TelegramRuntimeBoundaryRequest(
        telegram_runtime_boundary_request_id="request:1",
        metadata=meta,
        requested_runtime_capability=capability,
        requested_pre_gate_surface=surface,
        gate_references=refs,
        correlation_reference_ids=("corr:1",),
        causation_reference_ids=("cause:1",),
        evidence_reference_ids=("evidence:request",),
    )


def test_enum_matrices_are_exact() -> None:
    assert tuple(e.value for e in TelegramRuntimeCapability) == (
        "POSTGRESQL_TABLES",
        "SQLALCHEMY_MODELS",
        "PSYCOPG_USAGE",
        "ALEMBIC_MIGRATIONS",
        "PROVIDER_SDK_OR_LIBRARY",
        "HTTP_CLIENT_IMPLEMENTATION",
        "TELEGRAM_API_CALL",
        "WEBHOOK_ENDPOINT",
        "GETUPDATES_LOOP",
        "POLLING_CURSOR",
        "MINI_APP_FRONTEND",
        "BOTFATHER_CONFIGURATION",
        "BOT_TOKEN_CONSUMPTION",
        "PROVIDER_CREDENTIALS",
        "MESSAGE_TEMPLATES",
        "QUEUE_WORKER_SERVICE",
        "ENDPOINT_DOMAIN_TLS_PORT_CONFIGURATION",
        "DOCKER_CICD_DEPLOY",
    )
    assert tuple(e.value for e in TelegramPreGateAllowedSurface) == (
        "SEMANTIC_CONTRACTS",
        "SYNTHETIC_DETERMINISTIC_FAKES",
        "ARCHITECTURE_STATIC_CHECKS",
        "DOCUMENTATION_DECISIONS",
        "EVIDENCE_HANDOFF",
    )
    assert len(tuple(TelegramRuntimeGateKind)) == 10
    assert len(tuple(TelegramRuntimeGateState)) == 5
    assert len(tuple(TelegramRuntimeGateReasonCode)) == 15


def test_every_capability_has_deterministic_gate_outcome() -> None:
    meta = metadata()
    for capability in TelegramRuntimeCapability:
        outcome = TelegramRuntimeBoundaryOutcome.from_request(request(meta, capability=capability))
        assert outcome.state is TelegramRuntimeGateState.BLOCKED_PENDING_EXACT_GATES
        assert outcome.future_exact_task_required is True
        assert outcome.required_gate_kinds == tuple(
            sorted(
                outcome.required_gate_kinds, key=lambda x: tuple(TelegramRuntimeGateKind).index(x)
            )
        )
        assert outcome.missing_gate_kinds == outcome.required_gate_kinds
        assert outcome.reason_codes == tuple(
            TelegramRuntimeGateReasonCode.__members__[f"{k.name}_GATE_REQUIRED"]
            if f"{k.name}_GATE_REQUIRED" in TelegramRuntimeGateReasonCode.__members__
            else {
                TelegramRuntimeGateKind.BOTFATHER_AND_SECRET_OPERATIONS: TelegramRuntimeGateReasonCode.SECRET_OPERATIONS_GATE_REQUIRED,
                TelegramRuntimeGateKind.MINI_APP_SECURITY_AND_UI: TelegramRuntimeGateReasonCode.MINI_APP_GATE_REQUIRED,
            }[k]
            for k in outcome.missing_gate_kinds
        )


def test_all_gates_still_require_future_implementation() -> None:
    meta = metadata()
    refs = tuple(reference(meta, kind) for kind in TelegramRuntimeGateKind)
    outcome = TelegramRuntimeBoundaryOutcome.from_request(
        request(meta, capability=TelegramRuntimeCapability.WEBHOOK_ENDPOINT, refs=refs)
    )
    assert (
        outcome.state
        is TelegramRuntimeGateState.GATES_SATISFIED_FUTURE_IMPLEMENTATION_TASK_REQUIRED
    )
    assert outcome.reason_codes == (
        TelegramRuntimeGateReasonCode.FUTURE_IMPLEMENTATION_TASK_REQUIRED,
    )
    assert all(
        value is False for name, value in outcome.model_dump().items() if name.endswith("authority")
    )


@pytest.mark.parametrize("surface", tuple(TelegramPreGateAllowedSurface))
def test_pre_gate_surfaces_are_allowed_without_authority(
    surface: TelegramPreGateAllowedSurface,
) -> None:
    outcome = TelegramRuntimeBoundaryOutcome.from_request(request(metadata(), surface=surface))
    assert outcome.state is TelegramRuntimeGateState.PRE_GATE_SURFACE_ALLOWED
    assert outcome.future_exact_task_required is False
    assert all(
        value is False for name, value in outcome.model_dump().items() if name.endswith("authority")
    )


def test_conflicts_and_ambiguous_evidence_are_rejected() -> None:
    meta = metadata()
    with pytest.raises(ValueError):
        request(
            meta,
            capability=TelegramRuntimeCapability.TELEGRAM_API_CALL,
            surface=TelegramPreGateAllowedSurface.SEMANTIC_CONTRACTS,
        )
    with pytest.raises(ValueError):
        request(meta)
    with pytest.raises(ValueError):
        TelegramRuntimeGateReference(
            telegram_runtime_gate_reference_id="bad",
            metadata=meta,
            gate_kind=TelegramRuntimeGateKind.PROVIDER_RUNTIME,
            exact_decision_task_reference_id=None,
            safe_evidence_reference_ids=("e",),
            accepted=True,
            verified_in_exact_owner_task=True,
        )
    duplicate = (
        reference(meta, TelegramRuntimeGateKind.PROVIDER_RUNTIME),
        reference(meta, TelegramRuntimeGateKind.PROVIDER_RUNTIME, suffix="2"),
    )
    outcome = TelegramRuntimeBoundaryOutcome.from_request(
        request(meta, capability=TelegramRuntimeCapability.TELEGRAM_API_CALL, refs=duplicate)
    )
    assert outcome.state is TelegramRuntimeGateState.AMBIGUOUS
    assert outcome.reason_codes == (TelegramRuntimeGateReasonCode.AMBIGUOUS_GATE_EVIDENCE,)


def test_nested_types_and_authorities_are_exact_and_false() -> None:
    meta = metadata()
    ref = reference(meta, TelegramRuntimeGateKind.PHYSICAL_SCHEMA)
    with pytest.raises(ValueError):
        TelegramRuntimeBoundaryRequest(
            telegram_runtime_boundary_request_id="r",
            metadata=meta,
            gate_references=[ref],
            correlation_reference_ids=(),
            causation_reference_ids=(),
            evidence_reference_ids=(),
            requested_runtime_capability=TelegramRuntimeCapability.POSTGRESQL_TABLES,
        )
    with pytest.raises(ValueError):
        TelegramRuntimeGateReference(
            telegram_runtime_gate_reference_id="r",
            metadata=meta,
            gate_kind=TelegramRuntimeGateKind.PHYSICAL_SCHEMA,
            exact_decision_task_reference_id="t",
            safe_evidence_reference_ids=(),
            accepted=True,
            verified_in_exact_owner_task=True,
        )

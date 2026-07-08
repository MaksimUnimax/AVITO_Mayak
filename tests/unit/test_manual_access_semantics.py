from __future__ import annotations

import ast
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from mayak.modules.entitlements_and_billing import (
    ENTITLEMENTS_MANUAL_ACCESS_ADMIN,
    ManualAccessActorContext,
    ManualAccessGrantCreateRequest,
    ManualAccessGrantIdempotencyRecord,
    ManualAccessGrantLifecycleDecision,
    ManualAccessGrantLifecycleOutcome,
    ManualAccessGrantRequestKind,
    ManualAccessGrantRevokeRequest,
    evaluate_manual_access_create,
    evaluate_manual_access_revoke,
)
from mayak.modules.entitlements_and_billing.manual_access import compute_manual_access_request_fingerprint
from mayak.platform.idempotency import IdempotencyKey

DECISION_AT = datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc)
ACTIVE_INTERVAL_START = datetime(2026, 7, 8, 9, 0, tzinfo=timezone.utc)
ACTIVE_INTERVAL_END = datetime(2026, 7, 8, 11, 0, tzinfo=timezone.utc)
TARGET_ACCOUNT_ID = "acct-eb04-manual-001"
FOREIGN_SCOPE = "entitlements.billing"
ALLOWED_SCOPE = "entitlements.manual_access"


def _actor(
    *,
    scope: str = ALLOWED_SCOPE,
    capabilities: tuple[str, ...] = (ENTITLEMENTS_MANUAL_ACCESS_ADMIN,),
) -> ManualAccessActorContext:
    return ManualAccessActorContext(
        actor_id="actor-eb04-operator-001",
        actor_category="OPERATOR",
        authorization_scope=scope,
        authorization_reference="authz-eb04-001",
        audit_reference="audit-eb04-actor-001",
        actor_capabilities=capabilities,
    )


def _create_request(
    *,
    actor: ManualAccessActorContext | None = None,
    idempotency_key: IdempotencyKey | None = None,
    scope: str = ALLOWED_SCOPE,
    decision_at: datetime = DECISION_AT,
    effective_interval_end: datetime = ACTIVE_INTERVAL_END,
    prior_idempotency_record: ManualAccessGrantIdempotencyRecord | None = None,
    reason: str = "temporary operator-approved access",
) -> ManualAccessGrantCreateRequest:
    return ManualAccessGrantCreateRequest(
        actor=actor or _actor(scope=scope),
        target_account_id=TARGET_ACCOUNT_ID,
        capability="beacon.scan",
        scope=scope,
        effective_interval={
            "starts_at": ACTIVE_INTERVAL_START,
            "ends_at": effective_interval_end,
        },
        reason=reason,
        idempotency_key=idempotency_key,
        audit_reference="audit-eb04-create-001",
        decision_at=decision_at,
        prior_idempotency_record=prior_idempotency_record,
    )


def _revoke_request(
    *,
    actor: ManualAccessActorContext | None = None,
    idempotency_key: IdempotencyKey | None = None,
    decision_at: datetime = DECISION_AT,
    prior_idempotency_record: ManualAccessGrantIdempotencyRecord | None = None,
    reason: str = "operator closed the manual access window",
) -> ManualAccessGrantRevokeRequest:
    return ManualAccessGrantRevokeRequest(
        actor=actor or _actor(),
        grant_id="manual-grant-eb04-001",
        target_account_id=TARGET_ACCOUNT_ID,
        reason=reason,
        idempotency_key=idempotency_key,
        audit_reference="audit-eb04-revoke-001",
        decision_at=decision_at,
        prior_idempotency_record=prior_idempotency_record,
    )


def test_eb04_manual_access_lifecycle_outcomes_are_approved_and_complete_001() -> None:
    assert [member.value for member in ManualAccessGrantLifecycleOutcome] == [
        "CREATED",
        "REPLAYED",
        "REVOKED",
        "EXPIRED",
        "REJECTED",
        "CONFLICT",
        "IDEMPOTENCY_MISMATCH",
        "UNAUTHORIZED",
        "OUT_OF_SCOPE",
    ]


def test_eb04_manual_access_create_authorized_001() -> None:
    request = _create_request(idempotency_key=IdempotencyKey(value="idem-eb04-create-001"))
    decision = evaluate_manual_access_create(request)

    assert decision.outcome is ManualAccessGrantLifecycleOutcome.CREATED
    assert decision.terminal_outcome is ManualAccessGrantLifecycleOutcome.CREATED
    assert decision.reason_code == "MANUAL_ACCESS_CREATED"
    assert decision.history_preserved is True
    assert decision.request_kind is ManualAccessGrantRequestKind.CREATE


def test_eb04_manual_access_create_unauthorized_001() -> None:
    request = _create_request(
        actor=_actor(capabilities=()),
        idempotency_key=IdempotencyKey(value="idem-eb04-create-002"),
    )
    decision = evaluate_manual_access_create(request)

    assert decision.outcome is ManualAccessGrantLifecycleOutcome.UNAUTHORIZED
    assert decision.reason_code == "MANUAL_ACCESS_ADMIN_CAPABILITY_REQUIRED"


def test_eb04_manual_access_create_missing_idempotency_rejected_001() -> None:
    request = _create_request(idempotency_key=None)
    decision = evaluate_manual_access_create(request)

    assert decision.outcome is ManualAccessGrantLifecycleOutcome.REJECTED
    assert decision.reason_code == "IDEMPOTENCY_KEY_REQUIRED"


def test_eb04_manual_access_create_open_ended_rejected_001() -> None:
    payload = _create_request(
        idempotency_key=IdempotencyKey(value="idem-eb04-create-003"),
    ).model_dump()
    payload["effective_interval"].pop("ends_at")

    with pytest.raises(ValidationError):
        ManualAccessGrantCreateRequest.model_validate(payload)


def test_eb04_manual_access_create_out_of_scope_001() -> None:
    request = _create_request(
        actor=_actor(scope=FOREIGN_SCOPE),
        idempotency_key=IdempotencyKey(value="idem-eb04-create-004"),
    )
    decision = evaluate_manual_access_create(request)

    assert decision.outcome is ManualAccessGrantLifecycleOutcome.OUT_OF_SCOPE
    assert decision.reason_code == "AUTHORIZATION_SCOPE_OUT_OF_SCOPE"


def test_eb04_manual_access_idempotent_replay_same_fingerprint_001() -> None:
    request = _create_request(idempotency_key=IdempotencyKey(value="idem-eb04-create-005"))
    fingerprint = compute_manual_access_request_fingerprint(ManualAccessGrantRequestKind.CREATE, request)
    prior = ManualAccessGrantIdempotencyRecord(
        request_kind=ManualAccessGrantRequestKind.CREATE,
        idempotency_key=request.idempotency_key,
        request_fingerprint=fingerprint,
        terminal_outcome=ManualAccessGrantLifecycleOutcome.CREATED,
    )
    replay_request = request.model_copy(update={"prior_idempotency_record": prior})

    decision = evaluate_manual_access_create(replay_request)

    assert decision.outcome is ManualAccessGrantLifecycleOutcome.REPLAYED
    assert decision.terminal_outcome is ManualAccessGrantLifecycleOutcome.CREATED
    assert decision.reason_code == "IDEMPOTENT_REPLAY"


def test_eb04_manual_access_idempotency_mismatch_001() -> None:
    request = _create_request(idempotency_key=IdempotencyKey(value="idem-eb04-create-006"))
    prior = ManualAccessGrantIdempotencyRecord(
        request_kind=ManualAccessGrantRequestKind.CREATE,
        idempotency_key=request.idempotency_key,
        request_fingerprint=compute_manual_access_request_fingerprint(ManualAccessGrantRequestKind.CREATE, request),
        terminal_outcome=ManualAccessGrantLifecycleOutcome.CREATED,
    )
    changed_request = request.model_copy(
        update={
            "reason": "changed request fingerprint",
            "prior_idempotency_record": prior,
        }
    )

    decision = evaluate_manual_access_create(changed_request)

    assert decision.outcome is ManualAccessGrantLifecycleOutcome.IDEMPOTENCY_MISMATCH
    assert decision.reason_code == "IDEMPOTENCY_MISMATCH"


def test_eb04_manual_access_revoke_authorized_001() -> None:
    request = _revoke_request(idempotency_key=IdempotencyKey(value="idem-eb04-revoke-001"))
    decision = evaluate_manual_access_revoke(request)

    assert decision.outcome is ManualAccessGrantLifecycleOutcome.REVOKED
    assert decision.terminal_outcome is ManualAccessGrantLifecycleOutcome.REVOKED
    assert decision.history_preserved is True


def test_eb04_manual_access_revoke_unauthorized_001() -> None:
    request = _revoke_request(
        actor=_actor(capabilities=()),
        idempotency_key=IdempotencyKey(value="idem-eb04-revoke-002"),
    )
    decision = evaluate_manual_access_revoke(request)

    assert decision.outcome is ManualAccessGrantLifecycleOutcome.UNAUTHORIZED
    assert decision.reason_code == "MANUAL_ACCESS_ADMIN_CAPABILITY_REQUIRED"


def test_eb04_manual_access_revoke_missing_audit_rejected_001() -> None:
    payload = _revoke_request(idempotency_key=IdempotencyKey(value="idem-eb04-revoke-003")).model_dump()
    payload.pop("audit_reference")

    with pytest.raises(ValidationError):
        ManualAccessGrantRevokeRequest.model_validate(payload)


def test_eb04_manual_access_revoke_does_not_delete_history_001() -> None:
    request = _revoke_request(idempotency_key=IdempotencyKey(value="idem-eb04-revoke-004"))
    decision = evaluate_manual_access_revoke(request)

    assert decision.outcome is ManualAccessGrantLifecycleOutcome.REVOKED
    assert decision.history_preserved is True
    assert decision.grant_id == "manual-grant-eb04-001"


def test_eb04_manual_access_no_ui_db_provider_authority_001() -> None:
    create_source = Path("src/mayak/modules/entitlements_and_billing/manual_access.py").read_text().lower()
    forbidden_fragments = (
        "ui toggle",
        "chat message",
        "direct database edit",
        "provider/payment event",
        "client-side admin flag",
        "fastapi",
        "sqlalchemy",
        "psycopg",
        "alembic",
        "provider sdk",
        "payment",
    )

    assert all(fragment not in create_source for fragment in forbidden_fragments)


def test_eb04_od010_od011_od013_remain_gated_001() -> None:
    request_field_names = set(ManualAccessGrantCreateRequest.model_fields)
    revoke_field_names = set(ManualAccessGrantRevokeRequest.model_fields)

    for forbidden_fragment in ("country", "monitoring_frequency", "retention"):
        assert forbidden_fragment not in request_field_names
        assert forbidden_fragment not in revoke_field_names


def test_eb04_no_runtime_db_provider_imports_001() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    module_path = repo_root / "src/mayak/modules/entitlements_and_billing/manual_access.py"
    source = module_path.read_text()
    tree = ast.parse(source)

    allowed_import_roots = {
        "__future__",
        "datetime",
        "enum",
        "contracts",
        "mayak",
        "pydantic",
        "typing",
    }

    import_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                import_roots.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            import_roots.add(node.module.split(".", 1)[0])

    assert import_roots <= allowed_import_roots

    request = _create_request(idempotency_key=IdempotencyKey(value="idem-eb04-create-007"))
    decision = evaluate_manual_access_create(request)
    synthetic_payload_text = request.model_dump_json().lower() + decision.model_dump_json().lower()

    for forbidden_fragment in ("token", "secret", "credential", "password", "card", "cvv", "pan"):
        assert forbidden_fragment not in synthetic_payload_text

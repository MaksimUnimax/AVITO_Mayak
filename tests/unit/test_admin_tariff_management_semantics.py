from __future__ import annotations

from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path

from mayak.modules.entitlements_and_billing import (
    APPROVED_TARIFF_DEFINITIONS,
    BASIC_TARIFF_POLICY,
    ENTITLEMENTS_MANUAL_ACCESS_ADMIN,
    FREE_TARIFF_POLICY,
    FUTURE_DECISION_GATES,
    AdminActorContext,
    AdminTariffAssignmentRequest,
    AdminTariffCapability,
    AdminTariffCommandFamily,
    AdminTariffDraftRequest,
    AdminTariffFieldValue,
    AdminTariffIdempotencyRecord,
    AdminTariffOutcome,
    AdminTariffPublishRequest,
    ENTITLEMENTS_TARIFF_ADMIN,
    ENTITLEMENTS_TARIFF_ASSIGN_ADMIN,
    compute_admin_tariff_request_fingerprint,
    evaluate_admin_tariff_assignment,
    evaluate_admin_tariff_draft,
    evaluate_admin_tariff_publish,
)
from mayak.platform.idempotency import IdempotencyKey

DECISION_AT = datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc)
ADMIN_SCOPE = "entitlements.tariff.admin"
ASSIGN_SCOPE = "entitlements.tariff.assign"
MANUAL_ACCESS_SCOPE = "entitlements.manual_access"
TARGET_ACCOUNT_ID = "acct-eb11-own-001"


def _actor(
    *,
    scope: str,
    capabilities: tuple[str, ...],
    actor_id: str = "actor-eb11-operator-001",
) -> AdminActorContext:
    return AdminActorContext(
        actor_id=actor_id,
        actor_category="OPERATOR",
        authorization_scope=scope,
        authorization_reference="authz-eb11-001",
        audit_reference="audit-eb11-actor-001",
        actor_capabilities=capabilities,
    )


def _tariff_fields(
    tariff,
    **overrides: str | int | bool | None,
) -> tuple[AdminTariffFieldValue, ...]:
    payload = {
        "tariff_name": tariff.tariff_name.value,
        "semantic_version": tariff.semantic_version,
        "price_rub": tariff.price_rub,
        "billing_period_label": tariff.billing_period_label,
        "scan_interval_floor_minutes": tariff.scan_interval_floor_minutes,
        "scan_interval_step_minutes": tariff.scan_interval_step_minutes,
        "active_beacon_limit": tariff.active_beacon_limit,
        "feature_notes": tariff.feature_notes,
        "mechanism_notes": tariff.mechanism_notes,
    }
    payload.update(overrides)
    return tuple(AdminTariffFieldValue(field_name=name, field_value=value) for name, value in payload.items())


def _draft_request(
    *,
    command_family: AdminTariffCommandFamily = AdminTariffCommandFamily.CREATE_TARIFF_DRAFT,
    actor: AdminActorContext | None = None,
    scope: str = ADMIN_SCOPE,
    capabilities: tuple[str, ...] = (ENTITLEMENTS_TARIFF_ADMIN,),
    semantic_draft_id: str = "draft-eb11-001",
    target_tariff_key: str = "BASIC",
    requested_tariff_fields: tuple[AdminTariffFieldValue, ...] | None = None,
    reason: str = "operator-approved draft",
    idempotency_key: IdempotencyKey | None = None,
    audit_reference: str | None = "audit-eb11-draft-001",
    current_product_policy=APPROVED_TARIFF_DEFINITIONS,
    open_decision_blockers: tuple[str, ...] = FUTURE_DECISION_GATES,
    direct_admin_write_requested: bool = False,
    direct_web_write_requested: bool = False,
    direct_table_write_requested: bool = False,
    role_change_requested: bool = False,
    mutate_historical_definition: bool = False,
    delete_tariff_history: bool = False,
    retire_or_disable_tariff: bool = False,
    target_tariff_reference: str | None = None,
) -> AdminTariffDraftRequest:
    resolved_actor = actor or _actor(scope=scope, capabilities=capabilities)
    resolved_requested_fields = (
        requested_tariff_fields
        if requested_tariff_fields is not None
        else _tariff_fields(BASIC_TARIFF_POLICY)
    )
    return AdminTariffDraftRequest(
        command_family=command_family,
        actor=resolved_actor,
        required_authorization_scope=scope,
        semantic_draft_id=semantic_draft_id,
        target_tariff_key=target_tariff_key,
        target_tariff_reference=target_tariff_reference,
        requested_tariff_fields=resolved_requested_fields,
        reason=reason,
        idempotency_key=idempotency_key,
        audit_reference=audit_reference,
        decision_at=DECISION_AT,
        current_product_policy=current_product_policy,
        open_decision_blockers=open_decision_blockers,
        direct_admin_write_requested=direct_admin_write_requested,
        direct_web_write_requested=direct_web_write_requested,
        direct_table_write_requested=direct_table_write_requested,
        role_change_requested=role_change_requested,
        mutate_historical_definition=mutate_historical_definition,
        delete_tariff_history=delete_tariff_history,
        retire_or_disable_tariff=retire_or_disable_tariff,
    )


def _publish_request(
    *,
    actor: AdminActorContext | None = None,
    scope: str = ADMIN_SCOPE,
    capabilities: tuple[str, ...] = (ENTITLEMENTS_TARIFF_ADMIN,),
    approved_tariff_definition=BASIC_TARIFF_POLICY,
    target_tariff_key: str | None = None,
    requested_tariff_fields: tuple[AdminTariffFieldValue, ...] | None = None,
    reason: str = "operator-approved publish",
    idempotency_key: IdempotencyKey | None = None,
    audit_reference: str | None = "audit-eb11-publish-001",
    current_product_policy=APPROVED_TARIFF_DEFINITIONS,
    publish_ready_only: bool = False,
    direct_admin_write_requested: bool = False,
    direct_web_write_requested: bool = False,
    direct_table_write_requested: bool = False,
    role_change_requested: bool = False,
    target_tariff_reference: str | None = None,
) -> AdminTariffPublishRequest:
    resolved_actor = actor or _actor(scope=scope, capabilities=capabilities)
    approved_definition = approved_tariff_definition
    if target_tariff_key is None and approved_definition is not None:
        target_tariff_key = approved_definition.tariff_name.value
    resolved_requested_fields = (
        requested_tariff_fields
        if requested_tariff_fields is not None
        else (_tariff_fields(approved_definition) if approved_definition is not None else ())
    )
    return AdminTariffPublishRequest(
        actor=resolved_actor,
        required_authorization_scope=scope,
        target_tariff_key=target_tariff_key,
        target_tariff_reference=target_tariff_reference,
        approved_tariff_definition=approved_definition,
        requested_tariff_fields=resolved_requested_fields,
        reason=reason,
        idempotency_key=idempotency_key,
        audit_reference=audit_reference,
        decision_at=DECISION_AT,
        current_product_policy=current_product_policy,
        publish_ready_only=publish_ready_only,
        direct_admin_write_requested=direct_admin_write_requested,
        direct_web_write_requested=direct_web_write_requested,
        direct_table_write_requested=direct_table_write_requested,
        role_change_requested=role_change_requested,
    )


def _assignment_request(
    *,
    command_family: AdminTariffCommandFamily = AdminTariffCommandFamily.ASSIGN_ACCOUNT_TARIFF,
    actor: AdminActorContext | None = None,
    scope: str = ASSIGN_SCOPE,
    capabilities: tuple[str, ...] = (ENTITLEMENTS_TARIFF_ASSIGN_ADMIN,),
    target_account_id: str = TARGET_ACCOUNT_ID,
    approved_tariff_definition=BASIC_TARIFF_POLICY,
    target_tariff_key: str | None = None,
    requested_tariff_fields: tuple[AdminTariffFieldValue, ...] | None = None,
    manual_access_scope: str | None = None,
    target_tariff_reference: str | None = None,
    provider_evidence_reference: str | None = None,
    ui_client_flag: str | None = None,
    provider_username: str | None = None,
    chat_title: str | None = None,
    local_config_reference: str | None = None,
    client_supplied_admin_flag: str | None = None,
    reason: str = "operator-approved assignment",
    idempotency_key: IdempotencyKey | None = None,
    audit_reference: str | None = "audit-eb11-assign-001",
    current_product_policy=APPROVED_TARIFF_DEFINITIONS,
    direct_admin_write_requested: bool = False,
    direct_web_write_requested: bool = False,
    direct_table_write_requested: bool = False,
    role_change_requested: bool = False,
) -> AdminTariffAssignmentRequest:
    resolved_actor = actor or _actor(scope=scope, capabilities=capabilities)
    if target_tariff_key is None and approved_tariff_definition is not None:
        target_tariff_key = approved_tariff_definition.tariff_name.value
    resolved_requested_fields = (
        _tariff_fields(approved_tariff_definition)
        if requested_tariff_fields is None and approved_tariff_definition is not None
        else (requested_tariff_fields or ())
    )
    return AdminTariffAssignmentRequest(
        command_family=command_family,
        actor=resolved_actor,
        required_authorization_scope=scope,
        target_account_id=target_account_id,
        target_tariff_key=target_tariff_key,
        target_tariff_reference=target_tariff_reference,
        approved_tariff_definition=approved_tariff_definition,
        manual_access_scope=manual_access_scope,
        provider_evidence_reference=provider_evidence_reference,
        ui_client_flag=ui_client_flag,
        provider_username=provider_username,
        chat_title=chat_title,
        local_config_reference=local_config_reference,
        client_supplied_admin_flag=client_supplied_admin_flag,
        reason=reason,
        idempotency_key=idempotency_key,
        audit_reference=audit_reference,
        decision_at=DECISION_AT,
        current_product_policy=current_product_policy,
        requested_tariff_fields=resolved_requested_fields,
        direct_admin_write_requested=direct_admin_write_requested,
        direct_web_write_requested=direct_web_write_requested,
        direct_table_write_requested=direct_table_write_requested,
        role_change_requested=role_change_requested,
    )


def test_eb11_capability_references_represented_001() -> None:
    assert [member.value for member in AdminTariffCapability] == [
        "ENTITLEMENTS_TARIFF_ADMIN",
        "ENTITLEMENTS_TARIFF_ASSIGN_ADMIN",
        "ENTITLEMENTS_MANUAL_ACCESS_ADMIN",
    ]
    assert ENTITLEMENTS_TARIFF_ADMIN == "ENTITLEMENTS_TARIFF_ADMIN"
    assert ENTITLEMENTS_TARIFF_ASSIGN_ADMIN == "ENTITLEMENTS_TARIFF_ASSIGN_ADMIN"
    assert ENTITLEMENTS_MANUAL_ACCESS_ADMIN == "ENTITLEMENTS_MANUAL_ACCESS_ADMIN"


def test_eb11_command_families_represented_001() -> None:
    assert [member.value for member in AdminTariffCommandFamily] == [
        "CreateTariffDraftCommand",
        "EditTariffDraftCommand",
        "PublishTariffDefinitionCommand",
        "AssignAccountTariffCommand",
        "AssignManualAccessCommand",
        "RejectAdminTariffCommand",
    ]


def test_eb11_outcomes_represented_001() -> None:
    assert [member.value for member in AdminTariffOutcome] == [
        "DRAFT_CREATED",
        "DRAFT_UPDATED",
        "PUBLISH_READY",
        "PUBLISHED",
        "ASSIGNED",
        "MANUAL_ACCESS_ASSIGNED",
        "REJECTED",
        "FORBIDDEN",
        "CONFLICT",
        "REPLAYED",
        "IDEMPOTENCY_MISMATCH",
        "BLOCKED",
        "UNAVAILABLE",
    ]


def test_eb11_create_tariff_draft_semantic_only_001() -> None:
    request = _draft_request(idempotency_key=IdempotencyKey(value="idem-eb11-draft-create-001"))
    decision = evaluate_admin_tariff_draft(request)

    assert decision.outcome is AdminTariffOutcome.DRAFT_CREATED
    assert decision.terminal_outcome is AdminTariffOutcome.DRAFT_CREATED
    assert decision.draft_non_authoritative is True
    assert decision.changes_access is False
    assert decision.changes_subscription is False
    assert decision.changes_payment_or_provider is False
    assert decision.semantic_only is True


def test_eb11_draft_does_not_change_access_subscription_payment_001() -> None:
    request = _draft_request(idempotency_key=IdempotencyKey(value="idem-eb11-draft-002"))
    decision = evaluate_admin_tariff_draft(request)

    assert decision.changes_access is False
    assert decision.changes_subscription is False
    assert decision.changes_payment_or_provider is False
    assert decision.changes_billing_tables is False


def test_eb11_edit_tariff_draft_semantic_only_001() -> None:
    request = _draft_request(
        command_family=AdminTariffCommandFamily.EDIT_TARIFF_DRAFT,
        semantic_draft_id="draft-eb11-edit-001",
        idempotency_key=IdempotencyKey(value="idem-eb11-draft-edit-001"),
    )
    decision = evaluate_admin_tariff_draft(request)

    assert decision.outcome is AdminTariffOutcome.DRAFT_UPDATED
    assert decision.draft_non_authoritative is True
    assert decision.semantic_draft_id == "draft-eb11-edit-001"


def test_eb11_publish_free_basic_only_when_approved_001() -> None:
    request = _publish_request(
        approved_tariff_definition=FREE_TARIFF_POLICY,
        requested_tariff_fields=_tariff_fields(FREE_TARIFF_POLICY),
        idempotency_key=IdempotencyKey(value="idem-eb11-publish-001"),
    )
    decision = evaluate_admin_tariff_publish(request)

    assert decision.outcome is AdminTariffOutcome.PUBLISHED
    assert decision.terminal_outcome is AdminTariffOutcome.PUBLISHED
    assert decision.approved_tariff_name.value == "FREE"
    assert decision.semantic_only is True


def test_eb11_future_tariff_values_blocked_001() -> None:
    request = _publish_request(
        approved_tariff_definition=BASIC_TARIFF_POLICY,
        requested_tariff_fields=_tariff_fields(BASIC_TARIFF_POLICY, price_rub=123),
        idempotency_key=IdempotencyKey(value="idem-eb11-publish-002"),
    )
    decision = evaluate_admin_tariff_publish(request)

    assert decision.outcome is AdminTariffOutcome.BLOCKED
    assert decision.reason_code == "FUTURE_TARIFF_VALUES_BLOCKED"


def test_eb11_published_tariff_historical_mutation_blocked_001() -> None:
    request = _draft_request(
        command_family=AdminTariffCommandFamily.EDIT_TARIFF_DRAFT,
        target_tariff_reference="tariff-basic-v1",
        mutate_historical_definition=True,
        idempotency_key=IdempotencyKey(value="idem-eb11-draft-hist-001"),
    )
    decision = evaluate_admin_tariff_draft(request)

    assert decision.outcome is AdminTariffOutcome.BLOCKED
    assert decision.reason_code == "HISTORICAL_TARIFF_MUTATION_BLOCKED"


def test_eb11_tariff_history_deletion_blocked_001() -> None:
    request = _draft_request(
        command_family=AdminTariffCommandFamily.EDIT_TARIFF_DRAFT,
        delete_tariff_history=True,
        idempotency_key=IdempotencyKey(value="idem-eb11-draft-delete-001"),
    )
    decision = evaluate_admin_tariff_draft(request)

    assert decision.outcome is AdminTariffOutcome.BLOCKED
    assert decision.reason_code == "HISTORICAL_TARIFF_MUTATION_BLOCKED"


def test_eb11_tariff_retirement_blocked_001() -> None:
    request = _draft_request(
        command_family=AdminTariffCommandFamily.EDIT_TARIFF_DRAFT,
        retire_or_disable_tariff=True,
        idempotency_key=IdempotencyKey(value="idem-eb11-draft-retire-001"),
    )
    decision = evaluate_admin_tariff_draft(request)

    assert decision.outcome is AdminTariffOutcome.BLOCKED
    assert decision.reason_code == "HISTORICAL_TARIFF_MUTATION_BLOCKED"


def test_eb11_assign_account_tariff_requires_approved_tariff_001() -> None:
    request = _assignment_request(
        command_family=AdminTariffCommandFamily.ASSIGN_ACCOUNT_TARIFF,
        approved_tariff_definition=BASIC_TARIFF_POLICY,
        target_tariff_key="BASIC",
        idempotency_key=IdempotencyKey(value="idem-eb11-assign-tariff-001"),
    )
    decision = evaluate_admin_tariff_assignment(request)

    assert decision.outcome is AdminTariffOutcome.ASSIGNED
    assert decision.target_account_id == TARGET_ACCOUNT_ID
    assert decision.approved_tariff_name.value == "BASIC"


def test_eb11_assign_draft_tariff_blocked_001() -> None:
    request = _assignment_request(
        command_family=AdminTariffCommandFamily.ASSIGN_ACCOUNT_TARIFF,
        approved_tariff_definition=None,
        target_tariff_reference="draft-only-001",
        idempotency_key=IdempotencyKey(value="idem-eb11-assign-draft-001"),
    )
    decision = evaluate_admin_tariff_assignment(request)

    assert decision.outcome is AdminTariffOutcome.REJECTED
    assert decision.reason_code == "APPROVED_TARIFF_DEFINITION_REQUIRED"


def test_eb11_assign_manual_access_uses_manual_access_capability_001() -> None:
    request = _assignment_request(
        command_family=AdminTariffCommandFamily.ASSIGN_MANUAL_ACCESS,
        actor=_actor(scope=MANUAL_ACCESS_SCOPE, capabilities=(ENTITLEMENTS_MANUAL_ACCESS_ADMIN,)),
        capabilities=(ENTITLEMENTS_MANUAL_ACCESS_ADMIN,),
        scope=MANUAL_ACCESS_SCOPE,
        manual_access_scope=MANUAL_ACCESS_SCOPE,
        approved_tariff_definition=None,
        idempotency_key=IdempotencyKey(value="idem-eb11-manual-assign-001"),
    )
    decision = evaluate_admin_tariff_assignment(request)

    assert decision.outcome is AdminTariffOutcome.MANUAL_ACCESS_ASSIGNED
    assert decision.manual_access_scope == MANUAL_ACCESS_SCOPE


def test_eb11_payment_provider_evidence_cannot_assign_tariff_001() -> None:
    request = _assignment_request(
        actor=_actor(scope=ASSIGN_SCOPE, capabilities=()),
        capabilities=(),
        approved_tariff_definition=BASIC_TARIFF_POLICY,
        target_tariff_key="BASIC",
        provider_evidence_reference="provider-ref-eb11-001",
        idempotency_key=IdempotencyKey(value="idem-eb11-provider-evidence-001"),
    )
    decision = evaluate_admin_tariff_assignment(request)

    assert decision.outcome is AdminTariffOutcome.FORBIDDEN
    assert decision.reason_code == "TARIFF_ASSIGN_ADMIN_CAPABILITY_REQUIRED"


def test_eb11_ui_client_flag_cannot_authorize_001() -> None:
    request = _assignment_request(
        actor=_actor(scope=ASSIGN_SCOPE, capabilities=()),
        capabilities=(),
        approved_tariff_definition=BASIC_TARIFF_POLICY,
        target_tariff_key="BASIC",
        ui_client_flag="admin-panel",
        provider_username="provider-username-placeholder",
        chat_title="admins-chat",
        local_config_reference="local-config-placeholder",
        client_supplied_admin_flag="true",
        idempotency_key=IdempotencyKey(value="idem-eb11-ui-flag-001"),
    )
    decision = evaluate_admin_tariff_assignment(request)

    assert decision.outcome is AdminTariffOutcome.FORBIDDEN
    assert decision.reason_code == "TARIFF_ASSIGN_ADMIN_CAPABILITY_REQUIRED"


def test_eb11_missing_actor_forbidden_or_rejected_001() -> None:
    request = AdminTariffDraftRequest(
        command_family=AdminTariffCommandFamily.CREATE_TARIFF_DRAFT,
        actor=None,
        required_authorization_scope=ADMIN_SCOPE,
        semantic_draft_id="draft-eb11-missing-actor-001",
        target_tariff_key="BASIC",
        requested_tariff_fields=_tariff_fields(BASIC_TARIFF_POLICY),
        reason="operator-approved draft",
        idempotency_key=IdempotencyKey(value="idem-eb11-missing-actor-001"),
        audit_reference="audit-eb11-missing-actor-001",
        decision_at=DECISION_AT,
        current_product_policy=APPROVED_TARIFF_DEFINITIONS,
        open_decision_blockers=FUTURE_DECISION_GATES,
    )
    decision = evaluate_admin_tariff_draft(request)

    assert decision.outcome is AdminTariffOutcome.UNAVAILABLE
    assert decision.reason_code == "ACTOR_CONTEXT_REQUIRED"


def test_eb11_missing_capability_forbidden_001() -> None:
    request = _draft_request(
        actor=_actor(scope=ADMIN_SCOPE, capabilities=()),
        capabilities=(),
        idempotency_key=IdempotencyKey(value="idem-eb11-missing-cap-001"),
    )
    decision = evaluate_admin_tariff_draft(request)

    assert decision.outcome is AdminTariffOutcome.FORBIDDEN
    assert decision.reason_code == "TARIFF_ADMIN_CAPABILITY_REQUIRED"


def test_eb11_missing_reason_rejected_001() -> None:
    request = _publish_request(
        reason=None,  # type: ignore[arg-type]
        idempotency_key=IdempotencyKey(value="idem-eb11-missing-reason-001"),
    )
    decision = evaluate_admin_tariff_publish(request)

    assert decision.outcome is AdminTariffOutcome.REJECTED
    assert decision.reason_code == "REASON_REQUIRED"


def test_eb11_missing_audit_reference_rejected_001() -> None:
    request = _publish_request(
        audit_reference=None,
        idempotency_key=IdempotencyKey(value="idem-eb11-missing-audit-001"),
    )
    decision = evaluate_admin_tariff_publish(request)

    assert decision.outcome is AdminTariffOutcome.REJECTED
    assert decision.reason_code == "AUDIT_REFERENCE_REQUIRED"


def test_eb11_missing_idempotency_rejected_001() -> None:
    request = _publish_request(idempotency_key=None)
    decision = evaluate_admin_tariff_publish(request)

    assert decision.outcome is AdminTariffOutcome.REJECTED
    assert decision.reason_code == "IDEMPOTENCY_KEY_REQUIRED"


def test_eb11_idempotent_replay_same_fingerprint_001() -> None:
    request = _draft_request(idempotency_key=IdempotencyKey(value="idem-eb11-replay-001"))
    fingerprint = compute_admin_tariff_request_fingerprint(request.command_family, request)
    prior = AdminTariffIdempotencyRecord(
        command_family=request.command_family,
        idempotency_key=request.idempotency_key,
        request_fingerprint=fingerprint,
        terminal_outcome=AdminTariffOutcome.DRAFT_CREATED,
    )
    replay_request = request.model_copy(update={"prior_idempotency_record": prior})

    decision = evaluate_admin_tariff_draft(replay_request)

    assert decision.outcome is AdminTariffOutcome.REPLAYED
    assert decision.terminal_outcome is AdminTariffOutcome.DRAFT_CREATED
    assert decision.reason_code == "IDEMPOTENT_REPLAY"


def test_eb11_idempotency_mismatch_001() -> None:
    request = _draft_request(idempotency_key=IdempotencyKey(value="idem-eb11-mismatch-001"))
    fingerprint = compute_admin_tariff_request_fingerprint(request.command_family, request)
    prior = AdminTariffIdempotencyRecord(
        command_family=request.command_family,
        idempotency_key=request.idempotency_key,
        request_fingerprint=fingerprint,
        terminal_outcome=AdminTariffOutcome.DRAFT_CREATED,
    )
    changed_request = request.model_copy(
        update={
            "reason": "changed request fingerprint",
            "prior_idempotency_record": prior,
        }
    )

    decision = evaluate_admin_tariff_draft(changed_request)

    assert decision.outcome is AdminTariffOutcome.IDEMPOTENCY_MISMATCH
    assert decision.reason_code == "IDEMPOTENCY_MISMATCH"


def test_eb11_direct_admin_write_blocked_001() -> None:
    request = _publish_request(
        direct_admin_write_requested=True,
        idempotency_key=IdempotencyKey(value="idem-eb11-direct-admin-001"),
    )
    decision = evaluate_admin_tariff_publish(request)

    assert decision.outcome is AdminTariffOutcome.BLOCKED
    assert decision.reason_code == "DIRECT_WRITE_BLOCKED"


def test_eb11_direct_web_write_blocked_001() -> None:
    request = _publish_request(
        direct_web_write_requested=True,
        idempotency_key=IdempotencyKey(value="idem-eb11-direct-web-001"),
    )
    decision = evaluate_admin_tariff_publish(request)

    assert decision.outcome is AdminTariffOutcome.BLOCKED
    assert decision.reason_code == "DIRECT_WRITE_BLOCKED"


def test_eb11_direct_table_write_blocked_001() -> None:
    request = _publish_request(
        direct_table_write_requested=True,
        idempotency_key=IdempotencyKey(value="idem-eb11-direct-table-001"),
    )
    decision = evaluate_admin_tariff_publish(request)

    assert decision.outcome is AdminTariffOutcome.BLOCKED
    assert decision.reason_code == "DIRECT_WRITE_BLOCKED"


def test_eb11_role_changing_blocked_001() -> None:
    request = _draft_request(
        role_change_requested=True,
        idempotency_key=IdempotencyKey(value="idem-eb11-role-change-001"),
    )
    decision = evaluate_admin_tariff_draft(request)

    assert decision.outcome is AdminTariffOutcome.BLOCKED
    assert decision.reason_code == "ROLE_CHANGING_BLOCKED"


def test_eb11_role_taxonomy_not_closed_001() -> None:
    module = import_module("mayak.modules.entitlements_and_billing.admin_tariff_management")

    assert AdminActorContext.model_fields["actor_category"].annotation is str
    assert not hasattr(module, "AdminRole")
    assert not hasattr(module, "AdminRoleTaxonomy")


def test_eb11_audit_retention_storage_blocked_od013_001() -> None:
    module_text = Path("src/mayak/modules/entitlements_and_billing/admin_tariff_management.py").read_text().lower()

    assert "audit_storage" not in module_text
    assert "retention_storage" not in module_text
    assert "persistent_audit" not in module_text
    assert "sqlalchemy" not in module_text
    assert "psycopg" not in module_text


def test_eb11_od010_od011_od013_remain_gated_001() -> None:
    assert FUTURE_DECISION_GATES == ("OD-010", "OD-011", "OD-013")
    publish_fields = set(AdminTariffPublishRequest.model_fields)
    assert "country_wide" not in publish_fields
    assert "monitoring_frequency" not in publish_fields
    assert "retention_days" not in publish_fields


def test_eb11_no_admin_web_role_db_runtime_imports_001() -> None:
    module_text = Path("src/mayak/modules/entitlements_and_billing/admin_tariff_management.py").read_text().lower()
    forbidden_fragments = (
        "fastapi",
        "starlette",
        "jinja2",
        "httpx",
        "sqlalchemy",
        "psycopg",
        "alembic",
        "identity_and_access",
        "admin_and_support",
        "web_cabinet",
        "docker",
    )

    assert all(fragment not in module_text for fragment in forbidden_fragments)


def test_eb11_no_secrets_or_credentials_in_fixtures_001() -> None:
    module_text = Path("src/mayak/modules/entitlements_and_billing/admin_tariff_management.py").read_text().lower()
    fixtures_text = Path("src/mayak/modules/entitlements_and_billing/fixtures.py").read_text().lower()
    sensitive_fragments = ("token", "credential", "password", "card", "cvv", "pan")

    assert all(fragment not in module_text for fragment in sensitive_fragments)
    assert all(fragment not in fixtures_text for fragment in sensitive_fragments)

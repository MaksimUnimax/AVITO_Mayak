"""Deterministic semantic contracts for admin tariff-management boundaries."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mayak.platform.idempotency import IdempotencyFingerprint, IdempotencyKey

from .contracts import TariffDefinition, TariffName
from .manual_access import ENTITLEMENTS_MANUAL_ACCESS_ADMIN
from .policies import APPROVED_TARIFF_DEFINITIONS, BASIC_TARIFF_POLICY, FREE_TARIFF_POLICY, FUTURE_DECISION_GATES

ENTITLEMENTS_TARIFF_ADMIN: Final[str] = "ENTITLEMENTS_TARIFF_ADMIN"
ENTITLEMENTS_TARIFF_ASSIGN_ADMIN: Final[str] = "ENTITLEMENTS_TARIFF_ASSIGN_ADMIN"


class AdminTariffCapability(str, Enum):
    """Approved semantic capability references for EB-11 admin tariff boundaries."""

    ENTITLEMENTS_TARIFF_ADMIN = ENTITLEMENTS_TARIFF_ADMIN
    ENTITLEMENTS_TARIFF_ASSIGN_ADMIN = ENTITLEMENTS_TARIFF_ASSIGN_ADMIN
    ENTITLEMENTS_MANUAL_ACCESS_ADMIN = ENTITLEMENTS_MANUAL_ACCESS_ADMIN


class AdminTariffCommandFamily(str, Enum):
    """Approved semantic command families for EB-11 admin tariff boundaries."""

    CREATE_TARIFF_DRAFT = "CreateTariffDraftCommand"
    EDIT_TARIFF_DRAFT = "EditTariffDraftCommand"
    PUBLISH_TARIFF_DEFINITION = "PublishTariffDefinitionCommand"
    ASSIGN_ACCOUNT_TARIFF = "AssignAccountTariffCommand"
    ASSIGN_MANUAL_ACCESS = "AssignManualAccessCommand"
    REJECT_ADMIN_TARIFF = "RejectAdminTariffCommand"


class AdminTariffOutcome(str, Enum):
    """Approved deterministic outcomes for EB-11 admin tariff semantics."""

    DRAFT_CREATED = "DRAFT_CREATED"
    DRAFT_UPDATED = "DRAFT_UPDATED"
    PUBLISH_READY = "PUBLISH_READY"
    PUBLISHED = "PUBLISHED"
    ASSIGNED = "ASSIGNED"
    MANUAL_ACCESS_ASSIGNED = "MANUAL_ACCESS_ASSIGNED"
    REJECTED = "REJECTED"
    FORBIDDEN = "FORBIDDEN"
    CONFLICT = "CONFLICT"
    REPLAYED = "REPLAYED"
    IDEMPOTENCY_MISMATCH = "IDEMPOTENCY_MISMATCH"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"


class AdminTariffFieldValue(BaseModel):
    """Explicit semantic field name/value pair for requested tariff data."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    field_name: str = Field(min_length=1)
    field_value: str | int | bool | None = None


class AdminActorContext(BaseModel):
    """Server-side actor facts for admin tariff-management semantics."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    actor_id: str = Field(min_length=1)
    actor_category: str = Field(min_length=1)
    authorization_scope: str = Field(min_length=1)
    authorization_reference: str = Field(min_length=1)
    audit_reference: str = Field(min_length=1)
    actor_capabilities: tuple[str, ...] = Field(default_factory=tuple)

    @model_validator(mode="after")
    def _validate_capabilities(self) -> "AdminActorContext":
        if any(not capability.strip() for capability in self.actor_capabilities):
            raise ValueError("actor capabilities must be non-empty")
        return self


class AdminTariffIdempotencyRecord(BaseModel):
    """Explicit prior idempotency evidence for deterministic replay semantics."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    command_family: AdminTariffCommandFamily
    idempotency_key: IdempotencyKey
    request_fingerprint: IdempotencyFingerprint
    terminal_outcome: AdminTariffOutcome


class _AdminTariffRequestBase(BaseModel):
    """Shared synthetic-contract inputs for EB-11 tariff boundary requests."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    actor: AdminActorContext | None = None
    required_authorization_scope: str | None = None
    semantic_draft_id: str | None = None
    target_account_id: str | None = None
    target_tariff_key: str | None = None
    target_tariff_reference: str | None = None
    approved_tariff_definition: TariffDefinition | None = None
    requested_tariff_fields: tuple[AdminTariffFieldValue, ...] = Field(default_factory=tuple)
    manual_access_scope: str | None = None
    reason: str | None = None
    idempotency_key: IdempotencyKey | None = None
    audit_reference: str | None = None
    decision_at: datetime
    current_product_policy: tuple[TariffDefinition, ...] = Field(default_factory=lambda: APPROVED_TARIFF_DEFINITIONS)
    open_decision_blockers: tuple[str, ...] = Field(default_factory=lambda: FUTURE_DECISION_GATES)
    prior_idempotency_record: AdminTariffIdempotencyRecord | None = None
    provider_evidence_reference: str | None = None
    ui_client_flag: str | None = None
    provider_username: str | None = None
    chat_title: str | None = None
    local_config_reference: str | None = None
    client_supplied_admin_flag: str | None = None
    direct_admin_write_requested: bool = False
    direct_web_write_requested: bool = False
    direct_table_write_requested: bool = False
    role_change_requested: bool = False
    mutate_historical_definition: bool = False
    delete_tariff_history: bool = False
    retire_or_disable_tariff: bool = False
    publish_ready_only: bool = False


class AdminTariffDraftRequest(_AdminTariffRequestBase):
    """Semantic request for create/edit tariff draft decisions."""

    command_family: AdminTariffCommandFamily

    @model_validator(mode="after")
    def _validate_command_family(self) -> "AdminTariffDraftRequest":
        if self.command_family not in (
            AdminTariffCommandFamily.CREATE_TARIFF_DRAFT,
            AdminTariffCommandFamily.EDIT_TARIFF_DRAFT,
        ):
            raise ValueError("draft requests must use create or edit command families")
        return self


class AdminTariffPublishRequest(_AdminTariffRequestBase):
    """Semantic request for publish tariff decisions."""

    command_family: AdminTariffCommandFamily = AdminTariffCommandFamily.PUBLISH_TARIFF_DEFINITION


class AdminTariffAssignmentRequest(_AdminTariffRequestBase):
    """Semantic request for tariff or manual-access assignment decisions."""

    command_family: AdminTariffCommandFamily

    @model_validator(mode="after")
    def _validate_command_family(self) -> "AdminTariffAssignmentRequest":
        if self.command_family not in (
            AdminTariffCommandFamily.ASSIGN_ACCOUNT_TARIFF,
            AdminTariffCommandFamily.ASSIGN_MANUAL_ACCESS,
        ):
            raise ValueError("assignment requests must use tariff or manual-access command families")
        return self


class AdminTariffRejectRequest(_AdminTariffRequestBase):
    """Semantic request for deterministic rejection/blocking decisions."""

    command_family: AdminTariffCommandFamily = AdminTariffCommandFamily.REJECT_ADMIN_TARIFF


class AdminTariffDecision(BaseModel):
    """Pure semantic decision for EB-11 tariff-management boundaries."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    command_family: AdminTariffCommandFamily
    outcome: AdminTariffOutcome
    terminal_outcome: AdminTariffOutcome
    reason_code: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    actor: AdminActorContext | None = None
    semantic_draft_id: str | None = None
    target_account_id: str | None = None
    target_tariff_key: str | None = None
    target_tariff_reference: str | None = None
    approved_tariff_name: TariffName | None = None
    manual_access_scope: str | None = None
    idempotency_key: IdempotencyKey | None = None
    request_fingerprint: IdempotencyFingerprint
    audit_reference: str | None = None
    decision_at: datetime
    current_product_policy: tuple[TariffDefinition, ...] = Field(default_factory=tuple)
    open_decision_blockers: tuple[str, ...] = Field(default_factory=tuple)
    source_references: tuple[str, ...] = Field(default_factory=tuple)
    semantic_only: bool = True
    draft_non_authoritative: bool = False
    changes_access: bool = False
    changes_subscription: bool = False
    changes_payment_or_provider: bool = False
    changes_billing_tables: bool = False
    changes_beacon_state: bool = False
    changes_scheduler_state: bool = False
    changes_notification_state: bool = False
    changes_role_state: bool = False
    history_preserved: bool = True

    @model_validator(mode="after")
    def _validate_terminal_outcome(self) -> "AdminTariffDecision":
        if self.outcome is not AdminTariffOutcome.REPLAYED and self.outcome != self.terminal_outcome:
            raise ValueError("terminal outcome must match the current outcome except for replayed decisions")
        return self


def _request_fingerprint(command_family: AdminTariffCommandFamily, request: BaseModel) -> IdempotencyFingerprint:
    return IdempotencyFingerprint(
        value=(
            f"{command_family.value}:"
            f"{request.model_dump_json(exclude={'idempotency_key', 'prior_idempotency_record', 'decision_at'})}"
        )
    )


def compute_admin_tariff_request_fingerprint(
    command_family: AdminTariffCommandFamily,
    request: BaseModel,
) -> IdempotencyFingerprint:
    """Public deterministic helper for admin tariff idempotency contracts/tests."""

    return _request_fingerprint(command_family, request)


def _build_decision(
    request: _AdminTariffRequestBase,
    *,
    command_family: AdminTariffCommandFamily,
    outcome: AdminTariffOutcome,
    reason_code: str,
    reason: str,
    terminal_outcome: AdminTariffOutcome | None = None,
    semantic_draft_id: str | None = None,
    target_account_id: str | None = None,
    target_tariff_key: str | None = None,
    target_tariff_reference: str | None = None,
    approved_tariff_name: TariffName | None = None,
    manual_access_scope: str | None = None,
    source_references: tuple[str, ...] = (),
    draft_non_authoritative: bool = False,
    changes_access: bool = False,
    changes_subscription: bool = False,
    changes_payment_or_provider: bool = False,
    changes_billing_tables: bool = False,
    changes_beacon_state: bool = False,
    changes_scheduler_state: bool = False,
    changes_notification_state: bool = False,
    changes_role_state: bool = False,
) -> AdminTariffDecision:
    return AdminTariffDecision(
        command_family=command_family,
        outcome=outcome,
        terminal_outcome=terminal_outcome or outcome,
        reason_code=reason_code,
        reason=reason,
        actor=request.actor,
        semantic_draft_id=semantic_draft_id,
        target_account_id=target_account_id,
        target_tariff_key=target_tariff_key,
        target_tariff_reference=target_tariff_reference,
        approved_tariff_name=approved_tariff_name,
        manual_access_scope=manual_access_scope,
        idempotency_key=request.idempotency_key,
        request_fingerprint=_request_fingerprint(command_family, request),
        audit_reference=request.audit_reference,
        decision_at=request.decision_at,
        current_product_policy=request.current_product_policy,
        open_decision_blockers=request.open_decision_blockers,
        source_references=source_references,
        semantic_only=True,
        draft_non_authoritative=draft_non_authoritative,
        changes_access=changes_access,
        changes_subscription=changes_subscription,
        changes_payment_or_provider=changes_payment_or_provider,
        changes_billing_tables=changes_billing_tables,
        changes_beacon_state=changes_beacon_state,
        changes_scheduler_state=changes_scheduler_state,
        changes_notification_state=changes_notification_state,
        changes_role_state=changes_role_state,
        history_preserved=True,
    )


def _has_capability(actor: AdminActorContext, capability: str) -> bool:
    return capability in actor.actor_capabilities


def _capability_forbidden(
    request: _AdminTariffRequestBase,
    *,
    command_family: AdminTariffCommandFamily,
    capability: str,
    reason_code: str,
) -> AdminTariffDecision | None:
    if request.actor is None:
        return None
    if _has_capability(request.actor, capability):
        return None
    return _build_decision(
        request,
        command_family=command_family,
        outcome=AdminTariffOutcome.FORBIDDEN,
        terminal_outcome=AdminTariffOutcome.FORBIDDEN,
        reason_code=reason_code,
        reason="The actor lacks the server-side capability required for this tariff boundary action.",
    )


def _requires_scope(request: _AdminTariffRequestBase) -> bool:
    return request.required_authorization_scope is not None


def _scope_authorized(request: _AdminTariffRequestBase) -> bool:
    if request.actor is None or request.required_authorization_scope is None:
        return False
    return request.actor.authorization_scope == request.required_authorization_scope


def _requested_fields_map(requested_tariff_fields: tuple[AdminTariffFieldValue, ...]) -> dict[str, str | int | bool | None]:
    result: dict[str, str | int | bool | None] = {}
    for field in requested_tariff_fields:
        result[field.field_name] = field.field_value
    return result


def _tariff_definition_payload(definition: TariffDefinition) -> dict[str, str | int | bool | None]:
    return {
        "tariff_name": definition.tariff_name.value,
        "semantic_version": definition.semantic_version,
        "price_rub": definition.price_rub,
        "billing_period_label": definition.billing_period_label,
        "scan_interval_floor_minutes": definition.scan_interval_floor_minutes,
        "scan_interval_step_minutes": definition.scan_interval_step_minutes,
        "active_beacon_limit": definition.active_beacon_limit,
        "feature_notes": definition.feature_notes,
        "mechanism_notes": definition.mechanism_notes,
    }


def _approved_tariff_definition(request: _AdminTariffRequestBase) -> TariffDefinition | None:
    if request.approved_tariff_definition is None:
        return None
    if request.approved_tariff_definition in request.current_product_policy:
        return request.approved_tariff_definition
    return None


def _direct_write_blocked(request: _AdminTariffRequestBase, command_family: AdminTariffCommandFamily) -> AdminTariffDecision | None:
    if request.direct_admin_write_requested or request.direct_web_write_requested or request.direct_table_write_requested:
        return _build_decision(
            request,
            command_family=command_family,
            outcome=AdminTariffOutcome.BLOCKED,
            terminal_outcome=AdminTariffOutcome.BLOCKED,
            reason_code="DIRECT_WRITE_BLOCKED",
            reason="Admin/Web direct writes into Entitlements or billing state are blocked.",
            source_references=(
                request.audit_reference or "",
                request.idempotency_key.value if request.idempotency_key is not None else "",
            ),
            changes_billing_tables=False,
            changes_subscription=False,
            changes_access=False,
            changes_payment_or_provider=False,
            changes_role_state=False,
        )
    return None


def _role_change_blocked(request: _AdminTariffRequestBase, command_family: AdminTariffCommandFamily) -> AdminTariffDecision | None:
    if request.role_change_requested:
        return _build_decision(
            request,
            command_family=command_family,
            outcome=AdminTariffOutcome.BLOCKED,
            terminal_outcome=AdminTariffOutcome.BLOCKED,
            reason_code="ROLE_CHANGING_BLOCKED",
            reason="Role changing belongs to Identity/Admin boundaries and is not implemented by Entitlements.",
            source_references=(
                request.audit_reference or "",
                request.idempotency_key.value if request.idempotency_key is not None else "",
            ),
            changes_role_state=False,
        )
    return None


def _basic_precondition_decision(
    request: _AdminTariffRequestBase,
    *,
    command_family: AdminTariffCommandFamily,
    require_account_id: bool = False,
    require_scope: bool = True,
    require_reason: bool = True,
    require_audit_reference: bool = True,
    require_idempotency: bool = True,
) -> AdminTariffDecision | None:
    if request.actor is None:
        return _build_decision(
            request,
            command_family=command_family,
            outcome=AdminTariffOutcome.UNAVAILABLE,
            terminal_outcome=AdminTariffOutcome.UNAVAILABLE,
            reason_code="ACTOR_CONTEXT_REQUIRED",
            reason="A verified server-side actor context is required before tariff boundary evaluation.",
        )

    if require_scope and not _requires_scope(request):
        return _build_decision(
            request,
            command_family=command_family,
            outcome=AdminTariffOutcome.UNAVAILABLE,
            terminal_outcome=AdminTariffOutcome.UNAVAILABLE,
            reason_code="AUTHORIZATION_SCOPE_REQUIRED",
            reason="A server-side authorization scope is required before tariff boundary evaluation.",
        )

    if require_reason and not isinstance(request.reason, str):
        return _build_decision(
            request,
            command_family=command_family,
            outcome=AdminTariffOutcome.REJECTED,
            terminal_outcome=AdminTariffOutcome.REJECTED,
            reason_code="REASON_REQUIRED",
            reason="A protected tariff mutation requires a reason.",
        )

    if require_reason and request.reason is not None and not request.reason.strip():
        return _build_decision(
            request,
            command_family=command_family,
            outcome=AdminTariffOutcome.REJECTED,
            terminal_outcome=AdminTariffOutcome.REJECTED,
            reason_code="REASON_REQUIRED",
            reason="A protected tariff mutation requires a reason.",
        )

    if require_idempotency and request.idempotency_key is None:
        return _build_decision(
            request,
            command_family=command_family,
            outcome=AdminTariffOutcome.REJECTED,
            terminal_outcome=AdminTariffOutcome.REJECTED,
            reason_code="IDEMPOTENCY_KEY_REQUIRED",
            reason="A protected tariff mutation requires an idempotency key before any effect.",
        )

    if require_audit_reference and not isinstance(request.audit_reference, str):
        return _build_decision(
            request,
            command_family=command_family,
            outcome=AdminTariffOutcome.REJECTED,
            terminal_outcome=AdminTariffOutcome.REJECTED,
            reason_code="AUDIT_REFERENCE_REQUIRED",
            reason="A protected tariff mutation requires an audit reference.",
        )

    if request.audit_reference is not None and not request.audit_reference.strip():
        return _build_decision(
            request,
            command_family=command_family,
            outcome=AdminTariffOutcome.REJECTED,
            terminal_outcome=AdminTariffOutcome.REJECTED,
            reason_code="AUDIT_REFERENCE_REQUIRED",
            reason="A protected tariff mutation requires an audit reference.",
        )

    if require_account_id and request.target_account_id is None:
        return _build_decision(
            request,
            command_family=command_family,
            outcome=AdminTariffOutcome.REJECTED,
            terminal_outcome=AdminTariffOutcome.REJECTED,
            reason_code="TARGET_ACCOUNT_ID_REQUIRED",
            reason="A protected tariff assignment requires a target account_id.",
        )

    if not _scope_authorized(request):
        return _build_decision(
            request,
            command_family=command_family,
            outcome=AdminTariffOutcome.FORBIDDEN,
            terminal_outcome=AdminTariffOutcome.FORBIDDEN,
            reason_code="AUTHORIZATION_SCOPE_FORBIDDEN",
            reason="The actor authorization scope does not cover the requested tariff boundary action.",
        )

    return None


def _idempotency_or_replay(
    request: _AdminTariffRequestBase,
    *,
    command_family: AdminTariffCommandFamily,
    terminal_outcome: AdminTariffOutcome,
    reason_code: str,
    reason: str,
    semantic_draft_id: str | None = None,
    target_account_id: str | None = None,
    target_tariff_key: str | None = None,
    target_tariff_reference: str | None = None,
    approved_tariff_name: TariffName | None = None,
    manual_access_scope: str | None = None,
    source_references: tuple[str, ...] = (),
    draft_non_authoritative: bool = False,
) -> AdminTariffDecision:
    request_fingerprint = _request_fingerprint(command_family, request)
    if request.prior_idempotency_record is None:
        return _build_decision(
            request,
            command_family=command_family,
            outcome=terminal_outcome,
            terminal_outcome=terminal_outcome,
            reason_code=reason_code,
            reason=reason,
            semantic_draft_id=semantic_draft_id,
            target_account_id=target_account_id,
            target_tariff_key=target_tariff_key,
            target_tariff_reference=target_tariff_reference,
            approved_tariff_name=approved_tariff_name,
            manual_access_scope=manual_access_scope,
            source_references=source_references,
            draft_non_authoritative=draft_non_authoritative,
        )

    if request.prior_idempotency_record.idempotency_key != request.idempotency_key:
        return _build_decision(
            request,
            command_family=command_family,
            outcome=AdminTariffOutcome.CONFLICT,
            terminal_outcome=AdminTariffOutcome.CONFLICT,
            reason_code="IDEMPOTENCY_KEY_CONFLICT",
            reason="The idempotency evidence references a different key than the current request.",
            semantic_draft_id=semantic_draft_id,
            target_account_id=target_account_id,
            target_tariff_key=target_tariff_key,
            target_tariff_reference=target_tariff_reference,
            approved_tariff_name=approved_tariff_name,
            manual_access_scope=manual_access_scope,
            source_references=source_references,
            draft_non_authoritative=draft_non_authoritative,
        )

    if request.prior_idempotency_record.request_fingerprint != request_fingerprint:
        return _build_decision(
            request,
            command_family=command_family,
            outcome=AdminTariffOutcome.IDEMPOTENCY_MISMATCH,
            terminal_outcome=AdminTariffOutcome.IDEMPOTENCY_MISMATCH,
            reason_code="IDEMPOTENCY_MISMATCH",
            reason="The same idempotency key was reused for a different request fingerprint.",
            semantic_draft_id=semantic_draft_id,
            target_account_id=target_account_id,
            target_tariff_key=target_tariff_key,
            target_tariff_reference=target_tariff_reference,
            approved_tariff_name=approved_tariff_name,
            manual_access_scope=manual_access_scope,
            source_references=source_references,
            draft_non_authoritative=draft_non_authoritative,
        )

    return _build_decision(
        request,
        command_family=command_family,
        outcome=AdminTariffOutcome.REPLAYED,
        terminal_outcome=request.prior_idempotency_record.terminal_outcome,
        reason_code="IDEMPOTENT_REPLAY",
        reason="The same idempotency key and request fingerprint replay the prior terminal outcome.",
        semantic_draft_id=semantic_draft_id,
        target_account_id=target_account_id,
        target_tariff_key=target_tariff_key,
        target_tariff_reference=target_tariff_reference,
        approved_tariff_name=approved_tariff_name,
        manual_access_scope=manual_access_scope,
        source_references=source_references,
        draft_non_authoritative=draft_non_authoritative,
    )


def evaluate_admin_tariff_draft(
    request: AdminTariffDraftRequest,
) -> AdminTariffDecision:
    """Evaluate deterministic tariff-draft semantics without side effects."""

    base = _basic_precondition_decision(request, command_family=request.command_family)
    if base is not None:
        return base

    direct_write = _direct_write_blocked(request, request.command_family)
    if direct_write is not None:
        return direct_write

    role_change = _role_change_blocked(request, request.command_family)
    if role_change is not None:
        return role_change

    capability_forbidden = _capability_forbidden(
        request,
        command_family=request.command_family,
        capability=ENTITLEMENTS_TARIFF_ADMIN,
        reason_code="TARIFF_ADMIN_CAPABILITY_REQUIRED",
    )
    if capability_forbidden is not None:
        return capability_forbidden

    if request.semantic_draft_id is None:
        return _build_decision(
            request,
            command_family=request.command_family,
            outcome=AdminTariffOutcome.REJECTED,
            terminal_outcome=AdminTariffOutcome.REJECTED,
            reason_code="SEMANTIC_DRAFT_ID_REQUIRED",
            reason="A tariff draft request requires a semantic draft id.",
        )

    if request.target_tariff_key is None:
        return _build_decision(
            request,
            command_family=request.command_family,
            outcome=AdminTariffOutcome.REJECTED,
            terminal_outcome=AdminTariffOutcome.REJECTED,
            reason_code="TARGET_TARIFF_KEY_REQUIRED",
            reason="A tariff draft request requires a target tariff key.",
        )

    if not request.requested_tariff_fields:
        return _build_decision(
            request,
            command_family=request.command_family,
            outcome=AdminTariffOutcome.REJECTED,
            terminal_outcome=AdminTariffOutcome.REJECTED,
            reason_code="REQUESTED_TARIFF_FIELDS_REQUIRED",
            reason="A tariff draft request requires explicit requested tariff fields.",
        )

    if request.mutate_historical_definition or request.delete_tariff_history or request.retire_or_disable_tariff:
        return _build_decision(
            request,
            command_family=request.command_family,
            outcome=AdminTariffOutcome.BLOCKED,
            terminal_outcome=AdminTariffOutcome.BLOCKED,
            reason_code="HISTORICAL_TARIFF_MUTATION_BLOCKED",
            reason="Historical tariff mutation, deletion or retirement is blocked.",
            semantic_draft_id=request.semantic_draft_id,
            target_tariff_key=request.target_tariff_key,
            draft_non_authoritative=True,
        )

    if request.command_family is AdminTariffCommandFamily.EDIT_TARIFF_DRAFT and request.target_tariff_reference is not None:
        return _build_decision(
            request,
            command_family=request.command_family,
            outcome=AdminTariffOutcome.BLOCKED,
            terminal_outcome=AdminTariffOutcome.BLOCKED,
            reason_code="PUBLISHED_TARIFF_EDIT_BLOCKED",
            reason="Editing an already published tariff requires an approved versioning rule and remains blocked.",
            semantic_draft_id=request.semantic_draft_id,
            target_tariff_key=request.target_tariff_key,
            target_tariff_reference=request.target_tariff_reference,
            draft_non_authoritative=True,
        )

    if request.prior_idempotency_record is not None:
        return _idempotency_or_replay(
            request,
            command_family=request.command_family,
            terminal_outcome=(
                AdminTariffOutcome.DRAFT_CREATED
                if request.command_family is AdminTariffCommandFamily.CREATE_TARIFF_DRAFT
                else AdminTariffOutcome.DRAFT_UPDATED
            ),
            reason_code=(
                "TARIFF_DRAFT_CREATED"
                if request.command_family is AdminTariffCommandFamily.CREATE_TARIFF_DRAFT
                else "TARIFF_DRAFT_UPDATED"
            ),
            reason=(
                "The tariff draft request is accepted as a non-authoritative draft."
                if request.command_family is AdminTariffCommandFamily.CREATE_TARIFF_DRAFT
                else "The tariff draft update is accepted as a non-authoritative draft."
            ),
            semantic_draft_id=request.semantic_draft_id,
            target_tariff_key=request.target_tariff_key,
            draft_non_authoritative=True,
            source_references=(
                request.semantic_draft_id,
                request.target_tariff_key,
                request.audit_reference or "",
            ),
        )

    return _build_decision(
        request,
        command_family=request.command_family,
        outcome=(
            AdminTariffOutcome.DRAFT_CREATED
            if request.command_family is AdminTariffCommandFamily.CREATE_TARIFF_DRAFT
            else AdminTariffOutcome.DRAFT_UPDATED
        ),
        terminal_outcome=(
            AdminTariffOutcome.DRAFT_CREATED
            if request.command_family is AdminTariffCommandFamily.CREATE_TARIFF_DRAFT
            else AdminTariffOutcome.DRAFT_UPDATED
        ),
        reason_code=(
            "TARIFF_DRAFT_CREATED"
            if request.command_family is AdminTariffCommandFamily.CREATE_TARIFF_DRAFT
            else "TARIFF_DRAFT_UPDATED"
        ),
        reason=(
            "The tariff draft request is accepted as a non-authoritative draft."
            if request.command_family is AdminTariffCommandFamily.CREATE_TARIFF_DRAFT
            else "The tariff draft update is accepted as a non-authoritative draft."
        ),
        semantic_draft_id=request.semantic_draft_id,
        target_tariff_key=request.target_tariff_key,
        draft_non_authoritative=True,
        source_references=(
            request.semantic_draft_id,
            request.target_tariff_key,
            request.audit_reference or "",
        ),
    )


def _publish_is_current_policy(request: AdminTariffPublishRequest) -> bool:
    approved_definition = _approved_tariff_definition(request)
    if approved_definition is None:
        return False
    if request.target_tariff_key != approved_definition.tariff_name.value:
        return False
    return _requested_fields_map(request.requested_tariff_fields) == _tariff_definition_payload(approved_definition)


def evaluate_admin_tariff_publish(
    request: AdminTariffPublishRequest,
) -> AdminTariffDecision:
    """Evaluate deterministic publish semantics without side effects."""

    base = _basic_precondition_decision(request, command_family=request.command_family)
    if base is not None:
        return base

    direct_write = _direct_write_blocked(request, request.command_family)
    if direct_write is not None:
        return direct_write

    role_change = _role_change_blocked(request, request.command_family)
    if role_change is not None:
        return role_change

    capability_forbidden = _capability_forbidden(
        request,
        command_family=request.command_family,
        capability=ENTITLEMENTS_TARIFF_ADMIN,
        reason_code="TARIFF_ADMIN_CAPABILITY_REQUIRED",
    )
    if capability_forbidden is not None:
        return capability_forbidden

    if request.target_tariff_key is None:
        return _build_decision(
            request,
            command_family=request.command_family,
            outcome=AdminTariffOutcome.REJECTED,
            terminal_outcome=AdminTariffOutcome.REJECTED,
            reason_code="TARGET_TARIFF_KEY_REQUIRED",
            reason="Publishing a tariff definition requires a target tariff key.",
        )

    if request.approved_tariff_definition is None:
        return _build_decision(
            request,
            command_family=request.command_family,
            outcome=AdminTariffOutcome.REJECTED,
            terminal_outcome=AdminTariffOutcome.REJECTED,
            reason_code="APPROVED_TARIFF_DEFINITION_REQUIRED",
            reason="Publishing requires an approved tariff definition as semantic input.",
            target_tariff_key=request.target_tariff_key,
        )

    if request.current_product_policy != APPROVED_TARIFF_DEFINITIONS:
        return _build_decision(
            request,
            command_family=request.command_family,
            outcome=AdminTariffOutcome.UNAVAILABLE,
            terminal_outcome=AdminTariffOutcome.UNAVAILABLE,
            reason_code="CURRENT_PRODUCT_POLICY_UNAVAILABLE",
            reason="The current product policy fact must be the approved Free/Basic policy.",
            target_tariff_key=request.target_tariff_key,
        )

    approved_definition = _approved_tariff_definition(request)
    if approved_definition is None:
        return _build_decision(
            request,
            command_family=request.command_family,
            outcome=AdminTariffOutcome.BLOCKED,
            terminal_outcome=AdminTariffOutcome.BLOCKED,
            reason_code="FUTURE_TARIFF_VALUES_BLOCKED",
            reason="Future tariff values, limits or defaults are blocked until separately approved.",
            target_tariff_key=request.target_tariff_key,
            target_tariff_reference=request.target_tariff_reference,
            draft_non_authoritative=False,
        )

    if request.approved_tariff_definition.tariff_name.value != request.target_tariff_key:
        return _build_decision(
            request,
            command_family=request.command_family,
            outcome=AdminTariffOutcome.CONFLICT,
            terminal_outcome=AdminTariffOutcome.CONFLICT,
            reason_code="TARIFF_KEY_CONFLICT",
            reason="The target tariff key does not match the approved tariff definition.",
            target_tariff_key=request.target_tariff_key,
            approved_tariff_name=request.approved_tariff_definition.tariff_name,
        )

    if not _publish_is_current_policy(request):
        return _build_decision(
            request,
            command_family=request.command_family,
            outcome=AdminTariffOutcome.BLOCKED,
            terminal_outcome=AdminTariffOutcome.BLOCKED,
            reason_code="FUTURE_TARIFF_VALUES_BLOCKED",
            reason="Future tariff values, limits or defaults are blocked until separately approved.",
            target_tariff_key=request.target_tariff_key,
            approved_tariff_name=request.approved_tariff_definition.tariff_name,
            source_references=(request.target_tariff_key, request.approved_tariff_definition.tariff_name.value),
        )

    if request.prior_idempotency_record is not None:
        return _idempotency_or_replay(
            request,
            command_family=request.command_family,
            terminal_outcome=(
                AdminTariffOutcome.PUBLISH_READY if request.publish_ready_only else AdminTariffOutcome.PUBLISHED
            ),
            reason_code=("PUBLISH_READY" if request.publish_ready_only else "TARIFF_PUBLISHED"),
            reason=(
                "The tariff definition is ready to publish under approved current policy."
                if request.publish_ready_only
                else "The tariff definition is published under approved current policy."
            ),
            target_tariff_key=request.target_tariff_key,
            target_tariff_reference=request.target_tariff_reference,
            approved_tariff_name=request.approved_tariff_definition.tariff_name,
            source_references=(
                request.target_tariff_key,
                request.approved_tariff_definition.tariff_name.value,
                request.audit_reference or "",
            ),
        )

    return _build_decision(
        request,
        command_family=request.command_family,
        outcome=AdminTariffOutcome.PUBLISH_READY if request.publish_ready_only else AdminTariffOutcome.PUBLISHED,
        terminal_outcome=AdminTariffOutcome.PUBLISH_READY if request.publish_ready_only else AdminTariffOutcome.PUBLISHED,
        reason_code="PUBLISH_READY" if request.publish_ready_only else "TARIFF_PUBLISHED",
        reason=(
            "The tariff definition is ready to publish under approved current policy."
            if request.publish_ready_only
            else "The tariff definition is published under approved current policy."
        ),
        target_tariff_key=request.target_tariff_key,
        target_tariff_reference=request.target_tariff_reference,
        approved_tariff_name=request.approved_tariff_definition.tariff_name,
        source_references=(
            request.target_tariff_key,
            request.approved_tariff_definition.tariff_name.value,
            request.audit_reference or "",
        ),
    )


def evaluate_admin_tariff_assignment(
    request: AdminTariffAssignmentRequest,
) -> AdminTariffDecision:
    """Evaluate deterministic tariff/manual-access assignment semantics without side effects."""

    base = _basic_precondition_decision(
        request,
        command_family=request.command_family,
        require_account_id=True,
    )
    if base is not None:
        return base

    direct_write = _direct_write_blocked(request, request.command_family)
    if direct_write is not None:
        return direct_write

    role_change = _role_change_blocked(request, request.command_family)
    if role_change is not None:
        return role_change

    if request.command_family is AdminTariffCommandFamily.ASSIGN_MANUAL_ACCESS or request.manual_access_scope is not None:
        if not _has_capability(request.actor, ENTITLEMENTS_MANUAL_ACCESS_ADMIN):
            return _build_decision(
                request,
                command_family=request.command_family,
                outcome=AdminTariffOutcome.FORBIDDEN,
                terminal_outcome=AdminTariffOutcome.FORBIDDEN,
                reason_code="MANUAL_ACCESS_ADMIN_CAPABILITY_REQUIRED",
                reason="The actor lacks ENTITLEMENTS_MANUAL_ACCESS_ADMIN.",
                target_account_id=request.target_account_id,
                manual_access_scope=request.manual_access_scope,
            )

        if request.manual_access_scope is None:
            return _build_decision(
                request,
                command_family=request.command_family,
                outcome=AdminTariffOutcome.REJECTED,
                terminal_outcome=AdminTariffOutcome.REJECTED,
                reason_code="MANUAL_ACCESS_SCOPE_REQUIRED",
                reason="Manual access assignment requires an explicit scope.",
                target_account_id=request.target_account_id,
            )

        return _idempotency_or_replay(
            request,
            command_family=request.command_family,
            terminal_outcome=AdminTariffOutcome.MANUAL_ACCESS_ASSIGNED,
            reason_code="MANUAL_ACCESS_ASSIGNED",
            reason="The manual access assignment is accepted as semantic-only input.",
            target_account_id=request.target_account_id,
            manual_access_scope=request.manual_access_scope,
            source_references=(
                request.target_account_id or "",
                request.manual_access_scope,
                request.audit_reference or "",
            ),
        )

    if request.approved_tariff_definition is None:
        return _build_decision(
            request,
            command_family=request.command_family,
            outcome=AdminTariffOutcome.REJECTED,
            terminal_outcome=AdminTariffOutcome.REJECTED,
            reason_code="APPROVED_TARIFF_DEFINITION_REQUIRED",
            reason="Account tariff assignment requires an approved tariff definition.",
            target_account_id=request.target_account_id,
        )

    if request.current_product_policy != APPROVED_TARIFF_DEFINITIONS:
        return _build_decision(
            request,
            command_family=request.command_family,
            outcome=AdminTariffOutcome.UNAVAILABLE,
            terminal_outcome=AdminTariffOutcome.UNAVAILABLE,
            reason_code="CURRENT_PRODUCT_POLICY_UNAVAILABLE",
            reason="The current product policy fact must be the approved Free/Basic policy.",
            target_account_id=request.target_account_id,
        )

    approved_definition = _approved_tariff_definition(request)
    if approved_definition is None:
        return _build_decision(
            request,
            command_family=request.command_family,
            outcome=AdminTariffOutcome.BLOCKED,
            terminal_outcome=AdminTariffOutcome.BLOCKED,
            reason_code="DRAFT_ONLY_TARIFF_BLOCKED",
            reason="Assignment to draft-only or unapproved tariffs is blocked.",
            target_account_id=request.target_account_id,
            target_tariff_key=request.target_tariff_key,
        )

    if request.target_tariff_key is not None and request.target_tariff_key != approved_definition.tariff_name.value:
        return _build_decision(
            request,
            command_family=request.command_family,
            outcome=AdminTariffOutcome.CONFLICT,
            terminal_outcome=AdminTariffOutcome.CONFLICT,
            reason_code="TARIFF_KEY_CONFLICT",
            reason="The target tariff key does not match the approved tariff definition.",
            target_account_id=request.target_account_id,
            target_tariff_key=request.target_tariff_key,
            approved_tariff_name=approved_definition.tariff_name,
        )

    if not _has_capability(request.actor, ENTITLEMENTS_TARIFF_ASSIGN_ADMIN):
        return _build_decision(
            request,
            command_family=request.command_family,
            outcome=AdminTariffOutcome.FORBIDDEN,
            terminal_outcome=AdminTariffOutcome.FORBIDDEN,
            reason_code="TARIFF_ASSIGN_ADMIN_CAPABILITY_REQUIRED",
            reason="The actor lacks ENTITLEMENTS_TARIFF_ASSIGN_ADMIN.",
            target_account_id=request.target_account_id,
            target_tariff_key=approved_definition.tariff_name.value,
            approved_tariff_name=approved_definition.tariff_name,
        )

    return _idempotency_or_replay(
        request,
        command_family=request.command_family,
        terminal_outcome=AdminTariffOutcome.ASSIGNED,
        reason_code="TARIFF_ASSIGNED",
        reason="The approved tariff assignment is accepted as semantic-only input.",
        target_account_id=request.target_account_id,
        target_tariff_key=approved_definition.tariff_name.value,
        approved_tariff_name=approved_definition.tariff_name,
        source_references=(
            request.target_account_id or "",
            approved_definition.tariff_name.value,
            request.audit_reference or "",
        ),
    )


def evaluate_admin_tariff_reject(
    request: AdminTariffRejectRequest,
) -> AdminTariffDecision:
    """Evaluate deterministic reject-command semantics without side effects."""

    base = _basic_precondition_decision(request, command_family=request.command_family, require_account_id=False)
    if base is not None:
        return base

    direct_write = _direct_write_blocked(request, request.command_family)
    if direct_write is not None:
        return direct_write

    role_change = _role_change_blocked(request, request.command_family)
    if role_change is not None:
        return role_change

    capability_forbidden = _capability_forbidden(
        request,
        command_family=request.command_family,
        capability=ENTITLEMENTS_TARIFF_ADMIN,
        reason_code="TARIFF_ADMIN_CAPABILITY_REQUIRED",
    )
    if capability_forbidden is not None:
        return capability_forbidden

    return _idempotency_or_replay(
        request,
        command_family=request.command_family,
        terminal_outcome=AdminTariffOutcome.REJECTED,
        reason_code="ADMIN_TARIFF_REJECTED",
        reason="The admin tariff request is rejected by deterministic semantic policy.",
        semantic_draft_id=request.semantic_draft_id,
        target_tariff_key=request.target_tariff_key,
        target_tariff_reference=request.target_tariff_reference,
        target_account_id=request.target_account_id,
        manual_access_scope=request.manual_access_scope,
        source_references=(
            request.audit_reference or "",
            request.idempotency_key.value if request.idempotency_key is not None else "",
        ),
    )


__all__ = [
    "AdminActorContext",
    "AdminTariffAssignmentRequest",
    "AdminTariffCapability",
    "AdminTariffCommandFamily",
    "AdminTariffDecision",
    "AdminTariffDraftRequest",
    "AdminTariffFieldValue",
    "AdminTariffIdempotencyRecord",
    "AdminTariffOutcome",
    "AdminTariffPublishRequest",
    "AdminTariffRejectRequest",
    "ENTITLEMENTS_MANUAL_ACCESS_ADMIN",
    "ENTITLEMENTS_TARIFF_ADMIN",
    "ENTITLEMENTS_TARIFF_ASSIGN_ADMIN",
    "compute_admin_tariff_request_fingerprint",
    "evaluate_admin_tariff_assignment",
    "evaluate_admin_tariff_draft",
    "evaluate_admin_tariff_publish",
    "evaluate_admin_tariff_reject",
]

"""Deterministic semantic contracts for manual access grants."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mayak.platform.idempotency import IdempotencyFingerprint, IdempotencyKey

from .contracts import EffectiveInterval

ENTITLEMENTS_MANUAL_ACCESS_ADMIN: Final[str] = "ENTITLEMENTS_MANUAL_ACCESS_ADMIN"


class ManualAccessGrantRequestKind(str, Enum):
    """Semantic request kinds for manual access lifecycle contracts."""

    CREATE = "CREATE"
    REVOKE = "REVOKE"


class ManualAccessGrantLifecycleOutcome(str, Enum):
    """Approved lifecycle outcomes for manual access semantic contracts."""

    CREATED = "CREATED"
    REPLAYED = "REPLAYED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"
    CONFLICT = "CONFLICT"
    IDEMPOTENCY_MISMATCH = "IDEMPOTENCY_MISMATCH"
    UNAUTHORIZED = "UNAUTHORIZED"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


class ManualAccessActorContext(BaseModel):
    """Server-side actor context for manual access semantic contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    actor_id: str = Field(min_length=1)
    actor_category: str = Field(min_length=1)
    authorization_scope: str = Field(min_length=1)
    authorization_reference: str = Field(min_length=1)
    audit_reference: str = Field(min_length=1)
    actor_capabilities: tuple[str, ...] = Field(default_factory=tuple)

    @model_validator(mode="after")
    def _validate_actor_capabilities(self) -> "ManualAccessActorContext":
        if any(not capability.strip() for capability in self.actor_capabilities):
            raise ValueError("actor capabilities must be non-empty")
        return self


class ManualAccessGrantIdempotencyRecord(BaseModel):
    """Explicit prior idempotency evidence for deterministic replay semantics."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    request_kind: ManualAccessGrantRequestKind
    idempotency_key: IdempotencyKey
    request_fingerprint: IdempotencyFingerprint
    terminal_outcome: ManualAccessGrantLifecycleOutcome


class ManualAccessGrantCreateRequest(BaseModel):
    """Explicit synthetic-contract input for manual access creation."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    actor: ManualAccessActorContext
    target_account_id: str = Field(min_length=1)
    capability: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    effective_interval: EffectiveInterval
    reason: str = Field(min_length=1)
    idempotency_key: IdempotencyKey | None = None
    audit_reference: str = Field(min_length=1)
    decision_at: datetime
    prior_idempotency_record: ManualAccessGrantIdempotencyRecord | None = None


class ManualAccessGrantRevokeRequest(BaseModel):
    """Explicit synthetic-contract input for manual access revocation."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    actor: ManualAccessActorContext
    grant_id: str = Field(min_length=1)
    target_account_id: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    idempotency_key: IdempotencyKey | None = None
    audit_reference: str = Field(min_length=1)
    decision_at: datetime
    prior_idempotency_record: ManualAccessGrantIdempotencyRecord | None = None


class ManualAccessGrantLifecycleDecision(BaseModel):
    """Pure semantic decision for manual access create/revoke contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    request_kind: ManualAccessGrantRequestKind
    outcome: ManualAccessGrantLifecycleOutcome
    terminal_outcome: ManualAccessGrantLifecycleOutcome
    reason_code: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    actor: ManualAccessActorContext
    target_account_id: str = Field(min_length=1)
    capability: str | None = None
    scope: str | None = None
    grant_id: str | None = None
    effective_interval: EffectiveInterval | None = None
    idempotency_key: IdempotencyKey | None = None
    request_fingerprint: IdempotencyFingerprint
    audit_reference: str = Field(min_length=1)
    decision_at: datetime
    history_preserved: bool = True

    @model_validator(mode="after")
    def _validate_terminal_outcome(self) -> "ManualAccessGrantLifecycleDecision":
        if self.outcome is not ManualAccessGrantLifecycleOutcome.REPLAYED and self.outcome != self.terminal_outcome:
            raise ValueError("terminal outcome must match the current outcome except for replayed decisions")
        return self


def _request_fingerprint(operation: ManualAccessGrantRequestKind, request: BaseModel) -> IdempotencyFingerprint:
    return IdempotencyFingerprint(
        value=(
            f"{operation.value}:"
            f"{request.model_dump_json(exclude={'idempotency_key', 'prior_idempotency_record', 'decision_at'})}"
        )
    )


def compute_manual_access_request_fingerprint(
    operation: ManualAccessGrantRequestKind,
    request: BaseModel,
) -> IdempotencyFingerprint:
    """Public deterministic helper for semantic idempotency contracts/tests."""

    return _request_fingerprint(operation, request)


def _has_admin_capability(actor: ManualAccessActorContext) -> bool:
    return ENTITLEMENTS_MANUAL_ACCESS_ADMIN in actor.actor_capabilities


def _replay_or_mismatch(
    *,
    operation: ManualAccessGrantRequestKind,
    request: BaseModel,
    request_idempotency_key: IdempotencyKey | None,
    prior_idempotency_record: ManualAccessGrantIdempotencyRecord | None,
    actor: ManualAccessActorContext,
    target_account_id: str,
    capability: str | None = None,
    scope: str | None = None,
    grant_id: str | None = None,
    effective_interval: EffectiveInterval | None = None,
    audit_reference: str,
    decision_at: datetime,
    terminal_outcome: ManualAccessGrantLifecycleOutcome,
    reason_code: str,
    reason: str,
) -> ManualAccessGrantLifecycleDecision:
    request_fingerprint = _request_fingerprint(operation, request)
    if prior_idempotency_record is None:
        return ManualAccessGrantLifecycleDecision(
            request_kind=operation,
            outcome=terminal_outcome,
            terminal_outcome=terminal_outcome,
            reason_code=reason_code,
            reason=reason,
            actor=actor,
            target_account_id=target_account_id,
            capability=capability,
            scope=scope,
            grant_id=grant_id,
            effective_interval=effective_interval,
            idempotency_key=request_idempotency_key,
            request_fingerprint=request_fingerprint,
            audit_reference=audit_reference,
            decision_at=decision_at,
            history_preserved=True,
        )

    if prior_idempotency_record.idempotency_key != request_idempotency_key:
        return ManualAccessGrantLifecycleDecision(
            request_kind=operation,
            outcome=ManualAccessGrantLifecycleOutcome.CONFLICT,
            terminal_outcome=ManualAccessGrantLifecycleOutcome.CONFLICT,
            reason_code="IDEMPOTENCY_KEY_CONFLICT",
            reason="The idempotency evidence references a different key than the current request.",
            actor=actor,
            target_account_id=target_account_id,
            capability=capability,
            scope=scope,
            grant_id=grant_id,
            effective_interval=effective_interval,
            idempotency_key=request_idempotency_key,
            request_fingerprint=request_fingerprint,
            audit_reference=audit_reference,
            decision_at=decision_at,
            history_preserved=True,
        )

    if prior_idempotency_record.request_fingerprint != request_fingerprint:
        return ManualAccessGrantLifecycleDecision(
            request_kind=operation,
            outcome=ManualAccessGrantLifecycleOutcome.IDEMPOTENCY_MISMATCH,
            terminal_outcome=ManualAccessGrantLifecycleOutcome.IDEMPOTENCY_MISMATCH,
            reason_code="IDEMPOTENCY_MISMATCH",
            reason="The same idempotency key was reused for a different request fingerprint.",
            actor=actor,
            target_account_id=target_account_id,
            capability=capability,
            scope=scope,
            grant_id=grant_id,
            effective_interval=effective_interval,
            idempotency_key=request_idempotency_key,
            request_fingerprint=request_fingerprint,
            audit_reference=audit_reference,
            decision_at=decision_at,
            history_preserved=True,
        )

    return ManualAccessGrantLifecycleDecision(
        request_kind=operation,
        outcome=ManualAccessGrantLifecycleOutcome.REPLAYED,
        terminal_outcome=prior_idempotency_record.terminal_outcome,
        reason_code="IDEMPOTENT_REPLAY",
        reason="The same idempotency key and request fingerprint replay the original terminal outcome.",
        actor=actor,
        target_account_id=target_account_id,
        capability=capability,
        scope=scope,
        grant_id=grant_id,
        effective_interval=effective_interval,
        idempotency_key=request_idempotency_key,
        request_fingerprint=request_fingerprint,
        audit_reference=audit_reference,
        decision_at=decision_at,
        history_preserved=True,
    )


def evaluate_manual_access_create(
    request: ManualAccessGrantCreateRequest,
) -> ManualAccessGrantLifecycleDecision:
    """Evaluate deterministic manual-access creation semantics without side effects."""

    if request.idempotency_key is None:
        request_fingerprint = _request_fingerprint(ManualAccessGrantRequestKind.CREATE, request)
        return ManualAccessGrantLifecycleDecision(
            request_kind=ManualAccessGrantRequestKind.CREATE,
            outcome=ManualAccessGrantLifecycleOutcome.REJECTED,
            terminal_outcome=ManualAccessGrantLifecycleOutcome.REJECTED,
            reason_code="IDEMPOTENCY_KEY_REQUIRED",
            reason="Manual access creation requires an idempotency key before any effect.",
            actor=request.actor,
            target_account_id=request.target_account_id,
            capability=request.capability,
            scope=request.scope,
            effective_interval=request.effective_interval,
            request_fingerprint=request_fingerprint,
            audit_reference=request.audit_reference,
            decision_at=request.decision_at,
            history_preserved=True,
        )

    if not _has_admin_capability(request.actor):
        request_fingerprint = _request_fingerprint(ManualAccessGrantRequestKind.CREATE, request)
        return ManualAccessGrantLifecycleDecision(
            request_kind=ManualAccessGrantRequestKind.CREATE,
            outcome=ManualAccessGrantLifecycleOutcome.UNAUTHORIZED,
            terminal_outcome=ManualAccessGrantLifecycleOutcome.UNAUTHORIZED,
            reason_code="MANUAL_ACCESS_ADMIN_CAPABILITY_REQUIRED",
            reason="The actor lacks ENTITLEMENTS_MANUAL_ACCESS_ADMIN.",
            actor=request.actor,
            target_account_id=request.target_account_id,
            capability=request.capability,
            scope=request.scope,
            effective_interval=request.effective_interval,
            idempotency_key=request.idempotency_key,
            request_fingerprint=request_fingerprint,
            audit_reference=request.audit_reference,
            decision_at=request.decision_at,
            history_preserved=True,
        )

    if request.actor.authorization_scope != request.scope:
        request_fingerprint = _request_fingerprint(ManualAccessGrantRequestKind.CREATE, request)
        return ManualAccessGrantLifecycleDecision(
            request_kind=ManualAccessGrantRequestKind.CREATE,
            outcome=ManualAccessGrantLifecycleOutcome.OUT_OF_SCOPE,
            terminal_outcome=ManualAccessGrantLifecycleOutcome.OUT_OF_SCOPE,
            reason_code="AUTHORIZATION_SCOPE_OUT_OF_SCOPE",
            reason="The actor authorization scope does not cover the requested manual access scope.",
            actor=request.actor,
            target_account_id=request.target_account_id,
            capability=request.capability,
            scope=request.scope,
            effective_interval=request.effective_interval,
            idempotency_key=request.idempotency_key,
            request_fingerprint=request_fingerprint,
            audit_reference=request.audit_reference,
            decision_at=request.decision_at,
            history_preserved=True,
        )

    request_fingerprint = _request_fingerprint(ManualAccessGrantRequestKind.CREATE, request)
    if request.prior_idempotency_record is not None:
        return _replay_or_mismatch(
            operation=ManualAccessGrantRequestKind.CREATE,
            request=request,
            request_idempotency_key=request.idempotency_key,
            prior_idempotency_record=request.prior_idempotency_record,
            actor=request.actor,
            target_account_id=request.target_account_id,
            capability=request.capability,
            scope=request.scope,
            effective_interval=request.effective_interval,
            audit_reference=request.audit_reference,
            decision_at=request.decision_at,
            terminal_outcome=ManualAccessGrantLifecycleOutcome.CREATED,
            reason_code="MANUAL_ACCESS_CREATED",
            reason="The manual access grant request is valid and becomes a created semantic grant.",
        )

    if request.decision_at >= request.effective_interval.ends_at:
        return ManualAccessGrantLifecycleDecision(
            request_kind=ManualAccessGrantRequestKind.CREATE,
            outcome=ManualAccessGrantLifecycleOutcome.EXPIRED,
            terminal_outcome=ManualAccessGrantLifecycleOutcome.EXPIRED,
            reason_code="MANUAL_ACCESS_EXPIRED",
            reason="The semantic decision time is at or after the effective interval end.",
            actor=request.actor,
            target_account_id=request.target_account_id,
            capability=request.capability,
            scope=request.scope,
            effective_interval=request.effective_interval,
            idempotency_key=request.idempotency_key,
            request_fingerprint=request_fingerprint,
            audit_reference=request.audit_reference,
            decision_at=request.decision_at,
            history_preserved=True,
        )

    return ManualAccessGrantLifecycleDecision(
        request_kind=ManualAccessGrantRequestKind.CREATE,
        outcome=ManualAccessGrantLifecycleOutcome.CREATED,
        terminal_outcome=ManualAccessGrantLifecycleOutcome.CREATED,
        reason_code="MANUAL_ACCESS_CREATED",
        reason="The manual access grant is authorized, in scope and within its effective interval.",
        actor=request.actor,
        target_account_id=request.target_account_id,
        capability=request.capability,
        scope=request.scope,
        effective_interval=request.effective_interval,
        idempotency_key=request.idempotency_key,
        request_fingerprint=request_fingerprint,
        audit_reference=request.audit_reference,
        decision_at=request.decision_at,
        history_preserved=True,
    )


def evaluate_manual_access_revoke(
    request: ManualAccessGrantRevokeRequest,
) -> ManualAccessGrantLifecycleDecision:
    """Evaluate deterministic manual-access revocation semantics without side effects."""

    if request.idempotency_key is None:
        request_fingerprint = _request_fingerprint(ManualAccessGrantRequestKind.REVOKE, request)
        return ManualAccessGrantLifecycleDecision(
            request_kind=ManualAccessGrantRequestKind.REVOKE,
            outcome=ManualAccessGrantLifecycleOutcome.REJECTED,
            terminal_outcome=ManualAccessGrantLifecycleOutcome.REJECTED,
            reason_code="IDEMPOTENCY_KEY_REQUIRED",
            reason="Manual access revocation requires an idempotency key before any effect.",
            actor=request.actor,
            target_account_id=request.target_account_id,
            grant_id=request.grant_id,
            request_fingerprint=request_fingerprint,
            audit_reference=request.audit_reference,
            decision_at=request.decision_at,
            history_preserved=True,
        )

    if not _has_admin_capability(request.actor):
        request_fingerprint = _request_fingerprint(ManualAccessGrantRequestKind.REVOKE, request)
        return ManualAccessGrantLifecycleDecision(
            request_kind=ManualAccessGrantRequestKind.REVOKE,
            outcome=ManualAccessGrantLifecycleOutcome.UNAUTHORIZED,
            terminal_outcome=ManualAccessGrantLifecycleOutcome.UNAUTHORIZED,
            reason_code="MANUAL_ACCESS_ADMIN_CAPABILITY_REQUIRED",
            reason="The actor lacks ENTITLEMENTS_MANUAL_ACCESS_ADMIN.",
            actor=request.actor,
            target_account_id=request.target_account_id,
            grant_id=request.grant_id,
            idempotency_key=request.idempotency_key,
            request_fingerprint=request_fingerprint,
            audit_reference=request.audit_reference,
            decision_at=request.decision_at,
            history_preserved=True,
        )

    request_fingerprint = _request_fingerprint(ManualAccessGrantRequestKind.REVOKE, request)
    if request.prior_idempotency_record is not None:
        return _replay_or_mismatch(
            operation=ManualAccessGrantRequestKind.REVOKE,
            request=request,
            request_idempotency_key=request.idempotency_key,
            prior_idempotency_record=request.prior_idempotency_record,
            actor=request.actor,
            target_account_id=request.target_account_id,
            grant_id=request.grant_id,
            audit_reference=request.audit_reference,
            decision_at=request.decision_at,
            terminal_outcome=ManualAccessGrantLifecycleOutcome.REVOKED,
            reason_code="MANUAL_ACCESS_REVOKED",
            reason="The manual access revocation is authorized and recorded as a semantic revoked outcome.",
        )

    return ManualAccessGrantLifecycleDecision(
        request_kind=ManualAccessGrantRequestKind.REVOKE,
        outcome=ManualAccessGrantLifecycleOutcome.REVOKED,
        terminal_outcome=ManualAccessGrantLifecycleOutcome.REVOKED,
        reason_code="MANUAL_ACCESS_REVOKED",
        reason="The manual access revocation is authorized and recorded as a semantic revoked outcome.",
        actor=request.actor,
        target_account_id=request.target_account_id,
        grant_id=request.grant_id,
        idempotency_key=request.idempotency_key,
        request_fingerprint=request_fingerprint,
        audit_reference=request.audit_reference,
        decision_at=request.decision_at,
        history_preserved=True,
    )


__all__ = [
    "ENTITLEMENTS_MANUAL_ACCESS_ADMIN",
    "ManualAccessActorContext",
    "ManualAccessGrantCreateRequest",
    "ManualAccessGrantIdempotencyRecord",
    "ManualAccessGrantLifecycleDecision",
    "ManualAccessGrantLifecycleOutcome",
    "ManualAccessGrantRequestKind",
    "ManualAccessGrantRevokeRequest",
    "compute_manual_access_request_fingerprint",
    "evaluate_manual_access_create",
    "evaluate_manual_access_revoke",
]


"""PostgreSQL identity runtime with caller-owned transactions.

This module is deliberately provider-neutral: provider adapters are responsible for
producing a verified assertion, while this boundary owns account authority.
"""

# SQL statements and safe result construction are kept visually grouped.
# noqa is limited to line wrapping; no lint rule is disabled for correctness.
# ruff: noqa: E501

from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from mayak.contracts.audit import (
    AuditActorCategory,
    AuditContext,
    AuditModuleIdentifier,
    AuditOperation,
    AuditReason,
    AuditTargetScope,
)
from mayak.contracts.idempotency import (
    IdempotencyDecision,
    IdempotencyFingerprint,
    IdempotencyScope,
)
from mayak.contracts.results import CommonOutcome, Result
from mayak.persistence.audit import PostgresAuditRepository
from mayak.persistence.idempotency import PostgresTerminalIdempotencyRepository
from mayak.persistence.metadata import metadata
from mayak.platform.correlation import CorrelationContext
from mayak.runtime.settings import MayakRuntimeSettings, RuntimeProfile

from .contracts import (
    ActorContextValidationOutcome,
    ActorContextValidationRequest,
    ActorContextValidationState,
    AuthorizationDecision,
    AuthSessionState,
    IdentityLinkChallengeOutcome,
    IdentityLinkChallengeRequest,
    IdentityLinkChallengeState,
    IdentityProvider,
    IdentityRuntimeState,
    ProviderIdentityResolutionOutcome,
    ProviderIdentityResolutionRequest,
    RoleAssignmentState,
    RoleMutationRequest,
    SafeSessionMetadata,
    SecretSessionToken,
    SessionValidationOutcome,
    SyntheticAcceptanceLoginOutcome,
    SyntheticAcceptanceLoginRequest,
    VerifiedProviderIdentity,
)

_ACCOUNTS = metadata.tables["mayak.identity_accounts"]
_LINKS = metadata.tables["mayak.identity_provider_links"]
_ROLES = metadata.tables["mayak.identity_role_assignments"]
_SESSIONS = metadata.tables["mayak.identity_sessions"]
_CHALLENGES = metadata.tables["mayak.identity_link_challenges"]
_SCOPE = IdempotencyScope(value="identity_and_access")


@dataclass(frozen=True, slots=True)
class IssuedSession:
    """Internal issuance boundary carrying the raw token for immediate transport use."""

    metadata: SafeSessionMetadata
    token: SecretSessionToken


def _now() -> datetime:
    return datetime.now(UTC)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _fingerprint(value: Any) -> IdempotencyFingerprint:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return IdempotencyFingerprint(value=_hash(encoded))


def _provider(value: IdentityProvider | str) -> str:
    return value.value if isinstance(value, IdentityProvider) else value


def _roles(session: Session, account_id: UUID) -> tuple[str, ...]:
    rows = session.execute(
        select(_ROLES.c.role_code).where(
            _ROLES.c.account_id == account_id, _ROLES.c.revoked_at.is_(None)
        )
    ).scalars()
    return tuple(sorted(set(rows)))


class IdentityRuntime:
    """Application services; every method leaves commit/rollback to its caller."""

    def __init__(self, settings: MayakRuntimeSettings | None = None) -> None:
        self.settings = settings
        self.idempotency = PostgresTerminalIdempotencyRepository()
        self.audit = PostgresAuditRepository()

    def resolve_verified_provider(
        self, session: Session, request: ProviderIdentityResolutionRequest
    ) -> ProviderIdentityResolutionOutcome:
        identity = request.identity
        if not identity.verified:
            return ProviderIdentityResolutionOutcome(
                state=IdentityRuntimeState.REJECTED, provider=identity.provider
            )
        subject = identity.provider_subject.strip()
        fingerprint = _fingerprint(
            (
                _provider(identity.provider),
                subject,
                identity.verified,
                identity.verification_reference,
            )
        )
        previous = self.idempotency.evaluate(
            session, scope=_SCOPE, key=request.idempotency_key, fingerprint=fingerprint, now=_now()
        )
        if previous.decision.decision is IdempotencyDecision.MISMATCH:
            return ProviderIdentityResolutionOutcome(
                state=IdentityRuntimeState.CONFLICT, provider=identity.provider
            )
        if previous.outcome is not None:
            account = UUID(previous.outcome.details[0])
            return ProviderIdentityResolutionOutcome(
                state=IdentityRuntimeState.REPLAYED, account_id=account, provider=identity.provider
            )
        row = session.execute(
            select(_LINKS.c.account_id).where(
                _LINKS.c.provider_code == _provider(identity.provider),
                _LINKS.c.provider_subject == subject,
            )
        ).scalar_one_or_none()
        created = row is None
        if row is None:
            account = uuid4()
            now = _now()
            session.execute(
                _ACCOUNTS.insert().values(
                    id=account, state="ACTIVE", phone=None, created_at=now, updated_at=now
                )
            )
            try:
                with session.begin_nested():
                    session.execute(
                        _LINKS.insert().values(
                            id=uuid4(),
                            account_id=account,
                            provider_code=_provider(identity.provider),
                            provider_subject=subject,
                            state="VERIFIED",
                            created_at=now,
                            updated_at=now,
                        )
                    )
            except IntegrityError:
                row = session.execute(
                    select(_LINKS.c.account_id).where(
                        _LINKS.c.provider_code == _provider(identity.provider),
                        _LINKS.c.provider_subject == subject,
                    )
                ).scalar_one()
                session.execute(_ACCOUNTS.delete().where(_ACCOUNTS.c.id == account))
                account = row
        else:
            account = row
        outcome = CommonOutcome(
            result=Result.SUCCEEDED, reason_code="IDENTITY_RESOLVED", details=(str(account),)
        )
        recorded = self.idempotency.record_terminal(
            session,
            record_id=uuid4(),
            scope=_SCOPE,
            key=request.idempotency_key,
            fingerprint=fingerprint,
            outcome=outcome,
            created_at=_now(),
            expires_at=_now() + timedelta(days=14),
            now=_now(),
        )
        if recorded.decision.decision is IdempotencyDecision.MISMATCH:
            return ProviderIdentityResolutionOutcome(
                state=IdentityRuntimeState.CONFLICT, provider=identity.provider
            )
        self._audit(session, None, request.correlation, "IDENTITY_RESOLVE", "account", account)
        return ProviderIdentityResolutionOutcome(
            state=IdentityRuntimeState.CREATED if created else IdentityRuntimeState.RESOLVED,
            account_id=account,
            provider=identity.provider,
        )

    def synthetic_login(
        self, session: Session, request: SyntheticAcceptanceLoginRequest
    ) -> tuple[SyntheticAcceptanceLoginOutcome, IssuedSession | None]:
        if (
            self.settings is None
            or self.settings.runtime.profile is not RuntimeProfile.SYNTHETIC_ACCEPTANCE
        ):
            return SyntheticAcceptanceLoginOutcome(state=IdentityRuntimeState.DISABLED), None
        if not self.settings.session.synthetic_identity_enabled:
            return SyntheticAcceptanceLoginOutcome(state=IdentityRuntimeState.DISABLED), None
        assertion = VerifiedProviderIdentity(
            provider="SYNTHETIC_ACCEPTANCE",
            provider_subject=request.synthetic_subject,
            verified=True,
            verification_reference="synthetic-acceptance",
        )
        resolved = self.resolve_verified_provider(
            session,
            ProviderIdentityResolutionRequest(
                identity=assertion,
                idempotency_key=request.idempotency_key,
                correlation=request.correlation,
            ),
        )
        if resolved.account_id is None:
            return SyntheticAcceptanceLoginOutcome(state=resolved.state), None
        issued = self.issue_session(session, resolved.account_id)
        return SyntheticAcceptanceLoginOutcome(
            state=resolved.state, account_id=resolved.account_id, session=issued.metadata
        ), issued

    def issue_session(self, session: Session, account_id: UUID) -> IssuedSession:
        ttl = self.settings.session.max_age_seconds if self.settings else 86_400
        raw = secrets.token_urlsafe(32)
        now = _now()
        expiry = now + timedelta(seconds=min(ttl, 86_400))
        sid = uuid4()
        session.execute(
            _SESSIONS.insert().values(
                id=sid,
                account_id=account_id,
                token_hash=_hash(raw),
                issued_at=now,
                expires_at=expiry,
                revoked_at=None,
                created_at=now,
            )
        )
        return IssuedSession(
            SafeSessionMetadata(
                session_id=sid, account_id=account_id, issued_at=now, expires_at=expiry,
                state=AuthSessionState.ISSUED,
            ),
            SecretSessionToken(raw),
        )

    def validate_session(
        self, session: Session, token: SecretSessionToken
    ) -> SessionValidationOutcome:
        row = (
            session.execute(select(_SESSIONS).where(_SESSIONS.c.token_hash == _hash(token.value)))
            .mappings()
            .one_or_none()
        )
        if row is None:
            return SessionValidationOutcome(state=AuthSessionState.INVALID)
        state = (
            AuthSessionState.REVOKED
            if row["revoked_at"] is not None
            else (AuthSessionState.EXPIRED if row["expires_at"] <= _now() else AuthSessionState.ACTIVE)
        )
        meta = SafeSessionMetadata(
            session_id=row["id"], account_id=row["account_id"], issued_at=row["issued_at"],
            expires_at=row["expires_at"], state=state,
        )
        return SessionValidationOutcome(
            state=state, metadata=meta,
            account_id=row["account_id"] if state is AuthSessionState.ACTIVE else None,
        )

    def revoke_session(self, session: Session, token: SecretSessionToken) -> bool:
        result = session.execute(
            update(_SESSIONS)
            .where(_SESSIONS.c.token_hash == _hash(token.value), _SESSIONS.c.revoked_at.is_(None))
            .values(revoked_at=_now(), row_version=_SESSIONS.c.row_version + 1)
        )
        return bool(getattr(result, "rowcount", 0))

    def validate_actor(
        self, session: Session, request: ActorContextValidationRequest, token: SecretSessionToken
    ) -> ActorContextValidationOutcome:
        validated = self.validate_session(session, token)
        if validated.account_id is None:
            return ActorContextValidationOutcome(
                state=ActorContextValidationState.UNAUTHENTICATED,
                target_account_id=request.target_account_id,
            )
        if validated.account_id != request.target_account_id:
            return ActorContextValidationOutcome(
                state=ActorContextValidationState.FORBIDDEN,
                actor_account_id=validated.account_id,
                target_account_id=request.target_account_id,
            )
        return ActorContextValidationOutcome(
            state=ActorContextValidationState.VERIFIED,
            actor_account_id=validated.account_id,
            target_account_id=request.target_account_id,
            roles=_roles(session, validated.account_id),
        )

    def authorize(
        self, session: Session, actor_account_id: UUID, target_account_id: UUID
    ) -> AuthorizationDecision:
        allowed = actor_account_id == target_account_id
        return AuthorizationDecision(
            allowed=allowed,
            reason_code="SELF_ACCESS_ALLOWED" if allowed else "CROSS_ACCOUNT_FORBIDDEN",
            actor_account_id=actor_account_id,
            target_account_id=target_account_id,
        )

    def mutate_role(
        self, session: Session, request: RoleMutationRequest, *, revoke: bool = False
    ) -> RoleAssignmentState:
        if request.role_code not in {"SUPPORT", "ADMIN"}:
            return RoleAssignmentState.REJECTED
        if "ADMIN" not in _roles(session, request.actor_account_id):
            return RoleAssignmentState.REJECTED
        active = session.execute(
            select(_ROLES.c.id).where(
                _ROLES.c.account_id == request.target_account_id,
                _ROLES.c.role_code == request.role_code,
                _ROLES.c.revoked_at.is_(None),
            )
        ).scalar_one_or_none()
        now = _now()
        if revoke:
            if active is None:
                return RoleAssignmentState.UNCHANGED
            session.execute(update(_ROLES).where(_ROLES.c.id == active).values(revoked_at=now))
            state = RoleAssignmentState.REVOKED
        else:
            if active is not None:
                return RoleAssignmentState.UNCHANGED
            session.execute(
                _ROLES.insert().values(
                    id=uuid4(),
                    account_id=request.target_account_id,
                    role_code=request.role_code,
                    assigned_by_account_id=request.actor_account_id,
                    reason=request.reason,
                    created_at=now,
                )
            )
            state = RoleAssignmentState.ASSIGNED
        self._audit(
            session,
            request.actor_account_id,
            request.correlation,
            "ROLE_MUTATION",
            "account",
            request.target_account_id,
        )
        return state

    def start_link_challenge(
        self, session: Session, request: IdentityLinkChallengeRequest
    ) -> tuple[IdentityLinkChallengeOutcome, SecretSessionToken | None]:
        ttl = self.settings.session.link_challenge_ttl_seconds if self.settings else 900
        raw = secrets.token_urlsafe(32)
        now = _now()
        cid = uuid4()
        session.execute(
            _CHALLENGES.insert().values(
                id=cid,
                account_id=request.actor_account_id,
                challenge_hash=_hash(raw),
                provider_code=_provider(request.target_provider),
                expires_at=now + timedelta(seconds=min(ttl, 900)),
                consumed_at=None,
                created_at=now,
            )
        )
        return IdentityLinkChallengeOutcome(
            state=IdentityLinkChallengeState.CREATED,
            challenge_id=cid,
            account_id=request.actor_account_id,
            target_provider=request.target_provider,
        ), SecretSessionToken(raw)

    def complete_link_challenge(
        self, session: Session, challenge: SecretSessionToken, assertion: VerifiedProviderIdentity
    ) -> IdentityLinkChallengeState:
        row = (
            session.execute(
                select(_CHALLENGES).where(_CHALLENGES.c.challenge_hash == _hash(challenge.value))
            )
            .mappings()
            .one_or_none()
        )
        if row is None or row["consumed_at"] is not None:
            return IdentityLinkChallengeState.REPLAYED
        if row["expires_at"] <= _now():
            return IdentityLinkChallengeState.EXPIRED
        provider_code = _provider(assertion.provider)
        if not assertion.verified or provider_code != row["provider_code"]:
            return IdentityLinkChallengeState.REJECTED
        existing = session.execute(
            select(_LINKS.c.account_id).where(
                _LINKS.c.provider_code == provider_code,
                _LINKS.c.provider_subject == assertion.provider_subject.strip(),
            )
        ).scalar_one_or_none()
        if existing is not None:
            return (
                IdentityLinkChallengeState.REPLAYED
                if existing == row["account_id"]
                else IdentityLinkChallengeState.FOREIGN_ACCOUNT_REJECTED
            )
        now = _now()
        session.execute(
            _LINKS.insert().values(
                id=uuid4(),
                account_id=row["account_id"],
                provider_code=provider_code,
                provider_subject=assertion.provider_subject.strip(),
                state="VERIFIED",
                created_at=now,
                updated_at=now,
            )
        )
        session.execute(
            update(_CHALLENGES)
            .where(_CHALLENGES.c.id == row["id"], _CHALLENGES.c.consumed_at.is_(None))
            .values(consumed_at=now, row_version=_CHALLENGES.c.row_version + 1)
        )
        return IdentityLinkChallengeState.COMPLETED

    def _audit(
        self,
        session: Session,
        actor: UUID | None,
        correlation: CorrelationContext,
        operation: str,
        target_type: str,
        target: UUID,
    ) -> None:
        context = AuditContext(
            actor_category=AuditActorCategory.REDACTED
            if actor is None
            else AuditActorCategory.OPERATOR,
            operation=AuditOperation(value=operation),
            module_id=AuditModuleIdentifier(value="02-identity-and-access"),
            target_scope=AuditTargetScope(value=target_type),
            reason=AuditReason(value="identity runtime command"),
            details=("safe-reference-only",),
            correlation=correlation,
        )
        self.audit.append(
            session,
            entry_id=uuid4(),
            actor_account_id=actor,
            context=context,
            target_id=str(target),
            created_at=_now(),
        )


__all__ = ["IdentityRuntime", "IssuedSession"]

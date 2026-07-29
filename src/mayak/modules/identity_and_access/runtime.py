"""Identity runtime: untrusted claims in, server-established authority out.

This module owns the database transaction boundary.  Provider adapters implement
``ProviderIdentityVerifier``; they do not get to construct a verified assertion.
"""

from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Literal, Protocol
from uuid import UUID, uuid4

from sqlalchemy import select, text, update
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
    AdminRecoveryRequest,
    AdminRecoveryState,
    AuthSessionState,
    IdentityLinkChallengeOutcome,
    IdentityLinkChallengeRequest,
    IdentityLinkChallengeState,
    IdentityProvider,
    IdentityRuntimeState,
    ProviderIdentityClaim,
    ProviderIdentityResolutionOutcome,
    ProviderIdentityResolutionRequest,
    RoleAssignmentState,
    RoleMutationRequest,
    SafeSessionMetadata,
    SessionValidationOutcome,
    SyntheticAcceptanceLoginOutcome,
    SyntheticAcceptanceLoginRequest,
)

_ACCOUNTS = metadata.tables["mayak.identity_accounts"]
_LINKS = metadata.tables["mayak.identity_provider_links"]
_ROLES = metadata.tables["mayak.identity_role_assignments"]
_SESSIONS = metadata.tables["mayak.identity_sessions"]
_CHALLENGES = metadata.tables["mayak.identity_link_challenges"]
_SCOPE = IdempotencyScope(value="identity_and_access")


class ProviderIdentityVerifier(Protocol):
    """Runtime port for server-side verification of a normalized claim."""

    def verify(self, claim: ProviderIdentityClaim) -> "ProviderVerificationOutcome": ...


@dataclass(frozen=True, slots=True)
class ProviderVerificationOutcome:
    status: Literal["VERIFIED", "REJECTED", "AMBIGUOUS"]
    provider: IdentityProvider | None = None
    subject: str | None = None
    reference: str = ""


class FakeProviderIdentityVerifier:
    """Deterministic test verifier; no SDK, network, or raw provider payload."""

    def __init__(
        self,
        outcomes: dict[tuple[IdentityProvider, str], ProviderVerificationOutcome] | None = None,
    ) -> None:
        self.outcomes = outcomes or {}
        self.calls: list[ProviderIdentityClaim] = []

    def verify(self, claim: ProviderIdentityClaim) -> ProviderVerificationOutcome:
        self.calls.append(claim)
        return self.outcomes.get(
            (claim.provider, claim.provider_subject.strip()),
            ProviderVerificationOutcome(
                "VERIFIED", claim.provider, claim.provider_subject.strip(), "fake-reference"
            ),
        )


@dataclass(frozen=True, slots=True)
class _RawSecret:
    _material: str

    def reveal(self) -> str:
        return self._material

    def __repr__(self) -> str:
        return "_RawSecret(<redacted>)"

    def __str__(self) -> str:
        return "<redacted>"


@dataclass(frozen=True, slots=True)
class _IssuedSession:
    metadata: SafeSessionMetadata
    token: _RawSecret


def _now() -> datetime:
    return datetime.now(UTC)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _fingerprint(value: Any) -> IdempotencyFingerprint:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return IdempotencyFingerprint(value=_hash(encoded))


def _roles(session: Session, account_id: UUID) -> tuple[str, ...]:
    return tuple(
        sorted(
            set(
                session.execute(
                    select(_ROLES.c.role_code).where(
                        _ROLES.c.account_id == account_id, _ROLES.c.revoked_at.is_(None)
                    )
                ).scalars()
            )
        )
    )


class IdentityRuntime:
    """Protected application commands; callers own commit and rollback."""

    def __init__(
        self,
        settings: MayakRuntimeSettings | None = None,
        verifier: ProviderIdentityVerifier | None = None,
    ) -> None:
        self.settings = settings
        self.verifier = verifier
        self.idempotency = PostgresTerminalIdempotencyRepository()
        self.audit = PostgresAuditRepository()

    def _terminal(
        self,
        session: Session,
        key: Any,
        fingerprint: IdempotencyFingerprint,
        outcome: CommonOutcome,
    ) -> tuple[bool, CommonOutcome | None]:
        decision = self.idempotency.evaluate(
            session, scope=_SCOPE, key=key, fingerprint=fingerprint, now=_now()
        )
        if decision.decision.decision is IdempotencyDecision.MISMATCH:
            return False, None
        if decision.outcome is not None:
            return False, decision.outcome
        recorded = self.idempotency.record_terminal(
            session,
            record_id=uuid4(),
            scope=_SCOPE,
            key=key,
            fingerprint=fingerprint,
            outcome=outcome,
            created_at=_now(),
            expires_at=_now() + timedelta(days=14),
            now=_now(),
        )
        if recorded.outcome is not None:
            return False, recorded.outcome
        return recorded.decision.decision is IdempotencyDecision.NEW, None

    def _verified(self, claim: ProviderIdentityClaim) -> ProviderVerificationOutcome:
        if self.verifier is None:
            return ProviderVerificationOutcome("REJECTED")
        result = self.verifier.verify(claim)
        if result.status != "VERIFIED" or result.provider not in (
            IdentityProvider.TELEGRAM,
            IdentityProvider.MAX,
        ):
            return result
        if not result.subject or len(result.subject.strip()) > 255 or not result.reference:
            return ProviderVerificationOutcome("REJECTED")
        return ProviderVerificationOutcome(
            "VERIFIED", result.provider, result.subject.strip(), result.reference
        )

    def resolve_provider(
        self, session: Session, request: ProviderIdentityResolutionRequest
    ) -> ProviderIdentityResolutionOutcome:
        claim = request.identity
        verified = self._verified(claim)
        if verified.status != "VERIFIED" or verified.provider is None or verified.subject is None:
            state = (
                IdentityRuntimeState.REJECTED
                if verified.status == "REJECTED"
                else IdentityRuntimeState.CONFLICT
            )
            return ProviderIdentityResolutionOutcome(state=state, provider=claim.provider)
        provider, subject = verified.provider, verified.subject
        fingerprint = _fingerprint((provider.value, subject, verified.reference))
        previous = self.idempotency.evaluate(
            session, scope=_SCOPE, key=request.idempotency_key, fingerprint=fingerprint, now=_now()
        )
        if previous.decision.decision is IdempotencyDecision.MISMATCH:
            return ProviderIdentityResolutionOutcome(
                state=IdentityRuntimeState.CONFLICT, provider=provider
            )
        if previous.outcome is not None:
            return ProviderIdentityResolutionOutcome(
                state=IdentityRuntimeState.REPLAYED,
                account_id=UUID(previous.outcome.details[0]),
                provider=provider,
            )
        row = session.execute(
            select(_LINKS.c.account_id).where(
                _LINKS.c.provider_code == provider.value, _LINKS.c.provider_subject == subject
            )
        ).scalar_one_or_none()
        created = False
        if row is None:
            account = uuid4()
            created = True
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
                            provider_code=provider.value,
                            provider_subject=subject,
                            state="VERIFIED",
                            created_at=now,
                            updated_at=now,
                        )
                    )
            except IntegrityError:
                row = session.execute(
                    select(_LINKS.c.account_id).where(
                        _LINKS.c.provider_code == provider.value,
                        _LINKS.c.provider_subject == subject,
                    )
                ).scalar_one()
                session.execute(_ACCOUNTS.delete().where(_ACCOUNTS.c.id == account))
                account = row
                created = False
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
                state=IdentityRuntimeState.CONFLICT, provider=provider
            )
        self._audit(session, None, request.correlation, "IDENTITY_RESOLVE", "account", account)
        return ProviderIdentityResolutionOutcome(
            state=IdentityRuntimeState.CREATED if created else IdentityRuntimeState.RESOLVED,
            account_id=account,
            provider=provider,
        )

    # Compatibility name accepts a claim only; it no longer accepts an assertion.
    resolve_verified_provider = resolve_provider

    def synthetic_login(
        self, session: Session, request: SyntheticAcceptanceLoginRequest
    ) -> tuple[SyntheticAcceptanceLoginOutcome, _IssuedSession | None]:
        if (
            self.settings is None
            or self.settings.runtime.profile is not RuntimeProfile.SYNTHETIC_ACCEPTANCE
            or not self.settings.session.synthetic_identity_enabled
        ):
            return SyntheticAcceptanceLoginOutcome(state=IdentityRuntimeState.DISABLED), None
        fingerprint = _fingerprint(("SYNTHETIC_ACCEPTANCE", request.synthetic_subject.strip()))
        previous = self.idempotency.evaluate(
            session, scope=_SCOPE, key=request.idempotency_key, fingerprint=fingerprint, now=_now()
        )
        if previous.decision.decision is IdempotencyDecision.MISMATCH:
            return SyntheticAcceptanceLoginOutcome(state=IdentityRuntimeState.CONFLICT), None
        if previous.outcome is not None:
            return SyntheticAcceptanceLoginOutcome(
                state=IdentityRuntimeState.REPLAYED,
                account_id=UUID(previous.outcome.details[0]),
                session=None,
            ), None
        claim_provider = "SYNTHETIC_ACCEPTANCE"
        subject = request.synthetic_subject.strip()
        account = session.execute(
            select(_LINKS.c.account_id).where(
                _LINKS.c.provider_code == claim_provider, _LINKS.c.provider_subject == subject
            )
        ).scalar_one_or_none()
        if account is None:
            account = uuid4()
            now = _now()
            session.execute(
                _ACCOUNTS.insert().values(
                    id=account, state="ACTIVE", phone=None, created_at=now, updated_at=now
                )
            )
            session.execute(
                _LINKS.insert().values(
                    id=uuid4(),
                    account_id=account,
                    provider_code=claim_provider,
                    provider_subject=subject,
                    state="VERIFIED",
                    created_at=now,
                    updated_at=now,
                )
            )
        issued = self.issue_session(session, account)
        self.idempotency.record_terminal(
            session,
            record_id=uuid4(),
            scope=_SCOPE,
            key=request.idempotency_key,
            fingerprint=fingerprint,
            outcome=CommonOutcome(
                result=Result.SUCCEEDED, reason_code="SYNTHETIC_LOGIN", details=(str(account),)
            ),
            created_at=_now(),
            expires_at=_now() + timedelta(days=14),
            now=_now(),
        )
        self._audit(session, None, request.correlation, "SYNTHETIC_LOGIN", "account", account)
        return SyntheticAcceptanceLoginOutcome(
            state=IdentityRuntimeState.CREATED, account_id=account, session=issued.metadata
        ), issued

    def issue_session(self, session: Session, account_id: UUID) -> _IssuedSession:
        account = session.execute(
            select(_ACCOUNTS.c.id).where(
                _ACCOUNTS.c.id == account_id, _ACCOUNTS.c.state == "ACTIVE"
            )
        ).scalar_one_or_none()
        if account is None:
            raise ValueError("active account required")
        ttl = min(self.settings.session.max_age_seconds if self.settings else 86_400, 86_400)
        raw = secrets.token_urlsafe(32)
        now = _now()
        expiry = now + timedelta(seconds=ttl)
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
        return _IssuedSession(
            SafeSessionMetadata(
                session_id=sid,
                account_id=account_id,
                issued_at=now,
                expires_at=expiry,
                state=AuthSessionState.ISSUED,
            ),
            _RawSecret(raw),
        )

    def validate_session(self, session: Session, token: _RawSecret) -> SessionValidationOutcome:
        row = (
            session.execute(
                select(_SESSIONS).where(_SESSIONS.c.token_hash == _hash(token.reveal()))
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return SessionValidationOutcome(state=AuthSessionState.INVALID)
        state = (
            AuthSessionState.REVOKED
            if row["revoked_at"] is not None
            else (
                AuthSessionState.EXPIRED if row["expires_at"] <= _now() else AuthSessionState.ACTIVE
            )
        )
        meta = SafeSessionMetadata(
            session_id=row["id"],
            account_id=row["account_id"],
            issued_at=row["issued_at"],
            expires_at=row["expires_at"],
            state=state,
        )
        return SessionValidationOutcome(
            state=state,
            metadata=meta,
            account_id=row["account_id"] if state is AuthSessionState.ACTIVE else None,
        )

    def _actor(
        self, session: Session, token: _RawSecret, expected_session: UUID | None = None
    ) -> UUID | None:
        validation = self.validate_session(session, token)
        if validation.account_id is None or (
            expected_session is not None
            and validation.metadata is not None
            and validation.metadata.session_id != expected_session
        ):
            return None
        return validation.account_id

    def revoke_my_session(
        self,
        session: Session,
        token: _RawSecret,
        *,
        idempotency_key: Any,
        correlation: CorrelationContext,
    ) -> AuthSessionState:
        actor = self._actor(session, token)
        fingerprint = _fingerprint(("self-revoke", str(actor)))
        if actor is None:
            return AuthSessionState.INVALID
        previous = self.idempotency.evaluate(
            session, scope=_SCOPE, key=idempotency_key, fingerprint=fingerprint, now=_now()
        )
        if previous.decision.decision is IdempotencyDecision.MISMATCH:
            return AuthSessionState.INVALID
        if previous.outcome is not None:
            return AuthSessionState.REVOKED
        session.execute(
            update(_SESSIONS)
            .where(
                _SESSIONS.c.token_hash == _hash(token.reveal()), _SESSIONS.c.revoked_at.is_(None)
            )
            .values(revoked_at=_now(), row_version=_SESSIONS.c.row_version + 1)
        )
        self.idempotency.record_terminal(
            session,
            record_id=uuid4(),
            scope=_SCOPE,
            key=idempotency_key,
            fingerprint=fingerprint,
            outcome=CommonOutcome(result=Result.SUCCEEDED, reason_code="SESSION_REVOKED"),
            created_at=_now(),
            expires_at=_now() + timedelta(days=14),
            now=_now(),
        )
        self._audit(session, actor, correlation, "SESSION_REVOKE", "account", actor)
        return AuthSessionState.REVOKED

    def mutate_role(
        self,
        session: Session,
        request: RoleMutationRequest,
        token: _RawSecret,
        *,
        revoke: bool = False,
    ) -> RoleAssignmentState:
        actor = self._actor(session, token, request.session_id)
        if (
            actor is None
            or request.role_code not in {"SUPPORT", "ADMIN"}
            or "ADMIN" not in _roles(session, actor)
        ):
            return RoleAssignmentState.REJECTED
        fingerprint = _fingerprint(
            ("role", str(request.target_account_id), request.role_code, request.reason, revoke)
        )
        previous = self.idempotency.evaluate(
            session,
            scope=_SCOPE,
            key=request.idempotency_key,
            fingerprint=fingerprint,
            now=_now(),
        )
        if previous.decision.decision is IdempotencyDecision.MISMATCH:
            return RoleAssignmentState.CONFLICT
        if previous.outcome is not None:
            return RoleAssignmentState(previous.outcome.details[0])
        if (
            session.execute(
                select(_ACCOUNTS.c.id).where(
                    _ACCOUNTS.c.id == request.target_account_id, _ACCOUNTS.c.state == "ACTIVE"
                )
            ).scalar_one_or_none()
            is None
        ):
            return RoleAssignmentState.REJECTED
        active = session.execute(
            select(_ROLES.c.id).where(
                _ROLES.c.account_id == request.target_account_id,
                _ROLES.c.role_code == request.role_code,
                _ROLES.c.revoked_at.is_(None),
            )
        ).scalar_one_or_none()
        state = RoleAssignmentState.UNCHANGED
        if revoke and active is not None:
            session.execute(update(_ROLES).where(_ROLES.c.id == active).values(revoked_at=_now()))
            state = RoleAssignmentState.REVOKED
        elif not revoke and active is None:
            session.execute(
                _ROLES.insert().values(
                    id=uuid4(),
                    account_id=request.target_account_id,
                    role_code=request.role_code,
                    assigned_by_account_id=actor,
                    reason=request.reason,
                    created_at=_now(),
                )
            )
            state = RoleAssignmentState.ASSIGNED
        self.idempotency.record_terminal(
            session,
            record_id=uuid4(),
            scope=_SCOPE,
            key=request.idempotency_key,
            fingerprint=fingerprint,
            outcome=CommonOutcome(
                result=Result.SUCCEEDED,
                reason_code="ROLE_MUTATION",
                details=(state.value,),
            ),
            created_at=_now(),
            expires_at=_now() + timedelta(days=14),
            now=_now(),
        )
        self._audit(
            session,
            actor,
            request.correlation,
            "ROLE_MUTATION",
            "account",
            request.target_account_id,
        )
        return state

    def start_link_challenge(
        self, session: Session, request: IdentityLinkChallengeRequest, token: _RawSecret
    ) -> tuple[IdentityLinkChallengeOutcome, _RawSecret | None]:
        actor = self._actor(session, token, request.session_id)
        if actor is None:
            return IdentityLinkChallengeOutcome(
                state=IdentityLinkChallengeState.REJECTED, target_provider=request.target_provider
            ), None
        fingerprint = _fingerprint(("link-start", str(actor), request.target_provider.value))
        previous = self.idempotency.evaluate(
            session,
            scope=_SCOPE,
            key=request.idempotency_key,
            fingerprint=fingerprint,
            now=_now(),
        )
        if previous.decision.decision is IdempotencyDecision.MISMATCH:
            return IdentityLinkChallengeOutcome(
                state=IdentityLinkChallengeState.BLOCKED,
                target_provider=request.target_provider,
            ), None
        if previous.outcome is not None:
            return IdentityLinkChallengeOutcome(
                state=IdentityLinkChallengeState.REPLAYED,
                challenge_id=UUID(previous.outcome.details[0]),
                account_id=actor,
                target_provider=request.target_provider,
            ), None
        raw = secrets.token_urlsafe(32)
        now = _now()
        cid = uuid4()
        ttl = min(self.settings.session.link_challenge_ttl_seconds if self.settings else 900, 900)
        session.execute(
            _CHALLENGES.insert().values(
                id=cid,
                account_id=actor,
                challenge_hash=_hash(raw),
                provider_code=request.target_provider.value,
                expires_at=now + timedelta(seconds=ttl),
                consumed_at=None,
                created_at=now,
            )
        )
        self.idempotency.record_terminal(
            session,
            record_id=uuid4(),
            scope=_SCOPE,
            key=request.idempotency_key,
            fingerprint=fingerprint,
            outcome=CommonOutcome(
                result=Result.SUCCEEDED,
                reason_code="LINK_CHALLENGE_STARTED",
                details=(str(cid),),
            ),
            created_at=_now(),
            expires_at=_now() + timedelta(days=14),
            now=_now(),
        )
        self._audit(session, actor, request.correlation, "LINK_CHALLENGE_START", "account", actor)
        return IdentityLinkChallengeOutcome(
            state=IdentityLinkChallengeState.CREATED,
            challenge_id=cid,
            account_id=actor,
            target_provider=request.target_provider,
        ), _RawSecret(raw)

    def complete_link_challenge(
        self,
        session: Session,
        challenge: _RawSecret,
        claim: ProviderIdentityClaim,
        *,
        idempotency_key: Any,
        correlation: CorrelationContext,
    ) -> IdentityLinkChallengeState:
        verified = self._verified(claim)
        if verified.status != "VERIFIED" or verified.provider is None or verified.subject is None:
            return IdentityLinkChallengeState.REJECTED
        row = (
            session.execute(
                select(_CHALLENGES)
                .where(_CHALLENGES.c.challenge_hash == _hash(challenge.reveal()))
                .with_for_update()
            )
            .mappings()
            .one_or_none()
        )
        if row is None or row["consumed_at"] is not None:
            return IdentityLinkChallengeState.REPLAYED
        if row["expires_at"] <= _now() or verified.provider.value != row["provider_code"]:
            return (
                IdentityLinkChallengeState.EXPIRED
                if row["expires_at"] <= _now()
                else IdentityLinkChallengeState.REJECTED
            )
        existing = session.execute(
            select(_LINKS.c.account_id).where(
                _LINKS.c.provider_code == verified.provider.value,
                _LINKS.c.provider_subject == verified.subject,
            )
        ).scalar_one_or_none()
        if existing is not None:
            return (
                IdentityLinkChallengeState.REPLAYED
                if existing == row["account_id"]
                else IdentityLinkChallengeState.FOREIGN_ACCOUNT_REJECTED
            )
        now = _now()
        try:
            session.execute(
                _LINKS.insert().values(
                    id=uuid4(),
                    account_id=row["account_id"],
                    provider_code=verified.provider.value,
                    provider_subject=verified.subject,
                    state="VERIFIED",
                    created_at=now,
                    updated_at=now,
                )
            )
        except IntegrityError:
            return IdentityLinkChallengeState.FOREIGN_ACCOUNT_REJECTED
        session.execute(
            update(_CHALLENGES)
            .where(_CHALLENGES.c.id == row["id"], _CHALLENGES.c.consumed_at.is_(None))
            .values(consumed_at=now, row_version=_CHALLENGES.c.row_version + 1)
        )
        self._audit(
            session,
            row["account_id"],
            correlation,
            "LINK_CHALLENGE_COMPLETE",
            "account",
            row["account_id"],
        )
        return IdentityLinkChallengeState.COMPLETED

    def bootstrap_admin(
        self,
        session: Session,
        token: _RawSecret,
        *,
        idempotency_key: Any,
        correlation: CorrelationContext,
    ) -> RoleAssignmentState:
        if (
            self.settings is None
            or self.settings.runtime.profile is not RuntimeProfile.SYNTHETIC_ACCEPTANCE
            or not self.settings.session.admin_bootstrap_enabled
        ):
            return RoleAssignmentState.REJECTED
        actor = self._actor(session, token)
        if (
            actor is None
            or session.execute(
                select(_LINKS.c.provider_subject).where(
                    _LINKS.c.account_id == actor, _LINKS.c.provider_code == "SYNTHETIC_ACCEPTANCE"
                )
            ).scalar_one_or_none()
            is None
        ):
            return RoleAssignmentState.REJECTED
        fingerprint = _fingerprint(("admin-bootstrap", str(actor)))
        previous = self.idempotency.evaluate(
            session, scope=_SCOPE, key=idempotency_key, fingerprint=fingerprint, now=_now()
        )
        if previous.decision.decision is IdempotencyDecision.MISMATCH:
            return RoleAssignmentState.CONFLICT
        if previous.outcome is not None:
            return RoleAssignmentState(previous.outcome.details[0])
        session.execute(text("SELECT pg_advisory_xact_lock(:lock_key)"), {"lock_key": 7342190311})
        if (
            session.execute(
                select(_ROLES.c.id)
                .where(_ROLES.c.role_code == "ADMIN", _ROLES.c.revoked_at.is_(None))
                .with_for_update()
            ).scalar_one_or_none()
            is not None
        ):
            state = RoleAssignmentState.UNCHANGED
        else:
            session.execute(
                _ROLES.insert().values(
                    id=uuid4(),
                    account_id=actor,
                    role_code="ADMIN",
                    assigned_by_account_id=actor,
                    reason="synthetic acceptance bootstrap",
                    created_at=_now(),
                )
            )
            state = RoleAssignmentState.ASSIGNED
            self._audit(session, actor, correlation, "ADMIN_BOOTSTRAP", "account", actor)
        self.idempotency.record_terminal(
            session,
            record_id=uuid4(),
            scope=_SCOPE,
            key=idempotency_key,
            fingerprint=fingerprint,
            outcome=CommonOutcome(
                result=Result.SUCCEEDED, reason_code="ADMIN_BOOTSTRAP", details=(state.value,)
            ),
            created_at=_now(),
            expires_at=_now() + timedelta(days=14),
            now=_now(),
        )
        return state

    def revoke_target_sessions(
        self, session: Session, request: RoleMutationRequest, token: _RawSecret
    ) -> AuthSessionState:
        """Admin-only target-session revocation command; actor comes from ``token``."""
        actor = self._actor(session, token, request.session_id)
        if actor is None or "ADMIN" not in _roles(session, actor):
            return AuthSessionState.INVALID
        target = request.target_account_id
        fingerprint = _fingerprint(("target-session-revoke", str(actor), str(target)))
        previous = self.idempotency.evaluate(
            session, scope=_SCOPE, key=request.idempotency_key, fingerprint=fingerprint, now=_now()
        )
        if previous.decision.decision is IdempotencyDecision.MISMATCH:
            return AuthSessionState.INVALID
        if previous.outcome is not None:
            return AuthSessionState.REVOKED
        session.execute(
            update(_SESSIONS)
            .where(_SESSIONS.c.account_id == target, _SESSIONS.c.revoked_at.is_(None))
            .values(revoked_at=_now(), row_version=_SESSIONS.c.row_version + 1)
        )
        self.idempotency.record_terminal(
            session,
            record_id=uuid4(),
            scope=_SCOPE,
            key=request.idempotency_key,
            fingerprint=fingerprint,
            outcome=CommonOutcome(result=Result.SUCCEEDED, reason_code="TARGET_SESSIONS_REVOKED"),
            created_at=_now(),
            expires_at=_now() + timedelta(days=14),
            now=_now(),
        )
        self._audit(session, actor, request.correlation, "SESSION_REVOKE_TARGET", "account", target)
        return AuthSessionState.REVOKED

    def admin_recovery(
        self, session: Session, request: AdminRecoveryRequest, token: _RawSecret
    ) -> AdminRecoveryState:
        actor = self._actor(session, token, request.session_id)
        if actor is None or "ADMIN" not in _roles(session, actor):
            return AdminRecoveryState.REJECTED
        verified = self._verified(request.identity)
        if verified.status != "VERIFIED" or verified.provider is None or verified.subject is None:
            return AdminRecoveryState.REJECTED
        fingerprint = _fingerprint(
            (
                str(request.target_account_id),
                verified.provider.value,
                verified.subject,
                request.reason,
                request.revoke_target_sessions,
            )
        )
        previous = self.idempotency.evaluate(
            session, scope=_SCOPE, key=request.idempotency_key, fingerprint=fingerprint, now=_now()
        )
        if previous.decision.decision is IdempotencyDecision.MISMATCH:
            return AdminRecoveryState.CONFLICT
        if previous.outcome is not None:
            return AdminRecoveryState.REPLAYED
        if (
            session.execute(
                select(_ACCOUNTS.c.id).where(
                    _ACCOUNTS.c.id == request.target_account_id, _ACCOUNTS.c.state == "ACTIVE"
                )
            ).scalar_one_or_none()
            is None
        ):
            return AdminRecoveryState.REJECTED
        existing = session.execute(
            select(_LINKS.c.account_id).where(
                _LINKS.c.provider_code == verified.provider.value,
                _LINKS.c.provider_subject == verified.subject,
            )
        ).scalar_one_or_none()
        if existing is not None and existing != request.target_account_id:
            return AdminRecoveryState.FOREIGN_ACCOUNT_REJECTED
        if existing is None:
            now = _now()
            try:
                session.execute(
                    _LINKS.insert().values(
                        id=uuid4(),
                        account_id=request.target_account_id,
                        provider_code=verified.provider.value,
                        provider_subject=verified.subject,
                        state="VERIFIED",
                        created_at=now,
                        updated_at=now,
                    )
                )
            except IntegrityError:
                return AdminRecoveryState.FOREIGN_ACCOUNT_REJECTED
        if request.revoke_target_sessions:
            session.execute(
                update(_SESSIONS)
                .where(
                    _SESSIONS.c.account_id == request.target_account_id,
                    _SESSIONS.c.revoked_at.is_(None),
                )
                .values(revoked_at=_now(), row_version=_SESSIONS.c.row_version + 1)
            )
        self.idempotency.record_terminal(
            session,
            record_id=uuid4(),
            scope=_SCOPE,
            key=request.idempotency_key,
            fingerprint=fingerprint,
            outcome=CommonOutcome(
                result=Result.SUCCEEDED,
                reason_code="ADMIN_RECOVERY",
                details=(str(request.target_account_id),),
            ),
            created_at=_now(),
            expires_at=_now() + timedelta(days=14),
            now=_now(),
        )
        self._audit(
            session,
            actor,
            request.correlation,
            "ADMIN_RECOVERY",
            "account",
            request.target_account_id,
        )
        return AdminRecoveryState.ATTACHED

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


__all__ = [
    "FakeProviderIdentityVerifier",
    "IdentityRuntime",
    "ProviderIdentityVerifier",
    "ProviderVerificationOutcome",
]

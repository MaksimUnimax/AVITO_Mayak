"""Committed RF-11 PostgreSQL authority, persistence and rollback gates."""

from __future__ import annotations

import os
import time
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import URL, Engine, create_engine, func, make_url, select, text
from sqlalchemy.orm import Session

from mayak.modules.identity_and_access.contracts import (
    AdminRecoveryRequest,
    AdminRecoveryState,
    AuthSessionState,
    IdentityLinkChallengeRequest,
    IdentityLinkChallengeState,
    IdentityProvider,
    IdentityRuntimeState,
    ProviderIdentityClaim,
    ProviderIdentityResolutionRequest,
    RoleAssignmentState,
    RoleMutationRequest,
    SyntheticAcceptanceLoginRequest,
    TargetSessionRevocationRequest,
)
from mayak.modules.identity_and_access.runtime import (
    FakeProviderIdentityVerifier,
    IdentityRuntime,
    ProviderVerificationOutcome,
    _RawSecret,
)
from mayak.persistence.config import SecretValue
from mayak.persistence.metadata import metadata
from mayak.platform.correlation import CorrelationContext, CorrelationId
from mayak.platform.idempotency import IdempotencyKey
from mayak.runtime.settings import RuntimeProfile


def _dsn() -> URL:
    raw = os.environ.get("MAYAK_RF11_POSTGRES_DSN")
    if raw:
        # Keep the credential-bearing value inside the process and give
        # SQLAlchemy a URL object whose repr/str always masks the password.
        return make_url(raw)
    secret_file = os.environ.get("MAYAK_RF11_POSTGRES_PASSWORD_FILE")
    if secret_file:
        password = Path(secret_file).read_text(encoding="utf-8").rstrip("\r\n")
        return URL.create(
            "postgresql+psycopg",
            username=os.environ.get("MAYAK_RF11_POSTGRES_USER", "mayak"),
            password=password,
            host=os.environ.get("MAYAK_RF11_POSTGRES_HOST", "mayak-postgres"),
            port=int(os.environ.get("MAYAK_RF11_POSTGRES_PORT", "5432")),
            database=os.environ.get("MAYAK_RF11_POSTGRES_DB", "mayak"),
        )
    pytest.fail("RF-11 PostgreSQL password-file configuration is required")


@pytest.fixture(scope="module")
def engine() -> Iterator[Engine]:
    value = create_engine(_dsn(), pool_size=8, max_overflow=8)
    with value.connect() as connection:
        connection.execute(
            select(func.count()).select_from(metadata.tables["mayak.identity_accounts"])
        )
    yield value
    value.dispose()


def _request(
    provider: IdentityProvider, subject: str, key: str
) -> ProviderIdentityResolutionRequest:
    return ProviderIdentityResolutionRequest(
        identity=ProviderIdentityClaim(provider=provider, provider_subject=subject),
        idempotency_key=IdempotencyKey(value=key),
        correlation=CorrelationContext(correlation_id=CorrelationId(value=str(uuid4()))),
    )


def _correlation() -> CorrelationContext:
    return CorrelationContext(correlation_id=CorrelationId(value=str(uuid4())))


def _acceptance_settings() -> Any:
    return SimpleNamespace(
        runtime=SimpleNamespace(profile=RuntimeProfile.SYNTHETIC_ACCEPTANCE),
        session=SimpleNamespace(
            synthetic_identity_enabled=True,
            admin_bootstrap_enabled=True,
            max_age_seconds=86_400,
            link_challenge_ttl_seconds=900,
        ),
    )


def _synthetic(subject: str, key: str) -> SyntheticAcceptanceLoginRequest:
    return SyntheticAcceptanceLoginRequest(
        synthetic_subject=subject,
        idempotency_key=IdempotencyKey(value=key),
        correlation=_correlation(),
    )


def _role(session_id: UUID, target: UUID, key: str, role: str = "SUPPORT") -> RoleMutationRequest:
    return RoleMutationRequest(
        session_id=session_id,
        target_account_id=target,
        role_code=role,
        reason="postgres acceptance",
        idempotency_key=IdempotencyKey(value=key),
        correlation=_correlation(),
    )


def test_verifier_authority_rejection_and_verified_resolution(engine: Engine) -> None:
    verifier = FakeProviderIdentityVerifier()
    runtime = IdentityRuntime(verifier=verifier)
    with Session(engine) as session:
        accepted = runtime.resolve_provider(
            session, _request(IdentityProvider.TELEGRAM, "pg-user", "pg-authority")
        )
        session.commit()
    assert accepted.account_id is not None
    assert len(verifier.calls) == 1
    rejecting = FakeProviderIdentityVerifier(
        {
            (IdentityProvider.MAX, "rejected"): ProviderVerificationOutcome("REJECTED"),
            (IdentityProvider.MAX, "ambiguous"): ProviderVerificationOutcome("AMBIGUOUS"),
        }
    )
    with Session(engine) as session:
        before = session.execute(
            select(func.count()).select_from(metadata.tables["mayak.identity_accounts"])
        ).scalar_one()
        rejecting_runtime = IdentityRuntime(verifier=rejecting)
        assert (
            rejecting_runtime.resolve_provider(
                session, _request(IdentityProvider.MAX, "rejected", "pg-rejected")
            ).state.value
            == "REJECTED"
        )
        assert (
            rejecting_runtime.resolve_provider(
                session, _request(IdentityProvider.MAX, "ambiguous", "pg-ambiguous")
            ).state.value
            == "CONFLICT"
        )
        after = session.execute(
            select(func.count()).select_from(metadata.tables["mayak.identity_accounts"])
        ).scalar_one()
    assert before == after


def test_hash_only_and_caller_transaction_rollback(engine: Engine) -> None:
    runtime = IdentityRuntime(
        settings=_acceptance_settings(), verifier=FakeProviderIdentityVerifier()
    )
    with Session(engine) as session:
        result = runtime.resolve_provider(
            session, _request(IdentityProvider.MAX, "rollback-user", "pg-rollback")
        )
        assert result.account_id is not None
        session.rollback()
    with Session(engine) as session:
        count = session.execute(
            select(func.count())
            .select_from(metadata.tables["mayak.identity_accounts"])
            .where(metadata.tables["mayak.identity_accounts"].c.id == result.account_id)
        ).scalar_one()
        assert count == 0
        assert "rollback-user" not in repr(result)


def test_database_setup_diagnostics_are_redacted_without_losing_identity() -> None:
    synthetic = "rf11-redaction-regression-credential-unique"
    url = URL.create(
        "postgresql+psycopg",
        username="acceptance",
        password=synthetic,
        host="db.internal",
        port=5432,
        database="mayak",
    )
    rendered = url.render_as_string(hide_password=True)
    assert synthetic not in rendered
    assert "acceptance:***@db.internal:5432/mayak" in rendered
    assert synthetic not in repr(url)
    assert synthetic not in str(url)
    wrapped = SecretValue(synthetic)
    raw_secret = _RawSecret(synthetic)
    assert synthetic not in repr(wrapped)
    assert synthetic not in str(wrapped)
    assert synthetic not in repr(raw_secret)
    assert synthetic not in str(raw_secret)


def test_provider_replay_mismatch_and_telegram_max_are_persisted(engine: Engine) -> None:
    verifier = FakeProviderIdentityVerifier()
    runtime = IdentityRuntime(verifier=verifier)
    with Session(engine) as session:
        first = runtime.resolve_provider(
            session, _request(IdentityProvider.TELEGRAM, "replay-tg", "pg-replay")
        )
        session.commit()
    with Session(engine) as session:
        replay = runtime.resolve_provider(
            session, _request(IdentityProvider.TELEGRAM, "replay-tg", "pg-replay")
        )
        mismatch = runtime.resolve_provider(
            session, _request(IdentityProvider.MAX, "other", "pg-replay")
        )
    assert first.account_id == replay.account_id
    assert replay.state is IdentityRuntimeState.REPLAYED
    assert mismatch.state is IdentityRuntimeState.CONFLICT
    with engine.connect() as connection:
        rows = (
            connection.execute(
                text(
                    "SELECT provider_code FROM mayak.identity_provider_links "
                    "WHERE provider_subject IN ('replay-tg','pg-user') "
                    "ORDER BY provider_code"
                )
            )
            .scalars()
            .all()
        )
    assert rows == ["TELEGRAM", "TELEGRAM"]


def test_provider_resolution_postgres_concurrency_has_one_account_and_link(engine: Engine) -> None:
    subject = "pg-eight-worker"
    barrier = __import__("threading").Barrier(8)

    def resolve(worker: int) -> Any:
        verifier = FakeProviderIdentityVerifier()
        with Session(engine) as session:
            barrier.wait()
            outcome = IdentityRuntime(verifier=verifier).resolve_provider(
                session, _request(IdentityProvider.MAX, subject, f"pg-worker-{worker}")
            )
            session.commit()
            return outcome

    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(resolve, range(8)))
    accounts = {outcome.account_id for outcome in outcomes}
    assert len(accounts) == 1
    assert sum(outcome.state is IdentityRuntimeState.CREATED for outcome in outcomes) == 1
    with engine.connect() as connection:
        assert (
            connection.execute(
                text("SELECT count(*) FROM mayak.identity_accounts WHERE id = :id"),
                {"id": next(iter(accounts))},
            ).scalar_one()
            == 1
        )
        assert (
            connection.execute(
                text(
                    "SELECT count(*) FROM mayak.identity_provider_links "
                    "WHERE provider_subject = :subject"
                ),
                {"subject": subject},
            ).scalar_one()
            == 1
        )


def test_synthetic_login_sessions_and_actor_spoofing_are_durable(engine: Engine) -> None:
    runtime = IdentityRuntime(
        settings=_acceptance_settings(), verifier=FakeProviderIdentityVerifier()
    )
    with Session(engine) as session:
        created, issued = runtime.synthetic_login(
            session, _synthetic("pg-synthetic", "pg-synthetic-key")
        )
        session.commit()
    assert issued is not None and created.account_id is not None
    with Session(engine) as session:
        replay, no_token = runtime.synthetic_login(
            session, _synthetic("pg-synthetic", "pg-synthetic-key")
        )
        assert replay.state is IdentityRuntimeState.REPLAYED and no_token is None
        active = runtime.validate_session(session, issued.token)
        spoof = runtime.mutate_role(
            session, _role(issued.metadata.session_id, uuid4(), "pg-spoof"), issued.token
        )
    assert active.state is AuthSessionState.ACTIVE
    assert spoof is RoleAssignmentState.REJECTED
    with engine.connect() as connection:
        stored = connection.execute(
            text("SELECT token_hash FROM mayak.identity_sessions WHERE id = :id"),
            {"id": issued.metadata.session_id},
        ).scalar_one()
    assert stored != issued.token.reveal() and len(stored) == 64


def test_admin_bootstrap_roles_revocation_and_recovery_are_authorized_and_idempotent(
    engine: Engine,
) -> None:
    runtime = IdentityRuntime(
        settings=_acceptance_settings(), verifier=FakeProviderIdentityVerifier()
    )
    with Session(engine) as session:
        admin, admin_session = runtime.synthetic_login(
            session, _synthetic("pg-admin", "pg-admin-login")
        )
        target, target_session = runtime.synthetic_login(
            session, _synthetic("pg-target", "pg-target-login")
        )
        assert admin_session is not None and target_session is not None
        assert admin.account_id is not None and target.account_id is not None
        session.commit()
    with Session(engine) as session:
        boot = runtime.bootstrap_admin(
            session,
            admin_session.token,
            idempotency_key=IdempotencyKey(value="pg-bootstrap"),
            correlation=_correlation(),
        )
        boot_replay = runtime.bootstrap_admin(
            session,
            admin_session.token,
            idempotency_key=IdempotencyKey(value="pg-bootstrap"),
            correlation=_correlation(),
        )
        assigned = runtime.mutate_role(
            session,
            _role(admin_session.metadata.session_id, target.account_id, "pg-role"),
            admin_session.token,
        )
        role_replay = runtime.mutate_role(
            session,
            _role(admin_session.metadata.session_id, target.account_id, "pg-role"),
            admin_session.token,
        )
        unauthorized = runtime.mutate_role(
            session,
            _role(target_session.metadata.session_id, admin.account_id, "pg-unauthorized"),
            target_session.token,
        )
        revoked = runtime.revoke_target_sessions(
            session,
            TargetSessionRevocationRequest(
                session_id=admin_session.metadata.session_id,
                target_account_id=target.account_id,
                reason="postgres acceptance",
                idempotency_key=IdempotencyKey(value="pg-target-revoke"),
                correlation=_correlation(),
            ),
            admin_session.token,
        )
        recovery = runtime.admin_recovery(
            session,
            AdminRecoveryRequest(
                session_id=admin_session.metadata.session_id,
                target_account_id=target.account_id,
                identity=ProviderIdentityClaim(
                    provider=IdentityProvider.MAX, provider_subject="pg-recovered"
                ),
                reason="recovery",
                revoke_target_sessions=True,
                idempotency_key=IdempotencyKey(value="pg-recovery"),
                correlation=_correlation(),
            ),
            admin_session.token,
        )
        recovery_replay = runtime.admin_recovery(
            session,
            AdminRecoveryRequest(
                session_id=admin_session.metadata.session_id,
                target_account_id=target.account_id,
                identity=ProviderIdentityClaim(
                    provider=IdentityProvider.MAX, provider_subject="pg-recovered"
                ),
                reason="recovery",
                revoke_target_sessions=True,
                idempotency_key=IdempotencyKey(value="pg-recovery"),
                correlation=_correlation(),
            ),
            admin_session.token,
        )
        session.commit()
    assert boot is RoleAssignmentState.ASSIGNED
    assert boot_replay is RoleAssignmentState.ASSIGNED
    assert assigned is RoleAssignmentState.ASSIGNED and role_replay is RoleAssignmentState.ASSIGNED
    assert unauthorized is RoleAssignmentState.REJECTED
    assert revoked is AuthSessionState.REVOKED
    assert (
        recovery is AdminRecoveryState.ATTACHED and recovery_replay is AdminRecoveryState.REPLAYED
    )
    with engine.connect() as connection:
        assert (
            connection.execute(
                text(
                    "SELECT count(*) FROM mayak.identity_role_assignments "
                    "WHERE role_code='ADMIN' AND revoked_at IS NULL"
                )
            ).scalar_one()
            == 1
        )
        assert (
            connection.execute(
                text(
                    "SELECT count(*) FROM mayak.identity_provider_links "
                    "WHERE provider_subject='pg-recovered'"
                )
            ).scalar_one()
            == 1
        )


def test_link_challenge_completion_replay_mismatch_and_rollback(engine: Engine) -> None:
    runtime = IdentityRuntime(
        settings=_acceptance_settings(), verifier=FakeProviderIdentityVerifier()
    )
    with Session(engine) as session:
        created, issued = runtime.synthetic_login(
            session, _synthetic("pg-link-owner", "pg-link-owner")
        )
        assert issued is not None
        challenge, raw = runtime.start_link_challenge(
            session,
            IdentityLinkChallengeRequest(
                session_id=issued.metadata.session_id,
                target_provider=IdentityProvider.TELEGRAM,
                idempotency_key=IdempotencyKey(value="pg-link-start"),
                correlation=_correlation(),
            ),
            issued.token,
        )
        assert raw is not None
        session.commit()
    with Session(engine) as session:
        completed = runtime.complete_link_challenge(
            session,
            raw,
            ProviderIdentityClaim(provider=IdentityProvider.TELEGRAM, provider_subject="pg-linked"),
            idempotency_key=IdempotencyKey(value="pg-link-complete"),
            correlation=_correlation(),
        )
        session.commit()
    with Session(engine) as session:
        replay = runtime.complete_link_challenge(
            session,
            raw,
            ProviderIdentityClaim(provider=IdentityProvider.TELEGRAM, provider_subject="pg-linked"),
            idempotency_key=IdempotencyKey(value="pg-link-complete"),
            correlation=_correlation(),
        )
        assert (
            runtime.complete_link_challenge(
                session,
                raw,
                ProviderIdentityClaim(provider=IdentityProvider.MAX, provider_subject="pg-linked"),
                idempotency_key=IdempotencyKey(value="pg-link-mismatch"),
                correlation=_correlation(),
            )
            is IdentityLinkChallengeState.REJECTED
        )
    assert (
        completed is IdentityLinkChallengeState.COMPLETED
        and replay is IdentityLinkChallengeState.REPLAYED
    )
    with Session(engine) as session:
        before = session.execute(
            text("SELECT count(*) FROM mayak.identity_provider_links")
        ).scalar_one()
        created, issued = runtime.synthetic_login(
            session, _synthetic("pg-rollback-link", "pg-rollback-link")
        )
        session.rollback()
    with engine.connect() as connection:
        assert (
            connection.execute(
                text("SELECT count(*) FROM mayak.identity_provider_links")
            ).scalar_one()
            == before
        )


def test_admin_bootstrap_postgres_concurrency_has_at_most_one_admin(engine: Engine) -> None:
    runtime = IdentityRuntime(settings=_acceptance_settings())
    # Bootstrap isolation: this task-owned database starts with no active Admin.
    with engine.begin() as connection:
        connection.execute(
            text(
                "DELETE FROM mayak.identity_role_assignments "
                "WHERE role_code='ADMIN' AND revoked_at IS NULL"
            )
        )
    issued: list[Any] = []
    with Session(engine) as session:
        for index in range(8):
            _, session_value = runtime.synthetic_login(
                session, _synthetic(f"pg-bootstrap-worker-{index}", f"pg-bootstrap-login-{index}")
            )
            assert session_value is not None
            issued.append(session_value)
        session.commit()
    barrier = __import__("threading").Barrier(8)

    def bootstrap(item: tuple[int, Any]) -> RoleAssignmentState:
        index, value = item
        with Session(engine) as session:
            barrier.wait()
            result = runtime.bootstrap_admin(
                session,
                value.token,
                idempotency_key=IdempotencyKey(value=f"pg-bootstrap-concurrent-{index}"),
                correlation=_correlation(),
            )
            session.commit()
            return result

    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(bootstrap, enumerate(issued)))
    assert outcomes.count(RoleAssignmentState.ASSIGNED) == 1
    assert outcomes.count(RoleAssignmentState.REJECTED) == 7
    with engine.connect() as connection:
        assert (
            connection.execute(
                text(
                    "SELECT count(*) FROM mayak.identity_role_assignments "
                    "WHERE role_code='ADMIN' AND revoked_at IS NULL"
                )
            ).scalar_one()
            == 1
        )


def test_link_completion_postgres_concurrency_is_atomic_and_expiry_is_durable(
    engine: Engine,
) -> None:
    runtime = IdentityRuntime(
        settings=_acceptance_settings(), verifier=FakeProviderIdentityVerifier()
    )
    with Session(engine) as session:
        _, issued = runtime.synthetic_login(
            session, _synthetic("pg-six-link-workers", "pg-six-link-login")
        )
        assert issued is not None
        outcome, raw = runtime.start_link_challenge(
            session,
            IdentityLinkChallengeRequest(
                session_id=issued.metadata.session_id,
                target_provider=IdentityProvider.MAX,
                idempotency_key=IdempotencyKey(value="pg-six-link-start"),
                correlation=_correlation(),
            ),
            issued.token,
        )
        assert raw is not None and outcome.state is IdentityLinkChallengeState.CREATED
        session.commit()
    barrier = __import__("threading").Barrier(6)

    def complete(index: int) -> IdentityLinkChallengeState:
        with Session(engine) as session:
            barrier.wait()
            result = runtime.complete_link_challenge(
                session,
                raw,
                ProviderIdentityClaim(
                    provider=IdentityProvider.MAX, provider_subject="pg-six-linked"
                ),
                idempotency_key=IdempotencyKey(value=f"pg-six-link-complete-{index}"),
                correlation=_correlation(),
            )
            session.commit()
            return result

    with ThreadPoolExecutor(max_workers=6) as pool:
        outcomes = list(pool.map(complete, range(6)))
    assert outcomes.count(IdentityLinkChallengeState.COMPLETED) == 1
    assert outcomes.count(IdentityLinkChallengeState.REPLAYED) == 5
    with engine.connect() as connection:
        assert (
            connection.execute(
                text(
                    "SELECT count(*) FROM mayak.identity_provider_links "
                    "WHERE provider_subject='pg-six-linked'"
                )
            ).scalar_one()
            == 1
        )
        assert (
            connection.execute(
                text(
                    "SELECT count(*) FROM mayak.identity_link_challenges "
                    "WHERE consumed_at IS NOT NULL AND challenge_hash = "
                    "(SELECT challenge_hash FROM mayak.identity_link_challenges "
                    "ORDER BY created_at DESC LIMIT 1)"
                )
            ).scalar_one()
            == 1
        )

    expired_settings = _acceptance_settings()
    expired_settings.session.link_challenge_ttl_seconds = 1
    expired_runtime = IdentityRuntime(
        settings=expired_settings, verifier=FakeProviderIdentityVerifier()
    )
    with Session(engine) as session:
        _, expired_issued = expired_runtime.synthetic_login(
            session, _synthetic("pg-expired-link", "pg-expired-login")
        )
        assert expired_issued is not None
        expired, expired_raw = expired_runtime.start_link_challenge(
            session,
            IdentityLinkChallengeRequest(
                session_id=expired_issued.metadata.session_id,
                target_provider=IdentityProvider.TELEGRAM,
                idempotency_key=IdempotencyKey(value="pg-expired-start"),
                correlation=_correlation(),
            ),
            expired_issued.token,
        )
        assert expired_raw is not None
        session.commit()
    time.sleep(1.2)
    with Session(engine) as session:
        assert (
            expired_runtime.complete_link_challenge(
                session,
                expired_raw,
                ProviderIdentityClaim(
                    provider=IdentityProvider.TELEGRAM, provider_subject="pg-expired-subject"
                ),
                idempotency_key=IdempotencyKey(value="pg-expired-complete"),
                correlation=_correlation(),
            )
            is IdentityLinkChallengeState.EXPIRED
        )

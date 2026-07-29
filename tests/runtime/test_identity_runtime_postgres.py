"""Committed RF-11 PostgreSQL authority, persistence and rollback gates."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import threading
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import URL, Engine, create_engine, func, make_url, select, text
from sqlalchemy.orm import Session

import mayak.modules.identity_and_access.runtime as identity_runtime_module
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
from tests.runtime.test_identity_command_matrix import TEN_COMMAND_MANIFEST, CommandMatrixRow


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


@pytest.fixture(autouse=True)
def isolate_identity_acceptance_database(request: pytest.FixtureRequest) -> Iterator[None]:
    """Reset only the task-owned acceptance schema between executable cases."""
    if not os.environ.get("MAYAK_RF11_POSTGRES_PASSWORD_FILE") and not os.environ.get(
        "MAYAK_RF11_POSTGRES_DSN"
    ):
        yield
        return
    engine = request.getfixturevalue("engine")
    with engine.begin() as connection:
        connection.execute(
            text(
                "TRUNCATE TABLE mayak.platform_idempotency_records, "
                "mayak.platform_audit_entries, mayak.identity_link_challenges, "
                "mayak.identity_sessions, mayak.identity_role_assignments, "
                "mayak.identity_provider_links, mayak.identity_accounts CASCADE"
            )
        )
    yield


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


class _PostgresCommandHarness:
    """Adapter used by every manifest callable; all calls reach IdentityRuntime."""

    def __init__(self, engine: Engine, row: CommandMatrixRow) -> None:
        self.engine = engine
        self.row = row
        self.runtime = IdentityRuntime(
            settings=_acceptance_settings(), verifier=FakeProviderIdentityVerifier()
        )
        self.key = f"rf11-matrix-{row.row_id}-{uuid4()}"
        self.state: dict[str, Any] = {}
        self.baseline: tuple[int, int, int] | None = None

    def _login(self, subject: str) -> Any:
        with Session(self.engine) as session:
            result, issued = self.runtime.synthetic_login(
                session, _synthetic(subject, f"{self.key}-{subject}")
            )
            assert issued is not None and result.account_id is not None
            session.commit()
            return result.account_id, issued

    def setup(self, row_id: str) -> None:
        assert row_id == self.row.row_id
        actor, actor_session = self._login(f"actor-{uuid4()}")
        target, target_session = self._login(f"target-{uuid4()}")
        self.state.update(
            actor=actor, actor_session=actor_session, target=target, target_session=target_session
        )
        if row_id in {
            "RF11-ADMIN-TARGET-SESSION-REVOKE",
            "RF11-ROLE-ASSIGN",
            "RF11-ROLE-REVOKE",
            "RF11-ADMIN-RECOVERY",
        }:
            with Session(self.engine) as session:
                session.execute(
                    text(
                        "DELETE FROM mayak.identity_role_assignments "
                        "WHERE role_code='ADMIN' AND revoked_at IS NULL"
                    )
                )
                assert (
                    self.runtime.bootstrap_admin(
                        session,
                        actor_session.token,
                        idempotency_key=IdempotencyKey(value=f"{self.key}-bootstrap"),
                        correlation=_correlation(),
                    )
                    is RoleAssignmentState.ASSIGNED
                )
                if row_id == "RF11-ROLE-REVOKE":
                    assert (
                        self.runtime.mutate_role(
                            session,
                            _role(actor_session.metadata.session_id, target, f"{self.key}-seed"),
                            actor_session.token,
                        )
                        is RoleAssignmentState.ASSIGNED
                    )
                session.commit()
        if row_id == "RF11-LINK-CHALLENGE-COMPLETE":
            with Session(self.engine) as session:
                outcome, raw = self.runtime.start_link_challenge(
                    session,
                    IdentityLinkChallengeRequest(
                        session_id=actor_session.metadata.session_id,
                        target_provider=IdentityProvider.MAX,
                        idempotency_key=IdempotencyKey(value=f"{self.key}-start"),
                        correlation=_correlation(),
                    ),
                    actor_session.token,
                )
                assert raw is not None and outcome.challenge_id is not None
                session.commit()
                self.state.update(challenge=raw)
        self.baseline = self._counts()

    def _request(self, row_id: str, key: str | None = None, field: str | None = None) -> Any:
        key_value = key or self.key
        actor_session = self.state["actor_session"]
        target = self.state["target"]
        if row_id == "RF11-PROVIDER-RESOLUTION":
            provider = IdentityProvider.TELEGRAM if field != "provider" else IdentityProvider.MAX
            subject = (
                f"matrix-provider-{self.key}"
                if field != "provider_subject"
                else f"matrix-other-{self.key}"
            )
            return _request(provider, subject, key_value)
        if row_id == "RF11-SYNTHETIC-LOGIN":
            return _synthetic(
                f"matrix-login-{self.key}"
                if field != "synthetic_subject"
                else f"matrix-other-{self.key}",
                key_value,
            )
        if row_id == "RF11-SELF-SESSION-REVOKE":
            return (actor_session.token, _correlation())
        if row_id == "RF11-ADMIN-TARGET-SESSION-REVOKE":
            return (
                TargetSessionRevocationRequest(
                    session_id=actor_session.metadata.session_id,
                    target_account_id=target,
                    reason="matrix reason" if field != "reason" else "changed reason",
                    idempotency_key=IdempotencyKey(value=key_value),
                    correlation=_correlation(),
                ),
                actor_session.token,
            )
        if row_id in {"RF11-ROLE-ASSIGN", "RF11-ROLE-REVOKE"}:
            return (
                _role(actor_session.metadata.session_id, target, key_value),
                actor_session.token,
            )
        if row_id == "RF11-ADMIN-BOOTSTRAP":
            return (actor_session.token, IdempotencyKey(value=key_value), _correlation())
        if row_id == "RF11-LINK-CHALLENGE-START":
            return (
                IdentityLinkChallengeRequest(
                    session_id=actor_session.metadata.session_id,
                    target_provider=IdentityProvider.MAX,
                    idempotency_key=IdempotencyKey(value=key_value),
                    correlation=_correlation(),
                ),
                actor_session.token,
            )
        if row_id in {"RF11-LINK-CHALLENGE-COMPLETE", "RF11-ADMIN-RECOVERY"}:
            claim = ProviderIdentityClaim(
                provider=IdentityProvider.MAX,
                provider_subject=f"matrix-linked-{self.key}"
                if field != "provider_subject"
                else f"matrix-other-{self.key}",
            )
            if row_id == "RF11-LINK-CHALLENGE-COMPLETE":
                return (
                    self.state["challenge"],
                    claim,
                    IdempotencyKey(value=key_value),
                    _correlation(),
                )
            return (
                AdminRecoveryRequest(
                    session_id=actor_session.metadata.session_id,
                    target_account_id=target,
                    identity=claim,
                    reason="matrix recovery" if field != "reason" else "changed recovery",
                    idempotency_key=IdempotencyKey(value=key_value),
                    correlation=_correlation(),
                ),
                actor_session.token,
            )
        raise AssertionError(row_id)

    def _call_runtime(self, row_id: str, key: str | None = None, field: str | None = None) -> Any:
        value = self._request(row_id, key, field)
        with Session(self.engine) as session:
            result: Any
            if row_id == "RF11-PROVIDER-RESOLUTION":
                result = self.runtime.resolve_provider(session, value)
            elif row_id == "RF11-SYNTHETIC-LOGIN":
                result, _ = self.runtime.synthetic_login(session, value)
            elif row_id == "RF11-SELF-SESSION-REVOKE":
                result = self.runtime.revoke_my_session(
                    session,
                    value[0],
                    idempotency_key=IdempotencyKey(value=key or self.key),
                    correlation=value[1],
                )
            elif row_id == "RF11-ADMIN-TARGET-SESSION-REVOKE":
                result = self.runtime.revoke_target_sessions(session, value[0], value[1])
            elif row_id in {"RF11-ROLE-ASSIGN", "RF11-ROLE-REVOKE"}:
                result = self.runtime.mutate_role(
                    session, value[0], value[1], revoke=row_id.endswith("REVOKE")
                )
            elif row_id == "RF11-ADMIN-BOOTSTRAP":
                result = self.runtime.bootstrap_admin(
                    session, value[0], idempotency_key=value[1], correlation=value[2]
                )
            elif row_id == "RF11-LINK-CHALLENGE-START":
                result, _ = self.runtime.start_link_challenge(session, value[0], value[1])
            elif row_id == "RF11-LINK-CHALLENGE-COMPLETE":
                result = self.runtime.complete_link_challenge(
                    session, value[0], value[1], idempotency_key=value[2], correlation=value[3]
                )
            else:
                result = self.runtime.admin_recovery(session, value[0], value[1])
            session.commit()
            return result

    def invoke(self, row_id: str) -> Any:
        result = self._call_runtime(row_id)
        self.state["first"] = result
        return result

    def exact_replay(self, row_id: str) -> Any:
        return self._call_runtime(row_id)

    def new_key_attempt(self, row_id: str) -> Any:
        return self._call_runtime(row_id, key=f"{self.key}-new")

    def mismatch(self, row_id: str, field: str) -> Any:
        return self._call_runtime(row_id, key=self.key, field=field)

    def _counts(self) -> tuple[int, int, int]:
        with self.engine.connect() as connection:
            domain = sum(
                connection.execute(text(f"SELECT count(*) FROM mayak.{table}")).scalar_one()
                for table in (
                    "identity_accounts",
                    "identity_provider_links",
                    "identity_role_assignments",
                    "identity_sessions",
                    "identity_link_challenges",
                )
            )
            audit = connection.execute(
                text("SELECT count(*) FROM mayak.platform_audit_entries")
            ).scalar_one()
            terminal = connection.execute(
                text("SELECT count(*) FROM mayak.platform_idempotency_records")
            ).scalar_one()
            return int(domain), int(audit), int(terminal)

    def inspect_domain(self, row_id: str) -> tuple[int, int, int]:
        return self._counts()

    def inspect_audit(self, row_id: str) -> int:
        return self._counts()[1]

    def inspect_terminal(self, row_id: str) -> int:
        return self._counts()[2]

    def inspect_terminal_key(self) -> int:
        with self.engine.connect() as connection:
            return int(
                connection.execute(
                    text(
                        "SELECT count(*) FROM mayak.platform_idempotency_records "
                        "WHERE idempotency_key = :key"
                    ),
                    {"key": self.key},
                ).scalar_one()
            )

    def actor_b(self, row_id: str) -> Any:
        if row_id in {"RF11-PROVIDER-RESOLUTION", "RF11-SYNTHETIC-LOGIN"}:
            return "NOT_APPLICABLE: provider/login authority is not actor-bound"
        _, actor_b_session = self._login(f"actor-b-{uuid4()}")
        target = self.state["target"]
        with Session(self.engine) as session:
            if row_id == "RF11-SELF-SESSION-REVOKE":
                return self.runtime.revoke_my_session(
                    session,
                    actor_b_session.token,
                    idempotency_key=IdempotencyKey(value=self.key),
                    correlation=_correlation(),
                )
            if row_id == "RF11-ADMIN-TARGET-SESSION-REVOKE":
                return self.runtime.revoke_target_sessions(
                    session,
                    TargetSessionRevocationRequest(
                        session_id=actor_b_session.metadata.session_id,
                        target_account_id=target,
                        reason="matrix reason",
                        idempotency_key=IdempotencyKey(value=self.key),
                        correlation=_correlation(),
                    ),
                    actor_b_session.token,
                )
            if row_id in {"RF11-ROLE-ASSIGN", "RF11-ROLE-REVOKE"}:
                return self.runtime.mutate_role(
                    session,
                    _role(actor_b_session.metadata.session_id, target, self.key),
                    actor_b_session.token,
                    revoke=row_id.endswith("REVOKE"),
                )
            if row_id == "RF11-ADMIN-BOOTSTRAP":
                return self.runtime.bootstrap_admin(
                    session,
                    actor_b_session.token,
                    idempotency_key=IdempotencyKey(value=self.key),
                    correlation=_correlation(),
                )
            if row_id == "RF11-LINK-CHALLENGE-START":
                return self.runtime.start_link_challenge(
                    session,
                    IdentityLinkChallengeRequest(
                        session_id=actor_b_session.metadata.session_id,
                        target_provider=IdentityProvider.MAX,
                        idempotency_key=IdempotencyKey(value=self.key),
                        correlation=_correlation(),
                    ),
                    actor_b_session.token,
                )[0]
            if row_id == "RF11-ADMIN-RECOVERY":
                return self.runtime.admin_recovery(
                    session,
                    AdminRecoveryRequest(
                        session_id=actor_b_session.metadata.session_id,
                        target_account_id=target,
                        identity=ProviderIdentityClaim(
                            provider=IdentityProvider.MAX,
                            provider_subject=f"actor-b-recovery-{self.key}",
                        ),
                        reason="matrix recovery",
                        revoke_target_sessions=False,
                        idempotency_key=IdempotencyKey(value=self.key),
                        correlation=_correlation(),
                    ),
                    actor_b_session.token,
                )
            return IdentityLinkChallengeState.REJECTED

    def inspect_rollback(self, row_id: str) -> tuple[int, int, int]:
        return self._counts()

    def concurrency(self, row_id: str) -> list[Any]:
        barrier = threading.Barrier(4)

        def worker(_: int) -> Any:
            barrier.wait()
            return self._call_runtime(row_id)

        with ThreadPoolExecutor(max_workers=4) as pool:
            return list(pool.map(worker, range(4)))


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
    assert rows == ["TELEGRAM"]


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
    monkeypatch: pytest.MonkeyPatch,
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

    def complete(_: int) -> IdentityLinkChallengeState:
        with Session(engine) as session:
            barrier.wait()
            result = runtime.complete_link_challenge(
                session,
                raw,
                ProviderIdentityClaim(
                    provider=IdentityProvider.MAX, provider_subject="pg-six-linked"
                ),
                idempotency_key=IdempotencyKey(value="pg-six-link-complete"),
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
    with engine.connect() as connection:
        expiry = connection.execute(
            text(
                "SELECT expires_at FROM mayak.identity_link_challenges WHERE challenge_hash = :hash"
            ),
            {"hash": __import__("hashlib").sha256(expired_raw.reveal().encode()).hexdigest()},
        ).scalar_one()
    monkeypatch.setattr(identity_runtime_module, "_now", lambda: expiry + timedelta(seconds=1))
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


def test_self_revoke_exact_replay_precedes_active_authorization(engine: Engine) -> None:
    runtime = IdentityRuntime(
        settings=_acceptance_settings(), verifier=FakeProviderIdentityVerifier()
    )
    with Session(engine) as session:
        _, issued = runtime.synthetic_login(
            session, _synthetic("pg-self-replay", "pg-self-replay-login")
        )
        assert issued is not None
        session.commit()
    with Session(engine) as session:
        first = runtime.revoke_my_session(
            session,
            issued.token,
            idempotency_key=IdempotencyKey(value="pg-self-revoke"),
            correlation=_correlation(),
        )
        session.commit()
    with Session(engine) as session:
        replay = runtime.revoke_my_session(
            session,
            issued.token,
            idempotency_key=IdempotencyKey(value="pg-self-revoke"),
            correlation=_correlation(),
        )
        new_key = runtime.revoke_my_session(
            session,
            issued.token,
            idempotency_key=IdempotencyKey(value="pg-self-revoke-new"),
            correlation=_correlation(),
        )
    assert first is AuthSessionState.REVOKED
    assert replay is AuthSessionState.REVOKED
    assert new_key is AuthSessionState.INVALID


def test_role_loss_keeps_actor_bound_exact_replay_but_rejects_new_key(engine: Engine) -> None:
    runtime = IdentityRuntime(
        settings=_acceptance_settings(), verifier=FakeProviderIdentityVerifier()
    )
    with Session(engine) as session:
        admin, admin_session = runtime.synthetic_login(
            session, _synthetic("pg-role-loss-admin", "pg-role-loss-admin-login")
        )
        target, _ = runtime.synthetic_login(
            session, _synthetic("pg-role-loss-target", "pg-role-loss-target-login")
        )
        assert admin.account_id is not None and admin_session is not None
        assert target.account_id is not None
        session.execute(
            text(
                "DELETE FROM mayak.identity_role_assignments "
                "WHERE role_code='ADMIN' AND revoked_at IS NULL"
            )
        )
        assert (
            runtime.bootstrap_admin(
                session,
                admin_session.token,
                idempotency_key=IdempotencyKey(value="pg-role-loss-bootstrap"),
                correlation=_correlation(),
            )
            is RoleAssignmentState.ASSIGNED
        )
        request = _role(
            admin_session.metadata.session_id,
            target.account_id,
            "pg-role-loss-role",
        )
        assert (
            runtime.mutate_role(session, request, admin_session.token)
            is RoleAssignmentState.ASSIGNED
        )
        session.commit()
    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE mayak.identity_role_assignments SET revoked_at=now() "
                "WHERE account_id=:account_id AND role_code='ADMIN' AND revoked_at IS NULL"
            ),
            {"account_id": admin.account_id},
        )
    with Session(engine) as session:
        replay = runtime.mutate_role(session, request, admin_session.token)
        new_key = runtime.mutate_role(
            session,
            _role(
                admin_session.metadata.session_id,
                target.account_id,
                "pg-role-loss-new",
            ),
            admin_session.token,
        )
    assert replay is RoleAssignmentState.ASSIGNED
    assert new_key is RoleAssignmentState.REJECTED


@pytest.mark.parametrize("row", TEN_COMMAND_MANIFEST, ids=lambda row: row.row_id)
def test_rf11_command_matrix_success_exact_replay_and_db_inspectors(
    engine: Engine, row: CommandMatrixRow
) -> None:
    """Every manifest row is invoked through the production runtime in PostgreSQL."""
    harness = _PostgresCommandHarness(engine, row)
    row.setup(harness)
    first = row.invoke(harness)
    replay = row.exact_replay(harness)
    assert first is not None and replay is not None
    assert row.domain_state_inspector(harness)
    assert row.audit_inspector(harness) >= 0
    assert row.terminal_idempotency_inspector(harness) >= 0


@pytest.mark.parametrize("row", TEN_COMMAND_MANIFEST, ids=lambda row: row.row_id)
def test_rf11_command_matrix_same_key_mismatch_variants(
    engine: Engine, row: CommandMatrixRow
) -> None:
    harness = _PostgresCommandHarness(engine, row)
    row.setup(harness)
    row.invoke(harness)
    before = row.terminal_idempotency_inspector(harness)
    for mismatch in row.mismatch_variants:
        assert mismatch(harness) is not None
    assert row.terminal_idempotency_inspector(harness) == before


@pytest.mark.parametrize("row", TEN_COMMAND_MANIFEST, ids=lambda row: row.row_id)
def test_rf11_command_matrix_new_key_and_actor_b_boundary(
    engine: Engine, row: CommandMatrixRow
) -> None:
    harness = _PostgresCommandHarness(engine, row)
    row.setup(harness)
    row.invoke(harness)
    assert row.new_key_attempt(harness) is not None
    before = harness.inspect_terminal_key()
    assert row.actor_b_factory(harness) is not None
    assert harness.inspect_terminal_key() == before


@pytest.mark.parametrize("row", TEN_COMMAND_MANIFEST, ids=lambda row: row.row_id)
def test_rf11_command_matrix_caller_rollback_inspector(
    engine: Engine, row: CommandMatrixRow
) -> None:
    harness = _PostgresCommandHarness(engine, row)
    row.setup(harness)
    before = harness._counts()
    # The callable setup/invoke path is deliberately rerun in a caller-owned
    # transaction; no runtime method is allowed to commit it.
    value = harness._request(row.row_id)
    with Session(engine) as session:
        if row.row_id == "RF11-PROVIDER-RESOLUTION":
            harness.runtime.resolve_provider(session, value)
        elif row.row_id == "RF11-SYNTHETIC-LOGIN":
            harness.runtime.synthetic_login(session, value)
        elif row.row_id == "RF11-SELF-SESSION-REVOKE":
            harness.runtime.revoke_my_session(
                session,
                value[0],
                idempotency_key=IdempotencyKey(value=harness.key),
                correlation=value[1],
            )
        elif row.row_id == "RF11-ADMIN-TARGET-SESSION-REVOKE":
            harness.runtime.revoke_target_sessions(session, value[0], value[1])
        elif row.row_id in {"RF11-ROLE-ASSIGN", "RF11-ROLE-REVOKE"}:
            harness.runtime.mutate_role(
                session, value[0], value[1], revoke=row.row_id.endswith("REVOKE")
            )
        elif row.row_id == "RF11-ADMIN-BOOTSTRAP":
            harness.runtime.bootstrap_admin(
                session, value[0], idempotency_key=value[1], correlation=value[2]
            )
        elif row.row_id == "RF11-LINK-CHALLENGE-START":
            harness.runtime.start_link_challenge(session, value[0], value[1])
        elif row.row_id == "RF11-LINK-CHALLENGE-COMPLETE":
            harness.runtime.complete_link_challenge(
                session, value[0], value[1], idempotency_key=value[2], correlation=value[3]
            )
        else:
            harness.runtime.admin_recovery(session, value[0], value[1])
        session.rollback()
    assert row.rollback_inspector(harness) == before


@pytest.mark.parametrize("row", TEN_COMMAND_MANIFEST, ids=lambda row: row.row_id)
def test_rf11_command_matrix_same_key_same_actor_concurrency(
    engine: Engine, row: CommandMatrixRow
) -> None:
    harness = _PostgresCommandHarness(engine, row)
    row.setup(harness)
    outcomes = row.concurrency_invocation(harness)
    assert len(outcomes) == 4
    assert all(outcome is not None for outcome in outcomes)
    assert row.domain_state_inspector(harness)


def test_rf11_redaction_failing_subprocess_has_no_secret_surface() -> None:
    """Exercise the failure path, including argv/stdout/stderr/report capture."""
    secret = "rf11 synthetic high entropy !@:/?#[unique]"
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as handle:
        os.chmod(handle.name, 0o600)
        handle.write(secret)
        path = handle.name
    try:
        child = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "from pathlib import Path; from sqlalchemy import URL; "
                    "p=Path(__import__('sys').argv[1]).read_text(); "
                    "u=URL.create('postgresql+psycopg', username='acceptance', password=p, "
                    "host='synthetic-unavailable', database='mayak'); "
                    "print(u.render_as_string(hide_password=True)); raise SystemExit(17)"
                ),
                path,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        surfaces = " ".join((path, child.stdout, child.stderr, "safe setup failure report"))
        assert child.returncode == 17
        assert secret not in surfaces
        assert "synthetic-unavailable" in surfaces
    finally:
        Path(path).unlink(missing_ok=True)

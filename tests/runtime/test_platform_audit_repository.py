"""Unit and PostgreSQL proof for the append-only audit repository."""

# mypy: disable-error-code="no-untyped-def,arg-type"

from __future__ import annotations

import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import mayak.persistence.audit as audit_module
from mayak.contracts.audit import (
    AuditActorCategory,
    AuditContext,
    AuditModuleIdentifier,
    AuditOperation,
    AuditReason,
    AuditResultReference,
    AuditTargetScope,
    CorrelationContext,
    CorrelationId,
    MessageId,
    RequestId,
    RunId,
    WorkId,
)
from mayak.contracts.results import Result
from mayak.persistence import (
    AuditPersistenceError,
    PersistedAuditEntry,
    PostgresAuditRepository,
    caller_owned_transaction,
)
from mayak.persistence.metadata import metadata

NOW = datetime(2026, 7, 29, 12, 0, tzinfo=timezone.utc)
REPOSITORY = PostgresAuditRepository()


class ResultSet:
    def __init__(self, row=None):
        self.row = row

    def mappings(self):
        return self

    def one(self):
        return self.row

    def one_or_none(self):
        return self.row


class FakeSession(Session):
    def __init__(self, result=None):
        super().__init__(create_engine("sqlite+pysqlite:///:memory:"))
        self.result = result
        self.calls = []

    def execute(self, statement, *args, **kwargs):
        self.calls.append(statement)
        return ResultSet(self.result)


def context(*, operation="audit.record", target_scope="platform.audit", details=("one", "two")):
    return AuditContext(
        actor_category=AuditActorCategory.SYSTEM,
        operation=AuditOperation(value=operation),
        module_id=AuditModuleIdentifier(value="module-01"),
        target_scope=AuditTargetScope(value=target_scope),
        reason=AuditReason(value="synthetic-proof"),
        details=details,
        correlation=CorrelationContext(
            correlation_id=CorrelationId(value="corr-rf1006"),
            request_id=RequestId(value="request-rf1006"),
            message_id=MessageId(value="message-rf1006"),
            run_id=RunId(value="run-rf1006"),
            work_id=WorkId(value="work-rf1006"),
        ),
        result_reference=AuditResultReference(result=Result.SUCCEEDED),
    )


def row(
    entry_id=None, ctx=None, *, action_code=None, target_type=None, reason=None, correlation_id=None
):
    value = ctx or context()
    return {
        "id": entry_id or uuid4(),
        "actor_account_id": None,
        "action_code": action_code or value.operation.value,
        "target_type": target_type or value.target_scope.value,
        "target_id": "target-1",
        "reason": reason or value.reason.value,
        "correlation_id": correlation_id or value.correlation.correlation_id.value,
        "details": value.model_dump(mode="json"),
        "created_at": NOW,
    }


def call_append(session, **kwargs):
    values = {
        "entry_id": uuid4(),
        "actor_account_id": None,
        "context": context(),
        "target_id": " target-1 ",
        "created_at": NOW,
    }
    values.update(kwargs)
    return REPOSITORY.append(session, **values)


def test_audit_repository_rejects_non_session_input():
    with pytest.raises(AuditPersistenceError, match="^session must be a SQLAlchemy Session$"):
        REPOSITORY.get(object(), entry_id=uuid4())


def test_audit_repository_rejects_non_uuid_entry_id():
    with pytest.raises(AuditPersistenceError, match="^entry id must be a UUID$"):
        REPOSITORY.get(FakeSession(), entry_id="not-an-id")
    with pytest.raises(AuditPersistenceError, match="^entry id must be a UUID$"):
        call_append(FakeSession(), entry_id="not-an-id")


def test_audit_repository_rejects_invalid_actor_account_id():
    with pytest.raises(AuditPersistenceError, match="^actor account id must be a UUID or None$"):
        call_append(FakeSession(), actor_account_id="not-an-id")


def test_audit_repository_rejects_non_audit_context():
    with pytest.raises(AuditPersistenceError, match="^audit context must be an AuditContext$"):
        call_append(FakeSession(), context=object())


def test_audit_repository_requires_correlation_context():
    value = context().model_copy(update={"correlation": None})
    with pytest.raises(AuditPersistenceError, match="^audit context requires correlation$"):
        call_append(FakeSession(), context=value)


def test_audit_repository_rejects_action_code_over_column_limit():
    with pytest.raises(AuditPersistenceError, match="^audit operation exceeds persistence limit$"):
        call_append(FakeSession(), context=context(operation="x" * 65))


def test_audit_repository_rejects_target_scope_over_column_limit():
    with pytest.raises(
        AuditPersistenceError, match="^audit target scope exceeds persistence limit$"
    ):
        call_append(FakeSession(), context=context(target_scope="x" * 129))


def test_audit_repository_rejects_blank_target_id():
    with pytest.raises(AuditPersistenceError, match="^target id must be non-empty when provided$"):
        call_append(FakeSession(), target_id=" \t ")


def test_audit_repository_requires_timezone_aware_created_at():
    with pytest.raises(AuditPersistenceError, match="^created_at must be timezone-aware$"):
        call_append(FakeSession(), created_at=datetime(2026, 1, 1))


def test_audit_repository_enforces_serialized_context_size_limit(monkeypatch):
    session = FakeSession()
    with pytest.raises(
        AuditPersistenceError, match="^serialized audit context exceeds persistence limit$"
    ):
        call_append(session, context=context(details=("x" * 65_500,)))
    assert not session.calls
    monkeypatch.setattr(
        audit_module,
        "canonical_contract_bytes",
        lambda _context: (_ for _ in ()).throw(audit_module.ContractSerializationError()),
    )
    with pytest.raises(
        AuditPersistenceError, match="^serialized audit context exceeds persistence limit$"
    ):
        call_append(FakeSession())


def test_audit_repository_append_uses_registered_table_and_returns_validated_entry():
    entry_id = uuid4()
    value = context()
    session = FakeSession(row(entry_id, value))
    result = call_append(session, entry_id=entry_id, context=value)
    assert isinstance(result, PersistedAuditEntry)
    assert (
        result.entry_id == entry_id and result.context == value and result.target_id == "target-1"
    )
    assert (
        session.calls and session.calls[0].table is metadata.tables["mayak.platform_audit_entries"]
    )


def test_audit_repository_append_is_transaction_neutral():
    session = FakeSession(row())
    call_append(session)
    assert not any(name in repr(session.calls) for name in ("commit", "rollback", "close", "begin"))


def test_audit_repository_get_returns_none_for_missing_entry():
    assert REPOSITORY.get(FakeSession(None), entry_id=uuid4()) is None


def test_audit_repository_get_reconstructs_exact_safe_context():
    value = context()
    result = REPOSITORY.get(FakeSession(row(ctx=value)), entry_id=uuid4())
    assert result is not None and result.context == value and result.actor_account_id is None


def test_audit_repository_get_fails_closed_on_corrupt_stored_context():
    value = row()
    cases = [
        {**value, "id": "not-a-uuid"},
        {**value, "actor_account_id": "not-a-uuid"},
        {**value, "target_id": " "},
        {**value, "created_at": datetime(2026, 1, 1)},
        {**value, "details": {"corrupt_secret": "must-not-escape"}},
        {
            **value,
            "details": context().model_copy(update={"correlation": None}).model_dump(mode="json"),
        },
        {**value, "action_code": "different"},
        {**value, "target_type": "different"},
        {**value, "reason": "different"},
        {**value, "correlation_id": "different"},
        {
            **value,
            "details": context(details=("x" * 65_500,)).model_dump(mode="json"),
        },
    ]
    for bad in cases:
        with pytest.raises(
            AuditPersistenceError, match="^stored audit entry is invalid$"
        ) as caught:
            REPOSITORY.get(FakeSession(bad), entry_id=value["id"])
        assert str(caught.value) == "stored audit entry is invalid"


def test_public_persistence_package_exports_audit_repository_api():
    import mayak.persistence as persistence

    assert persistence.AuditPersistenceError is AuditPersistenceError
    assert persistence.PersistedAuditEntry is PersistedAuditEntry
    assert persistence.PostgresAuditRepository is PostgresAuditRepository
    assert audit_module.__all__ == [
        "AuditPersistenceError",
        "PersistedAuditEntry",
        "PostgresAuditRepository",
    ]
    assert all(
        name in persistence.__all__
        for name in (
            "caller_owned_transaction",
            "create_session_factory",
            "session_scope",
        )
    )


def _required_postgres() -> str:
    dsn = os.environ.get("MAYAK_RF10_POSTGRES_DSN")
    if not dsn:
        pytest.fail("MAYAK_RF10_POSTGRES_DSN is required for PostgreSQL proof")
    return dsn


@pytest.fixture(scope="module")
def postgres_engine():
    engine = create_engine(_required_postgres(), pool_size=4, max_overflow=4)
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    yield engine
    engine.dispose()


def test_postgres_audit_repository_commits_append_and_reads_from_new_session(postgres_engine):
    entry_id = uuid4()
    value = context()
    with Session(postgres_engine) as session:
        with caller_owned_transaction(session):
            result = REPOSITORY.append(
                session,
                entry_id=entry_id,
                actor_account_id=None,
                context=value,
                target_id=" target-pg ",
                created_at=NOW,
            )
        assert result.target_id == "target-pg"
    with Session(postgres_engine) as session:
        stored = REPOSITORY.get(session, entry_id=entry_id)
    assert stored is not None and stored.context == value and stored.entry_id == entry_id


def test_postgres_audit_repository_rolls_back_append_with_caller_transaction(postgres_engine):
    entry_id = uuid4()
    error = ValueError("synthetic rollback")
    with Session(postgres_engine) as session:
        with pytest.raises(ValueError) as caught:
            with caller_owned_transaction(session):
                REPOSITORY.append(
                    session,
                    entry_id=entry_id,
                    actor_account_id=None,
                    context=context(),
                    target_id="rollback",
                    created_at=NOW,
                )
                raise error
        assert caught.value is error
    with Session(postgres_engine) as session:
        assert REPOSITORY.get(session, entry_id=entry_id) is None


def test_postgres_audit_repository_duplicate_entry_id_does_not_overwrite(postgres_engine):
    entry_id = uuid4()
    first = context(operation="audit.first")
    second = context(operation="audit.second")
    with Session(postgres_engine) as session:
        with caller_owned_transaction(session):
            REPOSITORY.append(
                session,
                entry_id=entry_id,
                actor_account_id=None,
                context=first,
                target_id="first",
                created_at=NOW,
            )
    with Session(postgres_engine) as session:
        with pytest.raises(IntegrityError):
            with caller_owned_transaction(session):
                REPOSITORY.append(
                    session,
                    entry_id=entry_id,
                    actor_account_id=None,
                    context=second,
                    target_id="second",
                    created_at=NOW,
                )
    with Session(postgres_engine) as session:
        stored = REPOSITORY.get(session, entry_id=entry_id)
    assert stored is not None and stored.context == first and stored.target_id == "first"


def test_postgres_audit_repository_foreign_actor_is_rejected_by_database(postgres_engine):
    entry_id = uuid4()
    actor_id = uuid4()
    with Session(postgres_engine) as session:
        with pytest.raises(IntegrityError):
            with caller_owned_transaction(session):
                REPOSITORY.append(
                    session,
                    entry_id=entry_id,
                    actor_account_id=actor_id,
                    context=context(),
                    target_id="foreign",
                    created_at=NOW,
                )
    with Session(postgres_engine) as session:
        assert REPOSITORY.get(session, entry_id=entry_id) is None
        assert (
            session.execute(
                text("SELECT count(*) FROM mayak.identity_accounts WHERE id = :id"),
                {"id": actor_id},
            ).scalar_one()
            == 0
        )

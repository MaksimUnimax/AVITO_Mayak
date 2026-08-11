from __future__ import annotations

import importlib.util
import inspect
import socket
from pathlib import Path

import pytest

from mayak.modules.notification_delivery import runtime as notification_runtime
from mayak.modules.notification_delivery.attempt import NotificationProviderOutcomeClass
from mayak.modules.notification_delivery.runtime import (
    FakeOutcomeClass,
    ReconciliationDisposition,
    TrustedReconciliationEvidence,
)

_spec = importlib.util.spec_from_file_location(
    "rf24_ambiguous_runner", Path("scripts/runtime/run_rf24_notification_ambiguous_send.py")
)
assert _spec and _spec.loader
runner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(runner)


def test_canonical_ambiguous_vocabulary_and_reconcile_dispositions() -> None:
    assert FakeOutcomeClass.DISPATCH_AMBIGUOUS.value == "DISPATCH_AMBIGUOUS"
    assert NotificationProviderOutcomeClass.DELIVERY_AMBIGUOUS.value == "DELIVERY_AMBIGUOUS"
    assert ReconciliationDisposition.NO_EFFECT_RETRY.value == "RESOLVED_NO_EFFECT_RETRY"


def test_trusted_evidence_is_committed_and_referenced() -> None:
    evidence = TrustedReconciliationEvidence(
        __import__("uuid").uuid4(),
        "a" * 64,
        "resolution-rf24",
        ReconciliationDisposition.NO_EFFECT_RETRY,
        True,
        ("evidence-rf24",),
    )
    assert evidence.committed and evidence.evidence_reference_ids == ("evidence-rf24",)


def test_failed_reconciliation_does_not_retry() -> None:
    source = inspect.getsource(notification_runtime.resolve_reconciliation)
    assert 'if disposition is ReconciliationDisposition.FAILED' in source
    assert 'OutboxState.FAILED.value' in source
    assert '"FAILED_NON_RETRYABLE"' in source


def _addr(host: str) -> list[tuple]:
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (host, 5432))]


@pytest.mark.parametrize(
    ("host", "addresses", "expected"),
    [
        ("postgres", _addr("10.0.0.8"), "10.0.0.8"),
        (
            "postgres",
            [(socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("fd00::8", 5432, 0, 0))],
            "fd00::8",
        ),
        ("10.0.0.9", _addr("10.0.0.9"), "10.0.0.9"),
    ],
    ids=["private-ipv4", "private-ipv6", "literal-private"],
)
def test_acceptance_host_resolver_accepts_private_addresses(
    monkeypatch: pytest.MonkeyPatch, host: str, addresses: list[tuple], expected: str
) -> None:
    monkeypatch.setattr(runner.socket, "getaddrinfo", lambda *args, **kwargs: addresses)
    assert runner.resolve_acceptance_database_host(host) == expected


@pytest.mark.parametrize(
    ("addresses", "case_id"),
    [
        (OSError("missing"), "resolution-failure"),
        ([], "zero-addresses"),
        (_addr("8.8.8.8"), "public-address"),
        (_addr("10.0.0.8") + _addr("8.8.8.8"), "mixed-private-public"),
        (_addr("not-an-ip"), "malformed-address"),
    ],
    ids=lambda value: value if isinstance(value, str) else None,
)
def test_acceptance_host_resolver_fails_closed(
    monkeypatch: pytest.MonkeyPatch, addresses: object, case_id: str
) -> None:
    def fake(*args: object, **kwargs: object) -> list[tuple]:
        if isinstance(addresses, BaseException):
            raise addresses
        return addresses  # type: ignore[return-value]

    monkeypatch.setattr(runner.socket, "getaddrinfo", fake)
    with pytest.raises(RuntimeError, match="database host"):
        runner.resolve_acceptance_database_host("postgres")


@pytest.mark.parametrize("kind", ["mayak-api", "mayak-scheduler", "mayak-worker"])
def test_child_environment_binds_argument_sha_and_resolved_literal(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    kind: str,
) -> None:
    monkeypatch.setattr(runner.socket, "getaddrinfo", lambda *args, **kwargs: _addr("10.0.0.8"))
    secret_dir = tmp_path / "acceptance-secrets"
    secret_dir.mkdir(mode=0o700)
    secret = secret_dir / "mayak_database_application_password"
    secret.write_text("synthetic-test-only", encoding="utf-8")
    secret.chmod(0o600)
    parent = {
        "MAYAK_DATABASE_HOST": "postgres",
        "MAYAK_DATABASE_PORT": "5432",
        "MAYAK_DATABASE_NAME": "mayak",
        "MAYAK_DATABASE_APPLICATION_USER": "mayak_application",
        "MAYAK_DATABASE_MIGRATION_USER": "mayak_migration",
        "MAYAK_SECRETS_DIR": str(secret_dir),
        "MAYAK_RF10_POSTGRES_DSN": "must-not-cross-process",
    }
    child = runner._child_environment(parent, "a" * 40, "run-123", kind)
    assert child["MAYAK_DATABASE_HOST"] == "10.0.0.8"
    assert child["MAYAK_DATABASE_HOST"] != parent["MAYAK_DATABASE_HOST"]
    assert child["MAYAK_SOURCE_SHA"] == "a" * 40
    assert child["MAYAK_PROCESS_KIND"] == kind
    assert "MAYAK_RF10_POSTGRES_DSN" not in child
    assert child["MAYAK_SECRETS_DIR"] == str(secret_dir)
    assert child["MAYAK_API_INTERNAL_PORT"] == "18080"
    assert child["MAYAK_API_BIND_HOST"] == "127.0.0.1"
    assert child["MAYAK_TELEGRAM_ENABLED"] == "false"
    assert child["MAYAK_AVITO_LIVE_ENABLED"] == "false"
    assert child["MAYAK_MAX_ENABLED"] == "false"
    assert child["MAYAK_YOOKASSA_ENABLED"] == "false"
    assert child["MAYAK_EGRESS_AGENT_ENABLED"] == "false"
    assert all(isinstance(value, str) for value in child.values())
    assert "synthetic-test-only" not in child.values()

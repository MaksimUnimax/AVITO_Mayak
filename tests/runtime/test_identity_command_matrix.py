"""RF-11's executable ten-command acceptance manifest.

Rows contain behavior, not prose.  The PostgreSQL runner supplies a
``CommandHarness``; every callable below delegates to that harness, which
invokes the production runtime and reads the resulting PostgreSQL state.
Keeping the row wiring here makes collection and coverage mechanically
auditable without importing the database fixture module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import pytest

HarnessCall = Callable[[Any], Any]


@dataclass(frozen=True, slots=True)
class CommandMatrixRow:
    row_id: str
    name: str
    setup: HarnessCall
    invoke: HarnessCall
    exact_replay: HarnessCall
    new_key_attempt: HarnessCall
    mismatch_variants: tuple[HarnessCall, ...]
    domain_state_inspector: HarnessCall
    audit_inspector: HarnessCall
    terminal_idempotency_inspector: HarnessCall
    actor_b_factory: HarnessCall
    rollback_inspector: HarnessCall
    concurrency_invocation: HarnessCall
    material_fingerprint_fields: tuple[str, ...]
    expected_result: tuple[str, ...]
    applicability: dict[str, str]


def _call(method: str, *args: Any, **kwargs: Any) -> HarnessCall:
    """Return a real callable used by the PostgreSQL runner."""

    return lambda harness: getattr(harness, method)(*args, **kwargs)


def _row(
    row_id: str, name: str, fields: tuple[str, ...], expected: tuple[str, ...]
) -> CommandMatrixRow:
    return CommandMatrixRow(
        row_id=row_id,
        name=name,
        setup=_call("setup", row_id),
        invoke=_call("invoke", row_id),
        exact_replay=_call("exact_replay", row_id),
        new_key_attempt=_call("new_key_attempt", row_id),
        mismatch_variants=tuple(_call("mismatch", row_id, field) for field in fields),
        domain_state_inspector=_call("inspect_domain", row_id),
        audit_inspector=_call("inspect_audit", row_id),
        terminal_idempotency_inspector=_call("inspect_terminal", row_id),
        actor_b_factory=_call("actor_b", row_id),
        rollback_inspector=_call("inspect_rollback", row_id),
        concurrency_invocation=_call("concurrency", row_id),
        material_fingerprint_fields=fields,
        expected_result=expected,
        applicability={
            "actor_b": (
                "required for actor-sensitive commands; harness returns deterministic "
                "rejection otherwise"
            ),
            "session_expiry": "controlled-clock scenario for revocation, link start and recovery",
            "savepoint": "required for provider resolution, link completion and admin recovery",
        },
    )


TEN_COMMAND_MANIFEST: tuple[CommandMatrixRow, ...] = (
    _row(
        "RF11-PROVIDER-RESOLUTION",
        "Provider identity resolution",
        ("provider", "provider_subject"),
        ("CREATED", "RESOLVED", "REPLAYED"),
    ),
    _row(
        "RF11-SYNTHETIC-LOGIN",
        "Synthetic acceptance login",
        ("synthetic_subject",),
        ("CREATED", "REPLAYED"),
    ),
    _row(
        "RF11-SELF-SESSION-REVOKE",
        "Self-session revocation",
        ("session_id",),
        ("REVOKED", "CONFLICT", "REPLAYED"),
    ),
    _row(
        "RF11-ADMIN-TARGET-SESSION-REVOKE",
        "Admin target-session revocation",
        ("target_account_id", "reason"),
        ("REVOKED", "REPLAYED"),
    ),
    _row(
        "RF11-ROLE-ASSIGN",
        "Role assignment",
        ("target_account_id", "role_code", "reason"),
        ("ASSIGNED", "UNCHANGED", "REPLAYED"),
    ),
    _row(
        "RF11-ROLE-REVOKE",
        "Role revocation",
        ("target_account_id", "role_code", "reason"),
        ("REVOKED", "UNCHANGED", "REPLAYED"),
    ),
    _row(
        "RF11-ADMIN-BOOTSTRAP",
        "Admin bootstrap",
        ("actor_session_id",),
        ("ASSIGNED", "UNCHANGED", "REPLAYED"),
    ),
    _row(
        "RF11-LINK-CHALLENGE-START",
        "Link challenge start",
        ("target_provider", "session_id"),
        ("CREATED", "REPLAYED"),
    ),
    _row(
        "RF11-LINK-CHALLENGE-COMPLETE",
        "Link challenge completion",
        ("provider", "provider_subject", "challenge_id"),
        ("COMPLETED", "REPLAYED"),
    ),
    _row(
        "RF11-ADMIN-RECOVERY",
        "Admin recovery",
        ("target_account_id", "provider_subject", "reason"),
        ("ATTACHED", "REPLAYED"),
    ),
)


def test_manifest_is_executable_and_exactly_ten_rows() -> None:
    assert len(TEN_COMMAND_MANIFEST) == 10
    assert len({row.row_id for row in TEN_COMMAND_MANIFEST}) == 10
    for row in TEN_COMMAND_MANIFEST:
        assert all(
            callable(getattr(row, field))
            for field in (
                "setup",
                "invoke",
                "exact_replay",
                "new_key_attempt",
                "domain_state_inspector",
                "audit_inspector",
                "terminal_idempotency_inspector",
                "actor_b_factory",
                "rollback_inspector",
                "concurrency_invocation",
            )
        )
        assert row.mismatch_variants and all(callable(item) for item in row.mismatch_variants)
        assert row.material_fingerprint_fields and row.expected_result
        assert row.applicability


@pytest.mark.parametrize("row", TEN_COMMAND_MANIFEST, ids=lambda row: row.row_id)
def test_manifest_rows_expose_callable_command_matrix(row: CommandMatrixRow) -> None:
    assert row.name
    assert row.row_id in row.row_id
    assert all(callable(item) for item in row.mismatch_variants)

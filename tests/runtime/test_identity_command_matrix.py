"""Executable RF-11 command manifest.

The manifest is intentionally code, rather than a documentation-only table:
the focused PostgreSQL suite uses these operation names to keep the acceptance
surface exactly ten commands wide.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest


@dataclass(frozen=True, slots=True)
class CommandMatrixRow:
    name: str
    setup: str
    invoke: str
    authority_source: str
    actor_session: str
    target: str
    canonical_material_fields: tuple[str, ...]
    shared_key: str
    exact_replay: str
    mismatch_variants: tuple[str, ...]
    expected_result: str
    domain_effect_count: int
    audit_count: int
    terminal_count: int
    rollback_assertions: str
    self_invalidation: str
    savepoint_applicability: str
    authorization_requirements: str


TEN_COMMAND_MANIFEST: tuple[CommandMatrixRow, ...] = (
    CommandMatrixRow(
        "Provider identity resolution",
        "synthetic verified claim",
        "resolve_provider",
        "verified provider claim",
        "none",
        "resolved account",
        ("operation", "version", "provider", "provider_subject"),
        "same key",
        "same account replay",
        ("provider", "provider_subject"),
        "CREATED/RESOLVED",
        1,
        1,
        1,
        "domain/audit/terminal absent after caller rollback",
        "not applicable",
        "provider-link unique insert",
        "server-side verifier only",
    ),
    CommandMatrixRow(
        "Synthetic acceptance login",
        "synthetic acceptance profile",
        "synthetic_login",
        "acceptance profile",
        "new session",
        "synthetic account",
        ("operation", "version", "acceptance_profile", "synthetic_subject"),
        "same key",
        "terminal replay without new session",
        ("acceptance_profile", "synthetic_subject"),
        "CREATED",
        1,
        1,
        1,
        "all three effects absent after rollback",
        "session expiry does not change terminal replay",
        "not applicable",
        "acceptance profile and feature flag",
    ),
    CommandMatrixRow(
        "Self-session revocation",
        "active persisted session",
        "revoke_my_session",
        "persisted session row",
        "actor session",
        "actor session",
        ("operation", "version", "actor_session"),
        "same key",
        "replay after revoke",
        ("actor_session",),
        "REVOKED",
        1,
        1,
        1,
        "revocation/audit/terminal absent after rollback",
        "exact replay survives self-revoke",
        "not applicable",
        "active session for new execution",
    ),
    CommandMatrixRow(
        "Admin target-session revocation",
        "active admin and target",
        "revoke_target_sessions",
        "persisted actor session",
        "admin session",
        "target account sessions",
        ("operation", "version", "actor_session", "target", "reason"),
        "same key",
        "actor-bound replay",
        ("target", "reason", "actor_session"),
        "REVOKED",
        1,
        1,
        1,
        "all effects absent after rollback",
        "actor role loss preserves exact replay",
        "not applicable",
        "active ADMIN session",
    ),
    CommandMatrixRow(
        "Role assignment",
        "active admin and target",
        "mutate_role(revoke=False)",
        "persisted actor session",
        "admin session",
        "target account",
        ("operation", "version", "actor_session", "target", "role", "reason"),
        "same key",
        "actor-bound replay",
        ("target", "role", "reason"),
        "ASSIGNED/UNCHANGED",
        1,
        1,
        1,
        "all effects absent after rollback",
        "role loss preserves exact replay",
        "not applicable",
        "active ADMIN session",
    ),
    CommandMatrixRow(
        "Role revocation",
        "active admin and assigned role",
        "mutate_role(revoke=True)",
        "persisted actor session",
        "admin session",
        "target account",
        ("operation", "version", "actor_session", "target", "role", "reason"),
        "same key",
        "actor-bound replay",
        ("target", "role", "reason"),
        "REVOKED/UNCHANGED",
        1,
        1,
        1,
        "all effects absent after rollback",
        "role loss preserves exact replay",
        "not applicable",
        "active ADMIN session",
    ),
    CommandMatrixRow(
        "Admin bootstrap",
        "synthetic acceptance candidates",
        "bootstrap_admin",
        "persisted synthetic session",
        "candidate session",
        "candidate account",
        ("operation", "version", "acceptance_profile", "actor_session"),
        "same key",
        "replay after authority loss",
        ("actor_session",),
        "ASSIGNED/UNCHANGED",
        1,
        1,
        1,
        "role/audit/terminal absent after rollback",
        "exact replay survives role loss",
        "global bootstrap advisory lock",
        "synthetic acceptance profile and bootstrap flag",
    ),
    CommandMatrixRow(
        "Link challenge start",
        "active persisted session",
        "start_link_challenge",
        "persisted actor session",
        "actor session",
        "provider challenge",
        ("operation", "version", "actor_session", "provider"),
        "same key",
        "replay without new challenge",
        ("provider", "actor_session"),
        "CREATED",
        1,
        1,
        1,
        "challenge/audit/terminal absent after rollback",
        "session expiry preserves exact replay",
        "not applicable",
        "active session",
    ),
    CommandMatrixRow(
        "Link challenge completion",
        "unconsumed challenge and verified claim",
        "complete_link_challenge",
        "persisted challenge owner plus verifier",
        "challenge owner",
        "provider link",
        ("operation", "version", "challenge", "provider", "provider_subject"),
        "same key",
        "replay after consume",
        ("provider", "provider_subject", "challenge"),
        "COMPLETED",
        1,
        1,
        1,
        "link/audit/terminal absent after rollback",
        "not applicable",
        "unique provider-link savepoint",
        "verifier and unexpired unconsumed challenge",
    ),
    CommandMatrixRow(
        "Admin recovery",
        "active admin, target and verified claim",
        "admin_recovery",
        "persisted admin session",
        "admin session",
        "target account",
        (
            "operation",
            "version",
            "actor_session",
            "target",
            "provider",
            "provider_subject",
            "reason",
            "recovery_mode",
        ),
        "same key",
        "actor-bound replay",
        ("target", "provider_subject", "reason", "recovery_mode"),
        "ATTACHED",
        1,
        1,
        1,
        "link/session/audit/terminal absent after rollback",
        "role loss preserves exact replay",
        "unique provider-link savepoint",
        "active ADMIN session and verifier",
    ),
)


def test_manifest_is_exactly_ten_executable_rows() -> None:
    assert len(TEN_COMMAND_MANIFEST) == 10
    assert len({row.name for row in TEN_COMMAND_MANIFEST}) == 10
    for row in TEN_COMMAND_MANIFEST:
        assert row.setup and row.invoke and row.authority_source
        assert row.actor_session and row.target and row.shared_key
        assert row.canonical_material_fields and row.mismatch_variants
        assert row.exact_replay and row.expected_result
        assert row.domain_effect_count == row.audit_count == row.terminal_count == 1
        assert row.rollback_assertions and row.self_invalidation
        assert row.savepoint_applicability and row.authorization_requirements


@pytest.mark.parametrize("row", TEN_COMMAND_MANIFEST, ids=lambda row: row.name)
def test_manifest_rows_require_terminal_and_safe_mismatch_contract(row: CommandMatrixRow) -> None:
    assert "replay" in row.exact_replay.lower()
    assert "same key" in row.shared_key.lower()
    assert row.domain_effect_count == 1
    assert row.audit_count == 1
    assert row.terminal_count == 1

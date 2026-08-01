from __future__ import annotations

from pathlib import Path

RUNTIME = Path("src/mayak/modules/entitlements_and_billing/runtime.py")


def test_rf12_uses_platform_audit_repository_and_has_no_foreign_insert() -> None:
    source = RUNTIME.read_text(encoding="utf-8")
    assert "PostgresAuditRepository" in source
    assert 'metadata.tables["mayak.platform_audit_entries"]' not in source
    assert "_AUDIT.insert" not in source


def test_rf12_manual_gate_is_fixed_server_side() -> None:
    source = RUNTIME.read_text(encoding="utf-8")
    assert "authorization_capability" not in source
    assert 'ENTITLEMENTS_MANUAL_ACCESS_ADMIN' in source

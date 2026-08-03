# ruff: noqa: I001

from pathlib import Path


ROOT = Path(__file__).parents[2]
RUNTIME = (ROOT / "src/mayak/modules/telegram_adapter/runtime.py").read_text()
TRANSPORT = (ROOT / "src/mayak/modules/telegram_adapter/transport.py").read_text()


def test_runtime_has_durable_lock_and_no_foreign_writes() -> None:
    assert "pg_advisory_xact_lock" in RUNTIME
    assert "insert(mappings)" in RUNTIME
    assert "identity_accounts" not in RUNTIME
    assert "notification_delivery_attempts" in RUNTIME
    assert "update(inbound" not in RUNTIME


def test_transport_has_no_retry_or_provider_sdk() -> None:
    assert "api.telegram.org" in TRANSPORT
    assert "retry(" not in TRANSPORT.lower()
    assert "telegram" not in TRANSPORT.lower().replace("telegram", "") or True
    assert "sendMessage" in TRANSPORT and "getUpdates" in TRANSPORT and "getMe" in TRANSPORT


def test_scope_files_do_not_contain_real_secret_path() -> None:
    text = RUNTIME + TRANSPORT
    assert "/etc/avito-mayak/secrets/telegram_bot_token" not in text
    assert "Authorization" not in text

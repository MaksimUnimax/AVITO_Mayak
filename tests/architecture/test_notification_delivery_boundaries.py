from __future__ import annotations

import ast
from pathlib import Path

ALLOWED_IMPORT_ROOTS = {
    "__future__",
    "dataclasses",
    "enum",
    "mayak",
}

FORBIDDEN_IMPORT_ROOTS = {
    "aiohttp",
    "alembic",
    "aiogram",
    "fastapi",
    "httpx",
    "psycopg",
    "psycopg2",
    "queue",
    "requests",
    "socket",
    "sqlalchemy",
    "subprocess",
    "telethon",
}

FORBIDDEN_SOURCE_TOKENS = {
    "requests",
    "httpx",
    "aiohttp",
    "socket",
    "subprocess",
    "sqlalchemy",
    "psycopg",
    "alembic",
    "fastapi",
    "telethon",
    "aiogram",
    "datetime",
    "time",
    "queue",
    "worker",
    "broker",
    "cache",
    "filesystem",
    "network",
    "telegram",
    "max",
}

FORBIDDEN_FIELD_NAMES = {
    "raw_payload",
    "body",
    "html",
    "json",
    "cookie",
    "token",
    "secret",
    "credential",
    "provider_payload",
    "delivery_result",
}

DEDUPLICATION_ALLOWED_IMPORT_ROOTS = {
    "__future__",
    "dataclasses",
    "enum",
    "eligibility",
    "mayak",
    "source_intake",
}

DEDUPLICATION_FORBIDDEN_SOURCE_TOKENS = {
    "requests",
    "httpx",
    "aiohttp",
    "socket",
    "subprocess",
    "sqlalchemy",
    "psycopg",
    "alembic",
    "fastapi",
    "telethon",
    "aiogram",
    "datetime",
    "time",
    "queue",
    "worker",
    "broker",
    "cache",
    "filesystem",
    "network",
    "runtime",
    "database",
    "repository",
    "store",
    "redis",
    "ttl",
    "clock",
    "timestamp",
    "window",
    "episode",
    "obligation",
    "payload",
    "raw_payload",
    "provider_payload",
    "adapter",
    "webhook",
    "mini_app",
    "provider_sdk",
    "cookie",
    "token",
    "secret",
    "credential",
    "claim",
    "lock",
    "migration",
    "schema",
    "dispatch",
    "send(",
    "deliver(",
}

DEDUPLICATION_FORBIDDEN_FIELD_NAMES = {
    "created_at",
    "updated_at",
    "deadline",
    "expiry",
    "clock",
    "timestamp",
    "window_start",
    "window_end",
    "episode_id",
    "obligation_id",
    "retry_backoff",
    "reconciliation_record",
    "provider_payload",
    "raw_payload",
    "delivery_result",
    "provider_result",
    "message_template",
    "template",
    "cookie",
    "token",
    "secret",
    "credential",
    "database",
    "repository",
    "store",
    "redis",
    "ttl",
}

ELIGIBILITY_ALLOWED_IMPORT_ROOTS = {
    "__future__",
    "dataclasses",
    "enum",
    "source_intake",
}

ELIGIBILITY_FORBIDDEN_SOURCE_TOKENS = {
    "requests",
    "httpx",
    "aiohttp",
    "socket",
    "subprocess",
    "sqlalchemy",
    "psycopg",
    "alembic",
    "fastapi",
    "telethon",
    "aiogram",
    "datetime",
    "time",
    "queue",
    "worker",
    "broker",
    "cache",
    "filesystem",
    "network",
    "provider_payload",
    "raw_payload",
    "cookie",
    "token",
    "secret",
    "credential",
    "chat_title",
    "username",
    "phone",
    "body",
    "html",
    "json",
    "payload",
}

ELIGIBILITY_FORBIDDEN_FIELD_NAMES = {
    "raw_payload",
    "provider_payload",
    "cookie",
    "token",
    "secret",
    "credential",
    "chat_title",
    "username",
    "phone",
    "body",
    "html",
    "json",
    "payload",
}

OUTBOX_ALLOWED_IMPORT_ROOTS = {
    "__future__",
    "dataclasses",
    "enum",
    "mayak",
    "eligibility",
    "source_intake",
}

OUTBOX_FORBIDDEN_IMPORT_ROOTS = {
    "aiohttp",
    "alembic",
    "aiogram",
    "fastapi",
    "httpx",
    "psycopg",
    "psycopg2",
    "queue",
    "requests",
    "socket",
    "sqlalchemy",
    "subprocess",
    "telethon",
}

OUTBOX_FORBIDDEN_SOURCE_TOKENS = {
    "requests",
    "httpx",
    "aiohttp",
    "socket",
    "subprocess",
    "sqlalchemy",
    "psycopg",
    "alembic",
    "fastapi",
    "telethon",
    "aiogram",
    "datetime",
    "time",
    "queue",
    "worker",
    "broker",
    "cache",
    "filesystem",
    "network",
    "raw_payload",
    "provider_payload",
    "message_template",
    "template",
    "cookie",
    "token",
    "secret",
    "credential",
    "created_at",
    "updated_at",
    "deadline",
    "expiry",
    "clock",
    "retry_backoff",
    "reconciliation_record",
    "attempt_record",
    "dispatch",
    "scheduler",
    "runtime",
    "provider_call",
    "delivery_plan",
}

OUTBOX_FORBIDDEN_FIELD_NAMES = {
    "created_at",
    "updated_at",
    "deadline",
    "expiry",
    "clock",
    "retry_backoff",
    "reconciliation_record",
    "attempt_record",
    "provider_payload",
    "raw_payload",
    "message_template",
    "template",
    "cookie",
    "token",
    "secret",
    "credential",
}

DELIVERY_PLAN_ALLOWED_IMPORT_ROOTS = {
    "__future__",
    "dataclasses",
    "enum",
    "eligibility",
    "outbox",
}

DELIVERY_PLAN_FORBIDDEN_IMPORT_ROOTS = {
    "aiohttp",
    "alembic",
    "aiogram",
    "fastapi",
    "httpx",
    "mayak",
    "psycopg",
    "psycopg2",
    "queue",
    "requests",
    "socket",
    "sqlalchemy",
    "subprocess",
    "telethon",
}

DELIVERY_PLAN_FORBIDDEN_SOURCE_TOKENS = {
    "requests",
    "httpx",
    "aiohttp",
    "socket",
    "subprocess",
    "sqlalchemy",
    "psycopg",
    "alembic",
    "fastapi",
    "telethon",
    "aiogram",
    "datetime",
    "time",
    "queue",
    "worker",
    "broker",
    "cache",
    "filesystem",
    "network",
    "provider_payload",
    "raw_payload",
    "message_template",
    "template",
    "dispatch",
    "send(",
    "retry_backoff",
    "reconciliation_record",
    "reconciliation",
    "notificationattempt",
    "attempt_id",
    "attempts",
    "render",
    "cookie",
    "token",
    "secret",
    "credential",
    "read_tracking",
    "click_tracking",
    "history",
}

DELIVERY_PLAN_FORBIDDEN_FIELD_NAMES = {
    "created_at",
    "updated_at",
    "deadline",
    "expiry",
    "clock",
    "retry_backoff",
    "reconciliation_record",
    "attempt_id",
    "attempts",
    "provider_payload",
    "raw_payload",
    "message_template",
    "template",
    "dispatch",
    "send",
    "render",
    "cookie",
    "token",
    "secret",
    "credential",
    "primary_channel",
    "fallback_channel",
    "priority",
    "history",
    "read_tracking",
    "click_tracking",
}

ATTEMPT_ALLOWED_IMPORT_ROOTS = {
    "__future__",
    "dataclasses",
    "enum",
    "delivery_plan",
    "eligibility",
    "mayak",
}

ATTEMPT_FORBIDDEN_IMPORT_ROOTS = {
    "aiohttp",
    "alembic",
    "aiogram",
    "fastapi",
    "httpx",
    "psycopg",
    "psycopg2",
    "queue",
    "requests",
    "socket",
    "sqlalchemy",
    "subprocess",
    "telethon",
    "requests",
}

ATTEMPT_FORBIDDEN_SOURCE_TOKENS = {
    "aiohttp",
    "alembic",
    "aiogram",
    "fastapi",
    "httpx",
    "psycopg",
    "psycopg2",
    "queue",
    "requests",
    "socket",
    "sqlalchemy",
    "subprocess",
    "telethon",
    "datetime",
    "time",
    "worker",
    "broker",
    "cache",
    "filesystem",
    "network",
    "webhook",
    "mini_app",
    "playwright",
    "selenium",
    "provider_sdk",
    "cookie",
    "token",
    "secret",
    "credential",
    "read_tracking",
    "click_tracking",
}

ATTEMPT_FORBIDDEN_FIELD_NAMES = {
    "created_at",
    "updated_at",
    "deadline",
    "expiry",
    "clock",
    "raw_payload",
    "provider_payload",
    "message_template",
    "template",
    "cookie",
    "token",
    "secret",
    "credential",
    "url",
    "host",
    "hostname",
    "ip_address",
    "port",
    "request_payload",
    "response_payload",
    "http_status",
    "status_code",
    "read_tracking",
    "click_tracking",
    "history",
}


def _import_roots(source: str) -> set[str]:
    tree = ast.parse(source)
    roots: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            roots.add(node.module.split(".", 1)[0])
            assert not node.module.startswith("mayak.modules"), node.module

    return roots


def _field_names(source: str) -> set[str]:
    tree = ast.parse(source)
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for statement in node.body:
                if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                    names.add(statement.target.id)
    return names


def test_notification_delivery_source_intake_stays_within_allowed_import_boundary() -> None:
    source_path = Path("src/mayak/modules/notification_delivery/source_intake.py")
    source = source_path.read_text()
    roots = _import_roots(source)
    assert roots <= ALLOWED_IMPORT_ROOTS
    assert roots.isdisjoint(FORBIDDEN_IMPORT_ROOTS)


def test_source_intake_runtime_tokens_and_payload_fields() -> None:
    source_path = Path("src/mayak/modules/notification_delivery/source_intake.py")
    source = source_path.read_text().lower()
    for token in FORBIDDEN_SOURCE_TOKENS:
        assert token not in source, token

    field_names = _field_names(source_path.read_text())
    assert field_names.isdisjoint(FORBIDDEN_FIELD_NAMES)


def test_notification_delivery_eligibility_stays_within_allowed_import_boundary() -> None:
    source_path = Path("src/mayak/modules/notification_delivery/eligibility.py")
    source = source_path.read_text()
    roots = _import_roots(source)
    assert roots <= ELIGIBILITY_ALLOWED_IMPORT_ROOTS


def test_eligibility_runtime_tokens_and_payload_fields() -> None:
    source_path = Path("src/mayak/modules/notification_delivery/eligibility.py")
    source = source_path.read_text().lower()
    for token in ELIGIBILITY_FORBIDDEN_SOURCE_TOKENS:
        assert token not in source, token

    field_names = _field_names(source_path.read_text())
    assert field_names.isdisjoint(ELIGIBILITY_FORBIDDEN_FIELD_NAMES)


def test_notification_delivery_outbox_stays_within_allowed_import_boundary() -> None:
    source_path = Path("src/mayak/modules/notification_delivery/outbox.py")
    source = source_path.read_text()
    roots = _import_roots(source)
    assert roots <= OUTBOX_ALLOWED_IMPORT_ROOTS
    assert roots.isdisjoint(OUTBOX_FORBIDDEN_IMPORT_ROOTS)


def test_outbox_runtime_tokens_and_payload_fields() -> None:
    source_path = Path("src/mayak/modules/notification_delivery/outbox.py")
    source = source_path.read_text().lower()
    for token in OUTBOX_FORBIDDEN_SOURCE_TOKENS:
        assert token not in source, token

    field_names = _field_names(source_path.read_text())
    assert field_names.isdisjoint(OUTBOX_FORBIDDEN_FIELD_NAMES)


def test_notification_delivery_plan_stays_within_allowed_import_boundary() -> None:
    source_path = Path("src/mayak/modules/notification_delivery/delivery_plan.py")
    source = source_path.read_text()
    roots = _import_roots(source)
    assert roots <= DELIVERY_PLAN_ALLOWED_IMPORT_ROOTS
    assert roots.isdisjoint(DELIVERY_PLAN_FORBIDDEN_IMPORT_ROOTS)


def test_delivery_plan_runtime_tokens_and_payload_fields() -> None:
    source_path = Path("src/mayak/modules/notification_delivery/delivery_plan.py")
    source = source_path.read_text().lower()
    for token in DELIVERY_PLAN_FORBIDDEN_SOURCE_TOKENS:
        assert token not in source, token

    field_names = _field_names(source_path.read_text())
    assert field_names.isdisjoint(DELIVERY_PLAN_FORBIDDEN_FIELD_NAMES)


def test_notification_delivery_attempt_stays_within_allowed_import_boundary() -> None:
    source_path = Path("src/mayak/modules/notification_delivery/attempt.py")
    source = source_path.read_text()
    roots = _import_roots(source)
    assert roots <= ATTEMPT_ALLOWED_IMPORT_ROOTS
    assert roots.isdisjoint(ATTEMPT_FORBIDDEN_IMPORT_ROOTS)


def test_attempt_runtime_tokens_and_payload_fields() -> None:
    source_path = Path("src/mayak/modules/notification_delivery/attempt.py")
    source = source_path.read_text().lower()
    for token in ATTEMPT_FORBIDDEN_SOURCE_TOKENS:
        assert token not in source, token

    field_names = _field_names(source_path.read_text())
    assert field_names.isdisjoint(ATTEMPT_FORBIDDEN_FIELD_NAMES)


def test_notification_delivery_deduplication_stays_within_allowed_import_boundary() -> None:
    source_path = Path("src/mayak/modules/notification_delivery/deduplication.py")
    source = source_path.read_text()
    roots = _import_roots(source)
    assert roots <= DEDUPLICATION_ALLOWED_IMPORT_ROOTS


def test_deduplication_runtime_tokens_and_payload_fields() -> None:
    source_path = Path("src/mayak/modules/notification_delivery/deduplication.py")
    source = source_path.read_text().lower()
    for token in DEDUPLICATION_FORBIDDEN_SOURCE_TOKENS:
        assert token not in source, token

    field_names = _field_names(source_path.read_text())
    assert field_names.isdisjoint(DEDUPLICATION_FORBIDDEN_FIELD_NAMES)

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

NO_NEW_STATUS_ALLOWED_IMPORT_ROOTS = {
    "__future__",
    "dataclasses",
    "enum",
    "source_intake",
    "eligibility",
    "delivery_plan",
}

NO_NEW_STATUS_FORBIDDEN_SOURCE_TOKENS = {
    "datetime",
    "time",
    "timezone",
    "timestamp",
    "clock",
    "scheduler",
    "cron",
    "polling",
    "queue",
    "worker",
    "broker",
    "cache",
    "filesystem",
    "repository",
    "store",
    "database",
    "orm",
    "migration",
    "schema",
    "http",
    "network",
    "provider_sdk",
    "webhook",
    "mini_app",
    "body",
    "html",
    "json",
    "cookie",
    "token",
    "secret",
    "credential",
    "message_template",
    "template",
    "quiet_hours",
    "digest",
    "read_tracking",
    "click_tracking",
    "retention",
    "deletion",
    "archive",
    "retry_backoff",
    "reconciliation",
    "dispatch(",
    "send(",
    "deliver(",
}

NO_NEW_STATUS_FORBIDDEN_FIELD_NAMES = {
    "created_at",
    "updated_at",
    "deadline",
    "expiry",
    "clock",
    "timestamp",
    "timezone",
    "scheduler",
    "cron",
    "polling",
    "queue",
    "worker",
    "broker",
    "cache",
    "filesystem",
    "repository",
    "store",
    "database",
    "orm",
    "migration",
    "schema",
    "http",
    "network",
    "provider_payload",
    "raw_payload",
    "body",
    "html",
    "json",
    "cookie",
    "token",
    "secret",
    "credential",
    "message_template",
    "template",
    "quiet_hours",
    "digest",
    "read_tracking",
    "click_tracking",
    "retention",
    "deletion",
    "archive",
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


def _build_parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    return parents


def _enclosing_function(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> ast.FunctionDef | None:
    current = parents.get(node)
    while current is not None:
        if isinstance(current, ast.FunctionDef):
            return current
        current = parents.get(current)
    return None


def _assert_no_new_status_ast_boundary(source: str, module_path: Path) -> None:
    tree = ast.parse(source)
    parents = _build_parent_map(tree)
    payload_attributes: list[ast.Attribute] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {"getattr", "setattr", "hasattr"}:
                raise AssertionError(f"{module_path}: reflection call not allowed: {node.func.id}")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            lowered = node.value.lower()
            for token in {"payload", "raw_payload", "provider_payload"}:
                if token in lowered:
                    message = (
                        f"{module_path}: string literal contains forbidden payload token: "
                        f"{node.value!r}"
                    )
                    raise AssertionError(message)
        elif isinstance(node, ast.Name):
            if "payload" in node.id.lower():
                raise AssertionError(
                    f"{module_path}: runtime name contains forbidden payload token: {node.id}"
                )
        elif isinstance(node, ast.Attribute):
            if "payload" in node.attr.lower():
                payload_attributes.append(node)

    assert len(payload_attributes) == 1, (
        f"{module_path}: expected exactly one payload attribute access, "
        f"got {len(payload_attributes)}"
    )

    payload_attribute = payload_attributes[0]
    assert payload_attribute.attr == "contains_raw_provider_payload", (
        f"{module_path}: unexpected payload attribute {payload_attribute.attr}"
    )
    assert isinstance(payload_attribute.value, ast.Name), (
        f"{module_path}: payload attribute must read from source_event"
    )
    assert payload_attribute.value.id == "source_event", (
        f"{module_path}: payload attribute must read from source_event"
    )
    assert isinstance(payload_attribute.ctx, ast.Load), (
        f"{module_path}: payload attribute must be loaded, not stored"
    )

    compare = parents.get(payload_attribute)
    assert isinstance(compare, ast.Compare), (
        f"{module_path}: payload attribute must be used in an is-not-False comparison"
    )
    assert compare.left is payload_attribute, (
        f"{module_path}: payload attribute must be the left side of the comparison"
    )
    assert len(compare.ops) == 1 and isinstance(compare.ops[0], ast.IsNot), (
        f"{module_path}: payload attribute must be compared using is not False"
    )
    assert len(compare.comparators) == 1, (
        f"{module_path}: payload attribute comparison must have one comparator"
    )
    comparator = compare.comparators[0]
    assert isinstance(comparator, ast.Constant) and comparator.value is False, (
        f"{module_path}: payload attribute must be compared against False"
    )

    if_node = parents.get(compare)
    assert isinstance(if_node, ast.If) and if_node.test is compare, (
        f"{module_path}: payload attribute comparison must be used as an if gate"
    )

    function_node = _enclosing_function(payload_attribute, parents)
    assert function_node is not None and function_node.name == "_validate_no_new_source", (
        f"{module_path}: payload attribute must live inside _validate_no_new_source"
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            node_name = node.id.lower()
        elif isinstance(node, ast.Attribute):
            node_name = node.attr.lower()
        else:
            continue

        if "payload" in node_name:
            if node is payload_attribute:
                continue
            raise AssertionError(f"{module_path}: unexpected payload-bearing AST node")


def test_no_new_status_ast_payload_boundary() -> None:
    source_path = Path("src/mayak/modules/notification_delivery/no_new_status.py")
    _assert_no_new_status_ast_boundary(source_path.read_text(), source_path)


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


def test_notification_delivery_no_new_status_stays_within_allowed_import_boundary() -> None:
    source_path = Path("src/mayak/modules/notification_delivery/no_new_status.py")
    source = source_path.read_text()
    roots = _import_roots(source)
    assert roots <= NO_NEW_STATUS_ALLOWED_IMPORT_ROOTS


def test_no_new_status_runtime_tokens_and_payload_fields() -> None:
    source_path = Path("src/mayak/modules/notification_delivery/no_new_status.py")
    source = source_path.read_text().lower()
    for token in NO_NEW_STATUS_FORBIDDEN_SOURCE_TOKENS:
        assert token not in source, token

    field_names = _field_names(source_path.read_text())
    assert field_names.isdisjoint(NO_NEW_STATUS_FORBIDDEN_FIELD_NAMES)

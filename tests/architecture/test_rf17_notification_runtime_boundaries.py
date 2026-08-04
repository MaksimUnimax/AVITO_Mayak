from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

ROOT = Path("src/mayak/modules/notification_delivery")
RUNTIME = ROOT / "runtime.py"

_LIVE_PROVIDER_URL = re.compile(r"https?://", re.IGNORECASE)
_BEARER_VALUE = re.compile(r"^bearer\s+", re.IGNORECASE)
_FORBIDDEN_PROVIDER_IDENTIFIERS = {
    "raw_provider_payload",
    "raw_provider_request",
    "raw_provider_response",
    "provider_payload",
    "provider_request",
    "provider_response",
    "provider_token",
    "access_token",
    "provider_credential",
    "provider_credentials",
    "provider_cookie",
    "provider_cookies",
    "provider_session",
    "provider_session_material",
    "session_cookie",
    "session_cookies",
    "cookies",
}


def _rf17_provider_material_violations(source: str) -> tuple[str, ...]:
    """Return semantic provider-material violations in Notification runtime source.

    First-party authorization names are intentionally not forbidden.  Provider
    material is identified by structured names/keys and literal transport or
    credential values, with parse failure treated as a violation.
    """

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ("syntax-error",)

    violations: set[str] = set()

    def inspect_identifier(value: str) -> None:
        normalized = value.casefold()
        if normalized in _FORBIDDEN_PROVIDER_IDENTIFIERS:
            violations.add(f"provider-identifier:{normalized}")

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            inspect_identifier(node.id)
        elif isinstance(node, ast.Attribute):
            inspect_identifier(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value
            if _LIVE_PROVIDER_URL.search(value):
                violations.add("live-provider-url")
            if _BEARER_VALUE.match(value.strip()):
                violations.add("bearer-provider-credential")
            inspect_identifier(value)

        if isinstance(node, ast.Dict):
            for key in node.keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    inspect_identifier(key.value)

        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            target_names = {
                target.id.casefold()
                for target in targets
                if isinstance(target, ast.Name)
            }
            value = node.value
            if target_names & {"headers", "request_headers", "http_headers"} and isinstance(
                value, ast.Dict
            ):
                if any(
                    isinstance(key, ast.Constant)
                    and isinstance(key.value, str)
                    and key.value.casefold() == "authorization"
                    for key in value.keys
                ):
                    violations.add("authorization-header-key")

    return tuple(sorted(violations))


def _rf17_check_source(source: str) -> None:
    violations = _rf17_provider_material_violations(source)
    assert not violations, ", ".join(violations)


def test_rf17_runtime_has_no_live_provider_or_broker_imports() -> None:
    tree = ast.parse(RUNTIME.read_text(encoding="utf-8"))
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    assert roots.isdisjoint(
        {"httpx", "requests", "aiohttp", "aiogram", "telethon", "redis", "celery", "kombu", "pika"}
    )


def test_rf17_runtime_names_only_the_existing_notification_tables() -> None:
    source = RUNTIME.read_text(encoding="utf-8")
    assert "notification_events" in source
    assert "notification_outbox" in source
    assert "notification_delivery_attempts" in source
    assert "notification_delivery_reconciliations" in source
    assert "notification_endpoints" in source
    assert "rabbitmq" not in source.lower()
    assert "kafka" not in source.lower()
    assert "celery" not in source.lower()


def test_rf17_runtime_does_not_persist_raw_provider_material() -> None:
    _rf17_check_source(RUNTIME.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("case", "source", "expected"),
    [
        (
            "typed first-party read authorization",
            "scope: NotificationReadAuthorizationScope\nauthorization_scope = scope\n",
            (),
        ),
        (
            "first-party authorization decision",
            "authorization_scope = make_first_party_scope()\nread_authorized = True\n",
            (),
        ),
        (
            "first-party authorization state",
            "decision = {'authorization': True, 'scope': 'first-party'}\n",
            (),
        ),
        (
            "raw provider payload field",
            "state.raw_provider_payload = example\n",
            ("provider-identifier:raw_provider_payload",),
        ),
        (
            "provider token field",
            "state.provider_token = 'synthetic-token'\n",
            ("provider-identifier:provider_token",),
        ),
        (
            "provider cookies",
            "state.cookies = {'sid': 'synthetic-cookie'}\n",
            ("provider-identifier:cookies",),
        ),
        (
            "provider session material",
            "state.provider_session = synthetic_session\n",
            ("provider-identifier:provider_session",),
        ),
        (
            "Authorization header",
            "headers = {'Authorization': 'synthetic-header'}\n",
            ("authorization-header-key",),
        ),
        (
            "bearer credential",
            "credential = 'Bearer synthetic-fixture-token'\n",
            ("bearer-provider-credential",),
        ),
        (
            "hard-coded HTTP endpoint",
            "endpoint = 'http://synthetic.provider.invalid'\n",
            ("live-provider-url",),
        ),
        (
            "hard-coded HTTPS endpoint",
            "endpoint = 'https://synthetic.provider.invalid'\n",
            ("live-provider-url",),
        ),
        (
            "raw provider response persisted",
            "state.provider_response = synthetic_response\n",
            ("provider-identifier:provider_response",),
        ),
    ],
)
def test_rf17_provider_material_guard_regression_matrix(
    case: str, source: str, expected: tuple[str, ...]
) -> None:
    actual = _rf17_provider_material_violations(source)
    assert actual == expected, case


def test_rf17_runtime_has_no_process_or_filesystem_execution() -> None:
    tree = ast.parse(RUNTIME.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = (
                node.func.id
                if isinstance(node.func, ast.Name)
                else node.func.attr
                if isinstance(node.func, ast.Attribute)
                else ""
            )
            assert name not in {"exec", "eval", "system", "popen", "run"}

from __future__ import annotations

import ast
from pathlib import Path

from mayak.modules import telegram_adapter

TG02 = {
    "TelegramAccountLinkReference",
    "TelegramIdentityResolutionOutcome",
    "TelegramIdentityResolutionRequest",
    "TelegramIdentityResolutionState",
    "TelegramProviderIdentity",
    "VerifiedTelegramIdentityEvidence",
}
TG03 = {
    "TelegramProviderUpdateIdentity",
    "TelegramUpdateAdmissionState",
    "TelegramUpdateStructuralClass",
    "TelegramUpdateIntakeState",
    "TelegramUpdateDeduplicationState",
    "TelegramUpdateIntakeRecord",
    "TelegramUpdateDeduplicationRecord",
}


def test_package_root_preserves_tg02_and_exports_tg03() -> None:
    assert telegram_adapter.MODULE_ID == "09-telegram-adapter"
    assert TG02 | TG03 <= set(telegram_adapter.__all__)
    assert {name for name in TG02 | TG03 if not hasattr(telegram_adapter, name)} == set()


def test_update_contracts_reuse_shared_primitives_and_have_no_runtime_types() -> None:
    source = (
        Path(__file__).parents[2] / "src/mayak/modules/telegram_adapter/contracts.py"
    ).read_text()
    forbidden_import_roots = {
        "aiogram",
        "telebot",
        "telethon",
        "pyrogram",
        "httpx",
        "requests",
        "aiohttp",
        "urllib3",
        "fastapi",
        "starlette",
        "flask",
        "django",
        "sqlalchemy",
        "psycopg",
        "alembic",
        "celery",
        "redis",
        "kombu",
        "pika",
    }
    forbidden_call_names = {
        "getUpdates",
        "get_updates",
        "setWebhook",
        "set_webhook",
        "deleteWebhook",
        "delete_webhook",
        "getWebhookInfo",
        "get_webhook_info",
        "start_polling",
        "run_polling",
        "poll_forever",
        "serve_forever",
        "create_engine",
        "sessionmaker",
    }
    forbidden_field_names = {
        "raw_payload",
        "provider_payload",
        "raw_update",
        "bot_token",
        "token_value",
        "secret_value",
        "secret_token",
        "webhook_secret",
        "private_key",
        "private_key_value",
        "message_archive",
        "private_message_archive",
    }
    forbidden_declarations = {
        "TelegramClient",
        "TelegramBotClient",
        "TelegramWebhookEndpoint",
        "TelegramPollingLoop",
        "TelegramWorker",
        "TelegramRuntimeService",
        "TelegramRepository",
    }

    def violations(candidate: str) -> set[str]:
        tree = ast.parse(candidate)
        found: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".", 1)[0] in forbidden_import_roots:
                        found.add("forbidden import")
                    if alias.name.startswith("mayak.modules.") and alias.name != (
                        "mayak.modules.telegram_adapter.contracts"
                    ):
                        found.add("foreign module import")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module.split(".", 1)[0] in forbidden_import_roots:
                    found.add("forbidden import")
                if module.startswith("mayak.modules.") and module != (
                    "mayak.modules.telegram_adapter.contracts"
                ):
                    found.add("foreign module import")
            elif isinstance(node, ast.Call):
                function = node.func
                terminal_name = (
                    function.id
                    if isinstance(function, ast.Name)
                    else function.attr
                    if isinstance(function, ast.Attribute)
                    else None
                )
                if terminal_name in forbidden_call_names:
                    found.add("forbidden call")
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                if "api.telegram.org" in node.value:
                    found.add("provider URL")
            elif isinstance(node, ast.ClassDef) and node.name in forbidden_declarations:
                found.add("forbidden declaration")

        def assignment_names(target: ast.AST) -> set[str]:
            if isinstance(target, ast.Name):
                return {target.id}
            if isinstance(target, (ast.Tuple, ast.List)):
                return set().union(*(assignment_names(item) for item in target.elts))
            return set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                targets = node.targets
            elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
                targets = [node.target]
            else:
                continue
            if forbidden_field_names & set().union(
                *(assignment_names(target) for target in targets)
            ):
                found.add("unsafe field")

        for node in tree.body:
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                found.add("top-level runtime instance")
            if isinstance(node, ast.AnnAssign) and isinstance(node.value, ast.Call):
                found.add("top-level runtime instance")
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                found.add("top-level runtime instance")
        return found

    tree = ast.parse(source)
    imports = {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    assert "mayak.contracts" in imports
    assert not violations(source)

    safe = (
        "from typing import Literal\n"
        "class Model:\n"
        "    http_acknowledgement_is_business_success: Literal[False] = False\n"
        "    provider_runtime_authorized: Literal[False] = False\n"
        "    runtime_policy_ref: str\n"
        "    http_acknowledgement_policy_ref: str\n"
        "    webhook_authenticity_policy_ref: str\n"
        "    get_updates_offset_advancement_policy_ref: str\n"
        "    mode = 'WEBHOOK'\n"
        "    other_mode = 'GET_UPDATES'\n"
        "    note = 'runtime/provider call is forbidden'\n"
    )
    assert not violations(safe)

    unsafe_cases = {
        "import httpx": "forbidden import",
        "import os, httpx": "forbidden import",
        "import httpx, os": "forbidden import",
        "import os, httpx, pathlib": "forbidden import",
        "from sqlalchemy import create_engine": "forbidden import",
        "import mayak.modules.identity_and_access": "foreign module import",
        "import os, mayak.modules.identity_and_access": "foreign module import",
        "import mayak.modules.identity_and_access, os": "foreign module import",
        "import os, mayak.modules.identity_and_access, pathlib": (
            "foreign module import"
        ),
        "from mayak.modules.identity_and_access import Identity": (
            "foreign module import"
        ),
        "client.get_updates()": "forbidden call",
        "client.set_webhook('synthetic')": "forbidden call",
        "provider_url = 'https://api.telegram.org/bot'": "provider URL",
        "raw_payload: object": "unsafe field",
        "bot_token: str": "unsafe field",
        "class TelegramWebhookEndpoint: pass": "forbidden declaration",
        "client = Client()": "top-level runtime instance",
    }
    for snippet, expected_violation in unsafe_cases.items():
        assert expected_violation in violations(snippet), snippet

    safe_cases = (
        "import os, pathlib",
        "import mayak.modules.telegram_adapter.contracts",
        "from mayak.modules.telegram_adapter.contracts import TelegramUpdateIntakeRecord",
        "from mayak.contracts import ContractMetadata",
        "http_acknowledgement_is_business_success: Literal[False] = False",
        "provider_runtime_authorized: Literal[False] = False",
        "runtime_policy_ref: str",
        "http_acknowledgement_policy_ref: str",
        "'WEBHOOK'",
        "'GET_UPDATES'",
        "'runtime/provider call is forbidden'",
    )
    for snippet in safe_cases:
        assert not violations(snippet), snippet

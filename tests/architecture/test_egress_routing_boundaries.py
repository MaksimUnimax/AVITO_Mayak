from __future__ import annotations

import ast
import re
import unicodedata
from pathlib import Path

MODULE_FILES = (
    Path("src/mayak/modules/egress_routing/__init__.py"),
    Path("src/mayak/modules/egress_routing/assignment.py"),
    Path("src/mayak/modules/egress_routing/dispatch.py"),
    Path("src/mayak/modules/egress_routing/registration.py"),
    Path("src/mayak/modules/egress_routing/selection.py"),
    Path("src/mayak/modules/egress_routing/fallback.py"),
    Path("src/mayak/modules/egress_routing/contracts.py"),
    Path("src/mayak/modules/egress_routing/fixtures.py"),
    Path("src/mayak/modules/egress_routing/lease.py"),
)

ALLOWED_IMPORT_ROOTS = {
    "__future__",
    "dataclasses",
    "enum",
    "typing",
    "mayak",
}

FORBIDDEN_IMPORT_ROOTS = {
    "aiohttp",
    "alembic",
    "asyncio",
    "bs4",
    "fastapi",
    "httpx",
    "lxml",
    "playwright",
    "psycopg",
    "requests",
    "selenium",
    "socket",
    "sqlalchemy",
    "subprocess",
    "urllib",
}

FORBIDDEN_MODULE_PREFIXES = {
    "mayak.modules.admin_and_support",
    "mayak.modules.beacon_management",
    "mayak.modules.egress_routing",
    "mayak.modules.filter_catalog",
    "mayak.modules.max_adapter",
    "mayak.modules.notification_delivery",
    "mayak.modules.scan_orchestration",
    "mayak.modules.telegram_adapter",
    "mayak.modules.web_cabinet",
}

FORBIDDEN_RUNTIME_IDENTIFIERS = {
    "solve_captcha",
    "captcha_solver",
    "captcha_service",
    "captcha_token",
    "bypass_captcha",
    "anti_captcha",
    "browser_launch",
    "webdriver",
    "network_request",
    "database_connection",
    "session_store",
    "cookie_store",
    "proxy_config",
    "vpn_config",
    "tunnel_config",
}

FORBIDDEN_EXECUTABLE_CALLS = {
    "eval",
    "exec",
    "__import__",
    "import_module",
    "setattr",
    "delattr",
}

FORBIDDEN_DYNAMIC_ENUM_ATTRS = {
    "_member_map_",
    "_value2member_map_",
    "_member_names_",
    "_generate_next_value_",
}

FORBIDDEN_EXACT_FIELD_NAMES = {
    "url",
    "host",
    "hostname",
    "ip",
    "ip_address",
    "port",
    "provider_name",
    "provider",
    "raw_html",
    "raw_json",
    "cookie",
    "cookies",
    "session",
    "sessions",
    "token",
    "private_key",
    "secret_value",
    "payload",
    "body",
    "db_credentials",
}

FORBIDDEN_STRING_VALUES = {
    "avito.ru",
    "www.avito.ru",
    "m.avito.ru",
    "http://",
    "https://",
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
}

ASSIGNMENT_MODULE_PATH = Path("src/mayak/modules/egress_routing/assignment.py")
DISPATCH_MODULE_PATH = Path("src/mayak/modules/egress_routing/dispatch.py")
ASSIGNMENT_ALLOWED_RELATIVE_IMPORTS = {
    "contracts",
    "lease",
}
ASSIGNMENT_ALLOWED_RELATIVE_IMPORT_NAMES = {
    "contracts": {
        "RouteLeaseStatus",
        "RouteReconciliationStatus",
        "RouteRestrictionStatus",
        "TransportAssignment",
    },
    "lease": {
        "RouteLeaseAuthority",
        "RouteLeaseAuthorizationBoundary",
    },
}
ASSIGNMENT_FORBIDDEN_IDENTIFIERS = {
    "DispatchAttempt",
    "DispatchStatus",
    "TransportAssignmentOutcome",
    "TransportOutcomeStatus",
    "PolicyBasedFallbackBoundary",
    "subprocess",
    "socket",
    "sqlalchemy",
    "alembic",
    "playwright",
    "selenium",
    "requests",
    "httpx",
    "aiohttp",
    "eval",
    "exec",
    "__import__",
    "import_module",
    "browser",
    "windows",
    "provider",
    "proxy",
    "vpn",
    "tunnel",
    "host",
    "hostname",
    "ip",
    "port",
    "account",
    "beacon",
    "tariff",
    "payment",
    "listing",
    "notification",
    "parser",
    "scan",
    "admin",
}

DISPATCH_ALLOWED_RELATIVE_IMPORTS = {
    "assignment",
    "contracts",
}
DISPATCH_ALLOWED_RELATIVE_IMPORT_NAMES = {
    "assignment": {
        "TransportAssignmentAuthority",
        "TransportAssignmentCommitmentBoundary",
    },
    "contracts": {
        "DispatchAttempt",
        "DispatchStatus",
        "RouteLeaseStatus",
        "RouteReconciliationStatus",
        "RouteRestrictionStatus",
    },
}
DISPATCH_FORBIDDEN_IDENTIFIERS = {
    "TransportAssignmentOutcome",
    "TransportOutcomeStatus",
    "PolicyBasedFallbackBoundary",
    "subprocess",
    "socket",
    "sqlalchemy",
    "alembic",
    "playwright",
    "selenium",
    "requests",
    "httpx",
    "aiohttp",
    "eval",
    "exec",
    "__import__",
    "import_module",
    "browser",
    "windows",
    "provider",
    "proxy",
    "vpn",
    "tunnel",
    "host",
    "hostname",
    "ip",
    "port",
    "account",
    "beacon",
    "tariff",
    "payment",
    "listing",
    "notification",
    "parser",
    "scan",
    "admin",
    "response_payload",
    "response_body",
    "receipt_payload",
    "send_payload",
    "transport_outcome",
    "safe_response_reference",
    "response_status",
    "reconciliation_result",
    "retry_count",
    "retry_delay",
    "backoff",
    "duration",
    "timeout_seconds",
    "capacity",
    "expires_at",
    "protocol",
    "cookie_value",
    "session_value",
    "credential_value",
    "Parser",
    "Scan",
    "Notification",
    "Beacon",
    "Admin",
}


def _read_source(path: Path) -> str:
    repo_root = Path(__file__).resolve().parents[2]
    return (repo_root / path).read_text()


def _iter_identifier_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
    return names


def _is_dataclass_decorator(decorator: ast.expr) -> bool:
    if isinstance(decorator, ast.Call):
        decorator = decorator.func
    return isinstance(decorator, ast.Name) and decorator.id == "dataclass"


def _dataclass_field_names(tree: ast.AST) -> dict[str, tuple[str, ...]]:
    result: dict[str, tuple[str, ...]] = {}
    for node in getattr(tree, "body", []):
        if not isinstance(node, ast.ClassDef):
            continue
        if not any(_is_dataclass_decorator(decorator) for decorator in node.decorator_list):
            continue
        field_names: list[str] = []
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                field_names.append(item.target.id)
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        field_names.append(target.id)
        result[node.name] = tuple(field_names)
    return result


def _import_issues(tree: ast.AST) -> tuple[set[str], set[str]]:
    forbidden_roots: set[str] = set()
    forbidden_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root not in ALLOWED_IMPORT_ROOTS:
                    forbidden_roots.add(root)
                if root in FORBIDDEN_IMPORT_ROOTS:
                    forbidden_roots.add(root)
                if any(alias.name.startswith(prefix) for prefix in FORBIDDEN_MODULE_PREFIXES):
                    forbidden_modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level > 0 or node.module is None:
                continue
            root = node.module.split(".", 1)[0]
            if root not in ALLOWED_IMPORT_ROOTS and not node.module.startswith("mayak.platform"):
                forbidden_roots.add(root)
            if root in FORBIDDEN_IMPORT_ROOTS:
                forbidden_roots.add(root)
            if any(node.module.startswith(prefix) for prefix in FORBIDDEN_MODULE_PREFIXES):
                forbidden_modules.add(node.module)
    return forbidden_roots, forbidden_modules


def _string_issues(tree: ast.AST) -> set[str]:
    issues: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        value = node.value.lower()
        if any(fragment in value for fragment in FORBIDDEN_STRING_VALUES):
            issues.add(node.value)
        if re.search(r"https?://", node.value):
            issues.add(node.value)
        if re.search(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", node.value):
            issues.add(node.value)
    return issues


def _obfuscation_issues(source: str, tree: ast.AST) -> set[str]:
    issues: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            if all(
                isinstance(side, ast.Constant) and isinstance(side.value, str)
                for side in (node.left, node.right)
            ):
                issues.add("string-concatenation")
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            segment = ast.get_source_segment(source, node) or node.value
            if "\\x" in segment or "\\u" in segment:
                issues.add("escaped-hex-or-unicode")
    return issues


def _identifiers_are_ascii_and_stable(tree: ast.AST) -> None:
    for name in _iter_identifier_names(tree):
        assert name.isascii(), f"non-ASCII identifier: {name!r}"
        assert unicodedata.normalize("NFKC", name) == name, f"unstable identifier: {name!r}"


def test_egress_routing_modules_use_only_allowed_imports_and_static_ast() -> None:
    for relative_path in MODULE_FILES:
        source = _read_source(relative_path)
        tree = ast.parse(source)

        forbidden_roots, forbidden_modules = _import_issues(tree)
        assert forbidden_roots == set(), f"{relative_path}: {sorted(forbidden_roots)}"
        assert forbidden_modules == set(), f"{relative_path}: {sorted(forbidden_modules)}"

        identifiers = _iter_identifier_names(tree)
        assert FORBIDDEN_RUNTIME_IDENTIFIERS.isdisjoint(identifiers)
        assert FORBIDDEN_EXECUTABLE_CALLS.isdisjoint(identifiers)
        assert FORBIDDEN_DYNAMIC_ENUM_ATTRS.isdisjoint(identifiers)

        string_issues = _string_issues(tree)
        assert string_issues == set(), f"{relative_path}: {sorted(string_issues)}"

        obfuscation_issues = _obfuscation_issues(source, tree)
        assert obfuscation_issues == set(), f"{relative_path}: {sorted(obfuscation_issues)}"

        _identifiers_are_ascii_and_stable(tree)


def test_assignment_module_imports_and_identifiers_are_minimal() -> None:
    source = _read_source(ASSIGNMENT_MODULE_PATH)
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                assert root in {"__future__", "dataclasses", "enum"}
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                assert node.level > 0
                continue
            if node.level == 0:
                root = node.module.split(".", 1)[0]
                assert root in {"__future__", "dataclasses", "enum"}
                continue
            assert node.module in ASSIGNMENT_ALLOWED_RELATIVE_IMPORTS
            imported_names = {alias.name for alias in node.names}
            assert imported_names == ASSIGNMENT_ALLOWED_RELATIVE_IMPORT_NAMES[node.module]

    identifiers = _iter_identifier_names(tree)
    assert ASSIGNMENT_FORBIDDEN_IDENTIFIERS.isdisjoint(identifiers)


def test_dispatch_module_imports_and_identifiers_are_minimal() -> None:
    source = _read_source(DISPATCH_MODULE_PATH)
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                assert root in {"__future__", "dataclasses", "enum"}
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                assert node.level > 0
                continue
            if node.level == 0:
                root = node.module.split(".", 1)[0]
                assert root in {"__future__", "dataclasses", "enum"}
                continue
            assert node.module in DISPATCH_ALLOWED_RELATIVE_IMPORTS
            imported_names = {alias.name for alias in node.names}
            assert imported_names == DISPATCH_ALLOWED_RELATIVE_IMPORT_NAMES[node.module]

    identifiers = _iter_identifier_names(tree)
    assert DISPATCH_FORBIDDEN_IDENTIFIERS.isdisjoint(identifiers)


def test_egress_routing_dataclass_field_names_do_not_expose_forbidden_runtime_configuration() -> (
    None
):
    forbidden_field_hits: dict[str, tuple[str, ...]] = {}
    for relative_path in (
        Path("src/mayak/modules/egress_routing/contracts.py"),
        Path("src/mayak/modules/egress_routing/registration.py"),
        Path("src/mayak/modules/egress_routing/selection.py"),
        Path("src/mayak/modules/egress_routing/fallback.py"),
        Path("src/mayak/modules/egress_routing/lease.py"),
        Path("src/mayak/modules/egress_routing/dispatch.py"),
    ):
        source = _read_source(relative_path)
        tree = ast.parse(source)
        dataclass_fields = _dataclass_field_names(tree)

        for class_name, field_names in dataclass_fields.items():
            hits = tuple(
                name for name in field_names if name.lower() in FORBIDDEN_EXACT_FIELD_NAMES
            )
            if hits:
                forbidden_field_hits[f"{relative_path}:{class_name}"] = hits

    assert forbidden_field_hits == {}


def test_egress_routing_semantic_literals_remain_allowed() -> None:
    source = _read_source(Path("src/mayak/modules/egress_routing/contracts.py"))
    tree = ast.parse(source)
    identifiers = _iter_identifier_names(tree)

    assert "SessionPolicyStatus" in identifiers
    assert "CAPTCHA_OR_CHALLENGE" in identifiers
    assert "credential_reference" in identifiers
    assert "RouteFamily" in identifiers

from __future__ import annotations

import ast
import re
import unicodedata
from pathlib import Path

MODULE_FILES = (
    Path("src/mayak/modules/egress_routing/__init__.py"),
    Path("src/mayak/modules/egress_routing/assignment.py"),
    Path("src/mayak/modules/egress_routing/dispatch.py"),
    Path("src/mayak/modules/egress_routing/outcome.py"),
    Path("src/mayak/modules/egress_routing/replay.py"),
    Path("src/mayak/modules/egress_routing/reconciliation.py"),
    Path("src/mayak/modules/egress_routing/reconciliation_resolution.py"),
    Path("src/mayak/modules/egress_routing/outcome_availability.py"),
    Path("src/mayak/modules/egress_routing/outcome_response.py"),
    Path("src/mayak/modules/egress_routing/outcome_response_failure.py"),
    Path("src/mayak/modules/egress_routing/restriction_signal.py"),
    Path("src/mayak/modules/egress_routing/outcome_fallback.py"),
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
    "captcha_bypass",
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

OUTCOME_MODULE_PATH = Path("src/mayak/modules/egress_routing/outcome.py")
OUTCOME_ALLOWED_RELATIVE_IMPORTS = {
    "contracts",
    "dispatch",
}
OUTCOME_ALLOWED_RELATIVE_IMPORT_NAMES = {
    "contracts": {
        "DispatchStatus",
        "RouteReconciliationStatus",
        "TransportAssignmentOutcome",
        "TransportOutcomeStatus",
    },
    "dispatch": {
        "TransportDispatchAuthority",
        "TransportDispatchAttemptBoundary",
    },
}
OUTCOME_FORBIDDEN_IDENTIFIERS = {
    "TransportAssignment",
    "DispatchAttempt",
    "TransportAssignmentCommitmentBoundary",
    "RouteLeaseAuthorizationBoundary",
    "TransportDispatchReplayBoundary",
    "TransportDispatchReconciliationBoundary",
    "TransportDispatchReconciliationResolutionBoundary",
    "PolicyBasedFallbackBoundary",
    "RouteRestrictionState",
    "RouteQuarantineDecision",
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

OUTCOME_AVAILABILITY_MODULE_PATH = Path("src/mayak/modules/egress_routing/outcome_availability.py")
OUTCOME_AVAILABILITY_ALLOWED_RELATIVE_IMPORTS = {
    "assignment",
    "contracts",
    "dispatch",
}
OUTCOME_AVAILABILITY_ALLOWED_RELATIVE_IMPORT_NAMES = {
    "assignment": {
        "TransportAssignmentCommitmentBoundary",
    },
    "contracts": {
        "DispatchAttempt",
        "DispatchStatus",
        "RouteReconciliationStatus",
        "TransportAssignment",
        "TransportAssignmentOutcome",
        "TransportOutcomeStatus",
    },
    "dispatch": {
        "TransportDispatchAttemptBoundary",
        "TransportDispatchAuthority",
    },
}
OUTCOME_AVAILABILITY_FORBIDDEN_IDENTIFIERS = (
    OUTCOME_FORBIDDEN_IDENTIFIERS
    - {
        "DispatchAttempt",
        "TransportAssignment",
        "TransportAssignmentCommitmentBoundary",
    }
) | {
    "TransportOutcomeCommitmentBoundary",
}

OUTCOME_RESPONSE_MODULE_PATH = Path("src/mayak/modules/egress_routing/outcome_response.py")
OUTCOME_RESPONSE_ALLOWED_RELATIVE_IMPORTS = {
    "assignment",
    "contracts",
    "dispatch",
}
OUTCOME_RESPONSE_ALLOWED_RELATIVE_IMPORT_NAMES = {
    "assignment": {
        "TransportAssignmentCommitmentBoundary",
    },
    "contracts": {
        "DispatchStatus",
        "DispatchAttempt",
        "RouteReconciliationStatus",
        "TransportAssignment",
        "TransportAssignmentOutcome",
        "TransportOutcomeStatus",
    },
    "dispatch": {
        "TransportDispatchAttemptBoundary",
        "TransportDispatchAuthority",
    },
}
OUTCOME_RESPONSE_FORBIDDEN_IDENTIFIERS = (
    OUTCOME_FORBIDDEN_IDENTIFIERS
    - {
        "DispatchAttempt",
        "TransportAssignment",
        "TransportAssignmentCommitmentBoundary",
    }
) | {
    "RouteLeaseAuthorizationBoundary",
    "TransportDispatchReplayBoundary",
    "TransportDispatchReconciliationBoundary",
    "TransportDispatchReconciliationResolutionBoundary",
    "PolicyBasedFallbackBoundary",
    "TransportOutcomeCommitmentBoundary",
    "TransportAvailabilityOutcomeBoundary",
    "ParserAttemptOutcome",
    "TransportOutcomeReference",
    "TransportResponseClassificationOutcome",
    "ParserOutcomeStatus",
    "ProviderResponseEvidenceClass",
    "ResponseCompletenessStatus",
    "ResponseRestrictionSignal",
    "content",
    "listing",
    "anchor",
    "baseline",
    "health",
    "quarantine",
    "fallback",
    "second_attempt",
    "retry_attempt",
}

OUTCOME_RESPONSE_FAILURE_MODULE_PATH = Path(
    "src/mayak/modules/egress_routing/outcome_response_failure.py"
)
OUTCOME_RESPONSE_FAILURE_ALLOWED_RELATIVE_IMPORTS = {
    "assignment",
    "contracts",
    "dispatch",
}
OUTCOME_RESPONSE_FAILURE_ALLOWED_RELATIVE_IMPORT_NAMES = {
    "assignment": {
        "TransportAssignmentCommitmentBoundary",
    },
    "contracts": {
        "DispatchAttempt",
        "DispatchStatus",
        "RouteReconciliationStatus",
        "TransportAssignment",
        "TransportAssignmentOutcome",
        "TransportOutcomeStatus",
    },
    "dispatch": {
        "TransportDispatchAttemptBoundary",
        "TransportDispatchAuthority",
    },
}
OUTCOME_RESPONSE_FAILURE_FORBIDDEN_IDENTIFIERS = (
    OUTCOME_FORBIDDEN_IDENTIFIERS
    - {
        "DispatchAttempt",
        "TransportAssignment",
        "TransportAssignmentCommitmentBoundary",
    }
) | {
    "RouteLeaseAuthorizationBoundary",
    "TransportDispatchReplayBoundary",
    "TransportDispatchReconciliationBoundary",
    "TransportDispatchReconciliationResolutionBoundary",
    "PolicyBasedFallbackBoundary",
    "TransportOutcomeCommitmentBoundary",
    "TransportAvailabilityOutcomeBoundary",
    "TransportResponsePresenceOutcomeBoundary",
    "ParserAttemptOutcome",
    "ParserOutcomeStatus",
    "ResponseCompletenessStatus",
    "ResponseRestrictionSignal",
    "ProviderResponseEvidenceClass",
    "RouteRestrictionState",
    "RouteQuarantineDecision",
    "content",
    "listing",
    "anchor",
    "baseline",
    "health",
    "quarantine",
    "fallback",
    "second_attempt",
    "retry_attempt",
    "retry",
    "backoff",
    "captcha_solver",
    "captcha_bypass",
}

RESTRICTION_SIGNAL_MODULE_PATH = Path("src/mayak/modules/egress_routing/restriction_signal.py")
RESTRICTION_SIGNAL_ALLOWED_RELATIVE_IMPORTS = {
    "assignment",
    "contracts",
    "dispatch",
    "outcome_response_failure",
}
RESTRICTION_SIGNAL_ALLOWED_RELATIVE_IMPORT_NAMES = {
    "assignment": {
        "TransportAssignmentAuthority",
        "TransportAssignmentCommitmentBoundary",
    },
    "contracts": {
        "DispatchAttempt",
        "DispatchStatus",
        "TransportAssignment",
        "TransportAssignmentOutcome",
        "TransportOutcomeStatus",
    },
    "dispatch": {
        "TransportDispatchAttemptBoundary",
        "TransportDispatchAuthority",
    },
    "outcome_response_failure": {
        "TransportResponseFailureOutcomeAuthority",
        "TransportResponseFailureOutcomeBoundary",
    },
}
RESTRICTION_SIGNAL_FORBIDDEN_IDENTIFIERS = {
    "RouteHealthState",
    "RouteRestrictionState",
    "RouteQuarantineDecision",
    "PolicyBasedFallbackBoundary",
    "TransportAvailabilityOutcomeBoundary",
    "TransportOutcomeCommitmentBoundary",
    "TransportResponsePresenceOutcomeBoundary",
    "RouteReadinessDecision",
    "RouteSelectionDecision",
    "Parser",
    "Scan",
    "Notification",
    "Beacon",
    "Admin",
    "raw_response",
    "response_body",
    "response_payload",
    "captcha_solver",
    "captcha_bypass",
}

OUTCOME_FALLBACK_MODULE_PATH = Path("src/mayak/modules/egress_routing/outcome_fallback.py")
OUTCOME_FALLBACK_ALLOWED_RELATIVE_IMPORTS = {
    "contracts",
    "fallback",
    "selection",
}
OUTCOME_FALLBACK_ALLOWED_RELATIVE_IMPORT_NAMES = {
    "contracts": {
        "PolicyBasedFallbackDecision",
        "PolicyBasedFallbackStatus",
        "RouteReconciliationStatus",
        "RouteSelectionDecision",
        "RouteSelectionStatus",
        "TransportOutcomeStatus",
    },
    "fallback": {
        "PolicyBasedFallbackBoundary",
    },
    "selection": {
        "RouteCandidateEligibilityStatus",
        "RouteCandidateEvaluation",
        "RouteSelectionAuthority",
        "ServerRouteSelectionBoundary",
    },
}
OUTCOME_FALLBACK_FORBIDDEN_IDENTIFIERS = (
    OUTCOME_RESPONSE_FAILURE_FORBIDDEN_IDENTIFIERS
    - {
        "PolicyBasedFallbackBoundary",
        "fallback",
    }
) | {
    "RouteHealthState",
    "RouteReadinessDecision",
    "RouteRestrictionState",
    "RouteQuarantineDecision",
    "TransportAssignment",
    "TransportAssignmentOutcome",
    "DispatchAttempt",
    "TransportDispatchAttemptBoundary",
    "RouteLeaseAuthorizationBoundary",
    "TransportOutcomeCommitmentBoundary",
    "TransportAvailabilityOutcomeBoundary",
    "TransportResponsePresenceOutcomeBoundary",
    "TransportResponseFailureOutcomeBoundary",
    "ParserAttemptOutcome",
    "ParserOutcomeStatus",
    "content",
    "listing",
    "baseline",
    "anchor",
    "pending_recovery",
    "captcha_solver",
    "captcha_bypass",
    "retry",
    "replay",
    "backoff",
    "network",
    "runtime",
    "storage",
    "provider",
    "proxy",
    "vpn",
    "tunnel",
    "browser",
    "windows",
}

REPLAY_MODULE_PATH = Path("src/mayak/modules/egress_routing/replay.py")
REPLAY_ALLOWED_RELATIVE_IMPORTS = {
    "contracts",
    "dispatch",
}
REPLAY_ALLOWED_RELATIVE_IMPORT_NAMES = {
    "contracts": {"DispatchStatus"},
    "dispatch": {
        "TransportDispatchAttemptBoundary",
        "TransportDispatchAuthority",
    },
}
REPLAY_FORBIDDEN_IDENTIFIERS = {
    "DispatchAttempt",
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

RECONCILIATION_MODULE_PATH = Path("src/mayak/modules/egress_routing/reconciliation.py")
RECONCILIATION_ALLOWED_RELATIVE_IMPORTS = {
    "contracts",
    "dispatch",
}
RECONCILIATION_ALLOWED_RELATIVE_IMPORT_NAMES = {
    "contracts": {
        "DispatchStatus",
        "RouteReconciliationState",
        "RouteReconciliationStatus",
    },
    "dispatch": {
        "TransportDispatchAttemptBoundary",
        "TransportDispatchAuthority",
    },
}
RECONCILIATION_FORBIDDEN_IDENTIFIERS = {
    "DispatchAttempt",
    "TransportAssignmentOutcome",
    "TransportOutcomeStatus",
    "TransportDispatchReplayBoundary",
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

RECONCILIATION_RESOLUTION_MODULE_PATH = Path(
    "src/mayak/modules/egress_routing/reconciliation_resolution.py"
)
RECONCILIATION_RESOLUTION_ALLOWED_RELATIVE_IMPORTS = {
    "contracts",
    "reconciliation",
}
RECONCILIATION_RESOLUTION_ALLOWED_RELATIVE_IMPORT_NAMES = {
    "contracts": {
        "RouteReconciliationState",
        "RouteReconciliationStatus",
    },
    "reconciliation": {
        "TransportDispatchReconciliationAuthority",
        "TransportDispatchReconciliationBoundary",
    },
}
RECONCILIATION_RESOLUTION_FORBIDDEN_IDENTIFIERS = {
    "DispatchAttempt",
    "TransportAssignmentOutcome",
    "TransportOutcomeStatus",
    "TransportDispatchAttemptBoundary",
    "TransportDispatchReplayBoundary",
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


def test_restriction_signal_module_imports_and_identifiers_are_minimal() -> None:
    source = _read_source(RESTRICTION_SIGNAL_MODULE_PATH)
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                assert root in {"__future__", "dataclasses", "enum", "typing"}
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                assert node.level > 0
                continue
            if node.level == 0:
                root = node.module.split(".", 1)[0]
                assert root in {"__future__", "dataclasses", "enum", "typing"}
                continue
            assert node.module in RESTRICTION_SIGNAL_ALLOWED_RELATIVE_IMPORTS
            imported_names = {alias.name for alias in node.names}
            assert imported_names == RESTRICTION_SIGNAL_ALLOWED_RELATIVE_IMPORT_NAMES[node.module]

    identifiers = _iter_identifier_names(tree)
    assert RESTRICTION_SIGNAL_FORBIDDEN_IDENTIFIERS.isdisjoint(identifiers)


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


def test_outcome_module_imports_and_identifiers_are_minimal() -> None:
    source = _read_source(OUTCOME_MODULE_PATH)
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
            assert node.module in OUTCOME_ALLOWED_RELATIVE_IMPORTS
            imported_names = {alias.name for alias in node.names}
            assert imported_names == OUTCOME_ALLOWED_RELATIVE_IMPORT_NAMES[node.module]

    identifiers = _iter_identifier_names(tree)
    assert OUTCOME_FORBIDDEN_IDENTIFIERS.isdisjoint(identifiers)


def test_outcome_availability_module_imports_and_identifiers_are_minimal() -> None:
    source = _read_source(OUTCOME_AVAILABILITY_MODULE_PATH)
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                assert root in {"__future__", "dataclasses", "enum", "typing"}
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                assert node.level > 0
                continue
            if node.level == 0:
                root = node.module.split(".", 1)[0]
                assert root in {"__future__", "dataclasses", "enum", "typing"}
                continue
            assert node.module in OUTCOME_AVAILABILITY_ALLOWED_RELATIVE_IMPORTS
            imported_names = {alias.name for alias in node.names}
            assert imported_names == OUTCOME_AVAILABILITY_ALLOWED_RELATIVE_IMPORT_NAMES[node.module]

    identifiers = _iter_identifier_names(tree)
    assert OUTCOME_AVAILABILITY_FORBIDDEN_IDENTIFIERS.isdisjoint(identifiers)


def test_outcome_response_module_imports_and_identifiers_are_minimal() -> None:
    source = _read_source(OUTCOME_RESPONSE_MODULE_PATH)
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
            assert node.module in OUTCOME_RESPONSE_ALLOWED_RELATIVE_IMPORTS
            imported_names = {alias.name for alias in node.names}
            assert imported_names == OUTCOME_RESPONSE_ALLOWED_RELATIVE_IMPORT_NAMES[node.module]

    identifiers = _iter_identifier_names(tree)
    assert OUTCOME_RESPONSE_FORBIDDEN_IDENTIFIERS.isdisjoint(identifiers)


def test_outcome_response_failure_module_imports_and_identifiers_are_minimal() -> None:
    source = _read_source(OUTCOME_RESPONSE_FAILURE_MODULE_PATH)
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
            assert node.module in OUTCOME_RESPONSE_FAILURE_ALLOWED_RELATIVE_IMPORTS
            imported_names = {alias.name for alias in node.names}
            assert (
                imported_names
                == OUTCOME_RESPONSE_FAILURE_ALLOWED_RELATIVE_IMPORT_NAMES[node.module]
            )

    identifiers = _iter_identifier_names(tree)
    assert OUTCOME_RESPONSE_FAILURE_FORBIDDEN_IDENTIFIERS.isdisjoint(identifiers)


def test_outcome_fallback_module_imports_and_identifiers_are_minimal() -> None:
    source = _read_source(OUTCOME_FALLBACK_MODULE_PATH)
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
            assert node.module in OUTCOME_FALLBACK_ALLOWED_RELATIVE_IMPORTS
            imported_names = {alias.name for alias in node.names}
            assert imported_names == OUTCOME_FALLBACK_ALLOWED_RELATIVE_IMPORT_NAMES[node.module]

    identifiers = _iter_identifier_names(tree)
    assert OUTCOME_FALLBACK_FORBIDDEN_IDENTIFIERS.isdisjoint(identifiers)
    assert {
        "ER07E_TASK_ID",
        "PolicyFallbackTransportOutcomeAuthority",
        "PolicyFallbackTransportOutcomeBoundary",
        "outcome_status",
        "transport_terminal",
        "new_fallback_effect_authorized",
        "parser_success_inferred",
        "scan_success_inferred",
        "notification_delivery_inferred",
    }.issubset(identifiers)


def test_replay_module_imports_and_identifiers_are_minimal() -> None:
    source = _read_source(REPLAY_MODULE_PATH)
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                assert root in {"__future__", "dataclasses", "enum", "mayak"}
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                assert node.level > 0
                continue
            if node.level == 0:
                root = node.module.split(".", 1)[0]
                assert root in {"__future__", "dataclasses", "enum", "mayak"}
                continue
            assert node.module in REPLAY_ALLOWED_RELATIVE_IMPORTS
            imported_names = {alias.name for alias in node.names}
            assert imported_names == REPLAY_ALLOWED_RELATIVE_IMPORT_NAMES[node.module]

    identifiers = _iter_identifier_names(tree)
    assert REPLAY_FORBIDDEN_IDENTIFIERS.isdisjoint(identifiers)
    assert {
        "original_scope",
        "original_key",
        "original_fingerprint",
        "replay_scope",
        "replay_key",
        "replay_fingerprint",
        "original_attempt_reference",
        "replay_dispatch_effect_authorized",
        "reconciliation_required",
    }.issubset(identifiers)


def test_reconciliation_module_imports_and_identifiers_are_minimal() -> None:
    source = _read_source(RECONCILIATION_MODULE_PATH)
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
            assert node.module in RECONCILIATION_ALLOWED_RELATIVE_IMPORTS
            imported_names = {alias.name for alias in node.names}
            assert imported_names == RECONCILIATION_ALLOWED_RELATIVE_IMPORT_NAMES[node.module]

    identifiers = _iter_identifier_names(tree)
    assert RECONCILIATION_FORBIDDEN_IDENTIFIERS.isdisjoint(identifiers)
    assert {
        "dispatch_attempt",
        "reconciliation_state",
        "reconciliation_state_committed",
        "new_dispatch_effect_authorized",
        "assignment_terminal",
        "resolved_outcome_reference",
        "reason_codes",
        "evidence_reference_ids",
    }.issubset(identifiers)


def test_reconciliation_resolution_module_imports_and_identifiers_are_minimal() -> None:
    source = _read_source(RECONCILIATION_RESOLUTION_MODULE_PATH)
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
            assert node.module in RECONCILIATION_RESOLUTION_ALLOWED_RELATIVE_IMPORTS
            imported_names = {alias.name for alias in node.names}
            assert (
                imported_names
                == RECONCILIATION_RESOLUTION_ALLOWED_RELATIVE_IMPORT_NAMES[node.module]
            )

    identifiers = _iter_identifier_names(tree)
    assert RECONCILIATION_RESOLUTION_FORBIDDEN_IDENTIFIERS.isdisjoint(identifiers)
    assert {
        "unresolved_reconciliation",
        "resolved_reconciliation_state",
        "resolution_committed",
        "new_dispatch_effect_authorized",
        "assignment_terminal",
        "resolved_outcome_reference",
        "reason_codes",
        "evidence_reference_ids",
    }.issubset(identifiers)


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
        Path("src/mayak/modules/egress_routing/replay.py"),
        Path("src/mayak/modules/egress_routing/reconciliation.py"),
        Path("src/mayak/modules/egress_routing/reconciliation_resolution.py"),
        Path("src/mayak/modules/egress_routing/outcome.py"),
        Path("src/mayak/modules/egress_routing/outcome_availability.py"),
        Path("src/mayak/modules/egress_routing/outcome_response.py"),
        Path("src/mayak/modules/egress_routing/outcome_fallback.py"),
        Path("src/mayak/modules/egress_routing/restriction_signal.py"),
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

from __future__ import annotations

import ast
from pathlib import Path


MODULE_FILES = (
    Path("src/mayak/modules/avito_parser_adapter/__init__.py"),
    Path("src/mayak/modules/avito_parser_adapter/contracts.py"),
    Path("src/mayak/modules/avito_parser_adapter/fixtures.py"),
)

ALLOWED_IMPORT_ROOTS = {
    "__future__",
    "dataclasses",
    "enum",
    "mayak",
    "typing",
}

def _fragment(*parts: str) -> str:
    return "".join(parts)


FORBIDDEN_IMPORT_ROOTS = {
    _fragment("a", "i", "o", "h", "t", "t", "p"),
    _fragment("a", "l", "e", "m", "b", "i", "c"),
    _fragment("b", "s", "4"),
    _fragment("h", "t", "t", "p", "x"),
    _fragment("l", "x", "m", "l"),
    _fragment("p", "l", "a", "y", "w", "r", "i", "g", "h", "t"),
    _fragment("p", "s", "y", "c", "o", "p", "g"),
    _fragment("r", "e", "q", "u", "e", "s", "t", "s"),
    _fragment("s", "e", "l", "e", "n", "i", "u", "m"),
    _fragment("s", "q", "l", "a", "l", "c", "h", "e", "m", "y"),
    _fragment("u", "r", "l", "l", "i", "b"),
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

FORBIDDEN_TEXT_FRAGMENTS = {
    _fragment("a", "v", "i", "t", "o", ".", "r", "u"),
    _fragment("w", "w", "w", ".", "a", "v", "i", "t", "o", ".", "r", "u"),
    _fragment("m", ".", "a", "v", "i", "t", "o", ".", "r", "u"),
    _fragment("h", "t", "t", "p", "x"),
    _fragment("r", "e", "q", "u", "e", "s", "t", "s"),
    _fragment("a", "i", "o", "h", "t", "t", "p"),
    _fragment("s", "e", "l", "e", "n", "i", "u", "m"),
    _fragment("p", "l", "a", "y", "w", "r", "i", "g", "h", "t"),
    _fragment("b", "s", "4"),
    _fragment("l", "x", "m", "l"),
    _fragment("s", "q", "l", "a", "l", "c", "h", "e", "m", "y"),
    _fragment("p", "s", "y", "c", "o", "p", "g"),
    _fragment("a", "l", "e", "m", "b", "i", "c"),
    _fragment("c", "o", "o", "k", "i", "e", "s"),
    _fragment("s", "e", "s", "s", "i", "o", "n"),
    _fragment("p", "r", "o", "x", "y"),
}

FORBIDDEN_CAPTCHA_RUNTIME_FRAGMENTS = {
    "solve_captcha",
    "captcha_solver",
    "captcha_service",
    "captcha_token",
    "captcha_cookie",
    "bypass_captcha",
    "anti_captcha",
    "2captcha",
    "rucaptcha",
}


def _import_issues(source: str) -> tuple[set[str], set[str]]:
    tree = ast.parse(source)
    forbidden_roots: set[str] = set()
    forbidden_modules: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root not in ALLOWED_IMPORT_ROOTS:
                    forbidden_roots.add(root)
                if any(alias.name.startswith(prefix) for prefix in FORBIDDEN_MODULE_PREFIXES):
                    forbidden_modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level > 0:
                continue
            if node.module is None:
                continue
            root = node.module.split(".", 1)[0]
            if root not in ALLOWED_IMPORT_ROOTS:
                forbidden_roots.add(root)
            if any(node.module.startswith(prefix) for prefix in FORBIDDEN_MODULE_PREFIXES):
                forbidden_modules.add(node.module)

    return forbidden_roots, forbidden_modules


def _enum_member_names(source: str, class_name: str) -> set[str]:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            members: set[str] = set()
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            members.add(target.id)
            return members
    raise AssertionError(f"{class_name} not found")


def test_avito_parser_adapter_module_has_only_allowed_imports_and_static_text() -> None:
    repo_root = Path(__file__).resolve().parents[2]

    for relative_path in MODULE_FILES:
        source = (repo_root / relative_path).read_text()
        forbidden_roots, forbidden_modules = _import_issues(source)
        assert forbidden_roots == set(), f"{relative_path}: {sorted(forbidden_roots)}"
        assert forbidden_modules == set(), f"{relative_path}: {sorted(forbidden_modules)}"

        lowered_source = source.lower()
        for fragment in FORBIDDEN_TEXT_FRAGMENTS:
            assert fragment not in lowered_source, f"{relative_path}: {fragment}"
        for fragment in FORBIDDEN_CAPTCHA_RUNTIME_FRAGMENTS:
            assert fragment not in lowered_source, f"{relative_path}: {fragment}"

        if relative_path == Path("src/mayak/modules/avito_parser_adapter/contracts.py"):
            parser_outcome_members = _enum_member_names(source, "ParserOutcomeStatus")
            assert "CAPTCHA_OR_CHALLENGE" in parser_outcome_members
            provider_response_members = _enum_member_names(source, "ProviderResponseEvidenceClass")
            assert "BODY_PRESENT_UNCLASSIFIED" in provider_response_members
            assert "EMPTY_WITHOUT_PROOF" in provider_response_members
            completeness_members = _enum_member_names(source, "ResponseCompletenessStatus")
            assert "EMPTY_BLOCKED" in completeness_members
            restriction_members = _enum_member_names(source, "ResponseRestrictionSignal")
            assert "CAPTCHA" in restriction_members

from __future__ import annotations

import ast
import unicodedata
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


def _build_parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    return parents


def _is_session_enum_assignment(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    if not isinstance(node, ast.Name):
        return False
    if node.id != "SESSION" or not isinstance(node.ctx, ast.Store):
        return False

    parent = parents.get(node)
    if not isinstance(parent, ast.Assign) or len(parent.targets) != 1:
        return False

    class_node = parents.get(parent)
    return isinstance(class_node, ast.ClassDef) and class_node.name == "SensitiveMaterialKind"


def _is_sensitive_material_kind_session_attribute(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "SESSION"
        and isinstance(node.value, ast.Name)
        and node.value.id == "SensitiveMaterialKind"
    )


def _assert_no_session_runtime_identifiers(source: str, module_path: Path) -> None:
    tree = ast.parse(source)
    parents = _build_parent_map(tree)

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            if "session" in node.id.casefold():
                assert _is_session_enum_assignment(node, parents), (
                    f"{module_path}: runtime identifier contains session: {node.id}"
                )
        elif isinstance(node, ast.arg):
            if "session" in node.arg.casefold():
                raise AssertionError(f"{module_path}: runtime arg contains session: {node.arg}")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if "session" in node.name.casefold():
                raise AssertionError(
                    f"{module_path}: runtime definition contains session: {node.name}"
                )
        elif isinstance(node, ast.Attribute):
            if "session" in node.attr.casefold():
                assert _is_sensitive_material_kind_session_attribute(node), (
                    f"{module_path}: runtime attribute contains session: {node.attr}"
                )


def _assert_sensitive_material_kind_is_canonical_and_static(source: str, module_path: Path) -> None:
    expected_pairs = [
        ("RAW_HTML", "RAW_HTML"),
        ("RAW_JSON", "RAW_JSON"),
        ("FULL_PROVIDER_PAYLOAD", "FULL_PROVIDER_PAYLOAD"),
        ("COOKIE", "COOKIE"),
        ("SESSION", "SESSION"),
        ("TOKEN", "TOKEN"),
        ("PRIVATE_KEY", "PRIVATE_KEY"),
        ("PRIVATE_CREDENTIAL", "PRIVATE_CREDENTIAL"),
        ("FOREIGN_ACCOUNT_DATA", "FOREIGN_ACCOUNT_DATA"),
        ("UNAPPROVED_PERSONAL_DATA", "UNAPPROVED_PERSONAL_DATA"),
        ("HIDDEN_PROVIDER_FIELDS", "HIDDEN_PROVIDER_FIELDS"),
    ]

    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name != "SensitiveMaterialKind":
            continue

        observed_pairs: list[tuple[str, str]] = []
        for item in node.body:
            if isinstance(item, ast.Expr) and isinstance(item.value, ast.Constant) and isinstance(
                item.value.value, str
            ):
                continue

            assert isinstance(item, ast.Assign), (
                f"{module_path}: non-assign member in SensitiveMaterialKind"
            )
            assert len(item.targets) == 1, (
                f"{module_path}: alias or multi-target assignment in SensitiveMaterialKind"
            )

            target = item.targets[0]
            assert isinstance(target, ast.Name), (
                f"{module_path}: computed target in SensitiveMaterialKind"
            )
            assert target.id.isascii(), f"{module_path}: non-ASCII enum identifier {target.id!r}"
            assert unicodedata.normalize("NFKC", target.id) == target.id, (
                f"{module_path}: unstable enum identifier {target.id!r}"
            )

            value = item.value
            assert isinstance(value, ast.Constant) and isinstance(value.value, str), (
                f"{module_path}: computed enum value for {target.id!r}"
            )
            assert value.value == target.id, f"{module_path}: alias enum value for {target.id!r}"

            observed_pairs.append((target.id, value.value))

        assert observed_pairs == expected_pairs, f"{module_path}: {observed_pairs}"
        return

    raise AssertionError(f"{module_path}: SensitiveMaterialKind not found")


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

        _assert_no_session_runtime_identifiers(source, relative_path)

        if relative_path == Path("src/mayak/modules/avito_parser_adapter/contracts.py"):
            assert 'SESSION = "SESSION"' in source
            assert "ＳＥＳＳＩＯＮ" not in source
            assert "\\x53\\x45\\x53\\x53\\x49\\x4f\\x4e" not in source
            assert "\\x73\\x65\\x73\\x73\\x69\\x6f\\x6e" not in source
            assert "ACCESS_KIND_" not in source
            assert "_SM_KIND_" not in source
            assert "_member_map_" not in source
            assert "type.__setattr__" not in source
            _assert_sensitive_material_kind_is_canonical_and_static(source, relative_path)
        elif relative_path == Path("src/mayak/modules/avito_parser_adapter/fixtures.py"):
            for literal in (
                "FX-APA11-COOKIE-SESSION-TOKEN-BLOCKED-001",
                "fx::apa11::decision::session",
                "FX::APA11::SESSION::BLOCKED",
            ):
                assert literal in source
            assert "ＳＥＳＳＩＯＮ" not in source
            assert "\\x53\\x45\\x53\\x53\\x49\\x4f\\x4e" not in source
            assert "\\x73\\x65\\x73\\x73\\x69\\x6f\\x6e" not in source
            assert "ACCESS_KIND_" not in source
            assert "_SM_KIND_" not in source
            assert "_member_map_" not in source
            assert "type.__setattr__" not in source

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

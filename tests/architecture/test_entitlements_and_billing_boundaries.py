from __future__ import annotations

import ast
from pathlib import Path

ALLOWED_IMPORT_ROOTS = {
    "__future__",
    "admin_tariff_management",
    "beacon_integration",
    "decimal",
    "contracts",
    "datetime",
    "enum",
    "fixtures",
    "manual_access",
    "mayak",
    "payment_provider_boundary",
    "pydantic",
    "policies",
    "subscription_lifecycle",
    "typing",
    "usage_consumption",
}

MODULE_FILES = (
    Path("src/mayak/modules/entitlements_and_billing/__init__.py"),
    Path("src/mayak/modules/entitlements_and_billing/contracts.py"),
    Path("src/mayak/modules/entitlements_and_billing/admin_tariff_management.py"),
    Path("src/mayak/modules/entitlements_and_billing/manual_access.py"),
    Path("src/mayak/modules/entitlements_and_billing/beacon_integration.py"),
    Path("src/mayak/modules/entitlements_and_billing/payment_provider_boundary.py"),
    Path("src/mayak/modules/entitlements_and_billing/policies.py"),
    Path("src/mayak/modules/entitlements_and_billing/fixtures.py"),
    Path("src/mayak/modules/entitlements_and_billing/evaluation.py"),
    Path("src/mayak/modules/entitlements_and_billing/usage_consumption.py"),
    Path("src/mayak/modules/entitlements_and_billing/subscription_lifecycle.py"),
    Path("src/mayak/modules/entitlements_and_billing/payment_reconciliation.py"),
)


def _import_roots(source: str) -> set[str]:
    tree = ast.parse(source)
    roots: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            roots.add(node.module.split(".", 1)[0])

    return roots


def test_entitlements_and_billing_contract_files_do_not_import_forbidden_frameworks_or_sdks() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    for relative_path in MODULE_FILES:
        source = (repo_root / relative_path).read_text()
        forbidden_imports = _import_roots(source) - ALLOWED_IMPORT_ROOTS
        assert forbidden_imports == set(), f"{relative_path}: {sorted(forbidden_imports)}"

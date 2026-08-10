"""Machine-enforced RF24 owner/DML boundary guard."""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

OWNER_TABLES = {
    "identity",
    "entitlements",
    "beacon",
    "scan",
    "notification",
    "filter",
    "admin",
    "support",
    "parser",
    "egress",
    "telegram",
    "max",
}
FORBIDDEN_IMPORT_PAIRS = {
    ("mayak.modules.scan_orchestration", "entitlements"),
    ("mayak.modules.scan_orchestration", "beacon"),
}
MUTATORS = {"insert", "update", "delete", "execute", "bulk_insert", "bulk_update", "bulk_delete"}


def _module(path: Path) -> str:
    return ".".join(path.with_suffix("").parts)


def violations(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    candidates = [root / "src/mayak/runtime/rf24_composition.py"]
    candidates += sorted((root / "scripts" / "runtime").glob("*rf24*expired*.py"))
    for path in candidates:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError) as exc:
            findings.append({"path": str(path.relative_to(root)), "reason": f"parse:{exc}"})
            continue
        text = path.read_text(encoding="utf-8")
        module = (
            _module(path.relative_to(root / "src"))
            if path.is_relative_to(root / "src")
            else str(path)
        )
        if "scan_orchestration" in module and (
            "entitlements_and_billing" in text or "beacon_management" in text
        ):
            findings.append({"path": str(path.relative_to(root)), "reason": "scan-owner-import"})
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if "mayak.modules.scan_orchestration" in node.module and node.module.endswith(
                    ("entitlements_and_billing", "beacon_management")
                ):
                    findings.append(
                        {
                            "path": str(path.relative_to(root)),
                            "line": str(node.lineno),
                            "reason": "forbidden-owner-import",
                        }
                    )
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in MUTATORS
            ):
                rendered = ast.unparse(node)
                if any(table in rendered.lower() for table in OWNER_TABLES):
                    findings.append(
                        {
                            "path": str(path.relative_to(root)),
                            "line": str(node.lineno),
                            "reason": "foreign-business-dml",
                        }
                    )
    return findings


def main(argv: list[str] | None = None) -> int:
    root = Path((argv or sys.argv[1:] or [Path.cwd()])[0]).resolve()
    result = {
        "technical_id": "RF24-EXPIRED-ACCESS-SCENARIO-01",
        "finding_count": len(violations(root)),
        "findings": violations(root),
    }
    print(json.dumps(result, sort_keys=True))
    return 1 if result["finding_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

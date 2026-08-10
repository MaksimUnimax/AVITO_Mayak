"""Static RF24 ownership boundary guard.

The guard discovers the complete RF24-relevant production surface and the
expired-access acceptance scripts.  Owner modules may write their own tables;
coordinators and acceptance producers may only call owner APIs and SELECT for
observation.
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

MUTATING_SQL = ("INSERT", "UPDATE", "DELETE")
OWNER_MODULES = {
    "entitlements_and_billing": "entitlements",
    "beacon_management": "beacon",
    "scan_orchestration": "scan",
}


def _paths(root: Path) -> list[Path]:
    paths: list[Path] = []
    for module in OWNER_MODULES:
        paths.extend((root / "src/mayak/modules" / module).rglob("*.py"))
    paths.extend((root / "src/mayak/runtime").glob("rf2[34]_composition.py"))
    paths.extend((root / "src/mayak/runtime").glob("scheduler.py"))
    paths.extend((root / "src/mayak/runtime").glob("worker.py"))
    paths.extend((root / "scripts/runtime").glob("rf24expired*.py"))
    paths.extend((root / "scripts/runtime").glob("*rf24_expired_access*.py"))
    return sorted(set(path for path in paths if path.is_file()))


def _rel(root: Path, path: Path) -> str:
    return str(path.relative_to(root))


def violations(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for path in _paths(root):
        relative = _rel(root, path)
        if path.name == "check_rf24_expired_access_ownership.py":
            continue
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=relative)
        except SyntaxError as exc:
            findings.append({"path": relative, "reason": f"parse:{exc}"})
            continue
        is_scan = "/scan_orchestration/" in relative
        is_acceptance = relative.startswith("scripts/runtime/") or relative.endswith(
            "rf24_composition.py"
        )
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if is_scan and (
                    "entitlements_and_billing" in node.module or "beacon_management" in node.module
                ):
                    findings.append(
                        {
                            "path": relative,
                            "line": str(node.lineno),
                            "reason": "scan-imports-foreign-owner",
                        }
                    )
        if is_acceptance or is_scan:
            for line_no, line in enumerate(source.splitlines(), 1):
                upper = line.upper()
                foreign_table = "BEACON" in upper or "ENTITLEMENT" in upper
                if (
                    any(token in upper for token in MUTATING_SQL)
                    and foreign_table
                    and (
                        is_scan
                        or any(
                            marker in upper
                            for marker in (
                                "TEXT(",
                                "EXECUTE(",
                                "SQL",
                                "INSERT INTO",
                                "UPDATE ",
                                "DELETE FROM",
                            )
                        )
                    )
                ):
                    findings.append(
                        {
                            "path": relative,
                            "line": str(line_no),
                            "reason": "acceptance-business-dml",
                        }
                    )
        if relative.endswith("rf24_composition.py"):
            for line_no, line in enumerate(source.splitlines(), 1):
                if any(
                    token in line.lower()
                    for token in ("metadata.tables", "insert(", "update(", "delete(")
                ):
                    findings.append(
                        {
                            "path": relative,
                            "line": str(line_no),
                            "reason": "coordinator-business-dml",
                        }
                    )
    return findings


def main(argv: list[str] | None = None) -> int:
    root = Path((argv or sys.argv[1:] or [Path.cwd()])[0]).resolve()
    findings = violations(root)
    result = {
        "technical_id": "RF24-EXPIRED-ACCESS-SCENARIO-01",
        "finding_count": len(findings),
        "findings": findings,
    }
    print(json.dumps(result, sort_keys=True))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())

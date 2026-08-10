"""Fail-closed source guard for RF24 acceptance ownership boundaries."""

from __future__ import annotations

import ast
import re
from pathlib import Path

FOREIGN_PREFIXES = (
    "identity_",
    "beacon_",
    "scan_",
    "entitlement_",
    "filter_",
    "admin_",
    "support_",
    "egress_",
    "parser_",
    "telegram_",
    "max_",
    "billing_",
    "payment_",
)
_DML = re.compile(r"\b(INSERT|UPDATE|DELETE)\b", re.IGNORECASE)
_TABLE = re.compile(r"\bmayak\.([a-z][a-z0-9_]*)\b", re.IGNORECASE)


def violations(paths: tuple[str, ...]) -> list[str]:
    findings: list[str] = []
    for name in paths:
        source = Path(name).read_text(encoding="utf-8")
        tree = ast.parse(source, filename=name)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            value = node.value
            if not _DML.search(value):
                continue
            tables = [table.lower() for table in _TABLE.findall(value)]
            if any(table.startswith(prefix) for table in tables for prefix in FOREIGN_PREFIXES):
                findings.append(f"{name}:{node.lineno}: foreign business DML")
            elif any(
                word in value.lower()
                for word in ("notification_events", "notification_outbox", "notification_delivery_")
            ):
                findings.append(f"{name}:{node.lineno}: direct Notification business DML")
    return findings


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    findings = violations(tuple(str(path) for path in args.paths))
    if findings:
        raise SystemExit("\n".join(findings))
    print("RF24_OWNERSHIP_STATIC_GUARD=PASS")


if __name__ == "__main__":
    main()

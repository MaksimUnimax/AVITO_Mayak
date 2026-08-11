"""Fail-closed scanner for the safe RF24 recovery upload directory."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from scripts.runtime.rf24_backup_restore_core import RAW_SUFFIXES, SECRET

MAX_CONTENT_BYTES = 1_048_576
RULES = (
    ("PEM_PRIVATE_KEY", re.compile(r"BEGIN [A-Z ]*PRIVATE KEY", re.I)),
    (
        "URL_USERINFO_PASSWORD",
        re.compile(r"(?:postgres|postgresql)(?:\+[^\s:/]+)?://[^\s:@/]+:[^\s@/]+@", re.I),
    ),
    ("SENSITIVE_VALUE", SECRET),
)


def _finding(path: Path, classification: str, reason: str, value: bytes = b"") -> dict[str, str]:
    item = {"path": path.as_posix(), "classification": classification, "reason": reason}
    if value:
        item["value_sha256"] = hashlib.sha256(value).hexdigest()
    return item


def scan_tree(root: Path) -> dict[str, object]:
    if not root.exists() or root.is_symlink() or not root.is_dir():
        raise ValueError("scan root is missing or unsafe")
    entries = sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix())
    if not entries:
        raise ValueError("scan root is empty")
    findings: list[dict[str, str]] = []
    inventory: list[dict[str, str]] = []
    for path in entries:
        rel = path.relative_to(root)
        if path.is_dir() and not path.is_symlink():
            inventory.append({"path": rel.as_posix(), "classification": "DIRECTORY"})
            continue
        if path.is_symlink():
            inventory.append({"path": rel.as_posix(), "classification": "SYMLINK"})
            findings.append(
                _finding(rel, "SYMLINK", "symlink entries are not allowed in RF26 evidence")
            )
            continue
        inventory.append({"path": rel.as_posix(), "classification": "UNINSPECTED"})
        if not path.is_file():
            inventory[-1]["classification"] = "UNINSPECTABLE"
            findings.append(_finding(rel, "UNINSPECTABLE", "entry is not a regular file"))
            continue
        mode = path.stat().st_mode
        if not mode & 0o444:
            inventory[-1]["classification"] = "UNINSPECTABLE"
            findings.append(_finding(rel, "UNINSPECTABLE", "entry is not readable"))
            continue
        try:
            size = path.stat().st_size
            if size > MAX_CONTENT_BYTES:
                inventory[-1]["classification"] = "OVERSIZED"
                findings.append(_finding(rel, "OVERSIZED", "entry exceeds bounded inspection size"))
                continue
            data = path.read_bytes()
        except (OSError, UnicodeError):
            inventory[-1]["classification"] = "UNINSPECTABLE"
            findings.append(_finding(rel, "UNINSPECTABLE", "entry could not be inspected"))
            continue
        if b"\x00" in data:
            inventory[-1]["classification"] = "BINARY"
            findings.append(
                _finding(rel, "BINARY", "binary entry is not permitted in RF26 evidence")
            )
            continue
        try:
            text = data.decode("utf-8", "strict")
        except UnicodeDecodeError:
            inventory[-1]["classification"] = "UNDECODABLE"
            findings.append(_finding(rel, "UNDECODABLE", "entry is not valid UTF-8"))
            continue
        inventory[-1]["classification"] = "TEXT"
        if path.suffix.lower() in RAW_SUFFIXES or path.name.endswith(".sql.gz"):
            findings.append(_finding(rel, "RAW_BACKUP", "raw backup material is not permitted"))
        for rule, pattern in RULES:
            match = pattern.search(text)
            if match:
                findings.append(_finding(rel, "SECRET", rule, match.group(0).encode("utf-8")))
        if re.search(r"raw_provider_payload", text) and '"raw_provider_payload": false' not in text:
            findings.append(_finding(rel, "PROVIDER_PAYLOAD", "raw provider payload marker"))
        if (
            re.search(r"production[_ -]?personal|real[_ -]?person|@avito\.ru", text, re.I)
            and '"production_personal_data": false' not in text
        ):
            findings.append(_finding(rel, "PERSONAL_DATA", "production personal data marker"))
    findings.sort(
        key=lambda item: (
            item["path"],
            item["classification"],
            item["reason"],
            item.get("value_sha256", ""),
        )
    )
    classified = [item for item in inventory if item["classification"] != "UNINSPECTED"]
    if len(classified) != len(inventory):
        raise ValueError("inventory closure failed")
    return {
        "schema_version": 2,
        "scanner": "rf26-receipt-tree-rf25-parity",
        "inventory": inventory,
        "enumerated_entry_count": len(inventory),
        "classified_entry_count": len(classified),
        "finding_count": len(findings),
        "findings": findings,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--result", type=Path, required=True)
    p.add_argument("--root", type=Path, help="Recursively scan one evidence tree")
    p.add_argument("paths", type=Path, nargs="*")
    a = p.parse_args()
    if a.root is not None:
        if a.paths:
            p.error("--root cannot be combined with positional paths")
        try:
            result = scan_tree(a.root)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
    else:
        if not a.paths:
            p.error("one or more paths are required")
        from scripts.runtime.rf24_backup_restore_core import scan_paths

        result = scan_paths(a.paths)
    a.result.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(1 if result["finding_count"] else 0)


if __name__ == "__main__":
    main()

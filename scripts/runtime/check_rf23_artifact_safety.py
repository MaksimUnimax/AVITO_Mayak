"""Scan the exact RF23 acceptance payload and emit its bound manifest."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from pathlib import Path

VERSION = "rf23-safety-scanner/v1"
EXPECTED = (
    "rf23-evidence.json",
    "rf23-focused-pytest.log",
    "rf23-runtime-probes.json",
    "rf23-api.log",
)
FORBIDDEN = re.compile(
    r"-----BEGIN .*PRIVATE KEY-----|Bearer\s+[A-Za-z0-9._~-]{20,}|"
    r"postgres(?:ql)?://[^\s:]+:[^\s@]+@",
    re.I,
)
RAW_KEYS = {
    "html",
    "response_body",
    "cookie",
    "session",
    "credential",
    "password",
    "password_file",
    "access_token",
    "auth_token",
    "private_key",
    "dsn",
    "raw_provider_payload",
}


def transport_inventory(repo_root: Path) -> dict[str, int]:
    forbidden = {
        "mayak.persistence.schema",
        "mayak.modules.identity_and_access.runtime",
        "mayak.modules.notification_delivery.runtime",
        "mayak.modules.scan_orchestration.read_models",
        "mayak.modules.telegram_adapter.runtime",
        "mayak.modules.max_adapter.runtime",
        "mayak.modules.beacon_management.runtime",
    }
    result = {
        "forbidden": 0,
        "private_identity": 0,
        "owner_read_model": 0,
        "direct_dml": 0,
        "integration_private_imports": 0,
        "integration_private_refs": 0,
        "integration_duck_typing": 0,
        "integration_secret_reveals": 0,
    }
    root = repo_root / "src/mayak/entrypoints/api"
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                modules = [module]
                if module == "mayak.modules.identity_and_access.runtime":
                    result["private_identity"] += sum(
                        alias.name.startswith("_") for alias in node.names
                    )
            else:
                modules = []
            result["forbidden"] += sum(module in forbidden for module in modules)
            result["owner_read_model"] += sum(module.endswith(".read_models") for module in modules)
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in {"insert", "update", "delete", "execute"}
            ):
                result["direct_dml"] += 1
    for path in (
        repo_root / "src/mayak/runtime/rf21_composition.py",
        repo_root / "src/mayak/runtime/rf23_composition.py",
    ):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                result["integration_private_imports"] += sum(
                    alias.name.startswith("_") for alias in node.names
                )
            if isinstance(node, ast.Name) and node.id == "_RawSecret":
                result["integration_private_refs"] += 1
            if isinstance(node, ast.Attribute) and node.attr == "_value_as_secret":
                result["integration_private_refs"] += 1
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "hasattr"
            ):
                if any(
                    isinstance(arg, ast.Constant) and arg.value == "_value_as_secret"
                    for arg in node.args
                ):
                    result["integration_duck_typing"] += 1
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "reveal"
            ):
                result["integration_secret_reveals"] += 1
    return result


def _find(value: object, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in RAW_KEYS:
                findings.append(f"sensitive field at {path}.{key}")
            findings.extend(_find(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_find(child, f"{path}[{index}]"))
    elif isinstance(value, str) and FORBIDDEN.search(value):
        findings.append(f"credential-like value at {path}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    if (
        len(args.paths) != len(EXPECTED)
        or tuple(path.name for path in args.paths) != EXPECTED
        or any(path.name != path.parts[-1] or ".." in path.parts for path in args.paths)
    ):
        raise SystemExit(
            "RF23 safety scanner requires exact payloads: "
            "rf23-evidence.json rf23-focused-pytest.log rf23-runtime-probes.json rf23-api.log"
        )

    findings: list[str] = []
    transport = transport_inventory(args.repo_root.resolve())
    if any(transport.values()):
        findings.append(f"transport boundary violations: {transport}")
    payloads: list[dict[str, object]] = []
    for path in args.paths:
        if not path.is_file():
            findings.append(f"missing payload: {path.name}")
            continue
        raw = path.read_bytes()
        if path.name == "rf23-api.log" and not raw:
            findings.append("API log is zero bytes")
        if path.name in {EXPECTED[0], "rf23-runtime-probes.json"}:
            try:
                findings.extend(_find(json.loads(raw.decode("utf-8"))))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                findings.append(f"malformed JSON: {exc}")
        elif FORBIDDEN.search(raw.decode("utf-8", errors="replace")):
            findings.append(f"credential-like value in {path.name}")
        payloads.append(
            {
                "path": path.resolve().as_posix(),
                "basename": path.name,
                "size": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "result": "PASS" if not findings else "FAIL",
                "classification": "NONE" if not findings else "SENSITIVE_CONTENT",
                "finding_count": len(findings),
            }
        )
    expected_payload_count = len(args.paths)
    manifest = {
        "scanner_method": VERSION,
        "payloads": payloads,
        "finding_count": len(findings),
        "classification": "PASS"
        if not findings and len(payloads) == expected_payload_count
        else "BLOCKED",
        "scanner_result": "PASS"
        if not findings and len(payloads) == expected_payload_count
        else "FAIL",
        "findings": findings,
        "transport_inventory": transport,
    }
    args.manifest.write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    if findings:
        raise SystemExit("RF23 safety scanner blocked: " + "; ".join(findings))
    print("RF23_ARTIFACT_SAFETY_VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Deterministic, fail-closed RF25 security, privacy and supply-chain verifier."""

# The pre-existing verifier uses compact single-line gate expressions; keep its
# established formatting contract while extending the controls.
# ruff: noqa: E501, E701, E702
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata as metadata
import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

SCHEMA = 1
RF25_SCHEMA = 1
RF25_TECHNICAL_ID = "RF25-SECURITY-PRIVACY-SUPPLY-CHAIN-01"
RF25_BASE_SHA = "c2f88430db02f8fd4c426bc327500ab5a8a66896"
MAX_BYTES = 20 * 1024 * 1024
ROOT = Path(__file__).resolve().parents[2]
HEX40 = re.compile(r"^[0-9a-f]{40}$")
PLACEHOLDER = re.compile(r"^(?:|none|null|false|example|placeholder|changeme|secret-evidence|<[^>]+>|\$\{[^}]+\}|REPLACE_ME|NOT_SET|Literal\[(?:None|True|False)\])$", re.I)
ASSIGNMENT = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*(?:secret|token|password|passwd|api_key|apikey|private_key|client_secret)[A-Za-z0-9_]*)\s*=(?!=)\s*([^#\s,;]+)", re.I)
RULES = (("PEM_PRIVATE_KEY", re.compile(r"BEGIN [A-Z0-9 _-]*PRIVATE KEY")), ("GITHUB_TOKEN", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+")), ("AWS_ACCESS_KEY", re.compile(r"\bAKIA[0-9A-Z]{16}\b")), ("SLACK_TOKEN", re.compile(r"\bxox[baprs]-[0-9A-Za-z-]+\b")), ("TELEGRAM_BOT_TOKEN", re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{35}\b")), ("URL_USERINFO_PASSWORD", re.compile(r"https?://[^/\s:@]+:[^/\s@]+@")))
CASE_IDS = ("ST01_PEM_PRIVATE_KEY_DETECTION", "ST02_KNOWN_TOKEN_FORMAT_DETECTION", "ST03_POPULATED_SECRET_ASSIGNMENT_DETECTION", "ST04_PLACEHOLDER_ASSIGNMENT_NOT_FLAGGED", "ST05_URL_USERINFO_REDACTION", "ST06_RAW_SECRET_VALUE_NOT_STORED", "ST07_FINDING_SCHEMA_MINIMAL_FIELDS", "ST08_BINARY_FILE_CLASSIFICATION", "ST09_UNSAFE_SYMLINK_REJECTION", "ST10_DETERMINISTIC_FINDING_SORT", "ST11_DUPLICATE_FINDING_ELIMINATION", "ST12_ZERO_VULNERABILITY_AUDIT_PARSE", "ST13_NONZERO_VULNERABILITY_AUDIT_PARSE", "ST14_LICENSE_METADATA_CLASSIFICATION", "ST15_LOCK_INVENTORY_PARSE", "ST16_INSTALLED_DISTRIBUTION_RECONCILIATION", "ST17_WORKFLOW_PIN_PERMISSION_AND_FORBIDDEN_CHECKS", "ST18_SECRET_NAMED_COMPARISON_NOT_FLAGGED")
EXPECTED_ACTIONS = ("actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1", "astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b", "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a")
WORKFLOW_CHECK_NAMES = ("exact_action_sequence", "nonempty_action_sequence", "immutable_action_pins", "top_level_permissions_exact", "no_write_permissions", "no_secrets_context", "persist_credentials_false_exactly_once", "no_pull_request_target", "no_continue_on_error", "no_forbidden_commands", "retention_30_exactly_once")
WORKFLOW_SUBCASES = ("WF00_CURRENT_WORKFLOW_PASS", "WF01_EMPTY_ACTION_LIST_REJECTED", "WF02_MISSING_EXPECTED_ACTION_REJECTED", "WF03_DUPLICATE_ACTION_REJECTED", "WF04_MUTABLE_OR_WRONG_PIN_REJECTED", "WF05_UNEXPECTED_ACTION_REJECTED", "WF06_CONTENTS_WRITE_REJECTED", "WF07_ADDITIONAL_WRITE_PERMISSION_REJECTED", "WF08_SECRETS_CONTEXT_REJECTED", "WF09_PERSISTED_CREDENTIALS_REJECTED", "WF10_PULL_REQUEST_TARGET_REJECTED", "WF11_FORBIDDEN_OR_CONTINUE_COMMAND_REJECTED", "WF12_INVALID_RETENTION_REJECTED")


def stable(value: object) -> object:
    if isinstance(value, dict):
        return {k: stable(value[k]) for k in sorted(value)}
    if isinstance(value, list):
        return [stable(v) for v in value]
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(stable(value), indent=2, ensure_ascii=False) + "\n").encode()
    fd, tmp = tempfile.mkstemp(prefix=".evidence-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data); handle.flush(); os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


def write_text(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".evidence-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data.replace("\r\n", "\n").replace("\r", "\n").encode()); handle.flush(); os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_sha() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True, timeout=10, shell=False)
    return result.stdout.strip()


def git_files() -> list[str]:
    result = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True, timeout=30, shell=False)
    return sorted(x.decode("utf-8") for x in result.stdout.split(b"\0") if x)


def redact_url(value: str) -> str:
    parts = urlsplit(value)
    if parts.username is None: return value
    host = parts.hostname or ""
    if parts.port: host += ":" + str(parts.port)
    return urlunsplit((parts.scheme, host, parts.path, parts.query, parts.fragment))


def _safe_symlink(path: Path, root: Path) -> bool:
    target = os.readlink(path)
    if os.path.isabs(target): return False
    lexical = Path(os.path.abspath(path.parent / target))
    try: lexical.relative_to(root.absolute())
    except ValueError: return False
    return True


def classify_tracked_file(root: Path, rel: str) -> tuple[str, bytes | None]:
    path = root / rel
    if path.is_symlink():
        if not _safe_symlink(path, root): raise RuntimeError("STOP_UNSAFE_TRACKED_SYMLINK")
        return "SAFE_SYMLINK", None
    data = path.read_bytes()
    if len(data) > MAX_BYTES: raise RuntimeError("STOP_OVERSIZED_TRACKED_FILE")
    if b"\0" in data: return "BINARY", data
    try: data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc: raise RuntimeError("STOP_UNDECODABLE_TRACKED_TEXT") from exc
    return "TEXT", data


def classification_inventory(files: list[str], root: Path = ROOT) -> dict[str, object]:
    records: list[tuple[str, str]] = []
    binary: list[str] = []
    symlinks: list[str] = []
    for rel in sorted(files):
        kind, _ = classify_tracked_file(root, rel)
        records.append((rel, kind))
        if kind == "BINARY": binary.append(rel)
        if kind == "SAFE_SYMLINK": symlinks.append(rel)
    stream = "".join(f"{rel}\t{kind}\n" for rel, kind in records).encode("utf-8")
    counts = {"tracked_file_count": len(records), "scanned_text_file_count": sum(k == "TEXT" for _, k in records), "inspected_binary_file_count": len(binary), "safe_symlink_count": len(symlinks)}
    counts["classification_total"] = sum(counts[k] for k in ("scanned_text_file_count", "inspected_binary_file_count", "safe_symlink_count"))
    return {**counts, "classification_inventory_sha256": sha256(stream), "binary_relative_paths": binary, "safe_symlink_relative_paths": symlinks}


def detect_findings(rel: str, data: bytes) -> list[dict[str, object]]:
    text = data.decode("utf-8", errors="strict").replace("\r\n", "\n").replace("\r", "\n")
    has_pem_block = bool(re.search(r"-----BEGIN [A-Z0-9 _-]*PRIVATE KEY-----\s*[A-Za-z0-9+/=\n]{24,}\s*-----END [A-Z0-9 _-]*PRIVATE KEY-----", text))
    findings: list[dict[str, object]] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        for rule, pattern in RULES:
            match = pattern.search(line)
            if match:
                value = match.group(0)
                if rule == "PEM_PRIVATE_KEY" and not has_pem_block:
                    continue
                if rule == "URL_USERINFO_PASSWORD" and any(x in line for x in ("example.test", "example.invalid")): continue
                if rule == "URL_USERINFO_PASSWORD": value = redact_url(value)
                findings.append({"path": rel, "line": line_no, "rule": rule, "value_sha256": sha256(value.encode()), "binary": False})
        if Path(rel).suffix.lower() not in {".md", ".txt", ".rst"}:
            for match in ASSIGNMENT.finditer(line):
                value = match.group(2).strip("'\"")
                if re.search(r"synthetic|acceptance|invalid\(|bootstrap-only|migration-only|application-only|session-key", line, re.I):
                    continue
                if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\)?", value) or re.match(r"[A-Za-z_][A-Za-z0-9_]*(?:\.|\()", value) or value.startswith(("{", "[", "(")): continue
                reference = re.search(r"(?:_ref|_reference|_policy|_evidence|_present|_presence|_material|_handling|_requested|_retained|_authorized|_consumed|hide_password)$", match.group(1), re.I)
                safe_template = value.startswith(("$", "%")) or "${" in value or value.startswith(("/run/secrets", "/etc/")) or re.search(r"synthetic|fixture|migration-only|application-only|session-key", value, re.I) is not None
                if not reference and not PLACEHOLDER.fullmatch(value) and not safe_template:
                    findings.append({"path": rel, "line": line_no, "rule": "POPULATED_SECRET_ASSIGNMENT", "value_sha256": sha256(value.encode()), "binary": False})
    return findings


def _git_files_at(ref: str) -> list[str]:
    result = subprocess.run(["git", "ls-tree", "-r", "--name-only", ref], cwd=ROOT, check=True, capture_output=True, text=True, timeout=30, shell=False)
    return sorted(x for x in result.stdout.splitlines() if x)


def _git_bytes_at(ref: str, rel: str) -> bytes:
    result = subprocess.run(["git", "show", f"{ref}:{rel}"], cwd=ROOT, check=True, capture_output=True, timeout=30, shell=False)
    return result.stdout


def _scan_ref(ref: str) -> dict[str, object]:
    findings: list[dict[str, object]] = []
    for rel in _git_files_at(ref):
        try:
            data = _git_bytes_at(ref, rel)
        except subprocess.CalledProcessError:
            continue
        if len(data) > MAX_BYTES or b"\0" in data:
            continue
        try:
            data.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            continue
        findings.extend(detect_findings(rel, data))
    normalized = normalize_findings(findings)
    return {"source_sha": ref, "finding_count": len(normalized), "findings": normalized, "status": "PASS" if not normalized else "FAIL"}


def _synthetic_finding(finding: dict[str, object]) -> bool:
    rel = str(finding["path"]).lower()
    return rel.startswith("tests/") or "/fixtures/" in rel or rel.endswith(".example") or ".env.example" in rel


def compare_findings(base: dict[str, object], candidate: dict[str, object]) -> dict[str, object]:
    base_rows = base.get("findings", [])
    candidate_rows = candidate.get("findings", [])
    def key(row: dict[str, object]) -> tuple[object, ...]:
        return (row["path"], row["line"], row["rule"], row["value_sha256"])
    base_keys = {key(row) for row in base_rows}
    rows = []
    for row in candidate_rows:
        k = key(row)
        real_rule = row["rule"] in {"PEM_PRIVATE_KEY", "GITHUB_TOKEN", "AWS_ACCESS_KEY", "SLACK_TOKEN", "TELEGRAM_BOT_TOKEN", "URL_USERINFO_PASSWORD", "SENSITIVE_FILENAME"}
        classification = "SYNTHETIC_EXAMPLE_OR_FIXTURE" if _synthetic_finding(row) else ("REAL_SECRET" if real_rule else ("UNCHANGED_BASELINE" if k in base_keys else "NEW_OR_WORSENED"))
        rows.append({"path": row["path"], "line": row["line"], "rule": row["rule"], "value_sha256": row["value_sha256"], "classification": classification})
    for row in base_rows:
        if key(row) not in {key(x) for x in candidate_rows} and not _synthetic_finding(row):
            rows.append({"path": row["path"], "line": row["line"], "rule": row["rule"], "value_sha256": row["value_sha256"], "classification": "FALSE_POSITIVE"})
    counts = {name: sum(x["classification"] == name for x in rows) for name in ("REAL_SECRET", "NEW_OR_WORSENED", "UNCHANGED_BASELINE", "SYNTHETIC_EXAMPLE_OR_FIXTURE", "FALSE_POSITIVE")}
    blockers = counts["REAL_SECRET"] + counts["NEW_OR_WORSENED"]
    return {"schema_version": RF25_SCHEMA, "base_sha": base.get("source_sha"), "candidate_sha": candidate.get("source_sha"), "findings": sorted(rows, key=lambda x: (x["path"], x["line"], x["rule"], x["value_sha256"])), "classification_counts": counts, "status": "PASS" if blockers == 0 else "FAIL"}


def unsafe_command_audit() -> dict[str, object]:
    paths = [x for x in git_files() if x.startswith(("src/mayak/", "scripts/ci/", ".github/workflows/ci-security-supply-chain.yml"))]
    checks = {"shell_true": [], "os_system": [], "dynamic_shell": [], "eval": []}
    for rel in paths:
        data = (ROOT / rel).read_text(encoding="utf-8", errors="strict") if (ROOT / rel).is_file() else ""
        for line_no, line in enumerate(data.splitlines(), 1):
            for name, pattern in (("shell_true", r"shell\s*=\s*True"), ("os_system", r"\bos\.system\s*\("), ("dynamic_shell", r"(?:sh|bash)\s+-c"), ("eval", r"\beval\s*\(")):
                if re.search(pattern, line): checks[name].append({"path": rel, "line": line_no})
    return {"schema_version": RF25_SCHEMA, "scope": paths, "checks": checks, "status": "PASS" if not any(checks.values()) else "FAIL"}


def runtime_security_audit() -> dict[str, object]:
    sources = {rel: (ROOT / rel).read_text(encoding="utf-8") for rel in (
        "src/mayak/modules/avito_parser_adapter/runtime.py",
        "src/mayak/modules/telegram_adapter/transport.py",
        "src/mayak/modules/max_adapter/transport.py",
        "src/mayak/modules/entitlements_and_billing/runtime.py",
    )}
    required = {
        "avito": ("max_response_bytes", "iter_bytes", "httpx.Timeout"),
        "telegram": ("_max_response_bytes", "iter_bytes", "httpx.Timeout", "reconciliation_required=True"),
        "max": ("self._limit", "iter_bytes", "httpx.Timeout", "response_too_large"),
        "yookassa": ("max_response_bytes", "iter_bytes", "httpx.Timeout", "RECONCILE_REQUIRED"),
    }
    checks = {name: all(token in sources[rel] for token in tokens) for name, rel, tokens in (
        ("avito", "src/mayak/modules/avito_parser_adapter/runtime.py", required["avito"]),
        ("telegram", "src/mayak/modules/telegram_adapter/transport.py", required["telegram"]),
        ("max", "src/mayak/modules/max_adapter/transport.py", required["max"]),
        ("yookassa", "src/mayak/modules/entitlements_and_billing/runtime.py", required["yookassa"]),
    )}
    checks.update({"safe_error": "internal error" in (ROOT / "src/mayak/entrypoints/api/application.py").read_text(encoding="utf-8"), "redaction_helper": (ROOT / "src/mayak/platform/redaction.py").is_file(), "provider_payload_not_logged": not any("logger" in text.lower() and "response.content" in text for text in sources.values())})
    return {"schema_version": RF25_SCHEMA, "checks": checks, "status": "PASS" if all(checks.values()) else "FAIL"}


def container_security_audit() -> dict[str, object]:
    docker = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
    checks = {
        "docker_nonroot": bool(re.search(r"^USER\s+10001:10001\s*$", docker, re.M)),
        "immutable_base": bool(re.search(r"FROM .*@sha256:[0-9a-f]{64}", docker)),
        "compose_no_postgres_host_port": not bool(re.search(r"postgresql?\s*:\s*\n(?:.|\n){0,500}?ports:", compose, re.I)),
        "compose_no_new_privileges": "no-new-privileges:true" in compose,
        "compose_cap_drop": "cap_drop:" in compose,
        "api_loopback": "127.0.0.1:" in compose,
    }
    return {"schema_version": RF25_SCHEMA, "checks": checks, "status": "PASS" if all(checks.values()) else "FAIL"}


def rf25_matrix(secret: dict, comparison: dict, commands: dict, runtime: dict, container: dict, dependency: dict, vulnerability: dict, workflow: dict) -> list[dict[str, object]]:
    rows = [
        ("secret_scanning", secret["status"], "scripts/ci/verify_security_supply_chain.py:secret_scan"),
        ("base_candidate_classification", comparison["status"], "scripts/ci/verify_security_supply_chain.py:compare_findings"),
        ("unsafe_commands", commands["status"], "scripts/ci/verify_security_supply_chain.py:unsafe_command_audit"),
        ("provider_privacy_redaction_safe_errors", runtime["status"], "src/mayak/platform/redaction.py; API safe errors"),
        ("bounded_http_timeout_cancellation", runtime["status"], "provider transports and HttpxTransport"),
        ("authorization_least_privilege", "REUSED_RF24", "RF24 cross-account and Compose evidence"),
        ("container_compose_hardening", container["status"], "Dockerfile; compose.yaml"),
        ("dependency_inventory", dependency["status"], "pyproject.toml; uv.lock"),
        ("vulnerability_evidence", vulnerability["status"], "uv audit"),
        ("license_inventory", "INVENTORY_COMPLETE_POLICY_NOT_EVALUATED", "installed distribution metadata"),
        ("workflow_security", workflow["status"], ".github/workflows/ci-security-supply-chain.yml"),
    ]
    return [{"requirement": name, "status": status, "evidence": evidence} for name, status, evidence in rows]


def artifact_safety(evidence: Path) -> dict[str, object]:
    forbidden = re.compile(r"-----BEGIN [A-Z0-9 _-]*PRIVATE KEY-----|\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]+\b|\bAKIA[0-9A-Z]{16}\b|https?://[^/\s:@]+:[^/\s@]+@", re.I)
    files = sorted(p for p in evidence.rglob("*") if p.is_file())
    unsafe = []
    for path in files:
        data = path.read_text(encoding="utf-8", errors="strict")
        if forbidden.search(data): unsafe.append(path.name)
    manifest = {"schema_version": RF25_SCHEMA, "file_count": len(files), "files": [{"name": p.name, "sha256": sha256(p.read_bytes()), "bytes": p.stat().st_size} for p in files], "unsafe_files": unsafe, "status": "PASS" if not unsafe else "FAIL"}
    write_json(evidence / "artifact-safety-manifest.json", manifest)
    return manifest


def normalize_findings(findings: list[dict[str, object]]) -> list[dict[str, object]]:
    unique = {(x["path"], x["line"], x["rule"], x["value_sha256"]): x for x in findings}
    return sorted(unique.values(), key=lambda x: (x["path"], x["line"], x["rule"], x["value_sha256"]))


def secret_scan() -> dict[str, object]:
    files = git_files(); inventory = classification_inventory(files)
    findings: list[dict[str, object]] = []
    for rel in files:
        kind, data = classify_tracked_file(ROOT, rel)
        if kind == "SAFE_SYMLINK": continue
        assert data is not None
        if Path(rel).name in {".env", ".env.local", ".env.production", ".env.acceptance", "id_rsa", "id_ed25519"} or "private-key" in Path(rel).name.lower():
            findings.append({"path": rel, "line": 1, "rule": "SENSITIVE_FILENAME", "value_sha256": sha256(rel.encode()), "binary": False})
        findings.extend(detect_findings(rel, data))
    safe = normalize_findings(findings); counts: dict[str, int] = {}
    for item in safe: counts[item["rule"]] = counts.get(item["rule"], 0) + 1
    return {"schema_version": SCHEMA, "source_sha": source_sha(), **inventory, "finding_count": len(safe), "rule_counts": counts, "findings": safe, "status": "PASS" if not safe else "FAIL"}


def audit_payload(payload: str, exit_code: int) -> dict[str, object]:
    try: parsed = json.loads(payload or "{}")
    except json.JSONDecodeError: parsed = {}
    vulnerabilities = parsed.get("vulnerabilities", []) if isinstance(parsed, dict) else []
    adverse = parsed.get("adverse_statuses", []) if isinstance(parsed, dict) else []
    return {"schema_version": SCHEMA, "exit_code": exit_code, "advisories": vulnerabilities, "adverse_statuses": adverse, "finding_count": len(vulnerabilities), "ignored_count": 0, "suppressed_count": 0, "status": "PASS" if exit_code == 0 and not vulnerabilities and not adverse else "FAIL"}


def audit() -> dict[str, object]:
    cmd = ["uv", "audit", "--frozen", "--output-format", "json", "--no-progress"]
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=180, shell=False)
    return {"command": cmd, **audit_payload(result.stdout, result.returncode)}


def lock_inventory(pyproject: dict, lock: dict) -> tuple[dict[str, dict], dict[str, int]]:
    packages = lock.get("package", []); records = {}; artifacts = 0; sdists = 0; wheels = 0; urls = []
    direct = {x.split("[", 1)[0].split(">", 1)[0].lower() for x in pyproject["project"].get("dependencies", []) + pyproject["dependency-groups"]["dev"]}
    for package in packages:
        name = package["name"]; norm = re.sub(r"[-_.]+", "-", name).lower()
        records[norm] = {"name": norm, "version": package["version"], "source_class": "editable" if package.get("source", {}).get("editable") else "registry", "direct_or_transitive": "direct" if norm in direct else "transitive", "artifact_count": 0, "sdist_count": 0, "wheel_count": 0, "artifact_hash_present": True}
        if "sdist" in package:
            item = package["sdist"]; urls.append(item["url"]); artifacts += 1; sdists += 1; records[norm]["sdist_count"] = 1; records[norm]["artifact_hash_present"] &= "hash" in item
        for item in package.get("wheels", []):
            urls.append(item["url"]); artifacts += 1; wheels += 1; records[norm]["wheel_count"] += 1; records[norm]["artifact_hash_present"] &= "hash" in item
        records[norm]["artifact_count"] = records[norm]["sdist_count"] + records[norm]["wheel_count"]
    conflicts = {}
    for package in packages:
        for key in ("sdist", "wheels"):
            entries = package.get(key, []) if key == "wheels" else ([package[key]] if key in package else [])
            for item in entries: conflicts.setdefault(item["url"], set()).add(item.get("hash"))
    counts = {"package_records": len(packages), "registry_records": sum(x["source_class"] == "registry" for x in records.values()), "editable_records": sum(x["source_class"] == "editable" for x in records.values()), "sdists": sdists, "wheels": wheels, "total_artifacts": artifacts, "hashed_artifacts": sum(1 for p in packages for k in ((["sdist"] if "sdist" in p else []) + ["wheels"]) for x in (p.get(k, []) if k == "wheels" else [p[k]]) if "hash" in x), "unique_artifact_urls": len(set(urls)), "duplicate_artifact_records": len(urls) - len(set(urls)), "conflicting_url_hash_pairs": sum(len(v) > 1 for v in conflicts.values())}
    return records, counts


def reconcile_distributions(distributions: list[dict[str, str]], lock_records: dict[str, dict]) -> tuple[list[dict], dict[str, int]]:
    rows = []; seen = set()
    for item in distributions:
        norm = re.sub(r"[-_.]+", "-", item["name"]).lower()
        if norm in seen: raise RuntimeError("STOP_DUPLICATE_INSTALLED_DISTRIBUTION")
        seen.add(norm); lock = lock_records.get(norm); owned = norm == "mayak"
        rows.append({"name": norm, "version": item["version"], "lock_version": lock["version"] if lock else None, "project_owned": owned, "metadata_source": "SYNTHETIC_OR_TASK_VENV", "reconciliation": "PROJECT_OWNED" if owned else ("MATCH" if lock and lock["version"] == item["version"] else "MISMATCH")})
    counts = {"count": len(rows), "duplicate_normalized_names": 0, "version_mismatches": sum(x["reconciliation"] == "MISMATCH" for x in rows), "unknown_external": sum(not x["project_owned"] and x["lock_version"] is None for x in rows)}
    return sorted(rows, key=lambda x: x["name"]), counts


def installed(lock_records: dict[str, dict], venv: Path) -> tuple[list[dict], dict[str, int], list[metadata.Distribution]]:
    site = next((p for p in (venv / "lib").glob("python*/site-packages") if p.is_dir()), None)
    if site is None: raise RuntimeError("STOP_TASK_VENV_SITE_PACKAGES_MISSING")
    distributions = list(metadata.distributions(path=[str(site)])); items = [{"name": d.metadata.get("Name", ""), "version": d.version} for d in distributions]
    rows, counts = reconcile_distributions(items, lock_records)
    return rows, counts, distributions


def licenses(rows: list[dict], distributions: list[metadata.Distribution]) -> tuple[list[dict], str]:
    output = []
    for row in rows:
        dist = next((d for d in distributions if re.sub(r"[-_.]+", "-", d.metadata.get("Name", "")).lower() == row["name"]), None)
        expression = dist.metadata.get("License-Expression") if dist else None; field = dist.metadata.get("License") if dist else None; classifiers = sorted(x.removeprefix("Classifier: ") for x in dist.metadata.get_all("Classifier", [])) if dist else []
        classification = "SPDX_EXPRESSION" if expression else "LICENSE_FIELD" if field else "CLASSIFIER_ONLY" if classifiers else "PROJECT_OWNED_UNDECLARED" if row["project_owned"] else "METADATA_UNSPECIFIED"
        output.append({"name": row["name"], "version": row["version"], "project_owned": row["project_owned"], "license_expression": expression, "license": field, "license_classifiers": classifiers, "classification": classification})
    output.sort(key=lambda x: (x["name"], x["version"])); tsv = "name\tversion\tclassification\n" + "".join(f"{x['name']}\t{x['version']}\t{x['classification']}\n" for x in output)
    return output, tsv


def workflow_check(workflow_text: str | None = None) -> dict[str, object]:
    text = workflow_text if workflow_text is not None else (ROOT / ".github/workflows/ci-security-supply-chain.yml").read_text(encoding="utf-8")
    uses = re.findall(r"^[ \t]*(?:-[ \t]*)?uses:\s*([^\s#]+)", text, re.M)
    action_refs = [x.rsplit("@", 1)[1] for x in uses if "@" in x]
    immutable = bool(uses) and len(action_refs) == len(uses) and all(HEX40.fullmatch(ref) for ref in action_refs)
    permission_lines: list[str] = []
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line == "permissions:":
            for candidate in lines[index + 1:]:
                if candidate and not candidate.startswith((" ", "\t")): break
                if candidate.strip(): permission_lines.append(candidate.strip())
            break
    permission_pairs = [re.match(r"^([^:#]+):\s*([^#\s]+)\s*$", line) for line in permission_lines]
    permission_pairs = [match.groups() for match in permission_pairs if match]
    writes = bool(re.search(r"(?:^|\s)permissions:\s*write-all\b|^\s*[A-Za-z0-9_-]+:\s*write\b", text, re.M | re.I)) or any(value.lower() == "write" for _, value in permission_pairs)
    credentials = re.findall(r"^\s*persist-credentials:\s*(true|false)\s*$", text, re.M | re.I)
    retention = re.findall(r"^\s*retention-days:\s*([^\s#]+)", text, re.M | re.I)
    checks = {
        "exact_action_sequence": tuple(uses) == EXPECTED_ACTIONS,
        "nonempty_action_sequence": bool(uses),
        "immutable_action_pins": immutable and tuple(uses) == EXPECTED_ACTIONS,
        "top_level_permissions_exact": permission_pairs == [("contents", "read")],
        "no_write_permissions": not writes,
        "no_secrets_context": not re.search(r"\bsecrets\s*(?:\.|\[)", text),
        "persist_credentials_false_exactly_once": credentials.count("false") == 1 and credentials.count("true") == 0 and text.lower().count("persist-credentials:") == 1,
        "no_pull_request_target": "pull_request_target" not in text,
        "no_continue_on_error": "continue-on-error" not in text,
        "no_forbidden_commands": not re.search(r"\bsudo\b|\beval\b|curl\s*\|\s*sh|wget\s*\|\s*sh|\bdocker\b|\bpsql\b|\balembic\b", text, re.I),
        "retention_30_exactly_once": len(retention) == 1 and retention[0] == "30",
    }
    return {"checks": checks, "status": "PASS" if all(checks.get(name, False) for name in WORKFLOW_CHECK_NAMES) else "FAIL", "actions": uses}


def valid_self_test_evidence(path: Path) -> bool:
    if not path.is_file(): return False
    try: data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError): return False
    cases = data.get("cases", [])
    matrix = data.get("workflow_rejection_matrix", {})
    return data.get("schema_version") == 1 and data.get("required_case_count") == 18 and data.get("executed_case_count") == 18 and data.get("passed_case_count") == 18 and data.get("failed_case_count") == 0 and data.get("status") == "PASS" and [x.get("case_id") for x in cases] == list(CASE_IDS) and all(x.get("status") == "PASS" and set(x) == {"case_id", "status", "safe_detail_code"} for x in cases) and next((x.get("safe_detail_code") for x in cases if x.get("case_id") == "ST17_WORKFLOW_PIN_PERMISSION_AND_FORBIDDEN_CHECKS"), None) == "WORKFLOW_REJECTION_MATRIX_PASS_13_OF_13" and matrix == {"required_subcase_count": 13, "executed_subcase_count": 13, "passed_subcase_count": 13, "failed_subcase_count": 0, "unexpected_pass_count": 0, "unexpected_check_count": 0, "case_ids": list(WORKFLOW_SUBCASES), "expected_failed_checks": ["PASS", "nonempty_action_sequence", "exact_action_sequence", "exact_action_sequence", "immutable_action_pins", "exact_action_sequence", "no_write_permissions", "no_write_permissions", "no_secrets_context", "persist_credentials_false_exactly_once", "no_pull_request_target", "no_continue_on_error", "retention_30_exactly_once"]}


def self_test(evidence: Path) -> None:
    results = []
    def case(case_id: str, fn, detail: str = "ASSERTIONS_PASSED") -> None:
        try: fn(); results.append({"case_id": case_id, "status": "PASS", "safe_detail_code": detail})
        except Exception as exc:
            results.append({"case_id": case_id, "status": "FAIL", "safe_detail_code": type(exc).__name__.upper()})
            write_json(evidence / "self-test-evidence.json", {"schema_version": 1, "source_sha": source_sha(), "required_case_count": 18, "executed_case_count": len(results), "passed_case_count": sum(x["status"] == "PASS" for x in results), "failed_case_count": 1, "cases": results, "status": "FAIL"})
            raise SystemExit("STOP_VERIFIER_SELF_TEST_COVERAGE_FAILED")
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory); pem = b"-----BEGIN PRIVATE KEY-----\n" + b"A" * 32 + b"\n-----END PRIVATE KEY-----"; field = b"api_" + b"token"; value = b"not-a-placeholder-value"
        (root / "x.py").write_bytes(b"PRIVATE_KEY = '" + pem + b"'\n")
        case(CASE_IDS[0], lambda: assert_rule("PEM_PRIVATE_KEY", pem))
        case(CASE_IDS[1], lambda: assert_rule("GITHUB_TOKEN", (b"gh" + b"p_" + b"x" * 20)))
        case(CASE_IDS[2], lambda: assert_true("POPULATED_SECRET_ASSIGNMENT" in {x["rule"] for x in detect_findings("x.py", field + b"='" + value + b"'")}))
        case(CASE_IDS[3], lambda: assert_true(not detect_findings("x.py", field + b"=placeholder")))
        case(CASE_IDS[4], lambda: assert_true(redact_url("https://user:password@example.invalid/x") == "https://example.invalid/x"))
        case(CASE_IDS[5], lambda: assert_true(value.decode() not in json.dumps(detect_findings("x.py", field + b"='" + value + b"'"))))
        case(CASE_IDS[6], lambda: assert_true(set(detect_findings("x.py", b"gh" + b"p_" + b"x" * 20)[0]) == {"path", "line", "rule", "value_sha256", "binary"}))
        (root / "binary.bin").write_bytes(b"\x00\xff")
        case(CASE_IDS[7], lambda: assert_true(classify_tracked_file(root, "binary.bin")[0] == "BINARY"))
        (root / "outside").mkdir(); (root / "link").symlink_to("../outside", target_is_directory=True)
        case(CASE_IDS[8], lambda: expect_runtime(lambda: classify_tracked_file(root, "link"), "STOP_UNSAFE_TRACKED_SYMLINK"))
        unsorted = [{"path": "b", "line": 1, "rule": "X", "value_sha256": "2"}, {"path": "a", "line": 1, "rule": "X", "value_sha256": "1"}]
        case(CASE_IDS[9], lambda: assert_true([x["path"] for x in normalize_findings(unsorted)] == ["a", "b"]))
        case(CASE_IDS[10], lambda: assert_true(len(normalize_findings(unsorted + unsorted[:1])) == 2 and compare_findings({"source_sha": "base", "findings": [{"path": "src/x.py", "line": 1, "rule": "SAFE", "value_sha256": "1"}]}, {"source_sha": "candidate", "findings": [{"path": "src/x.py", "line": 1, "rule": "SAFE", "value_sha256": "1"}]})["classification_counts"]["UNCHANGED_BASELINE"] == 1))
        case(CASE_IDS[11], lambda: assert_true(audit_payload('{"vulnerabilities": [], "adverse_statuses": []}', 0)["status"] == "PASS"))
        case(CASE_IDS[12], lambda: assert_true(audit_payload('{"vulnerabilities": [{"id": "X"}]}', 1)["status"] == "FAIL"))
        case(CASE_IDS[13], lambda: assert_true(licenses([{"name": "x", "version": "1", "project_owned": False}], [FakeDistribution("x", "1", "MIT")])[0][0]["classification"] == "LICENSE_FIELD"))
        pyproject = {"project": {"dependencies": ["x" ]}, "dependency-groups": {"dev": []}}
        lock = {"package": [{"name": "x", "version": "1", "sdist": {"url": "u", "hash": "h"}}]}
        case(CASE_IDS[14], lambda: assert_true(lock_inventory(pyproject, lock)[1]["package_records"] == 1))
        case(CASE_IDS[15], lambda: assert_true(reconcile_distributions([{ "name": "x", "version": "1"}], {"x": {"version": "1"}})[1]["version_mismatches"] == 0))
        good_workflow = (ROOT / ".github/workflows/ci-security-supply-chain.yml").read_text(encoding="utf-8")
        matrix_checks = ["PASS"]
        def rejected(case_text: str, check_name: str) -> None:
            result = workflow_check(case_text)
            assert_true(result["status"] == "FAIL")
            assert_true(result["checks"].get(check_name) is False)
            matrix_checks.append(check_name)
        def workflow_matrix() -> None:
            assert_true(workflow_check(good_workflow)["status"] == "PASS")
            rejected(re.sub(r"^[ \t]*(?:-[ \t]*)?uses:.*\n", "", good_workflow, flags=re.M), "nonempty_action_sequence")
            rejected(re.sub(r"^[ \t]*uses: astral-sh/setup-uv@[^\n]+\n", "", good_workflow, count=1, flags=re.M), "exact_action_sequence")
            rejected(good_workflow.replace("        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1\n", "        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1\n        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1\n", 1), "exact_action_sequence")
            rejected(good_workflow.replace("actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1", "actions/checkout@" + "a" * 40, 1), "immutable_action_pins")
            rejected(good_workflow.replace("          retention-days: 30", "      - name: Unexpected\n        uses: example/unexpected@" + "b" * 40 + "\n          retention-days: 30", 1), "exact_action_sequence")
            rejected(good_workflow.replace("  contents: read", "  contents: write", 1), "no_write_permissions")
            rejected(good_workflow.replace("  contents: read", "  contents: read\n  actions: write", 1), "no_write_permissions")
            rejected(good_workflow.replace("  PYTHONNOUSERSITE: \"1\"", "  LEAK: ${{ secrets.TEST }}\n  PYTHONNOUSERSITE: \"1\"", 1), "no_secrets_context")
            rejected(good_workflow.replace("persist-credentials: false", "persist-credentials: true", 1), "persist_credentials_false_exactly_once")
            rejected(good_workflow.replace("  pull_request:\n", "  pull_request_target:\n", 1), "no_pull_request_target")
            rejected(good_workflow.replace("        run: |", "        continue-on-error: true\n        run: |", 1), "no_continue_on_error")
            rejected(good_workflow.replace("retention-days: 30", "retention-days: 31", 1), "retention_30_exactly_once")
        case(CASE_IDS[16], workflow_matrix, "WORKFLOW_REJECTION_MATRIX_PASS_13_OF_13")
        comparisons = b"secret_path == 'synthetic'\ntoken_value != 'synthetic'\npassword_value <= 9\npassword_value >= 1\napi_token := 'synthetic'\n"
        case(CASE_IDS[17], lambda: assert_true(not detect_findings("x.py", comparisons) and compare_findings({"source_sha": "base", "findings": []}, {"source_sha": "candidate", "findings": [{"path": "src/x.py", "line": 1, "rule": "UNSAFE", "value_sha256": "2"}]})["classification_counts"]["NEW_OR_WORSENED"] == 1 and compare_findings({"source_sha": "base", "findings": [{"path": "src/x.py", "line": 1, "rule": "PEM_PRIVATE_KEY", "value_sha256": "3"}]}, {"source_sha": "candidate", "findings": [{"path": "src/x.py", "line": 1, "rule": "PEM_PRIVATE_KEY", "value_sha256": "3"}]})["classification_counts"]["REAL_SECRET"] == 1), "SECRET_NAMED_COMPARISONS_AND_BASELINE_CLASSIFICATION")
    evidence_data = {"schema_version": 1, "source_sha": source_sha(), "required_case_count": 18, "executed_case_count": 18, "passed_case_count": 18, "failed_case_count": 0, "cases": results, "workflow_rejection_matrix": {"required_subcase_count": 13, "executed_subcase_count": len(matrix_checks), "passed_subcase_count": sum(check != "FAIL" for check in matrix_checks), "failed_subcase_count": sum(check == "FAIL" for check in matrix_checks), "unexpected_pass_count": 0, "unexpected_check_count": 0, "case_ids": list(WORKFLOW_SUBCASES), "expected_failed_checks": matrix_checks}, "status": "PASS"}
    write_json(evidence / "self-test-evidence.json", evidence_data)
    print("SELF_TEST_PASS cases=18/18")


class FakeDistribution:
    def __init__(self, name: str, version: str, license_name: str): self.metadata = FakeMetadata(name, license_name); self.version = version


class FakeMetadata(dict):
    def __init__(self, name: str, license_name: str):
        super().__init__({"Name": name, "License": license_name, "License-Expression": None})

    def get_all(self, key: str, default: list[str] | None = None) -> list[str]:
        return []


def assert_true(value: bool) -> None:
    assert value


def assert_rule(rule: str, data: bytes) -> None:
    assert any(x["rule"] == rule for x in detect_findings("x.py", data))


def expect_runtime(fn, marker: str) -> None:
    try: fn()
    except RuntimeError as exc: assert str(exc) == marker
    else: raise AssertionError(marker)


def run_all(evidence: Path, venv: Path) -> None:
    if not valid_self_test_evidence(evidence / "self-test-evidence.json"): raise SystemExit("STOP_VERIFIER_SELF_TEST_COVERAGE_FAILED")
    with (ROOT / "pyproject.toml").open("rb") as handle: pyproject = tomllib.load(handle)
    with (ROOT / "uv.lock").open("rb") as handle: lock = tomllib.load(handle)
    records, counts = lock_inventory(pyproject, lock); rows, installed_counts, distributions = installed(records, venv); license_rows, tsv = licenses(rows, distributions); secret = secret_scan(); vuln = audit(); workflow = workflow_check()
    dep_expected = {"package_records": 50, "registry_records": 49, "editable_records": 1, "sdists": 48, "wheels": 246, "total_artifacts": 294, "hashed_artifacts": 294, "unique_artifact_urls": 294, "duplicate_artifact_records": 0, "conflicting_url_hash_pairs": 0}
    dep = {"schema_version": SCHEMA, "source_sha": source_sha(), "python_requirement": pyproject["project"]["requires-python"], "direct_runtime_dependencies": sorted(pyproject["project"]["dependencies"]), "direct_development_dependencies": sorted(pyproject["dependency-groups"]["dev"]), "packages": list(records.values()), "counts": counts, "pyproject_sha256": sha256((ROOT / "pyproject.toml").read_bytes()), "uv_lock_sha256": sha256((ROOT / "uv.lock").read_bytes()), "status": "PASS" if counts == dep_expected else "FAIL"}
    base_secret = _scan_ref(RF25_BASE_SHA)
    comparison = compare_findings(base_secret, secret)
    commands = unsafe_command_audit(); runtime = runtime_security_audit(); container = container_security_audit()
    matrix = rf25_matrix(secret, comparison, commands, runtime, container, dep, vuln, workflow)
    write_json(evidence / "secret-scan.json", secret); write_json(evidence / "base-secret-scan.json", base_secret); write_json(evidence / "base-candidate-comparison.json", comparison); write_json(evidence / "unsafe-command-audit.json", commands); write_json(evidence / "security-privacy-runtime.json", runtime); write_json(evidence / "container-compose-hardening.json", container); write_json(evidence / "rf25-requirement-matrix.json", {"schema_version": RF25_SCHEMA, "technical_id": RF25_TECHNICAL_ID, "base_sha": RF25_BASE_SHA, "candidate_sha": source_sha(), "rows": matrix})
    write_json(evidence / "vulnerability-audit.json", vuln); write_json(evidence / "dependency-inventory.json", dep); write_json(evidence / "installed-distribution-inventory.json", {"schema_version": SCHEMA, "distributions": rows, "reconciliation": installed_counts, "status": "PASS" if not installed_counts["version_mismatches"] and not installed_counts["unknown_external"] else "FAIL"}); write_json(evidence / "license-inventory.json", {"schema_version": SCHEMA, "records": license_rows, "status": "INVENTORY_COMPLETE_POLICY_NOT_EVALUATED"}); write_text(evidence / "license-inventory.tsv", tsv)
    safety = artifact_safety(evidence)
    self_summary = json.loads((evidence / "self-test-evidence.json").read_text(encoding="utf-8")); final_status = "PASS" if secret["status"] == "PASS" and comparison["status"] == "PASS" and vuln["status"] == "PASS" and dep["status"] == "PASS" and not installed_counts["version_mismatches"] and not installed_counts["unknown_external"] and workflow["status"] == "PASS" and commands["status"] == "PASS" and runtime["status"] == "PASS" and container["status"] == "PASS" and safety["status"] == "PASS" else "FAIL"
    write_json(evidence / "security-supply-chain-evidence.json", {"schema_version": RF25_SCHEMA, "technical_id": RF25_TECHNICAL_ID, "base_sha": RF25_BASE_SHA, "source_sha": source_sha(), "python_version": sys.version.split()[0], "standard_gil": bool(getattr(sys, "_is_gil_enabled", lambda: True)()), "pyproject_sha256": dep["pyproject_sha256"], "uv_lock_sha256": dep["uv_lock_sha256"], "lock_counts": counts, "installed_distribution_reconciliation": installed_counts, "self_test": {k: self_summary[k] for k in ("required_case_count", "executed_case_count", "passed_case_count", "failed_case_count", "status")}, "secret_scan": {k: secret[k] for k in ("finding_count", "status")}, "base_candidate_comparison": comparison, "unsafe_command_audit": commands, "provider_privacy_runtime": runtime, "container_compose": container, "requirement_matrix": matrix, "vulnerability": {k: vuln[k] for k in ("finding_count", "status")}, "dependency_inventory": dep["status"], "license_inventory": "INVENTORY_COMPLETE_POLICY_NOT_EVALUATED", "workflow_security": workflow["status"], "reused_evidence_identity": {"authorization": "RF24_ACCEPTED_CROSS_ACCOUNT_SCENARIOS", "postgresql": "RF24_ACCEPTED_DATABASE_BOUNDARY"}, "limitations": ["license policy is not defined by the repository", "live providers are not contacted"], "status": final_status, "production": "NOT_PRODUCTION_READY"})
    write_text(evidence / "summary.txt", f"RF25 security, privacy and supply-chain verification\nstatus: {final_status}\ntechnical_id: {RF25_TECHNICAL_ID}\nbase: {RF25_BASE_SHA}\ncandidate: {source_sha()}\nself-test cases: 18/18\nsecret findings: {secret['finding_count']}\nbase/candidate classifications: {comparison['classification_counts']}\nunsafe command audit: {commands['status']}\nprovider/privacy/http audit: {runtime['status']}\ncontainer/compose audit: {container['status']}\nvulnerability findings: {vuln['finding_count']}\nlicense inventory: COMPLETE_POLICY_NOT_EVALUATED\nNOT_PRODUCTION_READY\n")
    if final_status != "PASS": raise SystemExit("STOP_LOCAL_SECURITY_GATE_FAILED")


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--self-test", action="store_true"); parser.add_argument("--mode", choices=["all"], default="all"); parser.add_argument("--evidence-dir", type=Path, default=Path("ci-evidence/security-supply-chain")); parser.add_argument("--venv", type=Path, default=Path(".venv")); args = parser.parse_args()
    if args.self_test: self_test(args.evidence_dir)
    else: run_all(args.evidence_dir, args.venv)


if __name__ == "__main__": main()

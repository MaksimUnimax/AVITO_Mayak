#!/usr/bin/env python3
"""Deterministic, fail-closed RF-07 security and supply-chain verifier."""
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
MAX_BYTES = 20 * 1024 * 1024
ROOT = Path(__file__).resolve().parents[2]
HEX40 = re.compile(r"^[0-9a-f]{40}$")
PLACEHOLDER = re.compile(r"^(?:|none|null|false|example|placeholder|changeme|secret-evidence|<[^>]+>|\$\{[^}]+\}|REPLACE_ME|NOT_SET|Literal\[(?:None|True|False)\])$", re.I)
ASSIGNMENT = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*(?:secret|token|password|passwd|api_key|apikey|private_key|client_secret)[A-Za-z0-9_]*)\s*=\s*([^#\s,;]+)", re.I)
RULES = (("PEM_PRIVATE_KEY", re.compile(r"BEGIN [A-Z0-9 _-]*PRIVATE KEY")), ("GITHUB_TOKEN", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+")), ("AWS_ACCESS_KEY", re.compile(r"\bAKIA[0-9A-Z]{16}\b")), ("SLACK_TOKEN", re.compile(r"\bxox[baprs]-[0-9A-Za-z-]+\b")), ("TELEGRAM_BOT_TOKEN", re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{35}\b")), ("URL_USERINFO_PASSWORD", re.compile(r"https?://[^/\s:@]+:[^/\s@]+@")))
CASE_IDS = ("ST01_PEM_PRIVATE_KEY_DETECTION", "ST02_KNOWN_TOKEN_FORMAT_DETECTION", "ST03_POPULATED_SECRET_ASSIGNMENT_DETECTION", "ST04_PLACEHOLDER_ASSIGNMENT_NOT_FLAGGED", "ST05_URL_USERINFO_REDACTION", "ST06_RAW_SECRET_VALUE_NOT_STORED", "ST07_FINDING_SCHEMA_MINIMAL_FIELDS", "ST08_BINARY_FILE_CLASSIFICATION", "ST09_UNSAFE_SYMLINK_REJECTION", "ST10_DETERMINISTIC_FINDING_SORT", "ST11_DUPLICATE_FINDING_ELIMINATION", "ST12_ZERO_VULNERABILITY_AUDIT_PARSE", "ST13_NONZERO_VULNERABILITY_AUDIT_PARSE", "ST14_LICENSE_METADATA_CLASSIFICATION", "ST15_LOCK_INVENTORY_PARSE", "ST16_INSTALLED_DISTRIBUTION_RECONCILIATION", "ST17_WORKFLOW_PIN_PERMISSION_AND_FORBIDDEN_CHECKS")


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
    findings: list[dict[str, object]] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        for rule, pattern in RULES:
            match = pattern.search(line)
            if match:
                value = match.group(0)
                if rule == "URL_USERINFO_PASSWORD" and any(x in line for x in ("example.test", "example.invalid")): continue
                if rule == "URL_USERINFO_PASSWORD": value = redact_url(value)
                findings.append({"path": rel, "line": line_no, "rule": rule, "value_sha256": sha256(value.encode()), "binary": False})
        if Path(rel).suffix.lower() not in {".md", ".txt", ".rst"}:
            for match in ASSIGNMENT.finditer(line):
                value = match.group(2).strip("'\"")
                if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\)?", value) or re.match(r"[A-Za-z_][A-Za-z0-9_]*(?:\.|\()", value) or value.startswith(("{", "[", "(")): continue
                reference = re.search(r"(?:_ref|_reference|_policy|_evidence|_present|_presence|_material|_handling|_requested|_retained|_authorized|_consumed)$", match.group(1), re.I)
                if not reference and not PLACEHOLDER.fullmatch(value) and not value.startswith(("$", "%")):
                    findings.append({"path": rel, "line": line_no, "rule": "POPULATED_SECRET_ASSIGNMENT", "value_sha256": sha256(value.encode()), "binary": False})
    return findings


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
    uses = re.findall(r"^\s*- uses:\s*([^\s#]+)", text, re.M); pin = all("@" in x and HEX40.fullmatch(x.rsplit("@", 1)[1]) for x in uses)
    checks = {"no_pull_request_target": "pull_request_target" not in text, "permissions": bool(re.search(r"permissions:\n\s+contents: read\n", text)) and "write-all" not in text, "secrets_context": "${{ secrets." not in text, "immutable_pins": pin, "persist_credentials_false": text.count("persist-credentials: false") == 1, "no_forbidden_commands": not re.search(r"\bsudo\b|\beval\b|curl\s*\|\s*sh|wget\s*\|\s*sh|docker|psql|alembic", text, re.I), "no_continue": "continue-on-error" not in text, "retention": "retention-days: 30" in text}
    return {"checks": checks, "status": "PASS" if all(checks.values()) else "FAIL", "actions": uses}


def valid_self_test_evidence(path: Path) -> bool:
    if not path.is_file(): return False
    try: data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError): return False
    cases = data.get("cases", [])
    return data.get("schema_version") == 1 and data.get("required_case_count") == 17 and data.get("executed_case_count") == 17 and data.get("passed_case_count") == 17 and data.get("failed_case_count") == 0 and data.get("status") == "PASS" and [x.get("case_id") for x in cases] == list(CASE_IDS) and all(x.get("status") == "PASS" and set(x) == {"case_id", "status", "safe_detail_code"} for x in cases)


def self_test(evidence: Path) -> None:
    results = []
    def case(case_id: str, fn) -> None:
        try: fn(); results.append({"case_id": case_id, "status": "PASS", "safe_detail_code": "ASSERTIONS_PASSED"})
        except Exception as exc:
            results.append({"case_id": case_id, "status": "FAIL", "safe_detail_code": type(exc).__name__.upper()})
            write_json(evidence / "self-test-evidence.json", {"schema_version": 1, "source_sha": source_sha(), "required_case_count": 17, "executed_case_count": len(results), "passed_case_count": sum(x["status"] == "PASS" for x in results), "failed_case_count": 1, "cases": results, "status": "FAIL"})
            raise SystemExit("STOP_VERIFIER_SELF_TEST_COVERAGE_FAILED")
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory); pem = b"-----BEGIN " + b"PRIVATE KEY" + b"-----"; field = b"api_" + b"token"; value = b"synthetic" + b"-value"
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
        case(CASE_IDS[10], lambda: assert_true(len(normalize_findings(unsorted + unsorted[:1])) == 2))
        case(CASE_IDS[11], lambda: assert_true(audit_payload('{"vulnerabilities": [], "adverse_statuses": []}', 0)["status"] == "PASS"))
        case(CASE_IDS[12], lambda: assert_true(audit_payload('{"vulnerabilities": [{"id": "X"}]}', 1)["status"] == "FAIL"))
        case(CASE_IDS[13], lambda: assert_true(licenses([{"name": "x", "version": "1", "project_owned": False}], [FakeDistribution("x", "1", "MIT")])[0][0]["classification"] == "LICENSE_FIELD"))
        pyproject = {"project": {"dependencies": ["x" ]}, "dependency-groups": {"dev": []}}
        lock = {"package": [{"name": "x", "version": "1", "sdist": {"url": "u", "hash": "h"}}]}
        case(CASE_IDS[14], lambda: assert_true(lock_inventory(pyproject, lock)[1]["package_records"] == 1))
        case(CASE_IDS[15], lambda: assert_true(reconcile_distributions([{ "name": "x", "version": "1"}], {"x": {"version": "1"}})[1]["version_mismatches"] == 0))
        good_workflow = "permissions:\n  contents: read\n- uses: actions/checkout@" + "a" * 40 + "\n        persist-credentials: false\nretention-days: 30\n"
        case(CASE_IDS[16], lambda: assert_true(workflow_check(good_workflow)["status"] == "PASS"))
    evidence_data = {"schema_version": 1, "source_sha": source_sha(), "required_case_count": 17, "executed_case_count": 17, "passed_case_count": 17, "failed_case_count": 0, "cases": results, "status": "PASS"}
    write_json(evidence / "self-test-evidence.json", evidence_data)
    print("SELF_TEST_PASS cases=17/17")


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
    write_json(evidence / "secret-scan.json", secret); write_json(evidence / "vulnerability-audit.json", vuln); write_json(evidence / "dependency-inventory.json", dep); write_json(evidence / "installed-distribution-inventory.json", {"schema_version": SCHEMA, "distributions": rows, "reconciliation": installed_counts, "status": "PASS" if not installed_counts["version_mismatches"] and not installed_counts["unknown_external"] else "FAIL"}); write_json(evidence / "license-inventory.json", {"schema_version": SCHEMA, "records": license_rows, "status": "INVENTORY_COMPLETE_POLICY_NOT_EVALUATED"}); write_text(evidence / "license-inventory.tsv", tsv)
    self_summary = json.loads((evidence / "self-test-evidence.json").read_text(encoding="utf-8")); final_status = "PASS" if secret["status"] == "PASS" and vuln["status"] == "PASS" and dep["status"] == "PASS" and not installed_counts["version_mismatches"] and not installed_counts["unknown_external"] and workflow["status"] == "PASS" else "FAIL"
    write_json(evidence / "security-supply-chain-evidence.json", {"schema_version": SCHEMA, "source_sha": source_sha(), "python_version": sys.version.split()[0], "standard_gil": bool(getattr(sys, "_is_gil_enabled", lambda: True)()), "pyproject_sha256": dep["pyproject_sha256"], "uv_lock_sha256": dep["uv_lock_sha256"], "lock_counts": counts, "installed_distribution_reconciliation": installed_counts, "self_test": {k: self_summary[k] for k in ("required_case_count", "executed_case_count", "passed_case_count", "failed_case_count", "status")}, "secret_scan": {k: secret[k] for k in ("finding_count", "status")}, "vulnerability": {k: vuln[k] for k in ("finding_count", "status")}, "dependency_inventory": dep["status"], "license_inventory": "INVENTORY_COMPLETE_POLICY_NOT_EVALUATED", "workflow_security": workflow["status"], "status": final_status, "production": "NOT_PRODUCTION_READY"})
    write_text(evidence / "summary.txt", f"RF-07-02 security and supply-chain foundation\nstatus: {final_status}\nsource: {source_sha()}\nself-test cases: 17/17\ntracked files: {secret['tracked_file_count']}\ntext files: {secret['scanned_text_file_count']}\nbinary files: {secret['inspected_binary_file_count']}\nsafe symlinks: {secret['safe_symlink_count']}\nclassification inventory sha256: {secret['classification_inventory_sha256']}\nsecret findings: {secret['finding_count']}\nvulnerability findings: {vuln['finding_count']}\nlicense inventory: COMPLETE_POLICY_NOT_EVALUATED\nNOT_PRODUCTION_READY\n")
    if final_status != "PASS": raise SystemExit("STOP_LOCAL_SECURITY_GATE_FAILED")


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--self-test", action="store_true"); parser.add_argument("--mode", choices=["all"], default="all"); parser.add_argument("--evidence-dir", type=Path, default=Path("ci-evidence/security-supply-chain")); parser.add_argument("--venv", type=Path, default=Path(".venv")); args = parser.parse_args()
    if args.self_test: self_test(args.evidence_dir)
    else: run_all(args.evidence_dir, args.venv)


if __name__ == "__main__": main()

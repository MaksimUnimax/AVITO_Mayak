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
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def write_text(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".evidence-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data.replace("\r\n", "\n").replace("\r", "\n").encode())
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_files() -> list[str]:
    result = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True, timeout=30)
    return sorted(x.decode() for x in result.stdout.split(b"\0") if x)


def redact_url(value: str) -> str:
    parts = urlsplit(value)
    if parts.username is None:
        return value
    host = parts.hostname or ""
    if parts.port:
        host += ":" + str(parts.port)
    return urlunsplit((parts.scheme, host, parts.path, parts.query, parts.fragment))


def secret_scan() -> dict[str, object]:
    findings: list[dict[str, object]] = []
    inspected_binary = 0
    scanned = 0
    symlinks = 0
    files = git_files()
    for rel in files:
        path = ROOT / rel
        if path.is_symlink():
            symlinks += 1
            target = path.resolve()
            if path.is_absolute() or ROOT not in target.parents:
                raise RuntimeError("STOP_UNSAFE_TRACKED_SYMLINK")
            continue
        data = path.read_bytes()
        if len(data) > MAX_BYTES:
            raise RuntimeError("UNSCANNED_TRACKED_TEXT_FILE:" + rel)
        if b"\0" in data:
            inspected_binary += 1
            continue
        scanned += 1
        text = data.decode("utf-8", errors="strict").replace("\r\n", "\n").replace("\r", "\n")
        if Path(rel).name in {".env", ".env.local", ".env.production", ".env.acceptance", "id_rsa", "id_ed25519"} or "private-key" in Path(rel).name.lower():
            findings.append((rel, 1, "SENSITIVE_FILENAME", rel))
        for line_no, line in enumerate(text.splitlines(), 1):
            for rule, pattern in RULES:
                match = pattern.search(line)
                if match:
                    value = match.group(0)
                    if rule == "URL_USERINFO_PASSWORD" and any(x in line for x in ("example.test", "example.invalid")):
                        continue
                    if rule == "URL_USERINFO_PASSWORD":
                        value = redact_url(value)
                    findings.append((rel, line_no, rule, value))
            if Path(rel).suffix.lower() not in {".md", ".txt", ".rst"}:
                for match in ASSIGNMENT.finditer(line):
                    value = match.group(2).strip("'\"")
                    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\)?", value) or re.match(r"[A-Za-z_][A-Za-z0-9_]*(?:\.|\()", value) or value.startswith(("{", "[", "(")):
                        continue
                    semantic_reference = re.search(r"(?:_ref|_reference|_policy|_evidence|_present|_presence|_material|_handling|_requested|_retained|_authorized|_consumed)$", match.group(1), re.I)
                    if not semantic_reference and not PLACEHOLDER.fullmatch(value) and not value.startswith(("$", "%")):
                        findings.append((rel, line_no, "POPULATED_SECRET_ASSIGNMENT", value))
    unique = {}
    for rel, line, rule, value in findings:
        key = (rel, line, rule, sha256(value.encode()))
        unique[key] = {"path": rel, "line": line, "rule": rule, "value_sha256": key[3], "binary": False}
    safe = sorted(unique.values(), key=lambda x: (x["path"], x["line"], x["rule"]))
    counts: dict[str, int] = {}
    for item in safe:
        counts[item["rule"]] = counts.get(item["rule"], 0) + 1
    return {"schema_version": SCHEMA, "source_sha": source_sha(), "tracked_file_count": len(files), "scanned_text_file_count": scanned, "inspected_binary_file_count": inspected_binary, "safe_symlink_count": symlinks, "finding_count": len(safe), "rule_counts": counts, "findings": safe, "status": "PASS" if not safe else "FAIL"}


def source_sha() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True, timeout=10)
    return result.stdout.strip()


def audit() -> dict[str, object]:
    cmd = ["uv", "audit", "--frozen", "--output-format", "json", "--no-progress"]
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=180, shell=False)
    try:
        parsed = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        parsed = {}
    vulnerabilities = parsed.get("vulnerabilities", []) if isinstance(parsed, dict) else []
    adverse = parsed.get("adverse_statuses", []) if isinstance(parsed, dict) else []
    return {"schema_version": SCHEMA, "command": cmd, "exit_code": result.returncode, "advisories": vulnerabilities, "adverse_statuses": adverse, "finding_count": len(vulnerabilities), "ignored_count": 0, "suppressed_count": 0, "status": "PASS" if result.returncode == 0 and not vulnerabilities and not adverse else "FAIL"}


def lock_inventory(pyproject: dict, lock: dict) -> tuple[dict[str, dict], dict[str, int]]:
    packages = lock.get("package", [])
    records = {}
    artifacts = 0
    sdists = 0
    wheels = 0
    urls = []
    for package in packages:
        name = package["name"]
        records[name] = {"name": name, "version": package["version"], "source_class": "editable" if package.get("source", {}).get("editable") else "registry", "direct_or_transitive": "direct" if name.lower() in {x.split("[", 1)[0].split(">", 1)[0].lower() for x in pyproject["project"].get("dependencies", []) + pyproject["dependency-groups"]["dev"]} else "transitive", "artifact_count": 0, "sdist_count": 0, "wheel_count": 0, "artifact_hash_present": True}
        if "sdist" in package:
            item = package["sdist"]; urls.append(item["url"]); artifacts += 1; sdists += 1; records[name]["sdist_count"] = 1
            records[name]["artifact_hash_present"] &= "hash" in item
        for item in package.get("wheels", []):
            urls.append(item["url"]); artifacts += 1; wheels += 1; records[name]["wheel_count"] += 1; records[name]["artifact_hash_present"] &= "hash" in item
        records[name]["artifact_count"] = records[name]["sdist_count"] + records[name]["wheel_count"]
    conflicts = {}
    for package in packages:
        for key in ("sdist", "wheels"):
            entries = package.get(key, []) if key == "wheels" else ([package[key]] if key in package else [])
            for item in entries:
                conflicts.setdefault(item["url"], set()).add(item.get("hash"))
    conflicting = sum(len(v) > 1 for v in conflicts.values())
    counts = {"package_records": len(packages), "registry_records": sum(x["source_class"] == "registry" for x in records.values()), "editable_records": sum(x["source_class"] == "editable" for x in records.values()), "sdists": sdists, "wheels": wheels, "total_artifacts": artifacts, "hashed_artifacts": sum(1 for p in packages for k in (["sdist"] if "sdist" in p else []) + ["wheels"] for x in (p.get(k, []) if k == "wheels" else [p[k]]) if "hash" in x), "unique_artifact_urls": len(set(urls)), "duplicate_artifact_records": len(urls) - len(set(urls)), "conflicting_url_hash_pairs": conflicting}
    return records, counts


def installed(lock_records: dict[str, dict], pyproject: dict, venv: Path) -> tuple[list[dict], dict[str, int], list[metadata.Distribution]]:
    rows = []
    names = {}
    site = next((p for p in (venv / "lib").glob("python*/site-packages") if p.is_dir()), None)
    if site is None:
        raise RuntimeError("STOP_TASK_VENV_SITE_PACKAGES_MISSING")
    distributions = list(metadata.distributions(path=[str(site)]))
    for dist in distributions:
        name = dist.metadata.get("Name")
        if not name:
            raise RuntimeError("STOP_MALFORMED_DISTRIBUTION_METADATA")
        norm = re.sub(r"[-_.]+", "-", name).lower()
        if norm in names:
            raise RuntimeError("STOP_DUPLICATE_INSTALLED_DISTRIBUTION")
        names[norm] = dist
        lock = lock_records.get(norm, lock_records.get(name))
        owned = norm == "mayak"
        rows.append({"name": norm, "version": dist.version, "lock_version": lock["version"] if lock else None, "project_owned": owned, "metadata_source": "TASK_VENV_SITE_PACKAGES", "reconciliation": "PROJECT_OWNED" if owned else ("MATCH" if lock and lock["version"] == dist.version else "MISMATCH")})
    counts = {"count": len(rows), "duplicate_normalized_names": 0, "version_mismatches": sum(x["reconciliation"] == "MISMATCH" for x in rows), "unknown_external": sum(not x["project_owned"] and x["lock_version"] is None for x in rows)}
    return sorted(rows, key=lambda x: x["name"]), counts, distributions


def licenses(rows: list[dict], distributions: list[metadata.Distribution]) -> tuple[list[dict], str]:
    output = []
    for row in rows:
        dist = next(d for d in distributions if re.sub(r"[-_.]+", "-", d.metadata.get("Name", "")).lower() == row["name"])
        expression = dist.metadata.get("License-Expression")
        field = dist.metadata.get("License")
        classifiers = sorted(x.removeprefix("Classifier: ") for x in dist.metadata.get_all("Classifier", []))
        classification = "SPDX_EXPRESSION" if expression else "LICENSE_FIELD" if field else "CLASSIFIER_ONLY" if classifiers else "PROJECT_OWNED_UNDECLARED" if row["project_owned"] else "METADATA_UNSPECIFIED"
        output.append({"name": row["name"], "version": row["version"], "project_owned": row["project_owned"], "license_expression": expression, "license": field, "license_classifiers": classifiers, "classification": classification})
    output.sort(key=lambda x: (x["name"], x["version"]))
    tsv = "name\tversion\tclassification\n" + "".join(f"{x['name']}\t{x['version']}\t{x['classification']}\n" for x in output)
    return output, tsv


def workflow_check() -> dict[str, object]:
    text = (ROOT / ".github/workflows/ci-security-supply-chain.yml").read_text(encoding="utf-8")
    uses = re.findall(r"^\s*- uses:\s*([^\s#]+)", text, re.M)
    pin = all("@" in x and HEX40.fullmatch(x.rsplit("@", 1)[1]) for x in uses)
    checks = {"no_pull_request_target": "pull_request_target" not in text, "permissions": bool(re.search(r"permissions:\n\s+contents: read\n", text)) and "write-all" not in text, "secrets_context": "${{ secrets." not in text, "immutable_pins": pin, "persist_credentials_false": text.count("persist-credentials: false") == 1, "no_forbidden_commands": not re.search(r"\bsudo\b|\beval\b|curl\s*\|\s*sh|wget\s*\|\s*sh|docker|psql|alembic", text, re.I), "no_continue": "continue-on-error" not in text, "retention": "retention-days: 30" in text}
    return {"checks": checks, "status": "PASS" if all(checks.values()) else "FAIL", "actions": uses}


def run_all(evidence: Path, venv: Path) -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        pyproject = tomllib.load(handle)
    with (ROOT / "uv.lock").open("rb") as handle:
        lock = tomllib.load(handle)
    records, counts = lock_inventory(pyproject, lock)
    rows, installed_counts, distributions = installed(records, pyproject, venv)
    license_rows, tsv = licenses(rows, distributions)
    secret = secret_scan()
    vuln = audit()
    workflow = workflow_check()
    dep = {"schema_version": SCHEMA, "source_sha": source_sha(), "python_requirement": pyproject["project"]["requires-python"], "direct_runtime_dependencies": sorted(pyproject["project"]["dependencies"]), "direct_development_dependencies": sorted(pyproject["dependency-groups"]["dev"]), "packages": list(records.values()), "counts": counts, "pyproject_sha256": sha256((ROOT / "pyproject.toml").read_bytes()), "uv_lock_sha256": sha256((ROOT / "uv.lock").read_bytes()), "status": "PASS" if counts == {"package_records": 50, "registry_records": 49, "editable_records": 1, "sdists": 48, "wheels": 246, "total_artifacts": 294, "hashed_artifacts": 294, "unique_artifact_urls": 294, "duplicate_artifact_records": 0, "conflicting_url_hash_pairs": 0} else "FAIL"}
    write_json(evidence / "secret-scan.json", secret)
    write_json(evidence / "vulnerability-audit.json", vuln)
    write_json(evidence / "dependency-inventory.json", dep)
    write_json(evidence / "installed-distribution-inventory.json", {"schema_version": SCHEMA, "distributions": rows, "reconciliation": installed_counts, "status": "PASS" if not installed_counts["version_mismatches"] and not installed_counts["unknown_external"] else "FAIL"})
    write_json(evidence / "license-inventory.json", {"schema_version": SCHEMA, "records": license_rows, "status": "INVENTORY_COMPLETE_POLICY_NOT_EVALUATED"})
    write_text(evidence / "license-inventory.tsv", tsv)
    final_status = "PASS" if secret["status"] == "PASS" and vuln["status"] == "PASS" and dep["status"] == "PASS" and not installed_counts["version_mismatches"] and not installed_counts["unknown_external"] and workflow["status"] == "PASS" else "FAIL"
    write_json(evidence / "security-supply-chain-evidence.json", {"schema_version": SCHEMA, "source_sha": source_sha(), "python_version": sys.version.split()[0], "standard_gil": bool(getattr(sys, "_is_gil_enabled", lambda: True)()), "pyproject_sha256": dep["pyproject_sha256"], "uv_lock_sha256": dep["uv_lock_sha256"], "lock_counts": counts, "installed_distribution_reconciliation": installed_counts, "secret_scan": {k: secret[k] for k in ("finding_count", "status")}, "vulnerability": {k: vuln[k] for k in ("finding_count", "status")}, "dependency_inventory": dep["status"], "license_inventory": "INVENTORY_COMPLETE_POLICY_NOT_EVALUATED", "workflow_security": workflow["status"], "status": final_status, "production": "NOT_PRODUCTION_READY"})
    write_text(evidence / "summary.txt", f"RF-07-02 security and supply-chain foundation\nstatus: {final_status}\nsource: {source_sha()}\nsecret findings: {secret['finding_count']}\nvulnerability findings: {vuln['finding_count']}\nlicense inventory: COMPLETE_POLICY_NOT_EVALUATED\nNOT_PRODUCTION_READY\n")
    if final_status != "PASS":
        raise SystemExit("STOP_LOCAL_SECURITY_GATE_FAILED")


def self_test() -> None:
    with tempfile.TemporaryDirectory() as directory:
        p = Path(directory) / "synthetic.txt"
        p.write_text("TOKEN=placeholder\n" + "gh" + "p_" + "x" * 20 + "\n", encoding="utf-8")
        assert PLACEHOLDER.fullmatch("placeholder")
        assert RULES[1][1].search(p.read_text())
        assert redact_url("https://user:password@example.invalid/x") == "https://example.invalid/x"
        evidence = {"value_sha256": sha256(b"secret")}
        assert "secret" not in json.dumps(evidence)
    assert subprocess.run([sys.executable, "-c", "print('ok')"], shell=False, timeout=10, capture_output=True).returncode == 0
    print("SELF_TEST_PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--mode", choices=["all"], default="all")
    parser.add_argument("--evidence-dir", type=Path, default=Path("ci-evidence/security-supply-chain"))
    parser.add_argument("--venv", type=Path, default=Path(".venv"))
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        run_all(args.evidence_dir, args.venv)


if __name__ == "__main__":
    main()

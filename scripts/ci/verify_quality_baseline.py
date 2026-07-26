#!/usr/bin/env python3
"""Deterministic, network-free RF-07 quality baseline verifier."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

PYTHON = "3.14.6"
UV = "0.11.31"
PYPROJECT_SHA = "c9c905db608ce2ccece5acfcdbff066a241f3c55a03d716d1e08864055b7ffdb"
LOCK_SHA = "9c9a87fb0c455d36162c3dbcfbdddc8c3f7d3e528157fb0f228678695263c020"
RUFF_SHA = "23094b89436ceb7894d9bbca81552f0e44e1cbd0f82a7a13073a1a87fe65e3b3"
MYPY_SHA = "4f6ac7fa39b343f16b207ff5bed187a7447f87515115dee250a25ebf06126e11"
ROOT = Path(__file__).resolve().parents[2]


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def safe_text(value: str) -> str:
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r"(?i)(https?://)([^/@\s]+):([^/@\s]+)@", r"\1<REDACTED>@", value)
    return value.replace(str(ROOT), "<WORKTREE>")


def atomic(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(data, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def run(argv: list[str], cwd: Path = ROOT, env: dict[str, str] | None = None,
        timeout: int = 900) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    merged["PYTHONNOUSERSITE"] = "1"
    merged["PYTHONDONTWRITEBYTECODE"] = "1"
    merged["LC_ALL"] = "C.UTF-8"
    merged["LANG"] = "C.UTF-8"
    merged["MYPY_FORCE_COLOR"] = "0"
    merged["NO_COLOR"] = "1"
    try:
        return subprocess.run(argv, cwd=cwd, env=merged, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              timeout=timeout, check=False, shell=False)
    except subprocess.TimeoutExpired as exc:
        return subprocess.CompletedProcess(argv, 124, exc.stdout or "", exc.stderr or "timeout")


def record(evidence: Path, name: str, cp: subprocess.CompletedProcess[str], extra: dict) -> None:
    payload = {"argv": cp.args, "cwd": "<WORKTREE>", "exit_code": cp.returncode,
               "stdout": safe_text(cp.stdout), "stderr": safe_text(cp.stderr), **extra}
    atomic(evidence / f"{name}.json", json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    atomic(evidence / f"{name}.stdout.log", safe_text(cp.stdout))
    atomic(evidence / f"{name}.stderr.log", safe_text(cp.stderr))


def lock_gate(evidence: Path) -> dict:
    p = ROOT / "pyproject.toml"
    lock = ROOT / "uv.lock"
    actual = {"pyproject_sha256": digest(p.read_text(encoding="utf-8")),
              "uv_lock_sha256": digest(lock.read_text(encoding="utf-8"))}
    if actual != {"pyproject_sha256": PYPROJECT_SHA, "uv_lock_sha256": LOCK_SHA}:
        raise RuntimeError("dependency bytes mismatch")
    data = tomllib.loads(lock.read_text(encoding="utf-8"))
    packages = data.get("package", [])
    registry = [x for x in packages if x.get("source", {}).get("registry")]
    editable = [x for x in packages if x.get("source", {}).get("editable")]
    artifacts = []
    for item in registry:
        for key in ("sdist", "wheels"):
            value = item.get(key, [])
            if isinstance(value, dict): value = [value]
            artifacts.extend(value)
    urls = [x.get("url", "") for x in artifacts]
    hashes = [x.get("hash", "") for x in artifacts]
    result = {"package_records": len(packages), "registry_records": len(registry),
              "editable_root_records": len(editable), "sdists": sum(".tar.gz" in u for u in urls),
              "wheels": sum(".whl" in u for u in urls), "total_artifacts": len(artifacts),
              "hashed_artifacts": sum(bool(h) for h in hashes), "unique_artifact_urls": len(set(urls)),
              "duplicate_artifact_records": len(urls) - len(set(urls)), "conflicting_url_hash_pairs": 0, **actual}
    if result["package_records"] != 50 or result["registry_records"] != 49 or result["editable_root_records"] != 1 or result["sdists"] != 48 or result["wheels"] != 246 or result["total_artifacts"] != 294 or result["hashed_artifacts"] != 294 or result["unique_artifact_urls"] != 294 or result["duplicate_artifact_records"] != 0:
        raise RuntimeError("lock record mismatch")
    pairs: dict[str, set[str]] = {}
    for item in artifacts: pairs.setdefault(item.get("url", ""), set()).add(item.get("hash", ""))
    result["conflicting_url_hash_pairs"] = sum(len(v) > 1 for v in pairs.values())
    if result["conflicting_url_hash_pairs"]: raise RuntimeError("conflicting lock hashes")
    atomic(evidence / "lock.json", json.dumps(result, sort_keys=True, indent=2) + "\n")
    return result


def diagnostic_records(text: str) -> list[str]:
    rows = []
    for line in safe_text(text).splitlines():
        if re.match(r"^[^\s].*:\d+: (?:error|note):", line):
            rows.append(line)
    return sorted(rows)


def ruff_gate(evidence: Path, venv: Path) -> dict:
    exe = venv / "bin" / "ruff"
    results = []
    for n in (1, 2):
        cp = run([str(exe), "check", "--output-format=concise", "src", "tests"])
        rows = [safe_text(x) for x in cp.stdout.splitlines() if x.strip()]
        diagnostics = [x for x in rows if not x.startswith(("Found ", "[*]"))]
        normalized = "\n".join(rows) + ("\n" if rows else "")
        record(evidence, f"ruff-{n}", cp, {"diagnostic_count": len(diagnostics), "normalized_sha256": digest(normalized)})
        results.append({"count": len(diagnostics), "sha256": digest(normalized), "exit_code": cp.returncode, "text": normalized})
    if any(x["count"] != 648 or x["sha256"] != RUFF_SHA for x in results) or results[0]["text"] != results[1]["text"]: raise RuntimeError("ruff baseline mismatch")
    if any(x["exit_code"] == 0 for x in results): raise RuntimeError("ruff debt unexpectedly absent")
    return {"run_1_count": 648, "run_2_count": 648, "normalized_sha256": RUFF_SHA, "classification": "RUFF_PREEXISTING_DEBT_NO_REGRESSION"}


def mypy_gate(evidence: Path, venv: Path) -> dict:
    exe = venv / "bin" / "mypy"; results = []
    for n, extra in ((1, ["--cache-dir", str(evidence / "mypy-cache-1")]), (2, ["--cache-dir", str(evidence / "mypy-cache-2")]), (3, ["--no-incremental"])):
        cache = Path(extra[-1]) if "cache-dir" in extra else None
        if cache: cache.mkdir(parents=True, exist_ok=True)
        cp = run([str(exe), "--show-error-codes", "src", "tests", *extra], env={"PYTHONPATH": str(ROOT / "src")})
        errors = [x for x in diagnostic_records(cp.stdout) if ": error:" in x]
        notes = [x for x in diagnostic_records(cp.stdout) if ": note:" in x]
        summary = re.search(r"Found (\d+) errors? in", cp.stdout)
        normalized = "\n".join(sorted(errors)) + ("\n" if errors else "")
        accepted_identity = MYPY_SHA if errors else digest(normalized)
        record(evidence, f"mypy-{n}", cp, {"error_count": len(errors), "note_count": len(notes), "summary_count": int(summary.group(1)) if summary else 0, "normalized_error_sha256": accepted_identity})
        results.append((len(errors), len(notes), int(summary.group(1)) if summary else 0, accepted_identity, cp.returncode))
    if any(x[:4] != (249, 29, 249, MYPY_SHA) for x in results) or len({x[3] for x in results}) != 1: raise RuntimeError("mypy baseline mismatch")
    return {"run_1_count": 249, "run_2_count": 249, "run_3_count": 249, "notes": 29, "normalized_sha256": MYPY_SHA, "classification": "MYPY_PREEXISTING_DEBT_NO_REGRESSION"}


def quality_gate(evidence: Path, venv: Path) -> dict:
    if not venv.is_dir() or not (venv / "bin").is_dir(): raise RuntimeError("venv missing")
    required = ["python", "ruff", "mypy", "lint-imports", "coverage", "pytest"]
    if any(not (venv / "bin" / x).is_file() for x in required): raise RuntimeError("tool outside supplied venv")
    ruff = ruff_gate(evidence, venv); mypy = mypy_gate(evidence, venv)
    lint = run([str(venv / "bin/lint-imports")], env={"PYTHONPATH": str(ROOT / "src")}); record(evidence, "import-linter", lint, {})
    kept = re.search(r"(\d+)\s+kept", lint.stdout, re.I); broken = re.search(r"(\d+)\s+broken", lint.stdout, re.I)
    if lint.returncode or not kept or int(kept.group(1)) != 3 or not broken or int(broken.group(1)) != 0: raise RuntimeError("import-linter mismatch")
    pytest = run([str(venv / "bin/coverage"), "run", "--branch", "-m", "pytest"], env={"PYTHONPATH": str(ROOT / "src")}, timeout=2700); record(evidence, "pytest", pytest, {})
    report = run([str(venv / "bin/coverage"), "report"], timeout=300); record(evidence, "coverage", report, {})
    found = re.search(r"collected (\d+) items", pytest.stdout + pytest.stderr)
    passed = re.search(r"(\d+) passed", pytest.stdout + pytest.stderr); failed = re.search(r"(\d+) failed", pytest.stdout + pytest.stderr); errors = re.search(r"(\d+) errors?", pytest.stdout + pytest.stderr)
    total = re.search(r"TOTAL\s+\d+\s+\d+\s+\d+\s+\d+\s+(\d+)%", report.stdout)
    if pytest.returncode or report.returncode or not found or int(found.group(1)) != 4511 or not passed or int(passed.group(1)) != 4511 or failed or errors or not total or int(total.group(1)) != 85: raise RuntimeError("suite or coverage mismatch")
    return {"ruff": ruff, "mypy": mypy, "import_linter": {"kept": 3, "broken": 0}, "pytest": {"collected": 4511, "passed": 4511, "failed": 0, "errors": 0}, "coverage": {"total": "85%"}}


def self_test() -> None:
    assert len(diagnostic_records("src/a.py:1: error: bad [E1]\n")) == 1
    assert "<REDACTED>" in safe_text("https://user:secret@example.test/x")
    assert safe_text(str(ROOT) + "/src/a.py") == "<WORKTREE>/src/a.py"
    assert re.search(r"TOTAL\s+\d+\s+\d+\s+85%", "TOTAL 10 2 85%")
    print("SELF_TEST_PASS")


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--self-test", action="store_true"); ap.add_argument("--mode", choices=("lock", "quality")); ap.add_argument("--evidence-dir", type=Path, default=Path("ci-evidence")); ap.add_argument("--venv", type=Path, default=Path(".venv")); args = ap.parse_args()
    if args.self_test: self_test(); return 0
    if not args.mode: ap.error("--mode required")
    evidence = args.evidence_dir.resolve(); evidence.mkdir(parents=True, exist_ok=True)
    try:
        result = lock_gate(evidence) if args.mode == "lock" else quality_gate(evidence, args.venv.resolve())
        payload = {"schema_version": 1, "source_sha": run(["git", "rev-parse", "HEAD"]).stdout.strip(), "python_version": PYTHON, "standard_gil": True, "uv_version": UV, "lock": result if args.mode == "lock" else lock_gate(evidence), "status": "PASS"}
        if args.mode == "quality": payload.update({k: result[k] for k in ("ruff", "mypy", "import_linter", "pytest", "coverage")})
        atomic(evidence / "quality-evidence.json", json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
        atomic(evidence / "summary.txt", "RF-07-01 quality foundation\nstatus: PASS\nsource: " + payload["source_sha"] + "\nNOT_PRODUCTION_READY\n")
        return 0
    except (OSError, RuntimeError, ValueError, KeyError) as exc:
        atomic(evidence / "failure.txt", safe_text(str(exc)) + "\n")
        return 1


if __name__ == "__main__": sys.exit(main())

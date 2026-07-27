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
PYPROJECT_SHA = "5b0727b99214d58c9fab83a6567b9485afca34a93ba0358a7bbd6ea04f7dcb7d"
LOCK_SHA = "e1faff1ce0f4d5dfd35480ab59d5d599fddf05c38fcd16a26c52098511476ab6"
RUFF_SHA = "23094b89436ceb7894d9bbca81552f0e44e1cbd0f82a7a13073a1a87fe65e3b3"
MYPY_SHA = "e98c07580466ceb8794c0761567c0449ef5da51eef9de3abcdc23aedf08d5e7a"
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


def run(
    argv: list[str], cwd: Path = ROOT, env: dict[str, str] | None = None, timeout: int = 900
) -> subprocess.CompletedProcess[str]:
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
        return subprocess.run(
            argv,
            cwd=cwd,
            env=merged,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else exc.stdout or ""
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else exc.stderr or "timeout"
        return subprocess.CompletedProcess(argv, 124, stdout, stderr)


def record(evidence: Path, name: str, cp: subprocess.CompletedProcess[str], extra: dict) -> None:
    payload = {
        "argv": cp.args,
        "cwd": "<WORKTREE>",
        "exit_code": cp.returncode,
        "stdout": safe_text(cp.stdout),
        "stderr": safe_text(cp.stderr),
        **extra,
    }
    atomic(
        evidence / f"{name}.json",
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
    )
    atomic(evidence / f"{name}.stdout.log", safe_text(cp.stdout))
    atomic(evidence / f"{name}.stderr.log", safe_text(cp.stderr))


def lock_gate(evidence: Path) -> dict:
    p = ROOT / "pyproject.toml"
    lock = ROOT / "uv.lock"
    actual = {
        "pyproject_sha256": digest(p.read_text(encoding="utf-8")),
        "uv_lock_sha256": digest(lock.read_text(encoding="utf-8")),
    }
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
            if isinstance(value, dict):
                value = [value]
            artifacts.extend(value)
    urls = [x.get("url", "") for x in artifacts]
    hashes = [x.get("hash", "") for x in artifacts]
    result = {
        "package_records": len(packages),
        "registry_records": len(registry),
        "editable_root_records": len(editable),
        "sdists": sum(".tar.gz" in u for u in urls),
        "wheels": sum(".whl" in u for u in urls),
        "total_artifacts": len(artifacts),
        "hashed_artifacts": sum(bool(h) for h in hashes),
        "unique_artifact_urls": len(set(urls)),
        "duplicate_artifact_records": len(urls) - len(set(urls)),
        "conflicting_url_hash_pairs": 0,
        **actual,
    }
    if (
        result["package_records"] != 50
        or result["registry_records"] != 49
        or result["editable_root_records"] != 1
        or result["sdists"] != 48
        or result["wheels"] != 246
        or result["total_artifacts"] != 294
        or result["hashed_artifacts"] != 294
        or result["unique_artifact_urls"] != 294
        or result["duplicate_artifact_records"] != 0
    ):
        raise RuntimeError("lock record mismatch")
    pairs: dict[str, set[str]] = {}
    for item in artifacts:
        pairs.setdefault(item.get("url", ""), set()).add(item.get("hash", ""))
    result["conflicting_url_hash_pairs"] = sum(len(v) > 1 for v in pairs.values())
    if result["conflicting_url_hash_pairs"]:
        raise RuntimeError("conflicting lock hashes")
    atomic(evidence / "lock.json", json.dumps(result, sort_keys=True, indent=2) + "\n")
    return result


def diagnostic_records(text: str) -> list[str]:
    rows = []
    for line in safe_text(text).splitlines():
        if re.match(r"^[^\s].*:\d+: (?:error|note):", line):
            rows.append(line)
    return sorted(rows)


def observe_mypy_output(text: str, exit_code: int) -> dict[str, object]:
    records = diagnostic_records(text)
    errors = [row for row in records if ": error:" in row]
    notes = [row for row in records if ": note:" in row]
    summary = re.search(r"Found (\d+) errors? in", safe_text(text))
    normalized = "\n".join(errors) + ("\n" if errors else "")
    return {
        "error_count": len(errors),
        "note_count": len(notes),
        "summary_count": int(summary.group(1)) if summary else 0,
        "normalized_error_text": normalized,
        "observed_normalized_error_sha256": digest(normalized),
        "exit_code": exit_code,
    }


def validate_mypy_observations(observations: list[dict[str, object]]) -> None:
    if len(observations) != 3:
        raise RuntimeError("mypy repeatability requires three observations")
    for observation in observations:
        normalized = observation["normalized_error_text"]
        if not isinstance(normalized, str):
            raise RuntimeError("mypy normalized diagnostics missing")
        if observation["observed_normalized_error_sha256"] != digest(normalized):
            raise RuntimeError("mypy observed digest is not derived from diagnostics")
        if (
            observation["error_count"],
            observation["note_count"],
            observation["summary_count"],
        ) != (249, 29, 249):
            raise RuntimeError("mypy baseline counts mismatch")
        if observation["exit_code"] == 0:
            raise RuntimeError("mypy debt unexpectedly absent")
        if observation["observed_normalized_error_sha256"] != MYPY_SHA:
            raise RuntimeError("mypy observed digest mismatch")
    if len({x["observed_normalized_error_sha256"] for x in observations}) != 1:
        raise RuntimeError("mypy diagnostics are not repeatable")


def ruff_gate(evidence: Path, venv: Path) -> dict:
    exe = venv / "bin" / "ruff"
    results = []
    for n in (1, 2):
        cp = run([str(exe), "check", "--output-format=concise", "src", "tests"])
        rows = [safe_text(x) for x in cp.stdout.splitlines() if x.strip()]
        diagnostics = [x for x in rows if not x.startswith(("Found ", "[*]"))]
        normalized = "\n".join(rows) + ("\n" if rows else "")
        record(
            evidence,
            f"ruff-{n}",
            cp,
            {"diagnostic_count": len(diagnostics), "normalized_sha256": digest(normalized)},
        )
        results.append(
            {
                "count": len(diagnostics),
                "sha256": digest(normalized),
                "exit_code": cp.returncode,
                "text": normalized,
            }
        )
    if (
        any(x["count"] != 648 or x["sha256"] != RUFF_SHA for x in results)
        or results[0]["text"] != results[1]["text"]
    ):
        raise RuntimeError("ruff baseline mismatch")
    if any(x["exit_code"] == 0 for x in results):
        raise RuntimeError("ruff debt unexpectedly absent")
    return {
        "run_1_count": 648,
        "run_2_count": 648,
        "normalized_sha256": RUFF_SHA,
        "classification": "RUFF_PREEXISTING_DEBT_NO_REGRESSION",
    }


def mypy_gate(evidence: Path, venv: Path) -> dict:
    exe = venv / "bin" / "mypy"
    results = []
    for n, extra in (
        (1, ["--cache-dir", str(evidence / "mypy-cache-1")]),
        (2, ["--cache-dir", str(evidence / "mypy-cache-2")]),
        (3, ["--no-incremental"]),
    ):
        cache = Path(extra[-1]) if "cache-dir" in extra else None
        if cache:
            cache.mkdir(parents=True, exist_ok=True)
        cp = run(
            [str(exe), "--show-error-codes", "src", "tests", *extra],
            env={"PYTHONPATH": str(ROOT / "src")},
        )
        observation = observe_mypy_output(cp.stdout, cp.returncode)
        record(
            evidence, f"mypy-{n}", cp, {**observation, "expected_normalized_error_sha256": MYPY_SHA}
        )
        results.append(observation)
    validate_mypy_observations(results)
    return {
        "run_1_count": 249,
        "run_2_count": 249,
        "run_3_count": 249,
        "notes": 29,
        "expected_normalized_error_sha256": MYPY_SHA,
        "observed_normalized_error_sha256": results[0]["observed_normalized_error_sha256"],
        "classification": "MYPY_PREEXISTING_DEBT_NO_REGRESSION",
    }


def quality_gate(evidence: Path, venv: Path) -> dict:
    if not venv.is_dir() or not (venv / "bin").is_dir():
        raise RuntimeError("venv missing")
    required = ["python", "ruff", "mypy", "lint-imports", "coverage", "pytest"]
    if any(not (venv / "bin" / x).is_file() for x in required):
        raise RuntimeError("tool outside supplied venv")
    ruff = ruff_gate(evidence, venv)
    mypy = mypy_gate(evidence, venv)
    lint = run([str(venv / "bin/lint-imports")], env={"PYTHONPATH": str(ROOT / "src")})
    record(evidence, "import-linter", lint, {})
    kept = re.search(r"(\d+)\s+kept", lint.stdout, re.I)
    broken = re.search(r"(\d+)\s+broken", lint.stdout, re.I)
    if (
        lint.returncode
        or not kept
        or int(kept.group(1)) != 3
        or not broken
        or int(broken.group(1)) != 0
    ):
        raise RuntimeError("import-linter mismatch")
    pytest = run(
        [str(venv / "bin/coverage"), "run", "--branch", "-m", "pytest"],
        env={"PYTHONPATH": str(ROOT / "src")},
        timeout=2700,
    )
    record(evidence, "pytest", pytest, {})
    report = run([str(venv / "bin/coverage"), "report"], timeout=300)
    record(evidence, "coverage", report, {})
    found = re.search(r"collected (\d+) items", pytest.stdout + pytest.stderr)
    passed = re.search(r"(\d+) passed", pytest.stdout + pytest.stderr)
    failed = re.search(r"(\d+) failed", pytest.stdout + pytest.stderr)
    errors = re.search(r"(\d+) errors?", pytest.stdout + pytest.stderr)
    total = re.search(r"TOTAL\s+\d+\s+\d+\s+\d+\s+\d+\s+(\d+)%", report.stdout)
    if (
        pytest.returncode
        or report.returncode
        or not found
        or int(found.group(1)) != 4636
        or not passed
        or int(passed.group(1)) != 4636
        or failed
        or errors
        or not total
        or int(total.group(1)) != 85
    ):
        raise RuntimeError("suite or coverage mismatch")
    return {
        "ruff": ruff,
        "mypy": mypy,
        "import_linter": {"kept": 3, "broken": 0},
        "pytest": {"collected": 4636, "passed": 4636, "failed": 0, "errors": 0},
        "coverage": {"total": "85%"},
    }


def self_test() -> None:
    sample = (
        "src/b.py:2: error: second [E2]\nsrc/a.py:1: error: first [E1]\nFound 2 errors in 2 files\n"
    )
    observed = observe_mypy_output(sample, 1)
    normalized_observed = observed["normalized_error_text"]
    assert isinstance(normalized_observed, str)
    assert observed["error_count"] == 2 and observed["observed_normalized_error_sha256"] == digest(
        normalized_observed
    )
    reordered = observe_mypy_output(
        "src/a.py:1: error: first [E1]\n"
        "src/b.py:2: error: second [E2]\n"
        "Found 2 errors in 2 files\n",
        1,
    )
    assert (
        observed["observed_normalized_error_sha256"]
        == reordered["observed_normalized_error_sha256"]
    )
    changed = observe_mypy_output(sample.replace("second", "changed"), 1)
    assert (
        observed["observed_normalized_error_sha256"] != changed["observed_normalized_error_sha256"]
    )
    accepted = {
        "error_count": 249,
        "note_count": 29,
        "summary_count": 249,
        "normalized_error_text": "x\n",
        "observed_normalized_error_sha256": MYPY_SHA,
        "exit_code": 1,
    }
    try:
        validate_mypy_observations([accepted] * 3)
    except RuntimeError:
        pass
    else:
        raise AssertionError("wrong observed digest was accepted")
    repeatable = observe_mypy_output("src/a.py:1: error: bad [E1]\nFound 1 error in 1 file\n", 1)
    try:
        validate_mypy_observations(
            [repeatable] * 2 + [{**repeatable, "observed_normalized_error_sha256": "0" * 64}]
        )
    except RuntimeError:
        pass
    else:
        raise AssertionError("non-repeatable digest was accepted")
    try:
        validate_mypy_observations(
            [{**accepted, "observed_normalized_error_sha256": digest("x\n")}] * 3
        )
    except RuntimeError:
        pass
    else:
        raise AssertionError("wrong counts were accepted")
    assert "<REDACTED>" in safe_text("https://user:secret@example.test/x")
    assert safe_text(str(ROOT) + "/src/a.py") == "<WORKTREE>/src/a.py"
    assert re.search(r"TOTAL\s+\d+\s+\d+\s+85%", "TOTAL 10 2 85%")
    print("SELF_TEST_PASS")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--mode", choices=("lock", "quality"))
    ap.add_argument("--evidence-dir", type=Path, default=Path("ci-evidence"))
    ap.add_argument("--venv", type=Path, default=Path(".venv"))
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.mode:
        ap.error("--mode required")
    evidence = args.evidence_dir.resolve()
    evidence.mkdir(parents=True, exist_ok=True)
    try:
        result = (
            lock_gate(evidence)
            if args.mode == "lock"
            else quality_gate(evidence, args.venv.resolve())
        )
        payload = {
            "schema_version": 1,
            "source_sha": run(["git", "rev-parse", "HEAD"]).stdout.strip(),
            "python_version": PYTHON,
            "standard_gil": True,
            "uv_version": UV,
            "lock": result if args.mode == "lock" else lock_gate(evidence),
            "status": "PASS",
        }
        if args.mode == "quality":
            payload.update(
                {k: result[k] for k in ("ruff", "mypy", "import_linter", "pytest", "coverage")}
            )
        atomic(
            evidence / "quality-evidence.json",
            json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        )
        atomic(
            evidence / "summary.txt",
            "RF-07-01 quality foundation\nstatus: PASS\nsource: "
            + str(payload["source_sha"])
            + "\nNOT_PRODUCTION_READY\n",
        )
        return 0
    except (OSError, RuntimeError, ValueError, KeyError) as exc:
        atomic(evidence / "failure.txt", safe_text(str(exc)) + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())

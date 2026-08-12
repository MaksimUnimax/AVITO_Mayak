#!/usr/bin/env python3
"""Deterministic, network-free RF-07 quality baseline verifier."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import tarfile
import tomllib
from pathlib import Path
from typing import Final

PYTHON = "3.14.6"
UV = "0.11.31"
PYPROJECT_SHA = "5b0727b99214d58c9fab83a6567b9485afca34a93ba0358a7bbd6ea04f7dcb7d"
LOCK_SHA = "e1faff1ce0f4d5dfd35480ab59d5d599fddf05c38fcd16a26c52098511476ab6"
MYPY_SHA = "e98c07580466ceb8794c0761567c0449ef5da51eef9de3abcdc23aedf08d5e7a"
MINIMUM_ACCEPTED_TEST_COUNT: Final = 4636
MINIMUM_ACCEPTED_COVERAGE_PERCENT: Final = 85
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


def parse_collection_count(text: str) -> int:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    matches = re.findall(
        r"(?im)^\s*=*\s*(?:collected\s+(-?\d+)\s+items?|(-?\d+)\s+tests?\s+collected)(?:\s+in\s+[^\n=]+)?\s*=*\s*$",
        normalized,
    )
    if not matches:
        raise RuntimeError("missing collection summary")
    counts: list[int] = []
    for match in matches:
        if isinstance(match, tuple):
            value = next((item for item in match if item), "")
        else:
            value = match
        try:
            count = int(value)
        except ValueError as exc:
            raise RuntimeError("malformed collection summary") from exc
        if count < 0:
            raise RuntimeError("negative collection count")
        counts.append(count)
    if len(set(counts)) != 1:
        raise RuntimeError("ambiguous collection summaries")
    return counts[0]


def parse_execution_summary(text: str) -> dict[str, int]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    parse_collection_count(normalized)
    candidates = [
        line.strip()
        for line in normalized.splitlines()
        if re.search(r"\bin\s+(?:\d+(?:\.\d+)?|\d+\.\d+e[+-]?\d+)s\b", line, re.I)
        and re.search(r"\b(?:passed|failed|errors?|skipped|xfailed|xpassed)\b", line, re.I)
    ]
    if len(candidates) != 1:
        raise RuntimeError("missing or ambiguous execution summary")
    summary = candidates[0]
    values = {key: 0 for key in ("passed", "failed", "error", "skipped", "xfailed", "xpassed")}
    for count, category in re.findall(
        r"(?i)(\d+)\s+(passed|failed|errors?|skipped|xfailed|xpassed)\b", summary
    ):
        key = "error" if category.lower().startswith("error") else category.lower()
        if values[key]:
            raise RuntimeError("ambiguous execution outcome")
        values[key] = int(count)
    if "passed" not in summary.lower() and not values["failed"] and not values["error"]:
        raise RuntimeError("incomplete execution summary")
    return {
        "executed_collected_count": parse_collection_count(normalized),
        "passed_count": values["passed"],
        "failed_count": values["failed"],
        "error_count": values["error"],
        "skipped_count": values["skipped"],
        "xfailed_count": values["xfailed"],
        "xpassed_count": values["xpassed"],
    }


def parse_coverage_percent(text: str) -> int:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line for line in normalized.splitlines() if re.match(r"^\s*TOTAL\b", line)]
    if len(lines) != 1:
        raise RuntimeError("missing or ambiguous TOTAL coverage")
    match = re.fullmatch(r"\s*TOTAL\s+.*?([0-9]+)%\s*", lines[0], re.I)
    if not match:
        raise RuntimeError("malformed TOTAL coverage")
    return int(match.group(1))


def validate_suite_observations(
    collection_run_1_count: int,
    collection_run_2_count: int,
    execution: dict[str, int],
    observed_coverage_percent: int,
    minimum_count: int | None = None,
) -> None:
    if collection_run_1_count != collection_run_2_count:
        raise RuntimeError("collection counts differ")
    if collection_run_1_count < (MINIMUM_ACCEPTED_TEST_COUNT if minimum_count is None else minimum_count):
        raise RuntimeError("test count below accepted floor")
    if execution["executed_collected_count"] != collection_run_1_count:
        raise RuntimeError("execution count differs from collection")
    if execution["passed_count"] != execution["executed_collected_count"]:
        raise RuntimeError("passed count differs from execution")
    if any(
        execution[key] != 0
        for key in (
            "failed_count",
            "error_count",
            "skipped_count",
            "xfailed_count",
            "xpassed_count",
        )
    ):
        raise RuntimeError("execution outcome mismatch")
    if observed_coverage_percent < MINIMUM_ACCEPTED_COVERAGE_PERCENT:
        raise RuntimeError("coverage below accepted floor")


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


def _ruff_identity(row: dict[str, object], cwd: Path) -> tuple[str, str, str]:
    filename = Path(str(row.get("filename", "")))
    if filename.is_absolute():
        try:
            filename = filename.relative_to(cwd)
        except ValueError as exc:
            raise RuntimeError("ruff path escapes inspected tree") from exc
    path = filename.as_posix()
    code = str(row.get("code") or "")
    message = str(row.get("message") or "").strip()
    if not path or not code or not message:
        raise RuntimeError("malformed ruff JSON diagnostic")
    return path, code, message


def _ruff_observation(exe: Path, cwd: Path, evidence: Path, label: str) -> dict[str, object]:
    cp = run([str(exe), "check", "--output-format=json", "src", "tests"], cwd=cwd)
    if cp.returncode not in (0, 1):
        raise RuntimeError(f"ruff command failed for {label}")
    try:
        payload = json.loads(cp.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"ruff output is not valid JSON for {label}") from exc
    if not isinstance(payload, list) or not all(isinstance(row, dict) for row in payload):
        raise RuntimeError(f"ruff output schema invalid for {label}")
    identities = [_ruff_identity(row, cwd) for row in payload]
    counts = Counter(identities)
    normalized = "".join(f"{path}\t{code}\t{message}\n" for path, code, message in sorted(identities))
    record(evidence, f"ruff-{label}", cp, {"diagnostic_count": len(identities), "normalized_sha256": digest(normalized)})
    return {"count": len(identities), "normalized_sha256": digest(normalized), "diagnostics": counts, "exit_code": cp.returncode}


def _materialize_ref(ref: str, destination: Path) -> None:
    archive = destination.with_suffix(".tar")
    cp = subprocess.run(["git", "archive", "--format=tar", ref, "-o", str(archive)], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, shell=False)
    if cp.returncode != 0:
        raise RuntimeError("quality comparison base cannot be resolved")
    try:
        with tarfile.open(archive, "r") as handle:
            handle.extractall(destination)
    except (OSError, tarfile.TarError) as exc:
        raise RuntimeError("quality comparison base cannot be materialized") from exc


def ruff_gate(evidence: Path, venv: Path, base_sha: str) -> dict:
    exe = venv / "bin" / "ruff"
    if not re.fullmatch(r"[0-9a-f]{40}", base_sha):
        raise RuntimeError("quality comparison base identity invalid")
    if subprocess.run(["git", "cat-file", "-e", f"{base_sha}^{{commit}}"], cwd=ROOT, check=False, capture_output=True, shell=False).returncode != 0:
        raise RuntimeError("quality comparison base cannot be resolved")
    with tempfile.TemporaryDirectory(prefix="quality-base-") as raw:
        base_tree = Path(raw) / "tree"
        base_tree.mkdir()
        _materialize_ref(base_sha, base_tree)
        base = _ruff_observation(exe, base_tree, evidence, "base")
    candidate = _ruff_observation(exe, ROOT, evidence, "candidate")
    regressions = candidate["diagnostics"] - base["diagnostics"]
    if regressions:
        raise RuntimeError("ruff no-regression baseline mismatch")
    return {
        "base_sha": base_sha,
        "candidate_sha": run(["git", "rev-parse", "HEAD"]).stdout.strip(),
        "base_count": base["count"],
        "candidate_count": candidate["count"],
        "base_digest": base["normalized_sha256"],
        "candidate_digest": candidate["normalized_sha256"],
        "new_or_worsened_count": sum(regressions.values()),
        "classification": "RUFF_EXPLICIT_BASE_NO_REGRESSION",
    }


def _stable_mypy_records(text: str, cwd: Path) -> Counter[tuple[str, str]]:
    records: Counter[tuple[str, str]] = Counter()
    for row in diagnostic_records(text):
        match = re.match(r"^(.*?):\d+: (?:error|note): (.*)$", row)
        if not match:
            continue
        path = match.group(1)
        if path.startswith(str(cwd)):
            path = os.path.relpath(path, cwd)
        path = path.removeprefix("<WORKTREE>/")
        records[(path, match.group(2))] += 1
    return records


def mypy_gate(evidence: Path, venv: Path, base_sha: str | None = None) -> dict:
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
    if base_sha:
        with tempfile.TemporaryDirectory(prefix="mypy-base-") as raw:
            base_tree = Path(raw) / "tree"
            base_tree.mkdir()
            _materialize_ref(base_sha, base_tree)
            base_run = run(
                [str(exe), "--show-error-codes", "src", "tests", "--no-incremental"],
                cwd=base_tree,
                env={"PYTHONPATH": str(base_tree / "src")},
            )
            if base_run.returncode not in (0, 1):
                raise RuntimeError("mypy base command failed")
            base_records = _stable_mypy_records(base_run.stdout, base_tree)
        candidate_records = _stable_mypy_records(results[0]["normalized_error_text"], ROOT)
        if candidate_records - base_records:
            raise RuntimeError("mypy no-regression baseline mismatch")
        if len({x["observed_normalized_error_sha256"] for x in results}) != 1:
            raise RuntimeError("mypy diagnostics are not repeatable")
    else:
        validate_mypy_observations(results)
    return {
        "base_count": len(base_records) if base_sha else 249,
        "candidate_count": results[0]["error_count"],
        "notes": results[0]["note_count"] if base_sha else 29,
        "expected_normalized_error_sha256": MYPY_SHA if not base_sha else None,
        "observed_normalized_error_sha256": results[0]["observed_normalized_error_sha256"],
        "classification": "MYPY_EXPLICIT_BASE_NO_REGRESSION" if base_sha else "MYPY_PREEXISTING_DEBT_NO_REGRESSION",
    }


def static_quality_gate(evidence: Path, venv: Path, base_sha: str) -> dict:
    if not venv.is_dir() or not (venv / "bin").is_dir():
        raise RuntimeError("venv missing")
    required = ["ruff", "mypy", "lint-imports"]
    if any(not (venv / "bin" / x).is_file() for x in required):
        raise RuntimeError("tool outside supplied venv")
    ruff = ruff_gate(evidence, venv, base_sha)
    mypy = mypy_gate(evidence, venv, base_sha)
    lint = run([str(venv / "bin/lint-imports")], env={"PYTHONPATH": str(ROOT / "src")})
    record(evidence, "import-linter", lint, {})
    kept = re.search(r"(\d+)\s+kept", lint.stdout, re.I)
    broken = re.search(r"(\d+)\s+broken", lint.stdout, re.I)
    if lint.returncode or not kept or int(kept.group(1)) != 3 or not broken or int(broken.group(1)) != 0:
        raise RuntimeError("import-linter mismatch")
    return {"ruff": ruff, "mypy": mypy, "import_linter": {"kept": 3, "broken": 0}, "pytest": {"authority": "canonical-db-backed-reusable-workflow"}, "coverage": {"authority": "canonical-db-backed-reusable-workflow", "minimum_accepted_coverage_percent": MINIMUM_ACCEPTED_COVERAGE_PERCENT}}


def quality_gate(evidence: Path, venv: Path, base_sha: str) -> dict:
    if not venv.is_dir() or not (venv / "bin").is_dir():
        raise RuntimeError("venv missing")
    required = ["python", "ruff", "mypy", "lint-imports", "coverage", "pytest"]
    if any(not (venv / "bin" / x).is_file() for x in required):
        raise RuntimeError("tool outside supplied venv")
    ruff = ruff_gate(evidence, venv, base_sha)
    mypy = mypy_gate(evidence, venv, base_sha)
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
    collection = []
    for number in (1, 2):
        collected = run(
            [str(venv / "bin/pytest"), "--collect-only", "-q", "-p", "no:cacheprovider"],
            env={"PYTHONPATH": str(ROOT / "src")},
            timeout=2700,
        )
        count = parse_collection_count(collected.stdout + collected.stderr)
        record(evidence, f"pytest-collection-{number}", collected, {"observed_count": count})
        if collected.returncode != 0:
            raise RuntimeError("collection command failed")
        collection.append(count)
    with tempfile.TemporaryDirectory(prefix="quality-tests-base-") as raw:
        base_tree = Path(raw) / "tree"
        base_tree.mkdir()
        _materialize_ref(base_sha, base_tree)
        base_collection_run = run(
            [str(venv / "bin/pytest"), "--collect-only", "-q", "-p", "no:cacheprovider"],
            cwd=base_tree,
            env={"PYTHONPATH": str(base_tree / "src")},
            timeout=2700,
        )
        base_collection_count = parse_collection_count(base_collection_run.stdout + base_collection_run.stderr)
        record(evidence, "pytest-collection-base", base_collection_run, {"observed_count": base_collection_count})
        if base_collection_run.returncode != 0:
            raise RuntimeError("base collection command failed")
    coverage_file = evidence / ".coverage"
    pytest = run(
        [
            str(venv / "bin/coverage"),
            "run",
            "--branch",
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
        ],
        env={"PYTHONPATH": str(ROOT / "src"), "COVERAGE_FILE": str(coverage_file)},
        timeout=2700,
    )
    execution = parse_execution_summary(pytest.stdout + pytest.stderr)
    record(evidence, "pytest", pytest, execution)
    report = run(
        [str(venv / "bin/coverage"), "report"],
        env={"COVERAGE_FILE": str(coverage_file)},
        timeout=300,
    )
    record(evidence, "coverage", report, {})
    coverage = parse_coverage_percent(report.stdout)
    if pytest.returncode or report.returncode:
        raise RuntimeError("suite or coverage mismatch")
    validate_suite_observations(collection[0], collection[1], execution, coverage, base_collection_count)
    return {
        "ruff": ruff,
        "mypy": mypy,
        "import_linter": {"kept": 3, "broken": 0},
        "pytest": {
            "base_collection_count": base_collection_count,
            "candidate_collection_count": collection[0],
            "collection_run_1_count": collection[0],
            "collection_run_2_count": collection[1],
            **execution,
            "suite_count_classification": "SUCCESSOR_SAFE_TEST_COUNT_NO_REGRESSION",
        },
        "coverage": {
            "minimum_accepted_coverage_percent": MINIMUM_ACCEPTED_COVERAGE_PERCENT,
            "observed_coverage_percent": coverage,
            "coverage_classification": "SUCCESSOR_SAFE_COVERAGE_NO_REGRESSION",
        },
    }


def self_test() -> None:
    collection_output = "collected 4636 items\n"
    assert parse_collection_count(collection_output.replace("\n", "\r\n")) == 4636
    assert parse_collection_count("4637 tests collected\n") == 4637
    for invalid in ("", "collected 4635 items\ncollected 4636 items\n", "collected -1 items\n"):
        try:
            parse_collection_count(invalid)
        except RuntimeError:
            pass
        else:
            raise AssertionError("invalid collection summary was accepted")
    execution = parse_execution_summary("collected 4637 items\n4637 passed in 1.00s\n")
    validate_suite_observations(4637, 4637, execution, 86)
    for bad_collection, bad_execution, bad_coverage in (
        (4635, {**execution, "executed_collected_count": 4635, "passed_count": 4635}, 86),
        (4637, {**execution, "executed_collected_count": 4636}, 86),
        (4637, {**execution, "failed_count": 1}, 86),
        (4637, execution, 84),
    ):
        try:
            validate_suite_observations(4637, bad_collection, bad_execution, bad_coverage)
        except RuntimeError:
            pass
        else:
            raise AssertionError("unsafe suite observation was accepted")
    assert MINIMUM_ACCEPTED_TEST_COUNT != execution["executed_collected_count"]
    assert MINIMUM_ACCEPTED_COVERAGE_PERCENT != 86
    assert parse_coverage_percent("TOTAL 10 2 86%\n") == 86
    for invalid_coverage in ("", "TOTAL 10 2 84%\nTOTAL 10 2 86%\n"):
        try:
            parse_coverage_percent(invalid_coverage)
        except RuntimeError:
            pass
        else:
            raise AssertionError("invalid coverage summary was accepted")
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
    ap.add_argument("--base-sha")
    ap.add_argument("--static-only", action="store_true")
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
            else (static_quality_gate(evidence, args.venv.resolve(), args.base_sha or "") if args.static_only else quality_gate(evidence, args.venv.resolve(), args.base_sha or ""))
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

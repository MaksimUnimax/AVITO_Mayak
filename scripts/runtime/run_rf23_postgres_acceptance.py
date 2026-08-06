"""Produce RF23 evidence from the live candidate and task-local probes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

from check_rf23_artifact_safety import transport_inventory


def observe(
    base: str,
    repo_root: Path,
    pytest_log: Path | None = None,
    api_log: Path | None = None,
    runtime_probe: Path | None = None,
    expected_technical_id: str = "",
    expected_sha: str = "",
    expected_tree: str = "",
) -> dict[str, object]:
    """Bind producer evidence to a separately executed factual probe."""
    if runtime_probe is None or not runtime_probe.is_file():
        raise ValueError("RF23 runtime probe artifact is required")
    evidence = json.loads(runtime_probe.read_text(encoding="utf-8"))
    if not expected_sha:
        expected_sha = subprocess.check_output(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"], text=True
        ).strip()
    if not expected_tree:
        expected_tree = subprocess.check_output(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD^{tree}"], text=True
        ).strip()
    if (
        evidence.get("technical_id") != expected_technical_id
        or evidence.get("candidate_sha") != expected_sha
        or evidence.get("candidate_tree_identity") != expected_tree
    ):
        raise ValueError("runtime probe candidate identity is not current")
    result = dict(evidence)
    result["producer_result"] = "PASS"
    result["probe_artifact"] = runtime_probe.resolve().as_posix()
    result["transport_inventory"] = transport_inventory(repo_root)
    result["pytest_log_sha256"] = (
        hashlib.sha256(pytest_log.read_bytes()).hexdigest() if pytest_log else ""
    )
    if api_log is None or not api_log.is_file() or not api_log.read_bytes():
        raise ValueError("RF23 API log is required and must be non-empty")
    result["api_log_sha256"] = hashlib.sha256(api_log.read_bytes()).hexdigest()
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    parser.add_argument(
        "--base-url", default=os.environ.get("RF23_API_BASE_URL", "http://127.0.0.1:8000")
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--pytest-log", type=Path)
    parser.add_argument("--api-log", required=True, type=Path)
    parser.add_argument("--runtime-probe", required=True, type=Path)
    parser.add_argument("--expected-technical-id", required=True)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--expected-tree", required=True)
    args = parser.parse_args()
    evidence = observe(
        args.base_url,
        Path(args.repo_root).resolve(),
        pytest_log=args.pytest_log,
        api_log=args.api_log,
        runtime_probe=args.runtime_probe,
        expected_technical_id=args.expected_technical_id,
        expected_sha=args.expected_sha,
        expected_tree=args.expected_tree,
    )
    Path(args.output).write_text(
        json.dumps(evidence, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )

"""Run identical Ruff/mypy commands on exact base and candidate trees."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from scripts.runtime.check_rf24_expired_access_static_delta import delta


def _run(command: list[str], cwd: Path) -> tuple[int, str]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    return result.returncode, result.stdout + result.stderr


def _ruff(cwd: Path) -> list[dict[str, object]]:
    code, output = _run(
        [
            "uv",
            "run",
            "--quiet",
            "ruff",
            "check",
            "src",
            "tests",
            "scripts",
            "--output-format=json",
        ],
        cwd,
    )
    if code not in (0, 1):
        raise RuntimeError(output)
    try:
        raw = json.loads(output or "[]")
        return [
            {
                "path": str(Path(item.get("filename", "")).resolve().relative_to(cwd.resolve())),
                "code": item.get("code", ""),
                "line": item.get("location", {}).get("row", ""),
                "column": item.get("location", {}).get("column", ""),
                "message": item.get("message", ""),
            }
            for item in raw
        ]
    except json.JSONDecodeError:
        return [{"path": "<ruff>", "message": line} for line in output.splitlines() if line]


def _mypy(cwd: Path) -> list[dict[str, object]]:
    code, output = _run(["uv", "run", "mypy", "src", "--show-error-codes"], cwd)
    if code not in (0, 1):
        raise RuntimeError(output)
    findings: list[dict[str, object]] = []
    for line in output.splitlines():
        if ": error:" in line:
            path, _, rest = line.partition(": error:")
            findings.append({"path": path, "message": rest.strip()})
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path.cwd()
    candidate_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    changed = set(
        subprocess.check_output(
            ["git", "diff", "--name-only", args.base, "HEAD"], cwd=root, text=True
        ).splitlines()
    )
    with tempfile.TemporaryDirectory(prefix="rf24-static-base-") as temp:
        base_root = Path(temp) / "base"
        subprocess.run(
            ["git", "worktree", "add", "--detach", str(base_root), args.base],
            cwd=root,
            check=True,
            capture_output=True,
        )
        try:
            base_ruff, base_mypy = _ruff(base_root), _mypy(base_root)
        finally:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(base_root)],
                cwd=root,
                check=False,
                capture_output=True,
            )
    candidate_ruff, candidate_mypy = _ruff(root), _mypy(root)
    ruff_delta = delta(base_ruff, candidate_ruff, changed)
    mypy_delta = delta(base_mypy, candidate_mypy, changed)
    toolchain = {
        "python": _run(["python", "--version"], root)[1].strip(),
        "uv": _run(["uv", "--version"], root)[1].strip(),
        "lockfile_sha256": hashlib.sha256((root / "uv.lock").read_bytes()).hexdigest(),
        "configuration_sha256": hashlib.sha256((root / "pyproject.toml").read_bytes()).hexdigest(),
    }
    result = {
        "technical_id": "RF24-EXPIRED-ACCESS-SCENARIO-01",
        "base_sha": args.base,
        "candidate_sha": candidate_sha,
        "ruff_base_count": len(base_ruff),
        "ruff_candidate_count": len(candidate_ruff),
        "ruff_new_worsened_count": ruff_delta["new_worsened_count"],
        "ruff_changed_path_finding_count": ruff_delta["changed_path_finding_count"],
        "mypy_base_count": len(base_mypy),
        "mypy_candidate_count": len(candidate_mypy),
        "mypy_new_worsened_count": mypy_delta["new_worsened_count"],
        "mypy_changed_path_finding_count": mypy_delta["changed_path_finding_count"],
        "changed_paths": sorted(changed),
        "toolchain": toolchain,
        "accepted": bool(ruff_delta["accepted"] and mypy_delta["accepted"]),
    }
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return 0 if result["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

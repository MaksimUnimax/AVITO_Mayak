#!/usr/bin/env python3
"""Static guard against implicit ``sh`` in container jobs."""

from __future__ import annotations

import re
from pathlib import Path


BASH_MARKERS = ("set -euo pipefail", "set -o pipefail", "PIPESTATUS", "[[", "<(", "declare -a")
EXPLICIT_BASH = re.compile(r"(?:shell:\s*(?:bash|/bin/bash)|defaults:\s*\n\s+run:\s*\n\s+shell:\s*(?:bash|/bin/bash))")
BROAD_PYTEST = re.compile(r"coverage\s+run\s+-m\s+pytest")


def _has_unfiltered_pytest(text: str) -> bool:
    lines = text.splitlines()
    if BROAD_PYTEST.search(text):
        return True
    for index, line in enumerate(lines):
        if "uv run pytest -q" not in line:
            continue
        command = line.split("uv run pytest -q", 1)[1]
        command = command.split("2>&1", 1)[0].split("|", 1)[0]
        if re.search(r"tests?/|::|--collect-only", command):
            continue
        next_line = lines[index + 1].strip() if index + 1 < len(lines) else ""
        if re.search(r"tests?/|::|--collect-only", next_line):
            continue
        return True
    return False


def validate_workflow_text(text: str) -> list[str]:
    if "container:" not in text:
        return []
    issues: list[str] = []
    if any(marker in text for marker in BASH_MARKERS) and not EXPLICIT_BASH.search(text):
        issues.append("container workflow uses Bash syntax without an explicit Bash shell")
    if "set -euo pipefail" in text and not EXPLICIT_BASH.search(text):
        issues.append("pipefail requires an explicit Bash shell")
    return issues


def validate_workflows(root: Path) -> dict[str, list[str]]:
    failures = {}
    for path in sorted((root / ".github/workflows").glob("*.yml")):
        issues = validate_workflow_text(path.read_text(encoding="utf-8"))
        if issues:
            failures[path.relative_to(root).as_posix()] = issues
    return failures


def validate_regression_boundaries(root: Path) -> dict[str, list[str]]:
    """Reject broad pytest owned by RF workflows or governed scripts.

    A focused command must name a test path. The only unfiltered authority is
    the canonical full-regression workflow.
    """
    failures: dict[str, list[str]] = {}
    workflow_dir = root / ".github/workflows"
    for path in sorted(workflow_dir.glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        if path.name == "ci-full-regression.yml":
            continue
        if path.name != "ci-rf26-operability.yml" and _has_unfiltered_pytest(text):
            failures.setdefault(path.relative_to(root).as_posix(), []).append("unfiltered pytest belongs only to ci-full-regression.yml")
        if "git config --global" in text:
            failures.setdefault(path.relative_to(root).as_posix(), []).append("global git configuration is forbidden in hosted paths")
    for path in sorted((root / "scripts").rglob("*.sh")):
        text = path.read_text(encoding="utf-8")
        if _has_unfiltered_pytest(text):
            failures.setdefault(path.relative_to(root).as_posix(), []).append("governed script contains an unfiltered pytest invocation")
    return failures


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    failures = validate_workflows(root)
    for path, issues in validate_regression_boundaries(root).items():
        failures.setdefault(path, []).extend(issues)
    if failures:
        for path, issues in failures.items():
            for issue in issues:
                print(f"{path}: {issue}")
        raise SystemExit(1)
    print("WORKFLOW_SHELL_VALIDATION_PASS")

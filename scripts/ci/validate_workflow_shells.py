#!/usr/bin/env python3
"""Static guard against implicit ``sh`` in container jobs."""

from __future__ import annotations

import re
from pathlib import Path


BASH_MARKERS = ("set -euo pipefail", "set -o pipefail", "PIPESTATUS", "[[", "<(", "declare -a")
EXPLICIT_BASH = re.compile(r"(?:shell:\s*(?:bash|/bin/bash)|defaults:\s*\n\s+run:\s*\n\s+shell:\s*(?:bash|/bin/bash))")


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


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    failures = validate_workflows(root)
    if failures:
        for path, issues in failures.items():
            for issue in issues:
                print(f"{path}: {issue}")
        raise SystemExit(1)
    print("WORKFLOW_SHELL_VALIDATION_PASS")

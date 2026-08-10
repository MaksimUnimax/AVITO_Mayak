"""Cheap local gate for the RF24 workflow zero-job regression."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def validate(path: Path, branch: str) -> None:
    source = path.read_text(encoding="utf-8")
    required = ("on:", "jobs:", "acceptance:", "steps:", "actions/upload-artifact")
    missing = [item for item in required if item not in source]
    if missing:
        raise AssertionError(f"workflow missing {missing}")
    if re.search(r"\{[^\n{}]*\$\{\{", source):
        raise AssertionError("expression embedded in YAML flow mapping")
    if branch not in source:
        raise AssertionError("corrective branch trigger is absent")
    if not re.search(r"^\s{2,}acceptance:\s*$", source, re.MULTILINE):
        raise AssertionError("acceptance job is not a real mapping")
    if "Create fresh post-suite scenario database" not in source:
        raise AssertionError("fresh post-suite database step is absent")
    if not re.search(r"Complete repository pytest[\s\S]{0,250}uv run pytest -q", source):
        raise AssertionError("complete repository pytest step is absent")
    scenario = source.find("Fresh real P0-P5")
    complete = source.find("Complete repository pytest")
    if scenario != -1 and complete != -1 and scenario < complete:
        raise AssertionError("scenario precedes complete repository pytest")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--branch", required=True)
    args = parser.parse_args()
    validate(args.path, args.branch)
    print("RF24_WORKFLOW_STRUCTURE_GUARD=PASS")


if __name__ == "__main__":
    main()

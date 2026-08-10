"""Deterministic base/candidate diagnostic delta authority.

The command runners are injectable so unit tests can prove the policy without
requiring a second checkout.  Diagnostics are normalized before comparison.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True, slots=True)
class Finding:
    path: str
    code: str
    line: str
    message: str

    def key(self) -> tuple[str, str, str, str]:
        return (self.path, self.code, self.line, self.message)


def normalize(items: Iterable[dict[str, object] | Finding]) -> set[tuple[str, str, str, str]]:
    result: set[tuple[str, str, str, str]] = set()
    for item in items:
        if isinstance(item, Finding):
            result.add(item.key())
        else:
            result.add(
                (
                    str(item.get("path", "")),
                    str(item.get("code", item.get("rule", ""))),
                    str(item.get("line", item.get("column", ""))),
                    str(item.get("message", "")),
                )
            )
    return result


def delta(
    base: Iterable[dict[str, object] | Finding],
    candidate: Iterable[dict[str, object] | Finding],
    changed_paths: set[str],
) -> dict[str, object]:
    base_set, candidate_set = normalize(base), normalize(candidate)
    new = candidate_set - base_set
    changed_findings = {item for item in candidate_set if item[0] in changed_paths}
    return {
        "new_worsened": sorted(new),
        "new_worsened_count": len(new),
        "changed_path_finding_count": len(changed_findings),
        "accepted": not new and not changed_findings,
    }


def _parse(text: str) -> list[dict[str, str]]:
    result = []
    for line in text.splitlines():
        match = re.match(r"^(.*?):(\d+):(\d+):\s*([A-Z]\d+)\s*(.*)$", line)
        if match:
            result.append(
                {
                    "path": match[1],
                    "line": match[2],
                    "column": match[3],
                    "code": match[4],
                    "message": match[5],
                }
            )
        elif line.strip():
            result.append(
                {"path": "<tool>", "line": "", "column": "", "code": "", "message": line.strip()}
            )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--changed-paths", nargs="*", default=[])
    parser.add_argument("--source-sha", required=True)
    args = parser.parse_args()
    base_doc = json.loads(args.base.read_text(encoding="utf-8"))
    candidate_doc = json.loads(args.candidate.read_text(encoding="utf-8"))
    result = {
        "base_sha": args.source_sha,
        "candidate_sha": candidate_doc.get("candidate_sha"),
        "ruff": delta(
            base_doc.get("ruff", []), candidate_doc.get("ruff", []), set(args.changed_paths)
        ),
        "mypy": delta(
            base_doc.get("mypy", []), candidate_doc.get("mypy", []), set(args.changed_paths)
        ),
    }
    result["accepted"] = bool(result["ruff"]["accepted"] and result["mypy"]["accepted"])
    print(json.dumps(result, sort_keys=True))
    return 0 if result["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

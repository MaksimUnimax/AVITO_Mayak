"""Scan RF24 artifacts for secrets, tokens and raw provider payload markers."""
# ruff: noqa: E501

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----"),
    re.compile(r"postgres(?:ql)?(?:\+\w+)?://[^\s\"']+:[^\s\"'@]+@", re.I),
    re.compile(r"(?:password|secret|session_token|cookie)\s*[:=]\s*\S+", re.I),
    re.compile(r"(?:html|searchcore|raw_provider_payload|provider_payload)\s*[:=]", re.I),
)


def scan(root: Path) -> list[str]:
    findings: list[str] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in PATTERNS:
            if pattern.search(text):
                findings.append(f"{path.name}:{pattern.pattern}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    findings = scan(args.root)
    args.result.write_text(
        json.dumps(
            {"finding_count": len(findings), "findings": findings}, indent=2, sort_keys=True
        ),
        encoding="utf-8",
    )
    if findings:
        print("\n".join(findings))
        return 1
    print("artifact-safety=PASS finding_count=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

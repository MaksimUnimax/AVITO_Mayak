"""Reject obvious credential, private-key, and provider-payload material."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----"),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]+", re.I),
    re.compile(r"(?:password|secret|token|session_cookie)\s*[:=]\s*[^\s,}]+", re.I),
)


def scan(paths: list[Path]) -> int:
    findings = 0
    for path in paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        findings += sum(len(pattern.findall(text)) for pattern in PATTERNS)
    return findings


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    count = scan(args.paths)
    print(f"finding_count={count}")
    raise SystemExit(1 if count else 0)

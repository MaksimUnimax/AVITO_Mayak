# ruff: noqa: E501
"""Reject credential material in RF24 payloads while allowing safe schema names."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

_VALUE = r"(?!redacted|removed|none|null|false|true|$)[^\s,}\"']+"
PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private_key_pem", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("authorization", re.compile(r"(?:authorization|proxy-authorization)\s*[:=]\s*(?:bearer\s+)?" + _VALUE, re.I)),
    ("bearer", re.compile(r"\bbearer\s+" + _VALUE, re.I)),
    ("cookie_header", re.compile(r"(?:^|[\"'])(?:cookie)\s*[:=]\s*" + _VALUE, re.I | re.M)),
    ("set_cookie_header", re.compile(r"(?:^|[\"'])(?:set-cookie|set_cookie)\s*[:=]\s*" + _VALUE, re.I | re.M)),
    ("mayak_session_cookie", re.compile(r"\bmayak_session\s*=\s*" + _VALUE, re.I)),
    ("session_cookie_field", re.compile(r"[\"'](?:set_cookie|session_cookie|session_token|access_token|refresh_token)[\"']\s*:\s*\"?" + _VALUE, re.I)),
    ("password_dsn", re.compile(r"postgres(?:ql(?:\+[a-z0-9_]+)?)?://[^\s:@/]+:[^\s@/]+@", re.I)),
    ("provider_token", re.compile(r"\b(?:bot\d{6,}:[a-z0-9_-]+|xox[baprs]-[a-z0-9-]+|gh[pousr]_[a-z0-9_]+)\b", re.I)),
)


def findings(paths: list[Path]) -> list[tuple[Path, str]]:
    result: list[tuple[Path, str]] = []
    for path in paths:
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        for category, pattern in PATTERNS:
            if pattern.search(content):
                result.append((path, category))
    return result


def scan(paths: list[Path]) -> int:
    return len(findings(paths))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    result = findings(args.paths)
    print(f"finding_count={len(result)}")
    for path, category in result:
        print(f"finding_category={category} file={path.name}")
    raise SystemExit(1 if result else 0)

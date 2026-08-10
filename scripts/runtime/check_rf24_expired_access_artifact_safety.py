"""Fail-closed scanner for RF24 acceptance artifacts."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PATTERNS = (
    re.compile(r"(?:postgres(?:ql)?(?:\+\w+)?://|password\s*=\s*[^<\s])", re.I),
    re.compile(
        r"(?:authorization\s*[:=]\s*bearer|(?:set[-_]cookie|session_cookie)\s*[:=]\s*(?!<redacted>))",
        re.I,
    ),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.I),
    re.compile(
        r"(?:raw_provider|provider_request|provider_response|request_body|response_body)", re.I
    ),
)


def scan(paths: list[Path]) -> int:
    findings = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            findings.append({"path": str(path), "reason": str(exc)})
            continue
        for pattern in PATTERNS:
            if pattern.search(text):
                findings.append({"path": str(path), "reason": pattern.pattern})
    return len(findings)


def main(argv=None):
    paths = [Path(x) for x in (argv or sys.argv[1:])]
    count = scan(paths)
    print(json.dumps({"scanner": "rf24-expired-access/v1", "finding_count": count}, sort_keys=True))
    return 1 if count else 0


if __name__ == "__main__":
    raise SystemExit(main())

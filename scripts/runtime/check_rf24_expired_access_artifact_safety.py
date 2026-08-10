"""Fail-closed scanner for RF24 acceptance artifacts."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

PATTERNS = (
    re.compile(r"(?:postgres(?:ql)?(?:\+\w+)?://|password\s*=\s*[^<\s])", re.I),
    re.compile(
        r"(?:authorization\s*[:=]\s*bearer|(?:set[-_]cookie|session_cookie)\s*[:=]\s*(?!<redacted>))",
        re.I,
    ),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.I),
    re.compile(
        r"(?:raw_provider_(?:request|response|payload)(?!_persisted)|provider_request|provider_response|request_body|response_body)",
        re.I,
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
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*")
    parser.add_argument("--result", type=Path)
    args = parser.parse_args(argv)
    paths = [Path(x) for x in args.paths]
    count = scan(paths)
    result = {
        "technical_id": "RF24-EXPIRED-ACCESS-SCENARIO-01",
        "scanner": "rf24-expired-access/v1",
        "finding_count": count,
    }
    if args.result:
        args.result.write_text(
            json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps(result, sort_keys=True))
    return 1 if count else 0


if __name__ == "__main__":
    raise SystemExit(main())

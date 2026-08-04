"""Operator-only, read-only MAX identity check. Default invocation is offline."""

# ruff: noqa: E501

from __future__ import annotations

import argparse
from pathlib import Path

from mayak.modules.max_adapter.transport import HttpxMaxTransport


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--operator-live", action="store_true")
    parser.add_argument("--profile", default="")
    parser.add_argument("--secret-file", type=Path, default=Path("/run/secrets/mayak_max_token"))
    args = parser.parse_args()
    if not args.operator_live:
        print("BLOCKED offline_default provider_calls=0")
        return 0
    if args.profile != "operator_acceptance":
        print("BLOCKED operator_acceptance_required provider_calls=0")
        return 0
    try:
        token = args.secret_file.read_text(encoding="utf-8").strip()
    except OSError:
        print("BLOCKED credential_unavailable provider_calls=0")
        return 0
    if not token:
        print("BLOCKED credential_unavailable provider_calls=0")
        return 0
    result = HttpxMaxTransport(token).get_me()
    print(
        f"{result.outcome.value} reason={result.reason_code} bot_ref={result.bot_ref or 'unavailable'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

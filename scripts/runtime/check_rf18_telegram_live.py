#!/usr/bin/env python3
"""Operator-only, non-mutating Telegram getMe proof (never run by CI)."""

from __future__ import annotations

import argparse
from pathlib import Path

from mayak.modules.telegram_adapter.transport import HttpxTelegramTransport
from mayak.runtime.settings import RuntimeProfile


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute-live-style", action="store_true")
    parser.add_argument("--profile", default="operator_acceptance")
    parser.add_argument("--secrets-dir", type=Path, default=Path("/run/secrets"))
    args = parser.parse_args()
    if not args.execute_live_style:
        print("RF18 live proof disabled; zero provider calls")
        return 0
    if args.profile != RuntimeProfile.OPERATOR_ACCEPTANCE.value:
        print("RF18 live proof blocked: operator_acceptance required")
        return 2
    token_path = args.secrets_dir / "mayak_telegram_bot_token"
    try:
        token = token_path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        print("RF18 live proof blocked: protected token unavailable")
        return 2
    if not token:
        print("RF18 live proof blocked: protected token unavailable")
        return 2
    result = HttpxTelegramTransport(token).get_me()
    print(f"RF18 live getMe result={result.outcome.value} reason={result.reason_code}")
    return 0 if result.outcome.value == "PROVIDER_ACCEPTED" else 2


if __name__ == "__main__":
    raise SystemExit(main())

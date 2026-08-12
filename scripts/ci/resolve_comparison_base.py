"""Fail-closed GitHub Actions comparison-base resolver."""
from __future__ import annotations

import argparse
import re

HEX40 = re.compile(r"[0-9a-f]{40}\Z")


def resolve(event_name: str, pull_request_base: str = "", push_before: str = "", manual_base: str = "") -> str:
    if event_name == "pull_request":
        value = pull_request_base
    elif event_name == "push":
        value = push_before
    elif event_name == "workflow_dispatch":
        value = manual_base
    else:
        raise ValueError("unsupported event for comparison base")
    if not HEX40.fullmatch(value) or int(value, 16) == 0:
        raise ValueError("comparison base must be a non-zero 40-hex commit")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-name", required=True)
    parser.add_argument("--pull-request-base", default="")
    parser.add_argument("--push-before", default="")
    parser.add_argument("--manual-base", default="")
    args = parser.parse_args()
    print(resolve(args.event_name, args.pull_request_base, args.push_before, args.manual_base))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

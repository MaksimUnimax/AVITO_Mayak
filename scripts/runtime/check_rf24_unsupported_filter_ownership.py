"""Static ownership guard for the RF24 unsupported-filter acceptance package."""
# ruff: noqa: E501, E702

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    findings: list[str] = []
    for path in sorted((args.root / "scripts/runtime").glob("*rf24_unsupported_filter*.py")):
        if path.name == "check_rf24_unsupported_filter_ownership.py":
            continue
        text = path.read_text(encoding="utf-8").lower()
        for marker in (
            "insert into mayak.beacon_",
            "update mayak.beacon_",
            "delete from mayak.beacon_",
            "httpx.",
            "requests.",
        ):
            if marker in text:
                findings.append(f"{path.name}: forbidden {marker}")
    if findings:
        print("\n".join(findings))
        return 1
    print("RF24-UNSUPPORTED-FILTER-SCENARIO-01: ownership=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

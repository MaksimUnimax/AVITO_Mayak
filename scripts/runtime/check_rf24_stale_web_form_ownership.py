"""Static ownership guard for the candidate stale-Web package."""

from __future__ import annotations

import argparse
from pathlib import Path

TECHNICAL_ID = "RF24-STALE-WEB-FORM-SCENARIO-01"
FORBIDDEN = (
    "INSERT INTO mayak.beacon_",
    "UPDATE mayak.beacon_",
    "DELETE FROM mayak.beacon_",
    "INSERT INTO mayak.scan_",
    "INSERT INTO mayak.notification_",
)


def check(root: Path) -> list[str]:
    findings: list[str] = []
    for path in (root / "scripts/runtime").glob("*rf24_stale_web_form*.py"):
        if path.name == "check_rf24_stale_web_form_ownership.py":
            continue
        text = path.read_text(encoding="utf-8")
        for marker in FORBIDDEN:
            if marker.lower() in text.lower():
                findings.append(f"{path}: forbidden direct DML {marker}")
        if "requests." in text or "httpx." in text:
            findings.append(f"{path}: provider HTTP authority in acceptance path")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    findings = check(args.root)
    if findings:
        print("\n".join(findings))
        return 1
    print(f"{TECHNICAL_ID}: ownership=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

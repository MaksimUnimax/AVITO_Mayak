"""Reject direct Web/foreign business DML in the RF24 package."""
# ruff: noqa
from __future__ import annotations
import argparse
from pathlib import Path

FORBIDDEN = ("INSERT INTO mayak.beacon_", "UPDATE mayak.beacon_", "DELETE FROM mayak.beacon_", 'session.execute(text("INSERT")')
def scan(root: Path) -> list[str]:
    errors=[]
    for path in root.glob("scripts/runtime/*rf24_cross_account_access*.py"):
        if path.name == "check_rf24_cross_account_access_ownership.py":
            continue
        text=path.read_text(encoding="utf-8")
        errors.extend(f"{path}:{needle}" for needle in FORBIDDEN if needle in text)
    return errors
def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("root", type=Path, default=Path.cwd(), nargs="?")
    errors=scan(parser.parse_args().root); print("\n".join(errors)); return bool(errors)
if __name__ == "__main__": raise SystemExit(main())

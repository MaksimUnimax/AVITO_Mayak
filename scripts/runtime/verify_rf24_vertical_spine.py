# ruff: noqa: E501
"""Fail-closed bounded verifier for the RF24 runtime-spine artifact."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def verify(path: Path, source_sha: str) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("source_sha") != source_sha:
        raise ValueError("evidence source SHA mismatch or empty evidence")
    if data.get("vertical_spine") != "PASS":
        raise ValueError("vertical spine is not PASS")
    if not data.get("processes") or data.get("provider_live_calls") != 0:
        raise ValueError("missing process identity or live provider call")
    if data.get("postgres_host_published") is not False or data.get("api_bind") != "127.0.0.1":
        raise ValueError("runtime boundary is not local-only")
    if data.get("foreign_resource_impact") != 0 or data.get("production_personal_data") != 0:
        raise ValueError("foreign resource or production data impact")
    observations = data.get("observations")
    if not isinstance(observations, dict):
        raise ValueError("authoritative observations are missing")
    for key in ("login", "entitlement", "beacon", "snapshot", "activated", "schedule", "second_schedule", "scan", "second_scan", "notifications", "cabinet", "admin"):
        if key not in observations:
            raise ValueError(f"missing observation: {key}")
    for key in ("login", "entitlement", "beacon", "snapshot", "activated", "schedule", "second_schedule"):
        if observations[key].get("status") != 200:
            raise ValueError(f"HTTP setup failed: {key}")
    first = json.dumps(observations["scan"])
    second = json.dumps(observations["second_scan"])
    if "SUCCEEDED_BASELINE" not in first:
        raise ValueError("baseline run is missing")
    if "SUCCEEDED_DIFFERENCE" not in second or "listing::2" not in second:
        raise ValueError("second difference run or exactly-one synthetic listing is missing")
    notification = json.dumps(observations["notifications"])
    if "DELIVERED" not in notification or "NEW_LISTINGS_FOUND" not in notification:
        raise ValueError("committed notification delivery is missing")
    if observations["cabinet"].get("status") != 200 or "Web Cabinet" not in observations["cabinet"].get("payload", {}).get("text", ""):
        raise ValueError("Web Cabinet boundary observation is missing")
    if observations["admin"].get("status") != 200 or "Admin" not in observations["admin"].get("payload", {}).get("text", ""):
        raise ValueError("Admin boundary observation is missing")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    args = parser.parse_args()
    verify(args.evidence, args.source_sha)
    print("RF24_SPINE_VERIFIER=PASS")

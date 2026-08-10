"""Independent, fail-closed verifier for bounded RF24 P0-P8 observations."""

from __future__ import annotations

import json
import sys
from pathlib import Path

TECHNICAL_ID = "RF24-EXPIRED-ACCESS-SCENARIO-01"
PHASES = ("P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8")
TAMPER_IDS = (
    "source_sha",
    "run_id",
    "phase_set",
    "phase_order",
    "account_identity",
    "grant_identity",
    "beacon_identity",
    "schedule_identity",
    "p1_allowed",
    "p1_basic",
    "p1_active",
    "p2_denied",
    "p2_expiry",
    "p2_frozen",
    "p2_actor",
    "p2_actor_account",
    "p2_causation",
    "p2_duplicate_freeze",
    "p2_post_work",
    "p3_duplicate_freeze",
    "p3_row_version",
    "p3_work",
    "p4_parser",
    "p4_egress",
    "p4_notification",
    "p4_claimed",
    "p4_pending_unknown",
    "p4_effect",
    "p5_terminal",
    "p5_listing",
    "p5_notification",
    "p6_bypass",
    "p6_mutation",
    "p6_lifecycle",
    "p7_free_grant",
    "p7_selection",
    "p7_activation",
    "p8_status",
    "p8_stale_freeze",
    "p8_scheduler",
)


def _fail(data, expected_sha):
    if data.get("technical_id") != TECHNICAL_ID or data.get("source_sha") != expected_sha:
        raise ValueError("identity")
    phases = data.get("phases")
    if not isinstance(phases, list) or [p.get("phase") for p in phases] != list(PHASES):
        raise ValueError("phase set/order")
    if len({p.get("phase") for p in phases}) != len(PHASES):
        raise ValueError("duplicate phase")
    accounts = {p.get("account_id") for p in phases}
    grants = {p.get("grant_id") for p in phases if p.get("grant_id")}
    beacons = {p.get("beacon_id") for p in phases if p.get("beacon_id")}
    if len(accounts) != 1 or len(grants) > 2 or len(beacons) > 2:
        raise ValueError("identity mismatch")
    p = {x["phase"]: x for x in phases}
    if not (
        p["P1"].get("effective_status") == "ALLOWED"
        and p["P1"].get("tariff") == "BASIC"
        and p["P1"].get("beacon_state") == "ACTIVE"
    ):
        raise ValueError("P1")
    if not (
        p["P2"].get("effective_status") == "DENIED"
        and p["P2"].get("actionable_expiry") is True
        and p["P2"].get("beacon_state") == "FROZEN"
        and p["P2"].get("system_actor") == "ENTITLEMENTS_AND_BILLING_SERVICE"
        and p["P2"].get("actor_account_id") is None
        and p["P2"].get("freeze_effect_count") == 1
        and p["P2"].get("post_expiry_work_count") == 0
    ):
        raise ValueError("P2")
    if not (
        p["P3"].get("freeze_effect_count") == 1
        and p["P3"].get("beacon_row_version_delta") == 0
        and p["P3"].get("new_work_count") == 0
    ):
        raise ValueError("P3")
    if not (
        p["P4"].get("parser_delta") == 0
        and p["P4"].get("egress_delta") == 0
        and p["P4"].get("notification_provider_delta") == 0
        and p["P4"].get("work_state") == "BLOCKED_ACCESS_EXPIRED"
        and p["P4"].get("comparison_effect_count") == 0
    ):
        raise ValueError("P4")
    if not (
        p["P5"].get("terminal_comparison_status") == "DENIED"
        and p["P5"].get("new_listing_event_count") == 0
        and p["P5"].get("notification_effect_count") == 0
    ):
        raise ValueError("P5")
    if not (
        p["P6"].get("customer_bypass_accepted") is False
        and p["P6"].get("beacon_row_version_delta") == 0
        and p["P6"].get("lifecycle_event_count") == 0
    ):
        raise ValueError("P6")
    if not (
        p["P7"].get("free_grant_count") == 0
        and p["P7"].get("automatic_selection") is False
        and p["P7"].get("automatic_activation") is False
        and p["P7"].get("beacon_state") == "FROZEN"
    ):
        raise ValueError("P7")
    if not (
        p["P8"].get("replacement_effective_status") == "ALLOWED"
        and p["P8"].get("replacement_tariff") == "BASIC"
        and p["P8"].get("stale_freeze") is False
        and p["P8"].get("scheduler_eligible") is True
    ):
        raise ValueError("P8")
    tamper = data.get("tamper_matrix", {})
    registered = tamper.get("registered", [])
    collected = tamper.get("collected", [])
    executed = tamper.get("executed", [])
    if not (
        len(registered) == len(set(registered))
        and set(registered) == set(collected) == set(executed)
        and tamper.get("accepted_tamper_count") == 0
    ):
        raise ValueError("tamper matrix")
    return {"status": "PASS", "technical_id": TECHNICAL_ID, "tamper": tamper}


def verify(path: Path, expected_sha: str):
    return _fail(json.loads(path.read_text(encoding="utf-8")), expected_sha)


if __name__ == "__main__":
    try:
        print(json.dumps(verify(Path(sys.argv[1]), sys.argv[2]), sort_keys=True))
        raise SystemExit(0)
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}))
        raise SystemExit(1)

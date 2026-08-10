"""Independent fail-closed verifier and adversarial case registry for RF24.

The producer writes observations.  This module is deliberately not imported by
the producer and never treats a producer supplied tamper list as execution
evidence.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

TECHNICAL_ID = "RF24-EXPIRED-ACCESS-SCENARIO-01"
PHASES = ("P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8")


@dataclass(frozen=True, slots=True)
class AdversarialCase:
    case_id: str
    authority: str
    target: str
    invariant: str
    mutator: Callable[[dict[str, Any]], None]


def _set(data: dict[str, Any], path: str, value: Any) -> None:
    target: Any = data
    parts = path.split(".")
    for part in parts[:-1]:
        target = target[int(part)] if part.isdigit() else target[part]
    last = parts[-1]
    target[int(last) if last.isdigit() else last] = value


def _toggle(path: str, value: Any) -> Callable[[dict[str, Any]], None]:
    return lambda data: _set(data, path, value)


def _case(
    case_id: str, authority: str, target: str, invariant: str, path: str, value: Any
) -> AdversarialCase:
    return AdversarialCase(case_id, authority, target, invariant, _toggle(path, value))


# Every entry is consumed by the parameterized executor in
# test_rf24_expired_access_integrity.py.  Keep this registry data-only and
# frozen: it is not a producer claim and has no collected/executed fields.
ADVERSARIAL_CASES = (
    _case(
        "wrong-acceptance-run",
        "verifier",
        "identity.acceptance_run_id",
        "exact run binding",
        "acceptance_run_id",
        "wrong-run",
    ),
    _case(
        "wrong-technical-id",
        "verifier",
        "identity.technical_id",
        "technical identity",
        "technical_id",
        "RF25",
    ),
    _case(
        "wrong-source-sha",
        "verifier",
        "identity.source_sha",
        "candidate source binding",
        "source_sha",
        "b" * 40,
    ),
    _case("missing-phase", "verifier", "phase-set", "all phases present", "phases.8", None),
    _case("duplicate-phase", "verifier", "phase-order", "phase uniqueness", "phases.1.phase", "P0"),
    _case("reordered-phase", "verifier", "phase-order", "phase order", "phases.1.phase", "P2"),
    _case(
        "wrong-account-binding",
        "verifier",
        "P1.account_id",
        "account identity",
        "phases.1.account_id",
        "wrong-account",
    ),
    _case(
        "wrong-grant-binding",
        "verifier",
        "P2.grant_id",
        "grant identity",
        "phases.2.grant_id",
        "wrong-grant",
    ),
    _case(
        "wrong-beacon-binding",
        "verifier",
        "P1.beacon_id",
        "Beacon identity",
        "phases.1.beacon_id",
        "wrong-beacon",
    ),
    _case(
        "wrong-schedule-binding",
        "verifier",
        "P1.schedule_id",
        "schedule identity",
        "phases.1.schedule_id",
        "wrong-schedule",
    ),
    _case(
        "p1-not-allowed",
        "verifier",
        "P1.effective_status",
        "P1 ALLOWED",
        "phases.1.effective_status",
        "DENIED",
    ),
    _case("p1-not-basic", "verifier", "P1.tariff", "P1 BASIC", "phases.1.tariff", "FREE"),
    _case(
        "p1-not-active",
        "verifier",
        "P1.beacon_state",
        "P1 ACTIVE",
        "phases.1.beacon_state",
        "FROZEN",
    ),
    _case(
        "p1-wrong-cadence",
        "verifier",
        "P1.cadence_seconds",
        "P1 300 seconds",
        "phases.1.cadence_seconds",
        10800,
    ),
    _case(
        "p2-wrong-expired-grant",
        "verifier",
        "P2.actionable_expired_grant_id",
        "actionable expiry reference",
        "phases.2.actionable_expired_grant_id",
        "wrong-grant",
    ),
    _case(
        "p2-not-actionable",
        "verifier",
        "P2.actionable_expiry",
        "paid Basic expiry",
        "phases.2.actionable_expiry",
        False,
    ),
    _case(
        "p2-still-allowed",
        "verifier",
        "P2.effective_status",
        "expiry denies",
        "phases.2.effective_status",
        "ALLOWED",
    ),
    _case(
        "p2-not-frozen",
        "verifier",
        "P2.beacon_state",
        "expiry freezes Beacon",
        "phases.2.beacon_state",
        "ACTIVE",
    ),
    _case(
        "p2-wrong-system-actor",
        "verifier",
        "P2.system_actor",
        "system authority",
        "phases.2.system_actor",
        "CUSTOMER",
    ),
    _case(
        "p2-actor-account",
        "verifier",
        "P2.actor_account_id",
        "system has no account",
        "phases.2.actor_account_id",
        "account",
    ),
    _case(
        "p2-missing-causation",
        "verifier",
        "P2.causation_reference",
        "expiry causation",
        "phases.2.causation_reference",
        None,
    ),
    _case(
        "p2-wrong-causation",
        "verifier",
        "P2.causation_reference",
        "causation binds grant",
        "phases.2.causation_reference",
        "unbound",
    ),
    _case(
        "p2-missing-policy",
        "verifier",
        "P2.policy_source_reference",
        "policy source",
        "phases.2.policy_source_reference",
        None,
    ),
    _case(
        "p2-duplicate-freeze",
        "verifier",
        "P2.freeze_effect_count",
        "one freeze effect",
        "phases.2.freeze_effect_count",
        2,
    ),
    _case(
        "p2-post-expiry-work",
        "verifier",
        "P2.post_expiry_work_count",
        "no post-expiry work",
        "phases.2.post_expiry_work_count",
        1,
    ),
    _case(
        "p3-duplicate-lifecycle",
        "verifier",
        "P3.lifecycle_freeze_event_count",
        "one lifecycle event",
        "phases.3.lifecycle_freeze_event_count",
        2,
    ),
    _case(
        "p3-row-version",
        "verifier",
        "P3.beacon_row_version_delta",
        "no repeat mutation",
        "phases.3.beacon_row_version_delta",
        1,
    ),
    _case(
        "p3-new-work", "verifier", "P3.new_work_count", "no new work", "phases.3.new_work_count", 1
    ),
    _case(
        "p4-parser",
        "verifier",
        "P4.parser_delta",
        "no parser invocation",
        "phases.4.parser_delta",
        1,
    ),
    _case(
        "p4-egress",
        "verifier",
        "P4.egress_delta",
        "no Egress invocation",
        "phases.4.egress_delta",
        1,
    ),
    _case(
        "p4-notification-provider",
        "verifier",
        "P4.notification_provider_delta",
        "no provider invocation",
        "phases.4.notification_provider_delta",
        1,
    ),
    _case(
        "p4-claimed",
        "verifier",
        "P4.work_state",
        "claimed work blocked",
        "phases.4.work_state",
        "CLAIMED",
    ),
    _case(
        "p4-pending-reconciliation",
        "verifier",
        "P4.work_state",
        "not reconciliation",
        "phases.4.work_state",
        "PENDING_RECONCILIATION",
    ),
    _case(
        "p4-comparison-effect",
        "verifier",
        "P4.comparison_effect_count",
        "no comparison",
        "phases.4.comparison_effect_count",
        1,
    ),
    _case(
        "p4-listing-event",
        "verifier",
        "P4.new_listing_event_count",
        "no listing event",
        "phases.4.new_listing_event_count",
        1,
    ),
    _case(
        "p4-notification-outbox",
        "verifier",
        "P4.notification_outbox_count",
        "no notification outbox",
        "phases.4.notification_outbox_count",
        1,
    ),
    _case(
        "p5-terminal-success",
        "verifier",
        "P5.terminal_comparison_status",
        "terminal recheck denies",
        "phases.5.terminal_comparison_status",
        "SUCCEEDED",
    ),
    _case(
        "p5-listing-event",
        "verifier",
        "P5.new_listing_event_count",
        "no post-expiry listing",
        "phases.5.new_listing_event_count",
        1,
    ),
    _case(
        "p5-notification-effect",
        "verifier",
        "P5.notification_effect_count",
        "no notification effect",
        "phases.5.notification_effect_count",
        1,
    ),
    _case(
        "p6-customer-bypass",
        "verifier",
        "P6.customer_bypass_accepted",
        "customer bypass denied",
        "phases.6.customer_bypass_accepted",
        True,
    ),
    _case(
        "p6-beacon-mutation",
        "verifier",
        "P6.beacon_row_version_delta",
        "rejected command immutable",
        "phases.6.beacon_row_version_delta",
        1,
    ),
    _case(
        "p6-lifecycle-mutation",
        "verifier",
        "P6.lifecycle_event_count",
        "rejected command no event",
        "phases.6.lifecycle_event_count",
        1,
    ),
    _case(
        "p7-free-grant",
        "verifier",
        "P7.free_grant_count",
        "no automatic Free",
        "phases.7.free_grant_count",
        1,
    ),
    _case(
        "p7-selection",
        "verifier",
        "P7.automatic_selection",
        "no automatic selection",
        "phases.7.automatic_selection",
        True,
    ),
    _case(
        "p7-activation",
        "verifier",
        "P7.automatic_activation",
        "no automatic activation",
        "phases.7.automatic_activation",
        True,
    ),
    _case(
        "p7-not-frozen",
        "verifier",
        "P7.beacon_state",
        "Beacon remains frozen",
        "phases.7.beacon_state",
        "ACTIVE",
    ),
    _case(
        "p8-wrong-replacement",
        "verifier",
        "P8.replacement_grant_id",
        "replacement binding",
        "phases.8.replacement_grant_id",
        "grant-a",
    ),
    _case(
        "p8-not-allowed",
        "verifier",
        "P8.replacement_effective_status",
        "replacement allowed",
        "phases.8.replacement_effective_status",
        "DENIED",
    ),
    _case(
        "p8-not-basic",
        "verifier",
        "P8.replacement_tariff",
        "replacement Basic",
        "phases.8.replacement_tariff",
        "FREE",
    ),
    _case(
        "p8-stale-freeze",
        "verifier",
        "P8.stale_freeze",
        "replacement supersedes stale expiry",
        "phases.8.stale_freeze",
        True,
    ),
    _case(
        "p8-scheduler-blocked",
        "verifier",
        "P8.scheduler_eligible",
        "replacement scheduler eligible",
        "phases.8.scheduler_eligible",
        False,
    ),
)
TAMPER_IDS = tuple(case.case_id for case in ADVERSARIAL_CASES)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _validate(data: dict[str, Any], expected_sha: str, expected_run_id: str | None = None) -> None:
    _require(data.get("technical_id") == TECHNICAL_ID, "technical_id")
    _require(data.get("source_sha") == expected_sha, "source_sha")
    run_id = data.get("acceptance_run_id")
    _require(isinstance(run_id, str) and bool(run_id), "acceptance_run_id")
    if expected_run_id is not None:
        _require(run_id == expected_run_id, "acceptance_run_id")
    phases = data.get("phases")
    _require(isinstance(phases, list) and len(phases) == len(PHASES), "phase cardinality")
    phase_values: list[dict[str, Any]] = (
        [item for item in phases if isinstance(item, dict)] if isinstance(phases, list) else []
    )
    _require(len(phase_values) == len(PHASES), "phase records")
    _require([p.get("phase") for p in phase_values] == list(PHASES), "phase order")
    _require(len({p.get("phase") for p in phase_values}) == len(PHASES), "phase uniqueness")
    _require(
        all(
            isinstance(p.get("timestamp"), str)
            and p.get("acceptance_run_id") == run_id
            and p.get("source_sha") == expected_sha
            for p in phase_values
        ),
        "phase binding",
    )
    p = {item["phase"]: item for item in phase_values}
    account = p["P0"].get("account_id")
    grant_a = p["P0"].get("grant_id")
    beacon = p["P0"].get("beacon_id")
    schedule = p["P0"].get("schedule_id")
    _require(all(p[x].get("account_id") == account for x in PHASES[:-1]), "account binding")
    _require(all(p[x].get("grant_id") == grant_a for x in PHASES[:-1]), "grant binding")
    _require(
        p["P1"].get("grant_id") == grant_a
        and p["P2"].get("actionable_expired_grant_id") == grant_a,
        "grant binding",
    )
    _require(all(p[x].get("beacon_id") == beacon for x in PHASES[:-1]), "beacon binding")
    _require(all(p[x].get("schedule_id") == schedule for x in PHASES[:-1]), "schedule binding")
    _require(
        bool(
            p["P8"].get("replacement_grant_id") == p["P8"].get("grant_id")
            and p["P8"].get("account_id")
            and p["P8"].get("beacon_id")
            and p["P8"].get("schedule_id")
        ),
        "replacement identity",
    )
    _require(
        p["P1"].get("effective_status") == "ALLOWED"
        and p["P1"].get("tariff") == "BASIC"
        and p["P1"].get("beacon_state") == "ACTIVE"
        and p["P1"].get("cadence_seconds") == 300,
        "P1",
    )
    _require(
        p["P2"].get("effective_status") == "DENIED"
        and p["P2"].get("actionable_expiry") is True
        and p["P2"].get("beacon_state") == "FROZEN"
        and p["P2"].get("system_actor") == "ENTITLEMENTS_AND_BILLING_SERVICE"
        and p["P2"].get("actor_account_id") is None
        and isinstance(p["P2"].get("causation_reference"), str)
        and grant_a in p["P2"]["causation_reference"]
        and isinstance(p["P2"].get("policy_source_reference"), str)
        and p["P2"].get("freeze_effect_count") == 1
        and p["P2"].get("post_expiry_work_count") == 0,
        "P2",
    )
    _require(
        p["P3"].get("freeze_effect_count") == 1
        and p["P3"].get("beacon_row_version_delta") == 0
        and p["P3"].get("lifecycle_freeze_event_count") == 1
        and p["P3"].get("new_work_count") == 0,
        "P3",
    )
    _require(
        p["P4"].get("parser_delta") == 0
        and p["P4"].get("egress_delta") == 0
        and p["P4"].get("notification_provider_delta") == 0
        and p["P4"].get("work_state") == "BLOCKED_ACCESS_EXPIRED"
        and p["P4"].get("comparison_effect_count") == 0
        and p["P4"].get("new_listing_event_count") == 0
        and p["P4"].get("notification_outbox_count") == 0,
        "P4",
    )
    _require(
        p["P5"].get("terminal_comparison_status") == "DENIED"
        and p["P5"].get("new_listing_event_count") == 0
        and p["P5"].get("notification_effect_count") == 0,
        "P5",
    )
    _require(
        p["P6"].get("customer_bypass_accepted") is False
        and p["P6"].get("beacon_row_version_delta") == 0
        and p["P6"].get("lifecycle_event_count") == 0
        and p["P6"].get("new_work_count") == 0,
        "P6",
    )
    _require(
        p["P7"].get("free_grant_count") == 0
        and p["P7"].get("automatic_selection") is False
        and p["P7"].get("automatic_activation") is False
        and p["P7"].get("beacon_state") == "FROZEN",
        "P7",
    )
    _require(
        p["P8"].get("replacement_grant_id") not in (None, grant_a)
        and p["P8"].get("replacement_effective_status") == "ALLOWED"
        and p["P8"].get("replacement_tariff") == "BASIC"
        and p["P8"].get("stale_freeze") is False
        and p["P8"].get("beacon_state") == "ACTIVE"
        and p["P8"].get("scheduler_eligible") is True,
        "P8",
    )


def verify(path: Path, expected_sha: str, expected_run_id: str | None = None) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    _validate(data, expected_sha, expected_run_id)
    result = {
        "status": "PASS",
        "technical_id": TECHNICAL_ID,
        "source_sha": expected_sha,
        "acceptance_run_id": data["acceptance_run_id"],
    }
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    parser.add_argument("source_sha")
    parser.add_argument("--run-id")
    parser.add_argument("--result", type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.evidence, args.source_sha, args.run_id)
    except Exception as exc:
        result = {"status": "FAIL", "error": str(exc), "technical_id": TECHNICAL_ID}
        if args.result:
            args.result.write_text(
                json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
            )
        print(json.dumps(result, sort_keys=True))
        raise SystemExit(1)
    if args.result:
        args.result.write_text(
            json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps(result, sort_keys=True))

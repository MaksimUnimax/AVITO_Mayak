# ruff: noqa: E501
"""Fail-closed verifier for raw RF24 command idempotency evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, cast

TECHNICAL_ID = "RF24-COMMAND-IDEMPOTENCY-SCENARIOS-01"
SECRET = re.compile(
    r"(cookie|set-cookie|authorization|bearer|password|session[_-]?token|postgres(?:ql)?://[^\s:@/]+:[^\s@/]+@|BEGIN [A-Z ]+PRIVATE KEY)",
    re.I,
)


def fp(account: str, source_url: str, name: str) -> str:
    raw = {
        "command": "create_preparation",
        "values": {"account": account, "name": name, "url": source_url},
    }
    return hashlib.sha256(
        json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def require(value: object, message: str) -> None:
    if not value:
        raise ValueError(message)


def verify(evidence: dict[str, Any], source_sha: str) -> dict[str, Any]:
    encoded = json.dumps(evidence, sort_keys=True)
    require(not SECRET.search(encoded), "unsafe credential/session material")
    require(
        evidence.get("schema_version") == 1 and evidence.get("technical_id") == TECHNICAL_ID,
        "identity/schema mismatch",
    )
    require(evidence.get("source_sha") == source_sha, "wrong source SHA")
    require(
        isinstance(evidence.get("acceptance_run_id"), str) and evidence["acceptance_run_id"],
        "missing run identity",
    )
    require(evidence.get("public_endpoint") == "POST /api/v1/beacons", "wrong public boundary")
    trace = evidence.get("source_trace", {})
    require(
        trace.get("scope") == "beacon_management"
        and trace.get("repository") == "PostgresTerminalIdempotencyRepository",
        "wrong owner trace",
    )
    scenarios = evidence.get("scenarios")
    require(
        isinstance(scenarios, list)
        and {x.get("scenario_name") for x in scenarios}
        == {"duplicate-command", "same-key-different-fingerprint"},
        "exact scenario set required",
    )
    scenarios = cast(list[dict[str, Any]], scenarios)
    for item in scenarios:
        require(
            item.get("acceptance_run_id") == evidence["acceptance_run_id"]
            and item.get("source_sha") == source_sha,
            "scenario provenance mismatch",
        )
        require(item.get("scope") == "beacon_management" and item.get("key"), "scope/key missing")
        require(
            isinstance(item.get("before"), dict)
            and isinstance(item.get("after_first"), dict)
            and isinstance(item.get("after_second"), dict),
            "owning snapshots missing",
        )
        payload, candidate = item.get("payload"), item.get("candidate_payload")
        require(isinstance(payload, dict) and isinstance(candidate, dict), "payload missing")
        payload = cast(dict[str, Any], payload)
        candidate = cast(dict[str, Any], candidate)
        first = item.get("first_http", {})
        second = item.get("second_http", {})
        require(first.get("status") == 200, "first command did not succeed")
        require(
            item.get("fingerprint")
            == fp(item["account_id"], payload["source_url"], payload["name"]),
            "first fingerprint is not independently recomputed",
        )
        before, one, two = item["before"], item["after_first"], item["after_second"]
        before = cast(dict[str, Any], before)
        one = cast(dict[str, Any], one)
        two = cast(dict[str, Any], two)
        for field in ("beacons", "lifecycle_events", "audit", "idempotency"):
            require(
                len(one[field]) - len(before[field]) == 1,
                f"{item['scenario_name']}: first {field} delta",
            )
            require(
                len(two[field]) - len(one[field]) == 0,
                f"{item['scenario_name']}: second {field} delta",
            )
        require(
            len(one["idempotency"]) == 1 and len(two["idempotency"]) == 1,
            "terminal record not unique",
        )
        terminal_one, terminal_two = one["idempotency"][0], two["idempotency"][0]
        require(
            terminal_one["id"] == terminal_two["id"]
            and terminal_one["idempotency_key"] == item["key"],
            "terminal row replaced or wrong key",
        )
        require(
            terminal_one["request_fingerprint"]
            == terminal_two["request_fingerprint"]
            == item["fingerprint"],
            "stored fingerprint changed",
        )
        require(terminal_one["result"] == terminal_two["result"], "terminal outcome changed")
        require(
            len(one["beacons"]) == 1 and one["beacons"][0]["id"] == item["beacon_id"],
            "wrong owning Beacon",
        )
        require(one["beacons"] == two["beacons"], "Beacon state changed during replay/mismatch")
        require(
            first["body"].get("beacon_id") == item["beacon_id"], "first result identity mismatch"
        )
        if item["scenario_name"] == "duplicate-command":
            require(
                candidate == payload
                and item.get("candidate_fingerprint") == item.get("fingerprint"),
                "duplicate payload/fingerprint mismatch",
            )
            require(
                second.get("status") == 200
                and second.get("body", {}).get("beacon_id") == item["beacon_id"],
                "replay is not authoritative",
            )
        else:
            require(
                candidate != payload
                and item.get("candidate_fingerprint")
                == fp(item["account_id"], candidate["source_url"], candidate["name"]),
                "candidate fingerprint not recomputed",
            )
            require(
                item["candidate_fingerprint"] != item["fingerprint"],
                "mismatch candidates are equal",
            )
            require(second.get("status") == 409, "mismatch status is not 409")
            require(
                terminal_one["request_fingerprint"] != item["candidate_fingerprint"],
                "stored fingerprint replaced by candidate",
            )
    return {
        "verifier": "rf24-command-idempotency",
        "schema_version": 1,
        "source_sha": source_sha,
        "acceptance_run_id": evidence["acceptance_run_id"],
        "scenario_set": ["duplicate-command", "same-key-different-fingerprint"],
        "verdict": "PASS",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--evidence", type=Path, required=True)
    p.add_argument("--source-sha", required=True)
    p.add_argument("--result", type=Path)
    a = p.parse_args()
    evidence = json.loads(a.evidence.read_text(encoding="utf-8"))
    result = verify(evidence, a.source_sha)
    if a.result:
        a.result.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()

# ruff: noqa: E501
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[2]))

from scripts.runtime.verify_rf24_command_idempotency import fp, verify


def row(name: str, key: str, *, changed: bool = False) -> dict:
    account = "00000000-0000-0000-0000-000000000001"
    url = "https://synthetic.invalid/x"
    payload = {"source_url": url, "name": name}
    candidate = {"source_url": url, "name": name + "-changed"} if changed else payload
    beacon = {
        "id": "00000000-0000-0000-0000-000000000002",
        "account_id": account,
        "name": name,
        "source_url": url,
        "state": "DRAFT",
        "row_version": 1,
    }
    terminal = {
        "id": "00000000-0000-0000-0000-000000000003",
        "scope": "beacon_management",
        "idempotency_key": key,
        "request_fingerprint": fp(account, url, name),
        "result": {
            "result": "SUCCEEDED",
            "reason_code": "PREPARED",
            "details": ["beacon_id=00000000-0000-0000-0000-000000000002"],
        },
    }
    empty = {
        "beacons": [],
        "lifecycle_events": [],
        "audit": [],
        "idempotency": [],
        "observation_source": "owning-read-model",
    }
    full = {
        "beacons": [beacon],
        "lifecycle_events": [{"id": "e", "beacon_id": beacon["id"]}],
        "audit": [{"id": "a", "target_id": beacon["id"]}],
        "idempotency": [terminal],
        "observation_source": "owning-read-model",
    }
    return {
        "scenario_name": "same-key-different-fingerprint" if changed else "duplicate-command",
        "acceptance_run_id": "run",
        "source_sha": "a" * 40,
        "account_id": account,
        "key": key,
        "scope": "beacon_management",
        "payload": payload,
        "candidate_payload": candidate,
        "fingerprint": fp(account, url, name),
        "candidate_fingerprint": fp(account, url, candidate["name"]),
        "first_http": {"status": 200, "body": {"beacon_id": beacon["id"]}},
        "second_http": {
            "status": 409 if changed else 200,
            "body": {} if changed else {"beacon_id": beacon["id"]},
        },
        "before": empty,
        "after_first": full,
        "after_second": copy.deepcopy(full),
        "beacon_id": beacon["id"],
    }


def evidence():
    return {
        "schema_version": 1,
        "technical_id": "RF24-COMMAND-IDEMPOTENCY-SCENARIOS-01",
        "acceptance_run_id": "run",
        "source_sha": "a" * 40,
        "public_endpoint": "POST /api/v1/beacons",
        "source_trace": {
            "scope": "beacon_management",
            "repository": "PostgresTerminalIdempotencyRepository",
        },
        "scenarios": [row("A", "KA"), row("B", "KB", changed=True)],
    }


def test_positive():
    assert verify(evidence(), "a" * 40)["verdict"] == "PASS"


@pytest.mark.parametrize(
    "mutation",
    [
        "different-key",
        "changed-payload",
        "extra-beacon",
        "extra-event",
        "extra-audit",
        "replacement",
        "changed-outcome",
        "candidate-equal",
        "success-mismatch",
    ],
)
def test_adversarial_rejected(mutation):
    bad = evidence()
    if mutation == "different-key":
        bad["scenarios"][0]["key"] = "other"
    elif mutation == "changed-payload":
        bad["scenarios"][0]["candidate_payload"] = {
            "source_url": "https://synthetic.invalid/x",
            "name": "other",
        }
    elif mutation == "extra-beacon":
        bad["scenarios"][0]["after_second"]["beacons"].append({"id": "other"})
    elif mutation == "extra-event":
        bad["scenarios"][0]["after_second"]["lifecycle_events"].append({"id": "other"})
    elif mutation == "extra-audit":
        bad["scenarios"][0]["after_second"]["audit"].append({"id": "other"})
    elif mutation == "replacement":
        bad["scenarios"][0]["after_second"]["idempotency"][0]["id"] = "replaced"
    elif mutation == "changed-outcome":
        bad["scenarios"][0]["after_second"]["idempotency"][0]["result"] = {"x": 1}
    elif mutation == "candidate-equal":
        bad["scenarios"][1]["candidate_fingerprint"] = bad["scenarios"][1]["fingerprint"]
    else:
        bad["scenarios"][1]["second_http"]["status"] = 200
    with pytest.raises(ValueError):
        verify(bad, "a" * 40)
